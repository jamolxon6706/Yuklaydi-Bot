from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.db.repo import DownloadRepo, SongCacheRepo, UserRepo
from bot.db.session import async_session_factory


class DbMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session_factory() as session:
            data["session"] = session
            data["user_repo"] = UserRepo(session)
            data["download_repo"] = DownloadRepo(session)
            data["song_repo"] = SongCacheRepo(session)
            return await handler(event, data)
