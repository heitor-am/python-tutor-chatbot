"""Tests for the tool factory.

Block 4.5 will add the Tavily branch; for now both branches return `[]`,
but the env-var coupling is what we lock in here so the future upgrade
doesn't need to re-introduce the test scaffolding.
"""

from __future__ import annotations

import pytest

from app.config import get_settings
from app.tools import build_tools


class TestBuildTools:
    def test_returns_empty_when_tavily_key_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TAVILY_API_KEY", "")
        get_settings.cache_clear()
        assert build_tools() == []

    def test_returns_empty_when_tavily_key_set_but_grounding_not_wired_yet(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Setting the key today still returns [] — Block 4.5 will replace
        # this with a non-empty list. Locking the current behaviour so the
        # upgrade lands as a deliberate code change, not a silent feature.
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-fake-key-for-test")
        get_settings.cache_clear()
        assert build_tools() == []
