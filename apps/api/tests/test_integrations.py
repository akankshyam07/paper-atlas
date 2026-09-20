"""Dropbox import and voice routes. The stub FileSourceProvider stands in for
Dropbox, so these run with no credentials."""


def test_dropbox_list(client):
    r = client.get("/integrations/dropbox/files")
    assert r.status_code == 200
    assert len(r.json()["files"]) >= 1


def test_dropbox_import_ingests_a_real_object(client):
    import uuid
    canvas = str(uuid.uuid4())
    r = client.post("/integrations/dropbox/import", json={
        "canvasId": canvas, "fileId": "stub-1", "x": 10, "y": 20,
    })
    assert r.status_code == 200
    obj = r.json()["object"]
    # Went through service.ingest_file, so it is a persisted PDF object that
    # deduped to a source entity — not a fabricated stub response.
    assert obj["objectType"] == "PDF"
    assert obj["sourceEntityId"], "import must dedupe to a canonical source entity"
    assert obj["content"]["origin"] == "dropbox"
    assert obj["content"]["sizeBytes"] > 0
    assert obj["x"] == 10


def test_dropbox_import_dedupes_same_file(client):
    import uuid
    canvas = str(uuid.uuid4())
    body = {"canvasId": canvas, "fileId": "stub-1", "x": 0, "y": 0}
    a = client.post("/integrations/dropbox/import", json=body).json()["object"]
    b = client.post("/integrations/dropbox/import", json=body).json()["object"]
    assert a["id"] != b["id"], "each import is its own canvas placement"
    assert a["sourceEntityId"] == b["sourceEntityId"], "but one canonical source"


def test_speech_transcribe(client):
    r = client.post("/speech/transcribe", files={"audio": ("a.wav", b"xx", "audio/wav")})
    assert r.status_code == 200
    assert "text" in r.json()


def test_speech_synthesize_returns_audio(client):
    r = client.post("/speech/synthesize", json={"text": "hello"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
