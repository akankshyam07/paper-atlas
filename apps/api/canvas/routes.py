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
from schemas import (
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


@router.post("/objects", response_model=AddObjectResponse)
def add_object(req: AddObjectRequest, db: Session = Depends(get_db)) -> AddObjectResponse:
    source_entity_id = None
    if req.openalexId:
        entity = resolve_or_create_source_entity(
            db, source_type="OPENALEX_WORK", external_id=req.openalexId, title=req.title,
        )
        source_entity_id = entity.id
    obj = service.create_object(
        db,
        canvas_id=uuid.UUID(req.canvasId),
        object_type=req.objectType,
        title=req.title,
        content=req.content,
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
