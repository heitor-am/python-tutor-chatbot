# PRD — Python Tutor Chatbot

- **Project:** Python Tutor Chatbot
- **Status:** Released (`v1.0.0`) — chat live in production, full ADRs and docs in this repo
- **Live:** https://python-tutor-chatbot.fly.dev

## 1. Context

A conversational tutor specialised in teaching Python — a "digital tutor" for beginners and intermediate developers. The orchestration uses LangChain (specifically the modern `langchain.agents.create_agent` pattern) and routes all LLM traffic through OpenRouter.

It's the second of three sibling portfolio projects. Sister repos:

- [Virtual Library API](https://github.com/heitor-am/virtual-library-api) — REST + SQLite + OpenRouter
- [Semantic Document Search](https://github.com/heitor-am/semantic-document-search) — RAG with hybrid retrieval + reranker + Qdrant

All three share the OpenRouter wrapper verbatim (`app/ai/client.py`) and the same engineering conventions (Conventional Commits, Ruff + uv + mypy strict, Fly.io deploys via GitHub Actions).

### 1.1 Goal

Ship a chatbot that is **visually polished** and **technically correct**, with streaming responses, per-session memory, and a well-defined tutor persona.

### 1.2 Intentionally tight scope

This is the simplest of the three projects because basic chatbots are commodity. The value lives in:

- **Polished UX** (Chainlit) more than infrastructure complexity
- **Maximum reuse** of the shared portfolio patterns (OpenRouter wrapper, conventions, tooling)
- Carefully designed prompt engineering (persona, rules, response format)

Architectural weight in the portfolio sits with the REST API project (Q1, backend depth) and the Semantic Search project (Q3, RAG depth).

## 2. Scope

### 2.1 Core requirements

- Receive Python questions via text input
- Use LangChain to orchestrate the conversation
- Integrate with an LLM (via OpenRouter)
- Answer Python questions with executable, tutorial-quality examples
- Demonstrable working examples in the README

### 2.2 Differentiators (delivered in `v1.0.0`)

- **Chainlit UI** — chat-native streaming + history + feedback widgets
- **Token streaming** via `agent.astream(stream_mode="messages")`
- **Per-session memory** via LangGraph `InMemorySaver` keyed on `thread_id` (different browser tabs get isolated chats)
- **Python tutor persona** — system prompt with 8 explicit rules
- **Welcome starters** — three one-click example questions to remove blank-prompt friction
- **Thumbs up / down feedback** captured via `@cl.on_feedback`
- **Visible "Calling LLM" steps** in the Chainlit sidebar via `cl.AsyncLangchainCallbackHandler`
- **Friendly error messages** in the chat (instead of stack traces) when the LLM provider hiccups
- **Public deploy** to Fly.io (same pattern as the sibling repos)

### 2.3 Optional differentiator (planned)

- **Grounding via Tavily web search** — `tools=[TavilySearch(...)]` on `create_agent` so the tutor can verify version-specific Python APIs before answering. Opt-in via `TAVILY_API_KEY`; agent degrades gracefully without the key.

### 2.4 Out of scope

- Authentication
- Cross-session persistence (DB, threads survive restart)
- Multi-step agent loops (planning, reflection, self-correction)
- Automated answer-quality evaluation (no golden set, no eval harness)
- File upload / voice input

> Single-shot tool use (one search round per turn) **is** in scope as the optional Tavily upgrade. What stays out is multi-step agent orchestration with loops.

## 3. Stack

| Layer | Choice | Why |
|---|---|---|
| **UI / app framework** | Chainlit 2.x | Built for LLM apps; streaming + history + feedback widgets out of the box; Python-only; trivial Docker deploy. ADR-001. |
| **LLM orchestration** | LangChain `create_agent` (orchestrates via LangGraph internally) | Current canonical pattern in `docs.langchain.com/oss/python/langchain/`. `RunnableWithMessageHistory` (LCEL legacy) was removed from the docs; `create_agent` ships checkpointer + thread-based memory + tool calling without extra glue. ADR-005. |
| **Memory** | LangGraph `InMemorySaver` + `thread_id` per session | Replaces the legacy `ConversationBufferMemory`; the `create_agent` accepts the checkpointer as a kwarg with no boilerplate. |
| **LLM gateway** | OpenRouter via `langchain-openai`'s `ChatOpenAI` (custom `base_url`) | One key across the three sibling repos. ADR-002. |
| **Default chat model** | `anthropic/claude-haiku-4.5` | Best PT-BR fidelity at this price point on the smoke set. ADR-003. |
| **Optional grounding** | Tavily Search via `langchain-tavily` | Reduces hallucination on API signatures; one-liner integration with `create_agent`. Free tier covers the demo traffic. |
| **Dependency manager** | `uv` | Same as the sibling repos. |
| **Lint + format** | `ruff` | Same. |
| **Type check** | `mypy --strict` | Same. |
| **Deploy** | Fly.io (Docker + GitHub Actions auto-deploy) | Same `fly.toml` / `deploy.yml` pattern as the other two repos — reviewer reads it once. ADR-004. |

## 4. Architecture

### 4.1 Conversation flow

See [`docs/diagrams/conversation-flow.md`](diagrams/conversation-flow.md) for the full Mermaid sequence.

Briefly: the user types → Chainlit invokes the agent → the agent loads prior state from `InMemorySaver` (keyed on `thread_id`) → calls OpenRouter → streams tokens back through Chainlit → persists the new state. The optional Tavily branch adds a tool-call cycle before the final response stream when the LLM decides it needs to verify something.

### 4.2 Components

1. **System prompt** (`app/prompts/tutor.py`) — Python tutor persona + 8 rules. `build_system_prompt(with_grounding=)` appends rule 9 (verify-before-answer) only when search tools are present.
2. **Agent** (`app/agent.py`) — `create_agent(model, system_prompt, tools, checkpointer)`. Both the model and the checkpointer are injectable for testing.
3. **Tools factory** (`app/tools.py`) — returns `[]` by default; returns `[TavilySearch(...)]` when `TAVILY_API_KEY` is set.
4. **Memory** — `InMemorySaver` from `langgraph.checkpoint.memory`. Each Chainlit session uses a unique `thread_id` (uuid4). State lives in the saver, not in the chain itself.
5. **Chat model wiring** (`app/ai/client.py`) — `ChatOpenAI` pointed at OpenRouter with `HTTP-Referer` / `X-Title` headers for dashboard attribution.
6. **Chainlit handlers** (`app/main.py`) — `@cl.on_chat_start` (generate `thread_id`, build agent, set starters), `@cl.on_message` (invoke + stream), `@cl.on_feedback` (log thumbs-up / down).

## 5. Project structure

```
python-tutor-chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Chainlit handlers
│   ├── config.py                # pydantic-settings
│   ├── agent.py                 # build_agent() — create_agent + InMemorySaver
│   ├── tools.py                 # build_tools() — [] today, [TavilySearch] when key set
│   ├── prompts/
│   │   └── tutor.py             # SYSTEM_PROMPT (PT-BR persona, 8+1 rules)
│   ├── ai/
│   │   └── client.py            # ChatOpenAI factory pointed at OpenRouter
│   └── core/
│       ├── exceptions.py
│       └── logging.py
├── tests/
│   ├── test_smoke.py
│   ├── test_prompts.py
│   ├── test_tools.py
│   └── test_agent.py
├── docs/
│   ├── PRD.md
│   ├── adr/                     # 5 ADRs
│   └── diagrams/
│       └── conversation-flow.md
├── .chainlit/                   # UI config
├── .github/workflows/           # ci.yml + deploy.yml
├── chainlit.md                  # Welcome screen
├── Dockerfile                   # Multi-stage builder + runtime
├── fly.toml
├── pyproject.toml
├── Makefile
└── README.md
```

## 6. System prompt — outline

The tutor persona enforces 8 rules (full text in `app/prompts/tutor.py`):

- Always explain the reasoning before showing code
- Use short examples (under 15 lines), always executable
- Comment the code
- Ask before answering ambiguous questions
- Point out common pitfalls and best practices
- Prefer "Zen of Python" (readability over cleverness)
- Respond in Brazilian Portuguese unless the user asks otherwise
- Refuse off-topic questions politely, in one sentence

Rule 9 (grounding) is appended only when the agent has a search tool wired in:

- When uncertain about exact API signatures, version-specific behaviour, or external library APIs, call the search tool **before** answering. Don't invent signatures — verify. For basic, stable concepts (lists, loops, functions), answer directly without unnecessary search calls.

## 7. Releases

| Tag | Contents |
|---|---|
| `v0.1.0` | MVP — local chat working end-to-end (Chainlit UI + agent + streaming + memory + starters + feedback + off-topic refusal) |
| `v1.0.0` | Public deploy on Fly.io + 5 ADRs + conversation-flow diagram + polished README |

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| LangChain `create_agent` API churn (relatively new) | Pin exact version in `uv.lock`; `docs.langchain.com` is the source of truth |
| Streaming doesn't work first try with Chainlit | Use `cl.AsyncLangchainCallbackHandler` — officially supported integration |
| Fly cold-start is awkward in a chat UI | Accept 2-3s on first message + welcome message acknowledges it; bump `min_machines_running = 1` (~$2/mo) if it matters |
| WebSocket through Fly's proxy | Fly supports WS natively; verified via local + production smoke |
| OpenRouter out of credits during demo | Welcome message can be updated to mention rate-limit possibility |
| Tavily quota burnout (only when grounding is enabled) | Factory returns `[]` if `TAVILY_API_KEY` is absent — agent degrades gracefully |

## 9. Tests

- 31 unit tests, 100% coverage on `app/`. The agent uses `FakeMessagesListChatModel` in tests so end-to-end behaviour (including `thread_id` memory) runs without network.
- End-to-end smoke against real OpenRouter is verified manually before each release: multi-turn memory check + 3 off-topic refusal questions in PT-BR.
