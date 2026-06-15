from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from functools import partial
from typing import Optional

import yt_dlp

from bot.logger import logger

_CLEAN_RE = re.compile(
    r"\b(Official\s+)?(Music\s+)?(Video|Audio|Lyric\s+Video|Visualizer|MV|HD|4K|HQ)\b"
    r"|[\(\[]\s*(Official|Audio|Lyrics?|HD|4K|HQ|Full\s+Song|feat\.?\s+[^\)\]]+)\s*[\)\]]"
    r"|#\S+",
    re.IGNORECASE,
)


@dataclass
class SongEntry:
    id: str
    title: str
    uploader: str
    duration: int
    url: str
    thumbnail: Optional[str] = None


def clean_title(title: str) -> str:
    cleaned = _CLEAN_RE.sub("", title)
    return re.sub(r"\s{2,}", " ", cleaned).strip(" -|–")


def format_duration(seconds: int) -> str:
    m, s = divmod(max(0, seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _parse_entry(entry: dict) -> Optional[SongEntry]:
    vid_id = entry.get("id") or entry.get("url", "")
    if not vid_id:
        return None
    url = entry.get("webpage_url") or f"https://www.youtube.com/watch?v={vid_id}"
    return SongEntry(
        id=vid_id,
        title=clean_title(entry.get("title") or "Unknown"),
        uploader=entry.get("uploader") or entry.get("channel") or "Unknown",
        duration=int(entry.get("duration") or 0),
        url=url,
        thumbnail=entry.get("thumbnail"),
    )


def _search_sync(query: str, max_results: int) -> list[dict]:
    opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "socket_timeout": 20,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        result = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
    return list(result.get("entries") or [])


async def search_songs(query: str, max_results: int = 30) -> list[SongEntry]:
    try:
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(None, partial(_search_sync, query, max_results))
        entries = [_parse_entry(e) for e in raw if e]
        return [e for e in entries if e is not None]
    except Exception as e:
        logger.error(f"Music search error: {e}")
        return []


def _download_audio_sync(url: str, output_path: str) -> str:
    opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path.replace(".mp3", ""),
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 3,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "writethumbnail": False,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    return output_path


async def download_audio(url: str, output_path: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_download_audio_sync, url, output_path))
