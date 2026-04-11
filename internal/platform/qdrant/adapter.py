from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from internal.platform.config import QdrantConfig
from internal.platform.embeddings.toy import ToyEmbedder


@dataclass(slots=True)
class RetrievedSnippet:
    id: str
    score: float
    text: str
    metadata: dict[str, Any]


_DEMO_DOCUMENTS = [
    {
        "id": "policy-returns",
        "text": "Customers can return eligible items within 30 days. Refund approval is required for damaged or opened high-value items.",
        "metadata": {"source": "policy", "topic": "returns"},
    },
    {
        "id": "order-status",
        "text": "Order status requests should check the order service first and only answer with grounded shipment events.",
        "metadata": {"source": "runbook", "topic": "orders"},
    },
    {
        "id": "catalog-speakers",
        "text": "Waterproof bluetooth speakers should combine semantic product search with structured filters such as price and rating.",
        "metadata": {"source": "catalog-note", "topic": "discovery"},
    },
]


class QdrantAdapter:
    def __init__(self, config: QdrantConfig) -> None:
        self._config = config
        self._embedder = ToyEmbedder(size=config.vector_size)
        self._client = QdrantClient(url=config.url) if config.enabled else None

    def ping(self) -> bool:
        if not self._client:
            return False
        try:
            self._client.get_collections()
            return True
        except Exception:
            return False

    def ensure_collection(self) -> None:
        if not self._client:
            return

        collections = self._client.get_collections().collections
        existing = {item.name for item in collections}
        if self._config.collection_name in existing:
            return

        self._client.create_collection(
            collection_name=self._config.collection_name,
            vectors_config=models.VectorParams(
                size=self._config.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def bootstrap_demo_data(self) -> None:
        if not self._client or not self._config.bootstrap_demo_data:
            return

        self.ensure_collection()
        existing_count = self._client.count(self._config.collection_name, exact=True).count
        if existing_count > 0:
            return

        points = []
        for doc in _DEMO_DOCUMENTS:
            points.append(
                models.PointStruct(
                    id=doc["id"],
                    vector=self._embedder.embed(doc["text"]),
                    payload={
                        "text": doc["text"],
                        **doc["metadata"],
                    },
                )
            )

        self._client.upsert(collection_name=self._config.collection_name, points=points)

    def retrieve(self, query: str, limit: int = 3) -> list[RetrievedSnippet]:
        if not self._client:
            return []

        result = self._client.query_points(
            collection_name=self._config.collection_name,
            query=self._embedder.embed(query),
            with_payload=True,
            limit=limit,
        ).points

        snippets: list[RetrievedSnippet] = []
        for point in result:
            payload = point.payload or {}
            snippets.append(
                RetrievedSnippet(
                    id=str(point.id),
                    score=float(point.score or 0.0),
                    text=str(payload.get("text", "")),
                    metadata={k: v for k, v in payload.items() if k != "text"},
                )
            )
        return snippets
