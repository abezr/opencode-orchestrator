# C4 — Level 3: Components of the Orchestration Core

<div align="center">

*How collaborative autonomous agent execution is coordinated inside the AI orchestration service*

</div>

---

## Component Diagram

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    subgraph orch ["Orchestration Core"]
        direction TB
        IN["Inbound Request\nIngested"]:::input
        MEM["Context Builder"]:::context
        SUP["Supervisor /\nWorkflow Router"]:::router
        BUD["Budget &\nPolicy Gate"]:::gate

        IN --> MEM --> SUP --> BUD

        REG["Agent Registry"]:::router
        BUD --> REG

        RET["Retrieval Agent"]:::agent
        ACT["Support Action Planner"]:::agent
        MER["Merchandising Agent"]:::agent
        REG --> RET
        REG --> ACT
        REG --> MER

        TOOL["Tool Execution\nGate"]:::gate
        ACT --> TOOL

        COMP["Response\nComposer"]:::composer
        RET --> COMP
        TOOL --> COMP
        MER --> COMP

        CRIT["Critic /\nGroundedness Reviewer"]:::critic
        COMP --> CRIT

        ESCL["Escalation\nPolicy"]:::escalation
        CRIT -- "Low confidence / high risk" --> ESCL

        OUT["Outbound Event\nDispatcher"]:::output
        CRIT -- "Pass" --> OUT
        ESCL --> OUT
    end

    AUD["Audit & Eval\nEmitter"]:::audit
    SUP -. "audit" .-> AUD
    TOOL -. "audit" .-> AUD
    CRIT -. "audit" .-> AUD
    OUT -. "audit" .-> AUD

    classDef input fill:transparent,stroke:#319795,stroke-width:3px
    classDef context fill:transparent,stroke:#3182CE,stroke-width:3px
    classDef router fill:transparent,stroke:#2B6CB0,stroke-width:3px
    classDef agent fill:transparent,stroke:#E53E50,stroke-width:3px
    classDef gate fill:transparent,stroke:#38A169,stroke-width:3px
    classDef composer fill:transparent,stroke:#805AD5,stroke-width:3px
    classDef critic fill:transparent,stroke:#D69E2E,stroke-width:3px
    classDef output fill:transparent,stroke:#319795,stroke-width:3px
    classDef escalation fill:transparent,stroke:#C53030,stroke-width:3px
    classDef audit fill:transparent,stroke:#DD6B20,stroke-width:3px
```

---

## Components

### Supervisor / Workflow Router
Selects which workflow to run for the current request and enforces step budgets.

### Budget & Policy Gate
Global control point that prevents unsafe or runaway execution.

Typical checks:
- max tokens;
- max external tool calls;
- max wall-clock time;
- tool eligibility by workflow;
- escalation-required categories.

### Agent Registry
Catalog of available agents and their contracts.

Examples:
- `IntentAgent`
- `GuardrailAgent`
- `RetrievalAgent`
- `SupportActionAgent`
- `MerchandisingAgent`
- `CriticAgent`
- `EscalationAgent`
- `ComposerAgent`

### Context Builder
Builds the working context from recent turns, summaries, actor context, routing hints, and workflow-specific retrieval inputs.

### Retrieval Agent
Builds grounded context from semantic search, metadata filters, policy excerpts, order snippets, and reranked evidence.

### Support Action Planner
Turns support/order intent + retrieved context into a structured plan. The plan is a proposal, not an executable side effect by itself.

### Merchandising Agent
Handles catalog and campaign-oriented assistance such as attribute hints, enrichment suggestions, and bundle ideas.

### Tool Execution Gate
The only place where business actions can be executed.

### Critic / Groundedness Reviewer
Checks groundedness, policy fit, contradiction to evidence, completeness, and confidence.

### Response Composer
Builds the final user-facing or operator-facing answer from retrieved knowledge, structured action results, and merchandising suggestions.

### Escalation Policy
Decides when to involve a human.

### Audit & Eval Emitter
Emits structured records for every meaningful step so later analysis can explain cost, failure modes, and quality.
