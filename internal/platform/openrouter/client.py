from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from internal.platform.config import InferenceConfig, OpenRouterConfig, get_openrouter_api_key


@dataclass(slots=True)
class ChatResult:
    model: str
    content: str
    raw: dict[str, Any]
    used_stub: bool = False


class OpenRouterClient:
    def __init__(self, config: OpenRouterConfig, inference: InferenceConfig) -> None:
        self._config = config
        self._inference = inference

    async def chat(self, messages: list[dict[str, str]], model: str | None = None) -> ChatResult:
        api_key = get_openrouter_api_key()
        selected_model = model or self._inference.model
        fallback_models = [item for item in self._inference.fallback_models if item != selected_model]

        if not api_key:
            if self._inference.stub_if_missing_api_key:
                return ChatResult(
                    model="stub/no-api-key",
                    content=(
                        "OpenRouter API key is not configured. "
                        "The scaffold is running in stub mode."
                    ),
                    raw={"messages": messages},
                    used_stub=True,
                )
            raise RuntimeError("OPENROUTER_API_KEY is missing and stub mode is disabled")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._config.site_url,
            "X-OpenRouter-Title": self._config.app_name,
        }
        payload: dict[str, Any] = {
            "messages": messages,
            "temperature": self._inference.temperature,
            "max_tokens": self._inference.max_tokens,
        }
        if fallback_models:
            payload["model"] = selected_model
            payload["models"] = [selected_model, *fallback_models]
        else:
            payload["model"] = selected_model

        timeout = httpx.Timeout(self._inference.timeout_seconds)
        async with httpx.AsyncClient(base_url=self._config.base_url, timeout=timeout) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ChatResult(
            model=data.get("model", selected_model),
            content=content,
            raw=data,
            used_stub=False,
        )
