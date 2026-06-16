from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    DailyStat, Download, MusicSearch, RecognitionLog,
    Setting, SongCache, User, WelcomeMessage,
)


class UserRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, tg_id: int, username: Optional[str] = None, first_name: Optional[str] = None, lang: str = "uz") -> User:
        result = await self.session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(tg_id=tg_id, lang=lang, username=username, first_name=first_name)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            await self._inc_daily(new_users=1)
        else:
            # Update profile fields
            changes = {}
            if username is not None and user.username != username:
                changes["username"] = username
            if first_name is not None and user.first_name != first_name:
                changes["first_name"] = first_name
            if changes:
                await self.session.execute(update(User).where(User.tg_id == tg_id).values(**changes))
                await self.session.commit()
        return user

    async def get(self, tg_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.tg_id == tg_id))
        return result.scalar_one_or_none()

    async def touch(self, tg_id: int) -> None:
        await self.session.execute(
            update(User).where(User.tg_id == tg_id).values(last_active=func.now())
        )
        await self.session.commit()

    async def set_lang(self, tg_id: int, lang: str) -> None:
        await self.session.execute(update(User).where(User.tg_id == tg_id).values(lang=lang))
        await self.session.commit()

    async def set_blocked(self, tg_id: int, blocked: bool) -> None:
        await self.session.execute(update(User).where(User.tg_id == tg_id).values(is_blocked=blocked))
        await self.session.commit()

    async def inc_downloads(self, tg_id: int) -> None:
        await self.session.execute(
            update(User).where(User.tg_id == tg_id).values(downloads_count=User.downloads_count + 1)
        )
        await self.session.commit()

    async def inc_recognitions(self, tg_id: int) -> None:
        await self.session.execute(
            update(User).where(User.tg_id == tg_id).values(recognitions_count=User.recognitions_count + 1)
        )
        await self.session.commit()

    async def inc_searches(self, tg_id: int) -> None:
        await self.session.execute(
            update(User).where(User.tg_id == tg_id).values(searches_count=User.searches_count + 1)
        )
        await self.session.commit()

    async def count_all(self) -> int:
        r = await self.session.execute(select(func.count()).select_from(User))
        return r.scalar_one()

    async def count_new_today(self) -> int:
        today = datetime.utcnow().date()
        r = await self.session.execute(
            select(func.count()).select_from(User).where(func.date(User.joined_at) == today)
        )
        return r.scalar_one()

    async def count_new_week(self) -> int:
        week_ago = datetime.utcnow() - timedelta(days=7)
        r = await self.session.execute(
            select(func.count()).select_from(User).where(User.joined_at >= week_ago)
        )
        return r.scalar_one()

    async def count_active(self, days: int = 7) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        r = await self.session.execute(
            select(func.count()).select_from(User).where(User.last_active >= cutoff)
        )
        return r.scalar_one()

    async def get_all_ids(self) -> list[int]:
        r = await self.session.execute(select(User.tg_id).where(User.is_blocked.is_(False)))
        return list(r.scalars().all())

    async def get_all_for_export(self) -> list[User]:
        r = await self.session.execute(select(User).order_by(User.joined_at))
        return list(r.scalars().all())

    async def _inc_daily(self, **kwargs) -> None:
        today = date.today()
        stmt = (
            insert(DailyStat)
            .values(stat_date=today, downloads=0, recognitions=0, new_users=0,
                    searches=0, audio_sent=0, cache_hits=0, **kwargs)
            .on_conflict_do_update(
                index_elements=["stat_date"],
                set_={k: DailyStat.__table__.c[k] + v for k, v in kwargs.items()},
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()


class DownloadRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: int, url: str, platform: str, kind: str,
                     status: str = "done", from_cache: bool = False) -> Download:
        dl = Download(user_id=user_id, url=url, platform=platform, kind=kind,
                      status=status, from_cache=from_cache)
        self.session.add(dl)
        await self.session.commit()
        return dl

    async def count_today(self) -> int:
        today = datetime.utcnow().date()
        r = await self.session.execute(
            select(func.count()).select_from(Download).where(func.date(Download.created_at) == today)
        )
        return r.scalar_one()

    async def count_all(self) -> int:
        r = await self.session.execute(select(func.count()).select_from(Download))
        return r.scalar_one()

    async def count_today_cache_hits(self) -> int:
        today = datetime.utcnow().date()
        r = await self.session.execute(
            select(func.count()).select_from(Download).where(
                func.date(Download.created_at) == today,
                Download.from_cache.is_(True),
            )
        )
        return r.scalar_one()

    async def top_platforms(self, limit: int = 5) -> list:
        r = await self.session.execute(
            select(Download.platform, func.count().label("cnt"))
            .group_by(Download.platform)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return list(r.fetchall())

    async def inc_daily(self, cache_hit: bool = False) -> None:
        today = date.today()
        values = {"downloads": 1}
        if cache_hit:
            values["cache_hits"] = 1
        stmt = (
            insert(DailyStat)
            .values(stat_date=today, downloads=0, recognitions=0, new_users=0,
                    searches=0, audio_sent=0, cache_hits=0)
            .on_conflict_do_update(
                index_elements=["stat_date"],
                set_={k: DailyStat.__table__.c[k] + v for k, v in values.items()},
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()


class RecognitionRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(self, user_id: int, title: str, artist: str,
                  found_lyrics: bool = False, source: str = "shazam") -> None:
        rec = RecognitionLog(user_id=user_id, title=title, artist=artist,
                             found_lyrics=found_lyrics, source=source)
        self.session.add(rec)
        await self.session.commit()

    async def count_today(self) -> int:
        today = datetime.utcnow().date()
        r = await self.session.execute(
            select(func.count()).select_from(RecognitionLog)
            .where(func.date(RecognitionLog.created_at) == today)
        )
        return r.scalar_one()

    async def count_all(self) -> int:
        r = await self.session.execute(select(func.count()).select_from(RecognitionLog))
        return r.scalar_one()

    async def inc_daily(self) -> None:
        today = date.today()
        stmt = (
            insert(DailyStat)
            .values(stat_date=today, downloads=0, recognitions=1, new_users=0,
                    searches=0, audio_sent=0, cache_hits=0)
            .on_conflict_do_update(
                index_elements=["stat_date"],
                set_={"recognitions": DailyStat.recognitions + 1},
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()


class MusicSearchRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(self, user_id: int, query: str, picked_index: Optional[int] = None) -> None:
        row = MusicSearch(user_id=user_id, query=query, picked_index=picked_index)
        self.session.add(row)
        await self.session.commit()

    async def count_today(self) -> int:
        today = datetime.utcnow().date()
        r = await self.session.execute(
            select(func.count()).select_from(MusicSearch)
            .where(func.date(MusicSearch.created_at) == today)
        )
        return r.scalar_one()

    async def count_all(self) -> int:
        r = await self.session.execute(select(func.count()).select_from(MusicSearch))
        return r.scalar_one()

    async def inc_daily(self) -> None:
        today = date.today()
        stmt = (
            insert(DailyStat)
            .values(stat_date=today, downloads=0, recognitions=0, new_users=0,
                    searches=1, audio_sent=0, cache_hits=0)
            .on_conflict_do_update(
                index_elements=["stat_date"],
                set_={"searches": DailyStat.searches + 1},
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def inc_daily_audio(self) -> None:
        today = date.today()
        stmt = (
            insert(DailyStat)
            .values(stat_date=today, downloads=0, recognitions=0, new_users=0,
                    searches=0, audio_sent=1, cache_hits=0)
            .on_conflict_do_update(
                index_elements=["stat_date"],
                set_={"audio_sent": DailyStat.audio_sent + 1},
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()


class SongCacheRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def make_hash(title: str, artist: str) -> str:
        return hashlib.sha256(f"{title.lower()}|{artist.lower()}".encode()).hexdigest()

    async def get(self, title: str, artist: str) -> Optional[SongCache]:
        h = self.make_hash(title, artist)
        r = await self.session.execute(select(SongCache).where(SongCache.query_hash == h))
        return r.scalar_one_or_none()

    async def save(self, title: str, artist: str, lyrics: str) -> None:
        h = self.make_hash(title, artist)
        stmt = (
            insert(SongCache)
            .values(query_hash=h, title=title, artist=artist, lyrics=lyrics)
            .on_conflict_do_update(index_elements=["query_hash"], set_={"lyrics": lyrics})
        )
        await self.session.execute(stmt)
        await self.session.commit()


class WelcomeRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, lang: str) -> Optional[str]:
        r = await self.session.execute(
            select(WelcomeMessage.text).where(WelcomeMessage.lang == lang)
        )
        return r.scalar_one_or_none()

    async def set(self, lang: str, text: str) -> None:
        stmt = (
            insert(WelcomeMessage)
            .values(lang=lang, text=text)
            .on_conflict_do_update(index_elements=["lang"], set_={"text": text, "updated_at": func.now()})
        )
        await self.session.execute(stmt)
        await self.session.commit()


class SettingRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str, default: str = "") -> str:
        r = await self.session.execute(select(Setting.value).where(Setting.key == key))
        v = r.scalar_one_or_none()
        return v if v is not None else default

    async def set(self, key: str, value: str) -> None:
        stmt = (
            insert(Setting)
            .values(key=key, value=value)
            .on_conflict_do_update(index_elements=["key"], set_={"value": value})
        )
        await self.session.execute(stmt)
        await self.session.commit()
