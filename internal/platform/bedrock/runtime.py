from __future__ import annotations

from typing import Any

import boto3

from internal.platform.config import AWSConfig, BedrockConfig


class BedrockRuntimeAdapter:
    def __init__(self, aws: AWSConfig, bedrock: BedrockConfig) -> None:
        self._aws = aws
        self._bedrock = bedrock
        self._client = boto3.client("bedrock-runtime", region_name=aws.region)

    def converse(
        self,
        *,
        messages: list[dict[str, Any]],
        system_prompts: list[str] | None = None,
        model_id: str | None = None,
        inference_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        selected_model = model_id or self._bedrock.runtime_model_id
        if not selected_model:
            raise ValueError("Bedrock runtime model ID is not configured")

        payload: dict[str, Any] = {
            "modelId": selected_model,
            "messages": messages,
        }
        if system_prompts:
            payload["system"] = [{"text": item} for item in system_prompts]
        if inference_config:
            payload["inferenceConfig"] = inference_config

        response = self._client.converse(**payload)
        text_fragments: list[str] = []
        for block in response.get("output", {}).get("message", {}).get("content", []):
            if isinstance(block, dict) and "text" in block:
                text_fragments.append(str(block["text"]))

        return {
            "model_id": selected_model,
            "text": "\n".join(fragment for fragment in text_fragments if fragment),
            "usage": response.get("usage", {}),
            "stop_reason": response.get("stopReason"),
            "raw": response,
        }
