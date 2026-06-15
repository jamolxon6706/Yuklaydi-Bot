from __future__ import annotations

import asyncio
import os
import re
import shutil
import time
from functools import partial
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import yt_dlp

from bot.config import settings
from bot.logger import logger

# ── Platform detection ────────────────────────────────────────────────────────

SUPPORTED_PLATFORMS = {
    "youtube":   [r"youtu\.be", r"youtube\.com", r"youtube-nocookie\.com"],
    "tiktok":    [r"tiktok\.com", r"vm\.tiktok\.com"],
    "instagram": [r"instagram\.com", r"instagr\.am"],
    "facebook":  [r"facebook\.com", r"fb\.watch", r"fb\.com"],
    "twitter":   [r"twitter\.com", r"x\.com", r"t\.co"],
    "pinterest": [r"pinterest\.com", r"pin\.it"],
    "vimeo":     [r"vimeo\.com"],
    "reddit":    [r"reddit\.com", r"redd\.it"],
}

_STRIP_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "si", "igshid", "feature", "pp", "ref", "t",
}

# Check once at startup whether aria2c is available
_ARIA2C = shutil.which("aria2c")


class DownloadError(Exception):
    kind: str = "generic"

    def __init__(self, message: str, kind: str = "generic"):
        super().__init__(message)
        self.kind = kind


class DownloadResult:
    __slots__ = ("path", "t_extract", "t_download", "size_bytes")

    def __init__(self, path: str, t_extract: float, t_download: float, size_bytes: int):
        self.path = path
        self.t_extract = t_extract
        self.t_download = t_download
        self.size_bytes = size_bytes


def detect_platform(url: str) -> Optional[str]:
    for platform, patterns in SUPPORTED_PLATFORMS.items():
        for pat in patterns:
            if re.search(pat, url, re.IGNORECASE):
                return platform
    return None


def normalize_url(url: str) -> str:
    """Strip tracking params and fragment so URL variants share one cache key."""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        cleaned = {k: v for k, v in params.items() if k not in _STRIP_PARAMS}
        new_query = urlencode(cleaned, doseq=True)
        return urlunparse(parsed._replace(query=new_query, fragment=""))
    except Exception:
        return url


# ── Format selectors (progressive-first = no merge = faster) ─────────────────

def _format_selector(quality: str) -> str:
    """
    Priority: single progressive mp4 (no ffmpeg merge) → adaptive merge fallback.
    Progressive is faster because there is no post-download mux step.
    """
    if quality == "mp3":
        return "ba[ext=m4a]/ba/b"
    elif quality in ("1080", "1080p"):
        return (
            "b[ext=mp4][height<=1080]/b[height<=1080]"
            "/bv*[height<=1080]+ba[ext=m4a]/bv*[height<=1080]+ba/b"
        )
    else:  # default 720p
        return (
            "b[ext=mp4][height<=720]/b[height<=720]"
            "/bv*[height<=720]+ba[ext=m4a]/bv*[height<=720]+ba/b"
        )


# ── yt-dlp options builder ────────────────────────────────────────────────────

def _build_opts(output_path: str, quality: str) -> dict:
    opts: dict = {
        "outtmpl": output_path,
        "format": _format_selector(quality),
        "merge_output_format": "mp4",
        # Speed
        "concurrent_fragment_downloads": 16,   # HLS/DASH parallel segments
        "socket_timeout": 15,
        "retries": 3,
        "fragment_retries": 3,
        # No unnecessary work
        "noplaylist": True,
        "writethumbnail": False,
        "writesubtitles": False,
        "writeinfojson": False,
        "no_warnings": True,
        "quiet": True,
        "noprogress": True,
        # YouTube: web client with node.js EJS solver for n-challenge
        "extractor_args": {
            "youtube": {"player_client": ["web"]},
        },
        # node.js JS runtime for YouTube n-challenge solving (avoids throttled URLs)
        "js_runtimes": {"node": {}},
        # Download EJS challenge-solver script from GitHub on first use (cached)
        "remote_components": {"ejs:github"},
    }

    # aria2c: multi-connection HTTP downloads (big win for single-file MP4s)
    if _ARIA2C:
        opts["external_downloader"] = "aria2c"
        opts["external_downloader_args"] = {
            "aria2c": [
                "-x16", "-s16", "-k1M",
                "--min-split-size=1M",
                "--max-connection-per-server=16",
                "--optimize-concurrent-downloads=true",
                "--auto-file-renaming=false",
                "--summary-interval=0",
                "--quiet",
            ]
        }

    if quality == "mp3":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
        opts["outtmpl"] = output_path.replace(".mp4", "").replace(".mp3", "")
    else:
        # No transcode for video — remux/mux only (skip for MP3 which needs re-encode)
        opts["postprocessor_args"] = {"default": ["-c", "copy"]}

    cookies_path = settings.cookies_file or os.path.join(settings.download_dir, "cookies.txt")
    if cookies_path and os.path.exists(cookies_path):
        opts["cookiefile"] = cookies_path

    return opts


# ── Sync download (runs in executor) ─────────────────────────────────────────

def _download_sync(url: str, output_path: str, quality: str) -> DownloadResult:
    opts = _build_opts(output_path, quality)
    t_start = time.monotonic()
    t_extract = 0.0

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            # Single pass: extract_info(download=True) — no double fetch
            # We hook the progress callback to measure the extract vs download split
            _info_done = [False]
            _t_info = [t_start]

            orig_process = ydl.process_ie_result

            def _patched_process(ie_result, *args, **kwargs):
                if not _info_done[0]:
                    _info_done[0] = True
                    _t_info[0] = time.monotonic()
                return orig_process(ie_result, *args, **kwargs)

            ydl.process_ie_result = _patched_process

            ydl.extract_info(url, download=True)

            t_extract = _t_info[0] - t_start
            t_download = time.monotonic() - _t_info[0]

            if quality == "mp3":
                # yt-dlp appends .mp3 to the outtmpl (which has no extension)
                base = output_path.replace(".mp4", "").replace(".mp3", "")
                out = base + ".mp3"
            else:
                out = output_path

            # yt-dlp may save to a different extension (e.g. .webm instead of .mp4).
            # Scan the download dir for a recently created file with the same stem.
            if not os.path.exists(out) or os.path.getsize(out) == 0:
                stem = os.path.splitext(out)[0]
                parent = os.path.dirname(out)
                for fname in os.listdir(parent):
                    candidate = os.path.join(parent, fname)
                    if (fname.startswith(os.path.basename(stem))
                            and os.path.isfile(candidate)
                            and os.path.getsize(candidate) > 0):
                        out = candidate
                        break

            size = os.path.getsize(out) if os.path.exists(out) else 0
            return DownloadResult(out, t_extract, t_download, size)

    except yt_dlp.utils.DownloadError as e:
        msg = str(e).lower()
        if "private" in msg or "removed" in msg or "deleted" in msg:
            raise DownloadError(str(e), kind="private")
        elif "geo" in msg or "not available in your country" in msg:
            raise DownloadError(str(e), kind="geo")
        elif "timed out" in msg or "read timed out" in msg or "connection timed out" in msg or "curl: (28)" in msg:
            raise DownloadError(str(e), kind="timeout")
        elif "connection" in msg or "network" in msg or "errno" in msg:
            raise DownloadError(str(e), kind="timeout")
        elif any(x in msg for x in ("age restriction", "age-restricted", "age gate", "age limit", "age_verify")):
            raise DownloadError(str(e), kind="age")
        elif "sign in" in msg or "login" in msg or "log in" in msg:
            raise DownloadError(str(e), kind="no_video")
        elif "unsupported url" in msg:
            raise DownloadError(str(e), kind="unsupported")
        elif "there is no video in this post" in msg or "empty media response" in msg or "login required" in msg:
            raise DownloadError(str(e), kind="no_video")
        else:
            raise DownloadError(str(e), kind="generic")


async def download(url: str, output_path: str, quality: str = "720") -> DownloadResult:
    """Async wrapper — runs blocking yt-dlp in a thread pool executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, partial(_download_sync, url, output_path, quality)
    )


# ── Legacy sync extract_info (used only for metadata-first quality picker) ───

def _extract_info_sync(url: str) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "socket_timeout": 15,
        "extractor_args": {"youtube": {"player_client": ["web"]}},
        "js_runtimes": {"node": {}},
        "remote_components": {"ejs:github"},
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


async def extract_info(url: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_extract_info_sync, url))
