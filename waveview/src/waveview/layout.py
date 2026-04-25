"""Geometry: track positions, time-axis ticks, group headers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from waveview.config import ViewConfig
from waveview.source import SignalRef


LABEL_COL_W = 200
LEFT_PAD = 10
RIGHT_PAD = 10
TIME_AXIS_H = 30
GROUP_HEADER_H = 22


@dataclass(frozen=True)
class Track:
    """Resolved row for one signal."""
    sig: SignalRef
    label: str
    fmt: str
    color: Optional[str]
    y: int


@dataclass(frozen=True)
class GroupBlock:
    name: Optional[str]
    header_y: int
    tracks: Tuple[Track, ...]


@dataclass(frozen=True)
class Geometry:
    width: int
    height: int
    trace_x: int
    trace_w: int
    time_axis_y: int
    groups: Tuple[GroupBlock, ...]
    t_from: int
    t_to: int

    def x_of(self, t: int) -> int:
        if self.t_to <= self.t_from:
            return self.trace_x
        return self.trace_x + int(round((t - self.t_from) * self.trace_w / (self.t_to - self.t_from)))


def lay_out(view: ViewConfig, resolved_groups, t_from: int, t_to: int) -> Geometry:
    """Compute pixel positions for every track and group header."""
    width = view.width
    trace_x = LABEL_COL_W + LEFT_PAD
    trace_w = width - trace_x - RIGHT_PAD

    y = TIME_AXIS_H
    blocks: List[GroupBlock] = []
    for name, sigs_resolved in resolved_groups:
        header_y = y if name else y - GROUP_HEADER_H
        if name:
            y += GROUP_HEADER_H
        tracks = []
        for sig, label, fmt, color in sigs_resolved:
            tracks.append(Track(sig=sig, label=label, fmt=fmt, color=color, y=y))
            y += view.row_height
        blocks.append(GroupBlock(name=name, header_y=header_y, tracks=tuple(tracks)))

    return Geometry(
        width=width,
        height=max(y, TIME_AXIS_H + view.row_height),
        trace_x=trace_x,
        trace_w=trace_w,
        time_axis_y=0,
        groups=tuple(blocks),
        t_from=t_from,
        t_to=t_to,
    )


def pick_tick_step(t_from: int, t_to: int, target_ticks: int = 10) -> int:
    """Choose a round tick spacing in native time units."""
    span = max(1, t_to - t_from)
    raw = span / target_ticks
    # Snap to 1, 2, 5 * 10^k
    import math
    k = math.floor(math.log10(raw)) if raw > 0 else 0
    base = raw / (10 ** k)
    if base < 1.5:
        mult = 1
    elif base < 3.5:
        mult = 2
    elif base < 7.5:
        mult = 5
    else:
        mult = 10
    return mult * (10 ** k)


_SI_PREFIXES = [
    (-15, "f"),
    (-12, "p"),
    (-9, "n"),
    (-6, "u"),
    (-3, "m"),
    (0, ""),
]


def format_time(value: int, time_unit_exponent: int) -> str:
    """Render a time value as an SI-prefixed string in seconds."""
    if value == 0:
        return "0"
    # Normalize to seconds
    abs_value = abs(value) * (10 ** time_unit_exponent)
    sign = "-" if value < 0 else ""
    for exp, prefix in _SI_PREFIXES:
        scale = 10 ** exp
        if abs_value >= scale:
            n = abs_value / scale
            if n == int(n):
                return f"{sign}{int(n)}{prefix}s"
            return f"{sign}{n:g}{prefix}s"
    return f"{value}"
