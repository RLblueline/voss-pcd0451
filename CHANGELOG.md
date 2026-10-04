# Changelog

## v0.6 — expression engine (2026-10)

**Motion engine**
- Rebuilt as a queue of timed segments with easing styles (`ease`, `spring`, `snap`,
  `slow`, `hold`). There are no gesture threads any more. Tests and the animation tool
  drive it on a virtual clock.

**Gestures**
- New `voss/gestures.py` with 13 data-defined gestures: nod, bounce_nod, shake, peer,
  double_take, startle, sigh, scan, curious, stamp, glance_back, flutter, ack.
- Uses anticipation, overshoot-and-settle, holds, and eye/lid secondary motion.

**Claude control**
- Replies can carry an optional gesture tag after the mood. The persona prompt lists them,
  and `persona.parse_tags()` parses them.

**Moods**
- Each mood has an entry pose, a signature gesture and an idle profile (sway amplitude and
  speed, blink rate).

**Secondary motion**
- Natural blinks with doubles, speech-onset emphasis nods, and eye-led looks.

**Tooling and docs**
- New `calibrate gesture <name>`.
- New 36 s animation (`docs/img/voss_expressive.mp4/.gif`) rendered from the CAD with the
  real motion engine.
- 28 tests, all passing.


## v0.5 — V.O.S.S. (2026-10)

**Rename**
- M.E.M.O. → **V.O.S.S.** (Virtual Oversight & Supervision System) everywhere: package
  `voss`, service `voss`, `VOSS_*` settings, persona, lettering, printed memos.
- New personnel-record bio (`docs/00-bio.md`).

**Arm**
- Desk-lamp counterbalance: a gooseneck spring mast on the turret, with the cable eye on
  link1's axis line. The shoulder load drops from ~20 to ≤5.4 kg·cm, and the arm floats
  at ~51° unpowered.
- Shoulder and elbow servos are now DS3225; the servo supply drops to 6 V 6 A.
- Top-only arm covers with the wire harness underneath. Corrugated service tubes at the
  base, over the elbow, and into the head.

**Head**
- Deeper head: 151 mm at the crown, 125 mm lower down, chin tapered. It's shifted 15 mm on
  the tilt axis so its CG hangs under the axis.
- Open upper back, widened behind the ears. Tilt range grows from −35…+40° to **−40…+50°**.
- **Moving eye:** lens, LED ring and eyelids ride a carriage ±24 mm up and down the slot
  on two 3 mm rods. A second SG90 drives it with a 36 T rack and pinion. A sliding mask
  hides the open lids at any height.
- Original "Personnel Compliance • Branch 04" department seal on the housing and the head's
  left side.

**Housing**
- Printer mounted exit-down (memos drop out of the bottom); the yaw tower blocked the old
  front slot.
- Speaker moved to the left; jacks and vents moved to the sides; lettering moved to the bottom.

**Firmware**
- New `eye` joint (channel 5) and mood-specific eye heights.
- GLaDOS-style motion: minimum-jerk easing, idle sway, eye saccades, a speech-driven head
  bob, overshoot-and-settle looks, and the loom-and-drop stamp.
- Workspace check models the tapered head as four depth sections that swing with pitch.
- Rest and park at the spring's balance point. New `calibrate float` for spring tuning.

**CAD tools**
- New `loads.py`, `head_mass.py` and `reach.py`.
- The collision sweep now covers the moving eye (3 heights × 3 lid positions) and the new
  tilt range: all clear.


## v0.4 — classic arm (2026-10, as M.E.M.O.)

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


## v0.3 — rebuild (2026-10, as M.E.M.O.)

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
