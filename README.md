# Container with open source HDL tools

## vcd2png.py
Script for converting .vcd (Value Change Dump) HDL files to .png

Workaround for the gtkwave missing functionality of exporting automatically from the command line. It executes gtkwave on a dummy terminal, configures it with TCL, and takes a screenshot.

Based on https://github.com/ponty/sphinxcontrib-gtkwave

## hdl2diagram.py
**TODO**
Script for generating .png/.svg RTL diagrams from .hdl / .v files.

## backends
* [**GHDL**](https://github.com/ghdl/ghdl) for analysis, synthesis and simulation.
* [**gtkwave**](http://gtkwave.sourceforge.net/) (yes, not even https !) for simulation signals view generation 
* [**yosys**](https://github.com/YosysHQ/yosys) for RTL diagrams generation

## TODO
* Base it on https://github.com/YosysHQ/oss-cad-suite-build / https://hub.docker.com/r/yosyshq/cross-linux-x64 ?
* https://hub.docker.com/r/ghdl/ghdl
  * https://github.com/ghdl/docker
* Check https://hdl.github.io/containers/ !!!!
  * f4pga : https://hdl.github.io/containers/ug/AllInOne.html
* also ... https://hub.docker.com/r/hackfin/yosys ?
* https://github.com/Nic30/hwt
* https://github.com/Nic30/hwtGraph
* https://blog.eowyn.net/netlistsvg/

