"""AI proposals (PRD §16).

The agent never writes to the board. It reads the canvas through scoped calls
and emits proposals; the user sees what would change and accepts or rejects it.
Accepting is the only path that mutates the graph, and it runs through the same
canvas service as any user action, so provenance is identical.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from canvas import service
from db.session import get_db
from models.entities import AIProposal
from schemas import (
    OrganizeRequest, Proposal, ProposalList, ProposeRequest, ResolveResponse,
)

router = APIRouter()

SYSTEM = (
    "You organise a researcher's canvas. You never edit it directly: you propose "
    "changes and the user decides. Reply with JSON only."
)


def _out(p: AIProposal) -> Proposal:
    return Proposal(
        id=str(p.id), canvasId=str(p.canvas_id), proposalType=p.proposal_type,
        payload=p.payload or {}, reason=p.reason, status=p.status,
    )


@router.post("/proposals", response_model=Proposal)
def create_proposal(req: ProposeRequest, db: Session = Depends(get_db)) -> Proposal:
    """Record a proposed change. Nothing on the board moves until it is accepted."""
    p = AIProposal(
        canvas_id=uuid.UUID(req.canvasId), proposal_type=req.proposalType,
        payload=req.payload, reason=req.reason,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _out(p)


@router.get("/proposals", response_model=ProposalList)
def list_proposals(canvasId: str, status: str = "PENDING", db: Session = Depends(get_db)) -> ProposalList:
    rows = db.execute(
        select(AIProposal)
        .where(AIProposal.canvas_id == uuid.UUID(canvasId), AIProposal.status == status)
        .order_by(AIProposal.created_at.desc())
    ).scalars().all()
    return ProposalList(proposals=[_out(p) for p in rows])


@router.post("/proposals/{proposal_id}/accept", response_model=ResolveResponse)
def accept(proposal_id: str, db: Session = Depends(get_db)) -> ResolveResponse:
    """Apply a proposal. This is the only place an agent-authored change reaches
    the graph, and it goes through the normal canvas service."""
    p = db.get(AIProposal, uuid.UUID(proposal_id))
    if p is None:
        raise HTTPException(status_code=404, detail="proposal not found")
    if p.status != "PENDING":
        raise HTTPException(status_code=409, detail=f"already {p.status.lower()}")

    payload = p.payload or {}
    created: list[str] = []

    if p.proposal_type == "CREATE_OBJECT":
        obj = service.create_object(
            db, canvas_id=p.canvas_id, object_type=payload.get("objectType", "NOTE"),
            title=payload.get("title"), content=payload.get("content", {}),
            x=float(payload.get("x", 0)), y=float(payload.get("y", 0)), created_by="AI",
        )
        created.append(str(obj.id))

    elif p.proposal_type == "CREATE_EDGE":
        edge = service.create_edge(
            db, canvas_id=p.canvas_id,
            source_object_id=uuid.UUID(payload["sourceObjectId"]),
            target_object_id=uuid.UUID(payload["targetObjectId"]),
            edge_type=payload.get("edgeType", "RELATED_TO"), provenance="AI",
        )
        created.append(str(edge.id))

    elif p.proposal_type == "GROUP_OBJECTS":
        group = service.create_object(
            db, canvas_id=p.canvas_id, object_type="GROUP",
            title=payload.get("name", "Group"), content={"kind": "group"},
            x=float(payload.get("x", 0)), y=float(payload.get("y", 0)), created_by="AI",
        )
        created.append(str(group.id))

    elif p.proposal_type == "MOVE_OBJECTS":
        for mv in payload.get("moves", []):
            obj = service.get_object(db, uuid.UUID(mv["objectId"]))
            if obj:
                obj.x, obj.y = float(mv["x"]), float(mv["y"])
        db.commit()

    p.status = "ACCEPTED"
    p.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return ResolveResponse(id=str(p.id), status=p.status, createdIds=created)


@router.post("/proposals/{proposal_id}/reject", response_model=ResolveResponse)
def reject(proposal_id: str, db: Session = Depends(get_db)) -> ResolveResponse:
    p = db.get(AIProposal, uuid.UUID(proposal_id))
    if p is None:
        raise HTTPException(status_code=404, detail="proposal not found")
    p.status = "REJECTED"
    p.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return ResolveResponse(id=str(p.id), status=p.status, createdIds=[])


@router.post("/organize", response_model=ProposalList)
def organize(req: OrganizeRequest, db: Session = Depends(get_db)) -> ProposalList:
    """Ask the agent to tidy the canvas. It returns proposals, never edits.

    The model only sees compact object summaries — titles, types and positions —
    never whole documents (PRD §15 context budget).
    """
    from providers.registry import get_inference_optimizer, get_llm

    canvas_id = uuid.UUID(req.canvasId)
    objects = service.list_objects(db, canvas_id, limit=60)
    if len(objects) < 2:
        return ProposalList(proposals=[])

    summary = [{
        "id": str(o.id), "type": o.object_type,
        "title": (o.title or "")[:90],
        "topics": ((o.content or {}).get("topics") or [])[:3],
    } for o in objects]

    prompt = (
        f"Canvas objects:\n{json.dumps(summary, indent=None)}\n\n"
        f"Request: {req.instruction or 'Group these into meaningful clusters.'}\n\n"
        'Reply with JSON: {"groups":[{"name":"...","objectIds":["..."],"reason":"..."}]}. '
        "Use only ids from the list. Prefer two to four groups."
    )
    raw = get_llm().complete(get_inference_optimizer().optimize(prompt), system=SYSTEM)

    try:
        data = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
        groups = data.get("groups", [])
    except (ValueError, KeyError):
        # A model that did not return usable JSON must not silently produce an
        # empty result that looks like "nothing to organise".
        raise HTTPException(status_code=502, detail="the model did not return a usable plan")

    valid = {s["id"] for s in summary}
    out: list[AIProposal] = []
    for g in groups[:4]:
        ids = [i for i in g.get("objectIds", []) if i in valid]
        if len(ids) < 2:
            continue
        p = AIProposal(
            canvas_id=canvas_id, proposal_type="GROUP_OBJECTS",
            payload={"name": g.get("name", "Group")[:60], "objectIds": ids},
            reason=(g.get("reason") or "")[:300],
        )
        db.add(p)
        out.append(p)
    db.commit()
    for p in out:
        db.refresh(p)
    return ProposalList(proposals=[_out(p) for p in out])
