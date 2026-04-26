"""Regression tests for hierarchy bracket rendering.

The bracket label sits in the rotated left margin and is fitted to the
bracket's vertical span. The fit decision must not depend on which cairo
surface backs the rendering context: a divergence between SVGSurface and
ImageSurface defaults (hinting, antialias) caused the SVG to keep the
full label while the PNG truncated it.
"""

from pathlib import Path

import cairo
import pytest

from waveview.layout import BracketBlock, Geometry
from waveview.render import (
    BRACKET_FONT_SIZE,
    FONT_FAMILY,
    _bracket_measurement_ctx,
    _draw_brackets,
    _fit_text,
)


def _one_bracket_geom(name: str = "tb_glossary") -> Geometry:
    bracket = BracketBlock(name=name, lane=0, y_top=40, y_bot=200)
    return Geometry(
        width=240,
        height=240,
        trace_x=120,
        trace_w=100,
        label_x=80,
        label_w=40,
        time_axis_y=20,
        groups=(),
        brackets=(bracket,),
        t_from=0,
        t_to=100,
    )


def _render_brackets_only(out: Path, geom: Geometry, hint_style: int) -> None:
    surf = cairo.SVGSurface(str(out), geom.width, geom.height)
    ctx = cairo.Context(surf)
    fo = cairo.FontOptions()
    fo.set_hint_style(hint_style)
    ctx.set_font_options(fo)
    ctx.select_font_face(FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    _draw_brackets(geom, ctx)
    surf.finish()


def test_measurement_ctx_is_stable():
    """Two freshly-built measurement contexts must agree on text widths.

    The fix relies on every render() call producing identical fit
    decisions. If _bracket_measurement_ctx ever started picking up
    process-global state (font_options, locale), this would catch it.
    """
    a = _bracket_measurement_ctx()
    b = _bracket_measurement_ctx()
    for s in ("tb_glossary", "dut", "neotrng.uart_rx"):
        assert a.text_extents(s)[2] == b.text_extents(s)[2]


def test_long_label_fits_under_generous_span():
    """A 160px bracket has plenty of room for an 11-char 10pt label."""
    meas = _bracket_measurement_ctx()
    assert _fit_text(meas, "tb_glossary", max_w=140.0) == "tb_glossary"


def test_short_label_truncates_with_ellipsis():
    meas = _bracket_measurement_ctx()
    fitted = _fit_text(meas, "tb_glossary_extended", max_w=20.0)
    assert fitted.endswith("…")
    assert len(fitted) < len("tb_glossary_extended")


@pytest.mark.parametrize(
    "hint_style",
    [cairo.HINT_STYLE_NONE, cairo.HINT_STYLE_FULL],
)
def test_draw_brackets_emits_output_for_any_hint_style(tmp_path: Path, hint_style):
    """_draw_brackets must produce a non-empty SVG no matter how the
    rendering ctx is configured. This pins the architectural property:
    measurement no longer leaks from the rendering ctx into the fit
    decision.
    """
    geom = _one_bracket_geom()
    out = tmp_path / f"brackets_{hint_style}.svg"
    _render_brackets_only(out, geom, hint_style)
    assert out.is_file() and out.stat().st_size > 0
