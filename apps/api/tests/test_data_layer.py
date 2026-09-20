# Service + dedup unit tests against the DB (PRD §23 dedup, §6 provenance).
import uuid

from db.session import SessionLocal
from canvas import service
from canvas.dedup import resolve_or_create_source_entity


def test_dedup_same_openalex_id_returns_same_entity():
    db = SessionLocal()
    try:
        oid = f"W{uuid.uuid4().hex[:8]}"
        e1 = resolve_or_create_source_entity(db, source_type="OPENALEX_WORK", external_id=oid, title="Paper")
        db.commit()
        e2 = resolve_or_create_source_entity(db, source_type="OPENALEX_WORK", external_id=oid, title="Paper")
        assert e1.id == e2.id
    finally:
        db.rollback(); db.close()


def test_dedup_matches_normalized_title():
    db = SessionLocal()
    try:
        t = f"Attention {uuid.uuid4().hex[:6]}"
        e1 = resolve_or_create_source_entity(db, source_type="UPLOADED_FILE", title=t)
        db.commit()
        e2 = resolve_or_create_source_entity(db, source_type="UPLOADED_FILE", title=t.upper() + "!!!")
        assert e1.id == e2.id
    finally:
        db.rollback(); db.close()


def test_provenance_ai_object_flagged():
    db = SessionLocal()
    try:
        c = service.create_canvas(db, title="c")
        o = service.create_object(db, canvas_id=c.id, object_type="AI_SUMMARY", title="ai", created_by="AI")
        assert o.created_by == "AI"
    finally:
        db.close()


def test_get_neighbors_one_hop():
    db = SessionLocal()
    try:
        c = service.create_canvas(db, title="c")
        a = service.create_object(db, canvas_id=c.id, object_type="PAPER", title="A")
        b = service.create_object(db, canvas_id=c.id, object_type="PAPER", title="B")
        service.create_edge(db, canvas_id=c.id, source_object_id=a.id, target_object_id=b.id, edge_type="CITES")
        neigh = service.get_neighbors(db, a.id, depth=1)
        assert b.id in [n.id for n in neigh]
    finally:
        db.close()


def test_ingest_file_dedups_and_places():
    db = SessionLocal()
    try:
        c = service.create_canvas(db, title="c")
        obj = service.ingest_file(db, canvas_id=c.id, data=b"%PDF", filename="paper.pdf")
        assert obj.object_type == "PAPER"
        assert obj.source_entity_id is not None
    finally:
        db.close()
