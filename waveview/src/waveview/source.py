"""WaveformSource: read-only view over a waveform dump.

Wraps pywellen so the rest of waveview (and Phase 1's board renderer)
does not depend on pywellen's API directly. Swapping the parser later
means rewriting this file only.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, Optional, Sequence, Tuple, Union


@dataclass(frozen=True)
class SignalRef:
    full_path: str
    name: str
    width: int
    scope: str


class WaveformSource:
    """Read-only view over a VCD/FST/GHW dump."""

    def __init__(self, path: Union[str, Path]) -> None:
        import pywellen
        self._path = Path(path)
        self._wave = pywellen.Waveform(str(self._path))
        self._hier = self._wave.hierarchy
        self._refs: Dict[str, SignalRef] = {}
        for var in self._hier.all_vars():
            full = var.full_name(self._hier)
            name = var.name(self._hier)
            scope = full.rsplit(".", 1)[0] if "." in full else ""
            self._refs[full] = SignalRef(
                full_path=full,
                name=name,
                width=var.bitwidth(),
                scope=scope,
            )
        self._t_max_cached: Optional[int] = None

    @property
    def path(self) -> Path:
        return self._path

    @property
    def time_unit_exponent(self) -> int:
        return self._hier.timescale().unit.to_exponent()

    def t_min(self) -> int:
        return int(self._wave.time_table[0])

    def t_max(self) -> int:
        if self._t_max_cached is None:
            self._t_max_cached = int(self._wave.time_table[-1])
        return self._t_max_cached

    def signals(self) -> Sequence[SignalRef]:
        return list(self._refs.values())

    def find(self, path: str) -> SignalRef:
        return self._refs[path]

    def find_glob(self, pattern: str) -> Sequence[SignalRef]:
        return [r for p, r in self._refs.items() if fnmatch.fnmatch(p, pattern)]

    def cursor(self, t: int = 0) -> "TimeCursor":
        return TimeCursor(self, t)

    def events(self, sig: SignalRef) -> Iterator[Tuple[int, str]]:
        s = self._wave.get_signal_from_path(sig.full_path)
        for t, v in s.all_changes():
            yield int(t), str(v)


class TimeCursor:
    """Mutable cursor over time."""

    def __init__(self, src: WaveformSource, t: int = 0) -> None:
        self._src = src
        self._t = int(t)
        self._sig_cache: Dict[str, object] = {}

    @property
    def t(self) -> int:
        return self._t

    def step_to(self, t: int) -> None:
        self._t = int(t)

    def _signal(self, sig: SignalRef):
        s = self._sig_cache.get(sig.full_path)
        if s is None:
            s = self._src._wave.get_signal_from_path(sig.full_path)
            self._sig_cache[sig.full_path] = s
        return s

    def value(self, sig: SignalRef) -> Optional[str]:
        v = self._signal(sig).value_at_time(self._t)
        return None if v is None else str(v)

    def value_int(self, sig: SignalRef) -> Optional[int]:
        # pywellen returns Python int for resolved binary values, str for
        # values containing non-binary chars (x/z/u/h/l/w/-). Anything
        # non-int → unknown.
        v = self._signal(sig).value_at_time(self._t)
        return v if isinstance(v, int) else None
