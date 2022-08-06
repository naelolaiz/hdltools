# Container with open source HDL tools

## vcd2png.py
Script for converting .vcd (Value Change Dump) HDL files to .png

Workaround for the gtkwave missing functionality of exporting automatically from the command line. It executes gtkwave on a dummy terminal, configures it with TCL, and takes a screenshot.

Based on https://github.com/ponty/sphinxcontrib-gtkwave

## hdl2diagram.py
**TODO**
Script for generating .png/.svg RTL diagrams from .hdl / .v files.

## backends
* **GHDL** for analysis, synthesis and simulation.
* gtkwave for simulation signals view generatioin
* yosys for RTL diagrams generation
