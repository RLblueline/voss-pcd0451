"""Arm, head tilt and eye shutters on a PCA9685.

Joints: shoulder / elbow (horizontal plane), tilt (head pitch), shutter (eye aperture 0..1).
Moves are planned in joint space, eased, collision-checked against the housing and wall,
and executed by a 50 Hz thread. Printing calls quiesce() so the arm never moves while
the printer runs.
"""
import contextlib
import json
import logging
import math
import threading
import time
from collections import deque

from . import config

log = logging.getLogger("memo.body")

JOINTS = ("shoulder", "elbow", "tilt", "shutter")
HOME = {"shoulder": 90.0, "elbow": 0.0, "tilt": 0.0, "shutter": 1.0}
SULK = {"shoulder": 150.0, "elbow": 30.0, "tilt": 25.0, "shutter": 0.45}


# ------------------------------------------------------------------ kinematics
def fk(shoulder, elbow):
    """Return elbow-axis (x, y) and head-centre (x, y) in mm (plan view)."""
    sx, sy = config.SHOULDER_XY
    t1 = math.radians(shoulder)
    t12 = math.radians(shoulder + elbow)
    ex, ey = sx + config.L1 * math.cos(t1), sy + config.L1 * math.sin(t1)
    hx, hy = ex + config.HEAD_CENTER * math.cos(t12), ey + config.HEAD_CENTER * math.sin(t12)
    return (ex, ey), (hx, hy)


def _clear(x, y, r):
    if abs(x) <= config.HOUSING_HALF_W + r:
        return y >= config.HOUSING_D + r + config.CLEARANCE
    return y >= r + config.CLEARANCE


def workspace_ok(shoulder, elbow):
    lo, hi = config.LIMITS["shoulder"]
    if not lo <= shoulder <= hi:
        return False
    lo, hi = config.LIMITS["elbow"]
    if not lo <= elbow <= hi:
        return False
    (ex, ey), (hx, hy) = fk(shoulder, elbow)
    if not _clear(ex, ey, config.ELBOW_R):
        return False
    for f in (0.25, 0.5, 0.75):
        if not _clear(ex + (hx - ex) * f, ey + (hy - ey) * f, config.LINK_R):
            return False
    return _clear(hx, hy, config.HEAD_R)


def path_ok(a, b, steps=24):
    for i in range(steps + 1):
        f = i / steps
        if not workspace_ok(a["shoulder"] + (b["shoulder"] - a["shoulder"]) * f,
                            a["elbow"] + (b["elbow"] - a["elbow"]) * f):
            return False
    return True


def clamp_pose(p):
    return {j: max(config.LIMITS[j][0], min(config.LIMITS[j][1], float(p[j]))) for j in JOINTS}


def look_pose(angle_deg):
    """Arm pose that points the head toward a talker at angle_deg (+ toward +X)."""
    a = max(-config.DOA_MAX_DEG, min(config.DOA_MAX_DEG, angle_deg))
    return {"shoulder": 90.0 - a / 2.0, "elbow": -a / 2.0}


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


def joint_to_us(cal, joint, value):
    c = cal[joint]
    if joint == "shutter":
        deg = c["closed_deg"] + value * (c["open_deg"] - c["closed_deg"])
    else:
        deg = c["offset_deg"] + (-value if c.get("invert") else value)
    deg = max(0.0, min(float(c["range_deg"]), deg))
    return c["min_us"] + (c["max_us"] - c["min_us"]) * deg / c["range_deg"]


class ServoOutputs:
    def __init__(self, cal=None):
        self.cal = cal or load_calibration()
        self.enabled = False
        self.pca = None if config.SIM else PCA9685()
        self.oe = None
        if not config.SIM and config.SERVO_OE_GPIO >= 0:
            from gpiozero import OutputDevice
            # OE is active-low: on() drives the pin low = outputs enabled. Starts disabled.
            self.oe = OutputDevice(config.SERVO_OE_GPIO, active_high=False, initial_value=False)
        self.last_us = {}

    def write(self, pose):
        for j in JOINTS:
            us = joint_to_us(self.cal, j, pose[j])
            self.last_us[j] = us
            if self.pca:
                self.pca.set_us(self.cal[j]["ch"], us)

    def enable(self, pose):
        self.write(pose)
        if self.oe:
            self.oe.on()
        self.enabled = True

    def disable(self):
        if self.oe:
            self.oe.off()
        elif self.pca:
            for j in JOINTS:
                self.pca.full_off(self.cal[j]["ch"])
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

    # ---------------------------------------------------------- lifecycle
    def start(self):
        self._thread = threading.Thread(target=self._run, name="body", daemon=True)
        self._thread.start()

    def stop(self):
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
                    e = a * a * (3 - 2 * a)
                    self.current = {j: seg.start[j] + (seg.end[j] - seg.start[j]) * e for j in JOINTS}
                    if self.out.enabled:
                        self.out.write(self.current)
                    else:
                        self.out.enable(self.current)
                    if a >= 1.0:
                        self._segs.popleft()
                if not self._segs:
                    if self._release_when_idle and self.out.enabled and not self._frozen:
                        self.out.disable()
                        self._release_when_idle = False
                    self._idle.set()
            time.sleep(0.02)

    # ---------------------------------------------------------- moves
    @staticmethod
    def _duration(a, b, speed):
        t = max(abs(b[j] - a[j]) / (config.MAX_SPEED[j] * speed) for j in JOINTS)
        return max(0.05, t * 1.5)            # smoothstep peaks at 1.5x mean speed

    def move(self, target, speed=1.0, replace=True):
        """Move to a (partial) pose. Arm parts that fail the workspace check are ignored."""
        with self._lock:
            new = dict(self.goal)
            new.update(target)
            new = clamp_pose(new)
            if not workspace_ok(new["shoulder"], new["elbow"]):
                log.warning("pose rejected by workspace check: %s", new)
                new["shoulder"], new["elbow"] = self.goal["shoulder"], self.goal["elbow"]
            if replace:
                self._segs.clear()
            start = dict(self.current) if replace else dict(self.goal)
            path = [new]
            if not path_ok(start, new):
                via = dict(new, shoulder=HOME["shoulder"], elbow=HOME["elbow"])
                path = [via, new]
            prev = start
            for p in path:
                self._segs.append(_Seg(p, self._duration(prev, p, speed)))
                prev = p
            self.goal = new
            self._release_when_idle = False
            self._idle.clear()

    def wait(self, timeout=5.0):
        return self._idle.wait(timeout)

    @property
    def moving(self):
        return not self._idle.is_set()

    @contextlib.contextmanager
    def quiesce(self, timeout=5.0):
        """Stop the arm and cut servo outputs (e.g. while printing)."""
        self.wait(timeout)
        with self._lock:
            self._frozen = True
            was_enabled = self.out.enabled
            self.out.disable()
        try:
            yield
        finally:
            with self._lock:
                self._frozen = False
                if was_enabled:
                    self.out.enable(self.current)

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
        """Level the head, open the eye, then go limp and silent."""
        self.home(0.6)
        with self._lock:
            self._release_when_idle = True

    def look(self, angle_deg):
        self.cancel_gesture()
        p = look_pose(angle_deg)
        p.update(tilt=-3.0, shutter=1.0)
        self.move(p, 1.0)

    def listen(self):
        self.move({"tilt": -3.0, "shutter": 1.0}, 1.0)

    def think(self):
        self.move({"tilt": 8.0, "shutter": 0.7}, 0.6)

    def filing(self):
        """Rapid shutter pulse while 'logging' something."""
        steps = [({"shutter": 0.35}, 4.0, 0.03), ({"shutter": 1.0}, 4.0, 0.03)] * 3
        self.perform(steps)

    def stamp(self):
        """Audit squint + fast nose-down snap (the 'THUNK')."""
        self.perform([({"shutter": 0.25}, 3.0, 0.0),
                      ({"tilt": 30.0}, 4.0, 0.25),
                      ({"tilt": 12.0}, 0.8, 0.0)])

    def nod(self):
        self.perform([({"tilt": 12.0, "shutter": 1.0}, 1.5, 0.05), ({"tilt": 0.0}, 1.2, 0.0)])

    def mood(self, mood):
        if mood == "approve":
            self.nod()
        elif mood == "infraction":
            self.stamp()
        elif mood == "concern":
            self.cancel_gesture()
            self.move({"tilt": -5.0, "shutter": 1.0}, 0.4)   # locked open, no twitching
        elif mood == "sulk":
            self.cancel_gesture()
            self.move(SULK, 0.5)
        else:
            self.cancel_gesture()
            self.move({"tilt": 0.0, "shutter": 1.0}, 0.8)
