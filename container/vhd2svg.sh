#!/bin/bash

[[ -z ${1} ]] && echo "Usage: ${0} input_file.vhd [output_svg_filename]" && echo "It expects an entity with the same name as the file." && exit -1

input_vhd=${1}
entity_to_diagram=$(basename ${1} .vhd)
json_file=$(dirname ${1})/${entity_to_diagram}_svg.json
svg_file=${2:-$(dirname ${1})/${entity_to_diagram}_diagram.svg}


ghdl -a --std=08 ${input_vhd}
yosys -m ghdl -p 'ghdl --std=08 ${entity_to_diagram}; prep -top ${entity_to_diagram}; write_json -compat-int ${json_file}'
netlistsvg ${json_file} -o ${svg_file}
