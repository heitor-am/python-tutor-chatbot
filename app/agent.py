"""Agent factory — `create_agent` from `langchain.agents`.

This is the modern canonical pattern from `docs.langchain.com/oss/python/langchain/`:
`create_agent` orchestrates via LangGraph internally and ships built-in
support for tool calling, thread-based memory (via a checkpointer), and
streaming. Replaces the legacy LCEL-chain + `RunnableWithMessageHistory`
combo, which is no longer in the docs.

Memory: `InMemorySaver` keeps conversation state in process memory keyed
by `thread_id` (passed in `config={"configurable": {"thread_id": ...}}`
on each `agent.invoke`). For this single-instance chat demo it's the
right fit — survives within the process, resets on restart. Persistence
across restarts would swap to `RedisSaver` or `PostgresSaver` without
any code change to the agent itself.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.ai.client import get_openrouter_chat_model
from app.prompts.tutor import build_system_prompt
from app.tools import build_tools

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


def build_agent(
    *,
    model: BaseChatModel | None = None,
    checkpointer: InMemorySaver | None = None,
) -> Any:  # CompiledStateGraph[...] — generic params depend on tools/state shape
    """Construct the tutor agent.

    Both `model` and `checkpointer` are optional injections so tests
    can swap a fake chat model and start each test with a fresh saver
    without touching the production wiring.
    """
    chat_model = model if model is not None else get_openrouter_chat_model()
    saver = checkpointer if checkpointer is not None else InMemorySaver()
    tools = build_tools()
    system_prompt = build_system_prompt(with_grounding=bool(tools))

    return create_agent(
        model=chat_model,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=saver,
    )
