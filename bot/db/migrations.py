"""Safe, idempotent DB migrations run at startup before create_all."""
from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger("yuklaydi.migrations")

_ALTER_STMTS = [
    # users — new columns
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(128)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(256)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active TIMESTAMPTZ",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS recognitions_count INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS searches_count INTEGER DEFAULT 0",
    # downloads — new column
    "ALTER TABLE downloads ADD COLUMN IF NOT EXISTS from_cache BOOLEAN DEFAULT FALSE",
    # daily_stats — new columns
    "ALTER TABLE daily_stats ADD COLUMN IF NOT EXISTS searches INTEGER DEFAULT 0",
    "ALTER TABLE daily_stats ADD COLUMN IF NOT EXISTS audio_sent INTEGER DEFAULT 0",
    "ALTER TABLE daily_stats ADD COLUMN IF NOT EXISTS cache_hits INTEGER DEFAULT 0",
]

_DEFAULT_WELCOME = {
    "uz": (
        "👋 Salom, <b>{first_name}</b>!\n\n"
        "🎬 Video yuklash uchun havola yuboring.\n"
        "🎵 Qo'shiq topish uchun musiqa nomi yoki ovozli xabar yuboring.\n\n"
        "<i>🤖 @vidyuklaydi_bot</i>"
    ),
    "ru": (
        "👋 Привет, <b>{first_name}</b>!\n\n"
        "🎬 Отправьте ссылку для скачивания видео.\n"
        "🎵 Отправьте название песни или голосовое сообщение для поиска.\n\n"
        "<i>🤖 @vidyuklaydi_bot</i>"
    ),
    "en": (
        "👋 Hello, <b>{first_name}</b>!\n\n"
        "🎬 Send a link to download a video.\n"
        "🎵 Send a song name or voice message to find music.\n\n"
        "<i>🤖 @vidyuklaydi_bot</i>"
    ),
}

_DEFAULT_SETTINGS = {
    "required_channel_id": "",
    "required_channel_title": "",
    "required_channel_url": "",
}


async def run_migrations(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        for stmt in _ALTER_STMTS:
            try:
                await conn.execute(text(stmt))
            except Exception as e:
                logger.debug(f"Migration skipped ({stmt[:40]}...): {e}")

        # Seed welcome messages
        for lang, txt in _DEFAULT_WELCOME.items():
            await conn.execute(
                text(
                    "INSERT INTO welcome_messages (lang, text) VALUES (:lang, :text) "
                    "ON CONFLICT (lang) DO NOTHING"
                ),
                {"lang": lang, "text": txt},
            )

        # Seed default settings
        for key, value in _DEFAULT_SETTINGS.items():
            await conn.execute(
                text(
                    "INSERT INTO settings (key, value) VALUES (:key, :value) "
                    "ON CONFLICT (key) DO NOTHING"
                ),
                {"key": key, "value": value},
            )

    logger.info("DB migrations complete")
