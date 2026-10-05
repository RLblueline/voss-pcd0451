# 4. Printing

Every printable part is in `cad/stl/`. Regenerate the files with
`cd cad && ./tools/export.sh` after editing the model.

## Part list

The authoritative list is **`build/print_order_jlc3dp.csv`**: 27 numbered files in
`build/print_files/`, each with process, colour, size, volume and notes. Regenerate both
with `python3 cad/tools/package_build.py` after `cad/tools/export.sh`.

| Process | Parts |
|---|---|
| MJF PA12 nylon (or PETG at home, 40–60% infill) | housing, back plate, yaw tower, turret + mast, link1, link2, tilt post, covers, yaw coupler, spring block |
| SLA resin (strongly preferred for gears and splines) | head top (with ears), head middle, head chin, slot plate, eye carriage, eyelids, 18 T / 36 T pinions, rod bars, pulleys |
| Clear resin (tinted) | lens dome |
| TPU | neck bellows, chin bumper |

**Head mass:** about 696 g with 2.4 mm walls, CG about 1 mm from the tilt axis.

## Fasteners and hardware

| Item | Qty | Where |
|---|---|---|
| 608 bearing + 8 mm × 80 mm steel rod | 2 + 1 | yaw tower; shaft clamped by the turret and the coupler |
| 624 bearing + M4 × 20 shoulder bolt + nyloc | 3 | turret, elbow bracket, tilt post pivots |
| 3 mm steel rod, 148 mm | 2 | eye carriage guides |
| Extension spring (~2.1 N/mm, ~55 mm, OD ≤ 13 mm), 1 mm braided cable + 2 crimps, M3 axles + anchor pin + tensioner | 1 set | spring mast (2:1 reeving; pulleys are printed or bought) |
| M3 screws + heat-set inserts | ~30 inserts | covers (4), head seams (8), rod bars (6), back plate (4), coupler (1), spares |
| Servo horn screws | 4 per servo | horns → side plates and + ear |
| #8 × 2 in wood screws | 2 | back plate keyholes into the stud |
| Split-loom tubing 6–8 mm, zip ties | ~1 m | service tubes, harness |

## Cosmetic finishing

- **Lettering and seals:** engraved 0.6 mm. Fill with black paint and wipe, or print
  multi-colour.
- **Dymo labels:** real embossed Dymo tape on the head's right side.
- **Hex screws:** M3 button-head hex bolts at the marked seam spots.
- **Paper strip:** a real 58 mm strip printed on the thermal printer and glued into the chin slot.
