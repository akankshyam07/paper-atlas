# backend-ai lane tests. BE #2 extends: real OpenAlex, distinct broader/deeper,
# loop suppression, provenance on explain.
def test_search_returns_previews(client):
    r = client.get("/search", params={"q": "transformers"})
    assert r.status_code == 200
    assert len(r.json()["results"]) >= 1


def test_recommend_returns_three(client):
    r = client.post("/recommend", json={"objectId": "o1", "mode": "broader"})
    assert r.status_code == 200
    recs = r.json()["recommendations"]
    assert len(recs) == 3
    assert all(x["mode"] == "broader" for x in recs)


def test_broader_and_deeper_differ(client):
    b = client.post("/recommend", json={"objectId": "o1", "mode": "broader"}).json()
    d = client.post("/recommend", json={"objectId": "o1", "mode": "deeper"}).json()
    # PRD §13: distinct directional logic, so labels must not be identical.
    assert b["recommendations"][0]["relationshipLabel"] != d["recommendations"][0]["relationshipLabel"]


def test_explain_creates_note_with_edge(client):
    r = client.post("/explain", json={"objectId": "o1", "canvasId": "c1"})
    assert r.status_code == 200
    body = r.json()
    assert body["object"]["objectType"] == "AI_SUMMARY"
    assert body["edge"]["edgeType"] == "EXPLAINS"
    assert body["edge"]["targetObjectId"] == body["object"]["id"]
