"""Command-line interface for waveview."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from waveview import __version__
from waveview.config import discover_config, load_config
from waveview.render import render, resolve
from waveview.source import WaveformSource


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="waveview",
        description="Render a waveform diagram (SVG / PNG) from a VCD/FST/GHW dump.",
    )
    p.add_argument("input_pos", nargs="?", type=Path, help="Waveform dump (VCD, FST, or GHW).")
    p.add_argument("--input", "-i", type=Path, dest="input_opt",
                   help="Same as the positional INPUT, kept for back-compat with existing Makefiles.")
    p.add_argument("--config", type=Path,
                   help="View-config YAML. Defaults to <input>.view.yaml or <input_stem>.view.yaml next to input.")
    p.add_argument("--output", "-o", type=Path,
                   help="Output SVG path. Defaults to <input_dir>/<input_stem>.svg.")
    p.add_argument("--png", action="store_true",
                   help="Also emit <output_stem>.png alongside the SVG.")
    p.add_argument("--zoom-range", type=int, nargs=2, metavar=("FROM", "TO"),
                   help="Time window in the dump's native units. Overrides any time_window in the YAML.")
    p.add_argument("--width", type=int, help="Render width in px (overrides config).")
    p.add_argument("-v", "--verbose", action="store_true", help="DEBUG-level logging.")
    p.add_argument("--version", action="version", version=f"waveview {__version__}")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(name)s %(levelname)s %(message)s",
    )

    input_path: Optional[Path] = args.input_opt or args.input_pos
    if input_path is None:
        print("waveview: missing input (positional or --input/-i)", file=sys.stderr)
        return 1
    if not input_path.is_file():
        print(f"waveview: input not found: {input_path}", file=sys.stderr)
        return 1

    out_svg = args.output or input_path.with_suffix(".svg")
    out_png = out_svg.with_suffix(".png") if args.png else None

    try:
        src = WaveformSource(input_path)
    except Exception as exc:
        print(f"waveview: failed to open {input_path}: {exc}", file=sys.stderr)
        return 2

    config_path = args.config if args.config is not None else discover_config(input_path)
    try:
        config = load_config(config_path, src.time_unit_exponent)
    except Exception as exc:
        print(f"waveview: bad config {config_path}: {exc}", file=sys.stderr)
        return 1

    if args.width is not None:
        from dataclasses import replace
        config = replace(config, width=args.width)
    if args.zoom_range is not None:
        from dataclasses import replace
        config = replace(config, time_window=(int(args.zoom_range[0]), int(args.zoom_range[1])))

    try:
        view = resolve(src, config)
    except KeyError as exc:
        print(f"waveview: {exc}", file=sys.stderr)
        return 1

    render(view, out_svg, out_png)
    print(f"wrote {out_svg}" + (f" and {out_png}" if out_png else ""))
    return 0
