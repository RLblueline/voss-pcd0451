# 8. CAD workflow

Tools: OpenSCAD 2021.01+, plus `pip install trimesh manifold3d numpy` for the collision
checker. Rendering headless needs `xvfb-run`.

## Files

| File | Purpose |
|---|---|
| `cad/memo.scad` | Every part as a module in its own local frame; all parameters at the top |
| `cad/assembly.scad` | Posed assembly. `-D YAW= SH= EL= PITCH= SHUT=` plus `SHOW_WALL`, `SHOW_HOUSING`, `SHOW_HEAD`, `SHOW_SHELL`, `CUTAWAY` |
| `cad/view_eye.scad` | Eye mechanism close-up |
| `cad/tools/parts.scad` | Exports one part: `-D 'PART="link1"'` |
| `cad/tools/export.sh` | Exports every part to `cad/stl/` (shutters at 0, 0.5 and 1) |
| `cad/tools/render.sh` | Renders every view in this documentation to `docs/img/` |
| `cad/tools/collide.py` | Joint sweeps and firmware-pose check (see [Mechanical](03-mechanical.md#collision-check-results)) |

## Frames and transforms

| Group | Frame | Transform from its parent |
|---|---|---|
| Housing, back plate, yaw tower, yaw servo | world | — |
| Turret, shoulder servo, yaw coupler | turret | `translate([0, SY, 0]) rotate([0, 0, YAW])` |
| link1 (incl. elbow bracket), elbow servo | link1 | `rotate([0, -SH, 0])` |
| link2, tilt post, tilt servo | link2 | `translate([L1, 0, 0]) rotate([0, -EL, 0])` |
| Head and everything inside it | head | `translate([L2 + TILT_OFF, 0, -TILT_DROP]) rotate([0, TILT, 0])` |

In `assembly.scad`, `HEAD_LEVEL=true` (the default) sets `TILT = SH + EL + PITCH`.

`collide.py` uses the same transforms. If you change one, change both.

## Typical edit loop

```bash
cd cad
nano memo.scad                       # e.g. new servo dimensions
./tools/export.sh                    # ~1-2 min
python3 tools/collide.py             # must end with ALL CLEAR
./tools/render.sh                    # refresh docs/img
```

If you change arm or head geometry, update `memo/config.py` (`YAW_XY`, `L1`, `L2`,
`TILT_OFF`, `TILT_DROP`, `HEAD_R`, `HEAD_LEN`, `OBSTACLES`, `LIMITS`) so the firmware's
workspace check still matches.

## Gallery

| | | |
|---|---|---|
| ![](img/01_hero.png) | ![](img/02_front.png) | ![](img/03_side.png) |
| Hero | Front | Side (home) |
| ![](img/04_raised.png) | ![](img/05_audit_squint.png) | ![](img/06_stamp.png) |
| Raised (rest) | Audit squint | Stamp (dropped) |
| ![](img/07_sulk.png) | ![](img/10_arm_detail.png) | ![](img/11_top_look.png) |
| Sulk | Turret, links and yaw tower | Plan, looking at a talker |
