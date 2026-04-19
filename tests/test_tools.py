"""Tests for the tool factory.

Two branches: no `TAVILY_API_KEY` → `[]` (pure-LLM mode), key set → a
single `TavilySearch` tool. Tests don't make network calls — `TavilySearch`
construction reads the env var but doesn't hit the API until the LLM
actually invokes the tool.
"""

from __future__ import annotations

import pytest
from langchain_tavily import TavilySearch

from app.config import get_settings
from app.tools import build_tools


class TestBuildTools:
    def test_returns_empty_when_tavily_key_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TAVILY_API_KEY", "")
        get_settings.cache_clear()
        assert build_tools() == []

    def test_returns_tavily_search_when_key_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-fake-key-for-test")
        get_settings.cache_clear()
        tools = build_tools()
        assert len(tools) == 1
        assert isinstance(tools[0], TavilySearch)
        # Configured to keep the payload small — see app/tools.py rationale.
        assert tools[0].max_results == 3
        assert tools[0].include_answer == "basic"

    def test_grounding_disabled_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Belt-and-suspenders: `app.agent.build_agent` reads `bool(build_tools())`
        # to decide whether to append rule 9 to the system prompt. If this
        # default ever flips, the prompt would lie to the model — assert it
        # explicitly here so the regression shows up at PR time.
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        get_settings.cache_clear()
        assert not build_tools()
