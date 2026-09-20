"""Voice routes. The stub SpeechProvider stands in for Deepgram, so these
run with no credentials."""


def test_speech_transcribe(client):
    r = client.post("/speech/transcribe", files={"audio": ("a.wav", b"xx", "audio/wav")})
    assert r.status_code == 200
    assert "text" in r.json()


def test_speech_synthesize_returns_audio(client):
    r = client.post("/speech/synthesize", json={"text": "hello"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
