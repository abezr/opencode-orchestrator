# Bedrock AgentCore for Ops and Governance

This document explains how to extend the current **LangGraph + OpenRouter + PostgreSQL + Qdrant** scaffold with **Amazon Bedrock AgentCore** as the operational and governance plane.

## Why AgentCore is the right next step

The current scaffold already proves:
- Python-first orchestration
- provider abstraction
- deterministic escalation
- persisted operator-task outbox

The next gap is production governance:
- where tool access is governed
- where agent sessions run securely
- where production observability and evaluation live
- how operators and platform teams get centralized controls

For that layer, the best AWS-aligned addition is AgentCore.

## Recommended role of AgentCore in this repo

Keep the **decisioning/orchestration brain** in our Python service for now.
Use **AgentCore** around it for production controls.

### Suggested split
- **LangGraph service**: workflow logic, domain adapters, retrieval policy, escalation rules
- **AgentCore Runtime**: secure runtime and deployment target for agent workloads that should move to managed execution
- **AgentCore Gateway**: controlled tool exposure for order/support/catalog adapters
- **AgentCore Policy**: centralized authorization and validation for agent-tool interactions
- **AgentCore Observability + Evaluations**: production monitoring, quality checks, regression and online evaluation

## Target hybrid architecture

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    UI["Support Console / Admin UI / Assistant Widget"]:::ext --> API["FastAPI + LangGraph Orchestrator"]:::app

    API --> Q[("Qdrant")]:::db
    API --> PG[("PostgreSQL") ]:::db
    API --> OR["OpenRouter / selected model providers"]:::ext

    API --> GW["AgentCore Gateway"]:::aws
    GW --> POL["AgentCore Policy"]:::aws
    GW --> ECO["Existing E-commerce Microservices"]:::ext

    API --> OBS["AgentCore Observability"]:::aws
    API --> EVAL["AgentCore Evaluations"]:::aws

    API -. optional managed execution .-> RT["AgentCore Runtime"]:::aws

    classDef ext fill:transparent,stroke:#DD6B20,stroke-width:3px
    classDef app fill:transparent,stroke:#319795,stroke-width:3px
    classDef db fill:transparent,stroke:#3182CE,stroke-width:3px
    classDef aws fill:transparent,stroke:#805AD5,stroke-width:3px
```

## Recommended adoption order

### Phase 1 — Governance first
Adopt these first:
- AgentCore Gateway
- AgentCore Policy
- AgentCore Observability
- AgentCore Evaluations

This is the highest-value move because it adds controls without forcing us to rebuild the core Python orchestration path.

### Phase 2 — Optional managed runtime
Adopt AgentCore Runtime only for flows that benefit from:
- stricter managed execution
- long-running sessions
- deeper AWS-native deployment controls

### Phase 3 — Optional managed workflow/RAG pieces
Evaluate:
- Bedrock Flows for visible approval workflows
- Knowledge Bases for selected managed-RAG paths

## Concrete mapping from current scaffold

### Current operator-task outbox
Current state:
- escalations are written to PostgreSQL
- `/internal/escalations` exposes queued items

Next step with AgentCore:
- emit operator-task creation events into AgentCore Observability context
- evaluate escalated traces with AgentCore Evaluations
- eventually expose selected escalation actions as Gateway-controlled tools

### Current support/order adapters
Current state:
- adapters are called from Python orchestration

Next step with AgentCore:
- register those adapters behind AgentCore Gateway
- attach Policy rules to prevent unsafe invocations
- keep domain validation in Python while moving access control outside agent code

### Current request tracing
Current state:
- `X-Request-ID` ties API responses to graph execution

Next step with AgentCore:
- propagate `trace_id` and workflow metadata into AgentCore Observability spans and evaluation datasets

## Guardrails for this repo

1. Do **not** replace LangGraph yet.
2. Do **not** move all retrieval into Bedrock-managed services at once.
3. Start with governance around the current app, not a rewrite of the app.
4. Keep provider abstraction intact even if Bedrock services are adopted for operations.

## Minimal implementation target after this doc

When we implement AgentCore in code, the first thin slice should be:
- config fields for AWS/AgentCore resources
- one Gateway-facing adapter registration boundary
- one Policy-aware approval path for support/review actions
- one Observability/Evaluations integration point for escalated requests
