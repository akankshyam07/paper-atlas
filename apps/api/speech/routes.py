"""Voice layer (SpeechProvider, optional). Owner: backend-ai.

Transcribe mic audio for the chat bar; synthesize AI artifacts for read-aloud.
Deepgram SDK isolated in providers/deepgram_speech.py; here we only call the
interface. Off the core research path (PRD §17).
"""
from fastapi import APIRouter, UploadFile
from fastapi.responses import Response

from providers.registry import get_speech
from schemas import TranscribeResponse, SynthesizeRequest

router = APIRouter(prefix="/speech")


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(audio: UploadFile) -> TranscribeResponse:
    data = await audio.read()
    return TranscribeResponse(text=get_speech().transcribe(data, mime=audio.content_type or "audio/wav"))


@router.post("/synthesize")
def synthesize(req: SynthesizeRequest) -> Response:
    return Response(content=get_speech().synthesize(req.text), media_type="audio/mpeg")
