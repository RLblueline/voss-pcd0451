"""V.O.S.S. expression library: easing styles, gestures and mood profiles.

Gestures are data. Each step moves some joints, either to absolute values ("to") or by an
offset from the gesture's anchor pose ("rel"), over t seconds with an easing style, then
holds. Animation principles applied: anticipation (a small counter-move first), overshoot
and settle ("spring"), fast-in/slow-out snaps, slow sighs, holds, and secondary motion
(eye and lids lead or trail the head).
"""
import math

# ---------------------------------------------------------------- easing styles
_Z, _W = 0.55, 13.0                      # spring: damping ratio, natural frequency (per move)
_WD = _W * math.sqrt(1 - _Z * _Z)


def curve(style, a):
    """Progress 0..1 (spring overshoots ~12% and settles) for normalised time a in 0..1."""
    a = max(0.0, min(1.0, a))
    if style == "snap":                  # fast start, gentle stop
        return 1 - (1 - a) ** 3
    if style == "slow":                  # sigh-like, symmetric
        return 0.5 - 0.5 * math.cos(math.pi * a)
    if style == "spring":                # overshoot and settle
        e = 1 - math.exp(-_Z * _W * a) * (math.cos(_WD * a) + _Z / math.sqrt(1 - _Z * _Z) * math.sin(_WD * a))
        if a > 0.85:
            k = (a - 0.85) / 0.15
            e = e * (1 - k) + k
        return e
    return a * a * a * (a * (6 * a - 15) + 10)      # "ease" / "hold": minimum jerk


def S(rel=None, to=None, t=0.4, style="ease", hold=0.0):
    return {"rel": rel or {}, "to": to or {}, "t": t, "style": style, "hold": hold}


# ---------------------------------------------------------------- gestures
GESTURES = {
    # small acknowledgment
    "ack": [S({"pitch": 6}, t=0.22, style="snap"), S({"pitch": 0}, t=0.45, style="spring")],
    "nod": [S({"pitch": 14, "eye": 0.25}, t=0.25, style="snap"),
            S({"pitch": -2}, t=0.3),
            S({"pitch": 0, "eye": 0}, t=0.4, style="spring")],
    # happy: dip (anticipation), pop up, nod, settle
    "bounce_nod": [S({"shoulder": -3, "elbow": 3}, t=0.15),
                   S({"shoulder": 6, "elbow": -6, "pitch": -4, "eye": 0.3}, t=0.22, style="snap"),
                   S({"shoulder": 0, "elbow": 0, "pitch": 12, "eye": 0.2}, t=0.25),
                   S({"pitch": 0, "eye": 0.1}, t=0.45, style="spring")],
    "shake": [S({"yaw": -9}, t=0.18, style="snap"), S({"yaw": 9}, t=0.26), S({"yaw": -6}, t=0.24),
              S({"yaw": 0}, t=0.4, style="spring")],
    # suspicious: tiny lift, then a slow lean in, low and squinting
    "peer": [S({"pitch": -3}, t=0.2),
             S({"shoulder": -7, "elbow": 9, "pitch": 10, "eye": -0.5, "shutter": -0.6}, t=1.0, style="slow", hold=0.9)],
    "double_take": [S({"yaw": 22, "eye": 0.1}, t=0.55, hold=0.35),
                    S({"yaw": 0, "pitch": -6, "eye": 0.45}, t=0.16, style="snap", hold=0.3),
                    S({"pitch": 0, "eye": 0.15}, t=0.5, style="spring")],
    "startle": [S({"shoulder": 12, "elbow": -12, "pitch": -12, "eye": 0.5}, t=0.14, style="snap", hold=0.35),
                S({"shoulder": 0, "elbow": 0, "pitch": 0, "eye": 0}, t=1.0, style="slow")],
    "sigh": [S({"shoulder": -7, "elbow": 7, "pitch": 9, "eye": -0.3, "shutter": -0.45}, t=1.3, style="slow", hold=0.4),
             S({"shoulder": 0, "elbow": 0, "pitch": 0, "eye": 0, "shutter": 0}, t=1.1, style="slow")],
    "scan": [S({"yaw": -20, "eye": 0.2}, t=0.8, hold=0.15), S({"yaw": 20, "eye": -0.1}, t=1.3, hold=0.15),
             S({"yaw": 0, "eye": 0}, t=0.7, style="spring")],
    "curious": [S({"pitch": -9, "eye": 0.45, "yaw": 6, "shoulder": 4, "elbow": -4}, t=0.6, style="spring", hold=0.6),
                S({"pitch": -3, "eye": 0.2, "yaw": 3}, t=0.6)],
    # infraction: dip, loom and squint, hold, drop ~80 mm with a nose-down snap, settle
    "stamp": [S({"shoulder": -3, "pitch": -4}, t=0.22),
              S({"shoulder": 15, "elbow": -15, "pitch": 10, "eye": -0.4, "shutter": -0.75}, t=0.9, style="slow", hold=0.35),
              S({"shoulder": -25, "elbow": 25, "pitch": 15}, t=0.22, style="snap", hold=0.45),
              S({"shoulder": -5, "elbow": 5, "pitch": 8, "eye": -0.2, "shutter": -0.4}, t=0.8, style="spring")],
    # sulk secondary action: stays turned away, then a quick resentful glance back
    "glance_back": [S({}, t=0.0, hold=2.2),
                    S({"yaw": -28, "eye": 0.25, "shutter": 0.3}, t=0.35, style="snap", hold=0.6),
                    S({"yaw": 0, "eye": 0, "shutter": 0}, t=0.5)],
    "flutter": [S({"shutter": -0.65}, t=0.06, style="snap"), S({"shutter": 0}, t=0.06)] * 3,
}

# gestures Claude may request with a second tag, e.g. "[infraction] [peer] ..."
CLAUDE_GESTURES = ("nod", "shake", "peer", "double_take", "startle", "sigh", "scan", "curious")

# ---------------------------------------------------------------- moods
# entry pose (absolute joints, seconds, style), then the default gesture
MOOD_ENTRY = {
    "neutral": ({"pitch": 0.0, "shutter": 1.0, "eye": 0.0}, 0.6, "ease"),
    "approve": ({"shutter": 1.0, "eye": 0.15}, 0.3, "ease"),
    "infraction": ({"shoulder": 20.0, "elbow": -20.0, "pitch": 0.0, "shutter": 1.0}, 0.5, "ease"),
    "concern": ({"shoulder": 8.0, "elbow": -10.0, "pitch": -3.0, "shutter": 1.0, "eye": 0.0}, 1.4, "slow"),
    "sulk": ({"yaw": 145.0, "shoulder": 30.0, "elbow": -30.0, "pitch": 15.0, "shutter": 0.45, "eye": -0.6}, 1.3, "spring"),
}
MOOD_GESTURE = {"neutral": "ack", "approve": "bounce_nod", "infraction": "stamp", "concern": None, "sulk": "glance_back"}

# idle character per mood: sway amplitude, sway speed, blink rate (relative)
MOOD_IDLE = {
    "neutral": {"amp": 1.0, "speed": 1.0, "blink": 1.0},
    "approve": {"amp": 1.3, "speed": 1.25, "blink": 1.3},
    "infraction": {"amp": 0.45, "speed": 0.7, "blink": 0.35},   # still, staring
    "concern": {"amp": 0.5, "speed": 0.6, "blink": 0.8},        # calm, slow
    "sulk": {"amp": 0.7, "speed": 0.8, "blink": 0.6},
}
