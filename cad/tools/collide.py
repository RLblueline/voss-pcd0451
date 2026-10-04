"""Sweep every joint through its limits and report part-part interference.

Uses the STLs from tools/export.sh (each in its local frame) and the same transforms as
assembly.scad. Also checks that every pose the firmware's workspace check accepts is
collision-free against the housing and wall.

    python3 tools/collide.py            (from cad/, after ./tools/export.sh)
"""
import itertools
import warnings
warnings.filterwarnings("ignore")
import math
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
STL = HERE.parent / "stl"
sys.path.insert(0, str(HERE.parent.parent))
import os  # noqa: E402
os.environ.setdefault("MEMO_SIM", "1")
from memo import body as fw  # noqa: E402

SY, L1, L2, TILT_OFF, ZT = 108, 120, 100, 14, -184
TOL = 1.0   # mm^3 of overlap tolerated (coplanar contact faces)

WORLD = ["housing", "back_plate", "bracket", "s1_body"]
LINK1 = ["link1", "hanger", "s2_body", "s1_horn"]
LINK2 = ["link2", "post", "s3_body", "s2_horn"]
HEAD = ["head_top", "head_mid", "head_chin", "ears", "cartridge", "sg90", "leds", "bumper", "paper", "s3_horn"]

_cache = {}


def mesh(name):
    if name not in _cache:
        m = trimesh.load(STL / f"{name}.stl", force="mesh")
        m.merge_vertices()
        _cache[name] = m
    return _cache[name]


def tr(x, y, z):
    return trimesh.transformations.translation_matrix([x, y, z])


def rz(a):
    return trimesh.transformations.rotation_matrix(math.radians(a), [0, 0, 1])


def ry(a):
    return trimesh.transformations.rotation_matrix(math.radians(a), [0, 1, 0])


def T_l1(sh):
    return tr(0, SY, 0) @ rz(sh)


def T_l2(sh, el):
    return T_l1(sh) @ tr(L1, 0, 0) @ rz(el)


def T_h(sh, el, t):
    return T_l2(sh, el) @ tr(L2 + TILT_OFF, 0, ZT) @ ry(t)


def overlap(a, Ta, b, Tb):
    A = mesh(a).copy().apply_transform(Ta)
    B = mesh(b).copy().apply_transform(Tb)
    lo = np.maximum(A.bounds[0], B.bounds[0])
    hi = np.minimum(A.bounds[1], B.bounds[1])
    if np.any(hi <= lo):
        return 0.0
    try:
        r = trimesh.boolean.intersection([A, B], engine="manifold")
        return float(r.volume) if r is not None and not r.is_empty else 0.0
    except Exception as e:  # pragma: no cover
        print("  boolean failed", a, b, e)
        return -1.0


def check(label, pairs):
    worst = []
    for a, Ta, b, Tb, tag in pairs:
        v = overlap(a, Ta, b, Tb)
        if v > TOL or v < 0:
            worst.append((v, a, b, tag))
    status = "OK" if not worst else f"{len(worst)} HITS"
    print(f"{label:<44} {status}")
    for v, a, b, tag in sorted(worst, reverse=True)[:12]:
        print(f"    {a} x {b} @ {tag}: {v:.1f} mm^3")
    return not worst


def main():
    ok = True
    I = np.eye(4)
    # A: shoulder sweep
    pairs = [(a, T_l1(sh), b, I, f"sh={sh}") for sh in range(5, 176, 5) for a in LINK1 for b in WORLD]
    ok &= check("shoulder 5..175 : link1 vs housing/bracket", pairs)
    # B: elbow sweep (link2 + head vs link1)
    pairs = [(a, T_l2(90, el), b, T_l1(90), f"el={el}") for el in range(-50, 126, 5) for a in LINK2 for b in LINK1]
    pairs += [(a, T_h(90, el, t), b, T_l1(90), f"el={el} t={t}") for el in range(-50, 126, 25) for t in (-35, 40)
              for a in HEAD for b in LINK1]
    ok &= check("elbow -50..125 : link2/head vs link1", pairs)
    # C: tilt sweep, shutters open and closed
    head_s = lambda s: HEAD + [f"shut_top_{s}", f"shut_bot_{s}", "pinion"]
    pairs = [(a, T_h(90, 0, t), b, T_l2(90, 0), f"t={t} s={s}") for t in range(-35, 41, 5) for s in (0, 1)
             for a in head_s(s) for b in LINK2]
    ok &= check("tilt -35..40 : head vs link2/post", pairs)
    # D: shutters vs head internals (pinion/rack mesh excluded)
    static = [h for h in HEAD if h != "s3_horn"]
    pairs = []
    for s in ("0", "0.5", "1"):
        for sh_ in (f"shut_top_{s}", f"shut_bot_{s}"):
            pairs += [(sh_, I, b, I, f"s={s}") for b in static]
        pairs += [(f"shut_top_{s}", I, f"shut_bot_{s}", I, f"s={s}")]
    pairs += [("pinion", I, b, I, "") for b in static]
    ok &= check("shutters 0..1 : plates vs head internals", pairs)
    # E: every firmware-accepted arm pose is clear of housing/wall
    accepted = rejected = 0
    pairs = []
    for sh, el in itertools.product(range(5, 176, 10), range(-50, 126, 15)):
        if not fw.workspace_ok(sh, el):
            rejected += 1
            continue
        accepted += 1
        for t in (-35, 0, 40):
            pairs += [(a, T_h(sh, el, t), b, I, f"sh={sh} el={el} t={t}") for a in HEAD for b in WORLD]
        pairs += [(a, T_l2(sh, el), b, I, f"sh={sh} el={el}") for a in LINK2 for b in WORLD]
    wall = trimesh.creation.box(extents=[2000, 20, 2000], transform=tr(0, -10, 0))
    _cache["wall"] = wall
    for sh, el in itertools.product(range(5, 176, 10), range(-50, 126, 15)):
        if fw.workspace_ok(sh, el):
            pairs += [(a, T_h(sh, el, 0), "wall", I, f"sh={sh} el={el}") for a in ("head_top", "head_mid", "head_chin")]
    print(f"firmware workspace: {accepted} poses accepted, {rejected} rejected (grid 10 x 15 deg)")
    ok &= check("accepted poses : arm/head vs housing + wall", pairs)
    print("\nALL CLEAR" if ok else "\nINTERFERENCE FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
