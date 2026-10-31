"""Dimensioned placement drawings + tables for the manual: where each part sits inside the v12s box and where the
drop-in T-nuts go along each rail.  All numbers come from the built model.  Run: .venv/bin/python placement.py v12s"""
import os, sys, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import cage

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "manual", "img")
asm = cage.build()
bb = {}
for ch in asm.children:
    b = ch.obj.val().BoundingBox()
    bb[ch.name] = (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)
B, C = cage.B, cage.C
X0, Y0 = cage.x_in0, cage.y_in0                       # inner faces of the back width rail and the outboard depth rail
XF, YI = cage.out_D - B, cage.out_W - B               # inner faces of the front width rail and the inboard depth rail
fx = lambda x: x - X0                                 # measured from the back rail's inner face
fy = lambda y: y - Y0                                 # measured from the outboard rail's inner face

# --- bolt positions (same formulas as cage.build_v13) -------------------------------------------------------------
b = cage.COMPONENTS["battery"]; wall, clr = 6.0, cage.P.get("tray_clr", 1.0)
fd = b.d + 2 * wall + 2 * clr; fw = cage.COMPONENTS["smart200"].w + 2 * wall + 3.0
txs = (X0, cage.out_D - B - fd); ty = Y0 + 1                    # trays butt the width rails (2026-10-25)
nuts = {}
nuts["bottom outboard depth rail (trays' outer walls)"] = sorted(fx(tx + h) for tx in txs for h in (70, fd - 70))
nuts["top outboard depth rail (drop-shelf hangers)"] = sorted(fx(tx + wall + clr + (b.d - 130) / 2 + h) for tx in txs for h in (25, 105))
yt = cage.V13["plate_y"] + cage.P["card_t"] / 2 + cage.P["post_w"] / 2
nuts["bottom back width rail (post 0 sill; tray 0 end wall; bus shelf back wall)"] = sorted([fy(yt - 12), fy(ty + 28), fy(ty + fw - 28), fy(ty + fw + 30), fy(cage.V13["plate_y"] - 40)])
nuts["bottom front width rail (post 1 sill; tray 1 end wall; bus shelf front wall)"] = sorted([fy(yt - 12), fy(ty + 28), fy(ty + fw - 28), fy(ty + fw + 30), fy(cage.V13["plate_y"] - 40)])
nuts["top inboard depth rail (Garmin hanger)"] = sorted([fx(cage.out_D - 25.0 - 55.0 - 20.0 - 130.0 + 25.0), fx(cage.out_D - 25.0 - 55.0 - 20.0 - 130.0 + 130.0 - 25.0)])
nuts["top back width rail (clip 0)"] = [fy(yt - 2)]
nuts["top front width rail (clip 1)"] = [fy(yt - 2)]

parts = [  # (label, name)
    ("Tray 0 (back)", "print_tray_battery_0"), ("Tray 1 (front)", "print_tray_battery_1"),
    ("Post 0 (back)", "print_post_inverter_0"), ("Post 1 (front)", "print_post_inverter_1"),
    ("Drop shelf 0", "print_breaker_shelf_0"), ("Drop shelf 1", "print_breaker_shelf_1"),
    ("Bus shelf plate 0", "print_bus_shelf_0"), ("Bus shelf plate 1", "print_bus_shelf_1"), ("Bus shelf plate 2", "print_bus_shelf_2"),
    ("Inverter plate (all tiles)", "print_plate_inverter_tile_00"), ("MultiPlus", "victron_multiplus_long"),
]
rows = []
for label, nm in parts:
    x0, x1, y0, y1, z0, z1 = bb[nm]
    if label.startswith("Inverter plate"):
        xs = [bb[n] for n in bb if n.startswith("print_plate_inverter_tile")]
        x0, x1 = min(v[0] for v in xs), max(v[1] for v in xs); z0, z1 = min(v[4] for v in xs), max(v[5] for v in xs)
    rows.append((label, fx(x0), fx(x1), fy(y0), fy(y1), z0, z1))
json.dump({"nuts": nuts, "parts": rows, "refs": {"X0": X0, "Y0": Y0, "XF": XF, "YI": YI}}, open(os.path.join(OUT, "placement.json"), "w"), indent=1)

# --- plan drawing ------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(13, 9), dpi=120)
ax.set_aspect("equal"); ax.axis("off")
D, W = cage.out_D, cage.out_W
for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):   # rails
    ax.add_patch(Rectangle((x, y), w, h, fc="#c8ccd2", ec="#777", lw=0.8))
cols = {"print_tray_battery": "#e8b89a", "print_post_inverter": "#d9541f",
        "print_breaker_shelf": "#f0c9a8", "print_bus_shelf": "#e8b89a", "print_plate_inverter_tile": "#9a3a0f", "victron_multiplus": "#9bbcf0", "battery_": "#6fa3ec"}
for nm, (x0, x1, y0, y1, z0, z1) in bb.items():
    key = next((k for k in cols if nm.startswith(k)), None)
    if key is None:
        continue
    alpha = 0.55 if key in ("print_breaker_shelf",) else 0.9
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=cols[key], ec="#333", lw=0.6, alpha=alpha))
def dim(ax, x0, x1, y, text, above=True):
    ax.annotate("", xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle="<->", lw=0.8, color="#222"))
    ax.text((x0 + x1) / 2, y + (6 if above else -14), text, ha="center", fontsize=7.5, color="#222")
def vdim(ax, x, y0, y1, text, left=True):
    ax.annotate("", xy=(x, y0), xytext=(x, y1), arrowprops=dict(arrowstyle="<->", lw=0.8, color="#222"))
    ax.text(x + (-6 if left else 6), (y0 + y1) / 2, text, ha="right" if left else "left", va="center", fontsize=7.5, color="#222", rotation=90)
# T-nut marks and their positions along each rail
for lbl, ys, xs_, rail_y in (("bottom", None, nuts["bottom outboard depth rail (trays' outer walls)"], B / 2),):
    for x in xs_:
        ax.plot(X0 + x, rail_y, marker="v", color="#1a4fb3", ms=6)
        ax.text(X0 + x, -12, f"{x:.0f}", ha="center", fontsize=7, color="#1a4fb3")
for x in nuts["top outboard depth rail (drop-shelf hangers)"]:
    ax.plot(X0 + x, B / 2 + 8, marker="^", color="#b31a1a", ms=6)
    ax.text(X0 + x, -26, f"{x:.0f}", ha="center", fontsize=7, color="#b31a1a")
for x in nuts["top inboard depth rail (Garmin hanger)"]:
    ax.plot(X0 + x, W - B / 2 - 8, marker="v", color="#b31a1a", ms=6)
    ax.text(X0 + x, W + 2, f"{x:.0f}", ha="center", fontsize=7, color="#b31a1a")
for y in nuts["bottom back width rail (post 0 sill; tray 0 end wall; bus shelf back wall)"]:
    ax.plot(B / 2, Y0 + y, marker=">", color="#1a4fb3", ms=6); ax.text(-14, Y0 + y, f"{y:.0f}", ha="right", va="center", fontsize=7, color="#1a4fb3")
for y in nuts["bottom front width rail (post 1 sill; tray 1 end wall; bus shelf front wall)"]:
    ax.plot(D - B / 2, Y0 + y, marker="<", color="#1a4fb3", ms=6); ax.text(D + 14, Y0 + y, f"{y:.0f}", ha="left", va="center", fontsize=7, color="#1a4fb3")
ax.text(D / 2, W + 34, "v12s placement, plan view (lid off). Rails grey; blue arrows = drop-in T-nut positions in the BOTTOM rails' inner slots, red = TOP rails (outboard: drop-shelf hangers; inboard: the Garmin hanger).\n"
        "Depth positions are measured from the back rail's inner face, width positions from the outboard rail's inner face (both at 0 on their rail).",
        ha="center", va="bottom", fontsize=8.5)
ax.text(-8, W / 2, "BACK (against the main IceBox)", rotation=90, ha="right", va="center", fontsize=9, color="#444")
ax.text(D + 8, W / 2, "FRONT (ports)", rotation=90, ha="left", va="center", fontsize=9, color="#444")
ax.text(D / 2, -40, "OUTBOARD side (batteries)", ha="center", fontsize=9, color="#444")
ax.text(D / 2, W + 14, "INBOARD side (inverter)", ha="center", fontsize=9, color="#444")
tx0, tx1 = txs
dim(ax, X0, tx0 - 6, Y0 + fw + 14, f"{fx(tx0) - 6:.0f}")
dim(ax, tx1 + fd + 6, XF, Y0 + fw + 14, f"{XF - (tx1 + fd + 6):.0f}")
vdim(ax, X0 + 20, Y0, Y0 + 1 + fw, f"tray {fw:.0f} wide, 1 off the rail", left=False)
vdim(ax, X0 + 20, Y0 + 1 + fw, cage.V13["plate_y"], f"column {cage.V13['plate_y'] - (Y0 + 1 + fw):.0f}", left=False)
vdim(ax, X0 + 20, cage.V13["plate_y"] + 6, YI, f"plate to inboard rail {YI - cage.V13['plate_y'] - 6:.0f}", left=False)
ax.set_xlim(-60, D + 60); ax.set_ylim(-60, W + 70)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "placement-plan.png"), facecolor="white"); plt.close(fig)
print("wrote placement-plan.png")
print(json.dumps(nuts, indent=1))
for r in rows:
    print(f"{r[0]:28s} depth {r[1]:6.1f}..{r[2]:6.1f}  width {r[3]:6.1f}..{r[4]:6.1f}  height {r[5]:5.1f}..{r[6]:5.1f}")
