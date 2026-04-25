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
    (0, ""),
    (-3, "m"),
    (-6, "u"),
    (-9, "n"),
    (-12, "p"),
    (-15, "f"),
]


def pick_axis_unit(step: int, time_unit_exponent: int) -> Tuple[int, str]:
    """Pick a single SI prefix for the whole axis based on tick step.

    Iterates from the LARGEST unit (seconds) downward and returns the first
    one for which `step` is an exact integer multiple. This guarantees every
    tick label renders as a clean integer in that unit — no mix of "200ns"
    and "2.5e+08fs" on the same axis.
    """
    for prefix_exp, prefix in _SI_PREFIXES:
        diff = time_unit_exponent - prefix_exp
        if diff > 0:
            continue  # prefix smaller than dump unit — would inflate every value
        divisor = 10 ** (-diff)
        if step >= divisor and step % divisor == 0:
            return prefix_exp, prefix
    # Fallback: dump's native unit, even if the SI table doesn't cover it.
    for exp, prefix in _SI_PREFIXES:
        if exp == time_unit_exponent:
            return exp, prefix
    return time_unit_exponent, ""


def format_time(value: int, time_unit_exponent: int, prefix_exp: int, prefix: str) -> str:
    """Render a time value as `<n><prefix>s` using only integer arithmetic."""
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    av = abs(value)
    diff = time_unit_exponent - prefix_exp
    if diff <= 0:
        divisor = 10 ** (-diff)
        q, r = divmod(av, divisor)
        if r == 0:
            return f"{sign}{q}{prefix}s"
        # Non-exact division — show as decimal with limited precision instead of scientific.
        whole = av // divisor
        frac = av - whole * divisor
        # 6 significant digits is enough for any realistic waveform tick label.
        return f"{sign}{whole}.{frac:0{len(str(divisor)) - 1}d}".rstrip("0").rstrip(".") + f"{prefix}s"
    # Smaller prefix than the dump unit (e.g. ns dump rendered in fs): always integer.
    return f"{sign}{av * (10 ** diff)}{prefix}s"
