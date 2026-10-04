#!/usr/bin/env bash
# Export every part to stl/ (run from cad/). Shutters are exported open (1) and closed (0).
set -e
cd "$(dirname "$0")/.."
mkdir -p stl
parts="lens carriage_frame neck_boot ear_plus ear_minus cover1 cover2 housing back_plate tower yaw_body turret coupler sh_body link1 el_body sh_horn link2 post tl_body el_horn head_top head_mid head_chin ears eye_plate eye_rods lift_sg90 lift_pinion leds bumper paper s3_horn"
for p in $parts; do
  openscad -q -D "PART=\"$p\"" -o "stl/$p.stl" tools/parts.scad &
  [ $(jobs -r | wc -l) -ge 4 ] && wait -n
done
for e in -1 0 1; do
  openscad -q -D 'PART="carriage"' -D "PE=$e" -o "stl/carriage_$e.stl" tools/parts.scad &
  openscad -q -D 'PART="pinion"' -D "PE=$e" -o "stl/pinion_$e.stl" tools/parts.scad &
  for s in 0 0.5 1; do
    openscad -q -D 'PART="shut_top"' -D "S=$s" -D "PE=$e" -o "stl/shut_top_${e}_$s.stl" tools/parts.scad &
    openscad -q -D 'PART="shut_bot"' -D "S=$s" -D "PE=$e" -o "stl/shut_bot_${e}_$s.stl" tools/parts.scad &
    [ $(jobs -r | wc -l) -ge 6 ] && wait -n
  done
done
wait
ls stl | wc -l
