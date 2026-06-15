from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from bot.config import settings
from bot.services.cache import get_user_lang


class UserLangMiddleware(BaseMiddleware):
    """Attach user_lang to handler data from Redis cache (fast path) or DB."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id: Optional[int] = None

        if isinstance(event, Update):
            for attr in ("message", "callback_query", "inline_query"):
                obj = getattr(event, attr, None)
                if obj and obj.from_user:
                    user_id = obj.from_user.id
                    break
        else:
            from_user = getattr(event, "from_user", None)
            if from_user:
                user_id = from_user.id

        lang = settings.default_lang
        if user_id:
            cached = await get_user_lang(user_id)
            if cached:
                lang = cached
            else:
                user_repo = data.get("user_repo")
                if user_repo:
                    user = await user_repo.get(user_id)
                    if user:
                        lang = user.lang

        data["user_lang"] = lang
        return await handler(event, data)
