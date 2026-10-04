# 6. Software

Python 3, installed to `/opt/voss` and run as the systemd service `voss`.

## Pipeline

```
arecord (I2S stereo, 16 kHz) ──► openWakeWord ──► GCC-PHAT DOA ──► arm swings to the talker
                                                        │
                    webrtcvad endpointing + Vosk small-en (streaming, local)
                                                        │
             Claude (claude-haiku-4-5-20251001) ◄──► tools (timers, weather, notes, print…)
                                                        │
                    "[mood] reply"  ──►  pose + eye + eyelids + lights
                                                        │
           Piper en_US-amy-low ──► sox intercom filter + chime/sfx ──► aplay
                                   (speech envelope drives the eye light and a head bob)
```

- **Local stages:** the wake word and speech-to-text run on the Pi. Only the transcript goes to Claude.
- **Conversation memory:** the last 8 exchanges are kept as plain text.
- **Tool loop:** up to 5 tool rounds per reply.
- **Failure:** if Claude can't be reached, she says an in-character fallback line.

## Modules (`voss/`)

| Module | Role |
|---|---|
| `config` | Every setting, overridable with `VOSS_*` environment variables |
| `persona` | System prompt (lore and rules) and mood-tag parsing |
| `audio` | Capture thread (48→16 kHz decimator), playback with level envelope, GCC-PHAT direction of arrival |
| `stt` | Wake word and utterance capture with Vosk |
| `tts` | Piper → sox intercom chain → chime / thunk / relay-click sfx |
| `lights` | WS2812 over SPI (eye ring, REC, AUD, OK) at 50 Hz |
| `body` | PCA9685 driver, calibration, kinematics, workspace check, motion thread, alive overlay, gestures |
| `printer` | ESC/POS layouts: memo, write-up, commendation, checklist |
| `tools` | Claude tool schemas and handlers |
| `brain` | Claude tool-use loop and rolling history |
| `main` | Orchestration (voice mode, or `--text` keyboard mode) |
| `calibrate` | Bring-up command-line tool |

## Tools available to Claude

| Tool | What it does |
|---|---|
| `get_time` | Local date and time |
| `set_timer` / `list_timers` / `cancel_timer` | Countdown timers, announced aloud when they finish |
| `get_weather` | Open-Meteo (no key) for home or a named place |
| `checklist` | "Mandatory Preparedness Checklist" to-do list |
| `notes` | "Permanent record" notes: add, list, search, delete |
| `print_memo` | Print a memo, write-up, commendation or the checklist |

## Motion model

**Pose joints:** `yaw`, `shoulder`, `elbow`, `pitch` (absolute head pitch, + nose down),
`shutter` (eyelids 0–1) and `eye` (height in the slot, −1…1).

**Servo channels:** yaw, shoulder, elbow, tilt, shutter, eye. The tilt servo is derived
as `tilt = pitch + shoulder + elbow`; if that would leave −40…+50°, pitch is adjusted to fit.

| Pose | yaw | shoulder | elbow | pitch | eye | Notes |
|---|---|---|---|---|---|---|
| Home | 90 | 20 | −20 | 0 | 0 | |
| Listen / look | 90 − DOA | 12 | −8 | −4 | 0.2 | 6° overshoot, then settle |
| Think | — | 30 | −34 | 8 | 0.6 | eye rolls up |
| Stamp | — | 35 → −5 | −35 → 5 | 10 → 15 | −0.4 | loom, then ~80 mm drop at 4× speed |
| Concern | — | 8 | −10 | −3 | 0 | slow |
| Sulk | 145 | 30 | −30 | 15 | −0.6 | |
| Rest / park | 90 | 50 | −50 | 0 | 0 | spring balance point |

### Feeling alive (GLaDOS-style)

- **Easing:** minimum-jerk (quintic), so moves start and stop with no visible snap.
- **Alive overlay:** on top of the planned pose, while awake and not moving:
  - slow sway on unrelated periods: yaw ±4°, shoulder ±2.5°, pitch ±2°
  - pseudo-random eye flicks of ±0.12
  - it fades in over 1 s when she stops and out over 0.5 s when she moves
- **Speech bob:** the head lifts up to 3° on loud syllables, from the same envelope that
  drives the eye light.
- **Validation:** every overlay sample passes the workspace check, otherwise it's skipped.

## Motion safety

- **Workspace check.** Every target passes `body.workspace_ok()`:
  - joint limits, including the derived tilt
  - the elbow as a 30 mm circle
  - the head as four plan-view circles at increasing depth (crown to chin) that swing with
    head pitch

  These are checked against the housing, yaw tower and wall. The CAD collision sweep
  confirms every accepted pose is clear.
- **Path check.** Moves are interpolated in joint space; failing paths go via home.
- **Holding.**
  - The spring carries most of the shoulder load, so the shoulder and elbow hold quietly.
  - At rest, yaw, tilt and eyelids are released. The eye lift stays powered so the
    carriage doesn't sag.
  - While printing, motion is frozen, not cut.
  - On shutdown, the arm parks at the spring's balance point before OE cuts power.

## Reach

From `cad/tools/reach.py`, over every pose the firmware accepts with the head level:

| | |
|---|---|
| Home | head front about 400 mm from the wall; eye about 150 mm below the shoulder axis |
| Farthest out | head front about **430 mm** (17 in) from the wall |
| Tucked in | head centre about 130 mm from the wall (swung to the side) |
| Side to side | head centre up to about **±255 mm** (10 in) from the housing centreline, a sweep about 51 cm wide |
| Up and down | eye height range about **315 mm** (12 in) from the arm, plus 48 mm of eye travel in the slot |

## Configuration

Set values in `/etc/voss.env`:

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required |
| `VOSS_LAT`, `VOSS_LON` | — | Home weather location |
| `VOSS_TEMP_UNIT` | fahrenheit | or celsius |
| `VOSS_CAPTURE_RATE` | 16000 | 48000 if 16 kHz I2S capture is flaky |
| `VOSS_MIC_GAIN` | 4.0 | Software gain on the INMP441s |
| `VOSS_WAKE_MODEL` | hey_jarvis | Path to a trained `hey_voss.onnx` |
| `VOSS_WAKE_THRESHOLD` | 0.5 | Raise if she wakes by accident |
| `VOSS_LED_BRIGHTNESS` | 0.6 | Global LED brightness |
| `VOSS_SERVO_OE_GPIO` | 17 | −1 if OE isn't wired |
| `VOSS_SIM` | 0 | 1 = no hardware (desktop testing) |

The geometry constants in `config.py` must match `cad/voss.scad`:
`YAW_XY`, `L1`, `L2`, `TILT_OFF`, `TILT_DROP`, `HEAD_SECTIONS`, `OBSTACLES`, `LIMITS`.
Change them together and re-run `cad/tools/collide.py`.

## Tests

```bash
VOSS_SIM=1 python -m unittest discover tests
```

The tests cover:
- mood parsing, the tool loop (fake Claude client), history cap and API-failure fallback
- timers, checklist, notes and weather (fake HTTP)
- printer layouts staying within 32 ASCII columns
- DOA sign and accuracy, and the decimator
- workspace presets and rejects, level-head tilt, stamp drop height
- pulse mapping for all six channels
- the alive overlay staying valid
- motion with `quiesce()`, rest release and shutdown
- LED encoding and the sox chain
