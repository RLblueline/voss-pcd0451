# 7. Bring-up and calibration

## Install

On a fresh Raspberry Pi OS Lite (Bookworm, 64-bit):

```bash
git clone <this repo> voss && cd voss
sudo ./deploy/install.sh        # packages, venv, models, systemd unit, config.txt lines
sudo nano /etc/voss.env         # ANTHROPIC_API_KEY, VOSS_LAT, VOSS_LON
sudo reboot
```

The installer:
- appends `deploy/config.txt.snippet` to `/boot/firmware/config.txt` (I2C, SPI, UART,
  voicehat overlay, fixed core clock)
- frees the serial port from the login console
- downloads Piper, the amy-low voice, the Vosk small model and the openWakeWord models

## First power-on, in order

All commands run from `/opt/voss` as `sudo -u voss venv/bin/python -m voss.calibrate …`.

| Step | Command | Pass when |
|---|---|---|
| 1. Audio card | `arecord -l` | `sndrpigooglevoi` is listed |
| 2. Mics | `arecord -D plughw:CARD=sndrpigooglevoi -c 2 -r 16000 -f S16_LE -d 3 t.wav && aplay t.wav` | You hear yourself |
| 3. LEDs | `leds` | Red, green, blue and amber wipe across all 19 |
| 4. Servo zero | `zero` | Yaw 90, link1 level, links in line, head level, eye centred. Fit horns now; support the arm before releasing |
| 5. Trim | `trim shoulder -3` (yaw, shoulder, elbow, tilt) | Link1 level and links straight at zero |
| 6. Spring | `float` | See below |
| 7. Range | `set shoulder 60`, `set shoulder -20`, `set elbow -60` | Moves smoothly; head stays level |
| 8. Eyelids | `set shutter 0`, `set shutter 1`, `shutter 4 176` | 12 mm slit closed; lids hidden when open |
| 9. Eye lift | `set eye 1`, `set eye -1`, `set eye 0` | Eye glides the full slot, centred at 0 |
| 10. Direction | `doa` | Clap on the left → negative, right → positive |
| 11. Printer | `print` | Test memo drops out of the bottom |
| 12. Show | `demo` | All five moods play |
| 13. Service | `sudo systemctl start voss && journalctl -u voss -f` | "V.O.S.S. online" |

## Tuning the spring

`calibrate float` raises the arm to 30°, then releases only the shoulder servo.

| What the arm does | Fix |
|---|---|
| Floats up and settles near 50° | Tuned |
| Sinks | Tighten the tensioner screw at the bottom of the mast |
| Shoots up hard | Loosen it |
| Still sinks with the screw nearly maxed | The spring is too weak: use a stiffer one, or shorten the cable one crimp |

A well-tuned arm stays roughly wherever you push it, like a desk lamp.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Capture glitches or silence | `VOSS_CAPTURE_RATE=48000` |
| Very quiet speech | Raise `VOSS_MIC_GAIN` (6–8) |
| Arm turns the wrong way to talkers | Swap the mics' L/R strap pins, or flip the sign in `audio.doa_degrees` |
| LEDs flicker or show wrong colours | Add a 74AHCT125 level shifter; check the `core_freq` lines |
| Printer prints garbage | Check `VOSS_PRINTER_BAUD`, and that the serial console is off |
| Pi reboots when the arm moves | Servos must be on the separate 6 V rail with a common ground |
| Shoulder hums or gets warm | The spring needs tightening (`float`) |
| Eye drifts down at rest | Lift pinion slipping on the spline: tighten its screw, or reprint it with a tighter bore |
| Eye binds in the slot | Rods not parallel: loosen the mount bars, run `set eye 1` / `-1`, retighten |
| False wake-ups | Raise `VOSS_WAKE_THRESHOLD`; train "hey voss" |

## Training "hey voss"

Use openWakeWord's synthetic-data training notebook to make `hey_voss.onnx`. Copy it to
`/opt/voss/models/` and set `VOSS_WAKE_MODEL=/opt/voss/models/hey_voss.onnx`.
