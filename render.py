"""Render a QR module matrix to PNG (and optional caption) with Pillow."""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def render_png(
    matrix: list[list[bool]],
    path: str,
    scale: int = 10,
    border: int = 4,
    caption: str | None = None,
) -> str:
    """Write ``matrix`` as a PNG at ``path``; returns the path."""
    modules = len(matrix)
    side = (modules + border * 2) * scale

    caption_h = 0
    if caption:
        caption_h = int(scale * 5.2)

    img = Image.new("RGB", (side, side + caption_h), "white")
    draw = ImageDraw.Draw(img)

    for y, row in enumerate(matrix):
        for x, dark in enumerate(row):
            if dark:
                x0 = (x + border) * scale
                y0 = (y + border) * scale
                draw.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill="black")

    if caption:
        font = _font(int(scale * 3.2))
        bbox = draw.textbbox((0, 0), caption, font=font)
        tx = (side - (bbox[2] - bbox[0])) / 2
        ty = side + (caption_h - (bbox[3] - bbox[1])) / 2 - bbox[1]
        draw.text((tx, ty), caption, font=font, fill="#1c1c1c")

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path, optimize=True)
    return path
