# E-commerce AI Orchestration POC — Modular Monolith (Python + FastAPI + Provider Abstraction)

POC architecture for an AI application that demonstrates collaborative autonomous agent orchestration for an e-commerce platform while fitting into an existing microservice ecosystem.

## Runnable surfaces

This repository currently includes:
- FastAPI app entrypoint under `cmd/api/`
- FastAPI-based AgentCore mock service under `cmd/agentcore_mock/`
- FastAPI-based Bedrock demo service under `cmd/bedrock_demo/`
- LangGraph orchestration skeleton under `internal/modules/orchestration/`
- OpenRouter client wrapper under `internal/platform/openrouter/`
- Bedrock adapters under `internal/platform/bedrock/`
- Qdrant adapter under `internal/platform/qdrant/`
- PostgreSQL-backed operator task outbox under `internal/platform/events/`
- AgentCore integration seam under `internal/platform/agentcore/`
- sample approval-required support action path under `internal/modules/support/`
- Docker Compose profiles under `deploy/compose/`

## Bedrock integration status

The repository now has a thin AWS lane beside the existing default path:
- `BedrockRuntimeAdapter` for model calls via Bedrock Runtime
- `BedrockKnowledgeBaseAdapter` for Knowledge Bases queries
- `BedrockFlowAdapter` for flow invocation
- `cmd/bedrock_demo/main.py` as a small demo app exposing those adapters over HTTP

## Quick start

### Existing local profile

```bash
docker compose -f deploy/compose/docker-compose.dev-openrouter-free.yml up
```

### AgentCore HTTP profile

```bash
docker compose -f deploy/compose/docker-compose.dev-agentcore-http.yml up
```

### Bedrock demo profile

This profile runs a separate Bedrock demo app on port `8010`.
You must provide valid AWS credentials and the Bedrock identifiers you want to test.

```bash
docker compose -f deploy/compose/docker-compose.dev-bedrock-demo.yml up
```

Useful checks:

```bash
curl http://localhost:8010/healthz
curl http://localhost:8010/internal/bedrock
```

Example calls:

```bash
curl -X POST http://localhost:8010/api/v1/bedrock/converse \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":[{"text":"Hello from Bedrock"}]}]}'
```

```bash
curl -X POST http://localhost:8010/api/v1/bedrock/knowledge/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is our refund policy?"}'
```

## Known follow-ups

See [docs/TODO.md](./docs/TODO.md).

Most important current follow-up:
- the checked-in `config/profiles/dev-openrouter-free.yaml` still needs to be synchronized with the newer AgentCore and Bedrock config fields when the repo is fetched locally and edited outside the GitHub connector path.
