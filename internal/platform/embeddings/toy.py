from __future__ import annotations

import math
from typing import Iterable


class ToyEmbedder:
    """A tiny deterministic embedder for demos.

    This is intentionally simple so the scaffold can run without a paid embedding API.
    Replace it with a real embedding provider once the orchestration skeleton is proven.
    """

    def __init__(self, size: int = 16) -> None:
        self.size = size

    def embed(self, text: str) -> list[float]:
        buckets = [0.0] * self.size
        if not text:
            return buckets

        for index, char in enumerate(text.lower()):
            bucket = index % self.size
            buckets[bucket] += (ord(char) % 97) / 97.0

        norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
        return [value / norm for value in buckets]

    def embed_many(self, texts: Iterable[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]
