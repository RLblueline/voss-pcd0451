"""Bring-up and calibration tool.

  python -m memo.calibrate zero                  zero pose: yaw 90, link1 level, links in line, head level
  python -m memo.calibrate set shoulder 30       move one joint: yaw|shoulder|elbow|pitch|shutter
  python -m memo.calibrate us 2 1500             raw pulse on a PCA9685 channel
  python -m memo.calibrate trim elbow -3         nudge a channel's offset_deg (yaw|shoulder|elbow|tilt) and save
  python -m memo.calibrate shutter 40 130        set shutter closed/open servo degrees and save
  python -m memo.calibrate demo                  cycle every mood (pose + lights)
  python -m memo.calibrate say "text" [mood]     speak a line with pose and lights
  python -m memo.calibrate leds                  LED test pattern
  python -m memo.calibrate print                 print a test memo
  python -m memo.calibrate doa                   live direction-of-arrival readout
  python -m memo.calibrate off                   release ALL servos (support the arm first!)
"""
import sys
import time

from . import config
from .body import ZERO, JOINTS, Body, PCA9685, ServoOutputs, load_calibration, save_calibration


def _body():
    b = Body()
    b.start()
    return b


def main(argv=None):
    a = argv if argv is not None else sys.argv[1:]
    if not a:
        print(__doc__)
        return
    cmd = a[0]
    if cmd == "zero":
        b = _body()
        b.move(ZERO, 0.5)
        b.wait(10)
        print("Zero pose:", {j: ZERO[j] for j in JOINTS}, "pulses:", b.out.last_us)
        input("Fit horns now. Enter to release (support the arm)...")
        b.stop(park=False)
    elif cmd == "set":
        b = _body()
        b.move({a[1]: float(a[2])}, 0.5)
        b.wait(10)
        print(a[1], "->", a[2], "pulses:", b.out.last_us)
        input("Enter to release (support the arm)...")
        b.stop(park=False)
    elif cmd == "us":
        pca = PCA9685()
        pca.set_us(int(a[1]), float(a[2]))
        input("Enter to release...")
        pca.full_off(int(a[1]))
    elif cmd == "trim":
        cal = load_calibration()
        cal[a[1]]["offset_deg"] += float(a[2])
        save_calibration(cal)
        print(a[1], "offset_deg =", cal[a[1]]["offset_deg"])
    elif cmd == "shutter":
        cal = load_calibration()
        cal["shutter"].update(closed_deg=float(a[1]), open_deg=float(a[2]))
        save_calibration(cal)
        print("shutter", cal["shutter"])
    elif cmd == "off":
        ServoOutputs().disable()
    elif cmd == "leds":
        from .lights import Strip
        s = Strip()
        for col in [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 160, 70)]:
            for i in range(config.LED_COUNT):
                s.show([col if k <= i else (0, 0, 0) for k in range(config.LED_COUNT)])
                time.sleep(0.03)
            time.sleep(0.4)
        s.show([(0, 0, 0)] * config.LED_COUNT)
    elif cmd == "print":
        from .printer import Printer, build
        print(Printer().print_job(build("memo", "Printer test", "If you can read this, the printer works.")))
    elif cmd == "doa":
        from .audio import Capture, doa_degrees
        cap = Capture()
        cap.start()
        try:
            while True:
                time.sleep(0.5)
                ang = doa_degrees(cap.recent(0.5))
                print("quiet" if ang is None else f"{ang:+5.0f} deg  " + " " * int((ang + 60) / 4) + "|")
        except KeyboardInterrupt:
            cap.stop()
    elif cmd in ("demo", "say"):
        from .main import Memo
        m = Memo(voice=True)
        m.start()
        if cmd == "say":
            m.speak(a[2] if len(a) > 2 else "neutral", a[1])
        else:
            lines = {"neutral": "Good morning, Employee. Attendance has been noted.",
                     "approve": "Excellent work. A commendation has been drafted.",
                     "infraction": "That is a clear violation of policy four nineteen.",
                     "concern": "Hey. I'm here. Take a breath, and tell me what's going on.",
                     "sulk": "Fine. I will be filing this under hurtful."}
            for mood, line in lines.items():
                print("mood:", mood)
                m.speak(mood, line)
                time.sleep(2.5)
        time.sleep(1)
        m.stop()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
