# 5. Assembly

Build in this order so each stage gets tested before it's buried. Do the checks in
[Bring-up](07-bringup.md) at the steps marked ⚡.

![Arm detail](img/10_arm_detail.png)

## 0. Before you print

1. Measure your MG996R, DS3225, DS3218 and SG90s (body, flange, shaft offset, holes). Edit
   `MG`, `DS` and `SG` in `cad/voss.scad`.
2. Measure the printer module and speaker; edit `electronics()` and the housing.
3. Run `./tools/export.sh` and `python3 tools/collide.py`. Print only after `ALL CLEAR`.

## 1. Electronics on the bench ⚡

1. Flash Raspberry Pi OS Lite (Bookworm, 64-bit) and run `deploy/install.sh`.
2. Wire everything on a breadboard as in [Hardware → Wiring](02-hardware.md#wiring).
3. Test mics, amp, LEDs, printer and all six servo channels with `voss.calibrate`.

## 2. Housing

1. Press heat-set inserts into the back-plate edges and standoffs. Mount the Pi and PCA9685.
2. Fit:
   - the speaker behind the left grille
   - the mics behind their holes
   - the amp beside the speaker
3. Fit the printer exit-down over the slot in the bottom face.
4. Fit the DC jacks in the right side, and the 1000 µF capacitor across the PCA9685 V+/GND.
5. Fasten the yaw tower to the front with 4 × M3. Route the harness through the 12 mm hole.

## 3. Yaw

1. Press a 608 into each tower shelf.
2. Mount the MG996R shaft up, body toward the wall. ⚡ Run `calibrate zero` (yaw 90).
3. Screw the printed coupler to the MG996R horn and fit the horn. Push the 8 × 80 mm shaft
   down through both bearings into the coupler and tighten its M3 set screw. Fit the turret
   on top facing straight out and clamp it with its M3 screw.

## 4. Shoulder and counterbalance

1. Mount a DS3225 in the turret, shaft +Y, body down. Press a 624 into the pivot plate.
2. ⚡ Zero it. Fit link1 level: horn-side plate on the horn, other plate on the M4 bolt.
3. **Support the arm whenever the servos are unpowered until the spring is in.**
4. Hook the spring to the tensioner screw at the bottom of the mast bore, and hook the
   spring block (with its 7 mm pulley on an M3 axle) to the top of the spring.
5. Fit the 10 mm pulley on its M3 axle at the top of the mast.
6. **Reeve 2:1:** cable eye on link1 → over the top pulley → down under the spring-block
   pulley → up to the M3 anchor pin. Crimp it with the arm at 75° and the spring just taut.
7. ⚡ Tune with `calibrate float` (see [Bring-up](07-bringup.md#tuning-the-spring)).

## 5. Elbow and tilt post

1. Mount a DS3225 in link1's elbow bracket, body lying back along the beam. Press in a 624.
2. ⚡ Zero it. Fit link2 with the links in line.
3. Bolt the tilt post under link2's end block. Mount the DS3218 body up, press in a 624, and ⚡ zero it.

## 6. Eye

1. Fit the LED ring (LEDs forward) and the lens dome into the carriage.
2. Mount the eyelid SG90. ⚡ Run `set shutter 1`, then press its pinion on with both lids open.
3. Slide the lid tongues into the left rail groove and mesh the racks.
   ⚡ Run `set shutter 0` and back, then `shutter <closed> <open>`, until you get a 12 mm slit.
4. Push the two 3 mm rods through the carriage bushings and into the top and bottom mount bars.
5. Mount the lift SG90 on its strut. ⚡ Run `set eye 0`, then press the 36 T pinion onto the
   carriage rack with the eye centred.
6. ⚡ Run `set eye 1` and `set eye -1`. The eye should glide the full slot with no binding.

## 7. Head

1. Fit the status-bar LEDs behind the three windows and chain them after the eye ring.
2. Slide the eye assembly into the middle shell and fix the two rod bars with 6 × M3
   through the side walls into the bar-end inserts. Glue the slot plate behind the recess.
3. Press M3 inserts into the seam bosses of the top and middle pieces. Join the pieces with
   8 × M3 × 16, screwed up from inside the lower piece.
4. The ears are part of the crown print. Through the open back, bolt the + ear to the
   DS3218 horn, and pass the M4 pivot through the − ear into the 624.
5. Fit the TPU neck boot, the bumper, and a printed paper strip in the chin slot.

## 8. Harness and covers

1. Bundle the elbow, tilt, eyelid and eye-lift leads plus the LED line, then route them:
   - housing → corrugated loop → turret
   - top of link1 → loop over the elbow → top of link2
   - two neck tubes → open back of the head
2. Leave about 30 mm of slack at every loop. Run the arm through its range with
   `calibrate demo` and watch for snags.
3. Zip-tie the bundle to the beam tops and snap the covers on (2 × M3 each).

## 9. Wall

1. Find a stud. Drive two #8 screws 150 mm apart vertically, heads 4 mm proud.
2. Hang the back plate on the keyholes, slide the housing on, and fix the four side screws.
3. Check the reach envelope: the head swings up to about 430 mm out and about 255 mm to
   each side (see [Software → Reach](06-software.md#reach)).
4. ⚡ Run the full bring-up, then `sudo systemctl start voss`.
