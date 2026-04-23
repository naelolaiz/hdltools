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
| [GTKWave](http://gtkwave.sourceforge.net/) | Waveform viewer |
| [netlistsvg](https://github.com/nturley/netlistsvg) | Render Yosys JSON netlists as SVG |

Yosys and the GHDL plugin are compiled from `git` because the Debian/Ubuntu
packaged Yosys is too old for the plugin
(see [ghdl-yosys-plugin#149](https://github.com/ghdl/ghdl-yosys-plugin/issues/149)).

## Helper scripts

### `vcd2png.py`

Converts a `.vcd` (Value Change Dump) file to a `.png` of the waveform.

GTKWave has no headless PNG export, so this script runs GTKWave inside a
virtual X display (`xvfb`), drives it with a TCL script that adds every signal
and zooms to fit, then screenshots the window. Adapted from
[sphinxcontrib-gtkwave](https://github.com/ponty/sphinxcontrib-gtkwave).

```
vcd2png.py path/to/dump.vcd
```

The output is written next to the input as `gtkwave_<basename>.png`.

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
podman run --rm -it -v "$PWD:/work" -w /work hdltools /tools/vcd2png.py my_dump.vcd
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
