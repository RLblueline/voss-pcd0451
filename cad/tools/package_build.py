"""Assemble build/: print files for JLC3DP (or any print service / home printer), the order sheet,
and the purchasing BOM.   python3 cad/tools/package_build.py   (after cad/tools/export.sh)"""
import csv, shutil, warnings
from pathlib import Path
import trimesh
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
STL, OUT = ROOT / "cad" / "stl", ROOT / "build"
PR = OUT / "print_files"

MJF, RES, TPU = "MJF PA12 nylon", "SLA resin (standard)", "TPU (FDM) - see note"
# (stl, output name, qty, process, colour / finish, notes)
PARTS = [
    ("housing", "01_housing", 1, MJF, "any; paint corporate beige", "Largest part (144 x 70 x 226). Front lettering engraved 0.6 mm"),
    ("back_plate", "02_back_plate", 1, MJF, "any", "Keyholes for one stud; 4 M3 heat-set inserts in the edges"),
    ("tower", "03_yaw_tower", 1, MJF, "any", "Two 608 pockets + MG996R mount"),
    ("turret", "04_turret_with_spring_mast", 1, MJF, "any; paint beige", "Carries the shoulder servo and the 2:1 spring mast"),
    ("link1", "05_link1", 1, MJF, "any; paint beige", "Includes the elbow bracket and the cable eye"),
    ("link2", "06_link2", 1, MJF, "any; paint beige", ""),
    ("post", "07_tilt_post", 1, MJF, "any", "Self-tap M3 x 2 into link2"),
    ("cover1", "08_cover_link1", 1, MJF, "any; paint beige", "Top-only arm cover"),
    ("cover2", "09_cover_link2", 1, MJF, "any; paint beige", "Top-only arm cover"),
    ("p_yaw_coupler", "10_yaw_coupler", 1, MJF, "any", "MG996R horn -> 8 mm shaft, M3 insert + set screw"),
    ("p_spring_block", "11_spring_block", 1, MJF, "any", "Rides on the spring; 7 mm pulley on an M3 axle"),
    ("p_pulley", "12_pulley_10mm", 1, RES, "any", "Or buy a 10 mm / M3 cable pulley"),
    ("p_pulley_small", "13_pulley_7mm", 1, RES, "any", "Or buy a 7 mm / M3 cable pulley"),
    ("p_head_top", "14_head_top_with_ears", 1, RES, "white; paint beige", "Crown + status windows + tilt ears; 4 M3 heat-set inserts in the seam bosses"),
    ("p_head_mid", "15_head_middle", 1, RES, "white; paint beige", "Eye recess; 4 inserts (bottom seam) + 6 wall holes for the rod bars"),
    ("p_head_chin", "16_head_chin", 1, RES, "white; paint beige", "Chin slot"),
    ("p_eye_plate", "17_eye_slot_plate", 1, RES, "black", "Glue to the back of the eye recess"),
    ("p_carriage", "18_eye_carriage", 1, RES, "black", "Mask, rear plate, rails, lens seat, SG90 mount, rod bushings, lift rack"),
    ("p_lid_top", "19_eyelid_top", 1, RES, "dark grey", "Involute rack, module 1"),
    ("p_lid_bottom", "20_eyelid_bottom", 1, RES, "dark grey", "Involute rack, module 1"),
    ("p_pinion18", "21_pinion_18T", 1, RES, "any (tough resin preferred)", "SG90 spline bore + M2 horn screw"),
    ("p_pinion36", "22_pinion_36T", 1, RES, "any (tough resin preferred)", "SG90 spline bore + M2 horn screw"),
    ("p_rod_bar_top", "23_rod_bar_top", 1, RES, "black", "2 M3 inserts in the ends"),
    ("p_rod_bar_bottom", "24_rod_bar_bottom_with_lift_mount", 1, RES, "black", "4 M3 inserts in the ends; lift SG90 mount"),
    ("p_lens", "25_eye_lens_dome", 1, "SLA clear resin", "clear; tint amber (or buy a 60 mm amber acrylic dome)", "60 mm dome, 8 mm high"),
    ("p_neck_boot", "26_neck_boot", 1, TPU, "black", "Flexible bellows"),
    ("p_bumper", "27_chin_bumper", 1, TPU, "black", ""),
]

BOM = [
    # (category, qty, item, spec, used for, approx USD)
    ("Electronics", 1, "Raspberry Pi Zero 2 W", "with soldered header", "brain", 15),
    ("Electronics", 1, "microSD card", "32 GB, A1", "OS", 7),
    ("Electronics", 2, "INMP441 I2S MEMS microphone", "breakout", "voice + direction of arrival", 6),
    ("Electronics", 1, "MAX98357A I2S amplifier", "breakout", "voice", 5),
    ("Electronics", 1, "Speaker", "40 mm, 4 ohm, 3 W", "voice", 3),
    ("Electronics", 1, "PCA9685 servo driver", "16 channel, OE pin broken out", "servos", 6),
    ("Electronics", 1, "WS2812B LED ring", "16 LEDs, 44 mm OD", "eye light", 5),
    ("Electronics", 3, "WS2812B single-LED boards", "~10 mm", "REC / AUD / OK", 4),
    ("Electronics", 1, "58 mm TTL thermal printer + paper", "ESC/POS, 9600 baud", "memos", 25),
    ("Electronics", 1, "Electrolytic capacitor", "1000 uF 10 V", "servo rail", 1),
    ("Electronics", 1, "Resistor", "330 ohm", "LED data line", 0),
    ("Electronics", 2, "DC barrel jack, panel mount", "5.5 x 2.1 mm", "power in", 2),
    ("Electronics", 1, "Level shifter (optional)", "74AHCT125", "only if LEDs glitch", 2),
    ("Power", 1, "5 V supply", "5 A", "Pi, amp, LEDs, printer", 12),
    ("Power", 1, "6 V supply", "6 A", "servo rail", 15),
    ("Servos", 1, "MG996R", "standard size, 180 deg", "base yaw", 6),
    ("Servos", 2, "DS3225", "25 kg-cm, standard size, 180 deg", "shoulder, elbow", 32),
    ("Servos", 1, "DS3218", "20 kg-cm, 180 deg", "head tilt", 14),
    ("Servos", 2, "SG90", "9 g, 180 deg", "eyelids, eye lift", 6),
    ("Motion", 2, "608 ball bearing", "8 x 22 x 7", "yaw shaft", 2),
    ("Motion", 3, "624 ball bearing", "4 x 13 x 5", "shoulder / elbow / tilt pivots", 2),
    ("Motion", 1, "Steel rod", "8 mm x 80 mm (cut)", "yaw shaft", 3),
    ("Motion", 2, "Steel rod", "3 mm x 148 mm (cut)", "eye carriage guides", 2),
    ("Counterbalance", 1, "Extension spring", "~2.1 N/mm, ~55 mm free length incl. hooks, OD <= 13 mm, >= 40 mm safe extension, >= 130 N max", "shoulder spring (2:1 reeved)", 4),
    ("Counterbalance", 1, "Braided steel cable", "1 mm, ~40 cm + 2 crimp sleeves", "spring cable", 3),
    ("Fasteners", 3, "M4 x 20 shoulder bolt + nyloc", "", "pitch pivots", 3),
    ("Fasteners", 1, "M3 screw assortment", "6-30 mm, button + socket head, nuts", "general; axles; tensioner", 6),
    ("Fasteners", 30, "M3 heat-set inserts", "M3 x 5.7 x 4.6", "covers, seams, rod bars, coupler, back plate", 4),
    ("Fasteners", 1, "M3 x 6 set screw", "", "yaw coupler", 0),
    ("Fasteners", 2, "#8 x 2 in wood screw", "", "wall stud", 1),
    ("Wiring", 1, "Servo extension leads + hookup wire", "22-26 AWG", "harness", 5),
    ("Wiring", 1, "Split-loom tubing + zip ties", "6-8 mm, ~1 m", "service tubes", 3),
    ("Finishing", 1, "Primer + beige / black paint, Dymo tape", "", "the look", 10),
]


def main():
    PR.mkdir(parents=True, exist_ok=True)
    for f in PR.glob("*.stl"):
        f.unlink()
    with open(OUT / "print_order_jlc3dp.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "qty", "process / material", "colour / finish", "size x mm", "size y mm", "size z mm", "volume cm3", "notes"])
        for src, name, q, proc, col, note in PARTS:
            m = trimesh.load(STL / f"{src}.stl", force="mesh")
            assert m.is_volume and len(m.split(only_watertight=False)) == 1, src
            shutil.copy(STL / f"{src}.stl", PR / f"{name}.stl")
            e = m.extents
            w.writerow([f"{name}.stl", q, proc, col, f"{e[0]:.1f}", f"{e[1]:.1f}", f"{e[2]:.1f}", f"{m.volume / 1000:.1f}", note])
    total = 0
    with open(OUT / "BOM.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["category", "qty", "item", "spec", "used for", "approx USD (line total)"])
        for row in BOM:
            w.writerow(row); total += row[-1]
        w.writerow(["", "", "TOTAL (purchased parts, excl. printing)", "", "", total])
    print(f"{len(PARTS)} print files -> {PR}\nBOM total ~${total} (excluding printing)")


if __name__ == "__main__":
    main()
