# E-commerce AI Orchestration POC — Modular Monolith (Python + FastAPI + Provider Abstraction)

POC architecture for an AI application that demonstrates collaborative autonomous agent orchestration for an e-commerce platform while fitting into an existing microservice ecosystem.

## Runnable scaffold

This repository now includes a first runnable scaffold for the selected Python-first path:
- FastAPI app entrypoint under `cmd/api/`
- LangGraph orchestration skeleton under `internal/modules/orchestration/`
- OpenRouter client wrapper with documented fallback support under `internal/platform/openrouter/`
- Qdrant adapter under `internal/platform/qdrant/`
- PostgreSQL-backed operator task outbox under `internal/platform/events/`
- config-backed AgentCore Gateway/Policy boundary under `internal/platform/agentcore/`
- sample approval-required support action path under `internal/modules/support/`
- `dev-openrouter-free` configuration profile under `config/profiles/`
- Docker Compose profile under `deploy/compose/`
- request tracing via `X-Request-ID`
- `/healthz` and `/readyz` probes
- one deterministic escalation branch for sensitive flows

## AWS next phase

The current recommendation is a **hybrid AWS extension**, not a rewrite:
- keep **LangGraph + provider abstraction + Qdrant** as the core app path;
- use **Bedrock AgentCore** for ops/governance;
- use **Bedrock Flows** only for selected visible approval workflows;
- use **Knowledge Bases** only for selected managed-RAG corpora.

### Quick start

1. Copy `.env.example` to `.env`
2. Set `OPENROUTER_API_KEY` if you want live OpenRouter responses
3. Start Postgres, Qdrant, and the API:

```bash
docker compose -f deploy/compose/docker-compose.dev-openrouter-free.yml up
```

4. Check probes:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
curl http://localhost:8000/internal/agentcore
```

5. Call the core assistant API:

```bash
curl -X POST http://localhost:8000/api/v1/assist \
  -H "Content-Type: application/json" \
  -d '{"message":"Can I return a damaged speaker after 30 days?"}'
```

6. Call the sample approval-required support action path:

```bash
curl -X POST http://localhost:8000/api/v1/support/refund-review \
  -H "Content-Type: application/json" \
  -d '{"order_id":"ORD-123","customer_message":"I want a refund for a damaged item","requested_amount":49.99}'
```

7. Inspect queued escalation tasks:

```bash
curl http://localhost:8000/internal/escalations
```

If `OPENROUTER_API_KEY` is not set, the scaffold still runs in stub mode so the orchestration path can be exercised without paid model access.

Sensitive flows now use a deterministic escalation path that ends generation early and stores an operator task in PostgreSQL for follow-up.
The sample refund-review endpoint uses the config-backed AgentCore boundary and, by default, queues approval-required refund actions instead of executing any real side effect.

## Repository Guide

| Section | Purpose |
|---|---|
| [Architecture Overview](./docs/architecture/README.md) | Main architecture document in a diagram-heavy style |
| [C4 — Context](./docs/architecture/c4-context.md) | Actors, systems, and trust boundaries |
| [C4 — Containers](./docs/architecture/c4-container.md) | Runtime blocks and integration boundaries |
| [C4 — Components](./docs/architecture/c4-components-orchestrator.md) | Orchestration internals and control points |
| [Agent Workflows](./docs/architecture/agent-workflows.md) | Collaborative autonomous agent flows |
| [Bedrock AgentCore for Ops/Governance](./docs/architecture/bedrock-agentcore-ops-governance.md) | Recommended AWS governance extension |
| [Optional Flows and Knowledge Bases](./docs/architecture/bedrock-flows-knowledge-bases.md) | Selective managed workflow and RAG additions |
| [Selected OpenRouter Dev Profile](./docs/architecture/profile-langgraph-openrouter-free.md) | Zero-cost dev/demo profile |
| [Modules](./docs/modules/README.md) | Domain/module boundaries in the modular monolith |
| [API Sketch](./docs/api/README.md) | Main synchronous and internal endpoints |
| [ADR 005](./docs/adr/005-bedrock-agentcore-for-ops-governance.md) | Why AgentCore is the recommended next AWS layer |
