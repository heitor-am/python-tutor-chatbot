# Python Tutor Chatbot

[![CI](https://github.com/heitor-am/python-tutor-chatbot/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/heitor-am/python-tutor-chatbot/actions/workflows/ci.yml)
[![Deploy](https://github.com/heitor-am/python-tutor-chatbot/actions/workflows/deploy.yml/badge.svg?branch=main)](https://github.com/heitor-am/python-tutor-chatbot/actions/workflows/deploy.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Coverage 100%](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](#testing)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Conversational Python tutor — Chainlit UI on top of LangChain `create_agent` (the modern canonical pattern; `RunnableWithMessageHistory` legacy avoided per current docs) with thread-based memory via LangGraph `InMemorySaver`. Talks to OpenRouter behind a single `ChatOpenAI` client.

> **Live:** <https://python-tutor-chatbot.fly.dev>

## Quickstart

```bash
git clone git@github.com:heitor-am/python-tutor-chatbot.git
cd python-tutor-chatbot
uv sync --all-extras

cp .env.example .env
# edit .env and set OPENROUTER_API_KEY=sk-or-...

make dev
# open http://localhost:8000
```

Or just hit production: <https://python-tutor-chatbot.fly.dev>. Fly auto-stops the machine after idle, so the first message after a quiet period pays a 2-3s cold-start.

## What it does

- Answers Python questions in PT-BR with executable examples and a clear "explain reasoning before code" structure.
- Remembers the conversation within a session via per-tab `thread_id` + LangGraph `InMemorySaver`.
- Refuses off-topic questions in one polite sentence (smoke-verified end-to-end against real OpenRouter — see PR #3 description for the test transcript).
- Streams tokens as they arrive (via `agent.astream(stream_mode="messages")` piped to `cl.Message.stream_token()`).
- Logs structured thumbs-up / thumbs-down feedback.
- Friendly chat message — not a stack trace — when the LLM provider hiccups (rate limit, timeout, transient 5xx).

## Stack

| Layer | Choice | Why |
|---|---|---|
| **UI** | Chainlit 2.x | Chat-native; streaming + history + feedback widgets out of the box (ADR-001) |
| **Orchestration** | LangChain `create_agent` | Current canonical pattern (`RunnableWithMessageHistory` is legacy and absent from the LangChain docs — using it would be negative signal). Orchestrates via LangGraph internally. (ADR-005) |
| **Memory** | LangGraph `InMemorySaver` + per-session `thread_id` | Tabs are isolated; no DB needed for this single-instance demo |
| **LLM gateway** | OpenRouter via `langchain-openai`'s `ChatOpenAI` (custom `base_url`) | One key across the portfolio (ADR-002) |
| **Default chat model** | `anthropic/claude-haiku-4.5` | Best PT-BR fidelity on the smoke set at this price point (ADR-003) |
| **Grounding (optional)** | Tavily web search via `langchain-tavily` | Opt-in via `TAVILY_API_KEY`. When set, the agent gets `tools=[TavilySearch(...)]` and the system prompt picks up rule 9 ("verify version-specific APIs before answering"). Without the key, agent runs pure-LLM and rule 9 is dropped — the prompt never lies about what the agent can do. ADR-006. |
| **Quality** | Ruff · mypy strict · pytest (≥ 80% gate, currently 100%) · pip-audit · bandit | All enforced in CI |
| **Infra** | Docker (multi-stage) · Fly.io · GitHub Actions | Auto-deploy on push to `main` (ADR-004) |

## Architecture

- [`docs/PRD.md`](docs/PRD.md) — product requirements, scope decisions, intentional non-goals
- [`docs/diagrams/conversation-flow.md`](docs/diagrams/conversation-flow.md) — sequence from "user types" to "tokens render", including the optional tool branch
- [`docs/adr/`](docs/adr/) — 5 Architecture Decision Records covering every load-bearing choice

## Project layout

```
app/
├── main.py        # Chainlit handlers (@cl.on_chat_start, @cl.on_message, @cl.on_feedback, @cl.set_starters)
├── agent.py       # build_agent() — create_agent + InMemorySaver + system prompt
├── prompts/
│   └── tutor.py   # SYSTEM_PROMPT (PT-BR persona, 8 rules); rule 9 appended when grounding tools are present
├── tools.py       # build_tools() — empty by default; returns Tavily when TAVILY_API_KEY is set
├── ai/client.py   # ChatOpenAI factory pointed at OpenRouter
├── config.py      # pydantic-settings
└── core/          # logging, exceptions
docs/
├── PRD.md         # product requirements + scope decisions
├── adr/           # 5 ADRs
└── diagrams/      # conversation flow (Mermaid)
tests/             # 31 tests, 100% coverage on app/
```

## Testing

```bash
make check     # lint + typecheck + tests with coverage gate
```

Coverage is **100%** across 31 tests. The gate enforces ≥ 80% in CI.

Tests don't hit the real OpenRouter — `tests/test_agent.py` uses `FakeMessagesListChatModel` from `langchain_core` so the agent runs end-to-end (including thread-based memory) without network. End-to-end against the real provider is verified via local smoke before each release (off-topic refusal × 3, multi-turn memory check).

## Related repos

- **[Virtual Library API](https://github.com/heitor-am/virtual-library-api)** — FastAPI + SQLite + OpenRouter
- **[Semantic Document Search](https://github.com/heitor-am/semantic-document-search)** — FastAPI + Qdrant + OpenRouter (RAG with hybrid retrieval + cross-encoder rerank)

All three share the OpenRouter wrapper verbatim and the same Conventional Commits · Ruff + uv + mypy · Fly.io conventions.

## License

MIT — see [LICENSE](LICENSE).
