"""Render an animation of V.O.S.S. performing a short routine, using the firmware's poses,
minimum-jerk easing and idle sway. Every frame is checked with the firmware's workspace check.

    python3 cad/tools/animate.py            # frames -> /tmp/voss_anim, then docs/img/voss_routine.mp4/.gif
"""
import math, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VOSS_SIM", "1")
from voss import body, config  # noqa: E402

FPS = 6
OUT = Path("/tmp/voss_anim")
CAM = "0,220,-170,74,0,205,2050"
J = ("yaw", "shoulder", "elbow", "pitch", "eye", "shutter")

def P(**kw):
    p = dict(yaw=90, shoulder=20, elbow=-20, pitch=0, eye=0, shutter=1)
    p.update(kw); return p

# (seconds to reach, pose, hold seconds, caption)
ROUTINE = [
    (0.0, P(shoulder=50, elbow=-50), 0.7, "Rest: floating at the spring's balance point"),
    (1.2, P(), 0.4, "Wake word heard"),
    (0.9, P(yaw=44, shoulder=14, elbow=-10, pitch=-6, eye=0.3), 0.0, "Turns toward Employee..."),
    (0.5, P(yaw=50, shoulder=12, elbow=-8, pitch=-4, eye=0.2), 0.6, "...and leans in to listen"),
    (1.0, P(yaw=60, shoulder=30, elbow=-34, pitch=8, eye=0.6, shutter=0.7), 0.7, "Thinking: rises, eye rolls up"),
    (1.3, P(yaw=60, shoulder=0, elbow=0, pitch=-6, eye=0.2), 0.6, "Full reach toward Employee"),
    (1.0, P(yaw=70, shoulder=35, elbow=-35, pitch=10, eye=-0.4, shutter=0.25), 0.4, "Infraction detected: looms and squints"),
    (0.3, P(yaw=70, shoulder=-5, elbow=5, pitch=15, eye=-0.4, shutter=0.25), 0.5, "STAMP"),
    (0.8, P(yaw=70, shoulder=15, elbow=-15, pitch=8, eye=-0.2, shutter=0.6), 0.2, "Logged to your permanent record"),
    (0.5, P(yaw=80, pitch=12, eye=0.3), 0.0, "Approval nod"),
    (0.5, P(yaw=80, pitch=0, eye=0.0), 0.5, "Approval nod"),
    (1.5, P(yaw=145, shoulder=30, elbow=-30, pitch=15, eye=-0.6, shutter=0.45), 0.8, "Sulk"),
    (1.5, P(shoulder=50, elbow=-50), 0.6, "Back to rest"),
]


def ease(a):
    return a * a * a * (a * (6 * a - 15) + 10)


def timeline():
    frames = []
    cur = ROUTINE[0][1]
    for dur, pose, hold, cap in ROUTINE:
        n = max(1, round(dur * FPS))
        start = dict(cur)
        if dur > 0:
            for i in range(1, n + 1):
                e = ease(i / n)
                frames.append(({j: start[j] + (pose[j] - start[j]) * e for j in J}, cap, False))
        for _ in range(round(hold * FPS)):
            frames.append((dict(pose), cap, True))
        cur = pose
    # idle sway on held frames (same rhythms as the firmware overlay, faded in)
    out, amp = [], 0.0
    for k, (p, cap, held) in enumerate(frames):
        t = k / FPS
        amp = min(1.0, amp + 1.0 / FPS) if held else max(0.0, amp - 2.0 / FPS)
        q = dict(p)
        q["yaw"] += amp * config.SWAY["yaw"] * math.sin(2 * math.pi * t / 11.0)
        q["shoulder"] += amp * config.SWAY["shoulder"] * math.sin(2 * math.pi * t / 8.3 + 1.0)
        q["pitch"] += amp * config.SWAY["pitch"] * math.sin(2 * math.pi * t / 6.1 + 2.0)
        q["eye"] += amp * config.SWAY["eye"] * body._saccade(t)
        out.append((q, cap))
    return out


def main(limit=None):
    frames = timeline()
    bad = [i for i, (p, _) in enumerate(frames) if not body.workspace_ok(dict(p, shutter=p["shutter"]))]
    print(f"{len(frames)} frames, {len(bad)} rejected by the firmware workspace check")
    if bad:
        sys.exit(f"invalid frames: {bad[:10]}")
    OUT.mkdir(exist_ok=True)
    done = 0
    for i, (p, cap) in enumerate(frames):
        f = OUT / f"f{i:04d}.png"
        if f.exists():
            continue
        if limit is not None and done >= limit:
            break
        done += 1
        args = ["openscad", "-q", "-o", str(f), "--imgsize=640,720", "--colorscheme=Tomorrow", f"--camera={CAM}",
                "-D", "$fn=20", "-D", f"YAW={p['yaw']:.2f}", "-D", f"SH={p['shoulder']:.2f}", "-D", f"EL={p['elbow']:.2f}",
                "-D", f"PITCH={p['pitch']:.2f}", "-D", f"EYE={p['eye']:.3f}", "-D", f"SHUT={p['shutter']:.3f}",
                str(ROOT / "cad" / "assembly.scad")]
        subprocess.run(args, check=True)
        (OUT / f"f{i:04d}.txt").write_text(cap)
        print(f"frame {i + 1}/{len(frames)}", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
