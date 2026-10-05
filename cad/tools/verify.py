"""Build-readiness checks: every bolt path is clear through both mating parts, and every print
file is a single watertight solid.   python3 tools/verify.py   (from cad/, after export.sh)"""
import math, sys, warnings
from pathlib import Path
import numpy as np, trimesh
warnings.filterwarnings("ignore")
STL = Path(__file__).resolve().parent.parent / "stl"
HD, HW, WALL, HS, ARM_Z0 = 70, 144, 3, 15, 70
X2 = 114                                        # link2 tilt axis x


def load(n):
    m = trimesh.load(STL / f"{n}.stl", force="mesh"); m.merge_vertices(); return m


def rod(p0, p1, d):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    v = p1 - p0; L = np.linalg.norm(v)
    c = trimesh.creation.cylinder(radius=d / 2, height=L, sections=24)
    T = trimesh.geometry.align_vectors([0, 0, 1], v / L); T[:3, 3] = (p0 + p1) / 2
    return c.apply_transform(T)


def hits(cyl, part):
    tot = 0.0
    for b in [part] if part.is_volume else part.split(only_watertight=False):
        r = trimesh.boolean.intersection([cyl, b], engine="manifold")
        tot += 0 if r is None or r.is_empty else r.volume
    return tot


# (name, parts in a shared frame, p0, p1, probe diameter) - probe is a little under the screw's
# minor diameter, so any misaligned hole shows up as material in the way
BOLTS = []
for x in (-24, 24):
    for z in (-136 + ARM_Z0, -52 + ARM_Z0):
        BOLTS.append((f"tower->housing M3 ({x},{z})", ["housing", "tower"], (x, 64, z), (x, 75, z), 2.8))
BOLTS.append(("harness hole housing/tower", ["housing", "tower"], (0, 64, -20), (0, 75, -20), 9.0))
for sx in (-1, 1):
    for z in (10, -160):
        BOLTS.append((f"housing->back plate M3 ({sx},{z})", ["housing", "back_plate"], (sx * 73, 2, z), (sx * 62, 2, z), 2.5))
for x in (X2 - 10, X2 + 10):
    BOLTS.append((f"post->link2 M3 x={x}", ["link2", "post"], (x, 11, -20), (x, 11, 4), 2.2))
for part, cov, xs in (("link1", "cover1", (52, 68)), ("link2", "cover2", (52, 90))):
    for x in xs:
        BOLTS.append((f"{cov}->{part} M3 x={x}", [part, cov], (x, 0, 6), (x, 0, 27), 2.6))
for sy in (-1, 1):
    for x, z in ((-3, -45), (-3, -187), (-27, -187)):
        yin = 61 if z == -45 else 58      # stop inside the 6 mm insert hole
        BOLTS.append((f"head wall->rod bar M3 ({x},{sy * 60},{z})", ["head_mid", "eye_rods"], (x + HS, sy * 72, z), (x + HS, sy * yin, z), 2.6))
for x in (-60, 32):
    for sy in (-1, 1):
        BOLTS.append((f"seam top/mid M3 ({x},{sy * 63})", ["head_top", "head_mid"], (x + HS, sy * 63, -52), (x + HS, sy * 63, -35), 2.6))
        BOLTS.append((f"seam mid/chin M3 ({x},{sy * 59.5})", ["head_mid", "head_chin"], (x + HS, sy * 59.5, -207), (x + HS, sy * 59.5, -190), 2.6))

PRINT = ["housing", "back_plate", "tower", "turret", "link1", "link2", "post", "cover1", "cover2",
         "p_head_top", "p_head_mid", "p_head_chin", "p_eye_plate", "p_rod_bar_top", "p_rod_bar_bottom", "p_carriage", "p_lens",
         "p_lid_top", "p_lid_bottom", "p_pinion18", "p_pinion36", "p_yaw_coupler", "p_pulley", "p_pulley_small",
         "p_spring_block", "p_neck_boot", "p_bumper"]


def main():
    ok = True
    cache = {}
    print("BOLT PATHS (probe cylinder must pass through both parts without touching material)")
    for name, parts, p0, p1, d in BOLTS:
        c = rod(p0, p1, d)
        v = [hits(c, cache.setdefault(p, load(p))) for p in parts]
        good = all(x < 0.5 for x in v)
        ok &= good
        print(f"  {'OK ' if good else 'BAD'} {name:44s} " + "  ".join(f"{p}:{x:.1f}" for p, x in zip(parts, v)))
    print("\nPRINT FILES (watertight, single body)")
    for p in PRINT:
        m = load(p)
        bodies = m.split(only_watertight=False)
        good = m.is_volume and len(bodies) == 1
        ok &= good
        e = m.extents
        print(f"  {'OK ' if good else 'BAD'} {p:16s} {e[0]:6.1f} x {e[1]:6.1f} x {e[2]:6.1f} mm  {m.volume / 1000:6.1f} cm3  bodies={len(bodies)}")
    print("\nALL CHECKS PASSED" if ok else "\nPROBLEMS FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
