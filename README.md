# E-commerce AI Orchestration POC — Modular Monolith (Python + FastAPI + Provider Abstraction)

POC architecture for an AI application that demonstrates collaborative autonomous agent orchestration for an e-commerce platform while fitting into an existing microservice ecosystem.

## Main app status

The main API now supports:
- provider-switched generation through `POST /api/v1/generate`
  - `openrouter`
  - `bedrock_runtime`
- provider-switched retrieval through `POST /api/v1/retrieve`
  - `qdrant`
  - `bedrock_knowledge_base`
- refund review through `POST /api/v1/support/refund-review`
  - `external_stub`
  - `http_client`
  - `gateway_mcp`

## Real AWS / Bedrock activation path

### 1. Real Bedrock Runtime for generation
Use `bedrock_runtime` through the main API and set:
- `AWS_REGION`
- `BEDROCK_ENABLED=true`
- `BEDROCK_RUNTIME_MODEL_ID`

### 2. Real Knowledge Base retrieval
Use `bedrock_knowledge_base` through the main API and set:
- `BEDROCK_KNOWLEDGE_BASE_ID`
- `BEDROCK_KNOWLEDGE_MODEL_ID`

This is intended for one narrow document-heavy corpus first, such as refund/help-center/policy content.

### 3. Real AgentCore Gateway / Policy for refund review
Use `AGENTCORE_MODE=gateway_mcp` and set:
- `AGENTCORE_GATEWAY_URL`
- `AGENTCORE_GATEWAY_AUTH_HEADER` when inbound authorization is enabled
- `AGENTCORE_REFUND_TOOL_NAME`

In this mode, `POST /api/v1/support/refund-review` calls the real AgentCore Gateway MCP endpoint at `/mcp` using `tools/call` semantics.

## Useful endpoints

Main API:
- `GET /healthz`
- `GET /readyz`
- `GET /internal/providers`
- `GET /internal/agentcore`
- `POST /api/v1/generate`
- `POST /api/v1/retrieve`
- `POST /api/v1/support/refund-review`
- `POST /api/v1/assist`

Bedrock demo API:
- `GET /healthz`
- `GET /internal/bedrock`
- `POST /api/v1/bedrock/converse`
- `POST /api/v1/bedrock/knowledge/query`
- `POST /api/v1/bedrock/flow/invoke`

## Example main-app calls

Generation with the default provider:

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"provider":"openrouter","messages":[{"role":"user","content":"Hello"}]}'
```

Retrieval with the default vector path:

```bash
curl -X POST http://localhost:8000/api/v1/retrieve \
  -H "Content-Type: application/json" \
  -d '{"provider":"qdrant","query":"refund policy"}'
```

Refund review via the configured AgentCore mode:

```bash
curl -X POST http://localhost:8000/api/v1/support/refund-review \
  -H "Content-Type: application/json" \
  -d '{"order_id":"ORD-123","customer_message":"I want a refund for a damaged item","requested_amount":49.99}'
```

## Known follow-ups

See [docs/TODO.md](./docs/TODO.md).

Most important current follow-ups:
- synchronize the checked-in `config/profiles/dev-openrouter-free.yaml` with the newer AgentCore and Bedrock config fields after fetching the repo locally;
- provision real AWS resources for the Gateway/Policy refund tool path and then replace any remaining fallback-only behavior.
