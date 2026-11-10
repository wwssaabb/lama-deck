import argparse
import io
import sys
import time

import httpx
from PIL import Image, ImageDraw


def build_image(width: int = 320, height: int = 240) -> tuple[bytes, bytes]:
    img = Image.new("RGB", (width, height))
    px = img.load()
    for y in range(height):
        for x in range(width):
            px[x, y] = (60 + x * 120 // width, 90 + y * 100 // height, 150)
    draw = ImageDraw.Draw(img)
    draw.rectangle((120, 80, 200, 160), fill=(240, 60, 60))
    draw.ellipse((60, 150, 110, 200), fill=(250, 220, 60))

    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rectangle((115, 75, 205, 165), fill=255)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    buf = io.BytesIO()
    mask.save(buf, format="PNG")
    return image_bytes, buf.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--engine", default="auto")
    parser.add_argument("--out", default="inpainted.png")
    args = parser.parse_args()

    with httpx.Client(base_url=args.base, timeout=300.0) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        print("health:", health.json())

        image_bytes, mask_bytes = build_image()
        files = {
            "image": ("sample.png", image_bytes, "image/png"),
            "mask": ("mask.png", mask_bytes, "image/png"),
        }
        data = {"options": f'{{"engine": "{args.engine}", "refine": true, "radius": 3}}'}

        started = time.perf_counter()
        res = client.post("/api/inpaint", files=files, data=data)
        elapsed = time.perf_counter() - started
        if res.status_code != 200:
            print("FAILED", res.status_code, res.text[:500])
            return 1

        with open(args.out, "wb") as fh:
            fh.write(res.content)

        result = Image.open(io.BytesIO(res.content))
        source = Image.open(io.BytesIO(image_bytes))
        print(
            f"engine={res.headers.get('x-inpaint-engine')} "
            f"server_ms={res.headers.get('x-inpaint-ms')} "
            f"client_s={elapsed:.2f} "
            f"size={result.size} saved={args.out}"
        )
        if result.size != source.size:
            print("FAILED: size mismatch")
            return 1
        print("OK")
        return 0


if __name__ == "__main__":
    sys.exit(main())
