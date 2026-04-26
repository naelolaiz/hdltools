"""Geometry: track positions, time-axis ticks, group headers, margin brackets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from waveview.brackets import BracketSpec
from waveview.config import ViewConfig
from waveview.source import SignalRef


LEFT_PAD = 10
RIGHT_PAD = 10
TIME_AXIS_H = 30
GROUP_HEADER_H = 22
BRACKET_LANE_W = 18
LABEL_GUTTER = 14
LABEL_MIN_W = 32
LABEL_MAX_W = 240


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
class BracketBlock:
    """A pixel-positioned hierarchy bracket in the left margin."""
    name: str
    lane: int
    y_top: int
    y_bot: int


@dataclass(frozen=True)
class Geometry:
    width: int
    height: int
    trace_x: int
    trace_w: int
    label_x: int
    label_w: int
    time_axis_y: int
    groups: Tuple[GroupBlock, ...]
    brackets: Tuple[BracketBlock, ...]
    t_from: int
    t_to: int

    def x_of(self, t: int) -> int:
        if self.t_to <= self.t_from:
            return self.trace_x
        return self.trace_x + int(round((t - self.t_from) * self.trace_w / (self.t_to - self.t_from)))


def lay_out(
    view: ViewConfig,
    resolved_groups,
    t_from: int,
    t_to: int,
    brackets_per_group: Sequence[Sequence[BracketSpec]] = (),
    label_w: Optional[int] = None,
) -> Geometry:
    """Compute pixel positions for every track, group header, and bracket.

    ``label_w`` is the pixel width reserved for the label column. The renderer
    measures actual text width and passes it in so the label column hugs the
    widest label rather than forcing a fixed-width gap before the traces.
    """
    width = view.width
    row_h = view.row_height
    if label_w is None:
        label_w = LABEL_MIN_W

    if brackets_per_group and len(brackets_per_group) != len(resolved_groups):
        raise ValueError("brackets_per_group must align with resolved_groups")
    if not brackets_per_group:
        brackets_per_group = [[] for _ in resolved_groups]

    y = TIME_AXIS_H
    blocks: List[GroupBlock] = []
    bracket_blocks: List[BracketBlock] = []

    for (name, sigs_resolved), specs in zip(resolved_groups, brackets_per_group):
        header_y = y if name else y - GROUP_HEADER_H
        if name:
            y += GROUP_HEADER_H
        track_y_start = y
        tracks: List[Track] = []
        for sig, label, fmt, color in sigs_resolved:
            tracks.append(Track(sig=sig, label=label, fmt=fmt, color=color, y=y))
            y += row_h
        for spec in specs:
            y_top = track_y_start + spec.row_lo * row_h + 2
            y_bot = track_y_start + spec.row_hi * row_h - 2
            bracket_blocks.append(BracketBlock(name=spec.name, lane=spec.lane, y_top=y_top, y_bot=y_bot))
        blocks.append(GroupBlock(name=name, header_y=header_y, tracks=tuple(tracks)))

    bracket_depth = 1 + max((b.lane for b in bracket_blocks), default=-1)
    label_x = LEFT_PAD + bracket_depth * BRACKET_LANE_W
    trace_x = label_x + label_w + LABEL_GUTTER
    trace_w = width - trace_x - RIGHT_PAD

    return Geometry(
        width=width,
        height=max(y, TIME_AXIS_H + row_h),
        trace_x=trace_x,
        trace_w=trace_w,
        label_x=label_x,
        label_w=label_w,
        time_axis_y=0,
        groups=tuple(blocks),
        brackets=tuple(bracket_blocks),
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
