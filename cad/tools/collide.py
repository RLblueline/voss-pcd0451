"""Sweep every joint through its limits and report part-part interference.

Uses the STLs from tools/export.sh (each in its local frame) and the same transforms as
assembly.scad. Also checks a grid of poses the firmware's workspace check accepts.

    python3 tools/collide.py            (from cad/, after ./tools/export.sh)
"""
import itertools
import math
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import trimesh

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
STL = HERE.parent / "stl"
sys.path.insert(0, str(HERE.parent.parent))
os.environ.setdefault("MEMO_SIM", "1")
from memo import body as fw  # noqa: E402

SY, L1, L2, TILT_OFF, TILT_DROP = 112, 120, 100, 14, 72
TOL = 1.0   # mm^3 of overlap tolerated (coplanar contact faces)

WORLD = ["housing", "back_plate", "tower", "yaw_body"]
TURRET = ["turret", "sh_body", "coupler"]
LINK1 = ["link1", "el_body", "sh_horn"]
LINK2 = ["link2", "post", "tl_body", "el_horn"]
HEAD = ["head_top", "head_mid", "head_chin", "ears", "cartridge", "sg90", "leds", "bumper", "paper", "s3_horn"]

_cache = {}


def mesh(name):
    if name not in _cache:
        m = trimesh.load(STL / f"{name}.stl", force="mesh")
        m.merge_vertices()
        _cache[name] = [m] if m.is_volume else list(m.split(only_watertight=False))
    return _cache[name]


def tr(x, y, z):
    return trimesh.transformations.translation_matrix([x, y, z])


def rz(a):
    return trimesh.transformations.rotation_matrix(math.radians(a), [0, 0, 1])


def ry(a):
    return trimesh.transformations.rotation_matrix(math.radians(a), [0, 1, 0])


def T_t(yaw):
    return tr(0, SY, 0) @ rz(yaw)


def T_l1(yaw, sh):
    return T_t(yaw) @ ry(-sh)


def T_l2(yaw, sh, el):
    return T_l1(yaw, sh) @ tr(L1, 0, 0) @ ry(-el)


def T_h(yaw, sh, el, tilt):
    return T_l2(yaw, sh, el) @ tr(L2 + TILT_OFF, 0, -TILT_DROP) @ ry(tilt)


def overlap(a, Ta, b, Tb):
    total = 0.0
    for A0 in mesh(a):
        A = A0.copy().apply_transform(Ta)
        for B0 in mesh(b):
            B = B0.copy().apply_transform(Tb)
            lo = np.maximum(A.bounds[0], B.bounds[0])
            hi = np.minimum(A.bounds[1], B.bounds[1])
            if np.any(hi <= lo):
                continue
            try:
                r = trimesh.boolean.intersection([A, B], engine="manifold")
                total += float(r.volume) if r is not None and not r.is_empty else 0.0
            except Exception as e:  # pragma: no cover
                print("  boolean failed", a, b, e)
                return -1.0
    return total


def check(label, pairs):
    hits = []
    for a, Ta, b, Tb, tag in pairs:
        v = overlap(a, Ta, b, Tb)
        if v > TOL or v < 0:
            hits.append((v, a, b, tag))
    print(f"{label:<50} {'OK' if not hits else f'{len(hits)} HITS'}")
    for v, a, b, tag in sorted(hits, reverse=True)[:12]:
        print(f"    {a} x {b} @ {tag}: {v:.1f} mm^3")
    return not hits


def main():
    ok = True
    I = np.eye(4)
    H = fw.HOME
    # A: yaw sweep, arm at home
    pairs = []
    for yw in range(5, 176, 5):
        pairs += [(a, T_t(yw), b, I, f"yaw={yw}") for a in TURRET for b in WORLD]
        pairs += [(a, T_l1(yw, H["shoulder"]), b, I, f"yaw={yw}") for a in LINK1 for b in WORLD]
    ok &= check("yaw 5..175 : turret/link1 vs housing/tower", pairs)
    # B: shoulder sweep (link2 kept level)
    pairs = []
    for sh in range(-20, 76, 5):
        el = max(-110, min(40, -sh))
        pairs += [(a, T_l1(90, sh), b, T_t(90), f"sh={sh}") for a in LINK1 for b in TURRET]
        pairs += [(a, T_l1(90, sh), b, I, f"sh={sh}") for a in LINK1 for b in WORLD]
        pairs += [(a, T_l2(90, sh, el), b, T_t(90), f"sh={sh} el={el}") for a in LINK2 for b in TURRET]
    ok &= check("shoulder -20..75 : link1/link2 vs turret/tower", pairs)
    # C: elbow sweep, link2 + head vs link1 and turret
    pairs = []
    for el in range(-110, 41, 5):
        pairs += [(a, T_l2(90, 20, el), b, T_l1(90, 20), f"el={el}") for a in LINK2 for b in LINK1]
        pairs += [(a, T_l2(90, 20, el), b, T_t(90), f"el={el}") for a in LINK2 for b in TURRET]
        t = max(-35, min(40, 20 + el))
        pairs += [(a, T_h(90, 20, el, t), b, T_l1(90, 20), f"el={el} t={t}") for a in HEAD for b in LINK1]
    ok &= check("elbow -110..40 : link2/head vs link1/turret", pairs)
    # D: tilt sweep, shutters open and closed
    head_s = lambda s: HEAD + [f"shut_top_{s}", f"shut_bot_{s}", "pinion"]
    pairs = [(a, T_h(90, 20, -20, t), b, T_l2(90, 20, -20), f"t={t} s={s}") for t in range(-35, 41, 5)
             for s in (0, 1) for a in head_s(s) for b in LINK2]
    ok &= check("tilt -35..40 : head vs link2/post", pairs)
    # E: shutters vs head internals (pinion/rack mesh excluded)
    static = [h for h in HEAD if h != "s3_horn"]
    pairs = []
    for s in ("0", "0.5", "1"):
        for sh_ in (f"shut_top_{s}", f"shut_bot_{s}"):
            pairs += [(sh_, I, b, I, f"s={s}") for b in static]
        pairs += [(f"shut_top_{s}", I, f"shut_bot_{s}", I, f"s={s}")]
    pairs += [("pinion", I, b, I, "") for b in static]
    ok &= check("shutters 0..1 : plates vs head internals", pairs)
    # F: firmware-accepted poses vs housing, tower, wall, and the arm itself
    _cache["wall"] = [trimesh.creation.box(extents=[2000, 20, 2000], transform=tr(0, -10, 0))]
    accepted = rejected = 0
    pairs = []
    for yw, sh, el, pt in itertools.product(range(5, 176, 17), range(-20, 76, 19), range(-110, 41, 25), (-30, 0, 30)):
        p = dict(yaw=yw, shoulder=sh, elbow=el, pitch=pt, shutter=1.0)
        if not fw.workspace_ok(p):
            rejected += 1
            continue
        accepted += 1
        t = fw.tilt_of(p)
        tag = f"yaw={yw} sh={sh} el={el} pitch={pt}"
        pairs += [(a, T_h(yw, sh, el, t), b, I, tag) for a in HEAD for b in WORLD + ["wall"]]
        pairs += [(a, T_h(yw, sh, el, t), b, T_l1(yw, sh), tag) for a in ("head_top", "head_mid", "head_chin") for b in LINK1]
        pairs += [(a, T_h(yw, sh, el, t), b, T_t(yw), tag) for a in ("head_top", "head_mid", "head_chin") for b in TURRET]
        pairs += [(a, T_l2(yw, sh, el), b, I, tag) for a in LINK2 for b in WORLD + ["wall"]]
        pairs += [(a, T_l1(yw, sh), b, I, tag) for a in LINK1 for b in WORLD + ["wall"]]
    print(f"firmware workspace: {accepted} poses accepted, {rejected} rejected (yaw/shoulder/elbow/pitch grid)")
    ok &= check("accepted poses : arm/head vs housing, tower, wall, arm", pairs)
    print("\nALL CLEAR" if ok else "\nINTERFERENCE FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
