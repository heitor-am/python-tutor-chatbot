"""Chainlit handlers — entry point for `chainlit run app/main.py`.

Each browser session gets its own `build_agent()` instance + a stable
`thread_id`, so:

- Conversation memory (LangGraph `InMemorySaver`) is per-session — opening
  a second tab starts a fresh chat.
- The agent object is built once per session, not per message; the
  `ChatOpenAI` constructor is cheap (no network on construction) so the
  cost is negligible.

Streaming: `agent.astream(stream_mode="messages")` yields
`(BaseMessage, metadata)` tuples for each LLM token chunk. We forward
the chunk content to `cl.Message.stream_token()` so the UI renders
tokens as they arrive. The `cl.AsyncLangchainCallbackHandler` is passed
as a callback so Chainlit shows the LLM call as a visible Step in the
sidebar.

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
    callback = cl.AsyncLangchainCallbackHandler()

    try:
        async for chunk, _metadata in agent.astream(
            {"messages": [{"role": "user", "content": message.content}]},
            config={
                "configurable": {"thread_id": thread_id},
                "callbacks": [callback],
            },
            stream_mode="messages",
        ):
            # Skip non-AI chunks (tool messages, system) — only assistant
            # tokens go to the user-facing bubble.
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                content = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                await response.stream_token(content)
    except _FRIENDLY_LLM_ERRORS as exc:
        # Log the structured error for debugging; show the user something
        # actionable instead of an exception trace in the chat bubble.
        logger.warning("llm_error", error_type=type(exc).__name__, message=str(exc))
        await response.stream_token(
            "⚠️ Não consegui responder agora — o serviço de LLM retornou um erro temporário "
            "(rate limit, timeout ou indisponibilidade). Tente novamente em alguns segundos."
        )

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
