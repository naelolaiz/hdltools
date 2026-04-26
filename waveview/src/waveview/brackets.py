"""Hierarchy detection: turn dotted signal paths into nested margin brackets.

A bracket spans a contiguous run of rows that share a leading dot-component
prefix. Consecutive single-child levels are merged into one bracket whose
name joins the components with '.', so a deep but linear scope like
``neotrng_cell_inst(0).neotrng_cell_inst_i`` shows as a single labelled
bracket rather than two redundant lanes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple


@dataclass(frozen=True)
class BracketSpec:
    """A logical bracket, by row index range and lane (nesting depth)."""
    name: str
    lane: int
    row_lo: int
    row_hi: int  # exclusive


def compute_brackets(paths: Sequence[str]) -> Tuple[List[BracketSpec], List[int]]:
    """Build hierarchy brackets for a list of dotted signal paths.

    Returns ``(brackets, prefix_consumed)`` where ``prefix_consumed[i]`` is the
    number of leading dot-components absorbed by enclosing brackets for row
    ``i`` — the renderer strips that many components from the row's label.

    A bracket is emitted only when it covers at least two consecutive rows;
    a single-row sub-scope keeps its components in the leaf label so the row
    is still self-describing.
    """
    n = len(paths)
    if n == 0:
        return [], []

    parts = [p.split(".") for p in paths]
    consumed = [0] * n
    spans: List[BracketSpec] = []

    def recurse(lo: int, hi: int, path_depth: int, lane: int) -> None:
        i = lo
        while i < hi:
            if path_depth >= len(parts[i]):
                i += 1
                continue
            comp = parts[i][path_depth]
            j = i + 1
            while j < hi and path_depth < len(parts[j]) and parts[j][path_depth] == comp:
                j += 1
            if j - i >= 2:
                # Greedy merge of single-child descendant levels into one
                # bracket: as long as every row in [i, j) has the same
                # component at the next depth, fold it into the bracket name.
                merged = [comp]
                merge_depth = path_depth + 1
                while True:
                    if any(merge_depth >= len(parts[k]) for k in range(i, j)):
                        break
                    nxt = parts[i][merge_depth]
                    if all(parts[k][merge_depth] == nxt for k in range(i, j)):
                        merged.append(nxt)
                        merge_depth += 1
                    else:
                        break
                spans.append(BracketSpec(name=".".join(merged), lane=lane, row_lo=i, row_hi=j))
                for k in range(i, j):
                    consumed[k] = merge_depth
                recurse(i, j, merge_depth, lane + 1)
            i = j

    recurse(0, n, 0, 0)
    return spans, consumed
