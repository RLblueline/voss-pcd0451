"""Static joint torques over the arm's range and the best desk-lamp spring for the shoulder.

    python3 tools/loads.py        (from cad/, after ./tools/export.sh)
"""
import sys, warnings
from pathlib import Path
import numpy as np, trimesh
warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import collide as c          # noqa: E402
import head_mass             # noqa: E402

STL = HERE.parent / "stl"
RHO = 1.24e-3
SPR_A, SPR_B = 96.0, 50.0
KGCM = 0.0980665             # N*m per kg*cm


def part(n, fill):
    m = trimesh.load(STL / f"{n}.stl", force="mesh")
    return m.volume * RHO * fill, (m.center_mass if m.is_volume else m.bounds.mean(0))


def masses():
    link1 = [part("link1", 0.55), part("cover1", 0.9), (60.0, trimesh.load(STL / "el_body.stl").bounds.mean(0)), (15.0, np.array([55.0, 0, 16]))]
    link2 = [part("link2", 0.55), part("post", 0.7), part("cover2", 0.9), (60.0, trimesh.load(STL / "tl_body.stl").bounds.mean(0)), (12.0, np.array([70.0, 0, 16]))]
    hm, hc = head_mass.mass_props()
    return link1, link2, [(hm, hc)]


def torques(sh, el, M):
    l1, l2, hd = M
    T1, T2, Th = c.T_l1(90, sh), c.T_l2(90, sh, el), c.T_h(90, sh, el, sh + el)
    pts = [(g, (T1 @ np.r_[p, 1])[:3]) for g, p in l1] + [(g, (T2 @ np.r_[p, 1])[:3]) for g, p in l2] + \
          [(g, (Th @ np.r_[p, 1])[:3]) for g, p in hd]
    e = (T1 @ np.r_[c.L1, 0, 0, 1])[:3]
    ts = sum(g * 9.81e-3 * (p[1] - c.SY) for g, p in pts) / 1000 / KGCM
    n1 = len(l1)
    te = sum(g * 9.81e-3 * (p[1] - e[1]) for g, p in pts[n1:]) / 1000 / KGCM
    return ts, te


def main():
    M = masses()
    th = np.arange(-20, 76, 1.0)
    g = np.array([torques(t, -t, M)[0] for t in th])
    e = np.array([torques(t, -t, M)[1] for t in th])
    best = min(((K, np.abs(g - K * np.cos(np.radians(th))).max()) for K in np.arange(5, 40, 0.05)), key=lambda x: x[1])
    K, resid = best
    r = g - K * np.cos(np.radians(th))
    eq = th[np.argmin(np.abs(r))]
    k = K * KGCM / (SPR_A * SPR_B * 1e-6) / 1000
    pq = lambda t: np.sqrt(SPR_A ** 2 + SPR_B ** 2 - 2 * SPR_A * SPR_B * np.sin(np.radians(t)))
    print(f"head {M[2][0][0]:.0f} g")
    print("shoulder (deg)  gravity  with spring   elbow   (kg*cm, link2 level)")
    for t in (-20, 0, 20, 45, 60, 75):
        i = int(t + 20)
        print(f"  {t:4d}         {g[i]:6.1f}     {r[i]:+6.1f}     {e[i]:5.1f}")
    print(f"spring: K = k*a*b = {K:.1f} kg*cm -> k = {k:.3f} N/mm (a={SPR_A:.0f}, b={SPR_B:.0f}); residual <= {resid:.1f} kg*cm;"
          f" unpowered balance ~{eq:.0f} deg; cable span {pq(75):.0f}..{pq(-20):.0f} mm; cable tension {k*pq(75):.0f}..{k*pq(-20):.0f} N")
    print(f"2:1 reeved spring: rate {4 * k:.2f} N/mm, travel {(pq(-20) - pq(75)) / 2:.0f} mm, force up to {2 * k * pq(-20):.0f} N")


if __name__ == "__main__":
    main()
