"""Upload, canvas delete, suppression, chat and discovery. No credentials needed:
storage falls back to local disk and the stub LLM answers chat."""
import uuid


def _canvas(client) -> str:
    return client.post("/canvas", json={"title": "T"}).json()["id"]


def test_upload_stores_and_places_object(client):
    cid = _canvas(client)
    r = client.post("/files", files={"file": ("p.pdf", b"%PDF-1.4 hello", "application/pdf")},
                    data={"canvasId": cid, "x": "5", "y": "6"})
    assert r.status_code == 200
    body = r.json()
    assert body["object"]["objectType"] == "PDF"
    assert body["object"]["content"]["storageKey"]
    assert body["url"]


def test_uploaded_file_is_served_back(client):
    cid = _canvas(client)
    up = client.post("/files", files={"file": ("p.pdf", b"%PDF-1.4 servable", "application/pdf")},
                     data={"canvasId": cid}).json()
    key = up["object"]["content"]["storageKey"]
    got = client.get(f"/files/{key}")
    assert got.status_code == 200
    assert got.content == b"%PDF-1.4 servable"


def test_upload_rejects_unsupported_type(client):
    cid = _canvas(client)
    r = client.post("/files", files={"file": ("x.exe", b"MZ", "application/x-msdownload")},
                    data={"canvasId": cid})
    assert r.status_code == 415


def test_upload_is_content_addressed(client):
    cid = _canvas(client)
    a = client.post("/files", files={"file": ("a.pdf", b"%PDF same", "application/pdf")},
                    data={"canvasId": cid}).json()
    b = client.post("/files", files={"file": ("a.pdf", b"%PDF same", "application/pdf")},
                    data={"canvasId": cid}).json()
    assert a["object"]["content"]["storageKey"] == b["object"]["content"]["storageKey"]


def test_delete_canvas_soft_deletes(client):
    cid = _canvas(client)
    assert client.delete(f"/canvas/{cid}").status_code == 200
    assert client.delete(f"/canvas/{uuid.uuid4()}").status_code == 404


def test_suppression_is_recorded_and_idempotent(client):
    cid = _canvas(client)
    body = {"canvasId": cid, "mode": "broader", "openalexId": "W999"}
    assert client.post("/suppressions", json=body).status_code == 200
    assert client.post("/suppressions", json=body).status_code == 200

    from db.session import SessionLocal
    from canvas import service
    db = SessionLocal()
    try:
        assert "W999" in service.suppressed_ids(db, uuid.UUID(cid), "broader")
        assert "W999" not in service.suppressed_ids(db, uuid.UUID(cid), "deeper")
    finally:
        db.close()


def test_chat_prioritises_selected_objects(client):
    cid = _canvas(client)
    sel = client.post("/objects", json={"canvasId": cid, "objectType": "NOTE", "title": "Selected",
                                        "content": {"text": "the selected note body"},
                                        "x": 0, "y": 0}).json()["object"]
    client.post("/objects", json={"canvasId": cid, "objectType": "NOTE", "title": "Other",
                                  "content": {"text": "unrelated"}, "x": 1, "y": 1})
    r = client.post("/chat", json={"canvasId": cid, "message": "what is this?",
                                   "selectedObjectIds": [sel["id"]]})
    assert r.status_code == 200
    body = r.json()
    assert body["reply"]
    # The selection must be in the context that produced the answer (PRD §15).
    assert sel["id"] in body["contextObjectIds"]


def test_chat_works_with_no_selection(client):
    cid = _canvas(client)
    r = client.post("/chat", json={"canvasId": cid, "message": "hello"})
    assert r.status_code == 200
    assert r.json()["reply"]
