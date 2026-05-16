"""AEOS FastAPI application entry point.

S1 骨架：僅暴露 /health 與 /metrics（後者為 S1-4 OBS infra 解鎖前的 placeholder）。
"""

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url=None,
)


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
