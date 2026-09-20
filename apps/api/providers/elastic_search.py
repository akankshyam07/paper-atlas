"""Elastic hybrid search (sponsor: Elastic). Implements SearchProvider.

Indexes only application/user content — canvas objects, excerpts, notes, AI
artifacts, parsed PDF chunks — plus cached scholarly metadata. OpenAlex stays
the scholarly source of truth and is never mirrored here (PRD §37).

Hybrid = BM25 keyword matching unioned with kNN vector similarity, so exact
terms and meaning both retrieve. The embedding comes from EmbeddingProvider, so
Elastic never talks to a model vendor itself.
"""
from __future__ import annotations

import os
from typing import Any

INDEX = os.getenv("ELASTIC_INDEX", "paper-atlas")
# text-embedding-3-small; must match the EmbeddingProvider in use.
EMBED_DIMS = int(os.getenv("ELASTIC_EMBED_DIMS", "1536"))

MAPPING: dict[str, Any] = {
    "properties": {
        "canvas_id": {"type": "keyword"},
        "object_id": {"type": "keyword"},
        "object_type": {"type": "keyword"},
        "title": {"type": "text"},
        "text": {"type": "text"},
        "openalex_id": {"type": "keyword"},
        "year": {"type": "integer"},
        "embedding": {"type": "dense_vector", "dims": EMBED_DIMS, "index": True, "similarity": "cosine"},
    }
}


class ElasticSearchProvider:
    def __init__(self, url: str | None = None, api_key: str | None = None) -> None:
        from elasticsearch import Elasticsearch  # imported lazily; SDK isolated here

        url = url or os.environ["ELASTIC_URL"]
        key = api_key or os.getenv("ELASTIC_API_KEY")
        self._es = Elasticsearch(url, api_key=key) if key else Elasticsearch(url)
        self._ensure_index()

    def _ensure_index(self) -> None:
        if not self._es.indices.exists(index=INDEX):
            self._es.indices.create(index=INDEX, mappings=MAPPING)

    def _embed(self, text: str) -> list[float] | None:
        from providers.registry import get_embedding

        try:
            vectors = get_embedding().embed([text])
            vector = vectors[0] if vectors else None
        except Exception:
            return None
        # A stub embedding has the wrong width; skip the vector clause instead of
        # failing the whole query.
        return vector if vector and len(vector) == EMBED_DIMS else None

    def index(self, doc_id: str, body: dict[str, Any]) -> None:
        text = " ".join(str(body.get(k, "")) for k in ("title", "text")).strip()
        vector = self._embed(text) if text else None
        doc = {k: v for k, v in body.items() if k != "embedding"}
        if vector:
            doc["embedding"] = vector
        self._es.index(index=INDEX, id=doc_id, document=doc, refresh=False)

    def search(self, query: str, *, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        must: list[dict[str, Any]] = [
            {"multi_match": {"query": query, "fields": ["title^2", "text"]}}
        ]
        filter_clauses = [{"term": {k: v}} for k, v in (filters or {}).items() if v is not None]

        body: dict[str, Any] = {
            "size": 10,
            "query": {"bool": {"must": must, "filter": filter_clauses}},
        }
        vector = self._embed(query)
        if vector:
            # kNN runs alongside BM25; Elastic blends both rankings.
            body["knn"] = {
                "field": "embedding", "query_vector": vector,
                "k": 10, "num_candidates": 100,
                **({"filter": filter_clauses} if filter_clauses else {}),
            }
        try:
            res = self._es.search(index=INDEX, body=body)
        except Exception:
            return []
        return [
            {"id": h["_id"], "score": h.get("_score"), **(h.get("_source") or {})}
            for h in res.get("hits", {}).get("hits", [])
        ]
