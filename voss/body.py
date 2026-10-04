"""Classic arm (base yaw + shoulder/elbow pitch), head tilt and eye shutters on a PCA9685.

Internal pose joints: yaw, shoulder, elbow, pitch (absolute head pitch, + nose down), shutter.
The tilt servo is derived as pitch + shoulder + elbow, which keeps the pendulum head level.
Moves are planned in joint space, eased with a minimum-jerk (quintic) profile, collision-
checked against the housing, yaw tower and wall, and executed by a 50 Hz thread. On top of
the planned pose sits a small "alive" overlay: a slow idle sway and a speech-driven head bob,
faded out while moving. The shoulder is spring-balanced (desk-lamp style) and holds only a
small residual torque; yaw, tilt and shutters are released at rest.
"""
import contextlib
import json
import logging
import math
import random
import threading
import time
from collections import deque

from . import config, gestures

log = logging.getLogger("voss.body")

JOINTS = ("yaw", "shoulder", "elbow", "pitch", "shutter", "eye")
CHANNELS = ("yaw", "shoulder", "elbow", "tilt", "shutter", "eye")
RELEASABLE = ("yaw", "tilt", "shutter")
HOME = {"yaw": 90.0, "shoulder": 20.0, "elbow": -20.0, "pitch": 0.0, "shutter": 1.0, "eye": 0.0}
ZERO = {"yaw": 90.0, "shoulder": 0.0, "elbow": 0.0, "pitch": 0.0, "shutter": 1.0, "eye": 0.0}     # horn fitting
REST = {"yaw": 90.0, "shoulder": 50.0, "elbow": -50.0, "pitch": 0.0, "shutter": 1.0, "eye": 0.0}   # spring balance point: near-zero load
PARK = {"yaw": 90.0, "shoulder": 50.0, "elbow": -50.0, "pitch": 0.0, "shutter": 1.0, "eye": 0.0}   # ~spring balance point
SULK = {"yaw": 145.0, "shoulder": 30.0, "elbow": -30.0, "pitch": 15.0, "shutter": 0.45, "eye": -0.6}


def tilt_of(p):
    return p["pitch"] + p["shoulder"] + p["elbow"]


# ------------------------------------------------------------------ kinematics
def fk(yaw, shoulder, elbow):
    """Plan-view (x, y) of the elbow axis and the tilt axis (= head centre), plus their z."""
    a = math.radians(shoulder)
    b = math.radians(shoulder + elbow)
    re, ze = config.L1 * math.cos(a), config.L1 * math.sin(a)
    x_t, d = config.L2 + config.TILT_OFF, config.TILT_DROP
    rw = re + x_t * math.cos(b) + d * math.sin(b)
    zw = ze + x_t * math.sin(b) - d * math.cos(b)
    sx, sy = config.YAW_XY
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return (sx + re * c, sy + re * s, ze), (sx + rw * c, sy + rw * s, zw)


def _clear(x, y, r):
    need = r + config.CLEARANCE
    if y < need:                                    # wall
        return False
    for x0, x1, y0, y1 in config.OBSTACLES:
        dx = max(x0 - x, 0.0, x - x1)
        dy = max(y0 - y, 0.0, y - y1)
        if math.hypot(dx, dy) < need:
            return False
    return True


def _in(j, v):
    lo, hi = config.LIMITS[j]
    return lo - 1e-6 <= v <= hi + 1e-6


def workspace_ok(p):
    if not all(_in(j, p[j]) for j in ("yaw", "shoulder", "elbow", "pitch")):
        return False
    if not _in("tilt", tilt_of(p)):
        return False
    (ex, ey, _), (hx, hy, _) = fk(p["yaw"], p["shoulder"], p["elbow"])
    if not _clear(ex, ey, config.ELBOW_R):
        return False
    # The head hangs below its tilt axis and tapers toward the chin. Model its plan view as
    # circles at four depths; pitching swings the deeper ones back (nose down) or forward.
    pr = math.radians(p["pitch"])
    c, s = math.cos(math.radians(p["yaw"])), math.sin(math.radians(p["yaw"]))
    for depth, cx, r in config.HEAD_SECTIONS:
        off = cx * math.cos(pr) + depth * math.sin(pr)
        if not _clear(hx + off * c, hy + off * s, r):
            return False
    return True


def path_ok(a, b, steps=24):
    for i in range(steps + 1):
        f = i / steps
        if not workspace_ok({j: a[j] + (b[j] - a[j]) * f for j in JOINTS}):
            return False
    return True


def clamp_pose(p):
    out = {j: max(config.LIMITS[j][0], min(config.LIMITS[j][1], float(p[j]))) for j in JOINTS}
    lo, hi = config.LIMITS["tilt"]                   # keep the tilt servo in range by adjusting pitch
    t = tilt_of(out)
    if t < lo:
        out["pitch"] += lo - t
    elif t > hi:
        out["pitch"] -= t - hi
    return out


def _saccade(t, period=2.7):
    """Smooth pseudo-random eye flicks in -1..1: hold, then glide quickly to the next target."""
    def target(i):
        return math.sin(i * 12.9898 + 78.233) * 43758.5453 % 2.0 - 1.0
    i, f = divmod(t / period, 1.0)
    a = min(1.0, f / 0.12)
    a = a * a * (3 - 2 * a)
    return target(int(i)) * (1 - a) + target(int(i) + 1) * a


def look_pose(angle_deg):
    """Yaw that points the head toward a talker at angle_deg (+ toward +X)."""
    a = max(-config.DOA_MAX_DEG, min(config.DOA_MAX_DEG, angle_deg))
    return {"yaw": 90.0 - a}


# ------------------------------------------------------------------ hardware
class PCA9685:
    MODE1, MODE2, PRESCALE, LED0 = 0x00, 0x01, 0xFE, 0x06

    def __init__(self, bus=config.I2C_BUS, addr=config.PCA9685_ADDR, freq=config.SERVO_FREQ):
        from smbus2 import SMBus
        self.bus, self.addr = SMBus(bus), addr
        prescale = int(round(25_000_000 / (4096 * freq))) - 1
        self._w(self.MODE1, 0x10)              # sleep
        self._w(self.PRESCALE, prescale)
        self._w(self.MODE1, 0x20)              # wake, auto-increment
        time.sleep(0.005)
        self._w(self.MODE2, 0x04)              # totem pole
        self.period_us = 1e6 * 4096 * (prescale + 1) / 25_000_000

    def _w(self, reg, val):
        self.bus.write_byte_data(self.addr, reg, val)

    def set_us(self, ch, us):
        ticks = max(0, min(4095, int(round(us * 4096 / self.period_us))))
        self.bus.write_i2c_block_data(self.addr, self.LED0 + 4 * ch, [0, 0, ticks & 0xFF, ticks >> 8])

    def full_off(self, ch):
        self.bus.write_i2c_block_data(self.addr, self.LED0 + 4 * ch, [0, 0, 0, 0x10])


def load_calibration(path=None):
    path = path or config.CALIBRATION_FILE
    cal = json.loads(json.dumps(config.DEFAULT_CALIBRATION))
    try:
        with open(path) as f:
            for j, v in json.load(f).items():
                cal.setdefault(j, {}).update(v)
    except FileNotFoundError:
        pass
    return cal


def save_calibration(cal, path=None):
    path = path or config.CALIBRATION_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(cal, f, indent=2)


def joint_to_us(cal, channel, value):
    c = cal[channel]
    if channel == "shutter":
        deg = c["closed_deg"] + value * (c["open_deg"] - c["closed_deg"])
    elif channel == "eye":
        deg = (c["low_deg"] + c["high_deg"]) / 2 + value * (c["high_deg"] - c["low_deg"]) / 2
    else:
        deg = c["offset_deg"] + (-value if c.get("invert") else value)
    deg = max(0.0, min(float(c["range_deg"]), deg))
    return c["min_us"] + (c["max_us"] - c["min_us"]) * deg / c["range_deg"]


def channel_values(pose):
    return {"yaw": pose["yaw"], "shoulder": pose["shoulder"], "elbow": pose["elbow"],
            "tilt": tilt_of(pose), "shutter": pose["shutter"], "eye": pose["eye"]}


class ServoOutputs:
    def __init__(self, cal=None):
        self.cal = cal or load_calibration()
        self.enabled = False
        self.released = set()
        self.pca = None if config.SIM else PCA9685()
        self.oe = None
        if not config.SIM and config.SERVO_OE_GPIO >= 0:
            from gpiozero import OutputDevice
            # OE is active-low: on() drives the pin low = outputs enabled. Starts disabled.
            self.oe = OutputDevice(config.SERVO_OE_GPIO, active_high=False, initial_value=False)
        self.last_us = {}

    def write(self, pose):
        for ch, v in channel_values(pose).items():
            if ch in self.released:
                continue
            us = joint_to_us(self.cal, ch, v)
            self.last_us[ch] = us
            if self.pca:
                self.pca.set_us(self.cal[ch]["ch"], us)

    def enable(self, pose):
        self.released.clear()
        self.write(pose)
        if self.oe:
            self.oe.on()
        self.enabled = True

    def release(self, channels=RELEASABLE):
        """Go limp on the joints that don't carry the arm (silent rest)."""
        for ch in channels:
            self.released.add(ch)
            if self.pca:
                self.pca.full_off(self.cal[ch]["ch"])

    def hold(self, pose):
        self.released.clear()
        self.write(pose)

    def disable(self):
        """All outputs off. The arm will sag to its mechanical stop - only on shutdown."""
        if self.oe:
            self.oe.off()
        elif self.pca:
            for ch in CHANNELS:
                self.pca.full_off(self.cal[ch]["ch"])
        self.enabled = False


# ------------------------------------------------------------------ motion
class _Seg:
    __slots__ = ("end", "dur", "style", "t0", "start")

    def __init__(self, end, dur, style="ease"):
        self.end, self.dur, self.style, self.t0, self.start = end, dur, style, None, None


def _styled_ok(a, b, style, steps=20):
    """Path check that follows the easing curve (a spring overshoots past b)."""
    for i in range(steps + 1):
        e = gestures.curve(style, i / steps)
        if not workspace_ok({j: a[j] + (b[j] - a[j]) * e for j in JOINTS}):
            return False
    return True


class Body:
    """Motion engine. Runs a 50 Hz thread on hardware; tests and the animation tool drive
    tick(now) directly with a virtual clock."""

    def __init__(self, outputs=None, clock=time.monotonic, seed=451):
        self.clock = clock
        self.out = outputs or ServoOutputs()
        self.current = dict(HOME)
        self.goal = dict(HOME)
        self.output_pose = dict(HOME)
        self._segs = deque()
        self._lock = threading.RLock()
        self._idle = threading.Event()
        self._idle.set()
        self._frozen = False
        self._release_when_idle = False
        self._stop = threading.Event()
        self._thread = None
        self._awake = True
        self._mood = "neutral"
        self._sway_amp = 0.0
        self._speech = 0.0
        self._bob = 0.0
        self._t0 = clock()
        self._last = None
        self._rng = random.Random(seed)
        self._blink_at = self._t0 + 2.0
        self._blinks = []                   # start times of scheduled blinks

    # ---------------------------------------------------------- lifecycle
    def start(self):
        self._thread = threading.Thread(target=self._run, name="body", daemon=True)
        self._thread.start()

    def stop(self, park=True):
        """Move to the spring's balance point before cutting power, so the arm barely drifts."""
        if park and self.out.enabled:
            self.move(PARK, 0.4)
            self.wait(6.0)
        self._stop.set()
        if self._thread:
            self._thread.join(1)
        self.out.disable()

    def _run(self):
        while not self._stop.is_set():
            self.tick(self.clock())
            time.sleep(0.02)

    def tick(self, now):
        with self._lock:
            dt = 0.02 if self._last is None else max(0.0, now - self._last)
            self._last = now
            seg_moving = False
            if not self._frozen and self._segs:
                seg = self._segs[0]
                if seg.t0 is None:
                    seg.t0, seg.start = now, dict(self.current)
                a = 1.0 if seg.dur <= 0 else min(1.0, (now - seg.t0) / seg.dur)
                e = gestures.curve(seg.style, a)
                self.current = {j: seg.start[j] + (seg.end[j] - seg.start[j]) * e for j in JOINTS}
                seg_moving = any(abs(seg.end[j] - seg.start[j]) > 1e-6 for j in JOINTS)
                if not self.out.enabled:
                    self.out.enable(self.current)
                elif self.out.released:
                    self.out.hold(self.current)
                if a >= 1.0:
                    self.current = dict(seg.end)
                    self._segs.popleft()
            prof = gestures.MOOD_IDLE.get(self._mood, gestures.MOOD_IDLE["neutral"])
            target = prof["amp"] if (self._awake and not seg_moving and not self._release_when_idle) else 0.0
            self._sway_amp += max(-2.0 * dt, min(1.0 * dt, target - self._sway_amp))
            self._bob *= math.exp(-dt / 0.15)
            self.output_pose = self.alive_pose(now)
            if not self._frozen and self.out.enabled and not self.out.released:
                self.out.write(self.output_pose)
            if not self._segs:
                if self._release_when_idle and self.out.enabled and not self._frozen and self._sway_amp <= 0.0:
                    self.out.release()
                    self._release_when_idle = False
                self._idle.set()

    # ---------------------------------------------------------- alive overlay
    def _blink(self, now):
        """Eyelid factor 0..1 (1 = open). Natural blinks, rate depends on mood; some doubles."""
        prof = gestures.MOOD_IDLE.get(self._mood, gestures.MOOD_IDLE["neutral"])
        if self._awake and now >= self._blink_at:
            self._blinks.append(now)
            if self._rng.random() < 0.15:
                self._blinks.append(now + 0.28)
            self._blink_at = now + self._rng.uniform(2.5, 6.0) / max(0.1, prof["blink"])
        self._blinks = [b for b in self._blinks if now - b < 0.25]
        f = 1.0
        for b in self._blinks:
            ph = now - b
            if 0 <= ph < 0.06:
                c = ph / 0.06
            elif 0.06 <= ph < 0.10:
                c = 1.0
            elif 0.10 <= ph < 0.21:
                c = 1 - (ph - 0.10) / 0.11
            else:
                c = 0.0
            f = min(f, 1 - 0.95 * c)
        return f

    def alive_pose(self, now):
        """Planned pose + idle sway, eye flicks, speech bob and blinks (only if still valid)."""
        prof = gestures.MOOD_IDLE.get(self._mood, gestures.MOOD_IDLE["neutral"])
        t = (now - self._t0) * prof["speed"]
        k = self._sway_amp
        p = dict(self.current)
        p["yaw"] += k * config.SWAY["yaw"] * math.sin(2 * math.pi * t / 11.0)
        p["shoulder"] += k * config.SWAY["shoulder"] * math.sin(2 * math.pi * t / 8.3 + 1.0)
        p["pitch"] += (k * config.SWAY["pitch"] * math.sin(2 * math.pi * t / 6.1 + 2.0)
                       - config.SPEECH_BOB * self._speech + config.SPEECH_EMPHASIS * self._bob)
        p["eye"] += k * config.SWAY["eye"] * _saccade(t)
        p["shutter"] *= self._blink(now)
        p = clamp_pose(p)
        if workspace_ok(p):
            return p
        q = dict(self.current)
        q["shutter"] = p["shutter"]
        return q

    def speech(self, level):
        """Speech envelope 0..1: the head lifts on loud syllables and gives a little nod on onsets."""
        level = max(0.0, min(1.0, level))
        if level - self._speech > 0.3 and level > 0.5:
            self._bob = 1.0
        self._speech = level

    def set_awake(self, awake):
        self._awake = awake

    def set_mood(self, mood):
        self._mood = mood if mood in gestures.MOOD_IDLE else "neutral"

    # ---------------------------------------------------------- moves
    @staticmethod
    def _duration(a, b, speed):
        t = max(abs(b[j] - a[j]) / (config.MAX_SPEED[j] * speed) for j in JOINTS)
        return max(0.05, t * 1.875)          # quintic peaks at 1.875x mean speed

    def move(self, target, speed=1.0, replace=True, style="ease", duration=None):
        """Move to a (partial) pose. Arm parts that fail the workspace check are ignored."""
        with self._lock:
            new = dict(self.goal)
            new.update(target)
            new = clamp_pose(new)
            if not workspace_ok(new):
                log.warning("pose rejected by workspace check: %s", new)
                new = clamp_pose(dict(new, **{j: self.goal[j] for j in ("yaw", "shoulder", "elbow", "pitch")}))
            if replace:
                self._segs.clear()
            start = dict(self.current) if replace else dict(self.goal)
            if style != "ease" and not _styled_ok(start, new, style):
                style = "ease"
            path = [new]
            if not path_ok(start, new):
                via = dict(new, yaw=new["yaw"] if path_ok(start, dict(start, yaw=new["yaw"])) else HOME["yaw"],
                           shoulder=HOME["shoulder"], elbow=HOME["elbow"], pitch=HOME["pitch"])
                path = [via, new]
            prev = start
            for p in path:
                dur = duration if (duration and len(path) == 1) else self._duration(prev, p, speed)
                self._segs.append(_Seg(p, dur, style))
                prev = p
            self.goal = new
            self._release_when_idle = False
            self._idle.clear()

    def perform(self, steps, replace=True, scale=1.0):
        """Queue a gesture: each step goes to absolute joints ("to") or an offset from the anchor
        ("rel"), with its own duration, easing and hold. Steps that would leave the workspace are
        held in place instead; springs that would overshoot out of it become plain eases."""
        with self._lock:
            if replace:
                self._segs.clear()
            prev = dict(self.current) if replace else dict(self.goal)
            anchor = dict(self.goal)
            for st in steps:
                tgt = dict(prev)
                if st["to"]:
                    tgt.update(st["to"])
                    anchor = clamp_pose(dict(anchor, **st["to"]))
                for j, d in st["rel"].items():
                    tgt[j] = anchor[j] + d * scale
                tgt = clamp_pose(tgt)
                style = st["style"]
                if not workspace_ok(tgt) or not path_ok(prev, tgt):
                    tgt = dict(prev)
                elif style != "ease" and not _styled_ok(prev, tgt, style):
                    style = "ease"
                if st["t"] > 0:
                    self._segs.append(_Seg(tgt, st["t"], style))
                if st["hold"] > 0:
                    self._segs.append(_Seg(tgt, st["hold"], "hold"))
                prev = tgt
            self.goal = prev
            self._release_when_idle = False
            self._idle.clear()

    def gesture(self, name, scale=1.0, replace=True):
        if name in gestures.GESTURES:
            self.perform(gestures.GESTURES[name], replace=replace, scale=scale)

    def express(self, mood, gesture=None):
        """Mood entry pose + the mood's signature gesture (or the gesture Claude asked for)."""
        self.set_mood(mood)
        self._awake = True
        steps = []
        entry = gestures.MOOD_ENTRY.get(mood)
        if entry:
            pose, t, style = entry
            steps.append(gestures.S(to=pose, t=t, style=style))
        name = gesture if gesture in gestures.GESTURES else gestures.MOOD_GESTURE.get(mood)
        if name:
            steps += gestures.GESTURES[name]
        if steps:
            self.perform(steps)

    def wait(self, timeout=5.0):
        return self._idle.wait(timeout)

    @property
    def moving(self):
        return not self._idle.is_set()

    @contextlib.contextmanager
    def quiesce(self, timeout=5.0):
        """Finish the current move and freeze motion (e.g. while printing). Joints keep holding:
        the servos are on their own 6 V rail, so the printer's current draw can't brown them out."""
        self.wait(timeout)
        with self._lock:
            self._frozen = True
        try:
            yield
        finally:
            with self._lock:
                self._frozen = False

    def cancel_gesture(self):
        with self._lock:
            self._segs.clear()
            self.goal = dict(self.current)

    # ---------------------------------------------------------- behaviours
    def home(self, speed=0.7):
        self.set_mood("neutral")
        self.move(HOME, speed)

    def rest(self):
        """Settle at the spring's balance point, head level, stop swaying, then yaw/tilt/eyelids
        go limp. The shoulder holds almost nothing here; the elbow holds the head."""
        self.set_mood("neutral")
        self._awake = False
        self.move(REST, 0.5)
        with self._lock:
            self._release_when_idle = True

    def look(self, angle_deg):
        """Eye flicks first, then the arm swings toward the talker with a springy settle, leaning in."""
        self._awake = True
        yaw = look_pose(angle_deg)["yaw"]
        self.perform([gestures.S(to={"eye": 0.35}, t=0.12, style="snap"),
                      gestures.S(to={"yaw": yaw, "shoulder": 12.0, "elbow": -8.0, "pitch": -4.0, "shutter": 1.0},
                                 t=max(0.5, abs(yaw - self.current["yaw"]) / 70.0), style="spring"),
                      gestures.S(to={"eye": 0.2}, t=0.3)])

    def listen(self):
        self._awake = True
        self.perform([gestures.S(to={"shoulder": 12.0, "elbow": -8.0, "pitch": -4.0, "shutter": 1.0, "eye": 0.2},
                                 t=0.6, style="spring")])

    def think(self):
        """Rise, eye rolls up, lids narrow a touch, then a slow drift as if reading a file."""
        self.perform([gestures.S(to={"shoulder": 30.0, "elbow": -34.0, "pitch": 8.0, "shutter": 0.7, "eye": 0.6},
                                 t=0.8, style="slow"),
                      gestures.S({"yaw": 6, "eye": -0.15}, t=1.2, style="slow"),
                      gestures.S({"yaw": -4, "eye": 0.1}, t=1.4, style="slow")])

    def filing(self):
        """Rapid eyelid flutter while 'logging' something (doesn't interrupt the current move)."""
        self.perform(gestures.GESTURES["flutter"], replace=False)

    def stamp(self):
        self.gesture("stamp")

    def nod(self):
        self.gesture("nod")

    def mood(self, mood, gesture=None):
        self.express(mood, gesture)
