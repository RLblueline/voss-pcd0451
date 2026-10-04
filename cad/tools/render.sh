#!/usr/bin/env bash
# Render the design views to docs/img/ (run from cad/). Needs openscad + xvfb.
set -e
cd "$(dirname "$0")/.."
OUT=../docs/img
mkdir -p $OUT
R() { name=$1; shift; xvfb-run -a openscad -q -o "$OUT/$name.png" --imgsize=1200,1400 --colorscheme=Tomorrow "$@"; echo "$name"; }
R 01_hero          --camera=10,170,-190,76,0,212,1350 assembly.scad
R 02_front         --camera=0,170,-200,90,0,180,1450 -D SHOW_WALL=false assembly.scad
R 03_side          --camera=0,170,-190,88,0,270,1500 -D SHOW_WALL=false assembly.scad
R 04_top_look      --camera=0,180,-100,0,0,0,1300 -D SHOW_WALL=false -D SH=70 -D EL=-40 assembly.scad
R 05_audit_squint  --camera=0,342,-300,82,0,200,620 -D SHOW_WALL=false -D TILT=15 -D SHUT=0.15 assembly.scad
R 06_stamp         --camera=0,180,-210,84,0,235,1400 -D SHOW_WALL=false -D TILT=30 -D SHUT=0 assembly.scad
R 07_sulk          --camera=-90,140,-180,74,0,160,1400 -D SHOW_WALL=false -D SH=150 -D EL=30 -D TILT=25 -D SHUT=0.45 assembly.scad
R 08_eye_mechanism_s1 --camera=15,25,-116,65,0,235,340 -D SHUT=1 view_eye.scad
R 08_eye_mechanism_s0 --camera=15,25,-116,65,0,235,340 -D SHUT=0 view_eye.scad
R 09_housing_cut   --camera=0,40,-80,84,0,195,720 -D SHOW_WALL=false -D SHOW_HEAD=false -D CUTAWAY=true assembly.scad
R 10_rear_arm      --camera=0,170,-120,70,0,25,1200 -D SHOW_WALL=false -D SH=60 -D EL=60 -D TILT=-20 assembly.scad
