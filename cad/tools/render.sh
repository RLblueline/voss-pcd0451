#!/usr/bin/env bash
# Render the design views to docs/img/ (run from cad/). Needs openscad + xvfb.
set -e
cd "$(dirname "$0")/.."
OUT=../docs/img
mkdir -p $OUT
R() { name=$1; shift; xvfb-run -a openscad -q -o "$OUT/$name.png" --imgsize=1200,1400 --colorscheme=Tomorrow "$@"; echo "$name"; }
R 01_hero          --camera=10,190,-170,76,0,212,1350 assembly.scad
R 02_front         --camera=0,190,-180,90,0,180,1400 -D SHOW_WALL=false assembly.scad
R 03_side          --camera=0,200,-160,88,0,270,1350 -D SHOW_WALL=false assembly.scad
R 04_raised        --camera=0,200,-120,88,0,270,1350 -D SHOW_WALL=false -D SH=60 -D EL=-60 assembly.scad
R 05_audit_squint  --camera=0,339,-147,82,0,200,620 -D SHOW_WALL=false -D PITCH=12 -D SHUT=0.15 assembly.scad
R 06_stamp         --camera=0,200,-190,88,0,270,1350 -D SHOW_WALL=false -D SH=-5 -D EL=5 -D PITCH=15 -D SHUT=0.15 assembly.scad
R 07_sulk          --camera=-80,170,-160,74,0,160,1400 -D SHOW_WALL=false -D YAW=145 -D SH=30 -D EL=-30 -D PITCH=15 -D SHUT=0.45 assembly.scad
R 08_eye_mechanism_s1 --camera=15,25,-116,65,0,235,340 -D SHUT=1 view_eye.scad
R 08_eye_mechanism_s0 --camera=15,25,-116,65,0,235,340 -D SHUT=0 view_eye.scad
R 09_housing_cut   --camera=0,60,-80,84,0,195,720 -D SHOW_WALL=false -D SHOW_HEAD=false -D CUTAWAY=true assembly.scad
R 10_arm_detail    --camera=10,190,-40,68,0,235,620 -D SHOW_WALL=false -D SHOW_HEAD=false -D SH=35 -D EL=-35 assembly.scad
R 11_top_look      --camera=0,180,-100,0,0,0,1300 -D SHOW_WALL=false -D YAW=60 -D SH=12 -D EL=-8 -D PITCH=-4 assembly.scad
