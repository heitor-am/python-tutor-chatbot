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
"""

from __future__ import annotations

import uuid

import chainlit as cl
from langchain_core.messages import AIMessageChunk

from app.agent import build_agent
from app.core.logging import configure_logging

configure_logging()


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

    await response.send()
