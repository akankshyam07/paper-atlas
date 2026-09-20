"""Single place that picks a provider implementation. Swap sponsor impls here
via env vars; the rest of the app calls get_* and never sees the vendor.

Example (later):
    if os.getenv("LLM_PROVIDER") == "openai":
        from providers.openai_llm import OpenAILLM
        return OpenAILLM()
"""
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
    return StubLLM()  # TODO: OpenAILLM() when OPENAI_API_KEY set


@lru_cache
def get_embedding() -> EmbeddingProvider:
    return StubEmbedding()  # TODO: OpenAIEmbedding()


@lru_cache
def get_search() -> SearchProvider:
    return StubSearch()  # TODO: ElasticSearchProvider() when ELASTIC_URL set


@lru_cache
def get_research_data() -> ResearchDataProvider:
    # TODO: OpenAlexProvider() (default) / VoloridgeProvider() when available.
    from openalex.client import OpenAlexProvider  # local import: stub for now
    return OpenAlexProvider()


@lru_cache
def get_inference_optimizer() -> InferenceOptimizationProvider:
    return PassthroughInferenceOptimizer()  # TODO: TokenCompanyOptimizer()


@lru_cache
def get_file_source() -> FileSourceProvider:
    return StubFileSource()  # TODO: DropboxFileSource() when DROPBOX_TOKEN set


@lru_cache
def get_speech() -> SpeechProvider:
    return StubSpeech()  # TODO: DeepgramSpeech() when DEEPGRAM_API_KEY set
