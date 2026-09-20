"""AI proposals (PRD §16), persisted threads (§17) and canvas retrieval (§15).
No credentials needed: the stub LLM/embedder covers these paths."""
import uuid

from retrieval.service import chunk_text


def _canvas(client) -> str:
    return client.post("/canvas", json={"title": "T"}).json()["id"]


# ---- proposals: the agent proposes, the user disposes ----

def test_proposal_does_not_touch_the_board_until_accepted(client):
    cid = _canvas(client)
    before = client.post("/objects", json={"canvasId": cid, "objectType": "NOTE",
                                           "title": "existing", "x": 0, "y": 0}).json()
    p = client.post("/proposals", json={
        "canvasId": cid, "proposalType": "CREATE_OBJECT",
        "payload": {"objectType": "NOTE", "title": "proposed", "content": {}, "x": 1, "y": 1},
        "reason": "because",
    }).json()
    assert p["status"] == "PENDING"

    # Still pending, so nothing was created by the proposal itself.
    pending = client.get(f"/proposals?canvasId={cid}").json()["proposals"]
    assert len(pending) == 1
    assert before["object"]["id"]

    accepted = client.post(f"/proposals/{p['id']}/accept").json()
    assert accepted["status"] == "ACCEPTED"
    assert len(accepted["createdIds"]) == 1
    assert client.get(f"/proposals?canvasId={cid}").json()["proposals"] == []


def test_rejected_proposal_creates_nothing(client):
    cid = _canvas(client)
    p = client.post("/proposals", json={
        "canvasId": cid, "proposalType": "CREATE_OBJECT",
        "payload": {"objectType": "NOTE", "title": "nope", "x": 0, "y": 0},
    }).json()
    r = client.post(f"/proposals/{p['id']}/reject").json()
    assert r["status"] == "REJECTED"
    assert r["createdIds"] == []
    assert client.get(f"/proposals?canvasId={cid}").json()["proposals"] == []


def test_proposal_cannot_be_accepted_twice(client):
    cid = _canvas(client)
    p = client.post("/proposals", json={
        "canvasId": cid, "proposalType": "CREATE_OBJECT",
        "payload": {"objectType": "NOTE", "title": "once", "x": 0, "y": 0},
    }).json()
    assert client.post(f"/proposals/{p['id']}/accept").status_code == 200
    assert client.post(f"/proposals/{p['id']}/accept").status_code == 409


# ---- threads ----

def test_thread_becomes_a_node_and_keeps_its_turns(client):
    cid = _canvas(client)
    src = client.post("/objects", json={"canvasId": cid, "objectType": "PAPER",
                                        "title": "Anchor", "content": {"text": "body"},
                                        "x": 0, "y": 0}).json()["object"]
    t = client.post("/threads", json={"canvasId": cid, "objectId": src["id"], "x": 5, "y": 5}).json()
    assert t["object"]["objectType"] == "THREAD"

    client.post("/chat", json={"canvasId": cid, "message": "hello",
                               "selectedObjectIds": [src["id"]], "threadId": t["threadId"]})
    msgs = client.get(f"/threads/{t['threadId']}").json()["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    # The snapshot is what makes an old answer reproducible (PRD §17).
    assert src["id"] in msgs[0]["contextSnapshot"]["objectIds"]


def test_chat_without_a_thread_persists_nothing(client):
    cid = _canvas(client)
    r = client.post("/chat", json={"canvasId": cid, "message": "hi"})
    assert r.status_code == 200


# ---- chunking ----

def test_chunking_packs_paragraphs_instead_of_cutting_blindly():
    body = "\n\n".join(f"Paragraph {i} " + "word " * 120 for i in range(8))
    chunks = chunk_text(body)
    assert len(chunks) > 1
    # Scholarly context survives: no chunk is a stray fragment.
    assert all(len(c) > 200 for c in chunks)
    assert "Paragraph 0" in chunks[0]


def test_chunking_handles_empty_and_short_text():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []
    assert chunk_text("one short line") == ["one short line"]
