# Sponsor architecture (PRD §37): every default provider satisfies its interface,
# so a sponsor impl can be swapped in behind the same interface.
from providers.base import (
    LLMProvider, EmbeddingProvider, SearchProvider,
    ResearchDataProvider, InferenceOptimizationProvider,
)
from providers import registry


def test_defaults_satisfy_interfaces():
    assert isinstance(registry.get_llm(), LLMProvider)
    assert isinstance(registry.get_embedding(), EmbeddingProvider)
    assert isinstance(registry.get_search(), SearchProvider)
    assert isinstance(registry.get_research_data(), ResearchDataProvider)
    assert isinstance(registry.get_inference_optimizer(), InferenceOptimizationProvider)
