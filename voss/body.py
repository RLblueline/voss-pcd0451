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
import threading
import time
from collections import deque

from . import config

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
    __slots__ = ("end", "dur", "t0", "start")

    def __init__(self, end, dur):
        self.end, self.dur, self.t0, self.start = end, dur, None, None


class Body:
    def __init__(self, outputs=None):
        self.out = outputs or ServoOutputs()
        self.current = dict(HOME)
        self.goal = dict(HOME)
        self._segs = deque()
        self._lock = threading.RLock()
        self._idle = threading.Event()
        self._idle.set()
        self._frozen = False
        self._release_when_idle = False
        self._stop = threading.Event()
        self._thread = None
        self._gesture_gen = 0
        self._awake = True
        self._sway_amp = 0.0
        self._speech = 0.0
        self._t0 = time.monotonic()

    # ---------------------------------------------------------- lifecycle
    def start(self):
        self._thread = threading.Thread(target=self._run, name="body", daemon=True)
        self._thread.start()

    def stop(self, park=True):
        """Move to the spring's balance point before cutting power, so the arm barely drifts."""
        if park and self.out.enabled:
            self.cancel_gesture()
            self.move(PARK, 0.4)
            self.wait(6.0)
        self._stop.set()
        if self._thread:
            self._thread.join(1)
        self.out.disable()

    def _run(self):
        while not self._stop.is_set():
            now = time.monotonic()
            with self._lock:
                if not self._frozen and self._segs:
                    seg = self._segs[0]
                    if seg.t0 is None:
                        seg.t0, seg.start = now, dict(self.current)
                    a = 1.0 if seg.dur <= 0 else min(1.0, (now - seg.t0) / seg.dur)
                    e = a * a * a * (a * (6 * a - 15) + 10)       # minimum-jerk
                    self.current = {j: seg.start[j] + (seg.end[j] - seg.start[j]) * e for j in JOINTS}
                    if not self.out.enabled:
                        self.out.enable(self.current)
                    elif self.out.released:
                        self.out.hold(self.current)
                    if a >= 1.0:
                        self._segs.popleft()
                moving = bool(self._segs)
                target_amp = 1.0 if (self._awake and not moving and not self._release_when_idle) else 0.0
                self._sway_amp += max(-0.04, min(0.02, target_amp - self._sway_amp))   # fade in 1 s, out 0.5 s
                if not self._frozen and self.out.enabled and not self.out.released:
                    self.out.write(self.alive_pose(now))
                if not self._segs:
                    if self._release_when_idle and self.out.enabled and not self._frozen and self._sway_amp <= 0.0:
                        self.out.release()
                        self._release_when_idle = False
                    self._idle.set()
            time.sleep(0.02)

    # ---------------------------------------------------------- moves
    @staticmethod
    def _duration(a, b, speed):
        t = max(abs(b[j] - a[j]) / (config.MAX_SPEED[j] * speed) for j in JOINTS)
        return max(0.05, t * 1.875)          # quintic peaks at 1.875x mean speed

    def move(self, target, speed=1.0, replace=True):
        """Move to a (partial) pose. Arm parts that fail the workspace check are ignored."""
        with self._lock:
            new = dict(self.goal)
            new.update(target)
            new = clamp_pose(new)
            if not workspace_ok(new):
                log.warning("pose rejected by workspace check: %s", new)
                arm = ("yaw", "shoulder", "elbow", "pitch")
                new = clamp_pose(dict(new, **{j: self.goal[j] for j in arm}))
            if replace:
                self._segs.clear()
            start = dict(self.current) if replace else dict(self.goal)
            path = [new]
            if not path_ok(start, new):
                via = dict(new, yaw=new["yaw"] if path_ok(start, dict(start, yaw=new["yaw"])) else HOME["yaw"],
                           shoulder=HOME["shoulder"], elbow=HOME["elbow"], pitch=HOME["pitch"])
                path = [via, new]
            prev = start
            for p in path:
                self._segs.append(_Seg(p, self._duration(prev, p, speed)))
                prev = p
            self.goal = new
            self._release_when_idle = False
            self._idle.clear()

    def alive_pose(self, now):
        """Planned pose plus the idle sway and speech bob, if that stays inside the workspace."""
        t = now - self._t0
        k = self._sway_amp
        p = dict(self.current)
        p["yaw"] += k * config.SWAY["yaw"] * math.sin(2 * math.pi * t / 11.0)
        p["shoulder"] += k * config.SWAY["shoulder"] * math.sin(2 * math.pi * t / 8.3 + 1.0)
        p["pitch"] += k * config.SWAY["pitch"] * math.sin(2 * math.pi * t / 6.1 + 2.0) - config.SPEECH_BOB * self._speech
        p["eye"] += k * config.SWAY["eye"] * _saccade(t)
        p = clamp_pose(p)
        return p if workspace_ok(p) else self.current

    def speech(self, level):
        """Feed the speech envelope (0..1); lifts the head slightly on stressed syllables."""
        self._speech = max(0.0, min(1.0, level))

    def set_awake(self, awake):
        self._awake = awake

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

    # ---------------------------------------------------------- gestures
    def perform(self, steps):
        """Run [(pose, speed, hold_s), ...] in the background; a newer gesture cancels it."""
        self._gesture_gen += 1
        gen = self._gesture_gen

        def run():
            for pose, speed, hold in steps:
                if gen != self._gesture_gen:
                    return
                self.move(pose, speed)
                self.wait(3.0)
                time.sleep(hold)

        threading.Thread(target=run, name="gesture", daemon=True).start()

    def cancel_gesture(self):
        self._gesture_gen += 1

    def home(self, speed=0.7):
        self.cancel_gesture()
        self.move(HOME, speed)

    def rest(self):
        """Settle at the spring's balance point, head level, stop swaying, then yaw/tilt/shutters
        go limp. The shoulder holds almost nothing here; the elbow holds the head."""
        self.cancel_gesture()
        self._awake = False
        self.move(REST, 0.5)
        with self._lock:
            self._release_when_idle = True

    def look(self, angle_deg):
        """Swing toward the talker with a small overshoot and settle, leaning in."""
        self.cancel_gesture()
        self._awake = True
        yaw = look_pose(angle_deg)["yaw"]
        over = max(config.LIMITS["yaw"][0], min(config.LIMITS["yaw"][1], yaw + (6.0 if yaw > self.current["yaw"] else -6.0)))
        self.perform([({"yaw": over, "shoulder": 14.0, "elbow": -10.0, "pitch": -6.0, "shutter": 1.0, "eye": 0.3}, 1.2, 0.0),
                      ({"yaw": yaw, "shoulder": 12.0, "elbow": -8.0, "pitch": -4.0, "eye": 0.2}, 0.5, 0.0)])

    def listen(self):
        self.move({"shoulder": 12.0, "elbow": -8.0, "pitch": -4.0, "shutter": 1.0, "eye": 0.2}, 1.0)

    def think(self):
        self.move({"shoulder": 30.0, "elbow": -34.0, "pitch": 8.0, "shutter": 0.7, "eye": 0.6}, 0.6)   # eye rolls up

    def filing(self):
        """Rapid shutter pulse while 'logging' something."""
        steps = [({"shutter": 0.35}, 4.0, 0.03), ({"shutter": 1.0}, 4.0, 0.03)] * 3
        self.perform(steps)

    def stamp(self):
        """Loom: rise and squint, then the whole head drops ~80 mm with a nose-down snap (THUNK)."""
        self.perform([({"shoulder": 35.0, "elbow": -35.0, "pitch": 10.0, "shutter": 0.25, "eye": -0.4}, 1.0, 0.35),
                      ({"shoulder": -5.0, "elbow": 5.0, "pitch": 15.0}, 4.0, 0.3),
                      ({"shoulder": 15.0, "elbow": -15.0, "pitch": 8.0}, 0.6, 0.0)])

    def nod(self):
        self.perform([({"pitch": 12.0, "shutter": 1.0, "eye": 0.3}, 1.5, 0.05), ({"pitch": 0.0, "eye": 0.0}, 1.2, 0.0)])

    def mood(self, mood):
        if mood == "approve":
            self.nod()
        elif mood == "infraction":
            self.stamp()
        elif mood == "concern":
            self.cancel_gesture()
            self.move({"shoulder": 8.0, "elbow": -10.0, "pitch": -3.0, "shutter": 1.0, "eye": 0.0}, 0.4)  # low, close, still
        elif mood == "sulk":
            self.cancel_gesture()
            self.move(SULK, 0.5)
        else:
            self.cancel_gesture()
            self.move({"pitch": 0.0, "shutter": 1.0, "eye": 0.0}, 0.8)
