"""Source-entity deduplication (PRD §23). One canonical entity per real source.

A paper uploaded, fetched, or imported from Dropbox must resolve to the SAME
source_entity so scholarly metadata is never duplicated across canvases.
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.entities import SourceEntity


def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def resolve_or_create_source_entity(
    db: Session,
    *,
    source_type: str,
    external_id: str | None = None,
    doi: str | None = None,
    title: str | None = None,
    url: str | None = None,
    metadata: dict | None = None,
) -> SourceEntity:
    """Find an existing canonical entity by external id, then DOI, then
    normalized title; create one if none matches."""
    stmt = None
    if external_id:
        stmt = select(SourceEntity).where(
            SourceEntity.source_type == source_type,
            SourceEntity.canonical_external_id == external_id,
        )
    elif doi:
        norm_doi = doi.lower().replace("https://doi.org/", "").strip()
        stmt = select(SourceEntity).where(SourceEntity.canonical_external_id == norm_doi)

    if stmt is not None:
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            return existing

    if title:
        norm = _norm_title(title)
        for cand in db.execute(select(SourceEntity).where(SourceEntity.source_type == source_type)).scalars():
            if cand.title and _norm_title(cand.title) == norm:
                return cand

    entity = SourceEntity(
        source_type=source_type,
        canonical_external_id=external_id or (doi.lower().replace("https://doi.org/", "").strip() if doi else None),
        canonical_url=url,
        title=title,
        entity_metadata=metadata or {},
    )
    db.add(entity)
    db.flush()
    return entity
