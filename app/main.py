"""Chainlit handlers — entry point for `chainlit run app/main.py`.

Each browser session gets its own `build_agent()` instance + a stable
`thread_id`, so:

- Conversation memory (LangGraph `InMemorySaver`) is per-session — opening
  a second tab starts a fresh chat.
- The agent object is built once per session, not per message; the
  `ChatOpenAI` constructor is cheap (no network on construction) so the
  cost is negligible.

Streaming strategy (`on_message`):
    `agent.astream(stream_mode="messages")` yields `(BaseMessage, metadata)`
    tuples for each LLM token chunk. In a tool-calling agent the model is
    invoked *multiple times*: once per tool round plus a final answer.
    Intermediate model calls emit their own content (reasoning like "vou
    buscar mais detalhes…") before producing `tool_call_chunks`, and we do
    NOT want that content in the user-facing bubble.

    We buffer content chunks per `message.id` and, once the stream is done,
    flush only the final message — i.e. the one whose chunks never carried
    `tool_call_chunks`. Emission is via `cl.Message.stream_token()` so the
    UI still gets the typewriter effect, just delayed until after the tool
    rounds finish (users see the Chainlit Step progress in the sidebar
    during that window — same UX as Claude.ai / ChatGPT tool use).

Errors from the LLM provider (rate limit, timeout, transient 5xx) are
caught and surfaced as a friendly message in the chat — never as a
stack trace in the UI.
"""

from __future__ import annotations

import uuid

import chainlit as cl
import structlog
from langchain_core.messages import AIMessageChunk
from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError

from app.agent import build_agent
from app.core.logging import configure_logging

configure_logging()

logger = structlog.get_logger()

# Error families surfaced as a friendly message + a structured log line.
# Anything else still crashes loudly (we want stack traces for unknown
# failure modes, not silent UX-friendly messages that hide bugs).
_FRIENDLY_LLM_ERRORS = (RateLimitError, APITimeoutError, APIConnectionError, APIError)


@cl.set_starters
async def set_starters(_user: cl.User | None = None) -> list[cl.Starter]:
    """Three example questions on the welcome screen so users have a
    one-click entry point — addresses the "blank prompt" friction."""
    return [
        cl.Starter(
            label="Como criar uma lista?",
            message="Como criar uma lista em Python e quais operações básicas eu posso fazer com ela?",
        ),
        cl.Starter(
            label="Explique decorators",
            message="O que é um decorator em Python e me dê um exemplo prático de quando usar.",
        ),
        cl.Starter(
            label="Como usar async/await?",
            message="Como funciona async/await em Python? Quando devo usar e quando NÃO devo usar?",
        ),
    ]


@cl.on_chat_start
async def on_chat_start() -> None:
    cl.user_session.set("agent", build_agent())
    cl.user_session.set("thread_id", str(uuid.uuid4()))


@cl.on_message
async def on_message(message: cl.Message) -> None:
    agent = cl.user_session.get("agent")
    thread_id = cl.user_session.get("thread_id")

    response = cl.Message(content="")
    # Chainlit's LangChain callback handler emits a Step per Runnable by
    # default — that includes the "LangGraph" graph wrapper, each "model"
    # call, and each tool invocation, with the model calls dumping the
    # full message history as JSON. Whitelisting via `to_keep` to the one
    # step that has user-visible signal: the `tavily_search` tool call.
    callback = cl.LangchainCallbackHandler(to_keep=["tavily_search"])

    # Buffer content tokens per `message.id`. If any chunk of a given
    # message id carries `tool_call_chunks`, that id is intermediate
    # reasoning (the model announcing its next tool call, e.g. "vou buscar
    # mais detalhes") — drop its buffer. Otherwise the id represents the
    # final answer and we flush it.
    buffers: dict[str, list[str]] = {}
    tool_calling_ids: set[str] = set()

    try:
        async for chunk, _metadata in agent.astream(
            {"messages": [{"role": "user", "content": message.content}]},
            config={
                "configurable": {"thread_id": thread_id},
                "callbacks": [callback],
            },
            stream_mode="messages",
        ):
            if not isinstance(chunk, AIMessageChunk):
                continue
            msg_id = chunk.id or "default"
            if chunk.tool_call_chunks:
                tool_calling_ids.add(msg_id)
                buffers.pop(msg_id, None)
                continue
            if msg_id in tool_calling_ids:
                continue
            if chunk.content:
                text = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                buffers.setdefault(msg_id, []).append(text)
    except _FRIENDLY_LLM_ERRORS as exc:
        # Log the structured error for debugging; show the user something
        # actionable instead of an exception trace in the chat bubble.
        logger.warning("llm_error", error_type=type(exc).__name__, message=str(exc))
        await response.stream_token(
            "⚠️ Não consegui responder agora — o serviço de LLM retornou um erro temporário "
            "(rate limit, timeout ou indisponibilidade). Tente novamente em alguns segundos."
        )
        await response.send()
        return

    # Flush every buffered final-answer message token-by-token so the UI
    # still renders with a typewriter cadence.
    for msg_id, buffer in buffers.items():
        if msg_id in tool_calling_ids:
            continue
        for token in buffer:
            await response.stream_token(token)

    await response.send()


@cl.on_feedback
async def on_feedback(feedback: cl.types.Feedback) -> None:
    """Capture thumbs up / down. We log structured events so a future
    persistence layer (DB, analytics) can be wired by replacing the
    handler body — no UI change required.
    """
    sentiment = (
        "positive" if feedback.value > 0 else "negative" if feedback.value < 0 else "neutral"
    )
    logger.info(
        "feedback_received",
        sentiment=sentiment,
        value=feedback.value,
        message_id=feedback.forId,
        thread_id=feedback.threadId,
        comment=feedback.comment,
    )
