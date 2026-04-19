# 003 — Claude Haiku 4.5 as the default chat model

- **Status:** accepted
- **Date:** 2026-04-18
- **Deciders:** @heitor-am

## Context

The chat experience is the product. Model choice has three first-order effects:

1. **Quality of explanations in PT-BR** — most "smaller" models slip back into English mid-response, especially when generating code comments.
2. **Tone fidelity to a system prompt** — the tutor persona ("explain reasoning before code", "refuse off-topic in one sentence") is non-trivial to follow consistently.
3. **Cost per message** — even at demo traffic, a 5x cost difference between Haiku-class and 4o-class models is real money over time.

Constraints:
- Must be available on OpenRouter (ADR-002).
- Must reliably refuse off-topic questions in PT-BR (verified via smoke).
- Must produce code blocks the markdown renderer treats correctly.

## Decision

Default chat model: **`anthropic/claude-haiku-4.5`** via OpenRouter. Configurable per-deploy via `OPENROUTER_CHAT_MODEL` env var.

## Consequences

**Positive:**
- Stays in PT-BR end-to-end on the smoke set (technical explanations + code comments + off-topic refusal).
- Persona adherence is solid: refuses cooking, history, and chemistry questions in one PT sentence without sneaking in Python content.
- Cheaper than 4o-class models — meaningful at portfolio-demo traffic where dozens of throwaway sessions are normal.
- Anthropic's instruction-following has been historically strong, which matters for the system prompt's 8 rules.

**Negative:**
- Smaller context window than the larger models — not a constraint here (chat sessions are short), but worth noting if memory grows.
- Tool-calling quality is good but not class-leading; the optional Tavily grounding upgrade may show this.

**Trade-offs accepted:**
- We pick one model and don't auto-route between cheaper/smarter based on query complexity. OpenRouter has an `auto` model that does this; rejected because the routing decision is opaque and would mask "is this answer good?" diagnostics.

## Alternatives considered

- **`openai/gpt-4o-mini`** — strong English tutor; PT-BR drift on long responses. The default for the companion REST-API repo (Q1) but Q2 needs PT-BR fidelity more than it needs OpenAI's tooling.
- **`google/gemini-1.5-flash`** — capable; less consistent in PT-BR persona adherence in our smoke set.
- **`meta-llama/llama-3.1-70b`** — open weights, cheap on OpenRouter; PT-BR quality lags Anthropic at this size.
- **`openrouter/auto`** — opaque routing; rejected on observability grounds.

## References

- `app/config.py` (`openrouter_chat_model` default)
- `.env.example`
- Smoke tests in PR #2 / #3 (off-topic refusal in PT-BR)
