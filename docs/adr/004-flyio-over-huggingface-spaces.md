# 004 — Fly.io over Hugging Face Spaces for the public deploy

- **Status:** accepted
- **Date:** 2026-04-18
- **Deciders:** @heitor-am

## Context

Two natural targets for a Chainlit chat app:

- **Hugging Face Spaces (Docker SDK)** — free, well-known to the ML community, a "deploy on Spaces" line on a portfolio is a recognisable signal.
- **Fly.io** — Docker container, GitHub Actions auto-deploy, custom subdomain, structured logs, real machines you can `ssh` into.

Both work. The actual cost is roughly equivalent: Chainlit needs Docker on either platform.

The companion repos (`virtual-library-api`, `semantic-document-search`) both deploy to Fly.io. The reviewer of this portfolio reads three repos in sequence; if Q2 picks a third deploy story, the reviewer pays a context-switch cost for no extra information.

## Decision

Deploy to **Fly.io**. Same pattern as the other two repos:

- `Dockerfile` — multi-stage, builder + runtime
- `fly.toml` — `gru` region, 512MB shared CPU, `auto_stop_machines = "stop"`
- `.github/workflows/deploy.yml` — `flyctl deploy --remote-only` on push to `main`

The chat endpoint at `https://python-tutor-chatbot.fly.dev` is the demo URL.

## Consequences

**Positive:**
- One deploy story across the three portfolio repos. The reviewer reads `fly.toml` once, the pattern repeats.
- Real subdomain with HTTPS, no `/spaces/heitor-am/...` URL.
- Structured logs via `fly logs`, can `fly ssh console` into the machine.
- WebSockets work natively through Fly's proxy (Chainlit needs them for streaming).
- Free tier covers a portfolio demo; auto-stop after idle keeps the bill at zero on quiet days.

**Negative:**
- Cold-start adds 2-3s on the first message after idle. Mitigation: bump `min_machines_running = 1` (~$2/mo) if it bothers a reviewer. Not done by default.
- Free tier requires a credit card on file (HF Spaces doesn't).
- "I deployed to HF Spaces" carries weight in some ML hiring loops; we trade that signal for portfolio consistency.

**Trade-offs accepted:**
- We don't try to deploy to *both* Fly and HF Spaces. The marginal value of two URLs is low; the maintenance cost of two CD pipelines is not.

## Alternatives considered

- **Hugging Face Spaces (Docker SDK)** — see context. Picked when ML-community signal matters more than portfolio coherence; not the case here (target is a backend AI role, not an ML demo evaluation).
- **Render / Railway** — fine; chosen by us elsewhere for non-AI projects. No specific advantage over Fly for this workload, and breaks the pattern with the other repos.
- **Self-hosted on a VPS** — over-engineering for a chat demo.

## References

- `Dockerfile`, `fly.toml`, `.github/workflows/deploy.yml`
- Companion deploys: virtual-library-api.fly.dev, semantic-document-search.fly.dev
- Fly.io docs: https://fly.io/docs
