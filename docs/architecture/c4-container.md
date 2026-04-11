# C4 — Level 2: Containers

<div align="center">

*Major runtime building blocks for the AI orchestration POC*

</div>

---

## Container Diagram

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    ch["☁️ App / Web / Internal UI Channels"]:::ext

    subgraph app ["AI Orchestration System"]
        direction TB

        subgraph hosts ["Runtime Hosts"]
            direction LR
            api["FastAPI API Host\nPython\n(Runs Modules)"]:::api
            wrk["Background Worker\nPython\n(Runs Modules)"]:::worker
        end

        plat["Platform Services Layer\n(Compiled into both hosts)"]:::platform

        api -. "Internal Events\n(via Outbox)" .-> wrk
        api -- "Uses" --> plat
        wrk -- "Uses" --> plat
    end

    ch -- "HTTP / events" --> api
    api -- "Responses" --> ch
    wrk -- "Async notifications" --> ch

    plat -- "SQLAlchemy" --> pg[("PostgreSQL")]:::db
    plat -- "Cache / dedup / rate limit" --> rd[("Redis")]:::cache
    plat -- "Vector search" --> qd[("Qdrant")]:::db
    plat -- "LLM / embeddings" --> llm["☁️ OpenAI / Anthropic / Bedrock"]:::ext
    plat -- "Catalog / order / customer APIs" --> eco["☁️ Existing E-commerce Microservices"]:::ext
    plat -- "Telemetry / audit" --> ot["☁️ Telemetry Sink"]:::ext

    classDef ext fill:transparent,stroke:#DD6B20,stroke-width:3px
    classDef api fill:transparent,stroke:#319795,stroke-width:3px
    classDef worker fill:transparent,stroke:#D69E2E,stroke-width:3px
    classDef platform fill:transparent,stroke:#805AD5,stroke-width:3px
    classDef db fill:transparent,stroke:#3182CE,stroke-width:3px
    classDef cache fill:transparent,stroke:#E53E3E,stroke-width:3px
```

---

## Containers Explained

### 1. FastAPI API Host
**Purpose:**
- receives shopper, support, merchandising, or admin requests;
- exposes playground/admin endpoints;
- exposes health/readiness endpoints.

### 2. Background Worker Host
**Purpose:**
- dispatch outbox messages;
- run async orchestration steps;
- process retries and scheduled evals;
- run embedding refresh and dataset jobs.

**Internal Structure (Shared by both hosts):**
Both hosts deploy the exact same internal code modules and platform services:
- **Modules**: Conversations, Orchestration, Agents, Retrieval, Catalog, Customer Support, Orders, Merchandising, Evaluations, Notifications.
- **Platform**: DB setup, provider abstraction, vector store adapter, internal event bus, telemetry, auth.

### 3. PostgreSQL
Primary durable store with per-module owned tables and an outbox table for async internal workflows.

### 4. Redis
Used for rate limiting, short-lived caching, idempotency / deduplication keys, and lightweight coordination.

### 5. Qdrant
Purpose-built vector store for semantic retrieval over product, policy, and KB content with metadata filtering.

### 6. OpenAI / Anthropic / Bedrock
External providers for generation and embeddings, wrapped behind a local abstraction.

### 7. Existing E-commerce Microservices
Represents the current platform that the POC plugs into: catalog, order management, customer/profile, support/ticketing, pricing/inventory.

---

## Container Interactions

### Synchronous path
```text
Channel / UI → FastAPI → Conversations → Orchestration → response or enqueue more work
```

### Asynchronous path
```text
Request persisted → Outbox event → Worker → Orchestration / Evaluations / Notifications
```

### External action path
```text
Approved workflow → Orders / Support adapter → Existing microservice APIs
```

### Retrieval path
```text
Parsed query → Qdrant + metadata filters + source snippets → grounded context package
```
