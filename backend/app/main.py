from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .routers import inpaint as inpaint_router
from .schemas import HealthResponse
from .services import lama_service

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="LaMa Studio API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inpaint_router.router, prefix="/api")


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "lama-studio",
        "health": "/api/health",
        "inpaint": "POST /api/inpaint",
        "docs": "/docs",
    }


@app.get("/api/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    settings = get_settings()
    reason = lama_service.unavailable_reason(settings)
    torch_ok = lama_service.torch_available()

    if settings.default_engine == "opencv":
        engine_name, fallback = "opencv", None
    elif reason is None:
        engine_name, fallback = "lama", None
    else:
        engine_name, fallback = "opencv", reason

    return HealthResponse(
        status="ok",
        version=settings.version,
        engine=engine_name,
        model="big-lama" if engine_name == "lama" else None,
        device=lama_service.effective_device(settings.device) if torch_ok else "cpu",
        model_ready=engine_name == "lama",
        torch_available=torch_ok,
        fallback_reason=fallback,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": f"服务器内部错误: {exc}"})
