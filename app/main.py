"""AEOS FastAPI application entry point.

S1 骨架 + S2 webhook + Expert Console + KC Review + Prometheus 量測。
"""

from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.api.admin import router as admin_router
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
app.include_router(expert_router)
app.include_router(kc_router)
app.include_router(admin_router)
app.include_router(testset_router)

# Prometheus instrumentation — auto HTTP histogram + per-handler labels
instrument_app(app)
register_app_info(version=settings.app_version, env=settings.app_env)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env, "version": settings.app_version}


@app.get("/metrics", tags=["meta"], include_in_schema=False)
async def metrics() -> Response:
    """Prometheus scrape 端點 — 暴露所有 default registry counter/histogram."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
