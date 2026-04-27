# waveview

Headless, deterministic waveform renderer. Reads VCD / FST / GHW (via
`pywellen`), renders to SVG and PNG (via `pycairo`).

## Install (inside the hdltools container)

The container's `Containerfile` runs `pip install /tools/waveview/`, so
`waveview` is on `$PATH` for everyone using `ghcr.io/naelolaiz/hdltools`.

## CLI

```
waveview <input> [--config PATH] [--output PATH] [--png]
                 [--zoom-range FROM TO] [--width N]
                 [-v|--verbose] [--version]
```

- `<input>`: a `.vcd` / `.fst` / `.ghw` dump.
- `--input` / `-i`: alias for the positional, kept for back-compat with
  `learning_fpga`'s existing Makefile invocation.
- `--config PATH`: explicit YAML. Otherwise auto-discover
  `<input>.view.yaml` then `<input_stem>.view.yaml` next to the input.
- `--output PATH`: defaults to `<input_dir>/<input_stem>.svg`.
- `--png`: also emits `<output_stem>.png`.
- `--zoom-range FROM TO`: integers in the dump's native time units;
  overrides any `time_window` in the YAML.

## View-config YAML

```yaml
version: 1
view:
  time_window: { from: 0, to: 1ms }
  width: 1200
  groups:
    - name: Inputs
      signals:
        - tb.dut.i_clk
        - { path: tb.dut.i_data, format: hex }
    - name: Outputs
      signals:
        - { path: tb.dut.o_data, format: hex, color: "#3478f6" }
```

Time literals accept integers (native units) or SI-suffixed strings
(`ms`, `us`, `ns`, `ps`, `fs`). Per-signal `format` ∈ `{default, hex,
dec, bin, ascii, signed}`. Unknown top-level keys (e.g. a future
`board:` section for Phase 1) trigger a one-line warning and are
ignored.

## Library API

```python
from waveview import WaveformSource

src = WaveformSource("sim.ghw")
counter = src.find("tb.dut.counter")
cur = src.cursor()
for t in range(0, src.t_max(), 5_000):
    cur.step_to(t)
    print(t, cur.value_int(counter))
```

`WaveformSource`, `SignalRef`, and `TimeCursor` are intentionally minimal so
they can be reused by future renderers (e.g. a virtual-board view) without
changes to the parser layer.

## Snapshot test

`tests/test_smoke.py` byte-compares a rendered `smoke.vcd` against a
committed `smoke.expected.svg`. Both files live under `tests/data/`.
Regenerate them only when intentionally bumping the snapshot — and only
inside the container, never on the host:

```sh
podman run --rm -v "$PWD:/work:rw" hdltools:waveview-dev bash -c '
  cd /work/waveview/tests/data
  ghdl -a smoke.vhd
  ghdl -e smoke
  ghdl -r smoke --vcd=smoke.vcd --stop-time=200ns
  cd /work
  python -c "
from pathlib import Path
from waveview.config import load_config
from waveview.render import render, resolve
from waveview.source import WaveformSource
src = WaveformSource(\"waveview/tests/data/smoke.vcd\")
cfg = load_config(None, src.time_unit_exponent)
render(resolve(src, cfg), Path(\"waveview/tests/data/smoke.expected.svg\"))
"
'
```
