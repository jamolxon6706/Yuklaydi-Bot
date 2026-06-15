import pytest
from bot.services.lyrics import clean_lyrics, paginate_lyrics


def test_clean_lyrics_removes_sections():
    raw = "[Verse 1]\nHello world\n[Chorus]\nLa la la"
    result = clean_lyrics(raw)
    assert "[Verse 1]" not in result
    assert "[Chorus]" not in result
    assert "Hello world" in result
    assert "La la la" in result


def test_clean_lyrics_removes_extra_newlines():
    raw = "Line 1\n\n\n\nLine 2"
    result = clean_lyrics(raw)
    assert "\n\n\n" not in result


def test_paginate_lyrics_short():
    text = "Short lyrics"
    pages = paginate_lyrics(text)
    assert len(pages) == 1
    assert pages[0] == text


def test_paginate_lyrics_long():
    text = "A\n" * 2000
    pages = paginate_lyrics(text)
    assert len(pages) > 1
    for page in pages:
        assert len(page) <= 3000
