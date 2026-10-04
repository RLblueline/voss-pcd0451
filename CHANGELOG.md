# Changelog

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
