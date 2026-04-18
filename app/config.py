"""Application settings loaded from environment / .env (pydantic-settings).

`get_settings()` is `lru_cache`d so the import-time validation runs once
and every consumer sees the same instance. Tests that need to vary
config call `get_settings.cache_clear()` (or build `Settings` directly).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    log_level: str = "INFO"
    environment: str = "development"

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_chat_model: str = "anthropic/claude-haiku-4.5"
    openrouter_app_name: str = "Python Tutor Chatbot"
    openrouter_app_url: str = "http://localhost:8000"

    # Optional grounding (Block 4.5). Empty => no Tavily tool, agent
    # runs without web search and degrades gracefully.
    tavily_api_key: str = ""

    git_sha: str = "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()
