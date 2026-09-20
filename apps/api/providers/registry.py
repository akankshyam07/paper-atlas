"""Single place that picks provider implementations (PRD §37).

Each getter prefers the real sponsor implementation when its credentials are
present and falls back to a stub, so the app always runs — with no key it is a
working demo, with a key it is the real thing. Nothing outside this module
imports a vendor SDK.
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache

log = logging.getLogger(__name__)

from providers.base import (
    LLMProvider, EmbeddingProvider, SearchProvider,
    ResearchDataProvider, InferenceOptimizationProvider,
    SpeechProvider,
)
from providers.stubs import (
    StubLLM, StubEmbedding, StubSearch, PassthroughInferenceOptimizer,
    StubSpeech,
)


@lru_cache
def get_llm() -> LLMProvider:
    if os.getenv("OPENAI_API_KEY"):
        try:
            from providers.openai_llm import OpenAILLM
            return OpenAILLM()
        except Exception:  # SDK missing or bad key — keep the app usable
            log.warning("OPENAI_API_KEY is set but OpenAILLM failed; using stub", exc_info=True)
    return StubLLM()


@lru_cache
def get_embedding() -> EmbeddingProvider:
    if os.getenv("OPENAI_API_KEY"):
        try:
            from providers.openai_llm import OpenAIEmbedding
            return OpenAIEmbedding()
        except Exception:
            log.warning("OPENAI_API_KEY is set but OpenAIEmbedding failed; using stub", exc_info=True)
    return StubEmbedding()


@lru_cache
def get_search() -> SearchProvider:
    if os.getenv("ELASTIC_URL"):
        try:
            from providers.elastic_search import ElasticSearchProvider
            return ElasticSearchProvider()
        except Exception:
            log.warning("ELASTIC_URL is set but ElasticSearchProvider failed; using stub", exc_info=True)
    return StubSearch()


@lru_cache
def get_research_data() -> ResearchDataProvider:
    from openalex.client import OpenAlexProvider
    return OpenAlexProvider()


@lru_cache
def get_inference_optimizer() -> InferenceOptimizationProvider:
    # Always on: the local cache and collapse strategies cost nothing and need
    # no key. The Token Company endpoint additionally kicks in when its key set.
    if os.getenv("INFERENCE_OPTIMIZER", "token_company") != "off":
        try:
            from providers.token_company import TokenCompanyOptimizer
            return TokenCompanyOptimizer()
        except Exception:
            pass
    return PassthroughInferenceOptimizer()


@lru_cache
def get_speech() -> SpeechProvider:
    if os.getenv("DEEPGRAM_API_KEY"):
        try:
            from providers.deepgram_speech import DeepgramSpeech
            return DeepgramSpeech()
        except Exception:
            log.warning("DEEPGRAM_API_KEY is set but DeepgramSpeech failed; using stub", exc_info=True)
    return StubSpeech()


def live_providers() -> dict[str, str]:
    """Which implementation each provider resolved to. Logged at startup: a
    stub where a real one was expected is otherwise invisible until a user
    reads "[stub explanation of: ...]" in the chat."""
    return {
        "llm": type(get_llm()).__name__,
        "embedding": type(get_embedding()).__name__,
        "search": type(get_search()).__name__,
        "speech": type(get_speech()).__name__,
        "inference": type(get_inference_optimizer()).__name__,
    }
