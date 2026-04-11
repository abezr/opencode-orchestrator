# ADR 001 — Start with One AI Orchestration Service

## Status
Accepted

## Context
The existing platform is already composed of business services. The new work is to add AI features that span support, catalog, and merchandising use cases.

A naive response would be to immediately create many new AI services. That would increase operational complexity before the team has:
- validated workflows;
- validated eval methodology;
- learned which retrieval and provider choices work best.

## Decision
Start with one AI orchestration service implemented as a modular monolith.

## Consequences

### Positive
- faster proof-of-value;
- simpler tracing and debugging;
- easier prompt/eval iteration;
- cleaner cost control while usage is still uncertain.

### Negative
- not the final service topology;
- stronger discipline is required to keep module boundaries clean.
