"""Snapshot test: render smoke.vcd to SVG and byte-compare."""

import re
from pathlib import Path

import pytest

from waveview.config import load_config
from waveview.render import render, resolve
from waveview.source import WaveformSource


DATA = Path(__file__).parent / "data"
SMOKE = DATA / "smoke.vcd"
EXPECTED = DATA / "smoke.expected.svg"


pytestmark = pytest.mark.skipif(
    not SMOKE.is_file() or not EXPECTED.is_file(),
    reason="smoke fixture not generated yet; build the container first",
)


# cairo numbers each surface it creates with a monotonic process-global
# counter (id="surfaceN"), so the byte at that position depends on how
# many cairo surfaces were built before this test ran. The counter is
# not user-visible content, just an internal label, so normalise it
# before comparing.
_SURFACE_ID_RE = re.compile(rb'id="surface\d+"')


def _normalize(svg: bytes) -> bytes:
    return _SURFACE_ID_RE.sub(b'id="surface"', svg)


def test_render_matches_snapshot(tmp_path: Path):
    src = WaveformSource(SMOKE)
    cfg = load_config(None, src.time_unit_exponent)
    view = resolve(src, cfg)
    out = tmp_path / "smoke.svg"
    render(view, out)
    assert _normalize(out.read_bytes()) == _normalize(EXPECTED.read_bytes()), (
        "smoke render diverged from snapshot. "
        "If the divergence is intentional, regenerate the snapshot inside the container "
        "(see waveview/README.md)."
    )


def test_png_emitted_alongside(tmp_path: Path):
    src = WaveformSource(SMOKE)
    cfg = load_config(None, src.time_unit_exponent)
    view = resolve(src, cfg)
    svg = tmp_path / "smoke.svg"
    png = tmp_path / "smoke.png"
    render(view, svg, png)
    assert svg.is_file() and svg.stat().st_size > 0
    assert png.is_file() and png.stat().st_size > 0
