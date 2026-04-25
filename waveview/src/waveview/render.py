"""Cairo-based renderer. SVG and PNG share one drawing function."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import cairo

from waveview.config import GroupSpec, SignalSpec, ViewConfig, default_groups_for
from waveview.format import format_value
from waveview.layout import (
    GROUP_HEADER_H,
    LEFT_PAD,
    Geometry,
    Track,
    format_time,
    lay_out,
    pick_tick_step,
)
from waveview.source import SignalRef, WaveformSource

FONT_FAMILY = "DejaVu Sans Mono"
FONT_SIZE = 11
GROUP_FONT_SIZE = 12
DEFAULT_TRACE_COLOR = (0.0, 0.6, 0.0)
UNKNOWN_COLOR = (0.85, 0.15, 0.15)
GRID_COLOR = (0.85, 0.85, 0.85)
TEXT_COLOR = (0.05, 0.05, 0.05)
GROUP_BG = (0.93, 0.93, 0.96)


@dataclass
class ResolvedView:
    src: WaveformSource
    config: ViewConfig
    groups: List[Tuple[Optional[str], List[Tuple[SignalRef, str, str, Optional[str]]]]]
    t_from: int
    t_to: int


def resolve(src: WaveformSource, config: ViewConfig) -> ResolvedView:
    """Bind YAML signal paths to actual SignalRefs and clamp the time window."""
    groups_in = config.groups or default_groups_for(src.signals())

    resolved_groups: List[Tuple[Optional[str], List[Tuple[SignalRef, str, str, Optional[str]]]]] = []
    for g in groups_in:
        rows: List[Tuple[SignalRef, str, str, Optional[str]]] = []
        for s in g.signals:
            try:
                ref = src.find(s.path)
            except KeyError:
                raise KeyError(f"signal not found in dump: {s.path!r}")
            label = s.label or ref.full_path
            rows.append((ref, label, s.format, s.color))
        resolved_groups.append((g.name, rows))

    t_from = config.time_window[0] if config.time_window[0] is not None else src.t_min()
    t_to = config.time_window[1] if config.time_window[1] is not None else src.t_max()
    if t_to <= t_from:
        t_to = t_from + 1

    return ResolvedView(src=src, config=config, groups=resolved_groups, t_from=t_from, t_to=t_to)


def render(view: ResolvedView, out_svg: Path, out_png: Optional[Path] = None) -> None:
    """Render to SVG and (optionally) PNG."""
    geom = lay_out(view.config, view.groups, view.t_from, view.t_to)

    out_svg.parent.mkdir(parents=True, exist_ok=True)
    svg = cairo.SVGSurface(str(out_svg), geom.width, geom.height)
    ctx = cairo.Context(svg)
    _draw(view, geom, ctx)
    svg.finish()

    if out_png is not None:
        out_png.parent.mkdir(parents=True, exist_ok=True)
        img = cairo.ImageSurface(cairo.FORMAT_ARGB32, geom.width, geom.height)
        ctx = cairo.Context(img)
        ctx.set_source_rgb(1, 1, 1)
        ctx.paint()
        _draw(view, geom, ctx)
        img.write_to_png(str(out_png))


def _draw(view: ResolvedView, geom: Geometry, ctx: cairo.Context) -> None:
    ctx.select_font_face(FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(FONT_SIZE)

    _draw_time_axis(view, geom, ctx)

    for block in geom.groups:
        if block.name:
            _draw_group_header(block.name, block.header_y, geom, ctx)
        for track in block.tracks:
            _draw_label(track, geom, ctx, view.config.row_height)
            _draw_trace(view, track, geom, ctx, view.config.row_height)


def _draw_time_axis(view: ResolvedView, geom: Geometry, ctx: cairo.Context) -> None:
    step = pick_tick_step(geom.t_from, geom.t_to)
    exp = view.src.time_unit_exponent

    ctx.set_source_rgb(*GRID_COLOR)
    ctx.set_line_width(1)
    ctx.move_to(geom.trace_x, 28)
    ctx.line_to(geom.trace_x + geom.trace_w, 28)
    ctx.stroke()

    ctx.set_source_rgb(*TEXT_COLOR)
    t = (geom.t_from // step) * step
    if t < geom.t_from:
        t += step
    while t <= geom.t_to:
        x = geom.x_of(t)
        ctx.move_to(x, 24)
        ctx.line_to(x, 28)
        ctx.stroke()
        label = format_time(t, exp)
        _, _, tw, _, _, _ = ctx.text_extents(label)
        ctx.move_to(int(x - tw / 2), 18)
        ctx.show_text(label)
        t += step


def _draw_group_header(name: str, y: int, geom: Geometry, ctx: cairo.Context) -> None:
    ctx.set_source_rgb(*GROUP_BG)
    ctx.rectangle(0, y, geom.width, GROUP_HEADER_H)
    ctx.fill()
    ctx.set_source_rgb(*TEXT_COLOR)
    ctx.set_font_size(GROUP_FONT_SIZE)
    ctx.move_to(LEFT_PAD, y + GROUP_HEADER_H - 6)
    ctx.show_text(name)
    ctx.set_font_size(FONT_SIZE)


def _draw_label(track: Track, geom: Geometry, ctx: cairo.Context, row_h: int) -> None:
    ctx.set_source_rgb(*TEXT_COLOR)
    ctx.move_to(LEFT_PAD, track.y + row_h - 8)
    ctx.show_text(track.label)


def _parse_color(spec: Optional[str]) -> Tuple[float, float, float]:
    if not spec:
        return DEFAULT_TRACE_COLOR
    s = spec.lstrip("#")
    if len(s) != 6:
        return DEFAULT_TRACE_COLOR
    r = int(s[0:2], 16) / 255.0
    g = int(s[2:4], 16) / 255.0
    b = int(s[4:6], 16) / 255.0
    return (r, g, b)


def _draw_trace(view: ResolvedView, track: Track, geom: Geometry, ctx: cairo.Context, row_h: int) -> None:
    color = _parse_color(track.color)
    sig = track.sig
    src = view.src
    t_from, t_to = geom.t_from, geom.t_to
    top = track.y + 4
    bot = track.y + row_h - 4

    events: List[Tuple[int, Optional[int]]] = []
    for t, raw in src.events(sig):
        try:
            events.append((int(t), int(raw)))
        except ValueError:
            # raw is a non-binary string (x/z/u/h/l/w/-) → unknown segment
            events.append((int(t), None))

    if not events:
        ctx.set_source_rgb(0.6, 0.6, 0.6)
        ctx.set_dash([3, 3])
        ctx.set_line_width(1)
        ctx.move_to(geom.trace_x, (top + bot) // 2)
        ctx.line_to(geom.trace_x + geom.trace_w, (top + bot) // 2)
        ctx.stroke()
        ctx.set_dash([])
        return

    # Build (start_t, end_t, value) segments clipped to [t_from, t_to].
    segments: List[Tuple[int, int, Optional[int]]] = []
    for i, (t, v) in enumerate(events):
        seg_end = events[i + 1][0] if i + 1 < len(events) else t_to
        seg_start = t
        if seg_end <= t_from or seg_start >= t_to:
            continue
        seg_start = max(seg_start, t_from)
        seg_end = min(seg_end, t_to)
        segments.append((seg_start, seg_end, v))

    if sig.width <= 1:
        _draw_bit_trace(segments, geom, ctx, top, bot, color)
    else:
        _draw_bus_trace(segments, geom, ctx, top, bot, color, sig.width, track.fmt)


def _draw_bit_trace(segments, geom: Geometry, ctx: cairo.Context, top: int, bot: int, color) -> None:
    ctx.set_source_rgb(*color)
    ctx.set_line_width(1.5)
    prev_y = None
    for start, end, v in segments:
        x0 = geom.x_of(start)
        x1 = geom.x_of(end)
        if v is None:
            ctx.set_source_rgb(*UNKNOWN_COLOR)
            ctx.rectangle(x0, top, max(1, x1 - x0), bot - top)
            ctx.fill()
            ctx.set_source_rgb(*color)
            prev_y = None
            continue
        y = top if v else bot
        if prev_y is not None and prev_y != y:
            ctx.move_to(x0, prev_y)
            ctx.line_to(x0, y)
        ctx.move_to(x0, y)
        ctx.line_to(x1, y)
        ctx.stroke()
        prev_y = y


def _draw_bus_trace(segments, geom: Geometry, ctx: cairo.Context, top: int, bot: int, color, width_bits: int, fmt: str) -> None:
    ctx.set_line_width(1.0)
    for start, end, v in segments:
        x0 = geom.x_of(start)
        x1 = geom.x_of(end)
        if x1 <= x0:
            continue
        if v is None:
            ctx.set_source_rgb(*UNKNOWN_COLOR)
            ctx.rectangle(x0, top, x1 - x0, bot - top)
            ctx.fill()
            continue
        ctx.set_source_rgb(*color)
        ctx.move_to(x0, top)
        ctx.line_to(x1, top)
        ctx.line_to(x1, bot)
        ctx.line_to(x0, bot)
        ctx.close_path()
        ctx.stroke()
        text = format_value(v, width_bits, fmt)
        _, _, tw, _, _, _ = ctx.text_extents(text)
        if tw < (x1 - x0) - 4:
            ctx.set_source_rgb(*TEXT_COLOR)
            ctx.move_to(x0 + (x1 - x0 - tw) / 2, bot - 4)
            ctx.show_text(text)
