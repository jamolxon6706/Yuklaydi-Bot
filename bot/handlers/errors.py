from __future__ import annotations

from aiogram import Router
from aiogram.types import ErrorEvent, InaccessibleMessage, Message

from bot.logger import logger

router = Router()

GENERIC_ERRORS = {
    "uz": "❌ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
    "ru": "❌ Произошла ошибка. Попробуйте позже.",
    "en": "❌ An error occurred. Please try again later.",
}


@router.error()
async def global_error_handler(event: ErrorEvent):
    logger.exception(f"Unhandled error: {event.exception}", exc_info=event.exception)
    try:
        update = event.update
        lang = "en"
        msg: Message | InaccessibleMessage | None = None

        if update.message:
            msg = update.message
        elif update.callback_query:
            msg = update.callback_query.message

        if isinstance(msg, Message):
            await msg.answer(GENERIC_ERRORS.get(lang, GENERIC_ERRORS["en"]))
    except Exception as e:
        logger.error(f"Error in error handler: {e}")
