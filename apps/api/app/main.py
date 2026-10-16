from fastapi import FastAPI

app = FastAPI(
    title="AI Travel Planning Agent API",
    description="Source-aware travel itinerary planning API.",
    version="0.1.0",
)


@app.get("/health", tags=["operations"])
def health_check() -> dict[str, str]:
    """Return a lightweight status check without contacting external providers."""
    return {"status": "ok"}
