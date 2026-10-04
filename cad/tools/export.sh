#!/usr/bin/env bash
# Export every part to stl/ (run from cad/). Shutters are exported open (1) and closed (0).
set -e
cd "$(dirname "$0")/.."
mkdir -p stl
parts="bezel cartridge_frame lens neck_boot ear_plus ear_minus housing back_plate bracket s1_body link1 hanger s2_body s1_horn link2 post s3_body s2_horn head_top head_mid head_chin ears cartridge sg90 leds bumper paper s3_horn pinion"
for p in $parts; do
  openscad -q -D "PART=\"$p\"" -o "stl/$p.stl" tools/parts.scad &
  [ $(jobs -r | wc -l) -ge 4 ] && wait -n
done
for s in 0 0.5 1; do
  openscad -q -D 'PART="shut_top"' -D "S=$s" -o "stl/shut_top_$s.stl" tools/parts.scad &
  openscad -q -D 'PART="shut_bot"' -D "S=$s" -o "stl/shut_bot_$s.stl" tools/parts.scad &
done
wait
ls stl | wc -l
