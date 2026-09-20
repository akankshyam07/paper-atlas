# backend-data lane, DB-backed. Requires Postgres (docker compose up -d db) with
# migrations applied (alembic upgrade head). Uses the local default DATABASE_URL.

def _new_canvas(client) -> str:
    return client.post("/canvas", json={"title": "T"}).json()["id"]


def test_create_canvas(client):
    r = client.post("/canvas", json={"title": "My canvas"})
    assert r.status_code == 200
    assert r.json()["id"]


def test_add_object_persists(client):
    cid = _new_canvas(client)
    r = client.post("/objects", json={
        "canvasId": cid, "objectType": "PAPER", "title": "X", "x": 5, "y": 6,
    })
    assert r.status_code == 200
    obj = r.json()["object"]
    assert obj["objectType"] == "PAPER"
    assert obj["canvasId"] == cid
    assert obj["x"] == 5


def test_add_edge_belongs_to_canvas(client):
    cid = _new_canvas(client)
    a = client.post("/objects", json={"canvasId": cid, "objectType": "PAPER", "title": "A", "x": 0, "y": 0}).json()["object"]["id"]
    b = client.post("/objects", json={"canvasId": cid, "objectType": "NOTE", "title": "B", "x": 1, "y": 1}).json()["object"]["id"]
    r = client.post("/edges", json={
        "canvasId": cid, "sourceObjectId": a, "targetObjectId": b, "edgeType": "CITES",
    })
    assert r.status_code == 200
    assert r.json()["edge"]["canvasId"] == cid


def test_edge_rejects_missing_object(client):
    cid = _new_canvas(client)
    a = client.post("/objects", json={"canvasId": cid, "objectType": "PAPER", "title": "A", "x": 0, "y": 0}).json()["object"]["id"]
    import uuid
    r = client.post("/edges", json={
        "canvasId": cid, "sourceObjectId": a, "targetObjectId": str(uuid.uuid4()), "edgeType": "CITES",
    })
    assert r.status_code == 400
