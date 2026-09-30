"""
Phase 4/5 - API entry point.

Run with: uvicorn app.api.main:app --reload   (from the repo root)
Then open http://127.0.0.1:8000/docs for interactive API documentation,
or http://127.0.0.1:8000/dashboard/ for the live dashboard.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers import anomalies, assets, bars, metrics, prices, ws
from app.realtime.broadcaster import redis_listener


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One background task, started when the server starts, subscribes to
    # Redis for the lifetime of the process and feeds every connected
    # WebSocket client. Cancelled cleanly on shutdown.
    listener_task = asyncio.create_task(redis_listener())
    yield
    listener_task.cancel()


app = FastAPI(
    title="Crypto Anomaly Radar API",
    description=(
        "Historical prices, aggregated bars, computed rolling-stats "
        "metrics, and flagged anomalies for a tracked basket of crypto "
        "assets."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

# Permissive for local development so the dashboard can call this API
# from a different origin without a silent CORS failure. Tighten
# allow_origins before any public deployment.
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
app.include_router(ws.router)

# Serves app/dashboard/index.html at /dashboard/
app.mount("/dashboard", StaticFiles(directory="app/dashboard", html=True), name="dashboard")


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"message": "Crypto Anomaly Radar API - see /docs for API docs, /dashboard/ for the live dashboard"}
