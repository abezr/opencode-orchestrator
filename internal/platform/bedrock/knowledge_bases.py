from __future__ import annotations

from typing import Any

import boto3

from internal.platform.config import AWSConfig, BedrockConfig


class BedrockKnowledgeBaseAdapter:
    def __init__(self, aws: AWSConfig, bedrock: BedrockConfig) -> None:
        self._aws = aws
        self._bedrock = bedrock
        self._client = boto3.client("bedrock-agent-runtime", region_name=aws.region)

    def retrieve_and_generate(
        self,
        *,
        query: str,
        knowledge_base_id: str | None = None,
        model_arn_or_id: str | None = None,
    ) -> dict[str, Any]:
        selected_kb = knowledge_base_id or self._bedrock.knowledge_base_id
        selected_model = model_arn_or_id or self._bedrock.knowledge_model_id
        if not selected_kb:
            raise ValueError("Bedrock knowledge base ID is not configured")
        if not selected_model:
            raise ValueError("Bedrock knowledge model ID is not configured")

        response = self._client.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": selected_kb,
                    "modelArn": selected_model,
                },
            },
        )

        citations: list[dict[str, Any]] = []
        for item in response.get("citations", []):
            citations.append(item)

        return {
            "knowledge_base_id": selected_kb,
            "model_arn_or_id": selected_model,
            "text": response.get("output", {}).get("text", ""),
            "citations": citations,
            "session_id": response.get("sessionId"),
            "raw": response,
        }
