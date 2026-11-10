from __future__ import annotations

import cv2
import numpy as np
from PIL import Image


def dilate_mask(mask: Image.Image, pixels: int) -> Image.Image:
    if pixels <= 0:
        return mask
    arr = (np.asarray(mask, dtype=np.uint8) > 0).astype(np.uint8) * 255
    kernel = np.ones((pixels * 2 + 1, pixels * 2 + 1), np.uint8)
    grown = cv2.dilate(arr, kernel, iterations=1)
    return Image.fromarray(grown)


def inpaint(image: Image.Image, mask: Image.Image, radius: int = 3) -> Image.Image:
    arr = np.asarray(image.convert("RGB"), dtype=np.uint8)
    hole = (np.asarray(mask, dtype=np.uint8) > 0).astype(np.uint8) * 255
    if not hole.any():
        return image.convert("RGB").copy()
    r = int(np.clip(radius, 1, 30))
    filled = cv2.inpaint(arr, hole, r, cv2.INPAINT_TELEA)
    return Image.fromarray(filled)


def refine_seams(image: Image.Image, mask: Image.Image, radius: int = 2) -> Image.Image:
    arr = np.asarray(image.convert("RGB"), dtype=np.uint8)
    hole = (np.asarray(mask, dtype=np.uint8) > 0).astype(np.uint8) * 255
    if not hole.any():
        return image.convert("RGB").copy()
    r = int(np.clip(radius, 1, 30))
    outer = cv2.dilate(hole, np.ones((5, 5), np.uint8), iterations=1)
    ring = np.where((outer > 0) & (hole == 0), 255, 0).astype(np.uint8)
    if not ring.any():
        return image.convert("RGB")
    smoothed = cv2.inpaint(arr, ring, r, cv2.INPAINT_TELEA)
    alpha = cv2.GaussianBlur(ring.astype(np.float32) / 255.0, (0, 0), sigmaX=2.0)
    alpha = np.clip(alpha, 0.0, 1.0)[..., None]
    blended = arr.astype(np.float32) * (1.0 - alpha) + smoothed.astype(np.float32) * alpha
    return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8))
