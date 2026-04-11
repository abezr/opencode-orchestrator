# E-commerce AI Orchestration POC — Modular Monolith (Python + FastAPI + Provider Abstraction)

POC architecture for an AI application that demonstrates **collaborative autonomous agent orchestration** for an e-commerce platform while fitting into an existing microservice ecosystem.

---

## What is included

This repository blueprint adapts the documentation style and folder layout of `justo-agent-poc` to an **e-commerce AI Engineer** use case:

- RAG over product, customer, and operational data
- multi-agent workflows for customer support, merchandising, and order processing
- provider abstraction for **OpenAI, Anthropic, and AWS Bedrock**
- vector retrieval + structured filters for catalog use cases
- evaluation, tracing, prompt/version control, and operator escalation from day one

It is intentionally optimized for:

- fast proof-of-concept delivery;
- low operational complexity;
- clear module boundaries;
- easy integration with an existing microservice-based platform;
- future extraction into dedicated AI services if product value is proven.

---

## Repository Guide

| Section | Purpose |
|---|---|
| [Architecture Overview](./docs/architecture/README.md) | Main architecture document in a diagram-heavy style |
| [C4 — Context](./docs/architecture/c4-context.md) | Actors, systems, and trust boundaries |
| [C4 — Containers](./docs/architecture/c4-container.md) | Runtime blocks and integration boundaries |
| [C4 — Components](./docs/architecture/c4-components-orchestrator.md) | Orchestration internals and control points |
| [Agent Workflows](./docs/architecture/agent-workflows.md) | Collaborative autonomous agent flows |
| [Modules](./docs/modules/README.md) | Domain/module boundaries in the modular monolith |
| [API Sketch](./docs/api/README.md) | Main synchronous and internal endpoints |
| [ADR 001](./docs/adr/001-orchestrator-service-first.md) | Why one orchestration service first |
| [ADR 002](./docs/adr/002-collaborative-agent-orchestration.md) | Why supervised multi-agent collaboration |
| [ADR 003](./docs/adr/003-hybrid-retrieval-and-provider-abstraction.md) | Why hybrid retrieval and model abstraction |
| [ADR 004](./docs/adr/004-evaluation-and-human-review-first.md) | Why evals and human review are first-class |

---

## Proposed Project Layout

```text
opencode-orchestrator/
├── cmd/
│   ├── api/                         # FastAPI app entrypoint
│   └── worker/                      # Async jobs / outbox / scheduled evals
├── internal/
│   ├── platform/
│   │   ├── db/                      # SQLAlchemy setup, migrations, transactions
│   │   ├── bus/                     # In-process event bus + outbox dispatcher
│   │   ├── llm/                     # OpenAI / Anthropic / Bedrock abstraction
│   │   ├── embeddings/              # Embedding model abstraction and policies
│   │   ├── vectorstore/             # Qdrant adapter and retrieval helpers
│   │   ├── telemetry/               # OTel traces, metrics, structured logs
│   │   ├── auth/                    # Admin auth / service auth
│   │   └── storage/                 # Object storage / prompt / eval artifact persistence
│   ├── modules/
│   │   ├── conversations/           # Sessions, turns, summaries, short-term memory
│   │   ├── orchestration/           # Supervisor, workflow router, task graph
│   │   ├── agents/                  # Agent definitions, tool policies, critics
│   │   ├── retrieval/               # Hybrid retrieval over catalog, KB, policies
│   │   ├── catalog/                 # Product data, metadata filters, merchandising facts
│   │   ├── customer_support/        # Support flows, returns, escalation packages
│   │   ├── orders/                  # Order-status / refund / fulfillment adapters
│   │   ├── merchandising/           # Attribute enrichment, campaign/copilot workflows
│   │   ├── evaluations/             # Offline/online eval runs and regression checks
│   │   └── notifications/           # Human handoff / alert routing
│   └── shared/
│       ├── kernel/                  # IDs, money, time, typed primitives, errors
│       └── contracts/               # Internal events / DTOs / schemas
├── docs/
│   ├── architecture/
│   ├── modules/
│   ├── api/
│   └── adr/
└── deploy/
    ├── docker/
    └── compose/
```

---

## How this POC demonstrates autonomous collaboration

This is not “one prompt in, one prompt out”. The POC demonstrates a supervised multi-agent workflow where a request can trigger:

1. guardrail and policy evaluation;
2. intent and workflow classification;
3. hybrid retrieval across knowledge + product + operational data;
4. tool-eligible planning for order or support actions;
5. merchandising or recommendation assistance;
6. critique and groundedness review;
7. final response composition;
8. optional human escalation and audit packaging.

The emphasis is on **observable collaboration**, not blind autonomy.

---

## Why modular monolith first still fits the vacancy

The target company already has an existing platform and microservice-based architecture. This POC therefore starts as a **single AI orchestration deployable** that integrates with existing services through adapters instead of immediately fragmenting into multiple new AI services.

That keeps:
- integration cost low;
- tracing and debugging simple;
- prompt/eval iteration fast;
- service boundaries explicit enough for later extraction.

---

## Future extraction path

The design keeps seams explicit so the following extraction path is possible later:

- `orchestration` → AI Orchestrator service;
- `retrieval` → Retrieval / RAG service;
- `evaluations` → Eval & PromptOps service;
- `customer_support` → Support Automation service;
- `merchandising` → Merchandising Copilot service.

---

## Save target used

The available GitHub connector in this environment could not create a brand-new repository directly, so this blueprint was saved into the existing repository:

`abezr/opencode-orchestrator`
