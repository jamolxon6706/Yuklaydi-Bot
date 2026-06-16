"""Integration tests: real audio fixtures through the production recognize() pipeline.

These hit the live Shazam API (network required). Run with the default `pytest`
invocation, or exclude via `pytest -m "not network"` when offline.

Fixtures are short OGG/Opus (voice-note shaped) and MP4 (video_note shaped) clips
cut from a real Uzbek song, covering the exact 7s/11s/16s durations that were
failing before the probe_duration OGG/Opus stream-duration fallback fix.
"""
import os
import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

pytestmark = pytest.mark.network


def _fixture(name: str) -> str:
    path = os.path.join(FIXTURES, name)
    if not os.path.exists(path):
        pytest.skip(f"fixture {name} not present")
    return path


@pytest.mark.asyncio
async def test_recognize_voice_note_16s():
    """16s OGG/Opus voice note (mono 48kHz, Telegram-shaped) recognizes correctly."""
    from bot.services.recognizer import recognize
    result = await recognize(_fixture("voice_16s.ogg"))
    assert result is not None
    assert result.artist


@pytest.mark.asyncio
async def test_recognize_voice_note_11s():
    """11s OGG/Opus voice note recognizes correctly."""
    from bot.services.recognizer import recognize
    result = await recognize(_fixture("voice_11s.ogg"))
    assert result is not None
    assert result.artist


@pytest.mark.asyncio
async def test_recognize_voice_note_7s():
    """7s OGG/Opus voice note — the shortest reported failing duration — recognizes correctly."""
    from bot.services.recognizer import recognize
    result = await recognize(_fixture("voice_7s.ogg"))
    assert result is not None
    assert result.artist


@pytest.mark.asyncio
async def test_recognize_video_note_14s():
    """14s round MP4 (video_note shape: video + audio track) recognizes via audio extraction."""
    from bot.services.recognizer import recognize
    result = await recognize(_fixture("video_note_14s.mp4"))
    assert result is not None
    assert result.artist


@pytest.mark.asyncio
async def test_recognize_audio_file_mp3():
    """Full-length MP3 (audio file type) recognizes correctly via the middle window."""
    from bot.services.recognizer import recognize
    candidates = [
        os.path.join(FIXTURES, "..", "..", "downloads", "mus_2a7hay88.mp3"),
    ]
    path = next((p for p in candidates if os.path.exists(p)), None)
    if not path:
        pytest.skip("no real mp3 fixture available in downloads/")
    result = await recognize(path)
    assert result is not None
    assert result.artist
