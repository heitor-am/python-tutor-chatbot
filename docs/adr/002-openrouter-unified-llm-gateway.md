# 002 — OpenRouter as the unified LLM gateway

- **Status:** accepted
- **Date:** 2026-04-18
- **Deciders:** @heitor-am

## Context

Three plausible paths for talking to an LLM:

1. Direct provider SDKs (`openai`, `anthropic`, `cohere`) — one client + one API key per vendor.
2. Single-vendor lock-in (e.g., OpenAI for everything).
3. A unified gateway that exposes an OpenAI-compatible API across many providers.

The portfolio repos this one accompanies all need an LLM. Picking different providers per repo means juggling three SDKs, three keys, three pricing models, three rate-limit envelopes.

## Decision

OpenRouter as the single LLM gateway, accessed via `langchain-openai`'s `ChatOpenAI` with a custom `base_url`. Configured in `app/ai/client.py`:

```python
ChatOpenAI(
    model=settings.openrouter_chat_model,
    base_url="https://openrouter.ai/api/v1",
    api_key=SecretStr(settings.openrouter_api_key),
    default_headers={
        "HTTP-Referer": settings.openrouter_app_url,
        "X-Title": settings.openrouter_app_name,
    },
    timeout=60.0,
    max_retries=3,
)
```

The `HTTP-Referer` + `X-Title` headers identify the app on the OpenRouter dashboard.

## Consequences

**Positive:**
- One key, one billing line, one rate-limit envelope across the entire portfolio.
- Swapping the chat model is `OPENROUTER_CHAT_MODEL=...` in `.env` — no code change. Tested with `anthropic/claude-haiku-4.5` (default), `openai/gpt-4o-mini`, others on the OpenRouter catalogue.
- LangChain integration is canonical: any model that speaks OpenAI Chat Completions works through `ChatOpenAI`.
- Same `app/ai/client.py` shape repeats verbatim across the companion repos — readers don't have to relearn the LLM wiring.

**Negative:**
- OpenRouter takes a small markup on top of provider pricing — acceptable for the operational simplification.
- Vendor-specific features (Anthropic's prompt caching, OpenAI's streaming-with-tool-calls quirks) may be filtered or unavailable through the gateway.
- Adds one more network hop (client → OpenRouter → provider).

**Trade-offs accepted:**
- We don't try to fall back to direct provider SDKs when OpenRouter is degraded. Chat downtime would hurt the demo, not a real production user; not worth the complexity.

## Alternatives considered

- **Direct OpenAI SDK** — works but locks the model choice; switching to Claude or Llama would mean a new client.
- **LangChain provider plugins** (`langchain-anthropic`, `langchain-openai`, ...) — adds N deps and N code paths for the same use case.
- **Multiple gateways** (OpenRouter + Together + Anyscale) — over-engineering for a demo.

## References

- `app/ai/client.py`
- `app/config.py` (OpenRouter settings)
- OpenRouter docs: https://openrouter.ai/docs
