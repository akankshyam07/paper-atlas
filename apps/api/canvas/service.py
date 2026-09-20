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
    return obj


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


def ingest_file(db: Session, *, canvas_id: uuid.UUID, data: bytes, filename: str) -> CanvasObject:
    """Seam for uploads AND Dropbox import (BE #2 calls this). Dedups to a
    source entity, then places a PAPER/PDF object. Parsing/DOI extraction is a
    follow-up; the dedup + placement contract is stable.
    """
    from canvas.dedup import resolve_or_create_source_entity

    entity = resolve_or_create_source_entity(
        db, source_type="UPLOADED_FILE", external_id=None, title=filename,
        metadata={"filename": filename, "size_bytes": len(data)},
    )
    return create_object(
        db, canvas_id=canvas_id, object_type="PAPER", title=filename,
        content={"filename": filename}, source_entity_id=entity.id,
    )
