import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.db.postgres import close_db, init_db
from app.db.redis_client import close_redis, get_redis_client, init_redis
from app.routers import admin, availability, dcs, items, orders

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    await init_db()
    await init_redis()
    logger.info(
        "startup complete",
        app=settings.APP_NAME,
        env=settings.APP_ENV,
        db="ready",
        redis="ready",
    )
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────────
    await close_db()
    await close_redis()
    logger.info("shutdown complete", app=settings.APP_NAME)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Local Delivery API",
        description="GoPuff-inspired local delivery system design demo",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request timing middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        elapsed = round((time.monotonic() - start) * 1000, 2)
        response.headers["X-Process-Time"] = f"{elapsed}ms"
        return response

    # ── Health endpoint ───────────────────────────────────────────────────────
    @app.get("/health", tags=["health"])
    async def health_check():
        from sqlalchemy import text

        from app.db.postgres import write_engine

        postgres_ok = False
        redis_ok = False

        try:
            async with write_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            postgres_ok = True
        except Exception as exc:
            logger.warning("postgres health check failed", error=str(exc))

        try:
            redis = get_redis_client()
            await redis.ping()
            redis_ok = True
        except Exception as exc:
            logger.warning("redis health check failed", error=str(exc))

        status = "ok" if (postgres_ok and redis_ok) else "degraded"
        code = 200 if status == "ok" else 503
        return JSONResponse(
            status_code=code,
            content={
                "status": status,
                "postgres": "ok" if postgres_ok else "error",
                "redis": "ok" if redis_ok else "error",
            },
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(availability.router, prefix="/api/v1/availability", tags=["availability"])
    app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
    app.include_router(dcs.router, prefix="/api/v1/dcs", tags=["distribution-centers"])
    app.include_router(items.router, prefix="/api/v1/items", tags=["items"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

    return app


app = create_app()
