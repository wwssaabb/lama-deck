from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

EngineName = Literal["auto", "lama", "opencv"]


class HealthResponse(BaseModel):
    status: str
    version: str
    engine: str
    model: str | None
    device: str
    model_ready: bool
    torch_available: bool
    fallback_reason: str | None


class InpaintOptions(BaseModel):
    engine: EngineName = "auto"
    refine: bool = False
    radius: int = Field(default=3, ge=1, le=30)
    dilate: int = Field(default=2, ge=0, le=10)

    @classmethod
    def from_raw(cls, raw: str | None) -> InpaintOptions:
        if not raw:
            return cls()
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return cls()
        if not isinstance(payload, dict):
            return cls()
        try:
            return cls.model_validate(payload)
        except ValidationError:
            return cls()


class ErrorDetail(BaseModel):
    detail: str
