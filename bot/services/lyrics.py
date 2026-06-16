from __future__ import annotations

import re
from typing import Optional

from bot.config import settings
from bot.logger import logger
from bot.services.cache import get_song_cache, set_song_cache

LYRICS_PAGE_SIZE = 3000


def clean_lyrics(text: str) -> str:
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def paginate_lyrics(text: str) -> list[str]:
    if len(text) <= LYRICS_PAGE_SIZE:
        return [text]
    pages = []
    while text:
        chunk = text[:LYRICS_PAGE_SIZE]
        last_nl = chunk.rfind("\n")
        if last_nl > LYRICS_PAGE_SIZE // 2:
            chunk = text[:last_nl]
        pages.append(chunk.strip())
        text = text[len(chunk):].lstrip("\n")
    return pages


def _clean_search_query(title: str, artist: str) -> tuple[str, str]:
    """Remove junk from YouTube-sourced titles before sending to lyrics APIs."""
    # Strip things like "(Official Video)", "Official Music Video", etc.
    junk = re.compile(
        r"\s*[\(\[]\s*(official|audio|lyrics?|hd|4k|hq|full\s+song|feat\.?\s+[^\)\]]+|mv|visualizer)\s*[\)\]]"
        r"|\s+(official\s+)?(music\s+)?(video|audio|lyric|hd|mv|4k)\b"
        r"|\s*-\s*official.*$"
        r"|\s*\|\s.*$",
        re.IGNORECASE,
    )
    clean_title = junk.sub("", title).strip(" -|")
    # Shorten artist name: take the first "word group" before &, feat, x, etc.
    clean_artist = re.split(r"\s+(?:feat\.?|ft\.?|&|x|vs\.?)\s+", artist, flags=re.IGNORECASE)[0].strip()
    return clean_title, clean_artist


async def _search_genius(title: str, artist: str) -> Optional[str]:
    if not settings.genius_token:
        return None
    try:
        import asyncio
        import lyricsgenius

        genius = lyricsgenius.Genius(
            settings.genius_token,
            timeout=10,
            retries=1,
            verbose=False,
            remove_section_headers=True,
        )
        genius.skip_non_songs = True

        loop = asyncio.get_event_loop()
        song = await loop.run_in_executor(
            None,
            lambda: genius.search_song(title, artist, get_full_info=False),
        )
        if song and song.lyrics:
            return clean_lyrics(song.lyrics)
    except Exception as e:
        err = str(e)
        if "403" in err or "429" in err:
            logger.warning(f"Genius blocked ({err[:60]}), skipping")
        else:
            logger.warning(f"Genius lookup failed: {err[:120]}")
    return None


async def _search_musixmatch(title: str, artist: str) -> Optional[str]:
    if not settings.musixmatch_token:
        return None
    try:
        import aiohttp
        params = {
            "format": "json",
            "namespace": "lyrics_richsynced",
            "q_track": title,
            "q_artist": artist,
            "apikey": settings.musixmatch_token,
            "f_has_lyrics": "1",
            "page_size": "1",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.musixmatch.com/ws/1.1/track.search",
                params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        track_list = (data.get("message", {}).get("body", {}) or {}).get("track_list", [])
        if not track_list:
            return None

        track_id = track_list[0]["track"]["track_id"]
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.musixmatch.com/ws/1.1/track.lyrics.get",
                params={"track_id": track_id, "apikey": settings.musixmatch_token, "format": "json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        lyrics_body = (data.get("message", {}).get("body", {}) or {}).get("lyrics", {}).get("lyrics_body", "")
        if lyrics_body and len(lyrics_body) > 50:
            return clean_lyrics(lyrics_body)
    except Exception as e:
        logger.warning(f"Musixmatch lookup failed: {e}")
    return None


async def get_lyrics(title: str, artist: str) -> Optional[str]:
    """Fetch lyrics: check cache → Genius → Musixmatch."""
    cached = await get_song_cache(title, artist)
    if cached and cached.get("lyrics"):
        return cached["lyrics"]

    clean_title, clean_artist = _clean_search_query(title, artist)

    lyrics = await _search_genius(clean_title, clean_artist)

    if not lyrics and settings.musixmatch_token:
        lyrics = await _search_musixmatch(clean_title, clean_artist)

    if lyrics:
        await set_song_cache(title, artist, {"lyrics": lyrics})

    return lyrics
