"""AI explanation / summarisation of a paper or a selected excerpt (PRD §10).

Provenance is the point: the caller records which source object and excerpt the
artifact came from. This module only builds the prompt and calls the LLM through
the provider interface.
"""
from __future__ import annotations

from typing import Any

from openalex import mapping

SYSTEM = (
    "You explain research clearly to a technical reader who is new to this "
    "specific paper. Be concrete and factual. Never invent findings, numbers, or "
    "citations. If the provided context is thin, say what is unclear."
)


def build_prompt(*, text: str | None, work: dict[str, Any] | None, action: str = "explain") -> str:
    parts: list[str] = []
    if work:
        hier = mapping.hierarchy(work)
        parts.append(f"Paper: {work.get('title') or work.get('display_name')}")
        if work.get("publication_year"):
            parts.append(f"Year: {work['publication_year']}")
        authors = mapping.authors(work, limit=5)
        if authors:
            parts.append("Authors: " + ", ".join(authors))
        if hier.get("topic"):
            parts.append(f"Field: {hier.get('field')} / {hier.get('subfield')} / {hier.get('topic')}")
        kws = mapping.keywords(work)
        if kws:
            parts.append("Keywords: " + ", ".join(kws[:8]))
        abstract = mapping.abstract_text(work.get("abstract_inverted_index"))
        if abstract:
            parts.append(f"Abstract: {abstract[:2500]}")
    if text:
        parts.append(f"Selected passage:\n{text[:2500]}")

    verb = {
        "explain": "Explain what this is about and why it matters, in 3-5 sentences.",
        "summarize": "Summarise the key claim, method, and result in 3-5 sentences.",
    }.get(action, "Explain this in 3-5 sentences.")
    parts.append(verb)
    return "\n\n".join(parts)


def explain(*, text: str | None, work: dict[str, Any] | None, action: str = "explain") -> str:
    from providers.registry import get_inference_optimizer, get_llm

    # Optimize here, not inside a provider: this is the one place every LLM
    # prompt is built, so the cost-saving layer covers all providers.
    prompt = get_inference_optimizer().optimize(build_prompt(text=text, work=work, action=action))
    return get_llm().complete(prompt, system=SYSTEM)
