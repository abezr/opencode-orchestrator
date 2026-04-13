from __future__ import annotations

from typing import Any

from internal.platform.bedrock.runtime import BedrockRuntimeAdapter
from internal.platform.config import ProfileConfig
from internal.platform.openrouter.client import OpenRouterClient


class GenerationRouter:
    def __init__(
        self,
        settings: ProfileConfig,
        openrouter: OpenRouterClient,
        bedrock_runtime: BedrockRuntimeAdapter,
    ) -> None:
        self._settings = settings
        self._openrouter = openrouter
        self._bedrock_runtime = bedrock_runtime

    async def generate(
        self,
        *,
        messages: list[dict[str, Any]],
        provider: str | None = None,
        system_prompts: list[str] | None = None,
        model_id: str | None = None,
        inference_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        selected_provider = provider or self._settings.inference.provider
        if selected_provider == "bedrock_runtime":
            result = self._bedrock_runtime.converse(
                messages=self._normalize_bedrock_messages(messages),
                system_prompts=system_prompts,
                model_id=model_id,
                inference_config=inference_config,
            )
            return {
                "provider": "bedrock_runtime",
                "model_id": result["model_id"],
                "text": result["text"],
                "metadata": {
                    "usage": result.get("usage", {}),
                    "stop_reason": result.get("stop_reason"),
                },
            }

        result = await self._openrouter.chat(
            self._normalize_openrouter_messages(messages),
            model=model_id,
        )
        return {
            "provider": "openrouter",
            "model_id": result.model,
            "text": result.content,
            "metadata": {
                "used_stub": result.used_stub,
            },
        }

    def _normalize_openrouter_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for message in messages:
            content = message.get("content", "")
            if isinstance(content, list):
                parts: list[str] = []
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        parts.append(str(item["text"]))
                    elif isinstance(item, str):
                        parts.append(item)
                content = "\n".join(parts)
            normalized.append(
                {
                    "role": str(message.get("role", "user")),
                    "content": str(content),
                }
            )
        return normalized

    def _normalize_bedrock_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for message in messages:
            content = message.get("content", "")
            if isinstance(content, str):
                content = [{"text": content}]
            normalized.append(
                {
                    "role": str(message.get("role", "user")),
                    "content": content,
                }
            )
        return normalized
