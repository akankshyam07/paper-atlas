"""OpenAI LLM + embeddings (sponsor: OpenAI). Implements LLMProvider /
EmbeddingProvider. The SDK is imported here and nowhere else (PRD §37).

Every completion goes through the InferenceOptimizationProvider first, so the
Token Company cost-saving layer sits on the one path all LLM calls share.
"""
from __future__ import annotations

import os
from typing import Any

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")


class OpenAILLM:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL) -> None:
        from openai import OpenAI  # imported lazily so the app runs without the SDK

        self._client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])
        self._model = model

    def complete(self, prompt: str, *, system: str | None = None, **kw: Any) -> str:
        # Prompts arrive already optimized — see intel/explain.py, which applies
        # the InferenceOptimizationProvider for every LLM provider, not just this one.
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=kw.get("temperature", 0.3),
            max_tokens=kw.get("max_tokens", 600),
        )
        return (resp.choices[0].message.content or "").strip()

    def classify(self, prompt: str, labels: list[str], **kw: Any) -> str:
        out = self.complete(
            f"{prompt}\n\nAnswer with exactly one of: {', '.join(labels)}.",
            system="You are a precise classifier. Reply with one label and nothing else.",
            max_tokens=8,
        )
        for label in labels:
            if label.lower() in out.lower():
                return label
        return labels[0]


class OpenAIEmbedding:
    def __init__(self, api_key: str | None = None, model: str = EMBED_MODEL) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = self._client.embeddings.create(model=self._model, input=texts)
        return [d.embedding for d in resp.data]
