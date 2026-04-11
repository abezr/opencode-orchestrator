# ADR 003 — Use Hybrid Retrieval and Provider Abstraction

## Status
Accepted

## Context
E-commerce queries commonly combine:
- fuzzy semantic intent;
- hard filters such as price, brand, stock, rating, or compatibility.

The role also explicitly mentions OpenAI, Anthropic, and AWS Bedrock.

## Decision
Adopt:
1. hybrid retrieval with semantic search + structured filtering + reranking;
2. a provider abstraction for generation and embeddings.

## Consequences

### Positive
- retrieval quality fits real catalog questions better than vector-only search;
- provider choice remains swappable;
- cost and latency routing can evolve without changing business logic.

### Negative
- retrieval evaluation becomes more complex;
- provider normalization layer adds some up-front work.
