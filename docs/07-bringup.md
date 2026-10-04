# 7. Bring-up and calibration

## Install

On a fresh Raspberry Pi OS Lite (Bookworm, 64-bit):

```bash
git clone <this repo> memo && cd memo
sudo ./deploy/install.sh        # packages, venv, models, systemd unit, config.txt lines
sudo nano /etc/memo.env         # ANTHROPIC_API_KEY, MEMO_LAT, MEMO_LON
sudo reboot
```

The installer:
- appends `deploy/config.txt.snippet` to `/boot/firmware/config.txt` (I2C, SPI, UART,
  voicehat overlay, fixed core clock for stable SPI and UART timing)
- frees the serial port from the login console
- downloads Piper, the amy-low voice, the Vosk small model and the openWakeWord models

## First power-on, in order

All commands run from `/opt/memo` as `sudo -u memo venv/bin/python -m memo.calibrate …`.

| Step | Command | Pass when |
|---|---|---|
| 1. Audio card | `arecord -l` | `sndrpigooglevoi` is listed |
| 2. Mics | `arecord -D plughw:CARD=sndrpigooglevoi -c 2 -r 16000 -f S16_LE -d 3 t.wav && aplay t.wav` | You hear yourself on both channels |
| 3. LEDs | `leds` | Red, green, blue, amber wipes across all 19 |
| 4. Servo zero | `zero` | Yaw 90, link1 level, links in line, head level; fit horns now. Support the arm before releasing |
| 5. Trim | `trim shoulder -3` (yaw, shoulder, elbow, tilt) | Link1 level and links straight at zero |
| 5b. Range | `set shoulder 60`, `set shoulder -20`, `set elbow -60` | Moves smoothly; the head stays level |
| 6. Shutters | `set shutter 0`, `set shutter 1`, `shutter 4 176` | 12 mm slit closed; plates hidden when open |
| 7. Direction | `doa` | Clap on the left → negative angle, right → positive |
| 8. Printer | `print` | Test memo prints |
| 9. Show | `demo` | All five moods play |
| 10. Service | `sudo systemctl start memo && journalctl -u memo -f` | "M.E.M.O. online" in the log |

## Troubleshooting

| Symptom | Fix |
|---|---|
| Capture glitches or silence | `MEMO_CAPTURE_RATE=48000` (software decimation) |
| Very quiet speech | Raise `MEMO_MIC_GAIN` (try 6–8) |
| Head turns the wrong way | Swap the mics' L/R strap pins, or flip the sign in `audio.doa_degrees` |
| LEDs flicker or show wrong colours | Add a 74AHCT125 level shifter; check `core_freq` lines in config.txt |
| Printer prints garbage | Check baud (`MEMO_PRINTER_BAUD`) and that the serial console is disabled |
| Pi reboots when the arm moves | Servos must be on the separate 6 V rail with a common ground |
| False wake-ups | Raise `MEMO_WAKE_THRESHOLD`; train "hey memo" |
| Shoulder hums or gets warm at rest | Expected: it's holding the arm. Fit the counterbalance spring |
| Arm drops when the service stops | It's lowered first on a clean stop; on power loss it sags. Fit the spring |

## Training "hey memo"

Use openWakeWord's synthetic-data training notebook to make `hey_memo.onnx`. Copy it to
`/opt/memo/models/` and set `MEMO_WAKE_MODEL=/opt/memo/models/hey_memo.onnx`.
