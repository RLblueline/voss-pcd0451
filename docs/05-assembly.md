# 5. Assembly

Build in this order so you can test each stage before it gets buried. Do the software
bring-up checks in [Bring-up](07-bringup.md) at the steps marked ⚡.

![Arm from behind](img/10_rear_arm.png)

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
5. Fasten the shoulder bracket to the housing front with 4 × M3. Route the shoulder servo
   cable through the 10 mm hole.

## 3. Shoulder

1. Press a 608 into the bracket floor pocket.
2. Drop the shoulder MG996R into the bracket, shaft up and body toward the wall. Screw
   the flange to the shelf.
3. ⚡ Run `calibrate zero` so the servo sits at 90°.
4. Fit the horn to the link1 top plate, then press it onto the spline with link1 pointing
   straight out. Insert the M8 pin up through link1's bottom plate into the 608, and
   tighten the nyloc just enough to remove play.

## 4. Elbow

1. Bolt the elbow hanger under link1's bottom plate (4 × M3). Press a 608 into its floor.
2. Mount the elbow MG996R, shaft up and body toward the shoulder.
3. ⚡ Zero the servo. Fit link2 with the links in line. Insert the M8 pin from below.

## 5. Tilt post

1. Bolt the tilt post under link2's tab (2 × M3). Press a 624 into the pivot plate.
2. Mount the DS3218 through the mount plate, shaft toward +Y and body up.
3. ⚡ Zero the servo.

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
