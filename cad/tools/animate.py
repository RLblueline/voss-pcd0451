"""Render V.O.S.S. performing an expressive routine. The real firmware Body (gestures, easing,
idle sway, blinks, speech bob, workspace check) runs on a virtual clock; every frame is a
sample of its output pose.

    python3 cad/tools/animate.py [N]        # render up to N more frames into /tmp/voss_anim2
    python3 cad/tools/compose_anim.py       # captions + docs/img/voss_expressive.mp4/.gif
"""
import math, os, random, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VOSS_SIM", "1")
from voss import body  # noqa: E402

FPS = 24
SIM_HZ = 48
OUT = Path("/tmp/voss_anim3")
CAM = "0,220,-100,74,0,205,2050"

# (time s, action, caption); speech windows feed a syllable envelope to body.speech()
SCRIPT = [
    (0.0, "rest", "Rest: floating at the spring's balance point"),
    (0.6, "look", "Wake word: eye flicks first, then she swings over"),
    (2.0, "think", "Thinking: rises, eye rolls up"),
    (3.8, ("express", "approve", None), "[approve] dip, pop, nod"),
    (5.6, ("express", "neutral", "peer"), "[peer] suspicious lean-in"),
    (7.8, ("express", "infraction", None), "[infraction] loom, squint... STAMP"),
    (11.0, ("gesture", "double_take"), "[double_take]"),
    (13.2, "rest", "Back to rest"),
]
SPEECH = [(4.0, 5.4), (9.4, 10.8)]
END = 15.0


class Clock:
    t = 0.0

    def __call__(self):
        return self.t


def simulate():
    clk = Clock()
    b = body.Body(clock=clk)
    b.current = dict(body.REST); b.goal = dict(body.REST); b._awake = False
    rng = random.Random(7)
    frames, caption, k, syl = [], "", 0, 0.0
    steps = int(END * SIM_HZ)
    for i in range(steps + 1):
        t = i / SIM_HZ
        while k < len(SCRIPT) and SCRIPT[k][0] <= t:
            _, act, caption = SCRIPT[k]
            if act == "rest":
                b.rest() if t > 0 else None
            elif act == "look":
                b.set_awake(True); b.look(30)
            elif act == "think":
                b.think()
            elif isinstance(act, tuple) and act[0] == "express":
                b.express(act[1], act[2])
            elif isinstance(act, tuple) and act[0] == "gesture":
                b.gesture(act[1])
            k += 1
        if any(a <= t < z for a, z in SPEECH):
            if i % 10 == 0:
                syl = rng.choice([0.2, 0.5, 0.9, 1.0, 0.3, 0.8])
            b.speech(syl * (0.6 + 0.4 * math.sin(t * 9)))
        else:
            b.speech(0.0)
        clk.t = t
        b.tick(t)
        if i % (SIM_HZ // FPS) == 0:
            frames.append((dict(b.output_pose), caption))
    return frames


def main(limit=None):
    frames = simulate()
    bad = [i for i, (p, _) in enumerate(frames) if not body.workspace_ok(p)]
    print(f"{len(frames)} frames ({len(frames) / FPS:.0f} s), {len(bad)} rejected by the workspace check")
    if bad:
        sys.exit(f"invalid frames: {bad[:10]}")
    OUT.mkdir(exist_ok=True)
    done = 0
    for i, (p, cap) in enumerate(frames):
        f = OUT / f"f{i:04d}.png"
        (OUT / f"f{i:04d}.txt").write_text(cap)
        if f.exists():
            continue
        if limit is not None and done >= limit:
            break
        done += 1
        args = ["openscad", "-q", "-o", str(f), "--imgsize=640,720", "--colorscheme=Tomorrow", f"--camera={CAM}",
                "-D", "$fn=20", "-D", "FAST=true", "-D", f"YAW={p['yaw']:.2f}", "-D", f"SH={p['shoulder']:.2f}", "-D", f"EL={p['elbow']:.2f}",
                "-D", f"PITCH={p['pitch']:.2f}", "-D", f"EYE={p['eye']:.3f}", "-D", f"SHUT={p['shutter']:.3f}",
                str(ROOT / "cad" / "assembly.scad")]
        subprocess.run(args, check=True)
        print(f"frame {i + 1}/{len(frames)}", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
