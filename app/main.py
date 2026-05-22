"""AEOS FastAPI application entry point.

S1 骨架 + S2 webhook：暴露 /health, /metrics + /api/v1/webhooks/line/{channel_id}。
"""

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.api.expert import router as expert_router
from app.api.kc import router as kc_router
from app.api.webhooks import line_router
from app.config import get_settings

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


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env, "version": settings.app_version}


@app.get("/metrics", response_class=PlainTextResponse, tags=["meta"])
async def metrics() -> str:
    return (
        "# placeholder until OBS-001 W1 (Prometheus instrumentation) lands\n"
        "# see docs/2-contracts/OBS-001-observability-spec.md\n"
        "aeos_build_info 1\n"
    )
