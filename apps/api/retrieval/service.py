"""Canvas-local retrieval (PRD §15).

Chunks are section-aware where possible and keep their source object, so a
retrieved passage can always be traced back to what it came from. Only
user/canvas content is embedded — OpenAlex already does semantic search over
the corpus, and duplicating that is explicitly out of scope.
"""
from __future__ import annotations

import re
import uuid

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from models.entities import CanvasObject, Chunk

# ~600-1000 tokens with overlap, per PRD §15 — small chunks destroy scholarly
# context, so paragraphs are packed rather than split blindly.
TARGET_CHARS = 3200
OVERLAP_CHARS = 400


def chunk_text(body: str) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n{2,}", body) if p.strip()]
    if not paras:
        return []
    out: list[str] = []
    buf = ""
    for p in paras:
        if len(buf) + len(p) + 2 <= TARGET_CHARS:
            buf = f"{buf}\n\n{p}" if buf else p
            continue
        if buf:
            out.append(buf)
            buf = (buf[-OVERLAP_CHARS:] + "\n\n" + p) if OVERLAP_CHARS else p
        else:
            out.append(p[:TARGET_CHARS])
            buf = ""
    if buf:
        out.append(buf)
    return out


def index_object(db: Session, obj: CanvasObject) -> int:
    """(Re)index one object. Returns how many chunks were written."""
    from providers.registry import get_embedding

    content = obj.content or {}
    body = str(content.get("abstract") or content.get("text") or "")
    if not body.strip():
        return 0

    db.execute(Chunk.__table__.delete().where(Chunk.object_id == obj.id))
    pieces = chunk_text(body)
    if not pieces:
        return 0

    vectors: list[list[float] | None] = [None] * len(pieces)
    try:
        embedded = get_embedding().embed(pieces)
        # A stub embedder returns the wrong width; store text-only rather than
        # writing vectors that can never match.
        if embedded and len(embedded[0]) == 1536:
            vectors = embedded  # type: ignore[assignment]
    except Exception:
        pass

    for piece, vec in zip(pieces, vectors):
        db.add(Chunk(canvas_id=obj.canvas_id, object_id=obj.id, text=piece,
                     section_title=(obj.title or "")[:200], embedding=vec))
    db.commit()
    return len(pieces)


def search(db: Session, canvas_id: uuid.UUID, query: str, *, limit: int = 6) -> list[dict]:
    """Vector search when embeddings exist, lexical fallback when they do not,
    so retrieval still works without an embedding key."""
    from providers.registry import get_embedding

    vec = None
    try:
        got = get_embedding().embed([query])
        if got and len(got[0]) == 1536:
            vec = got[0]
    except Exception:
        vec = None

    if vec is not None:
        rows = db.execute(
            text("""
                SELECT c.id, c.object_id, c.text, c.section_title,
                       1 - (c.embedding <=> CAST(:v AS vector)) AS score
                FROM chunks c
                WHERE c.canvas_id = :cid AND c.embedding IS NOT NULL
                ORDER BY c.embedding <=> CAST(:v AS vector)
                LIMIT :n
            """),
            {"v": str(vec), "cid": str(canvas_id), "n": limit},
        ).mappings().all()
        if rows:
            return [dict(r) for r in rows]

    like = f"%{query[:80]}%"
    rows = db.execute(
        select(Chunk).where(Chunk.canvas_id == canvas_id, Chunk.text.ilike(like)).limit(limit)
    ).scalars().all()
    return [{"id": r.id, "object_id": r.object_id, "text": r.text,
             "section_title": r.section_title, "score": None} for r in rows]
