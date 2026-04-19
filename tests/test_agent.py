"""Agent construction + thread-based memory tests.

The chat model is mocked with `langchain_core`'s `FakeMessagesListChatModel`
so the agent runs end-to-end without touching the network. Memory is
exercised by invoking twice with the same `thread_id` and asserting the
fake model sees the first turn's messages on the second invocation.
"""

from __future__ import annotations

import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.agent import build_agent
from app.ai import client as client_module
from app.config import Settings


def _fake_model(replies: list[str]) -> FakeMessagesListChatModel:
    """Build a fake chat model that returns the given AI messages in order."""
    return FakeMessagesListChatModel(responses=[AIMessage(content=r) for r in replies])


class TestBuildAgent:
    def test_construct_with_injected_model_does_not_hit_network(self) -> None:
        # If construction tried to call OpenRouter (no API key set), this
        # would raise — instead we inject the fake. Proves the seam works.
        agent = build_agent(model=_fake_model(["unused"]), checkpointer=InMemorySaver())
        assert agent is not None

    def test_construct_with_no_model_requires_openrouter_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.core.exceptions import LLMUnavailableError

        monkeypatch.setattr(
            client_module,
            "get_settings",
            lambda: Settings(_env_file=None, openrouter_api_key=""),  # type: ignore[call-arg]
        )
        with pytest.raises(LLMUnavailableError, match="OPENROUTER_API_KEY"):
            build_agent()


class TestAgentTurn:
    def test_invoke_returns_ai_response(self) -> None:
        agent = build_agent(
            model=_fake_model(["Olá! Sou seu tutor de Python."]),
            checkpointer=InMemorySaver(),
        )
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "Oi"}]},
            config={"configurable": {"thread_id": "t-1"}},
        )
        last = result["messages"][-1]
        assert isinstance(last, AIMessage)
        assert "tutor de Python" in last.content


class TestThreadMemory:
    def test_second_invoke_sees_first_turn_in_history(self) -> None:
        # State after both turns must contain ALL four messages — this is
        # the load-bearing fact: memory really persists across invokes
        # under the same thread_id.
        agent = build_agent(
            model=_fake_model(["Resposta 1", "Resposta 2"]),
            checkpointer=InMemorySaver(),
        )
        thread = {"configurable": {"thread_id": "session-A"}}

        agent.invoke({"messages": [{"role": "user", "content": "Pergunta 1"}]}, config=thread)
        agent.invoke({"messages": [{"role": "user", "content": "Pergunta 2"}]}, config=thread)

        final_state = agent.get_state(thread).values
        contents = [m.content for m in final_state["messages"]]
        assert "Pergunta 1" in contents
        assert "Pergunta 2" in contents
        assert "Resposta 1" in contents
        assert "Resposta 2" in contents
        # And the order is preserved (P1 before P2, R1 before R2).
        assert contents.index("Pergunta 1") < contents.index("Pergunta 2")
        assert contents.index("Resposta 1") < contents.index("Resposta 2")

    def test_separate_threads_do_not_share_memory(self) -> None:
        fake = _fake_model(["Reply A", "Reply B"])
        agent = build_agent(model=fake, checkpointer=InMemorySaver())

        agent.invoke(
            {"messages": [{"role": "user", "content": "From A"}]},
            config={"configurable": {"thread_id": "thread-A"}},
        )
        agent.invoke(
            {"messages": [{"role": "user", "content": "From B"}]},
            config={"configurable": {"thread_id": "thread-B"}},
        )

        state_a = agent.get_state({"configurable": {"thread_id": "thread-A"}}).values
        state_b = agent.get_state({"configurable": {"thread_id": "thread-B"}}).values

        contents_a = [m.content for m in state_a["messages"]]
        contents_b = [m.content for m in state_b["messages"]]
        # Thread A must not see thread B's user message and vice-versa.
        assert "From A" in contents_a and "From B" not in contents_a
        assert "From B" in contents_b and "From A" not in contents_b


class TestSystemPromptToggle:
    """`build_agent` must pass `with_grounding=True` to the system-prompt
    builder iff `build_tools()` returns tools. Otherwise we'd instruct
    the model to call a tool that doesn't exist (silent behavioural bug).

    Spies on `build_system_prompt` so we don't depend on whether
    `create_agent` exposes the system prompt via state inspection.
    """

    def test_with_grounding_false_when_no_tavily_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app import agent as agent_module
        from app.config import get_settings

        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        get_settings.cache_clear()

        captured: dict[str, bool] = {}

        def spy(*, with_grounding: bool) -> str:
            captured["with_grounding"] = with_grounding
            return "system prompt"

        monkeypatch.setattr(agent_module, "build_system_prompt", spy)
        build_agent(model=_fake_model(["x"]), checkpointer=InMemorySaver())
        assert captured == {"with_grounding": False}

    def test_with_grounding_true_when_tavily_key_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app import agent as agent_module
        from app.config import get_settings

        monkeypatch.setenv("TAVILY_API_KEY", "tvly-fake-key-for-test")
        get_settings.cache_clear()

        captured: dict[str, bool] = {}

        def spy(*, with_grounding: bool) -> str:
            captured["with_grounding"] = with_grounding
            return "system prompt"

        monkeypatch.setattr(agent_module, "build_system_prompt", spy)
        build_agent(model=_fake_model(["x"]), checkpointer=InMemorySaver())
        assert captured == {"with_grounding": True}
