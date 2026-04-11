# ADR 004 — Evaluation and Human Review Are First-Class

## Status
Accepted

## Context
Production AI features fail in subtle ways:
- weak grounding;
- stale or missing data;
- excessive cost;
- policy drift;
- unsafe confidence.

These problems are often invisible unless the system emits structured evidence.

## Decision
Make evaluation, tracing, and human escalation first-class design elements from the start.

## Consequences

### Positive
- prompt changes become measurable;
- provider and retrieval trade-offs become visible;
- risky workflows can degrade safely to human review.

### Negative
- more instrumentation work in the POC;
- some demo speed is traded for operational credibility.
