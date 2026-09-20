"""backend-ai lane. OpenAlex client + cache = default ResearchDataProvider.

Rules (PRD §12): direct ID/DOI fetch when possible, select= to trim payload,
cache only touched works, keyword vs semantic search, never mirror all of it.
Voloridge (PRD §37) is an alternative ResearchDataProvider wired in the registry.
"""
from typing import Any


class OpenAlexProvider:
    """Implements providers.base.ResearchDataProvider. STUB — BE #2 fills in."""

    def search_works(self, query: str, *, mode: str = "keyword") -> list[dict[str, Any]]:
        # TODO(BE#2): httpx call to OpenAlex /works, map via mapping.py.
        return []

    def get_work(self, work_id: str) -> dict[str, Any]:
        # TODO(BE#2): direct ID fetch with select=.
        return {}

    def get_citations(self, work_id: str, *, direction: str) -> list[dict[str, Any]]:
        # TODO(BE#2): referenced_works (out) / cites:<id> (in).
        return []
