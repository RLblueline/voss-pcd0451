"""WS2812 eye ring (16) + status bar REC/AUD/OK (3) over SPI MOSI (GPIO10)."""
import logging
import math
import random
import threading
import time

from . import config

log = logging.getLogger("memo.lights")

AMBER = (255, 160, 70)      # ~2700 K manila-amber
TUNGSTEN = (255, 118, 32)
REC_RED = (255, 18, 8)
AUD_AMBER = (255, 105, 0)
OK_GREEN = (70, 190, 60)

# SPI at 2.4 MHz: each WS2812 bit = 3 SPI bits (0 -> 100, 1 -> 110).
_LUT = []
for _v in range(256):
    _bits = 0
    for _i in range(7, -1, -1):
        _bits = (_bits << 3) | (0b110 if (_v >> _i) & 1 else 0b100)
    _LUT.append(_bits.to_bytes(3, "big"))
_GAMMA = [int(round(255 * (i / 255) ** 2.2)) for i in range(256)]


def encode(pixels):
    out = bytearray(24)                      # leading reset
    for r, g, b in pixels:
        out += _LUT[g] + _LUT[r] + _LUT[b]   # GRB order
    out += bytes(24)                         # trailing reset (>50 us low)
    return bytes(out)


class Strip:
    def __init__(self):
        self.spi = None
        if not config.SIM:
            import spidev
            self.spi = spidev.SpiDev()
            self.spi.open(config.LED_SPI_BUS, config.LED_SPI_DEV)
            self.spi.max_speed_hz = 2_400_000
            self.spi.mode = 0
        self.last = None

    def show(self, pixels):
        scaled = [tuple(_GAMMA[max(0, min(255, int(c * config.LED_BRIGHTNESS)))] for c in p) for p in pixels]
        self.last = scaled
        if self.spi:
            self.spi.writebytes2(encode(scaled))


def _scale(col, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(c * k) for c in col)


class Lights:
    """Modes: idle, listen, think, speak, off. Mood modifies palette/behaviour."""

    def __init__(self, strip=None):
        self.strip = strip or Strip()
        self.mode, self.mood = "idle", "neutral"
        self._level = 0.0
        self._ok_until = 0.0
        self._aud_until = 0.0
        self._stop = threading.Event()
        self._thread = None
        self._flick = 1.0

    def start(self):
        self._thread = threading.Thread(target=self._run, name="lights", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(1)
        self.strip.show([(0, 0, 0)] * config.LED_COUNT)

    def set_mode(self, mode, mood=None):
        self.mode = mode
        if mood is not None:
            self.mood = mood
        if mood == "approve":
            self.flash_ok(2.0)

    def set_level(self, x):
        # fast attack, slower release
        self._level = x if x > self._level else self._level * 0.8 + x * 0.2

    def flash_ok(self, seconds=1.5):
        self._ok_until = time.monotonic() + seconds

    def pulse_aud(self, seconds=1.0):
        self._aud_until = time.monotonic() + seconds

    def frame(self, t):
        n = config.LED_EYE_COUNT
        mood, mode = self.mood, self.mode
        if mode == "off":
            return [(0, 0, 0)] * config.LED_COUNT
        col = TUNGSTEN if mood == "concern" else AMBER
        eye = [0.0] * n
        if mode == "idle":
            b = 0.18 + 0.12 * (0.5 + 0.5 * math.sin(2 * math.pi * t / 4.0))
            eye = [b] * n
        elif mode == "listen":
            eye = [0.9] * n
        elif mode == "think":
            pos = (t * 1.5 * n) % n            # sweep around the ring
            for i in range(n):
                d = min(abs(i - pos), n - abs(i - pos))
                eye[i] = 0.12 + 0.88 * max(0.0, 1 - d / 3.0)
        elif mode == "speak":
            eye = [0.3 + 0.7 * self._level] * n
        if mode != "off":
            if mood == "infraction":
                if random.random() < 0.3:
                    self._flick = random.uniform(0.45, 1.0)
                eye = [e * self._flick for e in eye]
            elif mood == "concern":
                k = 0.93 + 0.07 * math.sin(2 * math.pi * t * 0.7)
                eye = [min(e, 0.4) * k for e in eye]
            elif mood == "sulk":
                eye = [e * 0.25 for e in eye]
        px = [_scale(col, e) for e in eye]
        rec = 0.0 if mode == "off" else (0.7 if mode == "listen" else 0.35)
        aud = 0.0
        if mode == "think" or t < self._aud_until:
            aud = 0.5 + 0.5 * math.sin(2 * math.pi * t * 2.0)
        elif mode == "listen":
            aud = 0.3
        ok = 0.8 if t < self._ok_until else 0.0
        status = [None] * 3
        status[config.LED_REC - n] = _scale(REC_RED, rec)
        status[config.LED_AUD - n] = _scale(AUD_AMBER, aud)
        status[config.LED_OK - n] = _scale(OK_GREEN, ok)
        return px + status

    def _run(self):
        while not self._stop.is_set():
            try:
                self.strip.show(self.frame(time.monotonic()))
            except Exception:
                log.exception("LED update failed")
                time.sleep(1)
            time.sleep(0.02)
