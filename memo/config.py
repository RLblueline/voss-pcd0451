"""M.E.M.O. configuration.

Every value can be overridden with an environment variable. On the Pi, put
overrides in /etc/memo.env (loaded by the systemd unit).

Frame: X along the wall, Y out of the wall, Z up. Wall face is y = 0.
"""
import os
from pathlib import Path


def _get(name, default, cast=str):
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    if cast is bool:
        return raw.strip().lower() in ("1", "true", "yes", "on")
    return cast(raw)


def _opt_float(name):
    raw = os.environ.get(name)
    return float(raw) if raw not in (None, "") else None


# ---------------------------------------------------------------- paths / mode
ROOT = Path(_get("MEMO_ROOT", "/opt/memo"))
DATA_DIR = Path(_get("MEMO_DATA", str(ROOT / "data")))
MODELS_DIR = Path(_get("MEMO_MODELS", str(ROOT / "models")))
SIM = _get("MEMO_SIM", False, bool)          # no hardware: fake servos/LEDs/printer

# ---------------------------------------------------------------- Claude
MODEL = _get("MEMO_MODEL", "claude-haiku-4-5-20251001")
MAX_TOKENS = _get("MEMO_MAX_TOKENS", 300, int)
HISTORY_TURNS = _get("MEMO_HISTORY_TURNS", 8, int)   # user+assistant exchanges kept
MAX_TOOL_ROUNDS = 5
API_TIMEOUT_S = 20.0

# ---------------------------------------------------------------- audio
ALSA_CAPTURE = _get("MEMO_ALSA_CAPTURE", "plughw:CARD=sndrpigooglevoi,DEV=0")
ALSA_PLAYBACK = _get("MEMO_ALSA_PLAYBACK", "plughw:CARD=sndrpigooglevoi,DEV=0")
CAPTURE_RATE = _get("MEMO_CAPTURE_RATE", 16000, int)   # 16000, or 48000 fallback
RATE = 16000                                           # pipeline rate
CHUNK = 1280                                           # 80 ms (openWakeWord frame)
MIC_GAIN = _get("MEMO_MIC_GAIN", 4.0, float)           # INMP441s are quiet
MIC_SPACING_M = 0.080
SPEED_OF_SOUND = 343.0
DOA_MAX_DEG = 60.0
DOA_MIN_RMS = 200.0                                    # ignore DOA below this level

# ---------------------------------------------------------------- wake word
WAKE_MODEL = _get("MEMO_WAKE_MODEL", "hey_jarvis")     # built-in name or path to .onnx
WAKE_THRESHOLD = _get("MEMO_WAKE_THRESHOLD", 0.5, float)
WAKE_COOLDOWN_S = 1.5

# ---------------------------------------------------------------- speech to text
VOSK_MODEL = Path(_get("MEMO_VOSK_MODEL", str(MODELS_DIR / "vosk-model-small-en-us-0.15")))
VAD_AGGRESSIVENESS = 2
SILENCE_END_MS = 700
MAX_UTTERANCE_S = 8.0
NO_SPEECH_TIMEOUT_S = 4.0

# ---------------------------------------------------------------- text to speech
PIPER_BIN = _get("MEMO_PIPER_BIN", "piper")
PIPER_MODEL = Path(_get("MEMO_PIPER_MODEL", str(MODELS_DIR / "en_US-amy-low.onnx")))
INTERCOM_FX = _get("MEMO_INTERCOM", True, bool)

# ---------------------------------------------------------------- servos
I2C_BUS = 1
PCA9685_ADDR = 0x40
SERVO_FREQ = 50
SERVO_OE_GPIO = _get("MEMO_SERVO_OE_GPIO", 17, int)   # PCA9685 OE; -1 = not wired.
                                                      # (GPIO16 is taken by the voicehat overlay)
CALIBRATION_FILE = DATA_DIR / "calibration.json"
REST_AFTER_S = 45.0          # idle time before the arm homes and yaw/tilt/shutter go limp

# Default calibration (5 channels). Yaw MG996R, shoulder 35 kg-cm standard-size servo
# (DS3235 class), elbow + tilt DS3218, shutters SG90.  servo_deg = offset_deg +/- joint_deg.
DEFAULT_CALIBRATION = {
    "yaw":      {"ch": 0, "min_us": 500, "max_us": 2500, "range_deg": 180, "offset_deg": 0,   "invert": False},
    "shoulder": {"ch": 1, "min_us": 500, "max_us": 2500, "range_deg": 180, "offset_deg": 90,  "invert": False},
    "elbow":    {"ch": 2, "min_us": 500, "max_us": 2500, "range_deg": 180, "offset_deg": 130, "invert": False},
    "tilt":     {"ch": 3, "min_us": 500, "max_us": 2500, "range_deg": 180, "offset_deg": 90,  "invert": False},
    "shutter":  {"ch": 4, "min_us": 500, "max_us": 2400, "range_deg": 180, "closed_deg": 4, "open_deg": 176},
}

# Joint conventions (match cad/assembly.scad):
#   yaw 90 = arm straight out from the wall;  shoulder 0 = link1 horizontal, + lifts;
#   elbow 0 = links in line, + lifts link2;  pitch = absolute head pitch, + nose down.
#   The tilt servo is derived: tilt = pitch + shoulder + elbow (keeps the head level).
LIMITS = {
    "yaw": (5.0, 175.0),
    "shoulder": (-20.0, 75.0),
    "elbow": (-110.0, 40.0),
    "pitch": (-40.0, 45.0),
    "tilt": (-35.0, 40.0),      # servo range, CAD collision-checked
    "shutter": (0.0, 1.0),
}
MAX_SPEED = {"yaw": 90.0, "shoulder": 60.0, "elbow": 90.0, "pitch": 150.0, "shutter": 4.0}  # deg/s, aperture/s

# ---------------------------------------------------------------- geometry (mm), matches cad/memo.scad
YAW_XY = (0.0, 112.0)            # yaw axis; the shoulder pitch axis sits on it at z = 0
L1 = 120.0
L2 = 100.0
TILT_OFF = 14.0                  # tilt axis past link2's end ...
TILT_DROP = 72.0                 # ... and this far below link2's centreline
HEAD_R = 84.0                    # plan-view radius covering the 90 x 140 mm head
HEAD_LEN = 270.0                 # tilt axis -> bottom of the head
ELBOW_R = 30.0
CLEARANCE = 8.0
# plan-view obstacles (x0, x1, y0, y1): housing, yaw tower
OBSTACLES = [(-72.0, 72.0, 0.0, 70.0), (-30.0, 30.0, 70.0, 132.0)]

# ---------------------------------------------------------------- LEDs (WS2812 on SPI MOSI)
LED_SPI_BUS = 0
LED_SPI_DEV = 0
LED_EYE_COUNT = 16                    # ring behind the lens
LED_REC, LED_AUD, LED_OK = 16, 17, 18  # status bar blocks, end of the chain
LED_COUNT = 19
LED_BRIGHTNESS = _get("MEMO_LED_BRIGHTNESS", 0.6, float)

# ---------------------------------------------------------------- printer
PRINTER_PORT = _get("MEMO_PRINTER_PORT", "/dev/serial0")
PRINTER_BAUD = _get("MEMO_PRINTER_BAUD", 9600, int)
PRINTER_COLS = 32

# ---------------------------------------------------------------- weather
LAT = _opt_float("MEMO_LAT")
LON = _opt_float("MEMO_LON")
TEMP_UNIT = _get("MEMO_TEMP_UNIT", "fahrenheit")      # or "celsius"
WIND_UNIT = _get("MEMO_WIND_UNIT", "mph")             # or "kmh"
