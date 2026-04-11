# E-commerce AI Orchestration POC — Modular Monolith (Python + FastAPI + Provider Abstraction)

POC architecture for an AI application that demonstrates collaborative autonomous agent orchestration for an e-commerce platform while fitting into an existing microservice ecosystem.

## Runnable scaffold

This repository now includes a first runnable scaffold for the selected Python-first path:
- FastAPI app entrypoint under `cmd/api/`
- LangGraph orchestration skeleton under `internal/modules/orchestration/`
- OpenRouter client wrapper with documented fallback support under `internal/platform/openrouter/`
- Qdrant adapter under `internal/platform/qdrant/`
- in-memory operator task outbox under `internal/platform/events/`
- `dev-openrouter-free` configuration profile under `config/profiles/`
- Docker Compose profile under `deploy/compose/`
- request tracing via `X-Request-ID`
- `/healthz` and `/readyz` probes
- one deterministic escalation branch for sensitive flows

### Quick start

1. Copy `.env.example` to `.env`
2. Set `OPENROUTER_API_KEY` if you want live OpenRouter responses
3. Start Qdrant and the API:

```bash
docker compose -f deploy/compose/docker-compose.dev-openrouter-free.yml up
```

4. Check probes:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
```

5. Call the API:

```bash
curl -X POST http://localhost:8000/api/v1/assist \
  -H "Content-Type: application/json" \
  -d '{"message":"Can I return a damaged speaker after 30 days?"}'
```

6. Inspect queued escalation tasks:

```bash
curl http://localhost:8000/internal/escalations
```

If `OPENROUTER_API_KEY` is not set, the scaffold still runs in stub mode so the orchestration path can be exercised without paid model access.

Sensitive flows now use a deterministic escalation path that ends generation early and enqueues an operator task payload for follow-up.

## Repository Guide

| Section | Purpose |
|---|---|
| [Architecture Overview](./docs/architecture/README.md) | Main architecture document in a diagram-heavy style |
| [C4 — Context](./docs/architecture/c4-context.md) | Actors, systems, and trust boundaries |
| [C4 — Containers](./docs/architecture/c4-container.md) | Runtime blocks and integration boundaries |
| [C4 — Components](./docs/architecture/c4-components-orchestrator.md) | Orchestration internals and control points |
| [Agent Workflows](./docs/architecture/agent-workflows.md) | Collaborative autonomous agent flows |
| [Selected OpenRouter Dev Profile](./docs/architecture/profile-langgraph-openrouter-free.md) | Zero-cost dev/demo profile |
| [Modules](./docs/modules/README.md) | Domain/module boundaries in the modular monolith |
| [API Sketch](./docs/api/README.md) | Main synchronous and internal endpoints |
