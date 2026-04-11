# ADR 005 — Use Bedrock AgentCore as the Ops and Governance Layer

## Status
Accepted

## Context
The selected implementation direction is Python-first:
- FastAPI
- LangGraph orchestration
- provider abstraction
- Qdrant/custom retrieval
- PostgreSQL-backed escalation outbox

That stack is a strong fit for the vacancy, but it still needs a clearer production story for:
- centralized controls over tool access
- secure managed execution where needed
- production observability for agent workflows
- evaluation and governance outside application code

## Decision
Adopt **Amazon Bedrock AgentCore** as the preferred ops/governance extension layer.

Use AgentCore primarily for:
- Gateway
- Policy
- Observability
- Evaluations

Keep LangGraph as the main orchestration runtime.

Use Bedrock Flows and Knowledge Bases only as optional additions for selected workflows and corpora.

## Consequences

### Positive
- adds AWS-native governance without forcing a rewrite of the core Python app
- keeps provider abstraction and LangGraph flexibility intact
- creates a clean path to stronger tool controls and production evaluation
- preserves the current custom Qdrant path where it is still better suited

### Negative
- adds a second architectural plane to understand
- requires care to avoid duplicating orchestration logic across LangGraph and Flows
- introduces AWS-specific operational dependencies for governance features
