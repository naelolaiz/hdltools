"""View-config YAML schema, loading, and auto-discovery."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import yaml

logger = logging.getLogger("waveview.config")


_TIME_SUFFIXES = {
    "ms": -3,
    "us": -6,
    "ns": -9,
    "ps": -12,
    "fs": -15,
}
_TIME_RE = re.compile(r"^\s*(\d+)\s*(ms|us|ns|ps|fs)?\s*$")

_VALID_FORMATS = {"default", "hex", "dec", "bin", "ascii", "signed"}


@dataclass(frozen=True)
class SignalSpec:
    path: str
    format: str = "default"
    color: Optional[str] = None
    label: Optional[str] = None


@dataclass(frozen=True)
class GroupSpec:
    name: Optional[str]
    signals: Tuple[SignalSpec, ...]


@dataclass(frozen=True)
class ViewConfig:
    time_window: Tuple[Optional[int], Optional[int]] = (None, None)
    width: int = 1200
    row_height: int = 24
    groups: Tuple[GroupSpec, ...] = field(default_factory=tuple)


def parse_time(value, time_unit_exponent: int) -> Optional[int]:
    """Convert an int or SI-suffixed string into the dump's native units."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        m = _TIME_RE.match(value)
        if not m:
            raise ValueError(f"invalid time literal {value!r}")
        n = int(m.group(1))
        suffix = m.group(2)
        if suffix is None:
            return n
        delta = _TIME_SUFFIXES[suffix] - time_unit_exponent
        return n * (10 ** delta) if delta >= 0 else n // (10 ** -delta)
    raise ValueError(f"invalid time literal {value!r}")


def _coerce_signal(entry) -> SignalSpec:
    if isinstance(entry, str):
        return SignalSpec(path=entry)
    if not isinstance(entry, dict) or "path" not in entry:
        raise ValueError(f"signal entry must be a string or have a `path` key, got {entry!r}")
    fmt = entry.get("format", "default")
    if fmt not in _VALID_FORMATS:
        raise ValueError(f"unknown format {fmt!r}; expected one of {sorted(_VALID_FORMATS)}")
    return SignalSpec(
        path=entry["path"],
        format=fmt,
        color=entry.get("color"),
        label=entry.get("label"),
    )


def load_config(yaml_path: Optional[Path], time_unit_exponent: int) -> ViewConfig:
    """Load a view-config YAML, or return defaults if path is None / missing."""
    if yaml_path is None or not yaml_path.is_file():
        return ViewConfig()
    raw = yaml.safe_load(yaml_path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{yaml_path}: top-level must be a mapping")

    for key in raw:
        if key not in {"version", "view"}:
            logger.warning("%s: ignoring unknown top-level key %r", yaml_path, key)

    view = raw.get("view") or {}
    if not isinstance(view, dict):
        raise ValueError(f"{yaml_path}: `view` must be a mapping")

    tw = view.get("time_window") or {}
    t_from = parse_time(tw.get("from"), time_unit_exponent) if tw.get("from") is not None else None
    t_to = parse_time(tw.get("to"), time_unit_exponent) if tw.get("to") is not None else None

    groups: List[GroupSpec] = []
    for g in view.get("groups", []) or []:
        signals = tuple(_coerce_signal(s) for s in g.get("signals", []) or [])
        groups.append(GroupSpec(name=g.get("name"), signals=signals))

    return ViewConfig(
        time_window=(t_from, t_to),
        width=int(view.get("width", 1200)),
        row_height=int(view.get("row_height", 24)),
        groups=tuple(groups),
    )


def discover_config(input_path: Path) -> Optional[Path]:
    """Find a sidecar `<input>.view.yaml` or `<input_stem>.view.yaml`, if any."""
    full_sidecar = input_path.with_suffix(input_path.suffix + ".view.yaml")
    if full_sidecar.is_file():
        return full_sidecar
    stem_sidecar = input_path.with_suffix(".view.yaml")
    if stem_sidecar.is_file():
        return stem_sidecar
    return None


def default_groups_for(signals: Sequence) -> Tuple[GroupSpec, ...]:
    """Produce a single ungrouped GroupSpec listing every signal in dump order."""
    return (
        GroupSpec(
            name=None,
            signals=tuple(SignalSpec(path=s.full_path) for s in signals),
        ),
    )
