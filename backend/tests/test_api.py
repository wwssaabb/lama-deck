from __future__ import annotations

import io
import os

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

os.environ["LAMA_ENGINE"] = "opencv"

from app.main import app  # noqa: E402

client = TestClient(app)


def image_bytes(width: int = 64, height: int = 48, fmt: str = "PNG") -> bytes:
    img = Image.new("RGB", (width, height))
    px = img.load()
    for y in range(height):
        for x in range(width):
            px[x, y] = (x * 4 % 256, y * 5 % 256, (x + y) * 3 % 256)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def noisy_image_bytes(width: int = 1200, height: int = 900) -> bytes:
    img = Image.frombytes("RGB", (width, height), os.urandom(width * height * 3))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def mask_bytes(width: int = 64, height: int = 48, box=(10, 10, 40, 30), fmt: str = "PNG") -> bytes:
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rectangle(box, fill=255)
    buf = io.BytesIO()
    mask.save(buf, format=fmt)
    return buf.getvalue()


def post_inpaint(image: bytes, mask: bytes, options: str | None = None):
    return client.post(
        "/api/inpaint",
        files={
            "image": ("image.png", image, "image/png"),
            "mask": ("mask.png", mask, "image/png"),
        },
        data={"options": options} if options else {},
    )


def test_health_shape():
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    for key in (
        "status",
        "version",
        "engine",
        "model",
        "device",
        "model_ready",
        "torch_available",
        "fallback_reason",
    ):
        assert key in body
    assert body["status"] == "ok"
    assert body["engine"] in {"lama", "opencv"}
    assert isinstance(body["torch_available"], bool)


def test_inpaint_success():
    res = post_inpaint(image_bytes(), mask_bytes())
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert res.headers["x-inpaint-engine"] == "opencv"
    assert int(res.headers["x-inpaint-ms"]) >= 0
    with Image.open(io.BytesIO(res.content)) as out:
        assert out.size == (64, 48)
        assert out.mode == "RGB"


def test_inpaint_changes_masked_area():
    res = post_inpaint(image_bytes(), mask_bytes(box=(0, 0, 64, 48)))
    assert res.status_code == 200
    with Image.open(io.BytesIO(res.content)) as out:
        assert out.size == (64, 48)


def test_refine_option():
    res = post_inpaint(image_bytes(), mask_bytes(), '{"refine": true, "radius": 5}')
    assert res.status_code == 200
    assert res.headers["x-inpaint-engine"] == "opencv"


def test_dilate_option():
    res = post_inpaint(image_bytes(), mask_bytes(box=(20, 15, 30, 25)), '{"dilate": 6}')
    assert res.status_code == 200
    res = post_inpaint(image_bytes(), mask_bytes(), '{"dilate": 0}')
    assert res.status_code == 200


def test_invalid_options_json_falls_back_to_defaults():
    res = post_inpaint(image_bytes(), mask_bytes(), "not-json{")
    assert res.status_code == 200


def test_mask_size_mismatch():
    res = post_inpaint(image_bytes(64, 48), mask_bytes(32, 32, box=(0, 0, 10, 10)))
    assert res.status_code == 400
    assert res.json()["detail"].startswith("mask 尺寸与图片不一致")


def test_mask_must_be_png():
    res = post_inpaint(image_bytes(), mask_bytes(fmt="JPEG"))
    assert res.status_code == 422
    assert "PNG" in res.json()["detail"]


def test_empty_image_rejected():
    res = post_inpaint(b"", mask_bytes())
    assert res.status_code == 422


def test_missing_field_rejected():
    res = client.post(
        "/api/inpaint",
        files={"image": ("image.png", image_bytes(), "image/png")},
    )
    assert res.status_code == 422


def test_max_side_limit(monkeypatch):
    monkeypatch.setenv("MAX_SIDE", "32")
    res = post_inpaint(image_bytes(64, 48), mask_bytes(64, 48))
    assert res.status_code == 413
    assert "最长边" in res.json()["detail"]


def test_max_bytes_limit(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    res = post_inpaint(noisy_image_bytes(), mask_bytes(1200, 900))
    assert res.status_code == 413
    assert "大小上限" in res.json()["detail"]
