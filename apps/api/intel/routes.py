"""backend-ai lane. Real OpenAlex search, Broader/Deeper recommendations, and
AI explanation. Endpoints stay thin; logic lives in recommend.py / explain.py.

The frontend addresses objects by canvas object id, so these routes resolve the
OpenAlex id from the stored object rather than asking the client for it — the
API contract stays unchanged.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from canvas import service
from db.session import get_db
from intel import explain as explain_mod
from intel.recommend import discover as run_discover
from intel.recommend import recommend as run_recommend
from intel.recommend import stance_candidates
from openalex import mapping
from providers.registry import get_research_data
from schemas import (
    StanceRequest, ChatRequest, ChatResponse,
    ThreadRequest, ThreadResponse, ThreadMessages, Message,
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
    if canvas_id:
        exclude |= service.suppressed_ids(db, canvas_id, req.mode)

    recs = run_recommend(
        openalex_id=openalex_id,
        mode=req.mode,
        offset=req.offset,
        exclude_ids=exclude,
        exclude_titles=service.canvas_titles(db, canvas_id) if canvas_id else set(),
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


@router.post("/stance", response_model=RecommendResponse)
def stance(req: StanceRequest, db: Session = Depends(get_db)) -> RecommendResponse:
    """Supporting or contradicting work for a paper (PRD §13)."""
    openalex_id, canvas_id = _resolve_openalex_id(db, req.objectId)
    if not openalex_id:
        return RecommendResponse(recommendations=[])
    exclude = service.canvas_openalex_ids(db, canvas_id) if canvas_id else set()
    recs = stance_candidates(openalex_id=openalex_id, stance=req.stance, exclude_ids=exclude)
    return RecommendResponse(recommendations=[Recommendation(
        paper=PaperPreview(**r["paper"]), mode=r["mode"],
        relationshipLabel=r["relationshipLabel"], reason=r["reason"], score=r["score"],
    ) for r in recs])


@router.get("/discover", response_model=RecommendResponse)
def discover_route(q: str, kind: str = "foundational", limit: int = 5) -> RecommendResponse:
    """Foundational or recent work for a topic (PRD §14)."""
    recs = run_discover(query=q, kind=kind, limit=limit)
    return RecommendResponse(recommendations=[Recommendation(
        paper=PaperPreview(**r["paper"]), mode=r["mode"],
        relationshipLabel=r["relationshipLabel"], reason=r["reason"], score=r["score"],
    ) for r in recs])


@router.get("/topics")
def topics(level: str = "field", parent: str | None = None, q: str | None = None) -> dict:
    """Interest taxonomy for onboarding (PRD §12 topic hierarchy).

    Without a query this walks the tree one level at a time — fields, then the
    subfields of a field, then the topics of a subfield — so the picker expands
    in place rather than dumping hundreds of tags at once. With a query it
    searches topics directly, for people who already know what they want.
    """
    provider = get_research_data()
    if q:
        rows = provider.search_topics(q)
        return {"level": "topic", "items": [{
            "id": mapping.short_id(r.get("id")),
            "name": r.get("display_name"),
            "worksCount": r.get("works_count") or 0,
            "parent": ((r.get("subfield") or {}).get("display_name")
                       or (r.get("field") or {}).get("display_name")),
        } for r in rows]}

    rows = provider.taxonomy(level, mapping.short_id(parent) if parent else None)
    return {"level": level, "items": [{
        "id": mapping.short_id(r.get("id")),
        "name": r.get("display_name"),
        "worksCount": r.get("works_count") or 0,
        "parent": None,
    } for r in rows]}


@router.get("/random", response_model=SearchResponse)
def random_work(topic: str | None = None, seed: int | None = None) -> SearchResponse:
    """A random well-cited paper, optionally within a topic.

    OpenAlex has no random endpoint, so this pages into a filtered, sorted
    result set at a random offset — cheap, and it keeps returning real work
    rather than obscure noise.
    """
    import random as _r

    rng = _r.Random(seed)
    provider = get_research_data()
    query = topic or rng.choice([
        "machine learning", "neuroscience", "climate", "quantum computing",
        "genomics", "economics", "materials science", "epidemiology",
    ])
    # A deep page can fall past the end of a result set, and OpenAlex
    # occasionally times out, so try a few shallower attempts before giving up
    # rather than handing back an empty result.
    for attempt in range(4):
        page = rng.randint(1, 5 - attempt)
        works = provider.search_works(query, per_page=25, page=page)
        if works:
            return SearchResponse(results=[PaperPreview(**mapping.to_paper_preview(rng.choice(works)))])
    return SearchResponse(results=[])


@router.post("/threads", response_model=ThreadResponse)
def create_thread(req: ThreadRequest, db: Session = Depends(get_db)) -> ThreadResponse:
    """Start a thread anchored on a node (PRD §17). The thread becomes its own
    object on the board and the source node is its initial pinned context."""
    from models.entities import ChatThread

    canvas_id = _as_uuid(req.canvasId)
    anchor = _as_uuid(req.objectId)
    src = service.get_object(db, anchor) if anchor else None
    title = req.title or (f"About: {src.title}" if src and src.title else "Thread")

    node = service.create_object(
        db, canvas_id=canvas_id, object_type="THREAD", title=title[:200],
        content={"anchorObjectId": req.objectId, "messageCount": 0}, x=req.x, y=req.y,
    )
    thread = ChatThread(canvas_id=canvas_id, canvas_object_id=node.id, title=title[:200])
    db.add(thread)
    db.commit()
    db.refresh(thread)

    if anchor:
        try:
            service.create_edge(db, canvas_id=canvas_id, source_object_id=anchor,
                                target_object_id=node.id, edge_type="THREAD_CONTEXT")
        except ValueError:
            pass

    return ThreadResponse(
        threadId=str(thread.id),
        object=CanvasObject(
            id=str(node.id), canvasId=str(node.canvas_id), objectType=node.object_type,
            sourceEntityId=None, title=node.title, content=node.content,
            x=node.x, y=node.y, createdBy=node.created_by,
        ),
    )


@router.get("/threads/{thread_id}", response_model=ThreadMessages)
def get_thread(thread_id: str, db: Session = Depends(get_db)) -> ThreadMessages:
    from models.entities import ChatMessage

    rows = db.execute(
        select(ChatMessage).where(ChatMessage.thread_id == uuid.UUID(thread_id))
        .order_by(ChatMessage.created_at)
    ).scalars().all()
    return ThreadMessages(messages=[Message(
        id=str(m.id), role=m.role, content=m.content,
        contextSnapshot=m.context_snapshot or {},
    ) for m in rows])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """Canvas chat. Context follows the PRD §15 retrieval priority: the user's
    selection first, then graph neighbours, then the rest of the canvas."""
    from providers.registry import get_inference_optimizer, get_llm

    parts: list[str] = []
    seen: set[str] = set()

    def add(obj, tag: str) -> None:
        if obj is None or str(obj.id) in seen:
            return
        seen.add(str(obj.id))
        body = (obj.content or {}).get("abstract") or (obj.content or {}).get("text") or ""
        parts.append(f"[{tag}] {obj.title or ''}\n{str(body)[:900]}".strip())

    canvas_uuid = _as_uuid(req.canvasId)
    # 1. explicit selection outranks everything else
    for oid in (req.selectedObjectIds or [])[:6]:
        u = _as_uuid(oid)
        if u:
            add(service.get_object(db, u), "selected")
    # 2. graph neighbours of the selection
    for oid in (req.selectedObjectIds or [])[:2]:
        u = _as_uuid(oid)
        if u:
            for n in service.get_neighbors(db, u, depth=1)[:4]:
                add(n, "linked")
    # 3. semantic retrieval over canvas-local chunks, before falling back to
    #    simply listing objects (PRD §15 retrieval order)
    if canvas_uuid and len(parts) < 4:
        try:
            from retrieval.service import search as retrieve
            for hit in retrieve(db, canvas_uuid, req.message, limit=4):
                key = f"chunk:{hit['id']}"
                if key in seen:
                    continue
                seen.add(key)
                parts.append(f"[retrieved] {hit.get('section_title') or ''}\n{hit['text'][:900]}".strip())
        except Exception:
            pass
    if canvas_uuid and len(parts) < 3:
        for o in service.list_objects(db, canvas_uuid, limit=6):
            add(o, "canvas")

    context = "\n\n---\n\n".join(parts[:8])
    prompt = (f"Canvas context:\n{context}\n\n" if context else "") + f"Question: {req.message}"
    answer = get_llm().complete(
        get_inference_optimizer().optimize(prompt),
        system=("You answer questions about the user's research canvas. Ground every "
                "claim in the provided context. If the context does not answer it, say so."),
    )
    # A thread keeps its turns, and each turn keeps the context that produced
    # it, so an old answer stays reproducible after the graph changes (PRD §17).
    if req.threadId:
        from models.entities import ChatMessage

        tid = _as_uuid(req.threadId)
        if tid:
            snapshot = {"objectIds": [s for s in seen if not s.startswith("chunk:")]}
            db.add(ChatMessage(thread_id=tid, role="user", content=req.message,
                               context_snapshot=snapshot))
            db.add(ChatMessage(thread_id=tid, role="assistant", content=answer,
                               context_snapshot=snapshot))
            db.commit()

    return ChatResponse(reply=answer, contextObjectIds=[s for s in seen if not s.startswith("chunk:")])


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
