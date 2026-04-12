# E-commerce AI Orchestration POC — Modular Monolith (Python + FastAPI + Provider Abstraction)

POC architecture for an AI application that demonstrates collaborative autonomous agent orchestration for an e-commerce platform while fitting into an existing microservice ecosystem.

## Runnable scaffold

This repository currently includes:
- FastAPI app entrypoint under `cmd/api/`
- FastAPI-based AgentCore mock service under `cmd/agentcore_mock/`
- LangGraph orchestration skeleton under `internal/modules/orchestration/`
- OpenRouter client wrapper with documented fallback support under `internal/platform/openrouter/`
- Qdrant adapter under `internal/platform/qdrant/`
- PostgreSQL-backed operator task outbox under `internal/platform/events/`
- AgentCore integration seam under `internal/platform/agentcore/`
- sample approval-required support action path under `internal/modules/support/`
- `dev-openrouter-free` configuration profile under `config/profiles/`
- Docker Compose profiles under `deploy/compose/`
- request tracing via `X-Request-ID`
- `/healthz` and `/readyz` probes
- deterministic escalation for sensitive flows

## AgentCore integration status

The repository now supports four AgentCore-oriented layers:
- **external stub** mode for local demos
- **HTTP client skeleton** mode for remote-style integration
- optional **stub fallback on transport error** for the HTTP client path
- **mock AgentCore service** for end-to-end local HTTP testing

The AgentCore seam currently includes:
- `evaluate_action(...)`
- `register_tool(...)`
- `emit_trace_event(...)`
- `submit_approval_request(...)`

The sample `POST /api/v1/support/refund-review` path uses that boundary and can:
- evaluate a support action,
- emit trace events,
- submit approval requests,
- persist resulting operator tasks.

## AWS next phase

The current recommendation remains a hybrid AWS extension rather than a rewrite:
- keep **LangGraph + provider abstraction + Qdrant** as the core app path;
- use **Bedrock AgentCore** for ops/governance;
- use **Bedrock Flows** only for selected visible approval workflows;
- use **Knowledge Bases** only for selected managed-RAG corpora.

## Quick start

### Default local profile

1. Copy `.env.example` to `.env`
2. Set `OPENROUTER_API_KEY` if you want live OpenRouter responses
3. Start Postgres, Qdrant, and the API:

```bash
docker compose -f deploy/compose/docker-compose.dev-openrouter-free.yml up
```

### HTTP-style AgentCore profile

This profile starts a local AgentCore mock service and runs the main API in `http_client` mode:

```bash
docker compose -f deploy/compose/docker-compose.dev-agentcore-http.yml up
```

Useful checks:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
curl http://localhost:8000/internal/agentcore
curl http://localhost:9001/healthz
curl http://localhost:9001/internal/state
```

### Sample requests

Core assistant API:

```bash
curl -X POST http://localhost:8000/api/v1/assist \
  -H "Content-Type: application/json" \
  -d '{"message":"Can I return a damaged speaker after 30 days?"}'
```

Approval-required support action path:

```bash
curl -X POST http://localhost:8000/api/v1/support/refund-review \
  -H "Content-Type: application/json" \
  -d '{"order_id":"ORD-123","customer_message":"I want a refund for a damaged item","requested_amount":49.99}'
```

Queued escalation tasks:

```bash
curl http://localhost:8000/internal/escalations
```

If `OPENROUTER_API_KEY` is not set, the scaffold still runs in stub mode so the orchestration path can be exercised without paid model access.

## Known follow-ups

See [docs/TODO.md](./docs/TODO.md).

Most important current follow-up:
- the checked-in `config/profiles/dev-openrouter-free.yaml` still needs to be synchronized with the newer AgentCore HTTP-client config fields when the repo is fetched locally and edited outside the GitHub connector path.

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
| [TODO](./docs/TODO.md) | Short list of known follow-ups |
