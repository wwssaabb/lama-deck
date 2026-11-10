from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ENGINES = ("auto", "lama", "opencv")
DEVICES = ("auto", "cpu", "cuda")

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "big-lama.pt"


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _choice_env(name: str, choices: tuple[str, ...], default: str) -> str:
    raw = os.environ.get(name, "").strip().lower()
    return raw if raw in choices else default


@dataclass(frozen=True)
class Settings:
    version: str
    default_engine: str
    device: str
    max_upload_mb: int
    max_side: int
    model_path: str | None
    model_url: str | None
    host: str
    port: int

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def get_settings() -> Settings:
    model_path = os.environ.get("LAMA_MODEL", "").strip() or None
    if model_path is None and DEFAULT_MODEL_PATH.exists():
        model_path = str(DEFAULT_MODEL_PATH)
    return Settings(
        version="0.1.0",
        default_engine=_choice_env("LAMA_ENGINE", ENGINES, "auto"),
        device=_choice_env("LAMA_DEVICE", DEVICES, "auto"),
        max_upload_mb=_int_env("MAX_UPLOAD_MB", 25),
        max_side=_int_env("MAX_SIDE", 4096),
        model_path=model_path,
        model_url=os.environ.get("LAMA_MODEL_URL", "").strip() or None,
        host=os.environ.get("HOST", "127.0.0.1").strip() or "127.0.0.1",
        port=_int_env("PORT", 8000),
    )
