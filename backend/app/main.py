"""FastAPI entry point for the ControlPlane.ai prototype."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.database import SessionLocal, init_db
from app.services.seed import seed_core


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        seed_core(db)
    yield


app = FastAPI(
    title="ControlPlane.ai Runtime API",
    description="Model-independent AI response risk evaluation, policy enforcement, review, and audit runtime.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api/v1")


@app.get("/health")
def root_health() -> dict[str, object]:
    return {"status": "healthy", "demo_mode": settings.demo_mode}
