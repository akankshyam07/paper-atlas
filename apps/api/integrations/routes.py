"""Dropbox import (FileSourceProvider). Owner: backend-data + backend-ai seam.

Lists a user's Dropbox files and imports one onto the canvas. The Dropbox SDK
is never touched here — only providers.registry.get_file_source(). Imported
files run through the same upload/parse path as a manual upload (PRD §10/§23),
so a Dropbox PDF dedupes to an OpenAlex work exactly like an uploaded one.
"""
import uuid
from fastapi import APIRouter

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
def import_file(req: DropboxImportRequest) -> DropboxImportResponse:
    # TODO: get_file_source().download(req.fileId) -> DocumentService upload+parse
    # -> dedup to source entity -> place object. Stub returns a placed PDF object.
    _ = get_file_source().download(req.fileId)
    obj = CanvasObject(
        id=str(uuid.uuid4()),
        canvasId=req.canvasId,
        objectType="PAPER",
        sourceEntityId=None,
        title="Imported from Dropbox (stub)",
        content={"origin": "dropbox", "fileId": req.fileId},
        x=req.x,
        y=req.y,
        createdBy="USER",
    )
    return DropboxImportResponse(object=obj)
