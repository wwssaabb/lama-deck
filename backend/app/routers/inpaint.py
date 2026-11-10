from __future__ import annotations

import io
import logging
import time

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from starlette.concurrency import run_in_threadpool

from ..config import Settings, get_settings
from ..schemas import InpaintOptions
from ..services import engine, image_utils
from ..services.image_utils import PayloadError

logger = logging.getLogger(__name__)

router = APIRouter()


def _pipeline(image_bytes: bytes, mask_bytes: bytes, options: InpaintOptions, settings: Settings):
    source = image_utils.decode_image(
        image_bytes, max_bytes=settings.max_upload_bytes, max_side=settings.max_side
    )
    mask = image_utils.decode_mask(mask_bytes, source.size)
    return engine.run(source, mask, options, settings)


@router.post("/inpaint")
async def inpaint(
    image: UploadFile = File(...),
    mask: UploadFile = File(...),
    options: str | None = Form(None),
) -> Response:
    settings = get_settings()
    started = time.perf_counter()
    try:
        image_bytes = await image_utils.read_limited(image, settings.max_upload_bytes)
        mask_bytes = await image_utils.read_limited(mask, settings.max_upload_bytes)
    except PayloadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    parsed = InpaintOptions.from_raw(options)
    try:
        result, engine_name, _ = await run_in_threadpool(
            _pipeline, image_bytes, mask_bytes, parsed, settings
        )
    except PayloadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    buffer = io.BytesIO()
    result.save(buffer, format="PNG")
    elapsed = int((time.perf_counter() - started) * 1000)
    logger.info("inpaint done engine=%s size=%s ms=%d", engine_name, result.size, elapsed)
    return Response(
        content=buffer.getvalue(),
        media_type="image/png",
        headers={
            "X-Inpaint-Engine": engine_name,
            "X-Inpaint-Ms": str(elapsed),
            "Content-Disposition": 'inline; filename="inpainted.png"',
        },
    )
