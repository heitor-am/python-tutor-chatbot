# Python Tutor Chatbot

[![CI](https://github.com/heitor-am/python-tutor-chatbot/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/heitor-am/python-tutor-chatbot/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Conversational Python tutor — Chainlit UI on top of LangChain `create_agent` + OpenRouter.

**Scaffold stage (`v0.0.1`).** The agent, UI, deploy, and tests land in upcoming releases; what's here right now is the package layout, the OpenRouter client, and the CI pipeline.

## Stack (planned)

- **UI:** Chainlit (chat-native, streaming + history + feedback out of the box)
- **Orchestration:** LangChain `create_agent` (modern pattern; orchestrates via LangGraph internally with `InMemorySaver` for thread-based memory)
- **LLM gateway:** OpenRouter — chat default `anthropic/claude-haiku-4.5`
- **Optional grounding:** Tavily web search via `langchain-tavily` (opt-in, agent degrades gracefully without the key)
- **Quality:** Ruff · mypy strict · pytest (≥ 80% coverage gate) · pip-audit · bandit
- **Infra:** Docker (multi-stage) · Fly.io · GitHub Actions

## Related repos

- **[Virtual Library API](https://github.com/heitor-am/virtual-library-api)** — FastAPI + SQLite + OpenRouter
- **[Semantic Document Search](https://github.com/heitor-am/semantic-document-search)** — FastAPI + Qdrant + OpenRouter (RAG with hybrid retrieval + reranker)

All three share the OpenRouter wrapper verbatim and the same Conventional Commits · Ruff + uv + mypy · Fly.io conventions.

## License

MIT — see [LICENSE](LICENSE).
