# 005 — `langchain.agents.create_agent` over the legacy LCEL + `RunnableWithMessageHistory` pattern

- **Status:** accepted
- **Date:** 2026-04-18
- **Deciders:** @heitor-am

## Context

Two ways to build a stateful chat in LangChain today:

1. **LCEL chain** — `prompt | llm | StrOutputParser`, wrapped in `RunnableWithMessageHistory` for memory. This is the pattern most blog posts (and my own first instinct) reach for.
2. **`langchain.agents.create_agent`** — a higher-level entry point that orchestrates the chat via LangGraph internally. Memory comes from a `Checkpointer` (`InMemorySaver`, `RedisSaver`, etc.) keyed on `thread_id`.

Reading `docs.langchain.com/oss/python/langchain/` (current as of 2026-04-18) makes the picture clearer than my training-data instinct: every short-term memory example in the docs uses `create_agent` + `InMemorySaver`. `RunnableWithMessageHistory` doesn't appear. Using the legacy pattern would land on a PR review as "this person didn't read the current docs."

## Decision

Build the chat agent with `create_agent`, keep memory in a LangGraph `InMemorySaver`, key it on a per-session `thread_id`:

```python
agent = create_agent(
    model=chat_model,
    system_prompt=SYSTEM_PROMPT,
    tools=tools,                        # [] today; Tavily added in the optional grounding upgrade
    checkpointer=InMemorySaver(),
)

agent.invoke(
    {"messages": [{"role": "user", "content": ...}]},
    config={"configurable": {"thread_id": "session-uuid"}},
)
```

Per Chainlit session, `app/main.py` generates a `uuid4()` `thread_id` so every browser tab is isolated.

## Consequences

**Positive:**
- Aligned with the current canonical docs — a reviewer reading `langchain` recently sees the same shape.
- Tool calling, streaming (`astream(stream_mode="messages")`), and middleware (`@before_model`, `@after_model`) all integrate without extra glue. The optional grounding upgrade is literally `tools=[TavilySearch(...)]`.
- Persistence backend is a swap: dev uses `InMemorySaver`, prod-with-restart-survival would swap to `RedisSaver` or `PostgresSaver` with no agent code change.
- `thread_id` isolation is built in — different tabs, different chats, no shared state by accident.

**Negative:**
- `create_agent` returns a `CompiledStateGraph` whose generic params are non-trivial (`AgentState[ResponseT], ContextT, ...`); we annotate the return as `Any` in `app/agent.py` rather than fighting the type. Documented in the function comment.
- LangGraph dep is now mandatory (it was optional under LCEL). Acceptable: it's already pulled in transitively by `langchain` 1.0+.

**Trade-offs accepted:**
- We use `create_agent` even though the chat is currently linear (no tools, no branching). The value isn't in today's behaviour but in the future shape: when Tavily grounding lands (optional Block 4.5), the agent already routes tool calls correctly without any architectural change.

## Alternatives considered

- **LCEL + `RunnableWithMessageHistory`** — works, but absent from current docs. Rejected on signal grounds, not capability.
- **Raw `langgraph.StateGraph` with hand-coded nodes** — overkill for a linear chat. Worth revisiting if branching logic appears (e.g. an explicit topic-classifier node that routes on/off-topic before reaching the tutor).
- **`init_chat_model("auto", model_provider="openrouter")`** — concise but doesn't expose the OpenRouter `HTTP-Referer` / `X-Title` headers cleanly; we want those for dashboard attribution. Stick with explicit `ChatOpenAI`.

## References

- `app/agent.py` (`build_agent`)
- `app/main.py` (per-session `thread_id` generation)
- LangChain short-term memory docs: https://docs.langchain.com/oss/python/langchain/short-term-memory
- LangChain `create_agent` reference: https://docs.langchain.com/oss/python/langchain/agents
