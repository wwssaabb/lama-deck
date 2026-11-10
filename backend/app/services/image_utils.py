from __future__ import annotations

import io

from PIL import Image, ImageOps, UnidentifiedImageError

SUPPORTED_IMAGE_FORMATS = {"PNG", "JPEG", "WEBP"}


class PayloadError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


async def read_limited(file, limit: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1 << 20)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise PayloadError(413, f"上传内容超过大小上限 {limit // (1024 * 1024)}MB")
        chunks.append(chunk)
    return b"".join(chunks)


def decode_image(data: bytes, *, max_bytes: int, max_side: int) -> Image.Image:
    if not data:
        raise PayloadError(422, "图片内容为空")
    if len(data) > max_bytes:
        raise PayloadError(413, f"图片超过大小上限 {max_bytes // (1024 * 1024)}MB")
    try:
        with Image.open(io.BytesIO(data)) as opened:
            fmt = (opened.format or "").upper()
            if fmt not in SUPPORTED_IMAGE_FORMATS:
                raise PayloadError(422, f"不支持的图片格式: {fmt or 'unknown'}，仅支持 PNG/JPEG/WEBP")
            opened.load()
            image = ImageOps.exif_transpose(opened).convert("RGB")
    except PayloadError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise PayloadError(422, "图片解码失败")
    if max(image.size) > max_side:
        raise PayloadError(413, f"图片最长边超过上限 {max_side}px（当前 {max(image.size)}px）")
    return image


def decode_mask(data: bytes, size: tuple[int, int]) -> Image.Image:
    if not data:
        raise PayloadError(422, "遮罩内容为空")
    try:
        with Image.open(io.BytesIO(data)) as opened:
            fmt = (opened.format or "").upper()
            if fmt != "PNG":
                raise PayloadError(422, "遮罩必须是 PNG 格式")
            opened.load()
            if opened.mode == "RGBA" and opened.getchannel("A").getextrema()[0] < 255:
                mask = opened.getchannel("A")
            else:
                mask = opened.convert("L")
    except PayloadError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise PayloadError(422, "遮罩解码失败")
    if mask.size != size:
        raise PayloadError(
            400,
            f"mask 尺寸与图片不一致: mask={mask.size[0]}x{mask.size[1]}, image={size[0]}x{size[1]}",
        )
    return mask.point(lambda p: 255 if p >= 128 else 0, mode="L")
