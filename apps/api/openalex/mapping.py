"""Map OpenAlex payloads to our shapes. Keeps payload assumptions out of
routes/components (context.md: don't bury OpenAlex assumptions in callers).
"""
from __future__ import annotations

import re
from typing import Any

# Fields we ask OpenAlex for. `select=` keeps payloads small (PRD §12).
WORK_FIELDS = (
    "id,doi,title,display_name,publication_year,type,cited_by_count,fwci,"
    "authorships,primary_location,best_oa_location,open_access,topics,keywords,"
    "referenced_works,related_works,abstract_inverted_index,counts_by_year,locations"
)
# Lighter projection for search results / candidate pools.
LIST_FIELDS = (
    "id,doi,title,display_name,publication_year,type,cited_by_count,fwci,"
    "authorships,primary_location,best_oa_location,open_access,topics,keywords,locations"
)


def short_id(openalex_id: str | None) -> str:
    """'https://openalex.org/W123' -> 'W123'."""
    if not openalex_id:
        return ""
    return openalex_id.rstrip("/").rsplit("/", 1)[-1]


def abstract_text(inverted: dict[str, list[int]] | None) -> str | None:
    """OpenAlex stores abstracts as an inverted index; rebuild the prose."""
    if not inverted:
        return None
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted.items():
        for i in idxs:
            positions.append((i, word))
    if not positions:
        return None
    positions.sort()
    return " ".join(w for _, w in positions)


def authors(work: dict[str, Any], limit: int = 8) -> list[str]:
    out: list[str] = []
    for a in (work.get("authorships") or [])[:limit]:
        name = (a.get("author") or {}).get("display_name")
        if name:
            out.append(name)
    return out


def venue(work: dict[str, Any]) -> str | None:
    loc = work.get("primary_location") or {}
    src = loc.get("source") or {}
    return src.get("display_name") or loc.get("raw_source_name")


_ARXIV = re.compile(r"arxiv\.org/(?:abs|pdf)/(.+?)(?:v\d+)?(?:\.pdf)?/?$", re.I)


def _arxiv_pdf(url: str | None) -> str | None:
    m = _ARXIV.search(url or "")
    return f"https://arxiv.org/pdf/{m.group(1)}" if m else None


def pdf_url(work: dict[str, Any]) -> str | None:
    """Priority per PRD §12: any OA location's pdf -> arXiv landing page -> an
    oa_url that is itself a PDF.

    A landing page is deliberately NOT returned: the viewer cannot render HTML,
    so the node would show a broken preview where the abstract belongs.
    """
    locs = [work.get("best_oa_location"), work.get("primary_location"), *(work.get("locations") or [])]
    for loc in locs:
        if loc and loc.get("pdf_url"):
            return loc["pdf_url"]
    for loc in locs:
        arx = _arxiv_pdf((loc or {}).get("landing_page_url"))
        if arx:
            return arx
    oa = (work.get("open_access") or {}).get("oa_url")
    return _arxiv_pdf(oa) or (oa if (oa or "").lower().endswith(".pdf") else None)


def has_pdf(work: dict[str, Any]) -> bool:
    return bool(pdf_url(work))


def topic_ids(work: dict[str, Any]) -> list[str]:
    return [short_id(t.get("id")) for t in (work.get("topics") or []) if t.get("id")]


def hierarchy(work: dict[str, Any]) -> dict[str, str | None]:
    """Primary topic's place in domain -> field -> subfield -> topic."""
    topics = work.get("topics") or []
    t = topics[0] if topics else {}
    return {
        "topic": t.get("display_name"),
        "topic_id": short_id(t.get("id")) if t.get("id") else None,
        "subfield": (t.get("subfield") or {}).get("display_name"),
        "field": (t.get("field") or {}).get("display_name"),
        "domain": (t.get("domain") or {}).get("display_name"),
    }


def keywords(work: dict[str, Any]) -> list[str]:
    return [k.get("display_name", "").lower() for k in (work.get("keywords") or []) if k.get("display_name")]


def to_paper_preview(work: dict[str, Any]) -> dict[str, Any]:
    """Matches packages/types PaperPreview."""
    return {
        "openalexId": short_id(work.get("id")),
        "title": work.get("title") or work.get("display_name") or "Untitled",
        "authors": authors(work),
        "year": work.get("publication_year"),
        "venue": venue(work),
        "citedByCount": work.get("cited_by_count") or 0,
        "hasPdf": has_pdf(work),
    }


def to_object_content(work: dict[str, Any]) -> dict[str, Any]:
    """What a PAPER canvas object stores about its work.

    The abstract matters beyond display: it is the text the viewer renders, so
    it is what the user can select to make excerpts, notes and explanations.
    """
    hier = hierarchy(work)
    return {
        "openalexId": short_id(work.get("id")),
        "doi": work.get("doi"),
        "abstract": abstract_text(work.get("abstract_inverted_index")),
        "year": work.get("publication_year"),
        "venue": venue(work),
        "authors": authors(work),
        "citedByCount": work.get("cited_by_count") or 0,
        "type": work.get("type"),
        "topics": [t.get("display_name") for t in (work.get("topics") or []) if t.get("display_name")],
        "keywords": keywords(work),
        "field": hier.get("field"),
        "subfield": hier.get("subfield"),
        "pdfUrl": pdf_url(work),
        "hasPdf": has_pdf(work),
        "referencedCount": len(work.get("referenced_works") or []),
    }
