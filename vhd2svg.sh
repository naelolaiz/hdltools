#!/bin/bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: ${0} input_file.vhd [output_svg_filename]"
    echo "It expects an entity with the same name as the file."
    exit 2
fi

input_vhd=$1
entity_to_diagram=$(basename "$input_vhd" .vhd)
svg_file=${2:-$(dirname "$input_vhd")/${entity_to_diagram}_diagram.svg}
json_file=$(dirname "$svg_file")/${entity_to_diagram}_svg.json


ghdl -a --std=08 "$input_vhd"
yosys -m ghdl -p "ghdl --std=08 ${entity_to_diagram}; prep -top ${entity_to_diagram}; write_json -compat-int ${json_file}"
netlistsvg "$json_file" -o "$svg_file"
