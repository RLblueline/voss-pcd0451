# Changelog

## v0.4 — classic arm (2026-10)

**Arm**
- Replaced the fold-flat horizontal-plane arm with a classic one: base yaw, then shoulder,
  elbow and head-tilt pitch.
- New yaw tower: an 8 mm shaft in two 608 bearings, driven by an MG996R.
- Shoulder and elbow brackets reuse the tilt-post joint bracket, with 624 bearings opposite
  each servo.
- Links are side plates around each bracket feeding a hollow centre beam.

**Servos and power**
- 35 kg·cm shoulder, DS3218 elbow, DS3218 tilt, MG996R yaw.
- Servo supply raised to 6 V 10 A.
- PCA9685 now uses channels 0–4.

**Firmware**
- Pose model is now yaw / shoulder / elbow / absolute head pitch; the tilt servo is derived,
  so the head stays level.
- New workspace check: the head is a plan-view capsule that follows its pitch swing, checked
  against the housing, the yaw tower and the wall.
- The shoulder and elbow always hold. Rest folds the arm upright and releases only yaw, tilt
  and shutters. Shutdown lowers the arm before cutting power.
- The stamp is now a real ~50 mm drop.

**CAD and docs**
- Collision checker rewritten for the new joints and run against a 4-D firmware pose grid:
  all clear.
- Docs and renders updated.


## v0.3 — rebuild (2026-10)

The v0.2 project files were unavailable, so everything was rebuilt from the written spec.

**Hardware**
- Bigger head: ~300 × 140 × 90 mm (was a 76 mm pod).
- Servos: MG996R shoulder and elbow, DS3218 tilt (were 3× MG90S), plus a new SG90 driving
  the eye shutters.
- Separate 6 V servo supply. PCA9685 OE on GPIO17 cuts servos at rest and while printing.
- 19 LEDs: a 16-LED eye ring plus REC, AUD and OK status blocks.

**Geometry**
- Shoulder axis moved to y = 108 and housing deepened to 70 mm, to fit the MG996R
  bracket and the printer.
- Head hangs as a pendulum from a tilt axis near its top, at z −184.

**Firmware**
- Workspace model changed to head centre 114 / radius 84.
- Shutter calibration defaults 4–176°.
- Shoulder and elbow speeds reduced for the heavier head.

**New**
- Full parametric OpenSCAD model, STLs, renders and a mesh-based collision checker.
- This documentation.

## v0.2

Original software and MG90S CAD (not included in this repository).
