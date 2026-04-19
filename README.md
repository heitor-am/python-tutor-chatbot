# Python Tutor Chatbot

[![CI](https://github.com/heitor-am/python-tutor-chatbot/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/heitor-am/python-tutor-chatbot/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Conversational Python tutor — Chainlit UI on top of LangChain `create_agent` + OpenRouter.

**`v0.1.0` — MVP.** The chat works end-to-end: streaming responses, per-session memory, three suggested starters, thumbs up / down feedback, and graceful refusal of off-topic questions. Deploy + extended documentation land in `v1.0.0`.

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

## Stack

| Layer | Choice | Notes |
|---|---|---|
| **UI** | Chainlit 2.x | Chat-native; streaming + history + feedback widgets out of the box |
| **Orchestration** | LangChain `create_agent` | Current canonical pattern from the LangChain docs (orchestrates via LangGraph internally; `RunnableWithMessageHistory` is legacy and absent from the docs) |
| **Memory** | LangGraph `InMemorySaver` | Per-session `thread_id` keeps each browser tab isolated |
| **LLM gateway** | OpenRouter | Default chat model: `anthropic/claude-haiku-4.5` |
| **Grounding (optional)** | Tavily web search via `langchain-tavily` | Opt-in via `TAVILY_API_KEY`; agent degrades gracefully without it (planned for the next release) |
| **Quality** | Ruff · mypy strict · pytest (≥ 80% coverage) · pip-audit · bandit | All enforced in CI |
| **Infra** | Docker multi-stage · Fly.io · GitHub Actions | Deploy lands in `v1.0.0` |

## Project layout

```
app/
├── main.py        # Chainlit handlers (@cl.on_chat_start, @cl.on_message, @cl.on_feedback)
├── agent.py       # build_agent() — create_agent + InMemorySaver + system prompt
├── prompts/
│   └── tutor.py   # SYSTEM_PROMPT (PT-BR persona, 8 rules)
├── tools.py       # build_tools() — empty by default, returns Tavily when TAVILY_API_KEY is set
├── ai/client.py   # ChatOpenAI pointed at OpenRouter
├── config.py      # pydantic-settings
└── core/          # logging, exceptions
tests/             # 31 tests, 100% coverage on app/
```

## Tests

```bash
make check     # lint + typecheck + tests with coverage
```

## Related repos

- **[Virtual Library API](https://github.com/heitor-am/virtual-library-api)** — FastAPI + SQLite + OpenRouter
- **[Semantic Document Search](https://github.com/heitor-am/semantic-document-search)** — FastAPI + Qdrant + OpenRouter (RAG with hybrid retrieval + reranker)

All three share the OpenRouter wrapper verbatim and the same Conventional Commits · Ruff + uv + mypy · Fly.io conventions.

## License

MIT — see [LICENSE](LICENSE).
