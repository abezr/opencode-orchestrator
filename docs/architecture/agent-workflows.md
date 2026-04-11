# Agent Workflows

<div align="center">

*Collaborative autonomous agent workflows for the e-commerce AI orchestration POC*

</div>

---

## Design Goal

The POC should prove **collaboration between specialized agents** instead of relying on one giant prompt. Each workflow combines deterministic orchestration with constrained agent autonomy.

Core idea:
- the system chooses a workflow;
- agents contribute partial work;
- tools are executed only through explicit gates;
- a critic and escalation policy prevent unsafe over-confidence.

---

## Agent Catalog

| Agent | Responsibility | Can Call Tools? | Notes |
|------|----------------|-----------------|------|
| Intent Agent | Classify request and route workflow | No | Fast, low-cost model preferred |
| Guardrail Agent | Detect policy/safety/escalation-sensitive content | No | Runs early |
| Retrieval Agent | Retrieve and summarize grounded evidence | Read-only retrieval | No side effects |
| Support Action Agent | Propose support/order actions and parameters | Proposes only | Never executes directly |
| Merchandising Agent | Produce enrichment / campaign suggestions | Read-only lookup | Optional branch |
| Critic Agent | Review groundedness, policy fit, completeness | No | Can force escalation |
| Escalation Agent | Package request for human handoff | No | Creates concise operator brief |
| Composer Agent | Produce final response or draft output | No | Last generation stage |

---

## Workflow 1 — Customer Support FAQ / Policy Question

### Goal
Answer support-style questions about shipping, returns, warranties, and other grounded policy topics.

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    A["Inbound request"]:::input --> B["Guardrail Agent"]:::agent
    B --> C["Intent Agent"]:::agent
    C --> D["Retrieval Agent"]:::agent
    D --> E["Composer Agent"]:::composer
    E --> F["Critic Agent"]:::critic
    F --> G{"Safe + grounded?"}
    G -- Yes --> H["Send reply"]:::output
    G -- No --> I["Escalation Agent"]:::escalation
    I --> J["Notify operator"]:::escalation

    classDef input fill:transparent,stroke:#319795,stroke-width:3px
    classDef agent fill:transparent,stroke:#E53E50,stroke-width:3px
    classDef composer fill:transparent,stroke:#805AD5,stroke-width:3px
    classDef critic fill:transparent,stroke:#D69E2E,stroke-width:3px
    classDef output fill:transparent,stroke:#319795,stroke-width:3px
    classDef escalation fill:transparent,stroke:#C53030,stroke-width:3px
```

## Workflow 2 — Order Status / Return / Refund Request

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    A["Inbound request"]:::input --> B["Guardrail Agent"]:::agent
    B --> C["Intent Agent"]:::agent
    C --> D["Retrieval Agent"]:::agent
    C --> E["Support Action Agent"]:::agent
    E --> F["Tool Execution Gate"]:::gate
    F --> G["Order / ticket / refund adapters"]:::ext
    D --> H["Composer Agent"]:::composer
    G --> H
    H --> I["Critic Agent"]:::critic
    I --> J{"Need human approval?"}
    J -- No --> K["Send reply"]:::output
    J -- Yes --> L["Escalation Agent"]:::escalation
    L --> M["Notify operator"]:::escalation

    classDef input fill:transparent,stroke:#319795,stroke-width:3px
    classDef agent fill:transparent,stroke:#E53E50,stroke-width:3px
    classDef gate fill:transparent,stroke:#38A169,stroke-width:3px
    classDef ext fill:transparent,stroke:#DD6B20,stroke-width:3px
    classDef composer fill:transparent,stroke:#805AD5,stroke-width:3px
    classDef critic fill:transparent,stroke:#D69E2E,stroke-width:3px
    classDef output fill:transparent,stroke:#319795,stroke-width:3px
    classDef escalation fill:transparent,stroke:#C53030,stroke-width:3px
```

## Workflow 3 — Catalog Q&A / Guided Discovery

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    A["Natural-language product query"]:::input --> B["Intent Agent"]:::agent
    B --> C["Retrieval Agent\n(hybrid search + filters)"]:::agent
    C --> D["Composer Agent"]:::composer
    D --> E["Critic Agent"]:::critic
    E --> F["Grounded response with product shortlist"]:::output

    classDef input fill:transparent,stroke:#319795,stroke-width:3px
    classDef agent fill:transparent,stroke:#E53E50,stroke-width:3px
    classDef composer fill:transparent,stroke:#805AD5,stroke-width:3px
    classDef critic fill:transparent,stroke:#D69E2E,stroke-width:3px
    classDef output fill:transparent,stroke:#319795,stroke-width:3px
```

## Workflow 4 — Merchandising Copilot

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    A["Internal merchandising request"]:::input --> B["Intent Agent"]:::agent
    B --> C["Retrieval Agent"]:::agent
    B --> D["Merchandising Agent"]:::agent
    C --> E["Composer Agent"]:::composer
    D --> E
    E --> F["Critic Agent"]:::critic
    F --> G["Return structured draft / suggestion"]:::output

    classDef input fill:transparent,stroke:#319795,stroke-width:3px
    classDef agent fill:transparent,stroke:#E53E50,stroke-width:3px
    classDef composer fill:transparent,stroke:#805AD5,stroke-width:3px
    classDef critic fill:transparent,stroke:#D69E2E,stroke-width:3px
    classDef output fill:transparent,stroke:#319795,stroke-width:3px
```

## Workflow 5 — Escalation-First Path

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    A["Inbound request"]:::input --> B["Guardrail Agent"]:::agent
    B --> C{"Sensitive / ambiguous / high-risk?"}
    C -- Yes --> D["Escalation Agent"]:::escalation
    D --> E["Create operator brief"]:::escalation
    E --> F["Notify human owner"]:::escalation
    F --> G["Optional holding response"]:::output
    C -- No --> H["Normal workflow"]:::output

    classDef input fill:transparent,stroke:#319795,stroke-width:3px
    classDef agent fill:transparent,stroke:#E53E50,stroke-width:3px
    classDef escalation fill:transparent,stroke:#C53030,stroke-width:3px
    classDef output fill:transparent,stroke:#319795,stroke-width:3px
```
