# backend-data lane tests. BE #1 extends: dedup, provenance, transactional edges.
def test_add_object_returns_shaped_object(client):
    r = client.post("/objects", json={
        "canvasId": "c1", "objectType": "PAPER", "title": "X", "x": 0, "y": 0,
    })
    assert r.status_code == 200
    obj = r.json()["object"]
    assert obj["objectType"] == "PAPER"
    assert obj["id"]


def test_add_edge_belongs_to_canvas(client):
    r = client.post("/edges", json={
        "canvasId": "c1", "sourceObjectId": "a", "targetObjectId": "b",
        "edgeType": "CITES",
    })
    assert r.status_code == 200
    assert r.json()["edge"]["canvasId"] == "c1"
