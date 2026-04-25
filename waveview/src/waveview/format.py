"""Value formatters for bus-shaped signals."""

from __future__ import annotations

from typing import Optional


def _hex(value: int, width: int) -> str:
    nibbles = max(1, (width + 3) // 4)
    return f"{value:0{nibbles}x}"


def _dec(value: int, width: int) -> str:
    return str(value)


def _bin(value: int, width: int) -> str:
    return f"{value:0{width}b}"


def _signed(value: int, width: int) -> str:
    if width > 0 and value & (1 << (width - 1)):
        value -= 1 << width
    return str(value)


def _ascii(value: int, width: int) -> str:
    bytestring = []
    bits = width
    v = value
    while bits > 0:
        bytestring.append(v & 0xff)
        v >>= 8
        bits -= 8
    chars = []
    for byte in reversed(bytestring):
        chars.append(chr(byte) if 0x20 <= byte < 0x7f else ".")
    return "".join(chars)


_FORMATTERS = {
    "hex": _hex,
    "dec": _dec,
    "bin": _bin,
    "signed": _signed,
    "ascii": _ascii,
}


def format_value(value: Optional[int], width: int, fmt: str = "default") -> str:
    """Render an integer signal value to the string shown inside a bus block.

    `fmt` of "default" picks bin for 1-bit signals, hex otherwise. Unknown
    values (None) render as "x".
    """
    if value is None:
        return "x"
    if fmt == "default":
        fmt = "bin" if width <= 1 else "hex"
    try:
        return _FORMATTERS[fmt](value, width)
    except KeyError as exc:
        raise ValueError(f"unknown format {fmt!r}") from exc
