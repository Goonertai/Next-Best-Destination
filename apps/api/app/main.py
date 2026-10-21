import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.itineraries import router as itineraries_router

app = FastAPI(
    title="AI Travel Planning Agent API",
    description="Source-aware travel itinerary planning API.",
    version="0.1.0",
)
allowed_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(itineraries_router)


@app.get("/health", tags=["operations"])
def health_check() -> dict[str, str]:
    """Return a lightweight status check without contacting external providers."""
    return {"status": "ok"}
