from __future__ import annotations

import importlib.util
import logging
import os
import threading
from typing import Any

from PIL import Image

from ..config import Settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_instance: Any = None
_load_error: str | None = None
_loaded_device: str | None = None


def torch_available() -> bool:
    return importlib.util.find_spec("torch") is not None


def lama_package_available() -> bool:
    return importlib.util.find_spec("simple_lama_inpainting") is not None


def unavailable_reason(settings: Settings) -> str | None:
    if not torch_available():
        return "torch 未安装（pip install -r requirements-lama.txt）"
    if not lama_package_available():
        return "simple-lama-inpainting 未安装"
    if settings.model_path and not os.path.exists(settings.model_path):
        return f"LaMa 权重不存在: {settings.model_path}（运行 scripts/download_model.ps1）"
    if _load_error:
        return _load_error
    return None


def is_loaded() -> bool:
    return _instance is not None


def effective_device(preference: str) -> str:
    if not torch_available():
        return "cpu"
    if preference == "cpu":
        return "cpu"
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _configure_env(settings: Settings) -> None:
    if settings.model_path:
        os.environ["LAMA_MODEL"] = settings.model_path
    if settings.model_url:
        os.environ.setdefault("LAMA_MODEL_URL", settings.model_url)


def _get_instance(settings: Settings):
    global _instance, _load_error, _loaded_device
    with _lock:
        if _instance is not None:
            return _instance
        if _load_error:
            raise RuntimeError(_load_error)
        try:
            import torch
            from simple_lama_inpainting import SimpleLama

            _configure_env(settings)
            device = torch.device(effective_device(settings.device))
            _instance = SimpleLama(device=device)
            _loaded_device = str(device)
            logger.info("LaMa model loaded on %s", _loaded_device)
            return _instance
        except Exception as exc:
            _load_error = f"LaMa 模型加载失败: {exc}"
            logger.exception("failed to load LaMa model")
            raise RuntimeError(_load_error) from exc


def inpaint(image: Image.Image, mask: Image.Image, settings: Settings) -> Image.Image:
    model = _get_instance(settings)
    result = model(image.convert("RGB"), mask.convert("L"))
    if not isinstance(result, Image.Image):
        result = Image.fromarray(result)
    if result.size != image.size:
        result = result.resize(image.size, Image.Resampling.LANCZOS)
    return result.convert("RGB")


def loaded_device() -> str | None:
    return _loaded_device
