# 3. Mechanical design

All dimensions in mm. The model is `cad/voss.scad`; every number below is a named
parameter at the top of that file.

## Frame

X along the wall, Y out of the wall, Z up. Wall face is y = 0. The yaw axis is vertical at
**(0, 112)**. The shoulder pitch axis crosses it at z = 0. The firmware uses the same frame
(`voss/config.py`).

![Side view](img/03_side.png)

## Joints

| Joint | Axis | Servo | Range (checked) | Zero |
|---|---|---|---|---|
| Yaw (base) | vertical, (0, 112) | MG996R | 5–175° | 90 = straight out from the wall |
| Shoulder | horizontal, on the yaw axis at z 0 | DS3225 + counterbalance spring | −20…+75° | 0 = link1 level, + lifts |
| Elbow | horizontal, 120 mm along link1 | DS3225 | −110…+40° | 0 = links in line |
| Head tilt | horizontal, 14 mm past link2 and 72 mm below it | DS3218 | **−40…+50°** relative to link2 | 0 = head in line with link2 |
| Eyelids | rack and pinion on the eye carriage | SG90 | 0–1 | 1 = open |
| Eye lift | rack and pinion, carriage on two rods | SG90 | ±24 mm (−1…1) | 0 = centred |

**Head pitch.** The firmware commands absolute head pitch and derives
`tilt = pitch + shoulder + elbow`. Lifting the arm keeps the head level unless she means
otherwise. The shoulder does most of the raising and lowering: the head's height range is
about 155 mm, and the infraction stamp drops it about 80 mm.

| Raised (rest / balance point) | Stamp (dropped) |
|---|---|
| ![](img/04_raised.png) | ![](img/06_stamp.png) |

| Deep nod (+45°) | Looking up (−40°, eye high) |
|---|---|
| ![](img/13_deep_nod.png) | ![](img/14_look_up.png) |

## How the arm is built

![Arm detail](img/10_arm_detail.png)

- **Joint brackets.** Every pitch joint uses the same bracket:
  - the servo mounts through a flange plate
  - a pivot plate holds a 624 bearing coaxial with the shaft on the far side
  - two side bars tie the plates together
- **Links.** The next link wraps each bracket with two side plates. One sits on the horn;
  the other rides an M4 shoulder bolt in the 624. At 36–44 mm from the axis, a cross block
  joins the plates to a hollow 20 × 24 mm centre beam.

| Assembly | What it is |
|---|---|
| Yaw tower (world) | Bolted to the housing front. An 8 mm shaft runs in two 608 bearings 52 mm apart, which carry the arm's moment. The MG996R below drives the shaft through a horn coupler |
| Turret (yaw frame) | Clamped to the top of the shaft. Joint bracket with the shoulder servo body down, plus the **gooseneck spring mast** |
| Link1 | Side plates around the turret, centre beam with a top cover, and the elbow joint bracket. Has the counterbalance cable eye |
| Link2 | Side plates around the elbow bracket, centre beam with a top cover, end block carrying the tilt post |
| Tilt post | Joint bracket with the DS3218 body pointing up. The neck narrows above the flange to clear the crown |

### Desk-lamp counterbalance

The trick from Anglepoise lamps: a spring whose force is proportional to its stretched
length exactly cancels a link's weight at every angle, if two conditions hold:
- one end sits directly above the pivot
- the other end sits on the link's axis line

Our version:

| Element | Detail |
|---|---|
| Pulley | 70 mm above the shoulder axis, on the end of a gooseneck mast that rises behind the turret |
| Cable eye | On link1's axis line, 44 mm out, in the plane y = −35 (outside the link) |
| Spring | Inside the mast, fed by a braided cable over two pulleys. A tensioner screw at the bottom sets the initial-tension offset, so it behaves like an ideal zero-length spring |
| Size | Rate about 0.8 N/mm; cable span 30–95 mm; force 24–76 N |

The cable plane sits outside the link, so the cable never crosses the arm. The mast's
radius from the yaw axis clears the housing at every yaw.

## Loads

From `cad/tools/loads.py`. Masses come from the CAD volumes: head about 690 g, centre of
gravity 1 mm from the tilt axis. Values are static, in kg·cm, with link2 level.

| Shoulder angle | Shoulder (gravity) | Shoulder (with spring) | Elbow |
|---|---|---|---|
| −20° | 19.4 | −4.5 | 9.2 |
| 0° | 20.0 | −5.4 | 9.2 |
| 20° (home) | 19.3 | −4.5 | 9.2 |
| 45° | 16.8 | −1.1 | 9.2 |
| 60° | 14.6 | +1.9 | 9.2 |
| 75° | 12.0 | +5.4 | 9.2 |

- **Shoulder.** The DS3225 works at no more than about 22% of its rating. If the spring
  ever fails it can still hold the arm (about 80%), but don't run it that way.
- **Unpowered.** The arm floats to about **51°** and stays there.
- **Elbow.** The DS3225 runs at about 37%.
- **Tilt.** The head is a balanced pendulum, so tilt needs at most about 6 kg·cm at
  ±45°. The DS3218 runs at about 30%.

## Head

![Front](img/02_front.png)

**Envelope (shell frame):**
- flat front at x 45
- back at x −105 at the crown and x −80 at z −230, so the top half stretches back further
- the chin tapers to 90 × 92 at z −270
- 140 wide at the crown

**Mounting:**
- The shell is shifted 15 mm (`HS`) relative to the tilt axis, so the deeper head's
  centre of gravity hangs under the axis.
- **Shell:** 2.4 mm walls in three pieces split at z −40 and −195, with skirts, M3 bosses
  and black hex screws.
- **Open back:** the neck slot runs from the crown down to 28 mm below the tilt axis and
  through the whole upper back. It widens to ±35 behind the ears, so link2's cross block
  can dip into it on deep nods. That gives the 90° tilt range, and it's where the service
  tubes enter.

### Moving eye

| Eye up, lids open | Eye down, lids closed |
|---|---|
| ![](img/08_eye_mechanism_s1.png) | ![](img/08_eye_mechanism_s0.png) |

**Fixed parts:**
- **Slotted plate:** the recess back, x 27–29. It has a 68 mm wide stadium slot covering
  the eye's ±24 mm travel.
- **Guide rods:** two 3 mm steel rods at y ±30, mounted on top and bottom bars.
- **Lift drive:** an SG90 on a strut drives a 36-tooth pinion (r 18) against a rack on the
  carriage's back. ±80° of servo gives ±24 mm.

**Carriage** (moves as one, about 70 g, so the lift servo barely notices it):

| x (shell frame) | Part |
|---|---|
| 25–26.6 | **Mask** (eye socket) with a Ø66 window. 166 tall, so it always covers the slot and hides the open eyelids |
| 22.6–24.6 | Eyelid plates (84 × 40) |
| 18.8–22.4 | Racks + eyelid pinion (r 9) |
| 15.4–18.6 | Rack backing rails |
| 13–21 | Ø60 amber lens |
| 8–12 | 16-LED ring |
| 3–6 | Rear plate |
| −4…3 | Rod bushings and lift rack |

**Eyelids.** Each plate travels 27 mm in opposite directions (about 172° of SG90 rotation).
Closed, they leave a 12 mm slit.

## Arm covers and harness

- **Covers.** Top-only shrouds snap onto the link beams with two clip screws each.
  - link1: x 46–74, stopping short of the elbow bracket
  - link2: x 46–96, stopping short of the tilt post
  - Each is 30 wide, open underneath, with 2 mm walls.
- **Harness.** The wire bundle and its zip ties sit on top of the beam under the cover.
  Between covers, the harness runs through corrugated service tubes with slack for each joint:
  - housing → turret
  - over the elbow
  - link2 → head

## Housing and tower

![Housing interior](img/09_housing_cut.png)

- **Housing:** 144 × 70 × 226.
- **Front:** mics 80 mm apart, speaker grille on the left, the department seal on the
  right, lettering along the bottom.
- **Underside:** the printer is mounted exit-down, so memos drop out of a slot in the
  bottom face with a tear bar.
- **Sides:** DC jacks and vents.
- **Wall:** the back plate has keyholes for one stud.

## Collision check results

`cad/tools/collide.py` sweeps:
- **yaw:** 5° steps with the arm at home
- **shoulder:** 5° steps with link2 level
- **elbow:** 5° steps with the head
- **tilt:** −40…+50° with the eye at both ends of its travel and the lids open and closed
- **eye and eyelids:** heights −1/0/1 × lids 0/0.5/1 against everything in the head

It then tests a 4-D grid of yaw, shoulder, elbow and head pitch. Every pose the firmware
accepts is checked for head, links and covers against the housing, tower, wall and the
arm itself.

```
yaw 5..175 : turret/link1 vs housing/tower         OK
shoulder -20..75 : link1/link2 vs turret/tower     OK
elbow -110..40 : link2/head vs link1/turret        OK
tilt -40..50 : head vs link2/post                  OK
eye -1..1, shutters 0..1 : vs head internals       OK
firmware workspace: 429 poses accepted, 1881 rejected
accepted poses : arm/head vs housing, tower, wall, arm OK
```

Gear meshes (pinions against racks) are excluded, because the tooth profiles are approximate.

## Known risks

1. **Spring tuning.** The balance is only as good as the spring. Use `voss.calibrate float`
   and the tensioner screw (see [Bring-up](07-bringup.md)).
2. **Unverified dimensions.** Servo, printer and speaker dimensions are datasheet values,
   and the DS3225s are modelled at DS3218 size. Measure yours.
3. **Head weight.** About 690 g with 2.4 mm walls. 1.6 mm walls bring it nearer 520 g and
   ease every joint; re-run `loads.py` and re-fit the spring.
4. **Eye lift backlash.** A loose lift pinion lets the eye drop a little when the servo
   is released. The firmware keeps the eye servo powered.
5. **Projection.** At home the head front sits about 400 mm off the wall. Mount it away
   from walkways.
6. **Print bed.** The housing needs a bed of at least 230 mm in one axis; the head crown
   is 151 × 140.
