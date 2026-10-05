#!/usr/bin/env bash
# Render the design views to docs/img/ (run from cad/). Needs openscad + xvfb.
set -e
cd "$(dirname "$0")/.."
OUT=../docs/img
mkdir -p $OUT
R() { name=$1; shift; xvfb-run -a openscad -q -o "$OUT/$name.png" --imgsize=1200,1400 --colorscheme=Tomorrow "$@"; echo "$name"; }
R 01_hero          --camera=10,190,-110,76,0,215,1450 assembly.scad
R 02_front         --camera=0,200,-120,90,0,180,1450 -D SHOW_WALL=false assembly.scad
R 03_side          --camera=0,200,-100,88,0,270,1450 -D SHOW_WALL=false assembly.scad
R 04_raised        --camera=0,200,-60,88,0,270,1450 -D SHOW_WALL=false -D SH=50 -D EL=-50 assembly.scad
R 05_audit_squint  --camera=0,345,-90,82,0,200,700 -D SHOW_WALL=false -D PITCH=12 -D SHUT=0.15 -D EYE=-0.4 assembly.scad
R 06_stamp         --camera=0,200,-130,88,0,270,1450 -D SHOW_WALL=false -D SH=-5 -D EL=5 -D PITCH=15 -D SHUT=0.15 -D EYE=-0.4 assembly.scad
R 07_sulk          --camera=-80,170,-100,74,0,160,1500 -D SHOW_WALL=false -D YAW=145 -D SH=30 -D EL=-30 -D PITCH=15 -D SHUT=0.45 -D EYE=-0.6 assembly.scad
R 08_eye_mechanism_s1 --camera=0,15,-116,62,0,235,420 -D SHUT=1 -D EYE=1 view_eye.scad
R 08_eye_mechanism_s0 --camera=0,15,-116,62,0,235,420 -D SHUT=0 -D EYE=-1 view_eye.scad
R 09_housing_cut   --camera=0,40,-80,84,0,195,720 -D SHOW_WALL=false -D SHOW_HEAD=false -D CUTAWAY=true assembly.scad
R 10_arm_detail    --camera=10,190,50,62,0,235,650 -D SHOW_WALL=false -D SHOW_HEAD=false -D SH=35 -D EL=-35 assembly.scad
R 11_top_look      --camera=0,180,-30,0,0,0,1350 -D SHOW_WALL=false -D YAW=60 -D SH=12 -D EL=-8 -D PITCH=-4 assembly.scad
R 12_eye_up        --camera=0,340,-80,90,0,180,520 -D SHOW_WALL=false -D EYE=1 -D PITCH=-8 assembly.scad
R 12_eye_down      --camera=0,340,-80,90,0,180,520 -D SHOW_WALL=false -D EYE=-1 -D SHUT=0.4 assembly.scad
R 13_deep_nod      --camera=0,200,-100,88,0,270,1450 -D SHOW_WALL=false -D PITCH=45 -D EYE=-0.5 assembly.scad
R 14_look_up       --camera=0,200,-100,88,0,270,1450 -D SHOW_WALL=false -D SH=40 -D EL=-40 -D PITCH=-40 -D EYE=0.8 assembly.scad
