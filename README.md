# hdltools

[![Build status](https://github.com/naelolaiz/hdltools/actions/workflows/docker-image.yml/badge.svg?branch=main)](https://github.com/naelolaiz/hdltools/actions/workflows/docker-image.yml)

Container image with an open-source HDL toolchain for VHDL, Verilog, and
SystemVerilog — GHDL, Yosys (with the GHDL plugin), Icarus Verilog,
Verilator, and slang — plus `waveview`, a deterministic headless
VCD/FST/GHW renderer, and `vhd2svg.sh` for rendering VHDL entities as
SVG schematics.

## Quickstart

The image is published to GitHub Container Registry on every push to `main`,
so the fast path is to pull, not build:

```
podman pull ghcr.io/naelolaiz/hdltools:release
podman run --rm -it -v "$PWD:/work" -w /work \
  ghcr.io/naelolaiz/hdltools:release waveview my_dump.vcd
```

(or `docker` in place of `podman` if you prefer)

## What's inside

| Tool | Purpose |
| --- | --- |
| [GHDL](https://github.com/ghdl/ghdl) | VHDL analysis, elaboration, simulation |
| [Yosys](https://github.com/YosysHQ/yosys) | RTL synthesis (built from source) |
| [ghdl-yosys-plugin](https://github.com/ghdl/ghdl-yosys-plugin) | Lets Yosys read VHDL via GHDL (built from source) |
| [Icarus Verilog](https://github.com/steveicarus/iverilog) | Verilog simulation (v13, built from source — Ubuntu 22.04 apt is stuck on v11 which doesn't accept the `vvp <vvp> -fst` extended-arg form needed for FST output) |
| [Verilator](https://github.com/verilator/verilator) | SystemVerilog 2017 simulator (v5.x, built from source — best-of-class open-source SV simulator; cycle-accurate, compiles SV → C++) |
| [slang](https://github.com/MikePopoloski/slang) | SystemVerilog 2017 parser/elaborator/linter (v10.x, built from source — modern, fast, and the front-end for the yosys-slang synthesis path) |
| [netlistsvg](https://github.com/nturley/netlistsvg) | Render Yosys JSON netlists as SVG |
| [pywellen](https://github.com/ekiwi/wellen) + [pycairo](https://pycairo.readthedocs.io/) | Parser + renderer used by `waveview` |

Yosys and the GHDL plugin are compiled from `git` because the Debian/Ubuntu
packaged Yosys is too old for the plugin
(see [ghdl-yosys-plugin#149](https://github.com/ghdl/ghdl-yosys-plugin/issues/149)).
Icarus Verilog, Verilator, and slang are also built from source: apt's
`iverilog` predates the FST output rework, apt's `verilator` is too old
for the SystemVerilog 2017 verification subset, and `slang` isn't packaged
on Ubuntu 22.04 at all.

## Using the toolchain

All examples assume `IMG=ghcr.io/naelolaiz/hdltools:release` and that the
input file is in the current directory.

### VHDL: simulate with GHDL, render the wave

```
podman run --rm -v "$PWD:/work" -w /work "$IMG" bash -c '
  ghdl -a smoke.vhd
  ghdl -e smoke
  ghdl -r smoke --vcd=smoke.vcd --stop-time=200ns
  waveview smoke.vcd --png
'
```

### Verilog: simulate with Icarus Verilog, dump FST

```
podman run --rm -v "$PWD:/work" -w /work "$IMG" bash -c '
  iverilog -o smoke.vvp smoke.v
  vvp smoke.vvp -fst        # -fst MUST come AFTER the .vvp file
  waveview smoke.fst --png
'
```

The `-fst` flag is an extended argument and must follow the `.vvp` file; if
it comes first, `vvp` parses it as a short-option group (`-f -s -t`) and
errors out.

### SystemVerilog: lint with Verilator and slang

```
podman run --rm -v "$PWD:/work" -w /work "$IMG" bash -c '
  verilator --lint-only --top sv_smoke sv_smoke.sv
  slang     --top sv_smoke sv_smoke.sv
'
```

Both linters parse the SystemVerilog 2017 subset (typedef, packed structs,
`always_ff`, struct literals, parameterised int widths). See
[`container/test/sv_smoke.sv`](container/test/sv_smoke.sv) for the CI fixture.

### Synthesise a VHDL entity to an SVG schematic

```
podman run --rm -v "$PWD:/work" -w /work "$IMG" /tools/vhd2svg.sh my_design.vhd
```

## Helper scripts

### `waveview`

Headless, deterministic waveform renderer. Reads `.vcd` / `.fst` / `.ghw`
(via [pywellen](https://github.com/ekiwi/wellen)) and writes SVG primary,
PNG via `--png`. No X server, no GTKWave, no screenshotting — pure parser
+ Cairo. Optional sidecar YAML controls signal selection, ordering,
grouping, value formatting, and time window. Full docs in
[`waveview/README.md`](waveview/README.md).

```
waveview path/to/dump.vcd                       # writes dump.svg next to input
waveview dump.vcd --png                          # also dump.png
waveview dump.vcd --zoom-range 0 200000          # native time units
waveview dump.vcd --config view.yaml --output …
```

`waveview` is also importable as a Python package — `WaveformSource` is the
parser-layer abstraction the future virtual-board renderer will reuse.

### `vhd2svg.sh`

Generates an SVG schematic from a single VHDL file. The file must contain an
entity with the same name as the file (minus the `.vhd` extension).

```
vhd2svg.sh input.vhd [output.svg]
```

Under the hood it runs:

```
ghdl -a --std=08 input.vhd
yosys -m ghdl -p 'ghdl --std=08 <entity>; prep -top <entity>; write_json -compat-int <entity>_svg.json'
netlistsvg <entity>_svg.json -o <entity>_diagram.svg
```

The `-m ghdl` flag is what loads the GHDL plugin into Yosys — easy to miss,
see the
[ghdl-yosys-plugin README](https://github.com/ghdl/ghdl-yosys-plugin/blob/master/README.md).

## Building the container yourself

```
podman build -t hdltools -f container/Containerfile .
# or: docker build -t hdltools -f container/Containerfile .
```

CI builds and publishes the image to GitHub Container Registry on every push
to `main` (see
[`.github/workflows/docker-image.yml`](.github/workflows/docker-image.yml)).

### Published tags

| Tag | What it is |
| --- | --- |
| `ghcr.io/naelolaiz/hdltools:latest`  | latest build from `main` (rolling) |
| `ghcr.io/naelolaiz/hdltools:release` | same as `latest`; what downstream repos pin to |
| `ghcr.io/naelolaiz/hdltools:sha-<short>` | content-addressed per commit |

### Migrating from `vcd2png`

Earlier images bundled a GTKWave/Xvfb-based `vcd2png.py`. That tool was
replaced by `waveview` (headless, deterministic, no X server) in commit
`a146717`. The last image that still ships `vcd2png.py` is preserved as a
parking spot for anyone still pinning to that pipeline:

| Tag | What it is |
| --- | --- |
| `ghcr.io/naelolaiz/hdltools:vcd2png` | legacy backup at commit `a146717` |

New work should use `:release` and `waveview`.

## Future work

Tracked in [GitHub Issues](https://github.com/naelolaiz/hdltools/issues).
Areas of interest: rebasing on
[oss-cad-suite-build](https://github.com/YosysHQ/oss-cad-suite-build) or
[ghdl/docker](https://github.com/ghdl/docker), surveying
[hdl/containers](https://hdl.github.io/containers/), and exploring
alternative RTL visualisers
([hwtGraph](https://github.com/Nic30/hwtGraph),
[hdelk](https://davidthings.github.io/hdelk/),
[netlistsvg tips](https://blog.eowyn.net/improving_netlistsvg/)).
