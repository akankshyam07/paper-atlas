"""Paper Atlas API. Registers the four demo endpoints across two lanes.

Stub responses ship on `main` so the frontend can develop immediately and the
demo build always runs. Each lane replaces its own stubs with real logic on its
branch (backend-data: canvas/, backend-ai: intel/).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from canvas.routes import router as canvas_router
from intel.routes import router as intel_router

app = FastAPI(title="Paper Atlas API")

# ponytail: wide-open CORS for local dev; lock to the web origin before any deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(canvas_router)
app.include_router(intel_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
