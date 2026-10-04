# 4. Printing

Every printable part is in `cad/stl/`. Regenerate the files with
`cd cad && ./tools/export.sh` after editing the model.

## Part list

Sizes are bounding boxes in mm. Volume is solid volume, so real filament use depends on
your walls and infill.

| Part | STL | Size | Vol cm³ | Material / colour | Orientation and notes |
|---|---|---|---|---|---|
| Housing | `housing.stl` | 144 × 70 × 226 | 232 | PLA/PETG beige | On its back (open side up); needs a 230 mm bed axis. Otherwise split at z −80 with a lap joint |
| Back plate | `back_plate.stl` | 137 × 9 × 219 | 120 | PLA beige | Flat, standoffs up |
| Yaw tower | `tower.stl` | 60 × 61 × 96 | 53 | **PETG**, 50% infill | Wall plate down; supports under the shelves |
| Turret | `turret.stl` | 44 × 49 × 72 | 39 | **PETG**, 60% | Base disc down |
| Link 1 (incl. elbow bracket) | `link1.stl` | 158 × 62 × 36 | 53 | **PETG** beige, 50% | On its side (a side plate down) |
| Link 2 | `link2.stl` | 146 × 62 × 32 | 51 | **PETG** beige, 50% | On its side |
| Tilt post | `post.stl` | 32 × 46 × 82 | 19 | **PETG**, 60% | Flange plate down |
| Head top | `head_top.stl` | 91 × 140 × 75 | 90 | PLA beige | Crown down; supports for the slot roof |
| Head middle | `head_mid.stl` | 90 × 137 × 160 | 156 | PLA beige | Upright, skirt down; supports in the eye recess |
| Head chin | `head_chin.stl` | 87 × 130 × 75 | 88 | PLA beige | Upright |
| + ear / − ear | `ear_plus.stl`, `ear_minus.stl` | 60 × 3.5 × 44 | 6 each | PETG | Flat |
| Eye bezel | `bezel.stl` | 2 × 92 × 148 | 20 | PLA charcoal | Flat |
| Eye frame (rear plate, rails, lens holder, SG90 mount) | `cartridge_frame.stl` | 22 × 124 × 142 | 69 | PLA charcoal | Rear plate down; supports under the rails |
| Shutter top / bottom | `shut_top_1.stl`, `shut_bot_1.stl` | ~6 × 87–107 × 80 | 8–9 | PLA dark grey (or 1.5 mm aluminium plate + printed racks) | Flat, racks up |
| Pinion | `pinion.stl` | 20 × 20 × 3.2 | 0.7 | PETG or resin | Flat; check the fit on the SG90 spline |
| Lens dome | `lens.stl` | Ø60 × 8 | 12 | Translucent amber PETG, or buy a 60 mm acrylic dome | Dome up, 0.12 mm layers |
| Neck boot | `neck_boot.stl` | 56 × 60 × 28 | 21 | **TPU** black | Upright |
| Bumper | `bumper.stl` | Ø22 × 8.5 | 3 | TPU black | Flat |

Solid total is about 1050 cm³ (about 1.3 kg). With normal infill, expect about 0.9–1.0 kg
plus reprints.

**Head mass:** the shells, cartridge and ears come to about 550 g as printed with 2.4 mm
walls. Electronics, the SG90 and the lens add roughly 50 g more, so the head is about
**600 g**. Use 1.6 mm walls if you want it lighter (see [Known risks](03-mechanical.md#known-risks)).

## Fasteners and hardware

| Item | Qty | Where |
|---|---|---|
| 608 bearing | 2 | yaw tower shelves |
| 8 mm steel rod, 75 mm | 1 | yaw shaft (clamped in the turret with an M3 screw) |
| 624 bearing | 3 | pivot plates of the turret, elbow bracket, tilt post |
| M4 × 20 shoulder bolt + nyloc | 3 | side plate → 624 at shoulder, elbow, tilt |
| M3 × 10 + heat-set inserts | ~30 | tower, post, head seams, back plate |
| Servo horn screws | 4 per servo | horn → link plates and + ear |
| #8 × 2 in wood screws | 2 | back plate keyholes into the stud |

## Cosmetic finishing

- **Lettering:** the text is engraved 0.6 mm. Fill it with black paint and wipe, or use a
  multi-colour print with the inlay meshes from `assembly.scad`.
- **Dymo labels:** use real embossed Dymo tape; the model only shows where it goes.
- **Hex screws:** M3 button-head hex bolts at the marked spots.
- **Paper strip:** a real 58 mm strip printed on the thermal printer and glued into the chin slot.
