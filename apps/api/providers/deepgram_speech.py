"""Deepgram speech (sponsor: Deepgram). Implements SpeechProvider.

Optional voice layer: transcribe mic audio for the canvas chat bar, and read AI
explanations aloud. Never on the core research path — if this fails, everything
else still works (PRD §37).
"""
from __future__ import annotations

import os
from typing import Any

STT_MODEL = os.getenv("DEEPGRAM_STT_MODEL", "nova-2")
TTS_MODEL = os.getenv("DEEPGRAM_TTS_MODEL", "aura-asteria-en")


class DeepgramSpeech:
    def __init__(self, api_key: str | None = None) -> None:
        from deepgram import DeepgramClient  # imported lazily; SDK isolated here

        self._dg = DeepgramClient(api_key or os.environ["DEEPGRAM_API_KEY"])

    def transcribe(self, audio: bytes, *, mime: str = "audio/wav") -> str:
        from deepgram import PrerecordedOptions

        res = self._dg.listen.rest.v("1").transcribe_file(
            {"buffer": audio, "mimetype": mime},
            PrerecordedOptions(model=STT_MODEL, smart_format=True, punctuate=True),
        )
        try:
            return res.results.channels[0].alternatives[0].transcript or ""
        except (AttributeError, IndexError):
            return ""

    def synthesize(self, text: str) -> bytes:
        from deepgram import SpeakOptions

        # Keep read-aloud snappy and bounded; long artifacts get truncated.
        res = self._dg.speak.rest.v("1").stream_memory(
            {"text": text[:1800]},
            SpeakOptions(model=TTS_MODEL, encoding="mp3"),
        )
        stream: Any = res.stream
        stream.seek(0)
        return stream.read()
