"""Sponsor provider behaviour that runs without any credentials (PRD §37).

The Token Company optimizer is fully exercised here because its local
strategies need no key — and measured savings is the challenge deliverable.
"""
from providers.base import (
    LLMProvider, EmbeddingProvider, SearchProvider, ResearchDataProvider,
    InferenceOptimizationProvider, FileSourceProvider, SpeechProvider,
)
from providers import registry
from providers.token_company import TokenCompanyOptimizer


def test_defaults_satisfy_interfaces():
    assert isinstance(registry.get_llm(), LLMProvider)
    assert isinstance(registry.get_embedding(), EmbeddingProvider)
    assert isinstance(registry.get_search(), SearchProvider)
    assert isinstance(registry.get_research_data(), ResearchDataProvider)
    assert isinstance(registry.get_inference_optimizer(), InferenceOptimizationProvider)
    assert isinstance(registry.get_file_source(), FileSourceProvider)
    assert isinstance(registry.get_speech(), SpeechProvider)


def test_optimizer_preserves_meaning_while_shrinking():
    opt = TokenCompanyOptimizer(api_key=None)
    prompt = "Explain   this  paper.\n\n\n\nAbstract:   attention is all you need."
    out = opt.optimize(prompt)
    assert "Explain this paper." in out
    assert "attention is all you need" in out
    assert "   " not in out
    assert len(out) < len(prompt)


def test_optimizer_drops_duplicated_context_blocks():
    opt = TokenCompanyOptimizer(api_key=None)
    para = "This is a long repeated context paragraph about sparse autoencoders."
    out = opt.optimize(f"{para}\n{para}\n{para}\nQuestion: why?")
    assert out.count(para) == 1
    assert "Question: why?" in out


def test_optimizer_caches_repeated_prompts_and_reports_savings():
    opt = TokenCompanyOptimizer(api_key=None)
    prompt = "Summarise this paper about interpretability in language models." * 4
    opt.optimize(prompt)
    opt.optimize(prompt)
    assert opt.cache_hits == 1
    stats = opt.stats()
    assert stats["tokens_saved"] > 0
    assert stats["percent_saved"] > 0


def test_optimizer_never_raises_without_network():
    # A failed compression must degrade to the local result, not break the call.
    opt = TokenCompanyOptimizer(api_key="bogus-key")
    long_prompt = "x " * 2000
    assert opt.optimize(long_prompt)
