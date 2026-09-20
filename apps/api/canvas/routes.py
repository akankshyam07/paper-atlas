"""backend-data lane. Owns canvas/object/edge persistence.

Routes stay thin: validate, call canvas.service, serialize. Domain logic and
transactions live in service.py.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from canvas import service
from canvas.dedup import resolve_or_create_source_entity
from models.entities import CanvasObject as CanvasObjectModel
from openalex import mapping
from providers.registry import get_research_data
from schemas import (
    SuppressRequest,
    AddObjectRequest, AddObjectResponse,
    AddEdgeRequest, AddEdgeResponse,
    CanvasObject, ObjectEdge,
)

router = APIRouter()


def _obj_out(o: CanvasObjectModel) -> CanvasObject:
    return CanvasObject(
        id=str(o.id),
        canvasId=str(o.canvas_id),
        objectType=o.object_type,
        sourceEntityId=str(o.source_entity_id) if o.source_entity_id else None,
        title=o.title,
        content=o.content or {},
        x=o.x,
        y=o.y,
        createdBy=o.created_by,
    )


class CreateCanvasRequest(BaseModel):
    title: str


class CreateCanvasResponse(BaseModel):
    id: str
    title: str


# NOTE: /canvas is not yet in packages/types (group-locked). Added here because
# objects/edges need a canvas to exist; add the matching type with the group.
@router.post("/canvas", response_model=CreateCanvasResponse)
def create_canvas(req: CreateCanvasRequest, db: Session = Depends(get_db)) -> CreateCanvasResponse:
    c = service.create_canvas(db, title=req.title)
    return CreateCanvasResponse(id=str(c.id), title=c.title)


@router.delete("/canvas/{canvas_id}")
def delete_canvas(canvas_id: str, db: Session = Depends(get_db)) -> dict:
    """Soft delete: the row stays so provenance and any shared links survive."""
    from datetime import datetime, timezone
    from models.entities import Canvas

    canvas = db.get(Canvas, uuid.UUID(canvas_id))
    if canvas is None:
        raise HTTPException(status_code=404, detail="canvas not found")
    canvas.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"deleted": canvas_id}


@router.post("/suppressions")
def suppress(req: SuppressRequest, db: Session = Depends(get_db)) -> dict:
    """Record a rejected recommendation so it is not resurfaced (PRD §13.5).
    Server-side, so a rejection survives a different browser."""
    service.suppress_candidate(db, canvas_id=uuid.UUID(req.canvasId),
                               mode=req.mode, openalex_id=req.openalexId)
    return {"suppressed": req.openalexId}


@router.get("/canvas/{canvas_id}/search")
def search_canvas(canvas_id: str, q: str, db: Session = Depends(get_db)) -> dict:
    """Search within a canvas. Uses the SearchProvider (Elastic when configured)
    and falls back to a title/text match over the canvas's own objects."""
    from providers.registry import get_search

    hits = []
    try:
        hits = get_search().search(q, filters={"canvas_id": canvas_id})
    except Exception:
        hits = []
    if hits:
        return {"results": hits, "source": "search-provider"}

    term = q.lower()
    results = [
        {"id": str(o.id), "title": o.title, "objectType": o.object_type}
        for o in service.list_objects(db, uuid.UUID(canvas_id), limit=200)
        if term in (o.title or "").lower()
        or term in str((o.content or {}).get("abstract") or (o.content or {}).get("text") or "").lower()
    ]
    return {"results": results[:20], "source": "database"}


@router.post("/objects", response_model=AddObjectResponse)
def add_object(req: AddObjectRequest, db: Session = Depends(get_db)) -> AddObjectResponse:
    source_entity_id = None
    content = dict(req.content or {})
    title = req.title

    if req.openalexId:
        entity = resolve_or_create_source_entity(
            db, source_type="OPENALEX_WORK", external_id=req.openalexId, title=req.title,
        )
        source_entity_id = entity.id

        # Fetch the work once, on add, so the object carries its abstract and
        # metadata. The abstract is what the viewer renders, and therefore what
        # the user can select to create excerpts, notes and explanations.
        work = get_research_data().get_work(req.openalexId)
        if work:
            content = {**mapping.to_object_content(work), **content}
            title = title or work.get("title") or work.get("display_name")
            if not entity.title:
                entity.title = title
            service.cache_openalex_work(db, source_entity_id=entity.id, work=work)

    obj = service.create_object(
        db,
        canvas_id=uuid.UUID(req.canvasId),
        object_type=req.objectType,
        title=title,
        content=content,
        source_entity_id=source_entity_id,
        x=req.x,
        y=req.y,
    )
    return AddObjectResponse(object=_obj_out(obj))


@router.post("/edges", response_model=AddEdgeResponse)
def add_edge(req: AddEdgeRequest, db: Session = Depends(get_db)) -> AddEdgeResponse:
    try:
        edge = service.create_edge(
            db,
            canvas_id=uuid.UUID(req.canvasId),
            source_object_id=uuid.UUID(req.sourceObjectId),
            target_object_id=uuid.UUID(req.targetObjectId),
            edge_type=req.edgeType,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return AddEdgeResponse(edge=ObjectEdge(
        id=str(edge.id),
        canvasId=str(edge.canvas_id),
        sourceObjectId=str(edge.source_object_id),
        targetObjectId=str(edge.target_object_id),
        edgeType=edge.edge_type,
        provenance=edge.provenance,
    ))
