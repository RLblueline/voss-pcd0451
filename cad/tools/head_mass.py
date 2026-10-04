"""Head mass and centre of gravity in the tilt-axis frame (for choosing HS and checking torques)."""
import warnings
from pathlib import Path
import numpy as np, trimesh
warnings.filterwarnings("ignore")
STL = Path(__file__).resolve().parent.parent / "stl"
RHO = 1.24e-3   # PLA g/mm3
PARTS = {"head_top": 0.9, "head_mid": 0.9, "head_chin": 0.9, "ears": 0.9, "eye_plate": 0.9, "eye_rods": 0.9,
         "carriage_0": 0.8, "shut_top_0_1": 1.0, "shut_bot_0_1": 1.0, "leds": 1.0, "paper": 0.5}
FIXED = {"lift_sg90": 9.0, "pinion_0": 1.0, "lift_pinion": 2.0}


def mass_props():
    tot, mom = 0.0, np.zeros(3)
    for n, f in PARTS.items():
        m = trimesh.load(STL / f"{n}.stl", force="mesh")
        g = m.volume * RHO * f
        c = m.center_mass if m.is_volume else m.bounds.mean(0)
        tot += g; mom += g * c
    for n, g in FIXED.items():
        c = trimesh.load(STL / f"{n}.stl", force="mesh").bounds.mean(0)
        tot += g; mom += g * c
    extra = 30.0                         # wiring, LED ring, screws, inserts
    tot += extra; mom += extra * np.array([0, 0, -120])
    return tot, mom / tot


if __name__ == "__main__":
    m, c = mass_props()
    print(f"head mass ~{m:.0f} g, CG (tilt-axis frame) x={c[0]:.1f} y={c[1]:.1f} z={c[2]:.1f} mm")
