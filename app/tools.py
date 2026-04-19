"""Tool factory for the tutor agent.

By default returns `[]` — no tools, agent answers from the LLM alone.
The optional grounding upgrade (Tavily web search) lands here in a
later release: the factory will return `[TavilySearch(...)]` iff
`TAVILY_API_KEY` is set in the environment, so the agent degrades
gracefully to no-grounding when the key is absent.
"""

from __future__ import annotations

from collections.abc import Sequence

from langchain_core.tools import BaseTool

from app.config import get_settings


def build_tools() -> Sequence[BaseTool]:
    """Return the list of tools the agent can call.

    Currently always `[]`. The TAVILY_API_KEY check is here so the
    behaviour stays consistent once the Tavily upgrade is wired in —
    callers can already branch on `bool(build_tools())` to ask "does
    the agent have grounding?".
    """
    settings = get_settings()
    if not settings.tavily_api_key:
        return []
    # Grounding tool wired in a later release. Keeping the branch
    # empty here keeps `app/agent.py` already compatible with the
    # future shape (tools may be non-empty).
    return []
