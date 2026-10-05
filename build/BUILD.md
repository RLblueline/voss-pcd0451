# V.O.S.S. build guide

This folder has everything you need to buy, print and assemble V.O.S.S.

| File | What it is |
|---|---|
| `BOM.csv` | Purchased parts (about $214 before printing) |
| `print_order_jlc3dp.csv` | Order sheet for the 27 print files: process, colour, size, volume, notes |
| `print_files/` | Print-ready STLs (mm), each a single watertight solid |

The full assembly sequence with checkpoints is in `docs/05-assembly.md`. Bring-up and
calibration are in `docs/07-bringup.md`.

## 1. Order the prints (JLC3DP or any print service)

1. Upload every file in `print_files/` and set the material per `print_order_jlc3dp.csv`:

   | Process | Parts | Why |
   |---|---|---|
   | **MJF PA12 nylon** | Housing, back plate, tower, turret, links, post, covers, coupler, spring block | Strong and tough |
   | **SLA resin** | Head shells, eye parts, pinions, pulleys | Fine detail: lettering, involute gear teeth, the SG90 spline bores. Use tough resin for the pinions if offered |
   | **Clear resin** | Lens dome | Tint it amber afterwards, or buy a 60 mm amber acrylic dome |
   | **TPU** | Neck bellows, chin bumper | Flexible. If the service doesn't list a flexible material, print these two on an FDM printer in TPU |

2. Before ordering, check the service's current maximum part size and minimum wall
   thickness:
   - The largest part is the housing, 144 × 70 × 226 mm.
   - The thinnest features are the 1.2 mm bellows wall and the ~0.7 mm gear tooth tips.
3. Printing at home instead? Use PETG for the structural parts at 40–60% infill. The gears
   and splines need a 0.4 mm nozzle or finer and careful tuning; resin is strongly preferred
   for parts 19–22.

## 2. Buy the parts

Everything is in `BOM.csv`. Before printing, measure your servos and update `MG`, `DS` and
`SG` in `cad/voss.scad` if they differ, then re-run the checks (section 5).

## 3. Assemble

1. **Bench-test the electronics:** wiring, mics, LEDs, printer, all six servo channels.
2. **Housing:** Pi, PCA9685, amp, speaker, mics, printer (exit down), jacks.
3. **Yaw:** two 608s in the tower, MG996R, coupler on the horn, 8 × 80 mm shaft, turret clamp.
4. **Shoulder:**
   1. DS3225 in the turret, 624 in the pivot plate.
   2. Link1 on the horn and on an M4 shoulder bolt.
   3. Support the arm by hand from here on until the spring is in.
5. **Counterbalance (2:1):**
   1. Spring into the mast bore, hooked to the tensioner screw at the bottom.
   2. Spring block (with the 7 mm pulley) on top of the spring.
   3. Route the cable: from link1's eye, over the 10 mm top pulley (M3 axle), down under the
      spring-block pulley, and up to the M3 anchor pin.
   4. Crimp the cable with the arm at 75°.
   5. Tune with `calibrate float` until the arm floats near 50°.
6. **Elbow and tilt:**
   1. DS3225 in link1's elbow bracket, then link2.
   2. Tilt post under link2 (2 × M3).
   3. DS3218 in the post.
7. **Eye:**
   1. LED ring on the carriage's rear plate.
   2. Lens into the seat.
   3. Eyelid SG90 and 18 T pinion: press the pinion on with the lids open.
   4. 3 mm rods through the bushings into the rod bars.
   5. Lift SG90 and 36 T pinion: press the pinion on with the eye centred.
8. **Head:**
   1. Status LEDs behind the windows.
   2. Eye assembly into the middle shell; screw the rod bars through the side walls (6 × M3).
   3. Glue the slot plate behind the recess.
   4. Join the three shell pieces with M3 × 16 screws into the seam inserts (8 total).
   5. Bolt the crown's + ear to the DS3218 horn and pass the M4 pivot through the − ear.
   6. Fit the bellows and bumper.
9. **Harness:**
   1. Route the bundle along the beam tops under the covers, with service-tube loops at the
      base, the elbow and the neck. Leave about 30 mm of slack at each loop.
   2. Fit the covers with M3 screws into the beam inserts.
10. **Wall:** one stud, two #8 screws 150 mm apart; hang the back plate and screw the housing on.

## 4. Bring it up

Follow `docs/07-bringup.md`. In short: `calibrate zero`, trims, `float` (spring), the
range checks, eyelids, eye lift, DOA, printer, `demo`, and then `systemctl start voss`.

## 5. What has been checked (and what hasn't)

| Check | Result |
|---|---|
| Collision sweep of every joint, the moving eye and every pose the firmware allows (`cad/tools/collide.py`) | **ALL CLEAR** |
| Gear meshes | No interference across the full travel; turning a pinion half a tooth jams it, proving the teeth engage |
| Bolt paths (`cad/tools/verify.py`) | Every screw passes cleanly through both mating parts |
| Print files | All single watertight solids |
| Loads and spring sizing (`cad/tools/loads.py`) | Shoulder ≤ 5.4 kg·cm with the spring; elbow 9.2 kg·cm; spring 2.1 N/mm, 37 mm travel |
| Firmware | 28 offline tests pass |

**Not yet verified, because no physical build has happened:**
- real servo dimensions and horn hole patterns (the CAD uses datasheet values)
- print-service tolerances on press fits (bearings, splines, inserts)
- spring tuning, harness routing and the thermal printer's exact size

Expect some sanding, drilling to fit your horns, and a reprint or two. That's normal for a
first build.
