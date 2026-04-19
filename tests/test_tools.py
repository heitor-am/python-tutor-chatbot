"""Tests for the tool factory.

Two branches: no `TAVILY_API_KEY` → `[]` (pure-LLM mode), key set → a
single `TavilySearch` tool. We swap `get_settings` directly instead of
relying on env-var overrides because pydantic-settings reads `.env` at
`Settings` construction time, and a `.env` file with a real key on the
dev machine would shadow `monkeypatch.delenv`.
"""

from __future__ import annotations

import pytest
from langchain_tavily import TavilySearch

from app import tools as tools_module
from app.config import Settings
from app.tools import build_tools


def _settings_with(tavily_api_key: str) -> Settings:
    """Build a Settings ignoring `.env` so test branches are deterministic."""
    return Settings(_env_file=None, tavily_api_key=tavily_api_key)  # type: ignore[call-arg]


class TestBuildTools:
    def test_returns_empty_when_tavily_key_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(tools_module, "get_settings", lambda: _settings_with(""))
        assert build_tools() == []

    def test_returns_tavily_search_when_key_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            tools_module, "get_settings", lambda: _settings_with("tvly-fake-key-for-test")
        )
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
        monkeypatch.setattr(tools_module, "get_settings", lambda: _settings_with(""))
        assert not build_tools()
