"""Generate the PWA app icons locally, pure Python stdlib (zlib + struct), no Pillow.

Draws a minimal flat barbell glyph (a horizontal bar with two end plates) on a
solid rounded-square background, at each size manifest.json references, and
writes plain 8-bit RGB PNGs directly via zlib.compress on hand-built scanline
data. No third-party imaging library, no network fetch, no CDN icon service -
keeps the "zero dependency" promise intact for the app's own build tooling,
not just its shipped runtime.

Usage:
    py tools/gen_icons.py
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = REPO_ROOT / "web" / "icons"

SIZES = (192, 512)

# Colors match the app's dark-theme accent (see web/css/styles.css --color-accent
# variants) so the icon reads consistently whether the OS launcher tray is
# light or dark.
BG = (15, 17, 21)       # --color-bg (dark theme)
BAR = (91, 155, 255)    # --color-accent (dark theme)
PLATE = (236, 238, 241)  # --color-text (dark theme), used for the end plates


def _write_png(path: Path, width: int, height: int, pixels: list[tuple[int, int, int]]) -> None:
    """Write a minimal 8-bit RGB (no alpha, no interlace) PNG."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # no filter for this scanline
        for x in range(width):
            r, g, b = pixels[y * width + x]
            raw += bytes((r, g, b))

    idat = zlib.compress(bytes(raw), level=9)

    png = sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    path.write_bytes(png)


def _rounded_square_mask(size: int, radius: int, x: int, y: int) -> bool:
    """True if (x, y) is inside a `size`x`size` square with corner radius `radius`."""
    corners = ((radius, radius), (size - radius - 1, radius), (radius, size - radius - 1),
               (size - radius - 1, size - radius - 1))
    if x < radius and y < radius:
        cx, cy = corners[0]
        return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2
    if x >= size - radius and y < radius:
        cx, cy = corners[1]
        return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2
    if x < radius and y >= size - radius:
        cx, cy = corners[2]
        return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2
    if x >= size - radius and y >= size - radius:
        cx, cy = corners[3]
        return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2
    return True


def _draw_icon(size: int) -> list[tuple[int, int, int]]:
    pixels = [BG] * (size * size)
    radius = size // 8

    # Barbell: a horizontal bar across the vertical center, with a thicker
    # plate block near each end. All proportions are fractions of `size` so
    # every generated resolution looks the same.
    bar_half_h = max(2, size // 24)
    bar_y0, bar_y1 = size // 2 - bar_half_h, size // 2 + bar_half_h

    plate_w = size // 7
    plate_half_h = size // 4
    plate_y0, plate_y1 = size // 2 - plate_half_h, size // 2 + plate_half_h
    margin = size // 6
    left_plate_x0, left_plate_x1 = margin, margin + plate_w
    right_plate_x0, right_plate_x1 = size - margin - plate_w, size - margin

    for y in range(size):
        for x in range(size):
            if not _rounded_square_mask(size, radius, x, y):
                continue
            idx = y * size + x
            on_bar = bar_y0 <= y < bar_y1 and left_plate_x1 <= x < right_plate_x0
            on_left_plate = plate_y0 <= y < plate_y1 and left_plate_x0 <= x < left_plate_x1
            on_right_plate = plate_y0 <= y < plate_y1 and right_plate_x0 <= x < right_plate_x1
            if on_left_plate or on_right_plate:
                pixels[idx] = PLATE
            elif on_bar:
                pixels[idx] = BAR
    return pixels


def main() -> int:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        pixels = _draw_icon(size)
        out_path = ICONS_DIR / f"icon-{size}.png"
        _write_png(out_path, size, size, pixels)
        print(f"wrote {out_path.relative_to(REPO_ROOT)} ({size}x{size})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
