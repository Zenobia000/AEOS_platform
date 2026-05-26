"""AEOS FastAPI application entry point.

S1 骨架 + S2 webhook + Expert Console + KC Review + Prometheus 量測。
"""

from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.api.admin import router as admin_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.expert import router as expert_router
from app.api.kc import router as kc_router
from app.api.testset import router as testset_router
from app.api.webhooks import line_router
from app.config import get_settings
from app.observability import instrument_app, register_app_info

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url=None,
)

app.include_router(line_router)
app.include_router(auth_router)
app.include_router(expert_router)
app.include_router(kc_router)
app.include_router(admin_router)
app.include_router(testset_router)
app.include_router(audit_router)

# Prometheus instrumentation — auto HTTP histogram + per-handler labels
instrument_app(app)
register_app_info(version=settings.app_version, env=settings.app_env)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Lightweight liveness — 不查 DB。給 docker healthcheck / LB 用。"""
    return {"status": "ok", "env": settings.app_env, "version": settings.app_version}


@app.get("/health/ready", tags=["meta"])
async def health_ready() -> dict[str, object]:
    """Readiness — 含 DB ping。失敗時回 503。給 k8s readiness probe 用。"""
    from fastapi import HTTPException
    from sqlalchemy import text as _text

    from app.db.session import session_scope

    checks: dict[str, str] = {"app": "ok"}
    try:
        async with session_scope() as session:
            result = await session.execute(_text("SELECT 1"))
            _ = result.scalar()
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"fail: {type(exc).__name__}"
        raise HTTPException(status_code=503, detail=checks) from exc
    return {"status": "ready", "checks": checks, "version": settings.app_version}


@app.get("/metrics", tags=["meta"], include_in_schema=False)
async def metrics() -> Response:
    """Prometheus scrape 端點 — 暴露所有 default registry counter/histogram."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
