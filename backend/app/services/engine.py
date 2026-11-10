from __future__ import annotations

import logging

from PIL import Image

from ..config import Settings
from ..schemas import InpaintOptions
from . import lama_service, opencv_service

logger = logging.getLogger(__name__)


def resolve(requested: str, settings: Settings) -> tuple[str, str | None]:
    effective = settings.default_engine if requested == "auto" else requested
    if effective == "opencv":
        return "opencv", None
    reason = lama_service.unavailable_reason(settings)
    if reason is None:
        return "lama", None
    return "opencv", reason


def run(
    image: Image.Image,
    mask: Image.Image,
    options: InpaintOptions,
    settings: Settings,
) -> tuple[Image.Image, str, str | None]:
    engine, reason = resolve(options.engine, settings)
    hole = opencv_service.dilate_mask(mask, options.dilate) if options.dilate else mask
    if engine == "lama":
        try:
            result = lama_service.inpaint(image, hole, settings)
        except Exception as exc:
            logger.exception("lama inference failed, falling back to opencv")
            engine = "opencv"
            reason = f"LaMa 推理失败，已降级: {exc}"
            result = opencv_service.inpaint(image, hole, options.radius)
    else:
        result = opencv_service.inpaint(image, hole, options.radius)

    if options.refine:
        result = opencv_service.refine_seams(result, hole, radius=2)
    return result, engine, reason
