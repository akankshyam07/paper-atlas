"""Upload and serve files (PRD §10/§22).

Uploads are validated for size and type, stored content-addressed, and placed on
the canvas through the same ingest path as a Dropbox import.
"""
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import Response

from canvas import service
from db import storage
from db.session import get_db
from schemas import CanvasObject
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/files", response_model=dict)
async def upload(
    file: UploadFile,
    canvasId: str = Form(...),
    x: float = Form(0.0),
    y: float = Form(0.0),
    db: Session = Depends(get_db),
) -> dict:
    data = await file.read()
    try:
        key = storage.store(data, filename=file.filename or "upload",
                            mime=file.content_type or "application/pdf")
    except storage.UploadTooLarge as e:
        raise HTTPException(status_code=413, detail=str(e))
    except storage.UploadTypeNotAllowed as e:
        raise HTTPException(status_code=415, detail=f"unsupported type: {e}")

    obj = service.ingest_file(
        db, canvas_id=uuid.UUID(canvasId), data=data,
        filename=file.filename or "upload", origin="upload", x=x, y=y,
        storage_key=key,
    )
    return {
        "object": CanvasObject(
            id=str(obj.id), canvasId=str(obj.canvas_id), objectType=obj.object_type,
            sourceEntityId=str(obj.source_entity_id) if obj.source_entity_id else None,
            title=obj.title, content=obj.content, x=obj.x, y=obj.y, createdBy=obj.created_by,
        ).model_dump(),
        "url": storage.signed_url(key),
    }


@router.get("/files/{key}")
def serve(key: str) -> Response:
    data = storage.load(key)
    if data is None:
        raise HTTPException(status_code=404, detail="file not found")
    return Response(content=data, media_type="application/pdf")
