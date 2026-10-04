# 4. Printing

Every printable part is in `cad/stl/`. Regenerate the files with
`cd cad && ./tools/export.sh` after editing the model.

## Part list

Sizes are bounding boxes in mm. Volume is solid volume, so real filament use depends on
your walls and infill.

| Part | STL | Size | cm³ | Material | Orientation and notes |
|---|---|---|---|---|---|
| Housing | `housing.stl` | 144 × 70 × 226 | 229 | PLA/PETG beige | On its back; needs a 230 mm bed axis, or split at z −80 with a lap joint |
| Back plate | `back_plate.stl` | 137 × 9 × 219 | 120 | PLA beige | Flat, standoffs up |
| Yaw tower | `tower.stl` | 60 × 61 × 96 | 53 | **PETG**, 50% | Wall plate down; supports under the shelves |
| Turret + spring mast | `turret.stl` | 58 × 63 × 132 | 56 | **PETG**, 60% | Base disc down; supports under the gooseneck arm |
| Link 1 (incl. elbow bracket, cable eye) | `link1.stl` | 158 × 68 × 32 | 53 | **PETG**, 50% | On its side |
| Link 2 | `link2.stl` | 146 × 62 × 32 | 51 | **PETG**, 50% | On its side |
| Tilt post | `post.stl` | 32 × 46 × 82 | 19 | **PETG**, 60% | Flange plate down |
| Arm covers | `cover1.stl`, `cover2.stl` | 30 wide | 3–5 | PLA beige | Upside down (open side up) |
| Head top / middle / chin | `head_top.stl`, `head_mid.stl`, `head_chin.stl` | 151 × 140 × 75 / 144 × 137 × 160 / 128 × 130 × 75 | 117 / 189 / 108 | PLA beige | Crown down / skirt down / upright; supports in the recess and neck slot |
| + ear / − ear | `ear_plus.stl`, `ear_minus.stl` | 60 × 4 × 44 | 6 each | PETG | Flat |
| Eye slot plate | `eye_plate.stl` | 2 × 92 × 148 | 13 | PLA charcoal | Flat |
| Eye carriage (mask, rear plate, rails, holder, SG90 mount, bushings, lift rack) | `carriage_frame.stl` | 31 × 112 × 166 | 71 | PLA charcoal | Mask down; supports under the rails |
| Rod mounts + lift-servo strut | `eye_rods.stl` (rods are steel) | 42 × 122 × 148 | — | PLA charcoal | Print the bars and strut; cut 2 × 148 mm of 3 mm rod |
| Eyelid plates | `shut_top_0_1.stl`, `shut_bot_0_1.stl` | ~6 × 87–106 × 80 | 8–9 | PLA dark grey (or 1.5 mm aluminium + printed racks) | Flat, racks up |
| Eyelid pinion (18 T) / lift pinion (36 T) | `pinion_0.stl`, `lift_pinion.stl` | Ø20 / Ø38 | <2 | PETG or resin | Flat; check the SG90 spline fit |
| Lens dome | `lens.stl` | Ø60 × 8 | 12 | Translucent amber PETG, or a 60 mm acrylic dome | Dome up, 0.12 mm layers |
| Neck boot, bumper | `neck_boot.stl`, `bumper.stl` | | 21 / 3 | **TPU** black | Upright |

Solid total is about 1.35 kg. With normal infill, expect about 1.1–1.3 kg plus reprints.

**Head mass:** about 690 g as printed with 2.4 mm walls, CG about 1 mm from the tilt axis
(`cad/tools/head_mass.py`). With 1.6 mm walls it's about 520 g; re-run `cad/tools/loads.py`
and re-fit the spring afterwards.

## Fasteners and hardware

| Item | Qty | Where |
|---|---|---|
| 608 bearing + 8 mm × 75 mm steel rod | 2 + 1 | yaw tower |
| 624 bearing + M4 × 20 shoulder bolt + nyloc | 3 | turret, elbow bracket, tilt post pivots |
| 3 mm steel rod, 148 mm | 2 | eye carriage guides |
| Extension spring (~0.8 N/mm), 1 mm braided cable, crimp loops, 2 small pulleys | 1 set | spring mast |
| M3 × 10 + heat-set inserts | ~36 | tower, post, covers, head seams, back plate, eye mounts |
| Servo horn screws | 4 per servo | horns → side plates and + ear |
| #8 × 2 in wood screws | 2 | back plate keyholes into the stud |
| Split-loom tubing 6–8 mm, zip ties | ~1 m | service tubes, harness |

## Cosmetic finishing

- **Lettering and seals:** engraved 0.6 mm. Fill with black paint and wipe, or print
  multi-colour.
- **Dymo labels:** real embossed Dymo tape on the head's right side.
- **Hex screws:** M3 button-head hex bolts at the marked seam spots.
- **Paper strip:** a real 58 mm strip printed on the thermal printer and glued into the chin slot.
