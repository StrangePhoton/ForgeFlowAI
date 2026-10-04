"""Deterministic hashed embeddings. Tests never call a paid embedding API."""

import hashlib
import math
import re

_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.IGNORECASE)

EMBEDDING_DIMENSION = 256


class HashedEmbeddingProvider:
    """Feature-hashing embedder. Stable across processes; no network access."""

    dimension = EMBEDDING_DIMENSION

    def embed_query(self, text: str) -> list[float]:
        return _hash_embed(text, self.dimension)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [_hash_embed(text, self.dimension) for text in texts]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    return max(-1.0, min(1.0, dot))


def _hash_embed(text: str, dimension: int) -> list[float]:
    vector = [0.0] * dimension
    tokens = _TOKEN.findall(text.lower())
    if not tokens:
        vector[0] = 1.0
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        vector[0] = 1.0
        return vector
    return [value / norm for value in vector]
