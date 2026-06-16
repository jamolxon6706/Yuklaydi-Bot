"""Debug: check what format is selected and measure download speed."""
import os
import sys
import tempfile
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("BOT_TOKEN", "0:dummy")
os.environ.setdefault("TELEGRAM_API_ID", "1")
os.environ.setdefault("TELEGRAM_API_HASH", "a" * 32)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://bot:bot@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ADMIN_IDS", "0")
os.environ.setdefault("DOWNLOAD_DIR", tempfile.gettempdir())

import yt_dlp
from bot.services.downloader import _build_opts, _format_selector

URL = "https://www.youtube.com/shorts/fRh_vgS2dFE"
fd, path = tempfile.mkstemp(suffix=".mp4", prefix="bench_yt_")
os.close(fd)
os.unlink(path)

print(f"Format selector: {_format_selector('720')}")
opts = _build_opts(path, "720")
opts["quiet"] = False
opts["no_warnings"] = False
opts["noprogress"] = False

t0 = time.monotonic()
with yt_dlp.YoutubeDL(opts) as ydl:
    info = ydl.extract_info(URL, download=True)

t1 = time.monotonic()
actual_path = path if os.path.exists(path) else (path.replace(".mp4", ".mkv") if os.path.exists(path.replace(".mp4", ".mkv")) else "NOT FOUND")
size = os.path.getsize(actual_path) if os.path.exists(actual_path) else 0
print(f"\nTotal time: {t1-t0:.1f}s, file: {actual_path}, size: {size/1024/1024:.1f}MB")
if os.path.exists(actual_path):
    os.unlink(actual_path)
