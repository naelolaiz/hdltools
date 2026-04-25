# hdltools

Container with open-source HDL tools, plus a couple of helper scripts that
paper over missing features in the underlying tools.

## What's inside

| Tool | Purpose |
| --- | --- |
| [GHDL](https://github.com/ghdl/ghdl) | VHDL analysis, elaboration, simulation |
| [Yosys](https://github.com/YosysHQ/yosys) | RTL synthesis (built from source) |
| [ghdl-yosys-plugin](https://github.com/ghdl/ghdl-yosys-plugin) | Lets Yosys read VHDL via GHDL (built from source) |
| [Icarus Verilog](https://github.com/steveicarus/iverilog) | Verilog simulation |
| [netlistsvg](https://github.com/nturley/netlistsvg) | Render Yosys JSON netlists as SVG |
| [pywellen](https://github.com/ekiwi/wellen) + [pycairo](https://pycairo.readthedocs.io/) | Parser + renderer used by `waveview` |

Yosys and the GHDL plugin are compiled from `git` because the Debian/Ubuntu
packaged Yosys is too old for the plugin
(see [ghdl-yosys-plugin#149](https://github.com/ghdl/ghdl-yosys-plugin/issues/149)).

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

## Building the container

```
podman build -t hdltools -f container/Containerfile .
# or: docker build -t hdltools -f container/Containerfile .
```

The CI workflow (`.github/workflows/docker-image.yml`) currently only verifies
that the image builds; it does not push to a registry.

## Running

Mount your working directory and run the tool you want:

```
podman run --rm -it -v "$PWD:/work" -w /work hdltools /tools/vhd2svg.sh my_design.vhd
podman run --rm -it -v "$PWD:/work" -w /work hdltools waveview my_dump.vcd
```

## Ideas / TODO

- Base the image on [oss-cad-suite-build](https://github.com/YosysHQ/oss-cad-suite-build)
  or [ghdl/docker](https://github.com/ghdl/docker) instead of installing
  things by hand.
- Survey [hdl/containers](https://hdl.github.io/containers/) — in particular
  [f4pga](https://hdl.github.io/containers/ug/AllInOne.html).
- Look at alternative RTL visualisers:
  [hwtGraph](https://github.com/Nic30/hwtGraph),
  [hdelk](https://davidthings.github.io/hdelk/),
  and the netlistsvg tips at
  [eowyn.net](https://blog.eowyn.net/improving_netlistsvg/).
