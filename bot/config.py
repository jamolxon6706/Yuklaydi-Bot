from __future__ import annotations

from typing import List
from typing_extensions import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    bot_token: str
    telegram_api_id: int
    telegram_api_hash: str
    local_api_url: str = ""  # empty = use standard Telegram cloud API

    # Database
    database_url: str = "postgresql+asyncpg://postgres:1@localhost:5432/vidbot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Lyrics
    genius_token: str = ""
    musixmatch_token: str = ""
    audd_token: str = ""

    # Bot config
    admin_ids: Annotated[List[int], NoDecode] = []
    default_lang: str = "uz"
    max_file_mb: int = 50
    download_dir: str = "./downloads"
    worker_concurrency: int = 5
    cookies_file: str = ""

    # Rate limiting
    rate_limit_requests: int = 10
    rate_limit_window: int = 60

    # Fairness / scale
    per_user_download_cap: int = 3       # max simultaneous fresh downloads per user
    yt_dlp_worker_concurrency: int = 3   # max concurrent yt-dlp calls per worker process
    job_timeout: int = 90                # arq job hard timeout (seconds)
    max_queue_depth: int = 2000          # reject new jobs above this depth

    # Logging
    log_level: str = "INFO"

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v

    @property
    def max_file_bytes(self) -> int:
        return self.max_file_mb * 1024 * 1024

    @property
    def use_local_api(self) -> bool:
        return bool(self.local_api_url)


settings = Settings()
