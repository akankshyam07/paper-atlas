"""SQLAlchemy models — the canvas graph truth (PRD §5, §6).

Two-level model: canonical `source_entities` (a paper/wiki/file, once per
workspace) vs `canvas_objects` (one placement of an entity or a user artifact on
one canvas). This keeps scholarly metadata de-duplicated and board state
independent of source state.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    String, Float, Integer, DateTime, ForeignKey, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Canvas(Base):
    __tablename__ = "canvases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    viewport_state: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    objects: Mapped[list[CanvasObject]] = relationship(back_populates="canvas", cascade="all, delete-orphan")
    edges: Mapped[list[ObjectEdge]] = relationship(back_populates="canvas", cascade="all, delete-orphan")


class SourceEntity(Base):
    """Canonical source, independent of any canvas. Deduped by
    (source_type, canonical_external_id)."""
    __tablename__ = "source_entities"
    __table_args__ = (
        # one canonical row per external id + type
        {"sqlite_autoincrement": False},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    source_type: Mapped[str] = mapped_column(String, nullable=False)  # OPENALEX_WORK|WIKIPEDIA|UPLOADED_FILE|EXTERNAL_URL
    canonical_external_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    canonical_url: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    entity_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    content_status: Mapped[str] = mapped_column(String, default="NONE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CanvasObject(Base):
    """One placement/instance on one canvas."""
    __tablename__ = "canvas_objects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    canvas_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("canvases.id", ondelete="CASCADE"), nullable=False, index=True)
    object_type: Mapped[str] = mapped_column(String, nullable=False)  # PAPER|NOTE|EXCERPT|AI_SUMMARY|...
    source_entity_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("source_entities.id"), nullable=True)
    parent_object_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("canvas_objects.id"), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[dict] = mapped_column(JSONB, default=dict)
    x: Mapped[float] = mapped_column(Float, default=0.0)
    y: Mapped[float] = mapped_column(Float, default=0.0)
    width: Mapped[float | None] = mapped_column(Float, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    z_index: Mapped[int] = mapped_column(Integer, default=0)
    visual_state: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_by: Mapped[str] = mapped_column(String, default="USER")  # USER|AI
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    canvas: Mapped[Canvas] = relationship(back_populates="objects")


class ObjectEdge(Base):
    """A typed link between two objects. Every edge belongs to a canvas."""
    __tablename__ = "object_edges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    canvas_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("canvases.id", ondelete="CASCADE"), nullable=False, index=True)
    source_object_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("canvas_objects.id", ondelete="CASCADE"), nullable=False)
    target_object_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("canvas_objects.id", ondelete="CASCADE"), nullable=False)
    edge_type: Mapped[str] = mapped_column(String, nullable=False)  # CITES|DERIVED_FROM|EXPLAINS|...
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    direction: Mapped[str] = mapped_column(String, default="DIRECTED")
    provenance: Mapped[str] = mapped_column(String, default="USER")  # USER|SYSTEM|AI
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    edge_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    canvas: Mapped[Canvas] = relationship(back_populates="edges")


class OpenAlexWorkCache(Base):
    """Cache only works the user touches (PRD §12) — never mirror all of OpenAlex."""
    __tablename__ = "openalex_works_cache"

    source_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_entities.id"), primary_key=True)
    openalex_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    doi: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    abstract_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_date: Mapped[str | None] = mapped_column(String, nullable=True)
    authors: Mapped[dict] = mapped_column(JSONB, default=dict)
    primary_topic: Mapped[dict] = mapped_column(JSONB, default=dict)
    topics: Mapped[dict] = mapped_column(JSONB, default=dict)
    keywords: Mapped[dict] = mapped_column(JSONB, default=dict)
    referenced_work_ids: Mapped[dict] = mapped_column(JSONB, default=dict)
    related_work_ids: Mapped[dict] = mapped_column(JSONB, default=dict)
    cited_by_count: Mapped[int] = mapped_column(Integer, default=0)
    open_access: Mapped[dict] = mapped_column(JSONB, default=dict)
    content_urls: Mapped[dict] = mapped_column(JSONB, default=dict)
    cached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Chunk(Base):
    """Embedded chunk of canvas-local content for RAG (PRD §15). BE #2 fills
    embeddings; the vector column is added in a follow-up migration once pgvector
    is confirmed enabled, to keep the first migration portable.
    """
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    canvas_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("canvases.id", ondelete="CASCADE"), nullable=False, index=True)
    object_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("canvas_objects.id", ondelete="CASCADE"), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    section_title: Mapped[str | None] = mapped_column(String, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # embedding VECTOR(1536) added by migration 0002 (needs pgvector extension)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
