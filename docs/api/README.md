# API Sketch

The POC exposes a small surface area that keeps request entrypoints explicit while allowing the internal orchestration engine to evolve.

## External Endpoints

### `POST /api/v1/assist`
General request entrypoint for shopper support, product discovery, operator requests, or merchandising playground flows.

### `POST /api/v1/support/order-status`
Structured entrypoint for order-oriented support flows.

### `POST /api/v1/merchandising/copilot`
Internal copilot entrypoint for merchandising assistance.

### `POST /api/v1/catalog/query`
Debug/playground endpoint for hybrid catalog retrieval.

### `GET /healthz`
Liveness probe.

### `GET /readyz`
Readiness probe for DB, Redis, Qdrant, and provider config.

## Internal / Operational Endpoints

### `POST /internal/outbox/dispatch`
Manual or scheduled dispatch of internal events.

### `POST /internal/evals/run`
Trigger offline regression or prompt/provider comparison runs.

### `GET /internal/traces/{trace_id}`
Fetch a stitched view of agent steps, tool calls, and outcomes.

### `GET /internal/evals/latest`
Return latest online/offline quality summaries.
