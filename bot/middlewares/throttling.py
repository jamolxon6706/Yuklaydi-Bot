from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from bot.config import settings
from bot.services.cache import check_rate_limit


class ThrottlingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if user_id is None or user_id in settings.admin_ids:
            return await handler(event, data)

        allowed, remaining = await check_rate_limit(user_id)
        if not allowed:
            lang = data.get("user_lang", settings.default_lang)
            msgs = {
                "uz": f"⏱ Biroz sekinroq! Iltimos, {remaining} soniya kuting.",
                "ru": f"⏱ Помедленнее! Подождите {remaining} секунд.",
                "en": f"⏱ Slow down! Please wait {remaining} seconds.",
            }
            await event.answer(msgs.get(lang, msgs["en"]))
            return
        return await handler(event, data)
