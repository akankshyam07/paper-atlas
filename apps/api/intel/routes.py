"""backend-ai lane. Owns: GET /search, POST /recommend, POST /explain.

STUB: returns contract-shaped fake data. BE #2 replaces with OpenAlex + real
Broader/Deeper scoring (recommend.py) and AI explain (explain.py).
"""
import uuid
from fastapi import APIRouter

from schemas import (
    SearchResponse, PaperPreview,
    RecommendRequest, RecommendResponse, Recommendation,
    ExplainRequest, ExplainResponse, CanvasObject, ObjectEdge,
)

router = APIRouter()

_FAKE_PAPER = PaperPreview(
    openalexId="W0000000",
    title="Attention Is All You Need",
    authors=["Vaswani", "Shazeer", "Parmar"],
    year=2017,
    venue="NeurIPS",
    citedByCount=100000,
    hasPdf=True,
)


@router.get("/search", response_model=SearchResponse)
def search(q: str) -> SearchResponse:
    # TODO(BE#2): call openalex/client.py keyword search, map via mapping.py.
    return SearchResponse(results=[_FAKE_PAPER])


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest) -> RecommendResponse:
    # TODO(BE#2): Broader vs Deeper are DISTINCT (PRD §13). Broader = hierarchy-up
    # / foundational / references. Deeper = semantic-narrow / recent citing works.
    # Score candidates deterministically, LLM-rerank top few, suppress loops.
    label = "foundational method" if req.mode == "broader" else "narrower application"
    recs = [
        Recommendation(
            paper=_FAKE_PAPER,
            mode=req.mode,
            relationshipLabel=label,
            reason=f"stub {req.mode} candidate #{i + 1}",
            score=1.0 - i * 0.1,
        )
        for i in range(3)
    ]
    return RecommendResponse(recommendations=recs)


@router.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest) -> ExplainResponse:
    # TODO(BE#2): call LLM on excerpt + source metadata; create AI_SUMMARY note
    # and an EXPLAINS edge back to the source (provenance, PRD §2.2).
    note = CanvasObject(
        id=str(uuid.uuid4()),
        canvasId=req.canvasId,
        objectType="AI_SUMMARY",
        sourceEntityId=None,
        title="Explanation (stub)",
        content={"text": "This is a stub explanation."},
        x=0.0,
        y=0.0,
        createdBy="AI",
    )
    edge = ObjectEdge(
        id=str(uuid.uuid4()),
        canvasId=req.canvasId,
        sourceObjectId=req.objectId or "unknown",
        targetObjectId=note.id,
        edgeType="EXPLAINS",
        provenance="AI",
    )
    return ExplainResponse(object=note, edge=edge)
