# Selected Dev Profile — LangGraph + OpenRouter Free Models

## Decision
For the selected Python-first architecture, use **LangChain + LangGraph** for orchestration and **OpenRouter free models** as the default zero-cost inference layer during development and demo work.

## Why this profile
- keeps the stack Python-first;
- avoids direct dependence on a single vendor SDK;
- allows easy provider abstraction later;
- makes the POC usable without paid OpenAI credits.

## Recommended model strategy

### Default
Use the OpenRouter free router:
- `openrouter/free`

### More controlled fallback
When a specific model proves more stable, pin a specific free variant using the `:free` suffix, for example:
- `meta-llama/...:free`
- `qwen/...:free`

## Suggested runtime policy
- primary: `openrouter/free`
- fallback list: curated specific `:free` models
- strict timeout per node
- graceful degradation to human escalation or a deterministic fallback when free capacity is unavailable

## Architecture note
OpenRouter free models are best for:
- prototyping;
- integration testing;
- architecture demos;
- low-volume internal experiments.

They are not the right default for production-critical flows because availability and latency can vary.

## Other stack pieces
- FastAPI
- LangGraph
- LangChain integrations
- PostgreSQL
- Qdrant
- optional LangSmith free developer tier
