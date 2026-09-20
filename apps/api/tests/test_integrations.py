def test_dropbox_list(client):
    r = client.get("/integrations/dropbox/files")
    assert r.status_code == 200
    assert len(r.json()["files"]) >= 1


def test_dropbox_import_places_object(client):
    r = client.post("/integrations/dropbox/import", json={
        "canvasId": "c1", "fileId": "stub-1", "x": 10, "y": 20,
    })
    assert r.status_code == 200
    obj = r.json()["object"]
    assert obj["content"]["origin"] == "dropbox"
    assert obj["x"] == 10


def test_speech_transcribe(client):
    r = client.post("/speech/transcribe", files={"audio": ("a.wav", b"xx", "audio/wav")})
    assert r.status_code == 200
    assert "text" in r.json()


def test_speech_synthesize_returns_audio(client):
    r = client.post("/speech/synthesize", json={"text": "hello"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
