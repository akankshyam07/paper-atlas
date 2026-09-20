"""Upload and serve files (PRD §10/§22).

Uploads are validated for size and type, stored content-addressed, and placed on
the canvas through service.ingest_file.
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
        storage_key=key, mime=file.content_type or "application/octet-stream",
    )
    return {
        "object": CanvasObject(
            id=str(obj.id), canvasId=str(obj.canvas_id), objectType=obj.object_type,
            sourceEntityId=str(obj.source_entity_id) if obj.source_entity_id else None,
            title=obj.title, content=obj.content, x=obj.x, y=obj.y, createdBy=obj.created_by,
        ).model_dump(),
        "url": storage.signed_url(key),
    }


# Extension -> media type, so a stored file is served as what it actually is
# and the browser can render images and stream video.
_MEDIA = {
    ".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp",
    ".svg": "image/svg+xml", ".mp4": "video/mp4", ".mov": "video/quicktime",
    ".webm": "video/webm", ".mp3": "audio/mpeg", ".wav": "audio/wav",
    ".m4a": "audio/mp4", ".txt": "text/plain", ".md": "text/markdown",
}


@router.get("/files/{key}")
def serve(key: str) -> Response:
    import pathlib as _p

    data = storage.load(key)
    if data is None:
        raise HTTPException(status_code=404, detail="file not found")
    media = _MEDIA.get(_p.Path(key).suffix.lower(), "application/octet-stream")
    return Response(content=data, media_type=media,
                    headers={"Accept-Ranges": "bytes", "Cache-Control": "public, max-age=3600"})


@router.get("/proxy/pdf")
def proxy_pdf(url: str) -> Response:
    """Stream an open-access PDF through the app.

    Publishers commonly send X-Frame-Options / CSP that stop a cross-origin PDF
    being embedded, so previewing one directly in the canvas renders blank.
    Serving it from our own origin fixes that.
    """
    import ipaddress
    import socket
    from urllib.parse import urlparse

    import httpx

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="only http(s) urls")

    # SSRF guard: never let a caller point this at the private network.
    try:
        for info in socket.getaddrinfo(parsed.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise HTTPException(status_code=400, detail="blocked host")
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="unresolvable host")

    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            r = client.get(url, headers={"User-Agent": "PaperAtlas/1.0"})
            r.raise_for_status()
            data = r.content
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"fetch failed: {e}")

    if len(data) > storage.MAX_BYTES:
        raise HTTPException(status_code=413, detail="pdf too large to preview")

    return Response(
        content=data,
        media_type=r.headers.get("content-type", "application/pdf").split(";")[0],
        headers={"Cache-Control": "public, max-age=86400"},
    )
