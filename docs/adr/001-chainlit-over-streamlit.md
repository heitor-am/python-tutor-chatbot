# 001 — Chainlit over Streamlit / Gradio for the chat UI

- **Status:** accepted
- **Date:** 2026-04-18
- **Deciders:** @heitor-am

## Context

The deliverable is a chat experience: streaming responses, multi-turn memory, a feedback signal, and starter suggestions. Three plausible Python-native choices:

- **Streamlit** — generalist dashboard framework. Chat is bolted on (`st.chat_input`, `st.chat_message`) but session state is fiddly and streaming requires manual `st.write_stream`.
- **Gradio** — ML-demo-first. `gr.ChatInterface` works but the UX has the "ML demo on Hugging Face Space" smell — fine for a model card, less polished as a tutor.
- **Chainlit** — chat-native. Streaming, message history, thumbs feedback, action buttons, starter suggestions, and a polished mobile-friendly UI all built in.

The portfolio viewer will judge polish quickly; bolting chat onto a dashboard framework would lose points for what's basically a packaging choice.

## Decision

Use Chainlit 2.x with the `cl.on_chat_start` / `cl.on_message` / `cl.on_feedback` handler pattern. Streaming via `agent.astream(stream_mode="messages")` piped to `cl.Message.stream_token()`.

## Consequences

**Positive:**
- Streaming, history, feedback, starters, "Calling LLM" steps in the sidebar — all out of the box.
- LangChain integration via `cl.AsyncLangchainCallbackHandler` is officially supported, no glue code to maintain.
- Welcome screen is a markdown file (`chainlit.md`), not a templating system.
- Mobile UI is decent without any extra work.

**Negative:**
- Smaller ecosystem than Streamlit; less help on Stack Overflow.
- Chainlit-flavoured opinions (sidebar layout, threading model) — escaping them means writing your own React frontend.
- Default UI strings are English; pt-BR translation file is missing (cosmetic — the tutor's *content* is PT via the system prompt).

**Trade-offs accepted:**
- Coupled to one framework. If Chainlit goes unmaintained, the migration is "rewrite the UI layer" — manageable because the agent (`app/agent.py`) and prompts (`app/prompts/tutor.py`) are framework-free.

## Alternatives considered

- **Streamlit** — rejected: chat is not its primary use case; `st.chat_*` works but is a lower-quality version of what Chainlit ships natively.
- **Gradio** — rejected: ML-demo aesthetic doesn't match a "tutor" framing; less control over the conversation feel.
- **Custom React + FastAPI WebSocket** — rejected: justified only if Chainlit's opinions actually got in the way. They don't, at this scope.

## References

- `app/main.py` (handlers)
- `chainlit.md` (welcome screen)
- `.chainlit/config.toml` (UI tweaks)
- Chainlit docs: https://docs.chainlit.io
