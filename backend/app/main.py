"""FastAPI entry point for the AeroOps AI Day 1 milestone."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Airport
from app.routers import audit, demo, disruptions, health
from app.seed import seed_demo_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        airport_count = db.scalar(select(func.count()).select_from(Airport)) or 0
        if airport_count == 0:
            seed_demo_data(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Portfolio-only decision-support demonstration using a fictional airline "
        "and synthetic passenger data."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health.router)
app.include_router(demo.router)
app.include_router(disruptions.router)
app.include_router(audit.router)

