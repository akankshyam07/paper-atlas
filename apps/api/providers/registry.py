"""Single place that picks provider implementations (PRD §37).

Each getter prefers the real sponsor implementation when its credentials are
present and falls back to a stub, so the app always runs — with no key it is a
working demo, with a key it is the real thing. Nothing outside this module
imports a vendor SDK.
"""
from __future__ import annotations

import os
from functools import lru_cache

from providers.base import (
    LLMProvider, EmbeddingProvider, SearchProvider,
    ResearchDataProvider, InferenceOptimizationProvider, FileSourceProvider,
    SpeechProvider,
)
from providers.stubs import (
    StubLLM, StubEmbedding, StubSearch, PassthroughInferenceOptimizer,
    StubFileSource, StubSpeech,
)


@lru_cache
def get_llm() -> LLMProvider:
    if os.getenv("OPENAI_API_KEY"):
        try:
            from providers.openai_llm import OpenAILLM
            return OpenAILLM()
        except Exception:  # SDK missing or bad key — keep the app usable
            pass
    return StubLLM()


@lru_cache
def get_embedding() -> EmbeddingProvider:
    if os.getenv("OPENAI_API_KEY"):
        try:
            from providers.openai_llm import OpenAIEmbedding
            return OpenAIEmbedding()
        except Exception:
            pass
    return StubEmbedding()


@lru_cache
def get_search() -> SearchProvider:
    # TODO: ElasticSearchProvider() when ELASTIC_URL is set.
    return StubSearch()


@lru_cache
def get_research_data() -> ResearchDataProvider:
    from openalex.client import OpenAlexProvider
    return OpenAlexProvider()


@lru_cache
def get_inference_optimizer() -> InferenceOptimizationProvider:
    # TODO: TokenCompanyOptimizer() (LLM cost saving) when its key is set.
    return PassthroughInferenceOptimizer()


@lru_cache
def get_file_source() -> FileSourceProvider:
    return StubFileSource()  # TODO: DropboxFileSource() when DROPBOX_TOKEN set


@lru_cache
def get_speech() -> SpeechProvider:
    return StubSpeech()  # TODO: DeepgramSpeech() when DEEPGRAM_API_KEY set
