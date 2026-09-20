"""Broader / Deeper recommendations (PRD §13).

The product constraint: these are NOT two labels over one similarity search.
They use different candidate pools and different scoring, so the graph actually
moves in a direction.

  BROADER -> toward general framing, prerequisites, foundational/survey work.
             Pools: what P cites, highly-cited work in P's topic, reviews.
             Rewards: older, heavily cited, survey/review type, general title.

  DEEPER  -> toward a narrower mechanism, application, or subproblem.
             Pools: work citing P, recent work in P's topic, semantic neighbours.
             Rewards: newer, high keyword overlap, specific/narrow title.

Scoring is deterministic first (PRD §13.3); an LLM may reorder the top few and
write the reason line, but never discovers the candidate set.
"""
from __future__ import annotations

import math
import re
from datetime import date
from typing import Any

from openalex import mapping
from openalex.client import OpenAlexProvider

RECOMMENDATION_COUNT = 3
CURRENT_YEAR = date.today().year
# Topic-pool candidates below this shared-substance score are dropped.
MIN_TOPIC_RELEVANCE = 0.06

_SURVEY_HINTS = ("survey", "review", "overview", "introduction to", "tutorial", "a primer", "foundations")
_SPECIFIC_HINTS = ("case study", "application", "towards", "improving", "fine-tun", "ablation", "benchmark", "on the")

# OpenAlex tags works with field-level ancestor keywords ("computer science",
# "mathematics"). Two papers sharing only these have nothing in common, so they
# are excluded from overlap — otherwise famous off-topic work scores highly.
_GENERIC_KEYWORDS = {
    "computer science", "artificial intelligence", "mathematics", "psychology",
    "philosophy", "engineering", "biology", "physics", "medicine", "economics",
    "statistics", "epistemology", "sociology", "political science", "chemistry",
    "geology", "business", "art", "history", "materials science", "geography",
    "linguistics", "mathematical analysis", "pure mathematics", "law",
    "theoretical computer science", "data science", "cognitive science",
}


def _substantive_keywords(work: dict[str, Any]) -> list[str]:
    return [k for k in mapping.keywords(work) if k not in _GENERIC_KEYWORDS]


def _title_of(w: dict[str, Any]) -> str:
    return (w.get("title") or w.get("display_name") or "").lower()


def norm_title(title: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def _looks_like_survey(w: dict[str, Any]) -> bool:
    t = _title_of(w)
    if any(h in t for h in _SURVEY_HINTS):
        return True
    return (w.get("type") or "") in {"review", "book", "book-chapter"}


def _looks_specific(w: dict[str, Any]) -> bool:
    return any(h in _title_of(w) for h in _SPECIFIC_HINTS)


def _overlap(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _title_tokens(w: dict[str, Any]) -> list[str]:
    return [t for t in re.findall(r"[a-z]{4,}", _title_of(w))]


def _log_citations(w: dict[str, Any]) -> float:
    return math.log10(1 + (w.get("cited_by_count") or 0))


def _relevance(candidate: dict[str, Any], source: dict[str, Any]) -> float:
    """Shared-substance signal for topic-pool candidates.

    Deliberately excludes topic overlap: the pool is *filtered* by topic, so
    every candidate matches by construction and the signal is tautological.
    Only shared vocabulary distinguishes a genuinely related paper from a
    famous unrelated one in the same broad field.
    """
    return (
        1.5 * _overlap(_substantive_keywords(source), _substantive_keywords(candidate))
        + 1.0 * _overlap(_title_tokens(source), _title_tokens(candidate))
    )


def _score(
    candidate: dict[str, Any],
    source: dict[str, Any],
    mode: str,
    origin: str = "topic",
) -> float:
    """Deterministic feature score. Same features, opposite weights per mode."""
    src_topics = mapping.topic_ids(source)
    src_keywords = _substantive_keywords(source)
    cand_topics = mapping.topic_ids(candidate)
    cand_keywords = _substantive_keywords(candidate)

    topic_overlap = _overlap(src_topics, cand_topics)
    keyword_overlap = _overlap(src_keywords, cand_keywords)
    title_overlap = _overlap(_title_tokens(source), _title_tokens(candidate))
    citations = _log_citations(candidate)

    src_year = source.get("publication_year") or 0
    cand_year = candidate.get("publication_year") or 0
    year_delta = (cand_year - src_year) if (src_year and cand_year) else 0

    score = 0.0
    # Relevance: a candidate must still be about the same thing.
    score += 2.0 * topic_overlap + 1.5 * keyword_overlap + 0.5 * title_overlap

    # Pool prior: a direct citation link is hard evidence of relatedness; a
    # top-cited work merely sharing a broad topic is not. Without this, famous
    # but unrelated papers dominate the topic pool.
    score += {"citation": 1.2, "semantic": 0.5, "topic": 0.0}.get(origin, 0.0)

    if mode == "broader":
        # Older and more cited = more foundational.
        score += 0.6 * citations
        score += 0.35 * min(max(-year_delta, 0), 20) / 4.0
        if _looks_like_survey(candidate):
            score += 1.6
        if _looks_specific(candidate):
            score -= 0.6
        # Generality proxy: fewer keywords = broader framing.
        score += 0.4 * max(0, 8 - len(cand_keywords)) / 8.0
    else:  # deeper
        # Newer and more specific = further down the rabbit hole.
        score += 0.30 * min(max(year_delta, 0), 12) / 3.0
        score += 1.4 * keyword_overlap  # specialisation shares vocabulary
        if _looks_specific(candidate):
            score += 0.9
        if _looks_like_survey(candidate):
            score -= 1.4
        # Some citation signal, but far less than broader — recency matters more.
        score += 0.18 * citations
        score += 0.4 * min(len(cand_keywords), 10) / 10.0

    return score


def _candidates(source: dict[str, Any], mode: str, client: OpenAlexProvider) -> list[tuple[dict[str, Any], str]]:
    """Different pools per direction — this is what makes the modes distinct."""
    source_id = mapping.short_id(source.get("id"))
    hier = mapping.hierarchy(source)
    topic_id = hier.get("topic_id")
    year = source.get("publication_year")
    pool: list[tuple[dict[str, Any], str]] = []

    def add(works: list[dict[str, Any]], origin: str) -> None:
        pool.extend((w, origin) for w in works)

    if mode == "broader":
        # 1. What this paper builds on — its own references are its prerequisites.
        add(client.get_citations(source_id, direction="out"), "citation")
        # 2. The heavy hitters of its topic.
        if topic_id:
            add(client.works_in_topic(topic_id, sort="cited_by_count:desc", per_page=25), "topic")
            # 3. Explicit reviews/surveys in the topic.
            add(client.works_in_topic(topic_id, sort="cited_by_count:desc", per_page=10,
                                      extra_filter="type:review"), "topic")
    else:
        # 1. Work that cites this paper — builds on and specialises it.
        add(client.get_citations(source_id, direction="in"), "citation")
        # 2. Recent work in the same topic.
        if topic_id:
            recent_from = (year or 2015) if year else 2018
            add(client.works_in_topic(
                topic_id, sort="publication_date:desc", per_page=25,
                extra_filter=f"from_publication_date:{max(recent_from, 2015)}-01-01",
            ), "topic")
        # 3. Semantic neighbours of the abstract — narrower phrasing of the idea.
        abstract = mapping.abstract_text(source.get("abstract_inverted_index"))
        if abstract:
            add(client.search_works(abstract[:1200], mode="semantic", per_page=15), "semantic")

    return pool


def recommend(
    *,
    openalex_id: str,
    mode: str,
    offset: int = 0,
    exclude_ids: set[str] | None = None,
    exclude_titles: set[str] | None = None,
    client: OpenAlexProvider | None = None,
    count: int = RECOMMENDATION_COUNT,
) -> list[dict[str, Any]]:
    """Return ranked candidates as {paper, mode, relationshipLabel, reason, score}."""
    client = client or OpenAlexProvider()
    exclude = {mapping.short_id(i) for i in (exclude_ids or set())}
    source = client.get_work(openalex_id)
    if not source:
        return []
    source_id = mapping.short_id(source.get("id"))
    exclude.add(source_id)
    # Title exclusion covers OpenAlex's duplicate records, where one paper
    # exists under several ids and would otherwise be suggested repeatedly.
    seen_titles = set(exclude_titles or set())
    seen_titles.add(norm_title(source.get("title") or source.get("display_name")))

    # Dedupe the pool and drop anything already on the canvas or rejected
    # (loop suppression, PRD §13.5).
    seen: set[str] = set()
    scored: list[tuple[float, dict[str, Any]]] = []
    for cand, origin in _candidates(source, mode, client):
        cid = mapping.short_id(cand.get("id"))
        if not cid or cid in seen or cid in exclude:
            continue
        seen.add(cid)
        title = cand.get("title") or cand.get("display_name")
        if not title:
            continue
        nt = norm_title(title)
        if not nt or nt in seen_titles:
            continue
        seen_titles.add(nt)
        # Relevance floor: topic-pool candidates must share real substance, not
        # just a broad topic label. Citation-linked work is exempt — the link
        # itself is the evidence.
        if origin == "topic" and _relevance(cand, source) < MIN_TOPIC_RELEVANCE:
            continue
        scored.append((_score(cand, source, mode, origin), cand))

    scored.sort(key=lambda s: s[0], reverse=True)
    window = scored[offset: offset + count]

    out: list[dict[str, Any]] = []
    for score, cand in window:
        out.append({
            "paper": mapping.to_paper_preview(cand),
            "mode": mode,
            "relationshipLabel": _label(cand, source, mode),
            "reason": _reason(cand, source, mode),
            "score": round(score, 3),
        })
    return out


def _label(cand: dict[str, Any], source: dict[str, Any], mode: str) -> str:
    if mode == "broader":
        if _looks_like_survey(cand):
            return "survey / review"
        if (cand.get("cited_by_count") or 0) > (source.get("cited_by_count") or 0):
            return "foundational work"
        return "broader context"
    if _looks_specific(cand):
        return "specific application"
    if (cand.get("publication_year") or 0) > (source.get("publication_year") or 0):
        return "builds on this"
    return "narrower focus"


def _reason(cand: dict[str, Any], source: dict[str, Any], mode: str) -> str:
    """One deterministic line. An LLM reranker may replace this later."""
    bits: list[str] = []
    cy, sy = cand.get("publication_year"), source.get("publication_year")
    cites = cand.get("cited_by_count") or 0
    if mode == "broader":
        if _looks_like_survey(cand):
            bits.append("survey-level treatment of the area")
        if cites:
            bits.append(f"{cites:,} citations")
        if cy and sy and cy < sy:
            bits.append(f"{sy - cy}y earlier")
    else:
        if cy and sy and cy > sy:
            bits.append(f"{cy - sy}y later, builds on it")
        elif cy:
            bits.append(f"published {cy}")
        shared = set(_substantive_keywords(source)) & set(_substantive_keywords(cand))
        if shared:
            bits.append("shares " + ", ".join(sorted(shared)[:2]))
    return "; ".join(bits) or ("broader framing" if mode == "broader" else "more specific")


# ---- Supporting / Contradicting (PRD §13) ----
# Deterministic retrieval first: both draw on work citing the paper plus
# semantic neighbours. An LLM then classifies the stance, because agreement and
# disagreement are not visible in metadata — but it only labels a small
# candidate set, it never discovers one.

_STANCE_LABELS = ["SUPPORTING", "CONTRADICTING", "NEITHER"]


def stance_candidates(
    *, openalex_id: str, stance: str, limit: int = 3,
    exclude_ids: set[str] | None = None, client: OpenAlexProvider | None = None,
) -> list[dict[str, Any]]:
    from providers.registry import get_llm

    client = client or OpenAlexProvider()
    exclude = {mapping.short_id(i) for i in (exclude_ids or set())}
    source = client.get_work(openalex_id)
    if not source:
        return []
    exclude.add(mapping.short_id(source.get("id")))

    pool: list[dict[str, Any]] = list(client.get_citations(openalex_id, direction="in"))
    abstract = mapping.abstract_text(source.get("abstract_inverted_index"))
    if abstract:
        pool += client.search_works(abstract[:1000], mode="semantic", per_page=10)

    seen: set[str] = set()
    ranked: list[tuple[float, dict[str, Any]]] = []
    for cand in pool:
        cid = mapping.short_id(cand.get("id"))
        if not cid or cid in seen or cid in exclude:
            continue
        seen.add(cid)
        ranked.append((_relevance(cand, source), cand))
    ranked.sort(key=lambda r: r[0], reverse=True)

    want = stance.upper()
    llm = get_llm()
    src_title = source.get("title") or source.get("display_name") or ""
    out: list[dict[str, Any]] = []
    # Classify only the strongest few, so cost stays bounded.
    for _, cand in ranked[:8]:
        if len(out) >= limit:
            break
        cand_title = cand.get("title") or cand.get("display_name") or ""
        verdict = llm.classify(
            f"Paper A: {src_title}\nPaper B: {cand_title}\n\n"
            "Does B support A's claims, contradict them, or neither?",
            _STANCE_LABELS,
        )
        # A stub classifier always returns the first label, so without a real
        # LLM this degrades to relevance order rather than inventing a stance.
        if verdict != want and llm.__class__.__name__ != "StubLLM":
            continue
        out.append({
            "paper": mapping.to_paper_preview(cand),
            "mode": "deeper",
            "relationshipLabel": want.lower(),
            "reason": f"cites this work; classified {verdict.lower()}",
            "score": 0.0,
        })
    return out


# ---- Foundational / Recent discovery (PRD §14) ----

def discover(*, query: str, kind: str = "foundational", limit: int = 5,
             client: OpenAlexProvider | None = None) -> list[dict[str, Any]]:
    """Blended ranking, not raw citation count (PRD §14)."""
    client = client or OpenAlexProvider()
    if kind == "recent":
        works = client.search_works(query, per_page=40)
        scored = []
        for w in works:
            year = w.get("publication_year") or 0
            if year < CURRENT_YEAR - 2:
                continue
            # Recency plus citation velocity, so a brand-new paper is not
            # punished for having few total citations.
            velocity = (w.get("cited_by_count") or 0) / max(1, CURRENT_YEAR - year + 1)
            scored.append((0.6 * (year - (CURRENT_YEAR - 3)) + 0.4 * math.log10(1 + velocity), w))
    else:
        works = client.search_works(query, per_page=40)
        scored = []
        for w in works:
            cites = math.log10(1 + (w.get("cited_by_count") or 0))
            age = max(0, CURRENT_YEAR - (w.get("publication_year") or CURRENT_YEAR))
            survey = 1.2 if _looks_like_survey(w) else 0.0
            # Influence and staying power, with a nod to surveys — not citations alone.
            scored.append((cites + survey + min(age, 25) / 25.0, w))

    scored.sort(key=lambda s: s[0], reverse=True)
    return [{
        "paper": mapping.to_paper_preview(w),
        "mode": "broader" if kind == "foundational" else "deeper",
        "relationshipLabel": kind,
        "reason": (f"{w.get('cited_by_count', 0):,} citations"
                   + (f" · {w.get('publication_year')}" if w.get("publication_year") else "")),
        "score": round(score, 3),
    } for score, w in scored[:limit]]
