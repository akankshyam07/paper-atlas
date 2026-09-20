"""backend-data lane. Owns: POST /objects, POST /edges.

STUB: returns contract-shaped fake data. BE #1 replaces with real DB writes
(canvas/service.py) — transactional graph mutations, provenance preserved.
"""
import uuid
from fastapi import APIRouter

from schemas import (
    AddObjectRequest, AddObjectResponse,
    AddEdgeRequest, AddEdgeResponse,
    CanvasObject, ObjectEdge,
)

router = APIRouter()


@router.post("/objects", response_model=AddObjectResponse)
def add_object(req: AddObjectRequest) -> AddObjectResponse:
    # TODO(BE#1): persist via canvas/service.py, dedup source entity, keep provenance.
    obj = CanvasObject(
        id=str(uuid.uuid4()),
        canvasId=req.canvasId,
        objectType=req.objectType,
        sourceEntityId=None,
        title=req.title or "Untitled",
        content=req.content,
        x=req.x,
        y=req.y,
        createdBy="USER",
    )
    return AddObjectResponse(object=obj)


@router.post("/edges", response_model=AddEdgeResponse)
def add_edge(req: AddEdgeRequest) -> AddEdgeResponse:
    # TODO(BE#1): persist edge; every edge belongs to a canvas (PRD invariant).
    edge = ObjectEdge(
        id=str(uuid.uuid4()),
        canvasId=req.canvasId,
        sourceObjectId=req.sourceObjectId,
        targetObjectId=req.targetObjectId,
        edgeType=req.edgeType,
        provenance="USER",
    )
    return AddEdgeResponse(edge=edge)
