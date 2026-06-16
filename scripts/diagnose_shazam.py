"""
Stage 1 diagnostic: test the full voice→song recognition pipeline without the bot.

Run from the project root:
    .venv\Scripts\python.exe scripts\diagnose_shazam.py [optional_audio_file.ogg]

Without an audio file argument the script generates a 15-second synthetic WAV
(a 440 Hz sine wave), which lets you confirm that the pipeline mechanics work
even if Shazam won't match a pure tone.  Pass a real voice/audio file to test
end-to-end recognition.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import struct
import sys
import tempfile
import time

# ── colour helpers ────────────────────────────────────────────────────────────
RED   = "\033[91m"
GRN   = "\033[92m"
YLW   = "\033[93m"
BLU   = "\033[94m"
RST   = "\033[0m"
BOLD  = "\033[1m"

def ok(msg):  print(f"{GRN}[OK]{RST}   {msg}")
def err(msg): print(f"{RED}[ERR]{RST}  {msg}")
def info(msg):print(f"{BLU}[>>]{RST}  {msg}")
def warn(msg):print(f"{YLW}[WARN]{RST} {msg}")
def hdr(msg): print(f"\n{BOLD}{msg}{RST}")

# ─────────────────────────────────────────────────────────────────────────────
PASS = "[PASS]"
FAIL = "[FAIL]"

results: list[tuple[str, str]] = []  # (stage, PASS/FAIL)

def record(stage: str, passed: bool) -> bool:
    results.append((stage, PASS if passed else FAIL))
    return passed


# ── Stage 0: environment ──────────────────────────────────────────────────────
async def check_env():
    hdr("STAGE 0 — Environment")
    import platform
    info(f"Python {sys.version}")
    info(f"Platform: {platform.platform()}")

    try:
        import shazamio
        version = getattr(shazamio, "__version__", "n/a")
        ok(f"shazamio imported (version={version})")
        record("shazamio import", True)
    except Exception as exc:
        err(f"shazamio import failed: {exc}")
        record("shazamio import", False)

    try:
        from shazamio_core import Recognizer
        r = Recognizer()
        ok(f"shazamio_core.Recognizer() ok → {type(r).__name__}")
        record("shazamio_core Recognizer", True)
    except Exception as exc:
        err(f"shazamio_core.Recognizer() FAILED: {type(exc).__name__}: {exc}")
        warn("This is likely the root cause — see fix below.")
        record("shazamio_core Recognizer", False)

    try:
        from shazamio import Shazam
        s = Shazam()
        ok(f"Shazam() ok — core_recognizer={type(s.core_recognizer).__name__}")
        record("Shazam() init", True)
    except Exception as exc:
        err(f"Shazam() init FAILED: {type(exc).__name__}: {exc}")
        record("Shazam() init", False)


# ── Stage 1: ffprobe / ffmpeg ─────────────────────────────────────────────────
async def check_fftools(audio_path: str):
    hdr("STAGE 1 — ffprobe / ffmpeg availability")

    # Add project root to sys.path so we can import bot modules
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from bot.services.media import ffmpeg_path, ffprobe_path, probe_duration, extract_audio_snippet

    fp = ffprobe_path()
    fm = ffmpeg_path()
    info(f"ffprobe → {fp}")
    info(f"ffmpeg  → {fm}")

    # Test ffprobe on the audio file
    hdr("STAGE 2 — probe_duration")
    info(f"Probing: {audio_path!r}  (size={os.path.getsize(audio_path)}B)")
    dur = await probe_duration(audio_path)
    if dur > 0:
        ok(f"probe_duration = {dur:.3f}s")
        record("probe_duration", True)
    else:
        err("probe_duration returned 0.0 — ffprobe could not read duration")
        record("probe_duration", False)
        warn("Check that ffprobe is installed and the audio file is valid.")

    # Test snippet extraction
    hdr("STAGE 3 — extract_audio_snippet → WAV 16kHz mono")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, prefix="diag_shz_") as tf:
        wav_path = tf.name
    try:
        t0 = time.monotonic()
        await extract_audio_snippet(audio_path, wav_path, snippet_duration=15, start_override=-1.0)
        elapsed = time.monotonic() - t0
        if os.path.exists(wav_path):
            wav_size = os.path.getsize(wav_path)
            info(f"WAV snippet: {wav_path!r}  size={wav_size}B  elapsed={elapsed:.2f}s")
            if wav_size > 1000:
                ok(f"WAV snippet is big enough ({wav_size}B > 1000B)")
                record("extract_audio_snippet", True)
                return wav_path
            else:
                err(f"WAV snippet too small ({wav_size}B) — ffmpeg may have failed")
                record("extract_audio_snippet", False)
        else:
            err("WAV file was not created — ffmpeg likely failed")
            record("extract_audio_snippet", False)
    except Exception as exc:
        err(f"extract_audio_snippet raised: {exc}")
        record("extract_audio_snippet", False)
    return None


# ── Stage 4: shazamio fingerprint generation ──────────────────────────────────
async def check_shazam_recognize(wav_path: str):
    hdr("STAGE 4 — shazamio.Shazam().recognize(wav_path)")
    from shazamio import Shazam

    shazam = Shazam()
    info(f"Calling shazam.recognize({wav_path!r}) …")
    t0 = time.monotonic()
    try:
        raw = await shazam.recognize(wav_path)
        elapsed = time.monotonic() - t0
        ok(f"recognize() returned in {elapsed:.2f}s")
        info(f"Top-level keys: {list(raw.keys())}")
        matches = raw.get("matches", [])
        info(f"matches: {len(matches)}")
        has_track = "track" in raw
        info(f"has 'track' key: {has_track}")
        if has_track:
            track = raw["track"]
            ok(f"SONG FOUND: {track.get('title')!r} — {track.get('subtitle')!r}")
            record("shazam API match", True)
        else:
            warn("No song matched — this is expected for a synthetic tone or unfamiliar clip.")
            warn("But if a real, well-known song fails here, the problem is in the Shazam API call.")
            info(f"Full raw response:\n{json.dumps(raw, indent=2, ensure_ascii=False)[:2000]}")
            record("shazam API match", False)
    except Exception as exc:
        elapsed = time.monotonic() - t0
        err(f"recognize() RAISED after {elapsed:.2f}s: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()
        record("shazam recognize() exception", False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def generate_sine_wav(path: str, duration_s: float = 15.0, freq: float = 440.0,
                       sample_rate: int = 16000):
    """Write a minimal PCM WAV with a sine wave at `freq` Hz."""
    num_samples = int(sample_rate * duration_s)
    with open(path, "wb") as f:
        data_size = num_samples * 2  # 16-bit = 2 bytes/sample
        # RIFF header
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")
        # fmt chunk
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))           # chunk size
        f.write(struct.pack("<H", 1))            # PCM
        f.write(struct.pack("<H", 1))            # mono
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", sample_rate * 2))  # byte rate
        f.write(struct.pack("<H", 2))            # block align
        f.write(struct.pack("<H", 16))           # bits/sample
        # data chunk
        f.write(b"data")
        f.write(struct.pack("<I", data_size))
        for i in range(num_samples):
            sample = int(32767 * math.sin(2 * math.pi * freq * i / sample_rate))
            f.write(struct.pack("<h", sample))


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    audio_arg = sys.argv[1] if len(sys.argv) > 1 else None

    await check_env()

    if audio_arg:
        if not os.path.exists(audio_arg):
            err(f"File not found: {audio_arg}")
            sys.exit(1)
        audio_path = audio_arg
        info(f"Using provided audio: {audio_path!r}")
        own_audio = False
    else:
        # Generate a synthetic 15-second sine wave (440 Hz, 16kHz, mono, s16le)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, prefix="diag_tone_") as tf:
            audio_path = tf.name
        generate_sine_wav(audio_path, duration_s=15.0)
        ok(f"Generated synthetic WAV: {audio_path!r} ({os.path.getsize(audio_path)}B)")
        info("NOTE: A sine tone will NOT match in Shazam. Use a real audio file for a full E2E test.")
        info("Usage: .venv\\Scripts\\python.exe scripts\\diagnose_shazam.py path/to/voice.ogg")
        own_audio = True

    wav_path = await check_fftools(audio_path)

    if wav_path is None and own_audio:
        # Synthetic WAV already IS the wav — try directly
        wav_path = audio_path

    if wav_path:
        await check_shazam_recognize(wav_path)

    if own_audio and os.path.exists(audio_path):
        os.unlink(audio_path)
    if wav_path and wav_path != audio_path and os.path.exists(wav_path):
        os.unlink(wav_path)

    # ── Summary table ─────────────────────────────────────────────────────────
    hdr("SUMMARY")
    for stage, outcome in results:
        colour = GRN if outcome == PASS else RED
        print(f"  {colour}{outcome}{RST}  {stage}")

    failed = sum(1 for _, o in results if o == FAIL)
    if failed == 0:
        print(f"\n{GRN}All checks passed.{RST}")
    else:
        print(f"\n{RED}{failed} check(s) failed.{RST}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
