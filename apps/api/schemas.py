"""Pydantic mirrors of packages/types/api.ts. Keep in sync with the contract."""
from typing import Any, Literal, Optional
from pydantic import BaseModel

ObjectType = Literal["PAPER", "PDF", "IMAGE", "VIDEO", "AUDIO", "DOC", "EMBED", "NOTE", "EXCERPT", "AI_SUMMARY", "GROUP", "THREAD"]
EdgeType = Literal["CITES", "DERIVED_FROM", "EXPLAINS", "RELATED_TO"]
RecommendMode = Literal["broader", "deeper"]


class PaperPreview(BaseModel):
    openalexId: str
    title: str
    authors: list[str]
    year: Optional[int]
    venue: Optional[str]
    citedByCount: int
    hasPdf: bool


class CanvasObject(BaseModel):
    id: str
    canvasId: str
    objectType: ObjectType
    sourceEntityId: Optional[str]
    title: Optional[str]
    content: dict[str, Any]
    x: float
    y: float
    createdBy: Literal["USER", "AI"]


class ObjectEdge(BaseModel):
    id: str
    canvasId: str
    sourceObjectId: str
    targetObjectId: str
    edgeType: EdgeType
    provenance: Literal["USER", "SYSTEM", "AI"]


class Recommendation(BaseModel):
    paper: PaperPreview
    mode: RecommendMode
    relationshipLabel: str
    reason: str
    score: float


class SearchResponse(BaseModel):
    results: list[PaperPreview]


class AddObjectRequest(BaseModel):
    canvasId: str
    objectType: ObjectType
    openalexId: Optional[str] = None
    title: Optional[str] = None
    content: dict[str, Any] = {}
    x: float
    y: float


class AddObjectResponse(BaseModel):
    object: CanvasObject


class AddEdgeRequest(BaseModel):
    canvasId: str
    sourceObjectId: str
    targetObjectId: str
    edgeType: EdgeType


class AddEdgeResponse(BaseModel):
    edge: ObjectEdge


class RecommendRequest(BaseModel):
    objectId: str
    mode: RecommendMode
    offset: int = 0


class RecommendResponse(BaseModel):
    recommendations: list[Recommendation]


class ExplainRequest(BaseModel):
    objectId: Optional[str] = None
    text: Optional[str] = None
    canvasId: str


class ExplainResponse(BaseModel):
    object: CanvasObject
    edge: ObjectEdge


# ---- Sponsor-feature schemas ----
class TranscribeResponse(BaseModel):
    text: str


class SynthesizeRequest(BaseModel):
    text: str


class SuppressRequest(BaseModel):
    canvasId: str
    mode: RecommendMode
    openalexId: str


class StanceRequest(BaseModel):
    objectId: str
    stance: str  # "supporting" | "contradicting"


class ChatRequest(BaseModel):
    canvasId: str
    message: str
    selectedObjectIds: list[str] = []


class ChatResponse(BaseModel):
    reply: str
    contextObjectIds: list[str]


class EmbedRequest(BaseModel):
    canvasId: str
    url: str
    title: str | None = None
    x: float = 0.0
    y: float = 0.0


class EmbedResponse(BaseModel):
    object: CanvasObject


class ConceptSpan(BaseModel):
    term: str
    start: int
    end: int
    title: str
    url: str


class ConceptsResponse(BaseModel):
    spans: list[ConceptSpan]


class WikiSummary(BaseModel):
    title: str
    extract: str
    url: str
    thumbnail: str | None = None
