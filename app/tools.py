"""Tool factory for the tutor agent.

When `TAVILY_API_KEY` is set, the agent gets a single `TavilySearch`
tool. The LLM decides per-turn whether to call it (the system prompt's
rule 9 nudges it to verify version-specific Python APIs and external
library signatures before answering, but stay direct on basic concepts).

When the key is absent, returns `[]` — the agent runs in pure-LLM mode
and the system prompt's rule 9 is also dropped (see
`app.prompts.tutor.build_system_prompt`) so we never instruct the
model to call a tool that isn't there.

`max_results=3` and `include_answer="basic"` keep the response payload
small (Tavily's pre-summarised answer + a few sources) so the LLM gets
useful context without a 10kB blob.
"""

from __future__ import annotations

from collections.abc import Sequence

from langchain_core.tools import BaseTool
from langchain_tavily import TavilySearch

from app.config import get_settings


def build_tools() -> Sequence[BaseTool]:
    """Return the list of tools the agent can call.

    Empty when `TAVILY_API_KEY` is not configured — `app.agent.build_agent`
    branches on `bool(build_tools())` to decide whether to append the
    grounding rule to the system prompt.
    """
    settings = get_settings()
    if not settings.tavily_api_key:
        return []
    return [
        TavilySearch(
            max_results=3,
            include_answer="basic",
            search_depth="basic",
        )
    ]
