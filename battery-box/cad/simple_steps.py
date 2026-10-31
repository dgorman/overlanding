"""Visual, low-text product-manual diagrams for MANUAL.md (bench prep, heat-set inserts, sub-assemblies, and assembly steps).
All coordinates come directly from the built CAD model (cage.py).
Run: .venv/bin/python simple_steps.py v12s   (writes ../manual/img/)"""
import os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, FancyBboxPatch, Polygon
import cage

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "manual", "img")
os.makedirs(OUT, exist_ok=True)
asm = cage.build()
bb = {ch.name: ch.obj.val().BoundingBox() for ch in asm.children}
B, C, D, W, H = cage.B, cage.C, cage.out_D, cage.out_W, cage.out_H
X0, Y0 = cage.x_in0, cage.y_in0

ORANGE = "#e4601f"
ORANGE_LT = "#fbe3d4"
GREY = "#c9cdd3"
GREY_LT = "#eef0f3"
BLUE = "#1a4fb3"
BLUE_LT = "#dce7fa"
GREEN = "#1b7f37"
GREEN_LT = "#dafbe1"
RED = "#c92a2a"
RED_LT = "#ffe3e3"
GOLD = "#d99b00"
GOLD_LT = "#fff3bf"
DARK = "#1f2328"


def banner(fig, step_tag, title, subtitle, hw_items=()):
    """Draw a two-row product-manual header bar so titles and hardware pills never overlap."""
    ax_b = fig.add_axes([0.0, 0.885, 1.0, 0.115])
    ax_b.set_xlim(0, 100); ax_b.set_ylim(0, 10); ax_b.axis("off")
    ax_b.add_patch(Rectangle((0, 0), 100, 10, fc="#1f2328", ec="none"))
    ax_b.add_patch(FancyBboxPatch((1.2, 2.0), 10.5, 6.0, boxstyle="round,pad=0.3", fc=ORANGE, ec="none"))
    ax_b.text(6.45, 5.0, step_tag, color="white", fontsize=12.5, weight="bold", ha="center", va="center")
    # Row 1 (top): Title on left, Hardware Pills on right
    ax_b.text(13.2, 6.8, title, color="white", fontsize=13.5, weight="bold", ha="left", va="center")
    # Row 2 (bottom): Subtitle across bottom
    ax_b.text(13.2, 2.4, subtitle, color="#cfd6e0", fontsize=9.2, ha="left", va="center")
    x_right = 99.0
    for text, bg, fg in reversed(hw_items):
        w_pill = max(10.0, len(text) * 0.42 + 1.8)
        x_left = x_right - w_pill
        ax_b.add_patch(FancyBboxPatch((x_left, 5.1), w_pill, 3.6, boxstyle="round,pad=0.22", fc=bg, ec="white", lw=0.8))
        ax_b.text(x_left + w_pill / 2, 6.9, text, color=fg, fontsize=8.2, weight="bold", ha="center", va="center")
        x_right = x_left - 0.8


def callout(ax, xy, xytext, text, color=DARK, bg="#fff8e7", ec=ORANGE, fs=9.2, weight="bold"):
    ax.annotate(
        text, xy=xy, xytext=xytext, fontsize=fs, weight=weight, color=color, ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.35", fc=bg, ec=ec, lw=1.4),
        arrowprops=dict(arrowstyle="-|>", lw=1.5, color=ec, shrinkA=0, shrinkB=3)
    )


def arrow(ax, p0, p1, text, offset=(0, 0), fs=11, color="#111"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="<|-|>", mutation_scale=14, lw=1.5, color=color))
    if text:
        ax.text((p0[0] + p1[0]) / 2 + offset[0], (p0[1] + p1[1]) / 2 + offset[1], text,
                ha="center", va="center", fontsize=fs, weight="bold", color=color,
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none", alpha=0.92))


def plan(ax, new_re, old_res=()):
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY, ec="#666", lw=1))
    for nm, b in bb.items():
        if nm.startswith("icebox_"):
            continue
        if re.match(new_re, nm):
            ax.add_patch(Rectangle((b.xmin, b.ymin), b.xlen, b.ylen, fc=ORANGE, ec="#7a2d08", lw=1.2))
        elif any(re.match(r, nm) for r in old_res):
            ax.add_patch(Rectangle((b.xmin, b.ymin), b.xlen, b.ylen, fc="#e9e9e9", ec="#aaa", lw=0.8))
    ax.text(-12, W / 2, "BACK\n(against\nIceBox)", rotation=90, ha="right", va="center", fontsize=10, weight="bold", color="#333")
    ax.text(D + 12, W / 2, "FRONT\n(ports)", rotation=270, ha="left", va="center", fontsize=10, weight="bold", color="#333")
    ax.text(D / 2, -16, "OUTBOARD SIDE (Batteries)", ha="center", va="top", fontsize=10, weight="bold", color="#333")
    ax.text(D / 2, W + 14, "INBOARD SIDE (MultiPlus Inverter)", ha="center", va="bottom", fontsize=10, weight="bold", color="#333")
    ax.set_xlim(-75, D + 75); ax.set_ylim(-65, W + 65)


# =====================================================================================================================
# BENCH 1: RAIL CUTS & PANEL PORT CUTOUT TEMPLATES
# =====================================================================================================================
def bench_01_rails_panels():
    fig = plt.figure(figsize=(15, 9.5), dpi=120)
    banner(fig, "BENCH 1", "Cut & Tap Rails + Cut Panels & Port Holes",
           "Do all saw cuts and 1/4\"-20 tapping on the bench before assembling the frame.",
           [("Tool: print_tool_tap_guide", ORANGE_LT, DARK), ("Tap: 1/4\"-20 + Cutting Oil", BLUE_LT, BLUE)])

    # Top-left: Rail Cut Schedule visual bars
    ax1 = fig.add_axes([0.03, 0.50, 0.54, 0.35])
    ax1.set_xlim(0, 680); ax1.set_ylim(0, 115); ax1.axis("off")
    ax1.text(0, 106, "① Cut & Tap the Aluminum Rails (Cut ONE End Only, Keep Factory Threads on Other End)",
             fontsize=10.8, weight="bold", color=DARK)

    # Width rails
    w_len = 436.6 * 0.68
    ax1.add_patch(Rectangle((10, 72), w_len, 18, fc=GREY, ec="#444", lw=1.2))
    ax1.text(18, 81, "4 × WIDTH RAILS: 436.6 mm (17.19\") — DO NOT CUT", fontsize=9, weight="bold", va="center")
    ax1.text(10 + w_len + 10, 81, "3 from donor + 1 Mod Kit bar (factory tapped)", fontsize=8.8, color="#444", weight="bold", va="center")

    # Depth rails
    full_d = 584.2 * 0.68; cut_d = 520.0 * 0.68
    ax1.add_patch(Rectangle((10, 40), cut_d, 18, fc="#9ec5fe", ec=BLUE, lw=1.4))
    ax1.add_patch(Rectangle((10 + cut_d, 40), full_d - cut_d, 18, fc=RED_LT, ec=RED, lw=1.2, ls="--"))
    ax1.plot([10 + cut_d, 10 + cut_d], [36, 62], color=RED, lw=2.2)
    ax1.text(18, 49, "4 × DEPTH RAILS: Cut to 520.0 mm (20.47\")", fontsize=9, weight="bold", color=DARK, va="center")
    ax1.text(10 + full_d + 10, 49, "Cut 64.2 mm (2.5\") off 1 end → Tap 1/4\"-20", fontsize=8.8, weight="bold", color=RED, va="center")

    # Height rails
    full_h = 508.0 * 0.68; cut_h = 230.2 * 0.68
    ax1.add_patch(Rectangle((10, 8), cut_h, 18, fc="#a3cfbb", ec=GREEN, lw=1.4))
    ax1.add_patch(Rectangle((10 + cut_h, 8), full_h - cut_h, 18, fc=GREY_LT, ec="#888", lw=1.0, ls="--"))
    ax1.plot([10 + cut_h, 10 + cut_h], [4, 30], color=GREEN, lw=2.2)
    ax1.text(16, 17, "4 × HEIGHT: 230.2 mm", fontsize=8.8, weight="bold", color=DARK, va="center")
    ax1.text(10 + full_h + 10, 17, "Practice tapping on the 4 offcuts first!", fontsize=8.8, weight="bold", color=GREEN, va="center")

    # Top-right: Tap Guide diagram
    ax2 = fig.add_axes([0.59, 0.50, 0.38, 0.35])
    ax2.set_xlim(0, 100); ax2.set_ylim(0, 100); ax2.axis("off")
    ax2.text(2, 93, "② How to Use the Printed Tap Guide", fontsize=11, weight="bold", color=DARK)
    ax2.add_patch(Rectangle((8, 28), 38, 34, fc=GREY, ec="#444", lw=1.5))
    ax2.plot([8, 46], [45, 45], color="#666", lw=1.2, ls="--")
    ax2.text(22, 66, "25 mm Rail\n(Squared End)", fontsize=8.8, ha="center", weight="bold")
    ax2.add_patch(Polygon([(34, 20), (64, 20), (64, 70), (34, 70), (34, 62), (46, 62), (46, 28), (34, 28)],
                          closed=True, fc=ORANGE, ec="#7a2d08", lw=1.5))
    ax2.add_patch(Rectangle((46, 41), 18, 8, fc="white", ec="#7a2d08", lw=1))
    ax2.add_patch(Rectangle((38, 42.5), 50, 5, fc=BLUE, ec="#0d2b66", lw=1.2))
    ax2.text(53, 76, "print_tool_tap_guide.stl\nSlips 14 mm over rail end", fontsize=8.8, weight="bold", color=ORANGE, ha="center")
    ax2.text(74, 24, "1/4\"-20 Tap + Cutting Oil\nStart square through Ø6.5 mm bore;\nback out 1/4 turn every 1/2 turn", fontsize=8.2, color=BLUE, ha="center", weight="bold")

    # Bottom-left: Front Panel Port Cutout Map
    ax3 = fig.add_axes([0.03, 0.04, 0.54, 0.43])
    ax3.set_aspect("equal"); ax3.axis("off")
    pw, ph = 444.0, 237.0
    ax3.add_patch(Rectangle((0, 0), pw, ph, fc="#343a40", ec="#111", lw=2))
    ax3.text(pw / 2, ph + 24, "③ FRONT PANEL CUTOUT TEMPLATE — 444 × 237 mm (Viewed from Outside Front)",
             fontsize=10.8, weight="bold", ha="center", color=DARK)
    ax3.text(pw / 2, ph + 8, "Measure X from LEFT (INBOARD) edge (0 mm), Z up from BOTTOM edge (0 mm):",
             fontsize=8.8, ha="center", color="#444")
    ax3.text(-10, ph / 2, "INBOARD EDGE (X = 0 mm)\n(Next to Main IceBox)", rotation=90, ha="right", va="center", fontsize=8.5, weight="bold", color=BLUE)
    ax3.text(pw + 10, ph / 2, "OUTBOARD EDGE\n(X = 444 mm)", rotation=270, ha="left", va="center", fontsize=8.5, weight="bold", color="#555")

    ports = [
        ("L14-30\nShore\nØ60\n(39, 50)", 39, 50, "c", 60, GOLD_LT, GOLD),
        ("L14-30\nAC Out\nØ60\n(39, 120)", 39, 120, "c", 60, GOLD_LT, GOLD),
        ("12V Ø29\n(39, 175)", 39, 175, "c", 29, BLUE_LT, BLUE),
        ("SB50 Solar\n48×37\n(92, 40)", 92, 40, "r", (48, 37), RED_LT, RED),
        ("SB50 Alt\n48×37\n(92, 96)", 92, 96, "r", (48, 37), RED_LT, RED),
        ("USB Ø22\n(92, 140)", 92, 140, "c", 22, GREEN_LT, GREEN),
        ("USB Ø22\n(92, 173)", 92, 173, "c", 22, GREEN_LT, GREEN),
        ("12V Ø29\n(124, 135)", 124, 135, "c", 29, BLUE_LT, BLUE),
        ("12V Ø29\n(124, 175)", 124, 175, "c", 29, BLUE_LT, BLUE),
        ("SB175\n(pack2)\n26×56\n(247, 88)", 247, 88, "r", (26, 56), ORANGE_LT, ORANGE),
    ]
    for lbl, x, z, kind, sz, fc, ec in ports:
        if kind == "c":
            ax3.add_patch(Circle((x, z), sz / 2, fc=fc, ec=ec, lw=1.5))
        else:
            w_, h_ = sz
            ax3.add_patch(Rectangle((x - w_ / 2, z - h_ / 2), w_, h_, fc=fc, ec=ec, lw=1.5))
        ax3.text(x, z, lbl, ha="center", va="center", fontsize=5.8, weight="bold", color=DARK)

    # Staggered column X guides under panel
    for x_col, y_txt, lbl_c in ((39, -8, "Col 1: X = 39 mm\n(Z = 50, 120, 175)"),
                                (92, -32, "Col 2: X = 92 mm\n(Z = 40, 96, 140, 173)"),
                                (124, -8, "Col 3: X = 124 mm\n(Z = 135, 175)"),
                                (247, -8, "Col 4: X = 247 mm\n(Z = 88)")):
        ax3.plot([x_col, x_col], [y_txt + 2, 18], color="#888", lw=0.9, ls=":")
        ax3.text(x_col, y_txt, lbl_c, ha="center", va="top", fontsize=7.5, weight="bold", color=DARK)
    ax3.set_xlim(-55, pw + 45); ax3.set_ylim(-58, ph + 38)

    # Bottom-right: Back Panel & Side Panels
    ax4 = fig.add_axes([0.59, 0.04, 0.38, 0.43])
    ax4.set_aspect("equal"); ax4.axis("off")
    ax4.add_patch(Rectangle((0, 0), pw, ph, fc="#495057", ec="#111", lw=2))
    ax4.text(pw / 2, ph + 24, "④ BACK PANEL (444 × 237 mm) + 2 SIDE PANELS",
             fontsize=10.5, weight="bold", ha="center", color=DARK)
    ax4.text(pw / 2, ph + 8, "Back panel uses donor perforated rear panel cut to 237 mm tall:",
             fontsize=8.8, ha="center", color="#444")
    gx_x, gx_z, gx_w, gx_h = 72, 138, 128, 86
    ax4.add_patch(Rectangle((gx_x - gx_w / 2, gx_z - gx_h / 2), gx_w, gx_h, fc=ORANGE_LT, ec=ORANGE, lw=2))
    ax4.text(gx_x, gx_z, "GX Touch 50 Cutout\n128 × 86 mm\n(80 mm from inboard rail,\n160 mm up from floor)\n+ print_touch_bezel.stl",
             ha="center", va="center", fontsize=7.5, weight="bold", color=DARK)
    for vx in range(175, 415, 38):
        for vz in (45, 115, 185):
            ax4.add_patch(Rectangle((vx, vz), 22, 8, fc="#ced4da", ec="none"))
    ax4.text(295, 22, "Factory Ventilation Slots", ha="center", fontsize=8.5, color="white", weight="bold")
    ax4.text(pw / 2, -26, "Plus cut 2 × Solid Side Panels to 527.5 mm long × 237 mm tall",
             ha="center", fontsize=9.2, weight="bold", color=BLUE,
             bbox=dict(boxstyle="round,pad=0.3", fc=BLUE_LT, ec=BLUE))
    ax4.set_xlim(-25, pw + 25); ax4.set_ylim(-58, ph + 38)

    path = os.path.join(OUT, "bench-01-rails-panels.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# BENCH 2: HEAT-SET INSERTS (TRAYS, DROP SHELVES, GARMIN HANGER & POSTS)
# =====================================================================================================================
def bench_02_inserts():
    fig = plt.figure(figsize=(15, 9.2), dpi=120)
    banner(fig, "BENCH 2", "Set Heat-Set Inserts — Trays, Drop Shelves, Posts & Garmin Hanger",
           "Set all brass inserts flush with a soldering iron (220–240 °C PETG / 250–260 °C ASA) BEFORE frame assembly.",
           [("12 × M4 Std 7.9mm (94180A353)", GREEN_LT, GREEN),
            ("2 × M4 Short 4.7mm (94180A351)", BLUE_LT, BLUE),
            ("4 × M5 6.7mm (94180A361)", RED_LT, RED)])

    # Panel 1: Battery Trays (×2)
    ax1 = fig.add_axes([0.02, 0.05, 0.35, 0.80])
    ax1.set_xlim(-25, 275); ax1.set_ylim(-75, 240); ax1.axis("off")
    ax1.text(121, 226, "① Battery Trays × 2 (print_tray_battery_0 & _1)", ha="center", fontsize=11.5, weight="bold", color=DARK)
    ax1.text(121, 211, "Identical in v12s & v13 — NO DRILLING (Ø5.6 mm holes printed to size)",
             ha="center", fontsize=8.8, weight="bold", color=GREEN)

    fd, fw = 242.0, 167.0
    ax1.add_patch(Rectangle((0, 20), fd, fw, fc=ORANGE_LT, ec=ORANGE, lw=1.8))
    ax1.add_patch(Rectangle((6, 26), fd - 12, 140, fc="white", ec="#7a2d08", lw=1.2))
    ax1.add_patch(Rectangle((0, 20 + fw - 21), fd, 21, fc="#f5b895", ec="#7a2d08", lw=1.2))
    ax1.text(fd / 2, 20 + fw - 18, "21 mm INBOARD WALL (Toward Center Column)", ha="center", va="center", fontsize=7.5, weight="bold", color=DARK)

    # 2 x Top M4 Standard inserts (x = 81, 161)
    for hx in (81, 161):
        ax1.add_patch(Circle((hx, 20 + fw - 8), 5.5, fc=GREEN, ec="white", lw=1.5))
    callout(ax1, (81, 20 + fw - 8), (121, 134),
            "2 × M4 Standard (7.9 mm, 94180A353)\nPress STRAIGHT DOWN into top of 21 mm wall\n(x = 81 & 161 mm from back end)",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=8.3)

    # 3 x Side M4 Standard inserts on outer face of inboard wall
    for hx in (40, 100, 140, 200):
        col_ = GREEN if hx != 200 else "#63b37b"
        ax1.add_patch(Rectangle((hx - 4, 20 + fw - 2), 8, 6, fc=col_, ec="black", lw=1))
    callout(ax1, (140, 20 + fw + 3), (121, 68),
            "3 × M4 Standard (7.9 mm) HORIZONTAL\ninto outer column face (z = 17 mm up):\n• Tray 0 (back): x = 40, 100, 140 mm\n• Tray 1 (front): x = 40, 120, 200 mm",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=8.2)

    # 4 x Countersunk rail holes (leave empty!)
    for (cx, cy) in ((70, 23), (172, 23), (3, 48), (3, 159)):
        ax1.add_patch(Circle((cx, cy), 4.2, fc="white", ec=BLUE, lw=1.5))
    callout(ax1, (70, 23), (121, -28),
            "4 × Countersunk 1/4\"-20 Holes Inside Pocket:\nLEAVE EMPTY (Bolts go into rails in Step 4)",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.5)

    # Panel 2: Breaker Drop Shelves (×2)
    ax2 = fig.add_axes([0.38, 0.05, 0.30, 0.80])
    ax2.set_xlim(-20, 190); ax2.set_ylim(-75, 240); ax2.axis("off")
    ax2.text(85, 226, "② Breaker Drop Shelves × 2", ha="center", fontsize=11.5, weight="bold", color=DARK)
    ax2.text(85, 211, "print_breaker_shelf_0 & _1 — NO DRILLING (Ø6.4 mm printed)",
             ha="center", fontsize=8.8, weight="bold", color=RED)

    ax2.add_patch(Rectangle((20, 25), 130, 168, fc=ORANGE_LT, ec=ORANGE, lw=1.8))
    ax2.add_patch(Rectangle((20, 25), 130, 6, fc=ORANGE, ec="#7a2d08", lw=1.2))
    ax2.add_patch(Rectangle((20, 25 + 147), 130, 21, fc="#f5b895", ec="#7a2d08", lw=1.2))
    b1, b2 = (44 + 8.9, 117 + 7.9), (44 + 65.5, 117 + 34.6)
    for bx, by in (b1, b2):
        ax2.add_patch(Circle((bx, by), 5.5, fc=RED, ec="white", lw=1.5))
    callout(ax2, b1, (85, 92), "2 × M5 Inserts (6.7 mm, 94180A361)\nPress STRAIGHT DOWN into top face\n(Diagonal holes for Bussmann 285 breaker)",
            color=RED, bg=RED_LT, ec=RED, fs=8.4)
    for fx_ in (45, 125):
        ax2.add_patch(Circle((fx_, 25 + 160), 3.8, fc="white", ec=DARK, lw=1.2))
    ax2.text(85, 25 + 148, "2 × M4 Clearance Holes in Foot (No inserts)", ha="center", va="bottom", fontsize=7.5, color=DARK, weight="bold")

    ax2.add_patch(Rectangle((5, -54), 160, 54, fc="#343a40", ec="black", lw=1.5))
    ax2.text(85, -27, "Peel & Stick 130 × 140 mm EPDM Foam Pad\nto FLAT UNDERSIDE of each shelf plate now\n(Compresses 1 mm onto battery top in Step 6)",
             ha="center", va="center", fontsize=8.0, weight="bold", color="white")

    # Panel 3: Garmin Hanger & Inverter Posts
    ax3 = fig.add_axes([0.69, 0.05, 0.29, 0.80])
    ax3.set_xlim(0, 180); ax3.set_ylim(-75, 240); ax3.axis("off")
    ax3.text(90, 226, "③ Garmin Hanger & Inverter Posts", ha="center", fontsize=11.5, weight="bold", color=DARK)
    ax3.text(90, 211, "Drill 4.6 mm printed pilots to 5.6 mm (7/32\") first!", ha="center", fontsize=8.8, weight="bold", color=BLUE)

    ax3.add_patch(Rectangle((25, 78), 130, 115, fc=ORANGE_LT, ec=ORANGE, lw=1.8))
    ax3.text(90, 180, "print_garmin_hanger.stl", ha="center", fontsize=9.5, weight="bold", color=DARK)
    for gx_ in (47.5, 132.5):
        ax3.add_patch(Circle((gx_, 136), 5.2, fc=BLUE, ec="white", lw=1.5))
    callout(ax3, (47.5, 136), (90, 98),
            "2 × M4 Short (4.7 mm, 94180A351)\n1. Drill pilots to Ø5.6 mm (7/32\")\n2. Press flush from Garmin side",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.2)

    for px, lbl in ((30, "Post 0 (Back)"), (120, "Post 1 (Front)")):
        ax3.add_patch(Rectangle((px, -54), 30, 105, fc=ORANGE_LT, ec=ORANGE, lw=1.8))
        ax3.add_patch(Circle((px + 15, 51), 5.2, fc=GREEN, ec="white", lw=1.5))
        ax3.text(px + 15, -24, lbl, ha="center", va="center", rotation=90, fontsize=8.5, weight="bold", color=DARK)
    callout(ax3, (45, 51), (90, 24),
            "1 × M4 Standard (7.9 mm)\ninto TOP END of each post\n(Drill to Ø5.6 mm; v12s only)",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=8.0)

    path = os.path.join(OUT, "bench-02-inserts-trays-shelves.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# BENCH 3: INVERTER PLATE SUB-ASSEMBLY (6 TILES + 8 SPLINES + 22 INSERTS + COLUMN UNITS)
# =====================================================================================================================
def bench_03_plate():
    fig = plt.figure(figsize=(15, 9.5), dpi=120)
    banner(fig, "BENCH 3", "Inverter Plate Sub-Assembly — Glue 6 Tiles, Set 22 Inserts & Mount Units",
           "Glue tiles 00..21 + 8 splines flat on the bench, drill the 22 printed Ø4.6 mm pilots, press inserts, and pre-mount units.",
           [("14 × M4 Short 4.7mm (Ø5.6mm)", BLUE_LT, BLUE),
            ("8 × M5 6.7mm (Ø6.4mm)", RED_LT, RED),
            ("8 × Splines + CA Glue", ORANGE_LT, DARK)])

    W_pl, H_pl = 505.5, 256.0
    zp = 21.0
    px0 = X0 + 18.0 - 10.0  # 33.0 in box coords

    # Left half: COLUMN FACE (-Y, facing batteries & bus column)
    ax1 = fig.add_axes([0.02, 0.06, 0.47, 0.80])
    ax1.set_aspect("equal"); ax1.axis("off")
    ax1.text(W_pl / 2, H_pl + 44, "① COLUMN FACE (Facing Batteries) — Set 18 Inserts & Mount 3 Units",
             ha="center", fontsize=11.0, weight="bold", color=DARK)
    ax1.text(W_pl / 2, H_pl + 20, "Drill 14 BLUE holes to Ø5.6 mm (7/32\") → Press M4 Short (4.7 mm)\nDrill 4 RED holes to Ø6.4 mm (1/4\") → Press M5 (6.7 mm)",
             ha="center", fontsize=8.5, weight="bold", color=BLUE)

    ax1.add_patch(Rectangle((0, 0), W_pl, H_pl, fc=ORANGE_LT, ec=ORANGE, lw=2))
    for col_i in range(3):
        for row_i in range(2):
            ax1.text(col_i * 168.5 + 84, row_i * 128 + 52, f"Tile {col_i}{row_i}",
                     ha="center", va="center", fontsize=13, weight="bold", color="#e6ccb8")
    for cx in (168.5, 337.0):
        ax1.plot([cx, cx], [0, H_pl], color="#7a2d08", lw=1.2, ls="--")
        for sz in (162, 218):
            ax1.add_patch(Rectangle((cx - 30, sz - 9), 60, 18, fc=ORANGE, ec="#7a2d08", lw=1))
    ax1.add_patch(Rectangle((0, 116), W_pl, 24, fc="#f5ceb0", ec="#7a2d08", lw=0.8, ls=":"))
    ax1.text(W_pl / 2, 128, "24 mm Horizontal Half-Lap Joint (CA Glue)", ha="center", va="center", fontsize=7.8, color="#7a2d08", weight="bold")

    # Cable window in tile 20 (front-bottom)
    wx = (D - B - 18.0 - 4.0 - 70.0) - px0
    wz = 42.0 - zp
    ax1.add_patch(FancyBboxPatch((wx, wz), 70, 70, boxstyle="round,pad=0,rounding_size=10", fc="white", ec="#7a2d08", lw=1.5))
    ax1.text(wx + 35, wz + 35, "70×70 Cable\nWindow\n(Front End)", ha="center", va="center", fontsize=7.8, weight="bold", color="#555")

    # 6 x Sill M4 Short inserts along bottom band (z = 28 -> u_z = 7)
    sill_xs = [32.0, 146.7, 226.7, 278.8, 358.8, 473.5]
    for sx in sill_xs:
        ax1.add_patch(Circle((sx, 7.0), 6.5, fc=BLUE, ec="white", lw=1.3))
    callout(ax1, (sill_xs[2], 7.0), (W_pl / 2, -42),
            "6 × M4 Short (4.7 mm) along Bottom Band (z = 7 mm from bottom edge)\nLeave empty on bench — Bus Shelf wall bolts here in Step 8 (6 × M4 × 8)",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.2)

    # Units on column face using exact c.w x c.h envelope on the plate
    units_info = [
        ("mppt", 50.0, 80.0, "MPPT 100/30\n4 × M5 (6.7 mm)\nDrive 4× M5×8\n(3 mm proud) & hang", RED, RED_LT),
        ("cerbo", 205.0, 188.0, "Cerbo GX\n4 × M4 Short (4.7 mm)\nMount with 4× M4×8", BLUE, BLUE_LT),
        ("orion", 390.0, 118.0, "Orion XS 50A\n4 × M4 Short (4.7 mm)\nMount with 4× M4×8", BLUE, BLUE_LT),
    ]
    for ukey, x0_box, z0_box, lbl, col, bg in units_info:
        c = cage.COMPONENTS[ukey]
        ux, uz = x0_box - px0, z0_box - zp
        uw, uh = c.w, c.h
        ax1.add_patch(Rectangle((ux, uz), uw, uh, fc=bg, ec=col, lw=1.6, ls="--", alpha=0.88))
        ax1.text(ux + uw / 2, uz + uh / 2, lbl, ha="center", va="center", fontsize=7.6, weight="bold", color=DARK)
        for (hu, hv) in cage.HOLES[ukey]:
            ax1.add_patch(Circle((ux + hu, uz + hv), 6.5, fc=col, ec="white", lw=1.3))

    ax1.text(0, -16, "◀ BACK (Post 0)", fontsize=8.8, weight="bold", color="#444")
    ax1.text(W_pl, -16, "FRONT (Post 1) ▶", ha="right", fontsize=8.8, weight="bold", color="#444")
    ax1.set_xlim(-25, W_pl + 25); ax1.set_ylim(-68, H_pl + 58)

    # Right half: INVERTER FACE (+Y, facing MultiPlus)
    ax2 = fig.add_axes([0.51, 0.06, 0.47, 0.80])
    ax2.set_aspect("equal"); ax2.axis("off")
    ax2.text(W_pl / 2, H_pl + 44, "② INVERTER FACE (Facing MultiPlus) — Set 4 × M5 Inserts & Leave Screws Proud",
             ha="center", fontsize=11.0, weight="bold", color=DARK)
    ax2.text(W_pl / 2, H_pl + 20, "Drill 4 RED keyhole pilots to Ø6.4 mm (1/4\") → Press 4 × M5 (6.7 mm, 94180A361)",
             ha="center", fontsize=8.5, weight="bold", color=RED)

    ax2.add_patch(Rectangle((0, 0), W_pl, H_pl, fc=ORANGE_LT, ec=ORANGE, lw=2))
    inv_x0 = W_pl - ((cage.V13["inv_x"] - px0) + 375.0)
    inv_z0 = 22.0 - zp
    ax2.add_patch(Rectangle((inv_x0, inv_z0), 375.0, 249.0, fc=BLUE_LT, ec=BLUE, lw=1.6, ls="--", alpha=0.55))
    ax2.text(inv_x0 + 187.5, inv_z0 + 135, "MultiPlus 12/800 or 12/1200 Footprint\n(Hangs on these 4 proud M5 screws in Step 9)",
             ha="center", va="center", fontsize=9.5, weight="bold", color=BLUE)

    mp_pts = []
    for (hu, hv) in cage.HOLES["multiplus_1200_long"]:
        mx = W_pl - ((cage.V13["inv_x"] - px0) + hu)
        mz = inv_z0 + hv
        mp_pts.append((mx, mz))
        ax2.add_patch(Circle((mx, mz), 7.5, fc=RED, ec="white", lw=1.5))

    callout(ax2, mp_pts[0], (W_pl / 2, -42),
            "IMPORTANT — Pre-Install 4 × M5 × 10 Button Heads + 10 mm Washers Now!\nLeave heads 3 mm PROUD of the plate face so MultiPlus keyholes drop over them in Step 9.",
            color=RED, bg=RED_LT, ec=RED, fs=8.2)

    for cx in (W_pl - 168.5, W_pl - 337.0):
        ax2.plot([cx, cx], [0, H_pl], color="#7a2d08", lw=1.2, ls="--")
        for sz in (38, 94):
            ax2.add_patch(Rectangle((cx - 30, sz - 9), 60, 18, fc=ORANGE, ec="#7a2d08", lw=1))
    ax2.text(W_pl / 2, 66, "4 × Lower Splines Glued into Flush Pockets on Inverter Face",
             ha="center", va="center", fontsize=8, weight="bold", color="#7a2d08",
             bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=ORANGE))

    ax2.text(0, -16, "◀ FRONT (Post 1)", fontsize=8.8, weight="bold", color="#444")
    ax2.text(W_pl, -16, "BACK (Post 0) ▶", ha="right", fontsize=8.8, weight="bold", color="#444")
    ax2.set_xlim(-25, W_pl + 25); ax2.set_ylim(-68, H_pl + 58)

    path = os.path.join(OUT, "bench-03-subassembly-plate.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# BENCH 4: BUS SHELF (PLATES 0 + 1 + 2) & GARMIN HANGER SUB-ASSEMBLIES
# =====================================================================================================================
def bench_04_bus_garmin():
    fig = plt.figure(figsize=(15, 8.8), dpi=120)
    banner(fig, "BENCH 4", "Bus Shelf (Plates 0 + 1 + 2) & Garmin Hanger Sub-Assemblies",
           "Join the 3 bus shelf plates (521.5 mm total), set 6 × M5 inserts, and mount the SmartShunt, Bus Bars & Garmin.",
           [("6 × M5 6.7mm Inserts (94180A361)", RED_LT, RED),
            ("6 × M5 × 12 Screws + 2 Washers", GOLD_LT, DARK),
            ("2 × M4 × 10 (Garmin)", BLUE_LT, BLUE)])

    ax1 = fig.add_axes([0.03, 0.07, 0.62, 0.78])
    ax1.set_aspect("equal"); ax1.axis("off")
    ax1.text(260, 195, "① Bus Shelf Sub-Assembly (521.5 × 110 mm) — Glue 2 Wall Half-Laps & Bolt Shunt + Bus Bars",
             ha="center", fontsize=11.0, weight="bold", color=DARK)

    b0, b1, b2 = 194.7, 326.8, 521.5
    ax1.add_patch(Rectangle((0, 0), b0, 110, fc=ORANGE_LT, ec=ORANGE, lw=1.8))
    ax1.add_patch(Rectangle((b0, 0), b1 - b0, 110, fc="#ffd8a8", ec=ORANGE, lw=2.2))
    ax1.add_patch(Rectangle((b1, 0), b2 - b1, 110, fc=ORANGE_LT, ec=ORANGE, lw=1.8))

    ax1.text(b0 / 2, 122, "print_bus_shelf_0 (Back)\n214.7 mm w/ tongue", ha="center", fontsize=8.8, weight="bold", color=DARK)
    ax1.text((b0 + b1) / 2, 126, "print_bus_shelf_1 (Middle)\n152.0 mm (Shortened for 22.5\" box!)",
             ha="center", fontsize=8.8, weight="bold", color=RED,
             bbox=dict(boxstyle="round,pad=0.25", fc=RED_LT, ec=RED))
    ax1.text((b1 + b2) / 2, 122, "print_bus_shelf_2 (Front)\n194.7 mm", ha="center", fontsize=8.8, weight="bold", color=DARK)

    for lx in (b0, b1):
        ax1.add_patch(Rectangle((lx, 0), 20, 8, fc=ORANGE, ec="black", lw=1))
        ax1.add_patch(Rectangle((lx, 102), 20, 8, fc=ORANGE, ec="black", lw=1))
        ax1.text(lx + 10, -14, "20 mm Wall Half-Lap\n(Drop of CA Glue)", ha="center", va="top", fontsize=8, weight="bold", color=ORANGE)

    ax1.add_patch(Rectangle((205, 16), 120, 44, fc=BLUE_LT, ec=BLUE, lw=1.6))
    ax1.text(265, 38, "SmartShunt 500A\n2 × M5 Inserts + M5×12", ha="center", va="center", fontsize=7.8, weight="bold", color=BLUE)
    for sx in (217, 313):
        ax1.add_patch(Circle((sx, 38), 5.0, fc=RED, ec="white", lw=1.2))

    for bx, lbl in ((35, "Positive (+) Bus Bar\n2 × M5 Inserts + M5×12"), (345, "Negative (−) Bus Bar\n2 × M5 Inserts + M5×12")):
        ax1.add_patch(Rectangle((bx, 62), 145, 32, fc=GOLD_LT, ec=GOLD, lw=1.6))
        ax1.text(bx + 72.5, 78, lbl, ha="center", va="center", fontsize=7.8, weight="bold", color=DARK)
        for hx in (bx + 18, bx + 127):
            ax1.add_patch(Circle((hx, 78), 5.0, fc=RED, ec="white", lw=1.2))

    callout(ax1, (217, 38), (260, -52),
            "Mark the 6 mounting holes using your real SmartShunt & Bus Bars → Drill Ø6.4 mm (1/4\")\n→ Press 6 × M5 (6.7 mm) Inserts → Bolt units down on the bench before Step 7!",
            color=RED, bg=RED_LT, ec=RED, fs=8.5)

    ax1.set_xlim(-30, 555); ax1.set_ylim(-80, 215)

    ax2 = fig.add_axes([0.67, 0.07, 0.30, 0.78])
    ax2.set_aspect("equal"); ax2.axis("off")
    ax2.text(80, 195, "② Garmin Hanger Sub-Assembly", ha="center", fontsize=11.0, weight="bold", color=DARK)
    ax2.add_patch(Rectangle((15, 20), 130, 149, fc=ORANGE_LT, ec=ORANGE, lw=1.8))
    ax2.add_patch(Rectangle((17.5, 42), 125, 75, fc="#343a40", ec="black", lw=1.6))
    ax2.text(80, 80, "Garmin PowerSwitch\n(Snaps into bracket)", ha="center", va="center", fontsize=9, weight="bold", color="white")
    for gx_ in (37.5, 122.5):
        ax2.add_patch(Circle((gx_, 79.5), 5.5, fc=BLUE, ec="white", lw=1.5))
    callout(ax2, (37.5, 79.5), (80, -25),
            "Bolt Garmin bracket to plate\nwith 2 × M4 × 10 Button Heads\ninto the 2 × M4 Short inserts",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=9)
    for rx in (40, 120):
        ax2.add_patch(Circle((rx, 156.5), 4.5, fc="white", ec=DARK, lw=1.4))
    ax2.text(80, 175, "2 × Top Rail Countersinks (Step 8)", ha="center", fontsize=8.5, color="#555", weight="bold")
    ax2.set_xlim(-10, 170); ax2.set_ylim(-60, 215)

    path = os.path.join(OUT, "bench-04-subassembly-bus.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# STEP 1 & 2: FRAME, PANELS & 24 DROP-IN T-NUT MAP
# =====================================================================================================================
def step1_2():
    fig = plt.figure(figsize=(15, 9.2), dpi=120)
    banner(fig, "STEPS 1–2", "Assemble Frame, Slide in 4 Panels & Load All 24 Drop-In T-Nuts",
           "Slide each panel into the rail centre slots before closing that face, then roll 24 × 1/4\"-20 T-nuts into the INNER rail slots.",
           [("8 × Corner Cubes + 12 Rails", GREY_LT, DARK),
            ("24 × 1/4\"-20 Drop-In T-Nuts (6000N501)", BLUE_LT, BLUE)])

    ax = fig.add_axes([0.04, 0.06, 0.92, 0.80])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY, ec="#555", lw=1.2))
    for cx in (0, D - B):
        for cy in (0, W - B):
            ax.add_patch(Rectangle((cx, cy), B, B, fc="#222", ec="black", lw=1))

    for x in (70, 172, 349.5, 451.5):
        ax.plot(X0 + x, B, marker="^", color=BLUE, ms=9)
        ax.text(X0 + x, B + 10, f"{x:.0f}", ha="center", fontsize=8.5, weight="bold", color=BLUE)
    for x in (81, 161, 360.5, 440.5):
        ax.plot(X0 + x, 4, marker="v", color=RED, ms=9)
        ax.text(X0 + x, -14, f"{x:.0f}", ha="center", fontsize=8.5, weight="bold", color=RED)

    for x in (341.5, 421.5):
        ax.plot(X0 + x, W - B, marker="v", color=BLUE, ms=9)
        ax.plot(X0 + x, W - 4, marker="^", color=RED, ms=9)
        ax.text(X0 + x, W - B - 16, f"{x:.1f}", ha="center", fontsize=8.5, weight="bold", color=DARK)

    for y in (29, 140, 198, 238, 281):
        ax.plot(B, Y0 + y, marker=">", color=BLUE, ms=8.5)
        ax.text(B + 10, Y0 + y, f"{y}", va="center", fontsize=8.5, weight="bold", color=BLUE)
        ax.plot(D - B, Y0 + y, marker="<", color=BLUE, ms=8.5)
        ax.text(D - B - 10, Y0 + y, f"{y}", ha="right", va="center", fontsize=8.5, weight="bold", color=BLUE)
    ax.plot(4, Y0 + 291, marker=">", color=RED, ms=9)
    ax.text(-8, Y0 + 291, "TOP: 291\n(Post Clip 0)", ha="right", va="center", fontsize=8.5, weight="bold", color=RED)
    ax.plot(D - 4, Y0 + 291, marker="<", color=RED, ms=9)
    ax.text(D + 8, Y0 + 291, "TOP: 291\n(Post Clip 1)", ha="left", va="center", fontsize=8.5, weight="bold", color=RED)

    ax.add_patch(FancyBboxPatch((82, 85), 408, 305, boxstyle="round,pad=0.4", fc="#f8f9fa", ec="#adb5bd", lw=1.2))
    ax.text(286, 365, "WHERE TO LOAD THE 24 DROP-IN T-NUTS", ha="center", fontsize=11.5, weight="bold", color=DARK)
    ax.text(286, 340, "All distances measured from BACK rail inner face (X = 0) or OUTBOARD rail inner face (Y = 0):",
            ha="center", fontsize=8.5, color="#444")
    summary = (
        "[BLUE TRIANGLES] BOTTOM RAILS (Inner Slot, z = 12.5 mm above floor) — 16 T-Nuts:\n"
        "  • Bottom Outboard Rail (4):  X = 70, 172, 349.5, 451.5 mm  (Battery Trays)\n"
        "  • Bottom Back Rail (5):      Y = 29, 140 (Tray 0) | 198, 238 (Bus Shelf) | 281 mm (Post 0)\n"
        "  • Bottom Front Rail (5):     Y = 29, 140 (Tray 1) | 198, 238 (Bus Shelf) | 281 mm (Post 1)\n"
        "  • Bottom Inboard Rail (2):   X = 341.5, 421.5 mm  (Lower Garmin Hanger)\n\n"
        "[RED TRIANGLES] TOP RAILS (Inner Slot, z = 269.2 mm) — 8 T-Nuts (v12s only; 0 in v13):\n"
        "  • Top Outboard Rail (4):     X = 81, 161, 360.5, 440.5 mm  (Breaker Shelf Hangers)\n"
        "  • Top Back & Front Rails (2): Y = 291 mm on each rail  (Post Clips 0 & 1)\n"
        "  • Top Inboard Rail (2):      X = 341.5, 421.5 mm  (Upper Garmin Hanger)"
    )
    ax.text(96, 212, summary, ha="left", va="center", fontsize=8.5, family="sans-serif", color=DARK, linespacing=1.42)

    ax.text(D / 2, -38, "OUTBOARD SIDE — Put 4 T-Nuts in Bottom Slot (Blue ▲) + 4 T-Nuts in Top Slot (Red ▼)",
            ha="center", fontsize=9.5, weight="bold", color=DARK)
    ax.text(D / 2, W + 22, "INBOARD SIDE — Put 2 T-Nuts in Bottom Slot (Blue ▼) + 2 T-Nuts in Top Slot (Red ▲)",
            ha="center", fontsize=9.5, weight="bold", color=DARK)
    ax.set_xlim(-95, D + 95); ax.set_ylim(-55, W + 45)

    path = os.path.join(OUT, "01-frame-simple.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# STEP 3: INVERTER POSTS
# =====================================================================================================================
def step3():
    p0, p1 = bb["print_post_inverter_0"], bb["print_post_inverter_1"]
    fig = plt.figure(figsize=(15, 9.2), dpi=120)
    banner(fig, "STEP 3", "Install the Two Inverter-Plate Posts (Post 0 & Post 1)",
           "Stand each post against the back and front width rails (slots facing each other) and drive 1 sill bolt per post.",
           [("Tool: 5/32\" Hex Key", GREY_LT, DARK),
            ("2 × 1/4\"-20 × 7/8\" Button Head (92949A541)", BLUE_LT, BLUE)])

    ax = fig.add_axes([0.03, 0.30, 0.94, 0.56])
    plan(ax, r"^print_post_inverter_")
    yc = (p0.ymin + p0.ymax) / 2
    arrow(ax, (D * 0.50, Y0), (D * 0.50, yc), f"{yc - Y0:.0f} mm\nfrom outboard rail face\nto post centre (T-nut at 281 mm)", offset=(0, 0))
    arrow(ax, (D * 0.80, yc), (D * 0.80, W - B), f"{(W - B) - yc:.0f} mm\nto inboard rail", offset=(0, 0))
    callout(ax, (p0.xmax, p0.ymin + 12), (p0.xmax + 115, Y0 + 55),
            "① Post 0 (print_post_inverter_0)\nPush flat against BACK rail\n(Slot faces front of box)", ec=ORANGE)
    callout(ax, (p1.xmin, p1.ymin + 12), (p1.xmin - 115, Y0 + 55),
            "② Post 1 (print_post_inverter_1)\nPush flat against FRONT rail\n(Slot faces back of box)", ec=ORANGE)

    ax2 = fig.add_axes([0.04, 0.02, 0.92, 0.25]); ax2.set_aspect("equal"); ax2.axis("off")
    ax2.add_patch(Rectangle((0, 0), 60, B, fc=GREY, ec="#666"))
    ax2.add_patch(Rectangle((0, H - B), 60, B, fc=GREY, ec="#666"))
    ax2.add_patch(Rectangle((60, 0), 18, 254, fc=ORANGE, ec="#7a2d08"))
    ax2.plot([64, 30], [B / 2, B / 2], color=BLUE, lw=4)
    ax2.text(-8, B / 2, "③ Drive 1 × 1/4\"-20 × 7/8\" Button-Head\nthrough plain sill hole (z = 12.5 mm)\ninto width rail T-nut at Y = 281 mm",
             ha="right", va="center", fontsize=10, color=BLUE, weight="bold")
    arrow(ax2, (150, 0), (150, 254), "Post stands 254 mm tall on floor\n(Top M4 insert faces UP for Step 8)", offset=(135, 0), fs=10)
    ax2.set_xlim(-250, 560); ax2.set_ylim(-15, 310)
    path = os.path.join(OUT, "03-posts-simple.png"); fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# STEP 4: BATTERY TRAYS
# =====================================================================================================================
def step4():
    t0, t1 = bb["print_tray_battery_0"], bb["print_tray_battery_1"]
    fig = plt.figure(figsize=(15, 9.2), dpi=120)
    banner(fig, "STEP 4", "Bolt the Two Battery Trays to the Bottom Rails",
           "Push Tray 0 into the back-outboard corner and Tray 1 into the front-outboard corner; drive 4 countersunk screws per tray.",
           [("Tool: 5/32\" Hex Key", GREY_LT, DARK),
            ("8 × 1/4\"-20 × 1/2\" Flat-Head Screws (92210A537)", BLUE_LT, BLUE)])

    ax = fig.add_axes([0.04, 0.06, 0.92, 0.80])
    plan(ax, r"^print_tray_battery_", [r"^print_post_inverter_"])

    for idx, (tr, lbl, x_nuts) in enumerate(((t0, "Tray 0 (Back)\nprint_tray_battery_0", (70, 172)),
                                             (t1, "Tray 1 (Front)\nprint_tray_battery_1", (349.5, 451.5)))):
        ax.add_patch(Rectangle((tr.xmin + 6, tr.ymin + 6), tr.xlen - 12, 140, fc="#fff5eb", ec="#7a2d08", lw=1))
        ax.text((tr.xmin + tr.xmax) / 2, tr.ymin + 76, lbl, ha="center", va="center", fontsize=11, weight="bold", color=DARK)
        for xn in x_nuts:
            bx = X0 + xn
            ax.plot([bx, bx], [tr.ymin + 14, B / 2], color=BLUE, lw=3)
            ax.add_patch(Circle((bx, tr.ymin + 10), 5, fc=BLUE, ec="white", lw=1))
        for yn in (29, 140):
            by = Y0 + yn
            if idx == 0:
                ax.plot([tr.xmin + 14, B / 2], [by, by], color=BLUE, lw=3)
                ax.add_patch(Circle((tr.xmin + 10, by), 5, fc=BLUE, ec="white", lw=1))
            else:
                ax.plot([tr.xmax - 14, D - B / 2], [by, by], color=BLUE, lw=3)
                ax.add_patch(Circle((tr.xmax - 10, by), 5, fc=BLUE, ec="white", lw=1))

    callout(ax, (X0 + 172, t0.ymin + 10), (160, 265),
            "① Drive 2 × 1/4\"-20 × 1/2\" Flat-Head Screws\nthrough OUTER wall into Bottom Outboard Rail\n(Tray 0: X = 70, 172 mm | Tray 1: X = 349.5, 451.5 mm)",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=9.2)
    callout(ax, (t0.xmin + 10, Y0 + 140), (160, 385),
            "② Drive 2 × 1/4\"-20 × 1/2\" Flat-Head Screws\nthrough END wall into Width Rail (Y = 29 & 140 mm)\nConfirm all 8 heads sit FLUSH inside countersinks!",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=9.2)
    callout(ax, (t1.xmax - 20, t1.ymax - 10), (425, 325),
            "③ Verify 5 × M4 Brass Inserts\nare already set in the 21 mm\ninboard wall of each tray!",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=9.2)

    path = os.path.join(OUT, "04-trays-simple.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# STEP 6: BREAKER DROP SHELVES & BUSSMANN 285 BREAKERS
# =====================================================================================================================
def step6():
    fig = plt.figure(figsize=(15, 9.2), dpi=120)
    banner(fig, "STEPS 5–6", "Drop In Batteries (Step 5), Then Install Breaker Drop Shelves (Step 6)",
           "Lower both SuperPack 60Ah batteries into the trays FIRST, then clamp each battery down with its Breaker Drop Shelf.",
           [("4 × M4 × 10 Foot Screws", GREEN_LT, GREEN),
            ("4 × 1/4\"-20 × 1/2\" Hanger Screws", BLUE_LT, BLUE),
            ("4 × M5 × 10 + Washers (Breakers)", RED_LT, RED)])

    ax1 = fig.add_axes([0.03, 0.06, 0.54, 0.80])
    plan(ax1, r"^(print_breaker_shelf_|power_breaker_shelf_)", [r"^print_post_inverter_", r"^print_tray_battery_", r"^battery_"])
    for r, x_nuts in ((0, (81, 161)), (1, (360.5, 440.5))):
        sh = bb[f"print_breaker_shelf_{r}"]
        br = bb[f"power_breaker_shelf_{r}"]
        ax1.add_patch(Rectangle((br.xmin, br.ymin), br.xlen, br.ylen, fc=GOLD, ec="black", lw=1.2))
        ax1.text((br.xmin + br.xmax) / 2, (br.ymin + br.ymax) / 2, "Bussmann\n285", ha="center", va="center", fontsize=8, weight="bold")
        for xn in x_nuts:
            bx = X0 + xn
            ax1.add_patch(Circle((bx, sh.ymax - 8), 5.5, fc=GREEN, ec="white", lw=1.2))
            ax1.add_patch(Circle((bx, Y0 + 4), 5.5, fc=BLUE, ec="white", lw=1.2))

    callout(ax1, (X0 + 161, bb["print_breaker_shelf_0"].ymax - 8), (185, 275),
            "① FIRST: Drive 2 × M4 × 10 Button Heads\nstraight down through foot into Tray Wall\n(X = 81, 161 mm & 360.5, 440.5 mm)",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=8.8)
    callout(ax1, (X0 + 360.5, Y0 + 4), (370, 390),
            "② SECOND: Drive 2 × 1/4\"-20 × 1/2\" Flat-Head\nthrough top hanger into Top Outboard Rail\n(Compresses foam pad 1 mm onto battery!)",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.8)

    ax2 = fig.add_axes([0.59, 0.06, 0.39, 0.80])
    ax2.set_aspect("equal"); ax2.axis("off")
    ax2.text(105, 295, "Cross-Section (Looking Along Box Depth)", ha="center", fontsize=11.5, weight="bold", color=DARK)

    ax2.add_patch(Rectangle((0, 0), B, B, fc=GREY, ec="#555", lw=1.2))
    ax2.add_patch(Rectangle((0, H - B), B, B, fc=GREY, ec="#555", lw=1.2))
    ax2.add_patch(Polygon([(26, 0), (193, 0), (193, 36), (172, 36), (172, 6), (32, 6), (32, 36), (26, 36)],
                          closed=True, fc=ORANGE_LT, ec=ORANGE, lw=1.5))
    ax2.add_patch(Rectangle((32.5, 6), 139, 208, fc=BLUE_LT, ec=BLUE, lw=1.5))
    ax2.text(102, 125, "Step 5:\nSuperPack 60Ah\nBattery\n(Lower in BEFORE\ndrop shelf!)", ha="center", va="center", fontsize=9.5, weight="bold", color=BLUE)
    ax2.add_patch(Rectangle((32.5, 214), 139, 3, fc="#222", ec="black"))
    ax2.add_patch(Polygon([(25, 215), (178, 215), (178, 36), (193, 36), (193, 42), (184, 42), (184, 239),
                           (178, 239), (178, 221), (31, 221), (31, 278.7), (25, 278.7)],
                          closed=True, fc=ORANGE, ec="#7a2d08", lw=1.4))
    ax2.add_patch(Rectangle((117, 221), 49, 44, fc=GOLD, ec="black", lw=1.3))
    ax2.text(141.5, 243, "③ Breaker\n2× M5×10", ha="center", va="center", fontsize=7.5, weight="bold")

    callout(ax2, (186, 42), (125, 72), "① Foot Bolt (2 × M4 × 10)\nStraight down into 21 mm tray wall", color=GREEN, bg=GREEN_LT, ec=GREEN, fs=8.5)
    callout(ax2, (25, 269.2), (125, 276), "② Hanger Bolt (2 × 1/4\"-20 × 1/2\")\ninto Top Outboard Rail (v12s)", color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.5)
    ax2.set_xlim(-15, 220); ax2.set_ylim(-15, 315)

    path = os.path.join(OUT, "06-shelves-simple.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# STEP 7: BUS SHELF INSTALLATION
# =====================================================================================================================
def step7():
    fig = plt.figure(figsize=(15, 9.2), dpi=120)
    banner(fig, "STEP 7", "Drop In the Assembled Bus Shelf & Bolt to Trays and Width Rails",
           "Lower the 521.5 mm Bus Shelf sub-assembly into the center column; drive 6 side M4 bolts and 4 rail 1/4\"-20 bolts.",
           [("6 × M4 × 10 Lip Screws (92095A190)", GREEN_LT, GREEN),
            ("4 × 1/4\"-20 × 1/2\" End-Wall Screws (92210A537)", BLUE_LT, BLUE)])

    ax = fig.add_axes([0.04, 0.06, 0.92, 0.80])
    plan(ax, r"^(print_bus_shelf_|power_busbar_|power_shunt_|victron_smartshunt_)",
         [r"^print_post_inverter_", r"^print_tray_battery_", r"^print_breaker_shelf_"])

    t0_x, t1_x = bb["print_tray_battery_0"].xmin, bb["print_tray_battery_1"].xmin
    lip_y = bb["print_bus_shelf_0"].ymin
    for hx in [t0_x + 40, t0_x + 100, t0_x + 140, t1_x + 40, t1_x + 120, t1_x + 200]:
        ax.add_patch(Circle((hx, lip_y + 3), 5.5, fc=GREEN, ec="white", lw=1.3))
        ax.plot([hx, hx], [lip_y + 12, lip_y - 8], color=GREEN, lw=2.5)

    for yn in (198, 238):
        by = Y0 + yn
        ax.add_patch(Circle((X0 + 4, by), 5.5, fc=BLUE, ec="white", lw=1.3))
        ax.add_patch(Circle((D - B - 4, by), 5.5, fc=BLUE, ec="white", lw=1.3))

    callout(ax, (t0_x + 100, lip_y + 3), (205, 325),
            "① Drive 6 × M4 × 10 Button Heads (3 into Tray 0, 3 into Tray 1)\nhorizontally through the Bus Shelf outboard lip into the Trays' M4 inserts",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=9.2)
    callout(ax, (X0 + 4, Y0 + 238), (370, 410),
            "② Drive 4 × 1/4\"-20 × 1/2\" Flat-Head Screws\n(2 through Back Wall + 2 through Front Wall)\ninto Bottom Width Rail T-Nuts at Y = 198 & 238 mm",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=9.2)

    path = os.path.join(OUT, "07-bus-simple.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# STEP 8: INVERTER PLATE, POST CLIPS & GARMIN HANGER
# =====================================================================================================================
def step8():
    fig = plt.figure(figsize=(15, 9.2), dpi=120)
    banner(fig, "STEP 8", "Slide In Inverter Plate, Bolt Sill & Post Clips, Mount Garmin Hangers",
           "Drop the pre-assembled Inverter Plate into the post slots, drive 6 sill screws, lock top post clips, and bolt Garmin plates.",
           [("6 × M4 × 8 Sill Screws", BLUE_LT, BLUE),
            ("2 × M4 × 35 + 2 × 1/4\"-20 × 7/8\" (Clips)", RED_LT, RED),
            ("4 × 1/4\"-20 × 1/2\" (Garmin)", GREEN_LT, GREEN)])

    ax = fig.add_axes([0.04, 0.06, 0.92, 0.80])
    plan(ax, r"^(print_plate_inverter_|victron_mppt_|victron_cerbo_|victron_orion_|print_post_clip_|print_garmin_hanger|garmin_powerswitch_hanger)",
         [r"^print_post_inverter_", r"^print_tray_battery_", r"^print_breaker_shelf_", r"^print_bus_shelf_"])

    yp = cage.V13["plate_y"]
    for sx in (65, 179.7, 259.7, 311.8, 391.8, 506.5):
        ax.add_patch(Circle((sx, yp - 2), 5.0, fc=BLUE, ec="white", lw=1.2))
    for cx in (X0 + 8, D - B - 8):
        ax.add_patch(Circle((cx, Y0 + 291), 6.0, fc=RED, ec="white", lw=1.4))
    for gx in (X0 + 341.5, X0 + 421.5):
        ax.add_patch(Circle((gx, W - B - 3), 5.5, fc=GREEN, ec="white", lw=1.3))

    callout(ax, (259.7, yp - 2), (200, 115),
            "① Slide Plate into Post 0 & Post 1 Slots\n② Drive 6 × M4 × 8 Button Heads from column side\nthrough Bus Shelf wall into Plate's bottom M4 inserts",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=9.0)
    callout(ax, (X0 + 8, Y0 + 291), (175, 412),
            "③ Fit Post Clips 0 & 1 on Top of Posts (v12s):\n• 1 × M4 × 35 straight down into post top insert\n• 1 × 1/4\"-20 × 7/8\" Flat-Head into Top Width Rail (Y = 291 mm)",
            color=RED, bg=RED_LT, ec=RED, fs=8.8)
    callout(ax, (X0 + 341.5, W - B - 3), (385, 345),
            "④ Bolt Garmin Hanger Plates to Inboard Depth Rails:\n• Upper Plate: 2 × 1/4\"-20 × 1/2\" into Top Rail (X = 341.5, 421.5)\n• Lower Plate: 2 × 1/4\"-20 × 1/2\" into Bottom Rail (X = 341.5, 421.5)",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=8.8)

    path = os.path.join(OUT, "08-plate-simple.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# STEP 9: MULTIPLUS INVERTER & HEAVY DC WIRING DIAGRAM
# =====================================================================================================================
def step9():
    fig = plt.figure(figsize=(15, 9.2), dpi=120)
    banner(fig, "STEP 9", "Hang MultiPlus Inverter on Keyholes & Connect Heavy 4 AWG DC Leads",
           "Hook the MultiPlus onto the 4 proud M5 keyhole screws on the plate, snug with a 3 mm hex key, and wire the DC bus.",
           [("Tool: 3 mm Hex Key (MultiPlus Keyholes)", GREY_LT, DARK),
            ("4 AWG Red (+) & Black (−) Lugs", RED_LT, RED)])

    ax = fig.add_axes([0.04, 0.06, 0.92, 0.80])
    plan(ax, r"^victron_multiplus_",
         [r"^print_post_inverter_", r"^print_tray_battery_", r"^print_breaker_shelf_", r"^print_bus_shelf_", r"^print_plate_inverter_", r"^print_garmin_hanger"])

    mp = bb["victron_multiplus_long"]
    ax.text((mp.xmin + mp.xmax) / 2, (mp.ymin + mp.ymax) / 2,
            "① MultiPlus 12/800 or 12/1200\nHook 4 rear keyholes over the 4 proud M5×10 screws\non the plate, then snug all 4 screws from above",
            ha="center", va="center", fontsize=9.8, weight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.35", fc=BLUE, ec="white", lw=1.5))

    ax.annotate("", xy=(140, 265), xytext=(120, 155), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=RED))
    ax.annotate("", xy=(190, 265), xytext=(400, 155), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=RED))
    ax.annotate("", xy=(265, 225), xytext=(95, 115), arrowprops=dict(arrowstyle="-|>", lw=3.5, color="#222"))
    ax.annotate("", xy=(295, 225), xytext=(375, 115), arrowprops=dict(arrowstyle="-|>", lw=3.5, color="#222"))
    ax.annotate("", xy=(430, 330), xytext=(485, 270), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=RED))
    ax.annotate("", xy=(415, 315), xytext=(465, 270), arrowprops=dict(arrowstyle="-|>", lw=3.5, color="#222"))

    callout(ax, (140, 265), (135, 235),
            "② RED 4 AWG (+):\nEach Battery (+) → Bussmann 285 Breaker\n→ Positive (+) Bus Bar",
            color=RED, bg=RED_LT, ec=RED, fs=8.8)
    callout(ax, (280, 225), (285, 110),
            "③ BLACK 4 AWG (−):\nEach Battery (−) → SmartShunt Battery Stud\n→ Negative (−) Bus Bar",
            color=DARK, bg=GREY_LT, ec=DARK, fs=8.8)
    callout(ax, (475, 285), (465, 195),
            "④ MultiPlus 4 AWG (+ & −):\nFrom Bus Bars through 70×70 Front Plate\nWindow into MultiPlus DC Terminals",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.8)

    path = os.path.join(OUT, "09-inverter-simple.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


if __name__ == "__main__":
    bench_01_rails_panels()
    bench_02_inserts()
    bench_03_plate()
    bench_04_bus_garmin()
    step1_2()
    step3()
    step4()
    step6()
    step7()
    step8()
    step9()
