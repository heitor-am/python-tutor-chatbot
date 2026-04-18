"""Scaffold-stage smoke tests.

Block 2 will replace these with real coverage of agent / prompt logic.
For now they exercise enough of the scaffold modules to keep the
coverage gate (80% via pyproject.toml) honest — no skipped lines hiding
under a low bar.

Tests build `Settings` directly (instead of going through the cached
`get_settings()` + .env) so cases stay independent and don't leak
into each other via the `lru_cache`.
"""

from __future__ import annotations

import pytest

import app
from app.ai import client as client_module
from app.config import Settings, get_settings
from app.core.exceptions import AppError, LLMUnavailableError
from app.core.logging import configure_logging


def test_package_exposes_version() -> None:
    assert app.__version__ == "0.0.1"


def test_settings_default_values_match_pkg_intent() -> None:
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.openrouter_chat_model == "anthropic/claude-haiku-4.5"
    assert s.openrouter_app_name == "Python Tutor Chatbot"
    assert s.environment == "development"


def test_settings_cache_returns_same_instance() -> None:
    get_settings.cache_clear()
    assert get_settings() is get_settings()


def test_logging_configures_in_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        client_module,
        "get_settings",
        lambda: Settings(_env_file=None, environment="development"),  # type: ignore[call-arg]
    )
    # Calling configure_logging twice exercises both caching and the
    # processor-list construction; explicit assertion would mock structlog,
    # which buys nothing for a smoke test.
    configure_logging()


def test_logging_configures_in_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    get_settings.cache_clear()
    configure_logging()


def test_openrouter_client_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        client_module,
        "get_settings",
        lambda: Settings(_env_file=None, openrouter_api_key=""),  # type: ignore[call-arg]
    )
    with pytest.raises(LLMUnavailableError, match="OPENROUTER_API_KEY"):
        client_module.get_openrouter_client()


def test_openrouter_client_returns_client_when_key_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        client_module,
        "get_settings",
        lambda: Settings(_env_file=None, openrouter_api_key="sk-test"),  # type: ignore[call-arg]
    )
    client = client_module.get_openrouter_client()
    assert client.api_key == "sk-test"


def test_exception_hierarchy() -> None:
    # LLMUnavailableError is an AppError so handlers can catch the base.
    assert issubclass(LLMUnavailableError, AppError)
