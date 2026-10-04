"""Reach envelope over every pose the firmware accepts (head level, eye centred).

    python3 cad/tools/reach.py
"""
import itertools, math, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("VOSS_SIM", "1")
from voss import body, config   # noqa: E402

FRONT = 61.0          # head front face ahead of the tilt axis (axis frame)
EYE_DZ = -116.0       # eye centre below the tilt axis


def main():
    best = dict(max_out=0, min_out=1e9, max_side=0, z_hi=-1e9, z_lo=1e9, face_max=0)
    n = 0
    for yaw, sh, el in itertools.product(range(5, 176, 5), range(-20, 76, 5), range(-110, 41, 5)):
        p = dict(body.HOME, yaw=yaw, shoulder=sh, elbow=el, pitch=0.0)
        if not body.workspace_ok(p):
            continue
        n += 1
        _, (hx, hy, hz) = body.fk(yaw, sh, el)
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        fx, fy = hx + FRONT * c, hy + FRONT * s
        best["max_out"] = max(best["max_out"], fy)
        best["min_out"] = min(best["min_out"], hy)
        best["max_side"] = max(best["max_side"], abs(hx))
        best["z_hi"] = max(best["z_hi"], hz + EYE_DZ)
        best["z_lo"] = min(best["z_lo"], hz + EYE_DZ)
        best["face_max"] = max(best["face_max"], math.hypot(fx, fy - 0))
    _, (hx, hy, hz) = body.fk(90, 20, -20)
    print(f"{n} valid poses (head level)")
    print(f"home: head front {hy + FRONT:.0f} mm from the wall, eye {hz + EYE_DZ:.0f} mm below the shoulder axis")
    print(f"farthest head front from the wall: {best['max_out']:.0f} mm")
    print(f"closest head centre to the wall:   {best['min_out']:.0f} mm")
    print(f"sideways: head centre up to +-{best['max_side']:.0f} mm from the housing centreline")
    print(f"eye height range: {best['z_lo']:.0f} .. {best['z_hi']:.0f} mm (span {best['z_hi'] - best['z_lo']:.0f}) "
          f"+ {2 * 24} mm eye travel in the slot")


if __name__ == "__main__":
    main()
