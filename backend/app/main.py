from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import Base, engine

# Import all models so SQLAlchemy knows about them.
import app.models

from app.api.reports import router as reports_router
from app.api.analytics import router as analytics_router
from app.api.datasets import router as datasets_router
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.

    On startup:
    - enable pgvector
    - create missing database tables

    On shutdown:
    - release application lifecycle cleanly
    """

    with engine.begin() as connection:
        connection.execute(
            text("CREATE EXTENSION IF NOT EXISTS vector")
        )

        Base.metadata.create_all(
            bind=connection
        )

    yield


app = FastAPI(
    title="SIFSentinel API",
    description=(
        "Serious Injury & Fatality Precursor "
        "Intelligence System"
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

app.include_router(
    reports_router
)

app.include_router(
    analytics_router
)

app.include_router(
    datasets_router
)

# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get(
    "/health",
    tags=["default"],
)
def health():
    return {
        "status": "ok",
        "service": "sifsentinel-api",
    }