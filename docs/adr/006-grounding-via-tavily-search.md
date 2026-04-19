# 006 — Grounding via Tavily web search

- **Status:** accepted
- **Date:** 2026-04-19
- **Deciders:** @heitor-am

## Context

LLMs hallucinate API signatures. The failure mode is well-known: confidently produces `list.append(item, idx=0)` (wrong) instead of `list.insert(0, item)`, or invents a stdlib function that doesn't exist, or describes Python 3.11+ behaviour as if it applied to 3.9. A tutor-shaped product can't ship those answers.

Cross-checking against a live source — official docs, Stack Overflow, recent blog posts — when the LLM is uncertain about a *factual* claim (signature, version, library) is the standard mitigation.

Three plausible grounding paths:

1. **Web search via a hosted API** — Tavily, Brave, Serper, Bing.
2. **DuckDuckGo via the unofficial `ddgs` Python lib** — no API key.
3. **RAG over `docs.python.org`** — pre-index the canonical docs, retrieve at query time.

## Decision

Tavily Search via `langchain-tavily` as the optional grounding tool. The agent gets `tools=[TavilySearch(max_results=3, include_answer="basic", search_depth="basic")]` when `TAVILY_API_KEY` is set in the environment; an empty list otherwise.

The system prompt's rule 9 ("when uncertain, call the search tool before answering") is appended to the prompt only when at least one tool is wired in (`build_system_prompt(with_grounding=)` reads `bool(build_tools())`). Without the key, the agent runs in pure-LLM mode and the prompt never instructs the model to call a non-existent tool.

## Consequences

**Positive:**
- One-line integration with `create_agent` (`tools=[TavilySearch(...)]`); no glue code, no custom retriever.
- Tavily returns an `include_answer="basic"` summary plus 3 sources — ~300 token payload back to the LLM, much cheaper than dumping raw search snippets.
- Free tier (1k requests/month) is generous for a portfolio demo.
- Tavily is the de-facto LLM-grounding API: stable since 2023, used in Anthropic / LangChain / Cohere reference apps. Reviewer recognises the choice.
- Optional and toggleable via env var: deploys without `TAVILY_API_KEY` still work, just without grounding. Reduces operator coupling.
- The system-prompt toggle (`build_system_prompt(with_grounding=)`) keeps the prompt honest: never asks for a tool that doesn't exist.

**Negative:**
- New dep (`langchain-tavily`) and one more network hop in the hot path when the LLM decides to call the tool.
- Free tier caps at 1k req/mo; a viral demo could burn it. Acceptable trade — agent degrades gracefully when the cap hits (`TavilySearch` would error → caught by the same `_FRIENDLY_LLM_ERRORS` wrapper in `app/main.py`).
- Tavily is a paid service; we're depending on the vendor.
- Introduces a "tool calling" code path that didn't exist before. Mitigated by `create_agent` handling tool orchestration end-to-end (we don't write tool-call parsing).

**Trade-offs accepted:**
- Default chat model is via OpenRouter (Claude Haiku); grounding is via Tavily directly. Two providers, but each does what it's best at — and OpenRouter doesn't currently proxy search APIs anyway.

## Alternatives considered

- **DuckDuckGo via `ddgs` (or `duckduckgo-search`)** — rejected after weighing it: (a) the lib is an unofficial scraper, periodically blocked by DDG → outage risk; (b) snippet quality is materially worse than Tavily's pre-summarised payload; (c) more tokens reach the LLM per call (more cost than the "free" search saves). The "no API key" win is small once you accept that we already need an `OPENROUTER_API_KEY`.
- **context7 MCP** — used elsewhere in the portfolio for library docs, but it indexes large library codebases (FastAPI, Django, etc.); for Python core / stdlib (the actual gap LLMs have) it's a mismatch.
- **RAG over `docs.python.org`** — would land high quality but requires a Q3-style retrieval pipeline (chunking + embedding + vector store + retriever). Out of scope per PRD §2.3 ("RAG over Python docs — would be Q3 with a twist").
- **No grounding at all** — viable; chosen for the v1.0.0 cut. We add it now as the first post-v1.0.0 feature because the LLM-hallucination risk in a *tutor* shape is real enough to justify the extra network hop.

## References

- `app/tools.py` (`build_tools`)
- `app/agent.py` (`build_agent` couples `with_grounding=bool(build_tools())`)
- `app/prompts/tutor.py` (`build_system_prompt` rule 9 toggle)
- `tests/test_tools.py`, `tests/test_agent.py::TestSystemPromptToggle`
- Tavily docs: https://docs.tavily.com
- LangChain Tavily integration: https://python.langchain.com/docs/integrations/tools/tavily_search/
