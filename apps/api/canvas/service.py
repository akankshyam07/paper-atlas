"""Canvas graph CRUD. Domain logic lives here, not in routes. All mutations are
transactional and preserve provenance (PRD §6, §11).
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.entities import Canvas, CanvasObject, ObjectEdge


def ensure_canvas(db: Session, canvas_id: uuid.UUID, *, title: str = "Untitled canvas") -> Canvas:
    """Get-or-create a canvas by client-supplied id.

    The frontend mints canvas ids locally (localStorage-first board state), so an
    object or edge can arrive before the canvas row exists. Both mutation paths
    route through here, so the row is created once, at the choke point.
    """
    canvas = db.get(Canvas, canvas_id)
    if canvas is None:
        canvas = Canvas(id=canvas_id, title=title)
        db.add(canvas)
        db.flush()
    return canvas


def create_canvas(db: Session, *, title: str, user_id: uuid.UUID | None = None) -> Canvas:
    canvas = Canvas(title=title, user_id=user_id)
    db.add(canvas)
    db.commit()
    db.refresh(canvas)
    return canvas


def create_object(
    db: Session,
    *,
    canvas_id: uuid.UUID,
    object_type: str,
    title: str | None = None,
    content: dict | None = None,
    source_entity_id: uuid.UUID | None = None,
    x: float = 0.0,
    y: float = 0.0,
    created_by: str = "USER",
) -> CanvasObject:
    ensure_canvas(db, canvas_id)
    obj = CanvasObject(
        canvas_id=canvas_id,
        object_type=object_type,
        title=title,
        content=content or {},
        source_entity_id=source_entity_id,
        x=x,
        y=y,
        created_by=created_by,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    _index(obj)
    return obj


def _index(obj: CanvasObject) -> None:
    """Mirror the object into the SearchProvider so canvas search can find it.
    Best-effort: search being down must never fail a canvas mutation."""
    from providers.registry import get_search

    content = obj.content or {}
    try:
        get_search().index(str(obj.id), {
            "canvas_id": str(obj.canvas_id),
            "object_id": str(obj.id),
            "object_type": obj.object_type,
            "title": obj.title or "",
            "text": str(content.get("abstract") or content.get("text") or ""),
            "openalex_id": content.get("openalexId"),
            "year": content.get("year"),
        })
    except Exception:
        pass


def create_edge(
    db: Session,
    *,
    canvas_id: uuid.UUID,
    source_object_id: uuid.UUID,
    target_object_id: uuid.UUID,
    edge_type: str,
    provenance: str = "USER",
) -> ObjectEdge:
    ensure_canvas(db, canvas_id)
    # Guard: both endpoints must exist on this canvas (edge belongs to a canvas).
    objs = db.execute(
        select(CanvasObject.id).where(
            CanvasObject.canvas_id == canvas_id,
            CanvasObject.id.in_([source_object_id, target_object_id]),
        )
    ).scalars().all()
    if set(objs) != {source_object_id, target_object_id}:
        raise ValueError("both objects must exist on the same canvas")

    edge = ObjectEdge(
        canvas_id=canvas_id,
        source_object_id=source_object_id,
        target_object_id=target_object_id,
        edge_type=edge_type,
        provenance=provenance,
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)
    return edge


def get_neighbors(db: Session, object_id: uuid.UUID, depth: int = 1) -> list[CanvasObject]:
    """1-hop (or more) graph neighbors. Used by RAG retrieval (PRD §15)."""
    seen: set[uuid.UUID] = {object_id}
    frontier: set[uuid.UUID] = {object_id}
    for _ in range(depth):
        edges = db.execute(
            select(ObjectEdge).where(
                (ObjectEdge.source_object_id.in_(frontier))
                | (ObjectEdge.target_object_id.in_(frontier))
            )
        ).scalars().all()
        nxt: set[uuid.UUID] = set()
        for e in edges:
            nxt.update({e.source_object_id, e.target_object_id})
        frontier = nxt - seen
        seen |= nxt
        if not frontier:
            break
    seen.discard(object_id)
    if not seen:
        return []
    return db.execute(select(CanvasObject).where(CanvasObject.id.in_(seen))).scalars().all()


def ingest_file(
    db: Session,
    *,
    canvas_id: uuid.UUID,
    data: bytes,
    filename: str,
    origin: str = "upload",
    x: float = 0.0,
    y: float = 0.0,
    storage_key: str | None = None,
) -> CanvasObject:
    """The one ingestion path for uploaded files.

    Dedupes to a canonical source entity, then places a PDF object. Text
    extraction and DOI matching against OpenAlex are a follow-up; this
    dedupe-and-place contract is what callers depend on.
    """
    from canvas.dedup import resolve_or_create_source_entity

    entity = resolve_or_create_source_entity(
        db, source_type="UPLOADED_FILE", external_id=None, title=filename,
        metadata={"filename": filename, "size_bytes": len(data), "origin": origin,
                  "storage_key": storage_key},
    )
    return create_object(
        db, canvas_id=canvas_id, object_type="PDF", title=filename,
        content={"filename": filename, "origin": origin, "sizeBytes": len(data),
                 "storageKey": storage_key,
                 "pdfUrl": f"/api/files/{storage_key}" if storage_key else None},
        source_entity_id=entity.id, x=x, y=y,
    )


def get_object(db: Session, object_id: uuid.UUID) -> CanvasObject | None:
    return db.get(CanvasObject, object_id)


def canvas_openalex_ids(db: Session, canvas_id: uuid.UUID) -> set[str]:
    """Every OpenAlex id already on this canvas — the recommender excludes them
    so suggestions move the graph forward instead of looping (PRD §13.5)."""
    rows = db.execute(
        select(CanvasObject.content).where(
            CanvasObject.canvas_id == canvas_id,
            CanvasObject.deleted_at.is_(None),
        )
    ).scalars().all()
    ids: set[str] = set()
    for content in rows:
        oid = (content or {}).get("openalexId")
        if oid:
            ids.add(oid)
    return ids


def cache_openalex_work(db: Session, *, source_entity_id: uuid.UUID, work: dict) -> None:
    """Persist a touched OpenAlex work (PRD §12: cache only what the user opens,
    never mirror the corpus). Upsert so reopening a paper refreshes counts."""
    from openalex import mapping
    from models.entities import OpenAlexWorkCache

    openalex_id = mapping.short_id(work.get("id"))
    if not openalex_id:
        return
    row = db.get(OpenAlexWorkCache, source_entity_id)
    if row is None:
        row = OpenAlexWorkCache(source_entity_id=source_entity_id, openalex_id=openalex_id)
        db.add(row)
    row.openalex_id = openalex_id
    row.doi = work.get("doi")
    row.title = work.get("title") or work.get("display_name")
    row.abstract_text = mapping.abstract_text(work.get("abstract_inverted_index"))
    row.publication_date = str(work.get("publication_year") or "") or None
    row.authors = {"list": mapping.authors(work)}
    row.primary_topic = mapping.hierarchy(work)
    row.topics = {"list": [t.get("display_name") for t in (work.get("topics") or [])]}
    row.keywords = {"list": mapping.keywords(work)}
    row.referenced_work_ids = {"list": work.get("referenced_works") or []}
    row.related_work_ids = {"list": work.get("related_works") or []}
    row.cited_by_count = work.get("cited_by_count") or 0
    row.open_access = work.get("open_access") or {}
    row.content_urls = {"pdf": mapping.pdf_url(work)}
    db.commit()


def suppress_candidate(db: Session, *, canvas_id: uuid.UUID, mode: str, openalex_id: str) -> None:
    from models.entities import Suppression

    ensure_canvas(db, canvas_id)
    exists = db.execute(
        select(Suppression.id).where(
            Suppression.canvas_id == canvas_id,
            Suppression.mode == mode,
            Suppression.openalex_id == openalex_id,
        )
    ).first()
    if exists:
        return
    db.add(Suppression(canvas_id=canvas_id, mode=mode, openalex_id=openalex_id))
    db.commit()


def suppressed_ids(db: Session, canvas_id: uuid.UUID, mode: str) -> set[str]:
    from models.entities import Suppression

    rows = db.execute(
        select(Suppression.openalex_id).where(
            Suppression.canvas_id == canvas_id, Suppression.mode == mode
        )
    ).scalars().all()
    return set(rows)


def list_objects(db: Session, canvas_id: uuid.UUID, *, limit: int = 50) -> list[CanvasObject]:
    return db.execute(
        select(CanvasObject)
        .where(CanvasObject.canvas_id == canvas_id, CanvasObject.deleted_at.is_(None))
        .order_by(CanvasObject.created_at.desc())
        .limit(limit)
    ).scalars().all()
