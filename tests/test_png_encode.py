import struct
import zlib

from ros2_sim.png_encode import encode_png


def test_png_has_valid_signature_and_ihdr():
    width, height = 4, 3
    pixels = bytes(range(width * height * 3))  # 3 channels (rgb8)
    png = encode_png(width, height, pixels, channels=3)

    assert png[:8] == b"\x89PNG\r\n\x1a\n"

    ihdr_len = struct.unpack(">I", png[8:12])[0]
    assert png[12:16] == b"IHDR"
    ihdr_data = png[16 : 16 + ihdr_len]
    w, h, bit_depth, color_type = struct.unpack(">IIBB", ihdr_data[:10])
    assert (w, h, bit_depth, color_type) == (width, height, 8, 2)  # color type 2 = RGB

    assert png.endswith(b"IEND" + struct.pack(">I", zlib.crc32(b"IEND")))


def test_png_grayscale_color_type_and_roundtrip_via_zlib():
    width, height = 2, 2
    pixels = bytes([10, 20, 30, 40])  # 1 channel (mono8)
    png = encode_png(width, height, pixels, channels=1)

    ihdr_len = struct.unpack(">I", png[8:12])[0]
    ihdr_data = png[16 : 16 + ihdr_len]
    color_type = ihdr_data[9]
    assert color_type == 0  # grayscale

    idat_start = 16 + ihdr_len + 4  # skip IHDR data + its CRC
    idat_len = struct.unpack(">I", png[idat_start : idat_start + 4])[0]
    idat_data = png[idat_start + 8 : idat_start + 8 + idat_len]
    raw = zlib.decompress(idat_data)

    # each scanline is a filter-type byte (0) followed by width*channels pixel bytes
    stride = width * 1
    expected = bytearray()
    for y in range(height):
        expected.append(0)
        expected.extend(pixels[y * stride : (y + 1) * stride])
    assert raw == bytes(expected)


def test_encode_png_rejects_wrong_byte_count():
    try:
        encode_png(4, 4, b"\x00" * 10, channels=3)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for mismatched pixel buffer length")
