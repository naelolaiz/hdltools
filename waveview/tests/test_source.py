"""Tests against the committed smoke.vcd."""

from pathlib import Path

import pytest

from waveview.source import WaveformSource


SMOKE = Path(__file__).parent / "data" / "smoke.vcd"


pytestmark = pytest.mark.skipif(
    not SMOKE.is_file(),
    reason="smoke.vcd not generated yet; build the container first",
)


def test_open_smoke_vcd():
    src = WaveformSource(SMOKE)
    assert src.t_max() > 0
    assert src.time_unit_exponent <= 0


def test_signals_listed():
    src = WaveformSource(SMOKE)
    sigs = src.signals()
    assert sigs
    paths = [s.full_path for s in sigs]
    # smoke.vhd has clk and counter[7:0]
    assert any("clk" in p for p in paths), paths
    assert any("counter" in p for p in paths), paths


def test_find_glob():
    src = WaveformSource(SMOKE)
    matches = src.find_glob("*counter*")
    assert matches


def test_cursor_value_int():
    src = WaveformSource(SMOKE)
    counter = next(s for s in src.signals() if "counter" in s.full_path.lower())
    cur = src.cursor(src.t_max())
    v = cur.value_int(counter)
    assert v is not None
    assert 0 <= v < (1 << counter.width)
