"""Default no-dependency implementations so the demo runs before any sponsor
SDK is wired. Each is replaced by a real provider under providers/ + registry.
"""
from typing import Any


class StubLLM:
    def complete(self, prompt: str, *, system: str | None = None, **kw: Any) -> str:
        return f"[stub explanation of: {prompt[:60]}]"

    def classify(self, prompt: str, labels: list[str], **kw: Any) -> str:
        return labels[0]


class StubEmbedding:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 8 for _ in texts]


class StubSearch:
    def index(self, doc_id: str, body: dict[str, Any]) -> None:
        return None

    def search(self, query: str, *, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return []


class PassthroughInferenceOptimizer:
    def optimize(self, prompt: str, **kw: Any) -> str:
        return prompt
