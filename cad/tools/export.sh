#!/usr/bin/env bash
# Export every part to stl/ (run from cad/): collision meshes (posed frames) and print parts (p_*).
# The eye carriage, eyelids and pinions are exported at eye heights -1/0/1 and lids 0/0.5/1.
set -e
cd "$(dirname "$0")/.."
mkdir -p stl
J() { [ $(jobs -r | wc -l) -ge 2 ] && wait -n; true; }
parts="housing back_plate tower yaw_body turret coupler sh_body link1 el_body sh_horn link2 post tl_body el_horn
cover1 cover2 head_top head_mid head_chin ears eye_plate eye_rods lift_sg90 leds bumper paper s3_horn neck_boot
p_head_top p_head_mid p_head_chin p_eye_plate p_rod_bar_top p_rod_bar_bottom p_carriage p_lens p_lid_top p_lid_bottom p_pinion18 p_pinion36
p_yaw_coupler p_pulley p_pulley_small p_spring_block p_neck_boot p_bumper"
for p in $parts; do openscad -q -D "PART=\"$p\"" -o "stl/$p.stl" tools/parts.scad & J; done
for e in -1 0 1; do
  openscad -q -D 'PART="carriage"' -D "PE=$e" -o "stl/carriage_$e.stl" tools/parts.scad & J
  openscad -q -D 'PART="lift_pinion"' -D "PE=$e" -o "stl/lift_pinion_$e.stl" tools/parts.scad & J
  for s in 0 0.5 1; do
    openscad -q -D 'PART="shut_top"' -D "S=$s" -D "PE=$e" -o "stl/shut_top_${e}_$s.stl" tools/parts.scad & J
    openscad -q -D 'PART="shut_bot"' -D "S=$s" -D "PE=$e" -o "stl/shut_bot_${e}_$s.stl" tools/parts.scad & J
    openscad -q -D 'PART="pinion"' -D "S=$s" -D "PE=$e" -o "stl/pinion_${e}_$s.stl" tools/parts.scad & J
  done
done
wait
ls stl | wc -l
