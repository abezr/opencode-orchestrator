# E-commerce AI Orchestration POC Architecture Documentation

<div align="center">

*Exploring how collaborative autonomous agents can be introduced into an e-commerce platform through one AI orchestration service before splitting responsibilities further*

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    subgraph mono ["E-commerce AI Orchestration POC - Single Deployable"]
        direction TB
        subgraph modules ["Modules"]
            M1["Conversations"]:::mod
            M2["Orchestration"]:::mod
            M3["Agents"]:::mod
            M4["Retrieval"]:::mod
            M5["Catalog"]:::mod
            M6["Customer Support"]:::mod
            M7["Orders"]:::mod
            M8["Merchandising"]:::mod
            M9["Evaluations"]:::mod
            M10["Notifications"]:::mod
        end
        PLAT["Shared Platform: FastAPI + SQLAlchemy + Outbox + Jobs"]:::platform
        modules --> PLAT
        PLAT --> DB[("PostgreSQL")]:::db
        PLAT --> RD[("Redis")]:::cache
        PLAT --> VDB[("Qdrant")]:::db
    end

    PLAT --> LLM["OpenAI / Anthropic / Bedrock"]:::ext
    PLAT --> EC["Existing E-commerce Microservices"]:::ext

    classDef mod fill:transparent,stroke:#E53E50,stroke-width:3px
    classDef platform fill:transparent,stroke:#805AD5,stroke-width:3px
    classDef db fill:transparent,stroke:#3182CE,stroke-width:3px
    classDef cache fill:transparent,stroke:#E53E3E,stroke-width:3px
    classDef ext fill:transparent,stroke:#DD6B20,stroke-width:3px
```

</div>

---

## About This Section

This pack explains not only **what** the proposed POC looks like, but **why** a single AI orchestration service is the right starting point for introducing agentic workflows into an existing e-commerce platform.

The design goal is to demonstrate:

- collaborative agent orchestration;
- safe tool use for support and order flows;
- RAG over catalog, customer, and policy data;
- observability and evaluation from day one;
- future extraction into dedicated AI services without rewriting the domain.

---

## Architecture Guide Index

### Core Concepts
| Document | Description | What It Clarifies |
|----------|-------------|-------------------|
| [C4 — Context](./c4-context.md) | People, systems, and trust boundaries | Who interacts with the POC |
| [C4 — Containers](./c4-container.md) | Main deployable/runtime blocks | What runs where |
| [C4 — Components](./c4-components-orchestrator.md) | Orchestration internals | How collaborative flows are coordinated |
| [Agent Workflows](./agent-workflows.md) | Main autonomous collaboration flows | How agents cooperate safely |

### Decisions
| Document | Description | Status |
|----------|-------------|--------|
| [ADR 001](../adr/001-orchestrator-service-first.md) | Start with one orchestration service | Accepted |
| [ADR 002](../adr/002-collaborative-agent-orchestration.md) | Use supervised multi-agent patterns | Accepted |
| [ADR 003](../adr/003-hybrid-retrieval-and-provider-abstraction.md) | Use hybrid retrieval + provider abstraction | Accepted |
| [ADR 004](../adr/004-evaluation-and-human-review-first.md) | Evals and human review are first-class | Accepted |

### Supporting Docs
| Document | Description | Where to Look |
|----------|-------------|---------------|
| [Modules](../modules/README.md) | Module boundaries and ownership | Domain decomposition |
| [API Sketch](../api/README.md) | Main HTTP endpoints | Request entrypoints and internal hooks |

---

## Architectural Principles

### 1. One AI Orchestration Service First

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    subgraph app ["ai-orchestrator · single deployable"]
        direction TB
        subgraph mods ["Modules"]
            C["Conversations"]:::mod
            O["Orchestration"]:::mod
            A["Agents"]:::mod
            R["Retrieval"]:::mod
            CA["Catalog"]:::mod
            S["Customer Support"]:::mod
            OR["Orders"]:::mod
            M["Merchandising"]:::mod
            E["Evaluations"]:::mod
        end
        P["Platform: FastAPI, SQLAlchemy, Transactions, Outbox, Jobs, Telemetry"]:::platform
        mods --> P
    end

    classDef mod fill:transparent,stroke:#E53E50,stroke-width:3px
    classDef platform fill:transparent,stroke:#805AD5,stroke-width:3px
```

**Why this matters:**

- **Fastest path to useful production evidence** — one deployable and one debugging surface
- **Lower operational risk** — new AI logic is centralized instead of spread across many services
- **Clean integration with the existing platform** — adapters call current catalog, order, customer, and support APIs
- **Better for a POC** — prompt, eval, and retrieval iteration stay fast

### 2. Agent Orchestration Must Be Supervised

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    MSG["User / operator request"]:::input --> SUP["Supervisor /\nWorkflow Router"]:::router
    SUP --> GA["Guardrail Agent"]:::agent
    SUP --> IA["Intent Agent"]:::agent
    SUP --> RA["Retrieval Agent"]:::agent
    SUP --> SA["Support Action Agent"]:::agent
    SUP --> MA["Merchandising Agent"]:::agent
    SUP --> CA["Critic Agent"]:::critic
    GA & IA & RA & SA & MA & CA --> RC["Response Composer"]:::output

    classDef input fill:transparent,stroke:#319795,stroke-width:3px
    classDef router fill:transparent,stroke:#2B6CB0,stroke-width:3px
    classDef agent fill:transparent,stroke:#E53E50,stroke-width:3px
    classDef critic fill:transparent,stroke:#D69E2E,stroke-width:3px
    classDef output fill:transparent,stroke:#805AD5,stroke-width:3px
```

The system does not grant open-ended autonomy. Every collaborative flow is bounded by:

- max steps / budget;
- tool allowlists;
- confidence thresholds;
- escalation conditions;
- auditability.

### 3. Retrieval Is Hybrid, Not “Vector Only”

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    Q["Natural-language request"]:::input --> P["Query parser /\nfilter extractor"]:::router
    P --> V["Semantic retrieval\n(Qdrant)"]:::agent
    P --> F["Structured filters\n(price, brand, rating, availability)"]:::gate
    V --> RR["Rerank / fusion"]:::critic
    F --> RR
    RR --> CTX["Grounded context package"]:::output

    classDef input fill:transparent,stroke:#319795,stroke-width:3px
    classDef router fill:transparent,stroke:#2B6CB0,stroke-width:3px
    classDef agent fill:transparent,stroke:#E53E50,stroke-width:3px
    classDef gate fill:transparent,stroke:#38A169,stroke-width:3px
    classDef critic fill:transparent,stroke:#D69E2E,stroke-width:3px
    classDef output fill:transparent,stroke:#805AD5,stroke-width:3px
```

That is critical for e-commerce because many queries combine fuzzy intent with hard constraints.

### 4. Business Actions Are Separated From LLM Reasoning

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    LLM["LLM proposes plan /\naction arguments"]:::agent
    LLM --> GATE["Policy + Tool Gate\nvalidates plan"]:::gate
    GATE --> ACT["Adapter / command handler\nexecutes approved action"]:::output

    classDef agent fill:transparent,stroke:#E53E50,stroke-width:3px
    classDef gate fill:transparent,stroke:#38A169,stroke-width:3px
    classDef output fill:transparent,stroke:#319795,stroke-width:3px
```

The model never directly owns side effects such as refund initiation, order updates, or catalog changes.

### 5. Evaluation and Tracing Are First-Class

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    UM["User message"]:::input
    UM --> TS["Trace span"]:::audit
    UM --> AD["Agent decisions"]:::audit
    UM --> TC["Tool calls"]:::audit
    UM --> TK["Token / cost metrics"]:::audit
    UM --> RQ["Groundedness / quality signals"]:::audit
    UM --> EO["Escalation outcome"]:::audit

    classDef input fill:transparent,stroke:#319795,stroke-width:3px
    classDef audit fill:transparent,stroke:#DD6B20,stroke-width:3px
```

The POC should prove not only that “the AI feature works”, but that:

- we can inspect why it answered the way it did;
- we can compare prompts, providers, and retrieval strategies;
- we can identify failure modes early.
