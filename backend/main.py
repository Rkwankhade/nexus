"""
NEXUS — FastAPI application entry point.

Phase 1 wires up: app factory, CORS, lifespan (DB/Redis/Neo4j),
global exception handlers, and health check. Routers are mounted
here as they're built out in Phase 2.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.database import close_db
from core.neo4j_client import neo4j_client
from core.redis_client import redis_client

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("nexus")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NEXUS starting up — env=%s", settings.APP_ENV)
    yield
app = FastAPI(
    title="NEXUS API",
    description="AI-Powered Cyber Operations Platform — recon, scan, defend, forensics, report",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["health"])
async def health_check():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/api/health", tags=["system"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
    }


# ── Routers (mounted incrementally as they are built — Phase 2) ──
from routers import auth  # noqa: E402
from routers import users  # noqa: E402
from routers import targets  # noqa: E402
from routers import scans  # noqa: E402
from routers import findings  # noqa: E402
from routers import exploits  # noqa: E402
from routers import ai  # noqa: E402
from routers import reports  # noqa: E402
from routers import alerts  # noqa: E402
from routers import blueteam  # noqa: E402
from routers import forensics  # noqa: E402
from routers import wireless  # noqa: E402
from routers import websocket  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(targets.router, prefix="/api/targets", tags=["targets"])
app.include_router(scans.router, prefix="/api/scans", tags=["scans"])
app.include_router(findings.router, prefix="/api/findings", tags=["findings"])
app.include_router(exploits.router, prefix="/api/exploits", tags=["exploits"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(blueteam.router, prefix="/api/blueteam", tags=["blueteam"])
app.include_router(forensics.router, prefix="/api/forensics", tags=["forensics"])
app.include_router(wireless.router, prefix="/api/wireless", tags=["wireless"])
app.include_router(websocket.router, tags=["websocket"])
