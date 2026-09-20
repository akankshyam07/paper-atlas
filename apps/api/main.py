"""Paper Atlas API. Registers the four demo endpoints across two lanes.

Stub responses ship on `main` so the frontend can develop immediately and the
demo build always runs. Each lane replaces its own stubs with real logic on its
branch (backend-data: canvas/, backend-ai: intel/).
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from canvas.routes import router as canvas_router
from concepts.routes import router as concepts_router
from embeds.routes import router as embeds_router
from files.routes import router as files_router
from intel.routes import router as intel_router
from speech.routes import router as speech_router

app = FastAPI(title="Paper Atlas API")

# Allow only the web app's origins. CORS_ORIGINS overrides for deploys; the
# defaults cover local development. Never widen this to "*" — with credentials
# enabled a wildcard would let any site call the API as the signed-in user.
CORS_ORIGINS = [
    o.strip() for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(canvas_router)
app.include_router(files_router)
app.include_router(embeds_router)
app.include_router(concepts_router)
app.include_router(intel_router)
app.include_router(speech_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/inference/stats")
def inference_stats() -> dict[str, object]:
    """LLM token savings from the inference optimizer (Token Company challenge).
    Reports what the optimization layer actually saved this process."""
    from providers.registry import get_llm, get_inference_optimizer

    optimizer = get_inference_optimizer()
    stats = optimizer.stats() if hasattr(optimizer, "stats") else {}
    return {
        "optimizer": type(optimizer).__name__,
        "llm": type(get_llm()).__name__,
        **stats,
    }
