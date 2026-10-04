# 3. Mechanical design

All dimensions in mm. The model is `cad/memo.scad`; every number below is a named
parameter at the top of that file.

## Frame

X along the wall, Y out of the wall, Z up. Wall face is y = 0. The yaw axis is vertical at
**(0, 112)**. The shoulder pitch axis crosses it at z = 0. The firmware uses the same frame
(`memo/config.py`).

![Side view](img/03_side.png)

## Arm layout: classic yaw, pitch, pitch

| Joint | Axis | Servo | Range (checked) | Zero |
|---|---|---|---|---|
| Yaw (base) | vertical, (0, 112) | MG996R | 5–175° | 90 = straight out from the wall |
| Shoulder | horizontal, on the yaw axis at z 0 | 35 kg·cm standard size (DS3235 class) | −20…+75° | 0 = link1 level, + lifts |
| Elbow | horizontal, 120 mm along link1 | DS3218 | −110…+40° | 0 = links in line |
| Head tilt | horizontal, 14 mm past link2 and 72 mm below it | DS3218 | −35…+40° relative to link2 | 0 = head in line with link2 |
| Shutters | rack and pinion | SG90 | aperture 0–1 | 1 = open |

**Head pitch.** The firmware works in absolute head pitch and derives the tilt servo as
`tilt = pitch + shoulder + elbow`. Lifting the arm doesn't tip the head unless she means it to.
Because tilt is limited to −35…+40°, link2 stays near level for a level head. The
shoulder does most of the raising and lowering:
- head height range about 155 mm
- the infraction "stamp" drops the head about 50 mm (2 in) with a nose-down snap

| Raised (rest pose) | Stamp (dropped) |
|---|---|
| ![raised](img/04_raised.png) | ![stamp](img/06_stamp.png) |

## How the joints are built

Every pitch joint uses the same **joint bracket**:
- the servo is mounted through a flange plate
- a pivot plate holds a 624 bearing on the servo's far side, coaxial with the shaft
- two side bars tie the plates together

The next link wraps the bracket with two **side plates**:
- one plate sits on the servo horn (y 27.25–30.75)
- the other rides an M4 shoulder bolt in the 624 (y −31…−27.5)

At 36–44 mm from the axis, a cross block joins the side plates to a hollow 20 × 24 mm
centre beam. The beam has a cable slot.

![Arm detail](img/10_arm_detail.png)

| Assembly | What it is |
|---|---|
| Yaw tower (world) | Bolted to the housing front. An 8 mm steel shaft runs in two 608 bearings 52 mm apart, so the bearings carry the arm's moment, not the servo. The MG996R below drives the shaft through a horn coupler |
| Turret (yaw frame) | Clamped to the top of the shaft. Joint bracket with the shoulder servo body pointing down |
| Link1 | Side plates around the turret, centre beam, and the elbow joint bracket at its end (servo body lies back along the beam). Has an anchor for an optional counterbalance spring |
| Link2 | Side plates around the elbow bracket, centre beam, and an end block that carries the tilt post |
| Tilt post | Joint bracket with the DS3218 body pointing up. The neck narrows above the servo flange to clear the head crown at −35° nose-up |

## Loads

Masses come from the CAD volumes, roughly 535 g for the head. Values are static torques.

| Pose | Shoulder | Elbow |
|---|---|---|
| Arm straight out (worst) | 16.0 kg·cm | 7.4 kg·cm |
| Home (shoulder 20, elbow −20) | 15.5 kg·cm | 7.4 kg·cm |
| Rest (shoulder 60, elbow −60) | about 11.5 kg·cm | 7.4 kg·cm |

That gives about 2.2× margin on a 35 kg·cm shoulder servo and 2.7× on the DS3218 elbow.

The yaw servo carries no gravity load. The 608 pair takes about 35 N each from the arm's
moment.

## Head

![Front](img/02_front.png)

The head is unchanged from v0.3:
- **Size:** 300 tall × 90 deep × 140 wide, hanging from the tilt axis near its top.
- **Shell:** 2.4 mm, three pieces split at z −40 and −195.
- **Eye recess:** 80 × 136.
- **Status windows:** three, at the top.
- **Chin slot:** 92 × 4.

### Eye mechanism

| Shutters open | Shutters closed (audit slit) |
|---|---|
| ![open](img/08_eye_mechanism_s1.png) | ![closed](img/08_eye_mechanism_s0.png) |

| x (head frame) | Part |
|---|---|
| 45 | front face |
| 28–45 | charcoal recess |
| 26–28 | bezel, Ø66 opening |
| 23.6–25.6 | shutter plates (84 × 40) |
| 19.8–23.4 | racks + pinion (module 1, 18 T) |
| 16.4–19.6 | rack backing rails |
| 14–22 | Ø60 amber lens |
| 9–12 | 16-LED ring |
| 4–7 | rear plate |

The pinion sits between the two racks, so the plates move in opposite directions. Each
travels 27 mm, which takes about 172° of SG90 rotation. When closed, a 12 mm slit is left
across the lens.

## Housing and tower

![Housing interior](img/09_housing_cut.png)

- **Housing:** 144 × 70 × 226, open back. Front features:
  - mics 80 mm apart
  - 40 mm speaker grille
  - printer exit at z −137
  - four M3 holes and a 12 mm cable hole for the yaw tower
- **Back plate:** keyholes for one stud.
- **Yaw tower:** from z −162 (servo bottom) to −46, centred on x = 0 in front of the housing.

## Collision check results

`cad/tools/collide.py` sweeps each joint through its full range and intersects the real part
meshes:
- **yaw:** 5° steps with the arm at home
- **shoulder:** 5° steps with link2 level
- **elbow:** 5° steps, with the head included
- **tilt:** 5° steps with shutters open and closed
- **shutters:** at 0, 0.5 and 1

It then checks a grid of yaw, shoulder, elbow and head-pitch poses. Every pose the
firmware accepts is tested for head, links and servos against the housing, tower, wall and
the arm itself.

```
yaw 5..175 : turret/link1 vs housing/tower         OK
shoulder -20..75 : link1/link2 vs turret/tower     OK
elbow -110..40 : link2/head vs link1/turret        OK
tilt -35..40 : head vs link2/post                  OK
shutters 0..1 : plates vs head internals           OK
firmware workspace: 260 poses accepted, 1126 rejected
accepted poses : arm/head vs housing, tower, wall, arm OK
```

One finding fed back into the firmware: pitching the head nose-down swings its bottom up
to about 135 mm back toward the wall. The workspace check therefore treats the head as a
plan-view capsule along that swing.

## Known risks

1. **Holding torque.** The shoulder and elbow hold the arm up all the time, so they can't go
   limp at rest. At home the shoulder servo works at about 45% of its rating, which means
   heat and hum over long idle periods. Mitigations:
   - The rest pose folds the arm up (about 25% less load).
   - The **recommended fix** is a tension spring from the turret top to the anchor on link1's
     beam, sized to cancel about 10 kg·cm. With it, the servo mostly just steers.
2. **Power loss.** If power is lost, the arm sags to its mechanical stop. On a normal
   shutdown the firmware lowers it gently first. Don't stand under the head, and use the
   spring.
3. **Unverified dimensions.** Servo, printer and speaker dimensions are datasheet values.
   The shoulder servo is modelled with standard-size (DS3218) dimensions; check your
   35 kg·cm servo's flange and height.
4. **Projection.** At home the head front sits about 385 mm off the wall, and reach changes
   with pose. Mount it away from walkways.
5. **Print bed.** The housing needs a bed of at least 230 mm in one axis.
