"""Dropbox import (FileSourceProvider).

Lists a user's Dropbox files and imports one onto the canvas. The Dropbox SDK is
never touched here — only providers.registry.get_file_source(). Imported files
run through the SAME upload/parse path as a manual upload (service.ingest_file),
so a Dropbox PDF dedupes to a canonical source entity exactly like an uploaded
one (PRD §10/§23).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from canvas import service
from db.session import get_db
from providers.registry import get_file_source
from schemas import (
    DropboxListResponse, DropboxFile,
    DropboxImportRequest, DropboxImportResponse, CanvasObject,
)

router = APIRouter(prefix="/integrations/dropbox")


@router.get("/files", response_model=DropboxListResponse)
def list_files(path: str = "") -> DropboxListResponse:
    files = [DropboxFile(**f) for f in get_file_source().list_files(path)]
    return DropboxListResponse(files=files)


@router.post("/import", response_model=DropboxImportResponse)
def import_file(req: DropboxImportRequest, db: Session = Depends(get_db)) -> DropboxImportResponse:
    source = get_file_source()
    try:
        data = source.download(req.fileId)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Dropbox download failed: {e}")

    filename = next(
        (f["name"] for f in source.list_files("") if f.get("id") == req.fileId),
        req.fileId.rsplit("/", 1)[-1] or "Dropbox file",
    )

    obj = service.ingest_file(
        db,
        canvas_id=uuid.UUID(req.canvasId),
        data=data,
        filename=filename,
        origin="dropbox",
        x=req.x,
        y=req.y,
    )
    return DropboxImportResponse(object=CanvasObject(
        id=str(obj.id), canvasId=str(obj.canvas_id), objectType=obj.object_type,
        sourceEntityId=str(obj.source_entity_id) if obj.source_entity_id else None,
        title=obj.title, content=obj.content, x=obj.x, y=obj.y, createdBy=obj.created_by,
    ))
