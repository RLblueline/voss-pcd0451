# 5. Assembly

Build in this order so you can test each stage before it gets buried. Do the software
bring-up checks in [Bring-up](07-bringup.md) at the steps marked ⚡.

![Arm detail](img/10_arm_detail.png)

## 0. Before you print

1. Measure your MG996R, DS3218 and SG90. Note body L × W × H, flange height and length,
   shaft offset, and mount-hole spacing. Edit `MG`, `DS` and `SG` in `cad/memo.scad`.
2. Measure the printer module and speaker, and edit `electronics()` and the housing
   grille and printer bay.
3. Re-run `./tools/export.sh` and `python3 tools/collide.py`. Only print once it says
   `ALL CLEAR`.

## 1. Electronics on the bench ⚡

1. Flash Raspberry Pi OS Lite (Bookworm, 64-bit) and run `deploy/install.sh`.
2. Wire everything on a breadboard exactly as in [Hardware → Wiring](02-hardware.md#wiring).
3. Test mics, amp, LEDs, printer and PCA9685 with `memo.calibrate` before anything goes
   into plastic.

## 2. Housing

1. Press M3 heat-set inserts into the back-plate edges and standoffs.
2. Mount the Pi Zero 2 W (upper standoffs) and PCA9685 (lower standoffs) on the back plate.
3. Fit the speaker behind the grille, the mics behind their holes (ports facing the holes),
   the amp beside the speaker, and the printer in its bay with paper exiting the front slot.
4. Fit the DC jacks in the bottom. Put the 1000 µF capacitor across the PCA9685 V+/GND.
5. Fasten the yaw tower to the housing front with 4 × M3. Route the servo cables through
   the 12 mm hole.

## 3. Yaw

1. Press a 608 into each tower shelf.
2. Mount the MG996R in the tower's servo shelf, shaft up and body toward the wall.
   ⚡ Run `calibrate zero` (yaw 90).
3. Push the 8 mm shaft down through both bearings into the coupler on the yaw horn, with the
   turret facing straight out. Clamp the turret's base on top of the shaft with its M3 screw.

## 4. Shoulder

1. Mount the 35 kg·cm servo through the turret's flange plate, shaft toward +Y and body down.
   Press a 624 into the turret's pivot plate.
2. ⚡ Zero the servo (shoulder 0 = link1 level).
3. Fit link1's horn-side plate to the horn and its other plate onto an M4 shoulder bolt through
   the 624, with link1 level.
4. **Support the arm by hand or with a prop from here on** whenever the servos are unpowered.
5. Optional but recommended: hook a tension spring from the top of the turret to the anchor on
   link1's beam.

## 5. Elbow and tilt post

1. Mount a DS3218 in link1's elbow bracket, body lying back along the beam. Press in a 624.
2. ⚡ Zero it. Fit link2's side plates on the horn and the pivot bolt with the links in line.
3. Bolt the tilt post under link2's end block (2 × M3). Mount the second DS3218, body up,
   and press in a 624. ⚡ Zero it.

## 6. Eye cartridge

1. Glue or screw the bezel to the cartridge frame's front standoffs.
2. Mount the LED ring (LEDs facing forward) on the rear plate. Fit the lens dome into the holder.
3. Mount the SG90 on its plate. ⚡ Run `calibrate set shutter 1`, then press the pinion
   on with both shutters fully open.
4. Slide both shutter tongues into the left rail groove and mesh the racks with the
   pinion. ⚡ Sweep `calibrate set shutter 0` and back, then tune
   `calibrate shutter <closed> <open>` until the slit is 12 mm and the open plates
   disappear behind the bezel.

## 7. Head

1. Fit the status-bar WS2812 boards behind the three windows and chain them after the
   eye ring.
2. Slide the eye cartridge into the middle shell, then join top, middle and chin with
   M3 screws through the seam bosses.
3. Bolt the + ear to the DS3218 horn and pass the M4 pivot bolt through the − ear into
   the 624. Fit the ears into the head crown and screw them to the top shell.
4. Fit the TPU neck boot over the crown slot. Glue a printed paper strip into the chin
   slot and add the bumper.

## 8. Wall

1. Find a stud. Drive two #8 screws 150 mm apart vertically, leaving the heads 4 mm proud.
2. Hang the back plate on the keyholes, slide the housing over it, and fix it with the
   four side screws.
3. Check that the arm at full reach is clear of door swings and walkways (the head front
   sits about 390 mm off the wall).
4. ⚡ Run the full bring-up and then `sudo systemctl start memo`.
