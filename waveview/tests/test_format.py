import pytest

from waveview.format import format_value


def test_unknown_renders_as_x():
    assert format_value(None, 8) == "x"


def test_default_picks_bin_for_1bit():
    assert format_value(1, 1) == "1"
    assert format_value(0, 1) == "0"


def test_default_picks_hex_for_wide():
    assert format_value(0xab, 8) == "ab"


def test_hex_pads_to_nibbles():
    assert format_value(0xa, 8, "hex") == "0a"
    assert format_value(0xf, 16, "hex") == "000f"


def test_dec():
    assert format_value(255, 8, "dec") == "255"


def test_bin_pads_to_width():
    assert format_value(5, 8, "bin") == "00000101"


def test_signed_negative():
    assert format_value(0xff, 8, "signed") == "-1"
    assert format_value(0x80, 8, "signed") == "-128"
    assert format_value(0x7f, 8, "signed") == "127"


def test_ascii_printable():
    # 'Hi' = 0x4869
    assert format_value(0x4869, 16, "ascii") == "Hi"


def test_ascii_nonprintable_dot():
    assert format_value(0x0001, 16, "ascii") == ".."


def test_unknown_format_raises():
    with pytest.raises(ValueError):
        format_value(0, 8, "wat")
