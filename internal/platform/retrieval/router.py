from __future__ import annotations

from typing import Any

from internal.platform.bedrock.knowledge_bases import BedrockKnowledgeBaseAdapter
from internal.platform.config import ProfileConfig
from internal.platform.qdrant.adapter import QdrantAdapter


class RetrievalRouter:
    def __init__(
        self,
        settings: ProfileConfig,
        qdrant: QdrantAdapter,
        knowledge_base: BedrockKnowledgeBaseAdapter,
    ) -> None:
        self._settings = settings
        self._qdrant = qdrant
        self._knowledge_base = knowledge_base

    def retrieve(
        self,
        *,
        query: str,
        provider: str | None = None,
        limit: int = 3,
        knowledge_base_id: str | None = None,
        model_arn_or_id: str | None = None,
    ) -> dict[str, Any]:
        selected_provider = provider or "qdrant"
        if selected_provider == "bedrock_knowledge_base":
            result = self._knowledge_base.retrieve_and_generate(
                query=query,
                knowledge_base_id=knowledge_base_id,
                model_arn_or_id=model_arn_or_id,
            )
            return {
                "provider": "bedrock_knowledge_base",
                "items": [],
                "text": result.get("text", ""),
                "citations": result.get("citations", []),
                "metadata": {
                    "knowledge_base_id": result.get("knowledge_base_id"),
                    "model_arn_or_id": result.get("model_arn_or_id"),
                    "session_id": result.get("session_id"),
                },
            }

        snippets = self._qdrant.retrieve(query=query, limit=limit)
        return {
            "provider": "qdrant",
            "items": [
                {
                    "id": snippet.id,
                    "score": snippet.score,
                    "text": snippet.text,
                    "metadata": snippet.metadata,
                }
                for snippet in snippets
            ],
            "text": "",
            "citations": [],
            "metadata": {
                "collection_name": self._settings.qdrant.collection_name,
                "limit": limit,
            },
        }
