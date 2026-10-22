"""Minimal stdlib PNG encoder, with no image library dependency, used to give
/camera/image_*/compressed topics a real, browser-decodable image instead of
a placeholder byte blob labeled as compressed. 8-bit grayscale or RGB only --
enough for this project's synthetic camera frames."""
from __future__ import annotations

import struct
import zlib

_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", zlib.crc32(chunk_type + data))


def encode_png(width: int, height: int, pixels: bytes, channels: int) -> bytes:
    """pixels is raw row-major, top-to-bottom pixel data (no filter bytes,
    no padding) -- channels=3 for 8-bit RGB (PNG color type 2), channels=1
    for 8-bit grayscale (color type 0)."""
    if channels not in (1, 3):
        raise ValueError(f"unsupported channel count: {channels}")
    color_type = 2 if channels == 3 else 0
    stride = width * channels
    if len(pixels) != stride * height:
        raise ValueError(f"expected {stride * height} bytes, got {len(pixels)}")

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # per-scanline filter type: 0 = None
        raw.extend(pixels[y * stride : (y + 1) * stride])

    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    idat = zlib.compress(bytes(raw), level=6)
    return _SIGNATURE + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")
