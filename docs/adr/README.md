# Architecture Decision Records

Each file documents one architectural choice: the context that forced the decision, the option taken, the consequences, and the alternatives that were rejected (and why). Format follows [`template.md`](template.md).

| # | Decision |
|---|---|
| [001](001-chainlit-over-streamlit.md) | Chainlit over Streamlit / Gradio for the chat UI |
| [002](002-openrouter-unified-llm-gateway.md) | OpenRouter as the unified LLM gateway |
| [003](003-claude-haiku-default-model.md) | Claude Haiku 4.5 as the default chat model |
| [004](004-flyio-over-huggingface-spaces.md) | Fly.io over Hugging Face Spaces for the public deploy |
| [005](005-create_agent-over-lcel-runnable.md) | `create_agent` over the legacy LCEL + `RunnableWithMessageHistory` pattern |

## When to add a new ADR

When a decision **closes off other options** and a future maintainer would benefit from knowing *why* — not "what does the code do" (the code answers that), but "why this and not that other reasonable thing." Bug fixes, refactors, and simple feature additions don't need ADRs.

Copy [`template.md`](template.md), bump the number, write the context as if explaining to someone who'd otherwise repeat the rejected alternative.
