# AWS / Bedrock Activation Runbook

This document captures the current solution state and the shortest safe path to make the AWS lane real.

## Current code status

The repository already supports:
- real Bedrock Runtime integration for `POST /api/v1/generate`
- real Bedrock Knowledge Base integration for `POST /api/v1/retrieve`
- real AgentCore Gateway MCP mode for `POST /api/v1/support/refund-review`
- provider-switchable orchestration in the LangGraph assist flow
- integration-style graph tests and one thin HTTP-level test for `POST /api/v1/assist`

## What still must happen in AWS

### 1. Bedrock Runtime
Configure a real model for `bedrock_runtime`.

Required runtime settings:
- `AWS_REGION`
- `BEDROCK_ENABLED=true`
- `BEDROCK_RUNTIME_MODEL_ID`

Use this to make `POST /api/v1/generate` a real Bedrock-backed path.

### 2. Bedrock Knowledge Base
Create one narrow document-heavy corpus first, such as refund/help-center/policy content.

Required retrieval settings:
- `BEDROCK_KNOWLEDGE_BASE_ID`
- `BEDROCK_KNOWLEDGE_MODEL_ID`

Use this to make `POST /api/v1/retrieve` real for one managed-RAG slice.

### 3. AgentCore Gateway / Policy for refund review
Provision a real AgentCore Gateway, attach a refund Lambda target and a Policy engine, and expose the refund tool through the Gateway MCP endpoint.

Required refund-tool settings:
- `AGENTCORE_MODE=gateway_mcp`
- `AGENTCORE_GATEWAY_URL`
- `AGENTCORE_GATEWAY_AUTH_HEADER` when inbound authorization is enabled
- `AGENTCORE_REFUND_TOOL_NAME`

Use this to make `POST /api/v1/support/refund-review` hit the real Gateway tool boundary.

## Security note

Do not store or reuse exposed long-term AWS credentials in chat history or repo docs.
Rotate any exposed access key immediately and use temporary credentials or IAM roles for ongoing setup and runtime access.

## Practical activation order

1. Turn on Bedrock Runtime for `POST /api/v1/generate`
2. Turn on one Bedrock Knowledge Base for `POST /api/v1/retrieve`
3. Turn on AgentCore Gateway / Policy for `POST /api/v1/support/refund-review`

## Repository follow-up

The checked-in `config/profiles/dev-openrouter-free.yaml` should still be synchronized locally with the newer AgentCore and Bedrock fields after the repo is fetched outside the GitHub connector path.
