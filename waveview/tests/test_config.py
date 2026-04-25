import textwrap
from pathlib import Path

import pytest

from waveview.config import (
    SignalSpec,
    ViewConfig,
    discover_config,
    load_config,
    parse_time,
)


def test_load_missing_returns_defaults():
    cfg = load_config(None, -15)
    assert isinstance(cfg, ViewConfig)
    assert cfg.groups == ()
    assert cfg.width == 1200


def test_load_basic_config(tmp_path: Path):
    p = tmp_path / "v.yaml"
    p.write_text(textwrap.dedent("""
        version: 1
        view:
          width: 800
          row_height: 30
          groups:
            - name: Inputs
              signals:
                - tb.dut.clk
                - { path: tb.dut.data, format: hex }
    """))
    cfg = load_config(p, -15)
    assert cfg.width == 800
    assert cfg.row_height == 30
    assert len(cfg.groups) == 1
    g = cfg.groups[0]
    assert g.name == "Inputs"
    assert g.signals[0] == SignalSpec(path="tb.dut.clk")
    assert g.signals[1].format == "hex"


def test_unknown_top_level_key_warns_but_loads(tmp_path: Path, caplog):
    p = tmp_path / "v.yaml"
    p.write_text("version: 1\nboard:\n  leds: []\nview:\n  width: 1000\n")
    with caplog.at_level("WARNING"):
        cfg = load_config(p, -15)
    assert cfg.width == 1000
    assert any("board" in rec.message for rec in caplog.records)


def test_invalid_format_raises(tmp_path: Path):
    p = tmp_path / "v.yaml"
    p.write_text("view:\n  groups:\n    - signals:\n        - { path: a, format: nope }\n")
    with pytest.raises(ValueError, match="unknown format"):
        load_config(p, -15)


def test_parse_time_int_passthrough():
    assert parse_time(42, -15) == 42


def test_parse_time_si_suffix_fs_dump():
    assert parse_time("1ns", -15) == 1_000_000
    assert parse_time("1us", -15) == 1_000_000_000


def test_parse_time_si_suffix_ps_dump():
    assert parse_time("1ns", -12) == 1000


def test_discover_config_full_sidecar(tmp_path: Path):
    inp = tmp_path / "tb.vcd"
    inp.write_text("")
    sidecar = tmp_path / "tb.vcd.view.yaml"
    sidecar.write_text("version: 1\n")
    assert discover_config(inp) == sidecar


def test_discover_config_stem_sidecar(tmp_path: Path):
    inp = tmp_path / "tb.vcd"
    inp.write_text("")
    sidecar = tmp_path / "tb.view.yaml"
    sidecar.write_text("version: 1\n")
    assert discover_config(inp) == sidecar


def test_discover_config_none(tmp_path: Path):
    inp = tmp_path / "tb.vcd"
    inp.write_text("")
    assert discover_config(inp) is None
