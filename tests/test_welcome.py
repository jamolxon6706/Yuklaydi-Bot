"""Tests for the DB-editable welcome message system."""
from __future__ import annotations

import html

from bot.handlers.start import _render, _DEFAULT_WELCOME


def test_render_basic():
    tpl = "Hello, {first_name}! Your username is {username}."
    result = _render(tpl, "Alice", "alice_bot")
    assert result == "Hello, Alice! Your username is alice_bot."


def test_render_html_escapes_user_values():
    tpl = "Hi, {first_name}!"
    result = _render(tpl, "<script>alert(1)</script>", "")
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_render_empty_username():
    tpl = "Hi {first_name} (@{username})"
    result = _render(tpl, "Bob", "")
    assert "Bob" in result
    assert "{first_name}" not in result
    assert "{username}" not in result


def test_default_welcome_all_languages():
    for lang in ("uz", "ru", "en"):
        assert lang in _DEFAULT_WELCOME
        assert "{first_name}" in _DEFAULT_WELCOME[lang]


def test_default_welcome_renders_safely():
    malicious = '<b>bold</b> & "quotes"'
    for lang in ("uz", "ru", "en"):
        result = _render(_DEFAULT_WELCOME[lang], malicious, "")
        assert "<b>bold</b>" not in result  # escaped
        assert "&lt;b&gt;" in result or html.escape(malicious) in result
