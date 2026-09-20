"""backend-ai lane. Real OpenAlex search, Broader/Deeper recommendations, and
AI explanation. Endpoints stay thin; logic lives in recommend.py / explain.py.

The frontend addresses objects by canvas object id, so these routes resolve the
OpenAlex id from the stored object rather than asking the client for it — the
API contract stays unchanged.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from canvas import service
from db.session import get_db
from intel import explain as explain_mod
from intel.recommend import recommend as run_recommend
from openalex import mapping
from providers.registry import get_research_data
from schemas import (
    SearchResponse, PaperPreview,
    RecommendRequest, RecommendResponse, Recommendation,
    ExplainRequest, ExplainResponse, CanvasObject, ObjectEdge,
)

router = APIRouter()


def _as_uuid(value: str | None) -> uuid.UUID | None:
    try:
        return uuid.UUID(value) if value else None
    except (ValueError, TypeError, AttributeError):
        return None


def _resolve_openalex_id(db: Session, object_id: str | None) -> tuple[str | None, uuid.UUID | None]:
    """Canvas object id -> the OpenAlex id stored on it (if it is a paper)."""
    oid = _as_uuid(object_id)
    if oid is None:
        # The client may already be passing a raw OpenAlex id.
        if object_id and object_id.upper().startswith("W"):
            return object_id, None
        return None, None
    obj = service.get_object(db, oid)
    if obj is None:
        return None, None
    content = obj.content or {}
    return content.get("openalexId"), obj.canvas_id


@router.get("/search", response_model=SearchResponse)
def search(q: str, mode: str = "keyword", limit: int = 10) -> SearchResponse:
    works = get_research_data().search_works(q, mode=mode, per_page=limit)
    return SearchResponse(results=[PaperPreview(**mapping.to_paper_preview(w)) for w in works])


@router.get("/citations", response_model=SearchResponse)
def citations(objectId: str, direction: str = "out", limit: int = 25, db: Session = Depends(get_db)) -> SearchResponse:
    """Papers this work cites (direction=out, from referenced_works) or papers
    citing it (direction=in, via the cites: filter). Backs the References,
    Cited by and Related actions (PRD §25).
    """
    openalex_id, _ = _resolve_openalex_id(db, objectId)
    if not openalex_id:
        return SearchResponse(results=[])

    provider = get_research_data()
    if direction == "related":
        work = provider.get_work(openalex_id)
        related = (work.get("related_works") or [])[:limit]
        works = provider.get_works_by_ids(related) if related else []
    else:
        works = provider.get_citations(openalex_id, direction=direction)[:limit]

    return SearchResponse(results=[PaperPreview(**mapping.to_paper_preview(w)) for w in works])


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest, db: Session = Depends(get_db)) -> RecommendResponse:
    openalex_id, canvas_id = _resolve_openalex_id(db, req.objectId)
    if not openalex_id:
        return RecommendResponse(recommendations=[])

    # Suppress anything already on the canvas (loop avoidance, PRD §13.5).
    exclude = service.canvas_openalex_ids(db, canvas_id) if canvas_id else set()

    recs = run_recommend(
        openalex_id=openalex_id,
        mode=req.mode,
        offset=req.offset,
        exclude_ids=exclude,
    )
    return RecommendResponse(recommendations=[
        Recommendation(
            paper=PaperPreview(**r["paper"]),
            mode=r["mode"],
            relationshipLabel=r["relationshipLabel"],
            reason=r["reason"],
            score=r["score"],
        )
        for r in recs
    ])


@router.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest, db: Session = Depends(get_db)) -> ExplainResponse:
    """A direct user action, so the artifact is created immediately — an explicit
    click is approval for its own derived object (PRD §16)."""
    openalex_id, _ = _resolve_openalex_id(db, req.objectId)
    work = get_research_data().get_work(openalex_id) if openalex_id else {}

    text = explain_mod.explain(text=req.text, work=work or None)
    title = (work.get("title") or work.get("display_name")) if work else None
    title = title or "Selection"

    canvas_uuid = _as_uuid(req.canvasId)
    note = service.create_object(
        db,
        canvas_id=canvas_uuid,
        object_type="AI_SUMMARY",
        title=f"Explanation: {title}"[:200],
        content={
            "text": text,
            # Provenance (PRD §2.2): what this artifact was derived from.
            "sourceOpenalexId": openalex_id,
            "sourceObjectId": req.objectId,
            "sourceText": (req.text or "")[:2000] or None,
        },
        created_by="AI",
    )

    edge_out = ObjectEdge(
        id=str(uuid.uuid4()), canvasId=req.canvasId,
        sourceObjectId=req.objectId or str(note.id), targetObjectId=str(note.id),
        edgeType="EXPLAINS", provenance="AI",
    )
    source_uuid = _as_uuid(req.objectId)
    if source_uuid and canvas_uuid:
        try:
            edge = service.create_edge(
                db, canvas_id=canvas_uuid, source_object_id=source_uuid,
                target_object_id=note.id, edge_type="EXPLAINS", provenance="AI",
            )
            edge_out = ObjectEdge(
                id=str(edge.id), canvasId=str(edge.canvas_id),
                sourceObjectId=str(edge.source_object_id),
                targetObjectId=str(edge.target_object_id),
                edgeType=edge.edge_type, provenance=edge.provenance,
            )
        except ValueError:
            pass  # source isn't a persisted object; the note still holds provenance

    return ExplainResponse(
        object=CanvasObject(
            id=str(note.id), canvasId=str(note.canvas_id), objectType=note.object_type,
            sourceEntityId=None, title=note.title, content=note.content,
            x=note.x, y=note.y, createdBy=note.created_by,
        ),
        edge=edge_out,
    )
