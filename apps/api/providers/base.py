"""Modular provider interfaces (PRD §37, docs/SPONSORS.md).

Sponsor SDKs implement these Protocols and are wired in providers/registry.py.
Nothing outside a provider implementation may import a sponsor SDK.
"""
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    # OpenAI (default sponsor). Chat/tool-calling/classification.
    def complete(self, prompt: str, *, system: str | None = None, **kw: Any) -> str: ...
    def classify(self, prompt: str, labels: list[str], **kw: Any) -> str: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    # Embeds user/canvas-local content only (not all of OpenAlex).
    def embed(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class SearchProvider(Protocol):
    # Elastic. Hybrid keyword+semantic search over application content.
    def index(self, doc_id: str, body: dict[str, Any]) -> None: ...
    def search(self, query: str, *, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]: ...


@runtime_checkable
class ResearchDataProvider(Protocol):
    # OpenAlex (default) / Voloridge. External scholarly discovery + citations.
    def search_works(self, query: str, *, mode: str = "keyword") -> list[dict[str, Any]]: ...
    def get_work(self, work_id: str) -> dict[str, Any]: ...
    def get_citations(self, work_id: str, *, direction: str) -> list[dict[str, Any]]: ...


@runtime_checkable
class InferenceOptimizationProvider(Protocol):
    # Token Company. Sits in front of the LLM call: compress/route long context.
    def optimize(self, prompt: str, **kw: Any) -> str: ...


@runtime_checkable
class SpeechProvider(Protocol):
    # Deepgram (challenge). Voice input to chat + read-aloud; SDK isolated here.
    def transcribe(self, audio: bytes, *, mime: str = "audio/wav") -> str: ...
    def synthesize(self, text: str) -> bytes: ...
