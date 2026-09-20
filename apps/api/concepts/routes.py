"""Wikipedia concept linking (PRD §11).

Turns the technical phrases in a paper's text into explorable links, without
turning every noun blue. Candidates come from the work's own OpenAlex keywords
and topics — terms the corpus already considers meaningful — then each is
confirmed against Wikipedia. Nothing is added to the canvas automatically
(PRD §11: clicking previews; adding is explicit).
"""
from __future__ import annotations

import re
from functools import lru_cache

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from canvas import service
from db.session import get_db
from schemas import ConceptSpan, ConceptsResponse, WikiSummary

router = APIRouter()

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
# Wikimedia's robot policy rejects terse agents with a 403. It wants the tool,
# a URL and a contact, so this string is deliberately descriptive.
UA = "Abstract/1.0 (https://github.com/rebeccajacob2008/paper-atlas; research canvas) httpx"

# Field labels OpenAlex attaches to nearly everything — linking them is noise.
TOO_GENERAL = {
    "computer science", "artificial intelligence", "mathematics", "psychology",
    "philosophy", "engineering", "biology", "physics", "medicine", "economics",
    "statistics", "epistemology", "sociology", "political science", "chemistry",
    "linguistics", "geology", "business", "history", "art",
}


@lru_cache(maxsize=2048)
def resolve(term: str) -> dict | None:
    """Confirm a phrase names a real article. Cached — the same concept recurs
    constantly across papers (PRD §11: resolve once, render every occurrence).

    Wikipedia titles are case-sensitive after the first character, and OpenAlex
    keywords arrive lowercased, so "machine learning" has to be tried as
    "Machine_learning" before it resolves.
    """
    slug = term.strip().replace(" ", "_")
    candidates = [slug[:1].upper() + slug[1:], slug, "_".join(w.capitalize() for w in term.split())]
    d = None
    try:
        with httpx.Client(timeout=6.0, follow_redirects=True) as c:
            for cand in dict.fromkeys(candidates):
                r = c.get(WIKI_API + cand, headers={"User-Agent": UA})
                if r.status_code == 200:
                    d = r.json()
                    break
    except httpx.HTTPError:
        return None
    if d is None:
        return None
    if d.get("type") == "disambiguation" or not d.get("extract"):
        return None
    return {
        "title": d.get("title") or term,
        "extract": d.get("extract", "")[:600],
        "url": (d.get("content_urls", {}).get("desktop", {}) or {}).get("page")
        or f"https://en.wikipedia.org/wiki/{slug}",
        "thumbnail": (d.get("thumbnail") or {}).get("source"),
    }


@router.get("/concepts", response_model=ConceptsResponse)
def concepts(objectId: str, limit: int = 12, db: Session = Depends(get_db)) -> ConceptsResponse:
    """Concept spans for an object's text, ranked by specificity."""
    import uuid as _u

    try:
        obj = service.get_object(db, _u.UUID(objectId))
    except (ValueError, AttributeError):
        obj = None
    if obj is None:
        return ConceptsResponse(spans=[])

    content = obj.content or {}
    text = str(content.get("abstract") or content.get("text") or "")
    if not text:
        return ConceptsResponse(spans=[])

    terms = [
        t for t in [*(content.get("keywords") or []), *(content.get("topics") or [])]
        if t and t.lower() not in TOO_GENERAL and len(t) > 3
    ]
    # Longer phrases first: link "machine translation", not "machine".
    terms = sorted({t.lower(): t for t in terms}.values(), key=len, reverse=True)

    spans: list[ConceptSpan] = []
    taken: list[tuple[int, int]] = []
    for term in terms:
        if len(spans) >= limit:
            break
        m = re.search(rf"\b{re.escape(term)}\b", text, re.I)
        if not m:
            continue
        if any(m.start() < e and s < m.end() for s, e in taken):
            continue  # already linked inside another concept
        info = resolve(term)
        if not info:
            continue
        taken.append((m.start(), m.end()))
        spans.append(ConceptSpan(term=text[m.start():m.end()], start=m.start(), end=m.end(),
                                 title=info["title"], url=info["url"]))

    spans.sort(key=lambda s: s.start)
    return ConceptsResponse(spans=spans)


@router.get("/concepts/summary", response_model=WikiSummary)
def summary(title: str) -> WikiSummary:
    """Preview an article without touching the graph (PRD §11)."""
    info = resolve(title)
    if not info:
        return WikiSummary(title=title, extract="No article found.", url="", thumbnail=None)
    return WikiSummary(**info)
