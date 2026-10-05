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
os.environ.setdefault("VOSS_SIM", "1")
from voss import body as fw  # noqa: E402

SY, L1, L2, TILT_OFF, TILT_DROP, ARM_Z0, HS = 112, 120, 100, 14, 72, 70, 15
PIN_Y, PIN_R, EYE_Z, LIFT_X, LIFT_R = 48, 9, -116, -19.25, 18
TOL = 1.0   # mm^3 of overlap tolerated (coplanar contact faces)

WORLD = ["housing", "back_plate", "tower", "yaw_body"]
TURRET = ["turret", "sh_body", "coupler"]
LINK1 = ["link1", "el_body", "sh_horn", "cover1"]
LINK2 = ["link2", "post", "tl_body", "el_horn", "cover2"]
HEAD_STATIC = ["head_top", "head_mid", "head_chin", "eye_plate", "eye_rods", "lift_sg90", "leds", "bumper", "paper"]   # head_top includes the ears
HEAD = HEAD_STATIC + ["s3_horn", "carriage_0"]
EYES = ("-1", "0", "1")
TILT_RANGE = (-40, 50)

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
    return tr(0, SY, ARM_Z0) @ rz(yaw)


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
        t = max(TILT_RANGE[0], min(TILT_RANGE[1], 20 + el))
        pairs += [(a, T_h(90, 20, el, t), b, T_l1(90, 20), f"el={el} t={t}") for a in HEAD for b in LINK1]
    ok &= check("elbow -110..40 : link2/head vs link1/turret", pairs)
    # D: tilt sweep, eye at its extremes, shutters open and closed
    head_s = lambda e, s: HEAD_STATIC + ["s3_horn", f"carriage_{e}", f"shut_top_{e}_{s}", f"shut_bot_{e}_{s}", f"pinion_{e}_{s}", f"lift_pinion_{e}"]
    pairs = [(a, T_h(90, 20, -20, t), b, T_l2(90, 20, -20), f"t={t} eye={e} s={s}") for t in range(TILT_RANGE[0], TILT_RANGE[1] + 1, 5)
             for e in ("-1", "1") for s in ("0", "1") for a in head_s(e, s) for b in LINK2]
    ok &= check(f"tilt {TILT_RANGE[0]}..{TILT_RANGE[1]} : head vs link2/post", pairs)
    # E: moving eye (carriage, eyelids, pinions) vs head internals; gear meshes excluded
    pairs = []
    for e in EYES:
        pairs += [(f"carriage_{e}", I, b, I, f"eye={e}") for b in HEAD_STATIC]
        pairs += [(f"lift_pinion_{e}", I, b, I, f"eye={e}") for b in HEAD_STATIC if b not in ("lift_sg90",)]
        for s in ("0", "0.5", "1"):
            pairs += [(f"pinion_{e}_{s}", I, b, I, f"eye={e} s={s}") for b in HEAD_STATIC]
            for sh_ in (f"shut_top_{e}_{s}", f"shut_bot_{e}_{s}"):
                pairs += [(sh_, I, b, I, f"eye={e} s={s}") for b in HEAD_STATIC + [f"carriage_{e}"]]
            pairs += [(f"shut_top_{e}_{s}", I, f"shut_bot_{e}_{s}", I, f"eye={e} s={s}")]
    ok &= check("eye -1..1, shutters 0..1 : vs head internals", pairs)
    # G: gear meshes. No interference across the travel, but turning a pinion half a tooth must
    # jam it against its rack (proves the teeth really engage).
    pairs, jam = [], []
    for e in EYES:
        z = EYE_Z + float(e) * 24
        for s in ("0", "0.5", "1"):
            pairs += [(f"pinion_{e}_{s}", I, f"shut_top_{e}_{s}", I, f"eye={e} s={s}"),
                      (f"pinion_{e}_{s}", I, f"shut_bot_{e}_{s}", I, f"eye={e} s={s}")]
            Rh = tr(0, PIN_Y, z) @ trimesh.transformations.rotation_matrix(math.radians(10), [1, 0, 0]) @ tr(0, -PIN_Y, -z)
            jam += [(f"pinion_{e}_{s}", Rh, f"shut_top_{e}_{s}", I), (f"pinion_{e}_{s}", Rh, f"shut_bot_{e}_{s}", I)]
        pairs += [(f"lift_pinion_{e}", I, f"carriage_{e}", I, f"eye={e}")]
        Rl = tr(LIFT_X + HS, 0, EYE_Z) @ trimesh.transformations.rotation_matrix(math.radians(5), [0, 1, 0]) @ tr(-LIFT_X - HS, 0, -EYE_Z)
        jam += [(f"lift_pinion_{e}", Rl, f"carriage_{e}", I)]
    ok &= check("gear meshes : pinions vs racks (no interference)", pairs)
    vols = [overlap(a, Ta, b, Tb) for a, Ta, b, Tb in jam]
    engaged = all(v > 2.0 for v in vols)
    print(f"{'gear meshes : half-tooth turn jams (engaged)':<50} {'OK' if engaged else 'NOT ENGAGED'}  (min {min(vols):.1f} mm^3)")
    ok &= engaged
    # F: firmware-accepted poses vs housing, tower, wall, and the arm itself
    _cache["wall"] = [trimesh.creation.box(extents=[2000, 20, 2000], transform=tr(0, -10, 0))]
    accepted = rejected = 0
    pairs = []
    for yw, sh, el, pt in itertools.product(range(5, 176, 17), range(-20, 76, 19), range(-110, 41, 25), (-40, -20, 0, 20, 45)):
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
