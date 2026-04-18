"""Chainlit handlers — wired in Block 3.

Scaffold stage: this module exposes the entry point Chainlit imports
(`chainlit run app/main.py`) but contains no handlers yet. Those land
in Block 3 once the agent (Block 2) is in place.
"""

from __future__ import annotations

from app.core.logging import configure_logging

configure_logging()
