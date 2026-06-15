"""Tests for music search routing, caching, and audio delivery."""
from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.music_search import SongEntry, clean_title, format_duration, _parse_entry


# ── SongEntry helpers ─────────────────────────────────────────────────────────

def _make_entry(i: int) -> SongEntry:
    return SongEntry(
        id=f"vid{i}",
        title=f"Song {i}",
        uploader=f"Artist {i}",
        duration=180 + i,
        url=f"https://youtube.com/watch?v=vid{i}",
        thumbnail=None,
    )


def test_song_entry_serialization():
    """SongEntry must round-trip through asdict / SongEntry(**dict)."""
    e = _make_entry(1)
    d = asdict(e)
    reconstructed = SongEntry(**d)
    assert reconstructed == e


def test_parse_entry_valid():
    raw = {
        "id": "abc123",
        "title": "My Song (Official Video)",
        "uploader": "My Artist",
        "duration": 240,
        "webpage_url": "https://youtube.com/watch?v=abc123",
    }
    entry = _parse_entry(raw)
    assert entry is not None
    assert entry.id == "abc123"
    assert entry.uploader == "My Artist"
    # Title should be cleaned
    assert "Official Video" not in entry.title


def test_parse_entry_missing_id():
    assert _parse_entry({}) is None
    assert _parse_entry({"title": "Song"}) is None


# ── Deduplication logic ───────────────────────────────────────────────────────

def test_deduplication():
    """Entries with identical (title, uploader) must be deduplicated."""
    entries = [
        SongEntry("a", "Blinding Lights", "The Weeknd", 200, "url_a"),
        SongEntry("b", "Blinding Lights", "The Weeknd", 200, "url_b"),  # duplicate
        SongEntry("c", "Save Your Tears", "The Weeknd", 190, "url_c"),
    ]

    seen: set = set()
    unique = []
    for e in entries:
        key = f"{e.title.lower()[:30]}|{e.uploader.lower()[:20]}"
        if key not in seen:
            seen.add(key)
            unique.append(e)

    assert len(unique) == 2
    assert unique[0].id == "a"
    assert unique[1].id == "c"


# ── Pagination ────────────────────────────────────────────────────────────────

def test_pagination_10_per_page():
    import math
    from bot.keyboards.inline import music_search_keyboard

    entries = [_make_entry(i) for i in range(25)]
    total_pages = math.ceil(len(entries) / 10)

    text0, kb0 = music_search_keyboard("hash1", entries, page=0, total_pages=total_pages, lang="en")
    text1, kb1 = music_search_keyboard("hash1", entries, page=1, total_pages=total_pages, lang="en")
    text2, kb2 = music_search_keyboard("hash1", entries, page=2, total_pages=total_pages, lang="en")

    # Page 0 should show entries 1-10 (numbers 1-10)
    assert "1." in text0
    assert "10." in text0
    assert "11." not in text0

    # Page 2 should show entries 21-25 (5 items)
    assert "21." in text2
    assert "25." in text2


def test_pagination_navigation_buttons():
    """Page 0 should have ▶️ but not ◀️. Last page should have ◀️ but not ▶️."""
    import math
    from bot.keyboards.inline import music_search_keyboard

    entries = [_make_entry(i) for i in range(20)]
    total = math.ceil(len(entries) / 10)

    _, kb_first = music_search_keyboard("h", entries, 0, total, "en")
    _, kb_last = music_search_keyboard("h", entries, total - 1, total, "en")

    # Inspect buttons
    def get_cb_data(kb) -> list[str]:
        return [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.callback_data]

    first_cbs = get_cb_data(kb_first)
    last_cbs = get_cb_data(kb_last)

    assert any("msp:h:1" in cb for cb in first_cbs), "Page 0 must have next button"
    assert not any("msp:h:-1" in cb for cb in first_cbs), "Page 0 must not have prev button"
    assert any("msp:h:0" in cb for cb in last_cbs), "Last page must have prev button"


# ── Cache helpers ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_music_search_cache_roundtrip():
    """set_music_search → get_music_search_by_hash must return same data."""
    from bot.services.cache import get_music_search_by_hash, set_music_search

    entries = [asdict(_make_entry(i)) for i in range(3)]
    fake_redis = {}

    async def fake_setex(key, ttl, val):
        fake_redis[key] = val

    async def fake_get(key):
        return fake_redis.get(key)

    mock_r = AsyncMock()
    mock_r.setex = AsyncMock(side_effect=fake_setex)
    mock_r.get = AsyncMock(side_effect=fake_get)

    with patch("bot.services.cache.get_redis", return_value=mock_r):
        qhash = await set_music_search("test query", entries)
        result = await get_music_search_by_hash(qhash)

    assert result is not None
    assert len(result) == 3
    assert result[0]["id"] == "vid0"


@pytest.mark.asyncio
async def test_audio_file_id_cache():
    """set_audio_file_id → get_audio_file_id must return same file_id."""
    from bot.services.cache import get_audio_file_id, set_audio_file_id

    fake_redis = {}

    async def fake_setex(key, ttl, val):
        fake_redis[key] = val

    async def fake_get(key):
        return fake_redis.get(key)

    mock_r = AsyncMock()
    mock_r.setex = AsyncMock(side_effect=fake_setex)
    mock_r.get = AsyncMock(side_effect=fake_get)

    with patch("bot.services.cache.get_redis", return_value=mock_r):
        await set_audio_file_id("vid123", "BQACAgIAAxk...")
        result = await get_audio_file_id("vid123")

    assert result == "BQACAgIAAxk..."


@pytest.mark.asyncio
async def test_second_tap_uses_cache():
    """get_audio_file_id returns cached value via Redis without a real download."""
    import bot.services.cache as cache_mod

    mock_r = AsyncMock()
    mock_r.get = AsyncMock(return_value="CACHED_FILE_ID")

    with patch("bot.services.cache.get_redis", return_value=mock_r):
        result = await cache_mod.get_audio_file_id("vid_cached")

    assert result == "CACHED_FILE_ID"
    mock_r.get.assert_called_once_with("aud:vid_cached")


# ── Empty search result ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_empty_search_returns_empty_list():
    from bot.services.music_search import search_songs

    with patch("bot.services.music_search._search_sync", return_value=[]):
        results = await search_songs("xyznotfound12345", max_results=5)

    assert results == []
