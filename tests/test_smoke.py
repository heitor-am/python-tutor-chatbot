"""Scaffold-level smoke: settings, logging, exception hierarchy, and the
chat-model factory. Real agent / prompt coverage lives in `test_agent.py`
and `test_prompts.py`.

Tests build `Settings` directly (or override `client_module.get_settings`)
so cases stay independent and don't leak via the `lru_cache`.
"""

from __future__ import annotations

import pytest

import app
from app.ai import client as client_module
from app.config import Settings, get_settings
from app.core.exceptions import AppError, LLMUnavailableError
from app.core.logging import configure_logging


def test_package_exposes_version() -> None:
    assert app.__version__ == "0.1.0"


def test_settings_default_values_match_pkg_intent() -> None:
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.openrouter_chat_model == "anthropic/claude-haiku-4.5"
    assert s.openrouter_app_name == "Python Tutor Chatbot"
    assert s.environment == "development"
    assert s.tavily_api_key == ""


def test_settings_cache_returns_same_instance() -> None:
    get_settings.cache_clear()
    assert get_settings() is get_settings()


def test_logging_configures_in_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        client_module,
        "get_settings",
        lambda: Settings(_env_file=None, environment="development"),  # type: ignore[call-arg]
    )
    configure_logging()


def test_logging_configures_in_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    get_settings.cache_clear()
    configure_logging()


def test_chat_model_factory_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        client_module,
        "get_settings",
        lambda: Settings(_env_file=None, openrouter_api_key=""),  # type: ignore[call-arg]
    )
    with pytest.raises(LLMUnavailableError, match="OPENROUTER_API_KEY"):
        client_module.get_openrouter_chat_model()


def test_chat_model_factory_returns_chatopenai_when_key_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        client_module,
        "get_settings",
        lambda: Settings(_env_file=None, openrouter_api_key="sk-test"),  # type: ignore[call-arg]
    )
    model = client_module.get_openrouter_chat_model()
    # Headers and base_url are wired through so OpenRouter sees the right app.
    assert model.openai_api_base == "https://openrouter.ai/api/v1"
    assert model.default_headers == {
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Python Tutor Chatbot",
    }


def test_exception_hierarchy() -> None:
    assert issubclass(LLMUnavailableError, AppError)
