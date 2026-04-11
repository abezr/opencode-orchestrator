# ADR 002 — Use Supervised Collaborative Agent Orchestration

## Status
Accepted

## Context
The vacancy emphasizes:
- RAG;
- agents for workflow automation;
- prompt quality and evaluation;
- latency/cost/performance optimization.

A single mega-prompt would hide decisions, make tool use fragile, and make evaluation harder.

## Decision
Use specialized agents coordinated by a supervisor with:
- workflow routing,
- budget limits,
- tool gates,
- critique,
- human escalation.

## Consequences

### Positive
- workflows become explicit and observable;
- prompts stay smaller and role-specific;
- unsafe tool use is easier to constrain;
- evals can target weak components separately.

### Negative
- more moving parts than one prompt;
- requires stronger tracing and internal contracts.
