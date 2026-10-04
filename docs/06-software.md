# 6. Software

Python 3, installed to `/opt/memo` and run as the systemd service `memo`.

## Pipeline

```
arecord (I2S stereo, 16 kHz) ──► openWakeWord ──► GCC-PHAT DOA ──► arm turns to talker
                                                        │
                    webrtcvad endpointing + Vosk small-en (streaming, local)
                                                        │
             Claude (claude-haiku-4-5-20251001) ◄──► tools (timers, weather, notes, print…)
                                                        │
                    "[mood] reply"  ──►  pose + shutters + lights
                                                        │
           Piper en_US-amy-low ──► sox intercom filter + chime/sfx ──► aplay, eye follows envelope
```

- **Local stages:** the wake word and speech-to-text run on the Pi. Only the transcript
  goes to Claude.
- **Conversation memory:** the last 8 exchanges are kept as plain text.
- **Tool loop:** up to 5 tool rounds per reply.
- **Failure:** if Claude can't be reached, she says an in-character fallback line.

## Modules (`memo/`)

| Module | Role |
|---|---|
| `config` | Every setting, overridable with `MEMO_*` environment variables |
| `persona` | System prompt (lore and rules) and mood-tag parsing |
| `audio` | Capture thread (with 48→16 kHz decimator), playback with level envelope, GCC-PHAT direction of arrival |
| `stt` | Wake word and utterance capture with Vosk |
| `tts` | Piper, then sox intercom chain, then concatenation of chime, thunk and relay-click sfx |
| `lights` | WS2812 over SPI (eye ring, REC, AUD, OK); modes and mood effects at 50 Hz |
| `body` | PCA9685 driver, calibration, kinematics and workspace check, eased motion thread, gestures, `quiesce()` |
| `printer` | ESC/POS memo layouts: memo, write-up, commendation, checklist |
| `tools` | Claude tool schemas and handlers |
| `brain` | Claude tool-use loop and rolling history |
| `main` | Orchestration (voice mode, or `--text` keyboard mode) |
| `calibrate` | Bring-up command-line tool |

## Tools available to Claude

| Tool | What it does |
|---|---|
| `get_time` | Local date and time |
| `set_timer` / `list_timers` / `cancel_timer` | Countdown timers, announced aloud when they finish |
| `get_weather` | Open-Meteo (no key) for home or a named place; °F/mph by default |
| `checklist` | "Mandatory Preparedness Checklist" to-do list (JSON on disk) |
| `notes` | "Permanent record" notes: add, list, search, delete |
| `print_memo` | Print a memo, write-up, commendation or the checklist |

## Motion safety

- **Workspace check.** Every arm target passes `body.workspace_ok()`, a plan-view check
  of the elbow, link and head against the housing footprint and the wall. The model uses
  head centre 114 mm past the elbow, radius 84. The CAD collision sweep confirms that
  every pose it accepts is clear.
- **Path check.** Moves are interpolated in joint space. If any intermediate pose fails,
  the move goes through home instead.
- **Printing.** `quiesce()` waits for motion to stop and cuts servo outputs (PCA9685 OE)
  while the printer runs.
- **Rest.** After 45 s idle the arm homes and the outputs are released, so she's silent.

## Configuration

Set values in `/etc/memo.env`. The most useful ones:

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required |
| `MEMO_LAT`, `MEMO_LON` | — | Home weather location |
| `MEMO_TEMP_UNIT` | fahrenheit | or celsius |
| `MEMO_CAPTURE_RATE` | 16000 | 48000 if 16 kHz I2S capture is flaky |
| `MEMO_MIC_GAIN` | 4.0 | Software gain on the INMP441s |
| `MEMO_WAKE_MODEL` | hey_jarvis | Path to a trained `hey_memo.onnx` later |
| `MEMO_WAKE_THRESHOLD` | 0.5 | Raise if she wakes by accident |
| `MEMO_LED_BRIGHTNESS` | 0.6 | Global LED brightness |
| `MEMO_SERVO_OE_GPIO` | 17 | −1 if OE isn't wired |
| `MEMO_SIM` | 0 | 1 = no hardware (desktop testing) |

Geometry constants in `config.py` (`SHOULDER_XY`, `HOUSING_D`, `HEAD_CENTER`, `HEAD_R`,
`LIMITS`) must match `cad/memo.scad`. If you change the CAD, update them and re-run
`cad/tools/collide.py`.

## Tests

```bash
MEMO_SIM=1 python -m unittest discover tests
```

The tests cover:
- mood parsing
- the tool loop (with a fake Claude client), history cap and API-failure fallback
- timers, checklist, notes and weather (with fake HTTP)
- printer layouts staying within 32 columns of ASCII
- DOA sign and accuracy on synthetic delays, and the decimator
- the workspace check and pulse mapping
- motion with `quiesce()` and rest release
- LED encoding
- the sox chain, if sox is installed
