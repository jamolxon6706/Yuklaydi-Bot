#!/usr/bin/env python3
"""
Speed benchmark for @vidyuklaydi_bot downloader.

Usage:
    python scripts/bench_speed.py [--runs N] [--quality 720|mp3]

What it measures:
    t_extract  – time for yt-dlp to extract video metadata
    t_download – time from info-ready to file on disk
    t_total    – t_extract + t_download (upload excluded here; add ~0.5–2s for Local API)
    size_mb    – file size in MB

For each URL:
    • Runs N times (default 3), reports min / median / max
    • Second run should be faster on YouTube when using android client cache

NOTE: Replace the TEST_URLS below with real, publicly accessible URLs before running.
      The included URLs are examples — they will stale over time.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import statistics
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Optional

# Ensure bot package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("BOT_TOKEN", "0:dummy")
os.environ.setdefault("TELEGRAM_API_ID", "1")
os.environ.setdefault("TELEGRAM_API_HASH", "a" * 32)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://bot:bot@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ADMIN_IDS", "0")
os.environ.setdefault("DOWNLOAD_DIR", tempfile.gettempdir())

# ── URLs to benchmark (replace with real, short clips) ───────────────────────
TEST_URLS: dict[str, str] = {
    # Short YouTube Shorts clip (~15s)
    "youtube_short": "https://www.youtube.com/shorts/fRh_vgS2dFE",
    # TikTok short video (~15s) — replace with a current URL
    "tiktok":        "https://www.tiktok.com/@tiktok/video/7106594312292453675",
    # Instagram reel (~15s) — must be public
    "instagram":     "https://www.instagram.com/reel/C7LkJObNyxo/",
    # Slightly longer YouTube clip (~1 min)
    "youtube_long":  "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
}
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class RunResult:
    label: str
    url: str
    run: int
    t_extract: float
    t_download: float
    t_total: float
    size_mb: float
    error: Optional[str] = None


async def bench_one(label: str, url: str, quality: str, run: int, out_dir: str) -> RunResult:
    from bot.services.downloader import DownloadResult, download

    suffix = ".mp3" if quality == "mp3" else ".mp4"
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=f"bench_{label}_", dir=out_dir)
    os.close(fd)
    # Delete the placeholder so yt-dlp writes a fresh file (mkstemp creates empty file)
    try:
        os.unlink(path)
    except OSError:
        pass

    t0 = time.monotonic()
    try:
        result: DownloadResult = await download(url, path, quality)
        t_total = time.monotonic() - t0
        size_mb = result.size_bytes / 1024 / 1024
        return RunResult(
            label=label, url=url, run=run,
            t_extract=result.t_extract,
            t_download=result.t_download,
            t_total=t_total,
            size_mb=round(size_mb, 1),
        )
    except Exception as e:
        t_total = time.monotonic() - t0
        return RunResult(label=label, url=url, run=run,
                         t_extract=0, t_download=0, t_total=t_total,
                         size_mb=0, error=str(e)[:80])
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass
        # Also clean up possible mp3
        if path.endswith(".mp4"):
            mp3 = path.replace(".mp4", ".mp3")
            try:
                os.unlink(mp3)
            except Exception:
                pass


def _median(vals: list[float]) -> float:
    return statistics.median(vals) if vals else 0.0


def _fmt(v: float) -> str:
    return f"{v:.1f}s"


async def main(runs: int, quality: str):
    out_dir = tempfile.gettempdir()
    all_results: list[RunResult] = []

    print(f"\n{'=' * 70}")
    print("  vidyuklaydi_bot — Download Speed Benchmark")
    print(f"  quality={quality}  runs={runs}  aria2c={'yes' if _has_aria2c() else 'NO (install aria2)'}")
    print(f"{'=' * 70}\n")

    for label, url in TEST_URLS.items():
        print(f">> {label}")
        for run in range(1, runs + 1):
            r = await bench_one(label, url, quality, run, out_dir)
            all_results.append(r)
            if r.error:
                print(f"  run {run}: ERROR — {r.error}")
            else:
                dl_speed = f"{r.size_mb / r.t_download:.1f}MB/s" if r.t_download > 0.01 else "—"
                print(f"  run {run}: extract={_fmt(r.t_extract)} + download={_fmt(r.t_download)} ({dl_speed}) = total={_fmt(r.t_total)}  [{r.size_mb}MB]")
        print()

    # Summary table
    print(f"\n{'─' * 70}")
    print(f"{'Source':<18} {'Runs':>5} {'t_extract':>10} {'t_download':>11} {'t_total':>9} {'MB':>6}")
    print(f"{'─' * 70}")

    for label in TEST_URLS:
        good = [r for r in all_results if r.label == label and not r.error]
        if not good:
            print(f"{label:<18} {'—':>5}  (all runs failed)")
            continue
        med_ex = _median([r.t_extract for r in good])
        med_dl = _median([r.t_download for r in good])
        med_tot = _median([r.t_total for r in good])
        med_mb = _median([r.size_mb for r in good])
        flag = " ✅" if med_tot < 5 else (" ⚠️" if med_tot < 10 else " ❌")
        print(
            f"{label:<18} {len(good):>5}  "
            f"{_fmt(med_ex):>9}  {_fmt(med_dl):>10}  {_fmt(med_tot):>8}  {med_mb:>5.1f}{flag}"
        )

    print(f"{'─' * 70}")
    print("\nTarget: ≤5s total for short clips (up to +2s for Telegram upload with Local API)")
    print("✅ = <5s  ⚠️ = 5-10s  ❌ = >10s\n")
    print("Note: upload to Telegram via Local API (~0.3–1s) is NOT included in these numbers.")
    print("      With cloud API upload adds ~1–3s per 10MB depending on server bandwidth.\n")


def _has_aria2c() -> bool:
    import shutil
    return bool(shutil.which("aria2c"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download speed benchmark")
    parser.add_argument("--runs", type=int, default=3, help="Runs per URL (default 3)")
    parser.add_argument("--quality", default="720", choices=["720", "1080", "mp3"])
    args = parser.parse_args()

    asyncio.run(main(args.runs, args.quality))
