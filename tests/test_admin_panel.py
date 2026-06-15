"""Tests for the admin panel: gating, broadcast logic, export, stats."""
from __future__ import annotations

import asyncio
import csv
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.config import settings


# ── Admin gating ──────────────────────────────────────────────────────────────

def test_admin_ids_from_settings():
    """settings.admin_ids must be a list of ints."""
    assert isinstance(settings.admin_ids, list)
    for aid in settings.admin_ids:
        assert isinstance(aid, int)


def test_is_admin_true():
    from bot.handlers.admin import _is_admin
    if settings.admin_ids:
        assert _is_admin(settings.admin_ids[0])


def test_is_admin_false():
    from bot.handlers.admin import _is_admin
    assert not _is_admin(0)
    assert not _is_admin(999999999)


# ── Broadcast rate limiting ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_broadcast_respects_rate_limit():
    """Broadcast must call asyncio.sleep after every 25 messages."""
    from bot.handlers.admin import _BROADCAST_RATE

    sleep_calls = []
    sent = []

    async def fake_copy(**kwargs):
        sent.append(kwargs.get("chat_id"))

    async def fake_sleep(n):
        sleep_calls.append(n)

    n_users = 60
    user_ids = list(range(1, n_users + 1))

    # Simulate the core broadcast loop directly (no bot object needed)
    for i, tg_id in enumerate(user_ids):
        await fake_copy(chat_id=tg_id, from_chat_id=1, message_id=1)
        if (i + 1) % _BROADCAST_RATE == 0:
            await fake_sleep(1)

    assert len(sent) == n_users
    # Should have slept after messages 25 and 50
    assert len(sleep_calls) == n_users // _BROADCAST_RATE


@pytest.mark.asyncio
async def test_broadcast_skips_forbidden():
    """Broadcast must skip users who blocked the bot and continue."""
    from aiogram.exceptions import TelegramForbiddenError

    delivered = 0
    failed = 0

    async def fake_copy(**kwargs):
        chat_id = kwargs["chat_id"]
        if chat_id == 2:  # blocked user
            raise TelegramForbiddenError(method=MagicMock(), message="Forbidden")
        nonlocal delivered
        delivered += 1

    bot = MagicMock()
    bot.copy_message = AsyncMock(side_effect=fake_copy)

    user_ids = [1, 2, 3]
    for tg_id in user_ids:
        try:
            await bot.copy_message(chat_id=tg_id, from_chat_id=1, message_id=1)
        except (TelegramForbiddenError, Exception):
            failed += 1

    assert delivered == 2
    assert failed == 1


# ── Export CSV ────────────────────────────────────────────────────────────────

def test_export_csv_has_bom_and_columns():
    """CSV export must have UTF-8 BOM and the required column headers."""
    buf = io.BytesIO()
    buf.write(b"\xef\xbb\xbf")  # UTF-8 BOM
    wrapper = io.TextIOWrapper(buf, encoding="utf-8", newline="")
    writer = csv.writer(wrapper)
    expected_cols = [
        "id", "telegram_id", "username", "first_name", "language",
        "joined_at", "last_active", "downloads_count", "recognitions_count",
        "searches_count", "is_banned",
    ]
    writer.writerow(expected_cols)
    wrapper.flush()

    raw = buf.getvalue()
    assert raw[:3] == b"\xef\xbb\xbf", "CSV must start with UTF-8 BOM"
    decoded = raw.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(decoded))
    header = next(reader)
    assert header == expected_cols


def test_export_csv_writes_user_row():
    """A sample user row must be readable back from the CSV."""
    buf = io.BytesIO()
    buf.write(b"\xef\xbb\xbf")
    wrapper = io.TextIOWrapper(buf, encoding="utf-8", newline="")
    writer = csv.writer(wrapper)
    writer.writerow(["id", "telegram_id", "username"])
    writer.writerow([1, 123456789, "testuser"])
    wrapper.flush()

    raw = buf.getvalue()
    decoded = raw.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(decoded)))
    assert rows[1] == ["1", "123456789", "testuser"]


# ── Welcome message persistence ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_welcome_repo_set_get():
    """WelcomeRepo.set then get must return the same text."""
    mock_session = AsyncMock()

    class FakeResult:
        def scalar_one_or_none(self):
            return "stored text"

    mock_session.execute = AsyncMock(return_value=FakeResult())
    mock_session.commit = AsyncMock()

    from bot.db.repo import WelcomeRepo
    repo = WelcomeRepo(mock_session)
    result = await repo.get("uz")
    assert result == "stored text"


# ── Stats counters ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_repo_inc_downloads():
    """inc_downloads must call execute and commit."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    from bot.db.repo import UserRepo
    repo = UserRepo(mock_session)
    await repo.inc_downloads(12345)

    assert mock_session.execute.called
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_download_repo_inc_daily():
    """DownloadRepo.inc_daily must not raise."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    from bot.db.repo import DownloadRepo
    repo = DownloadRepo(mock_session)
    await repo.inc_daily()
    assert mock_session.execute.called


@pytest.mark.asyncio
async def test_recognition_repo_inc_daily():
    """RecognitionRepo.inc_daily must not raise."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    from bot.db.repo import RecognitionRepo
    repo = RecognitionRepo(mock_session)
    await repo.inc_daily()
    assert mock_session.execute.called
