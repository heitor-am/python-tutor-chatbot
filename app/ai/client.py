"""LangChain chat model wired through OpenRouter.

OpenRouter exposes an OpenAI-compatible Chat Completions endpoint, so
`ChatOpenAI` with a custom `base_url` is the cleanest path — no extra
provider dependency, full control over headers (HTTP-Referer + X-Title
identify the app on the OpenRouter dashboard).

LangChain's chat model handles its own retry / timeout logic via
`max_retries` and `timeout`, so no tenacity wrapper here.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config import get_settings
from app.core.exceptions import LLMUnavailableError


def get_openrouter_chat_model() -> ChatOpenAI:
    """Build a `ChatOpenAI` pointed at OpenRouter, ready for `create_agent`.

    Raises `LLMUnavailableError` at call time if `OPENROUTER_API_KEY` is
    unset, so the caller fails fast at agent construction instead of
    blowing up on the first user message.
    """
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise LLMUnavailableError("OPENROUTER_API_KEY is not configured")

    return ChatOpenAI(
        model=settings.openrouter_chat_model,
        base_url=settings.openrouter_base_url,
        api_key=SecretStr(settings.openrouter_api_key),
        default_headers={
            "HTTP-Referer": settings.openrouter_app_url,
            "X-Title": settings.openrouter_app_name,
        },
        timeout=60.0,
        max_retries=3,
    )
