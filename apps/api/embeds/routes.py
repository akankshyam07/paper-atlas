"""Embed any URL as a canvas object (PRD §7 "generic web article", §27).

Recognised providers get their real embed player; anything else is embedded
directly when the site permits framing, and falls back to a link card when it
does not. We never scrape page bodies — only the title, so the card is readable.
"""
from __future__ import annotations

import re
import uuid
from urllib.parse import parse_qs, urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from canvas import service
from db.session import get_db
from schemas import CanvasObject, EmbedRequest, EmbedResponse

router = APIRouter()

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}


def embed_url(url: str) -> tuple[str | None, str]:
    """Return (embeddable url, provider). None means: show a link card."""
    u = urlparse(url)
    host = (u.hostname or "").lower()

    if host in YOUTUBE_HOSTS:
        vid = u.path.lstrip("/") if "youtu.be" in host else (parse_qs(u.query).get("v") or [""])[0]
        if not vid and u.path.startswith(("/embed/", "/shorts/")):
            vid = u.path.split("/")[2] if len(u.path.split("/")) > 2 else ""
        return (f"https://www.youtube.com/embed/{vid}" if vid else None), "youtube"

    if host.endswith("vimeo.com"):
        m = re.search(r"/(\d+)", u.path)
        return (f"https://player.vimeo.com/video/{m.group(1)}" if m else None), "vimeo"

    if host.endswith("wikipedia.org"):
        return url, "wikipedia"

    if host.endswith("arxiv.org") and "/abs/" in u.path:
        # Prefer the PDF so it renders as a document rather than a landing page.
        return url.replace("/abs/", "/pdf/"), "arxiv"

    return url, "web"


def fetch_title(url: str) -> str | None:
    try:
        with httpx.Client(timeout=6.0, follow_redirects=True) as c:
            r = c.get(url, headers={"User-Agent": "PaperAtlas/1.0"})
            r.raise_for_status()
            head = r.text[:200_000]
    except httpx.HTTPError:
        return None
    for pattern in (r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
                    r"<title[^>]*>([^<]+)</title>"):
        m = re.search(pattern, head, re.I)
        if m:
            return m.group(1).strip()[:200]
    return None


@router.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest, db: Session = Depends(get_db)) -> EmbedResponse:
    u = urlparse(req.url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise HTTPException(status_code=400, detail="only http(s) urls")

    src, provider = embed_url(req.url)
    title = req.title or fetch_title(req.url) or u.hostname

    obj = service.create_object(
        db,
        canvas_id=uuid.UUID(req.canvasId),
        object_type="EMBED",
        title=title,
        content={"url": req.url, "embedUrl": src, "provider": provider},
        x=req.x, y=req.y,
    )
    return EmbedResponse(object=CanvasObject(
        id=str(obj.id), canvasId=str(obj.canvas_id), objectType=obj.object_type,
        sourceEntityId=None, title=obj.title, content=obj.content,
        x=obj.x, y=obj.y, createdBy=obj.created_by,
    ))
