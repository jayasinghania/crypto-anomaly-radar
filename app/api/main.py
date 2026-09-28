"""
Phase 4 - API entry point.

Run with: uvicorn app.api.main:app --reload   (from the repo root)
Then open http://127.0.0.1:8000/docs for interactive API documentation,
auto-generated from the route signatures and Pydantic schemas below.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import anomalies, assets, bars, metrics, prices

app = FastAPI(
    title="Crypto Anomaly Radar API",
    description=(
        "Historical prices, aggregated bars, computed rolling-stats "
        "metrics, and flagged anomalies for a tracked basket of crypto "
        "assets."
    ),
    version="0.1.0",
)

# Permissive for local development so the Phase 5 browser dashboard can
# call this API from a different origin without a silent CORS failure.
# Tighten allow_origins before any public deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assets.router)
app.include_router(prices.router)
app.include_router(bars.router)
app.include_router(metrics.router)
app.include_router(anomalies.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"message": "Crypto Anomaly Radar API - see /docs for interactive documentation"}
