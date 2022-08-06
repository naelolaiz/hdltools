# Container with open source HDL tools

## vcd2png.py
Script for converting .vcd (Value Change Dump) HDL files to .png

Workaround for the gtkwave missing functionality of exporting automatically from the command line. It executes gtkwave on a dummy terminal, configures it with TCL, and takes a screenshot.

Based on https://github.com/ponty/sphinxcontrib-gtkwave

## hdl2svg.py
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
* https://blog.eowyn.net/improving_netlistsvg/
* https://davidthings.github.io/hdelk/


The instructions in https://blog.eowyn.net/improving_netlistsvg/ 
```
TOP=top
ghdl -a --std=08 ${TOP}.vhdl
yosys -p "ghdl --std=08 ${TOP}; prep -top ${TOP}; write_json -compat-int svg.json"
netlistsvg svg.json -o ${TOP}.svg
```
does not work, because yosys doesn't have the ghdl plugin.
Those instructions refer to https://github.com/YosysHQ/fpga-toolchain , but it is not supported anymore. That project then links to https://github.com/YosysHQ/oss-cad-suite-build , which is basically the container I am using, but does not contain the plugin :(
Plus it didn´t compile out of the box. These are the commands I needed to compile the plugin (in fact it didn´t) and yosys core in the container:
 
```
apt-get install git
git clone https://github.com/YosysHQ/yosys.git
git clone https://github.com/ghdl/ghdl-yosys-plugin.git
cd ghdl-yosys-plugin/
make
apt-get install yosys-dev tcl-dev 
cd yosys/
make 
apt-get install pkg-config clang libreadline-dev bison flex
```
Apparently provided version of yosys in the container is (latest release available) is not new enough for the ghdl plugin: https://github.com/ghdl/ghdl-yosys-plugin/issues/149  So both needs to be compiled from git sources :-/
