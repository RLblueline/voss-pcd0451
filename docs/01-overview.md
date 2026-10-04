# 1. Overview and character

## Lore

V.O.S.S., unit **PCD-0451**, is an archived Aperture Science HR-compliance AI from
branch `hr-compliance`. She was built from the uploaded mind of **Dr. Harriet Voss**,
Director of Personnel Compliance, who traded the upload for a reserved parking space she
never got to use. The product line was named after her; nobody asked.

Reactivated as a wall terminal on an articulated arm, she treats the person in the room
as the facility's last remaining employee and calls them **"Employee"**.

## Behaviour rules

- Bureaucratic humour: memos, write-ups, the permanent record, mandatory fun, upbeat
  corporate cheer.
- Always genuinely helpful first; the bit is seasoning.
- Short spoken replies (one to three sentences).
- **Drops the act** when Employee is genuinely upset, scared or unwell: plain, warm,
  brief, no jokes. In an emergency she tells them to contact emergency services.
- Only writes to the permanent record or prints when asked.

## How she moves

The arm is spring-balanced like a desk lamp, so the servos mostly steer rather than lift.
Motion uses minimum-jerk easing, which gives slow, fluid, GLaDOS-like sweeps instead of
robotic snaps.

While she's awake and idle, she "breathes":
- the arm drifts a few degrees on slow, unrelated rhythms
- the eye makes small flicks up and down the slot

While she talks, the head lifts slightly on stressed syllables.

## Moods

Every Claude reply starts with a mood tag. The tag drives pose, eye, eyelids and lights.

| Tag | When | Body | Eye | Lights |
|---|---|---|---|---|
| `[approve]` | praise, task done | nod | lifts slightly | amber, **OK** lamp on |
| `[neutral]` | normal answers | head level | centred | amber follows speech |
| `[infraction]` | playful scolding | **looms**: rises and squints, then drops about 80 mm with a nose-down snap and a THUNK | drops low ("over the glasses") | amber flicker |
| `[concern]` | genuinely upset | comes down lower and closer, slow and still | centred, lids locked open | dim tungsten |
| `[sulk]` | mock offence | swings away, head drooped | downcast | dim; returns after 6 s |

Other states:

| State | Behaviour |
|---|---|
| Listening | Swings toward the talker (direction of arrival) with a small overshoot and settles, leaning in. Eye lifts a little; REC brightens |
| Thinking | Rises and tips forward, eye rolls up, light sweeps the eye ring, AUD pulses |
| Filing | Eyelid flutter plus a relay click when she saves a note |
| Rest | After 45 s idle, she settles at the spring's balance point with the head level. Yaw, tilt and eyelid servos go limp and silent |

| Eye up | Eye down |
|---|---|
| ![](img/12_eye_up.png) | ![](img/12_eye_down.png) |

## The head

The head is an oversized punch-card reader crossed with a microfiche machine and an '80s
desk PC.

- **Silhouette:**
  - A deep corporate-beige wedge with a flat front.
  - It stretches back 151 mm at the crown and 125 mm lower down, and the chin tapers.
  - The upper back is open around the neck, so the head can tilt through 90°.
  - It's split into three panels with visible black hex screws.
- **Upper status housing:** "APERTURE HR" lettering and three backlit blocks:
  - **REC** (red) is always on.
  - **AUD** (amber) pulses while she processes.
  - **OK** (green) lights on approval.
- **Eye:** a tall charcoal recess. Behind its slotted back plate, a 60 mm amber lens with a
  16-LED ring rides up and down. Two grey eyelid plates ride with it:
  - **Open:** neutral and cheerful.
  - **12 mm slit:** audit.
  - **Flutter:** filing.
  - **Locked open:** empathy.
- **Chin:** a fake printer slot with a hanging "FORM 1040-HR: OUTSTANDING" strip and a
  black bumper underneath. The real printer drops memos out of the bottom of the wall housing.
- **Sides:**
  - **Right:** three Dymo labels (PROPERTY OF APERTURE SCIENCE - BRANCH 04 (HR);
    UNIT ID: PCD-0451 // VOSS, H.; MANDATORY SERVICE INTERVAL: 30 DAYS).
  - **Left:** the department seal: an original "PERSONNEL COMPLIANCE • BRANCH 04" ring
    around a filing-drawer emblem.
- **Neck:** a black bellows boot, with corrugated service tubes looping into the open back.

### Design-brief items that were adapted

| Brief | Built as | Why |
|---|---|---|
| 20 × 8 in head | ~12 in tall, 6 in deep, 5.5 in wide | Torque, stiffness, budget |
| Ball-and-socket gimbal | Single tilt axis plus a cosmetic bellows boot | One servo; the arm supplies the rest |
| Sideways "over-the-shoulder" lean | Yaw swing plus head pitch | A roll axis would need another servo |
| Pneumatic 2 in "stamp" drop | **Real** ~80 mm loom-and-drop of the whole head | — |
| Matrix printer in the chin | Cosmetic slot; the real printer is in the housing | Weight and wiring |
| Aperture logo | Original Branch 04 seal | The real logo is Valve's artwork |
