"""Generate a 13-page IKEA-style visual assembly manual (../manual/ikea/page-00..12.png) for IKEA-MANUAL.md.
Combines 3D isometric CAD views from cage.py with ultra-clean 2D IKEA callout diagrams, hardware pill boxes,
and checkmark/cross (OK / NO) visual rules so the box can be built with almost zero reading.

Run: .venv/bin/python ikea_manual.py v12s"""
import os, re, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, FancyBboxPatch, Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import cage, render

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "manual", "ikea")
os.makedirs(OUT, exist_ok=True)

asm = cage.build()
bb = {ch.name: ch.obj.val().BoundingBox() for ch in asm.children}
shapes = {ch.name: ch.obj.val() for ch in asm.children}
B, C, D, W, H = cage.B, cage.C, cage.out_D, cage.out_W, cage.out_H
X0, Y0 = cage.x_in0, cage.y_in0

BLACK = "#111111"
DARK = "#22252a"
GREY_LINE = "#666b73"
GREY_FILL = "#e6e8ec"
ORANGE = "#e4601f"
ORANGE_LT = "#fbe3d4"
BLUE = "#0058a3"       # Classic IKEA blue
BLUE_LT = "#dceefb"
YELLOW = "#ffdb00"     # Classic IKEA yellow
GREEN = "#1b7f37"
GREEN_LT = "#dafbe1"
RED = "#c92a2a"
RED_LT = "#ffe3e3"
GOLD = "#d99b00"
GOLD_LT = "#fff3bf"


def ikea_header(fig, step_num, title, tools_str, hw_badges):
    """Draw an iconic IKEA top strip with 3 non-overlapping full-width rows: Title, Tools, and Hardware Pills."""
    ax = fig.add_axes([0.02, 0.85, 0.96, 0.13])
    ax.set_xlim(0, 100); ax.set_ylim(0, 12); ax.axis("off")
    # Outer frame border
    ax.add_patch(Rectangle((0, 0.4), 100, 11.2, fc="white", ec=BLACK, lw=2.2))
    # Big black step box
    ax.add_patch(Rectangle((0, 0.4), 11.5, 11.2, fc=BLACK, ec=BLACK))
    ax.text(5.75, 6.0, str(step_num), color="white", fontsize=26, weight="bold", ha="center", va="center")
    # Row 1: Full-width Title
    ax.text(13.0, 9.5, title, color=BLACK, fontsize=14.0, weight="bold", ha="left", va="center")
    # Row 2: Full-width Tools
    ax.text(13.0, 6.6, f"TOOLS:  {tools_str}", color="#444", fontsize=8.8, weight="bold", ha="left", va="center")
    ax.plot([11.5, 100], [5.1, 5.1], color="#d0d4dc", lw=1.0)

    # Row 3: Dedicated full-width hardware pill bar (left-aligned starting at x=13.0)
    x_left = 13.0
    for code, qty, label, col, bg in hw_badges:
        pill_txt = f"{qty}×  {label}"
        w_box = max(11.0, len(pill_txt) * 0.43 + 4.8)
        ax.add_patch(FancyBboxPatch((x_left, 1.0), w_box, 3.6, boxstyle="round,pad=0.15", fc=bg, ec=col, lw=1.3))
        ax.add_patch(Circle((x_left + 1.8, 2.8), 1.25, fc=col, ec="white", lw=0.8))
        ax.text(x_left + 1.8, 2.8, code, color="white", fontsize=7.0, weight="bold", ha="center", va="center")
        ax.text(x_left + 3.5, 2.8, pill_txt, color=BLACK, fontsize=8.2, weight="bold", ha="left", va="center")
        x_left += w_box + 1.0


def render_3d_axes(ax, new_re, old_res=(), elev=25, azim=-52, only_names=None, zoom=1.15):
    """Render 3D CAD geometry into a subplot axis with new parts highlighted and old parts in light technical grey."""
    polys, cols = [], []
    for ch in asm.children:
        nm = ch.name
        if nm.startswith("icebox_"):
            continue
        if only_names is not None:
            if nm not in only_names:
                continue
            col = (0.90, 0.38, 0.12, 1.0)
        else:
            is_new = re.match(new_re, nm) is not None
            is_old = any(re.match(r, nm) for r in old_res)
            if not (is_new or is_old):
                continue
            if nm.startswith("lid_") and not is_new:
                continue
            if nm.startswith("panel_") and not is_new:
                continue
            if is_new:
                key = next((k for k in render.COLORS if nm.startswith(k)), "print")
                col = (0.15, 0.15, 0.15, 1.0) if nm.startswith("cube_") else render.COLORS[key]
            else:
                col = (0.78, 0.80, 0.82, 0.32)
        tri = render.part_tris(ch.obj.val())
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        shade = 0.55 + 0.45 * np.clip(n @ render.LIGHT, 0, 1)
        c = np.tile(np.array(col, dtype=float), (len(tri), 1))
        c[:, :3] *= shade[:, None]
        polys.append(tri); cols.append(c)
    tri, col = np.concatenate(polys), np.concatenate(cols)
    ax.add_collection3d(Poly3DCollection(tri, facecolors=col, edgecolors="none", linewidths=0))
    if only_names is not None:
        lo, hi = tri.reshape(-1, 3).min(0), tri.reshape(-1, 3).max(0)
        pad = 10.0
    else:
        lo, hi = np.array([0.0, 0.0, 0.0]), np.array([D, W, H + 20.0])
        pad = 12.0
    ax.set_xlim(lo[0] - pad, hi[0] + pad)
    ax.set_ylim(lo[1] - pad, hi[1] + pad)
    ax.set_zlim(lo[2] - pad, hi[2] + pad)
    ax.set_box_aspect(tuple(hi - lo + 2 * pad), zoom=zoom)
    ax.view_init(elev=elev, azim=azim)
    ax.set_proj_type("ortho")
    ax.set_axis_off()


def badge(ax, x, y, num_str, text, color=BLACK, bg="white", ec=BLACK, fs=9.5):
    """Draw a numbered IKEA action callout box."""
    ax.text(x, y, f"({num_str})  {text}", fontsize=fs, weight="bold", color=color, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.38", fc=bg, ec=ec, lw=1.6))


def callout(ax, xy, xytext, text, color=DARK, bg="white", ec=BLACK, fs=9.0):
    ax.annotate(
        text, xy=xy, xytext=xytext, fontsize=fs, weight="bold", color=color, ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.35", fc=bg, ec=ec, lw=1.5),
        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=ec, shrinkA=0, shrinkB=3)
    )


def ok_no_box(ax, x, y, w, h, ok_title, no_title):
    """Draw an IKEA-style OK vs NO rule box."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25", fc="#f8f9fa", ec=BLACK, lw=1.4))
    ax.add_patch(FancyBboxPatch((x + 1.5, y + h / 2 + 0.8), w - 3, h / 2 - 1.8, boxstyle="round,pad=0.2", fc=GREEN_LT, ec=GREEN, lw=1.2))
    ax.text(x + w / 2, y + 3 * h / 4, f"[OK]  {ok_title}", color=GREEN, fontsize=8.8, weight="bold", ha="center", va="center")
    ax.add_patch(FancyBboxPatch((x + 1.5, y + 1.0), w - 3, h / 2 - 1.8, boxstyle="round,pad=0.2", fc=RED_LT, ec=RED, lw=1.2))
    ax.text(x + w / 2, y + h / 4, f"[NO!]  {no_title}", color=RED, fontsize=8.8, weight="bold", ha="center", va="center")


# =====================================================================================================================
# PAGE 0: VISUAL PARTS & HARDWARE INVENTORY (H1..H11 & P1..P10)
# =====================================================================================================================
def page_00_inventory():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "0", "PARTS & HARDWARE CHECKLIST (COUNT BEFORE STARTING)",
                "Hex Keys: 2.5, 3, 4, 5 mm + 5/32\"  |  Soldering Iron (230°C)  |  Drills: 7/32\" (5.6 mm) & 1/4\" (6.4 mm)",
                [("H", "46", "Brass Inserts", GREEN, GREEN_LT),
                 ("H", "24", "Rail T-Nuts", BLUE, BLUE_LT),
                 ("P", "21", "3D Prints", ORANGE, ORANGE_LT)])

    ax = fig.add_axes([0.02, 0.03, 0.96, 0.80])
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    # Left half: Hardware (H1 .. H11) drawn with visual icons
    ax.add_patch(Rectangle((0, 0), 48.5, 98, fc="white", ec=BLACK, lw=1.8))
    ax.add_patch(Rectangle((0, 91), 48.5, 7, fc=BLACK, ec=BLACK))
    ax.text(24.25, 94.5, "FASTENERS & HEAT-SET INSERTS (CODES H1 – H11)", color="white", fontsize=12, weight="bold", ha="center", va="center")

    hw_list = [
        ("H1", "24×", "1/4\"-20 Drop-In T-Nut (6000N501)", "Roll into rail inner slots", BLUE, BLUE_LT),
        ("H2", "20×", "1/4\"-20 × 1/2\" Flat-Head (92210A537)", "All 6 mm walls → Rail T-nuts", BLUE, BLUE_LT),
        ("H3", "2×",  "1/4\"-20 × 7/8\" Flat-Head (92210A541)", "Top Post Clips → Width rails", BLUE, BLUE_LT),
        ("H4", "2×",  "1/4\"-20 × 7/8\" Button-Head (92949A541)", "Post Sills → Bottom width rails", BLUE, BLUE_LT),
        ("H5", "12×", "M4 Standard Insert, 7.9 mm (94180A353)", "Trays (10×) + Post tops (2×)", GREEN, GREEN_LT),
        ("H6", "16×", "M4 Short Insert, 4.7 mm (94180A351)", "6 mm Inverter Plate (14×) + Garmin (2×)", GREEN, GREEN_LT),
        ("H7", "18×", "M5 Insert, 6.7 mm (94180A361)", "Plate (8×), Shelves (4×), Bus Shelf (6×)", RED, RED_LT),
        ("H8", "12×", "M4 × 10 Button-Head (92095A190)", "Bus lip (6×), Shelf feet (4×), Garmin (2×)", DARK, GREY_FILL),
        ("H9", "14×", "M4 × 8 Button-Head (92095A189)", "Bus wall (6×), Cerbo (4×), Orion (4×)", DARK, GREY_FILL),
        ("H10", "2×", "M4 × 35 Button-Head (92095A199)", "Down through Post Clips into Posts", DARK, GREY_FILL),
        ("H11", "18×", "M5 Button-Heads + 10× Washers", "8× M5×10, 4× M5×8, 6× M5×12", RED, RED_LT),
    ]
    for i, (code, qty, name, use, col, bg) in enumerate(hw_list):
        y = 85.5 - i * 7.8
        ax.add_patch(FancyBboxPatch((1.5, y - 2.8), 45.5, 6.4, boxstyle="round,pad=0.15", fc=bg, ec=col, lw=1.2))
        ax.add_patch(Circle((4.5, y + 0.4), 2.1, fc=col, ec="white", lw=1))
        ax.text(4.5, y + 0.4, code, color="white", fontsize=8.5, weight="bold", ha="center", va="center")
        ax.text(8.0, y + 0.4, qty, color=BLACK, fontsize=11.5, weight="bold", ha="left", va="center")
        ax.text(14.5, y + 1.5, name, color=BLACK, fontsize=9.2, weight="bold", ha="left", va="center")
        ax.text(14.5, y - 1.3, use, color="#444", fontsize=8.0, ha="left", va="center")

    # Right half: Printed Parts (P1 .. P10) & Frame Parts (F1 .. F5)
    ax.add_patch(Rectangle((51.5, 0), 48.5, 98, fc="white", ec=BLACK, lw=1.8))
    ax.add_patch(Rectangle((51.5, 91), 48.5, 7, fc=BLACK, ec=BLACK))
    ax.text(75.75, 94.5, "3D-PRINTED PARTS (P1 – P10) & FRAME PARTS (F1 – F5)", color="white", fontsize=12, weight="bold", ha="center", va="center")

    parts_list = [
        ("P1", "2×", "Battery Trays (print_tray_battery_0 & _1)", "242 × 167 × 36 mm (Identical in v12s & v13)"),
        ("P2", "2×", "Breaker Drop Shelves (print_breaker_shelf_0 & _1)", "130 × 168 × 243 mm + 2× EPDM Foam Pads"),
        ("P3", "3×", "Bus Shelf Plates (0: 215mm, 1: 152mm, 2: 195mm)", "Note: Middle Plate 1 is 152 mm for 22.5\" box!"),
        ("P4", "6×", "Inverter Plate Tiles (00, 01, 10, 11, 20, 21)", "168.5 × 140 × 6 mm (Forms 505.5 × 256 mm plate)"),
        ("P5", "8×", "Inverter Plate Splines (plate_inverter_splines)", "60 × 18 × 3 mm (CA-glued across tile joints)"),
        ("P6", "2×", "Inverter Posts (print_post_inverter_0 & _1)", "254 × 24 × 18 mm (Back = 0, Front = 1)"),
        ("P7", "2×", "Inverter Post Clips (print_post_clip_0 & _1)", "40 × 20 × 28 mm (v12s only; not used in v13)"),
        ("P8", "2×", "Garmin Hanger Upper & Lower Plates", "130 × 149 mm (upper) + 130 × 127 mm (lower)"),
        ("P9", "1×", "GX Touch 50 Trim Bezel (print_touch_bezel)", "150 × 108 × 3 mm (Rear panel display frame)"),
        ("P10", "1×", "25 mm Rail-End Tap Guide (print_tool_tap_guide)", "46 × 46 × 32 mm cap — PRINT THIS FIRST!"),
        ("F1", "12×", "Aluminum Rails + 8× Corner Cubes (25.75 mm)", "4× Width (436.6), 4× Depth (520.0), 4× Height (230.2)"),
    ]
    for i, (code, qty, name, sub) in enumerate(parts_list):
        y = 85.5 - i * 7.8
        col = ORANGE if code.startswith("P") else "#495057"
        bg = ORANGE_LT if code.startswith("P") else GREY_FILL
        ax.add_patch(FancyBboxPatch((53.0, y - 2.8), 45.5, 6.4, boxstyle="round,pad=0.15", fc=bg, ec=col, lw=1.2))
        ax.add_patch(Circle((56.0, y + 0.4), 2.1, fc=col, ec="white", lw=1))
        ax.text(56.0, y + 0.4, code, color="white", fontsize=8.5, weight="bold", ha="center", va="center")
        ax.text(59.5, y + 0.4, qty, color=BLACK, fontsize=11.5, weight="bold", ha="left", va="center")
        ax.text(65.5, y + 1.5, name, color=BLACK, fontsize=9.2, weight="bold", ha="left", va="center")
        ax.text(65.5, y - 1.3, sub, color="#444", fontsize=8.0, ha="left", va="center")

    path = os.path.join(OUT, "page-00-inventory.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 1: CUT & TAP RAILS + CUT PANELS
# =====================================================================================================================
def page_01_rails_panels():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "1", "CUT & TAP RAILS + CUT PANELS & PORT HOLES",
                "Mitre Saw (80T Non-Ferrous)  |  1/4\"-20 Tap + Oil  |  Hole Saws: Ø22, Ø29, Ø60 mm + Jigsaw",
                [("P10", "1", "Tap Guide Cap", ORANGE, ORANGE_LT),
                 ("F1", "12", "Frame Rails", DARK, GREY_FILL)])

    # Top-left: Rail Cuts
    ax1 = fig.add_axes([0.03, 0.47, 0.54, 0.35])
    ax1.set_xlim(0, 680); ax1.set_ylim(0, 110); ax1.axis("off")
    ax1.text(0, 102, "(1)  CUT ONE END ONLY — KEEP FACTORY THREADS ON THE OTHER END", fontsize=11, weight="bold", color=BLACK)
    w_len = 436.6 * 0.68
    ax1.add_patch(Rectangle((10, 68), w_len, 18, fc=GREY_FILL, ec=BLACK, lw=1.4))
    ax1.text(18, 77, "4× WIDTH RAILS = 436.6 mm (17.19\") — DO NOT CUT", fontsize=9.2, weight="bold", va="center")
    full_d = 584.2 * 0.68; cut_d = 520.0 * 0.68
    ax1.add_patch(Rectangle((10, 36), cut_d, 18, fc=BLUE_LT, ec=BLUE, lw=1.5))
    ax1.add_patch(Rectangle((10 + cut_d, 36), full_d - cut_d, 18, fc=RED_LT, ec=RED, lw=1.2, ls="--"))
    ax1.plot([10 + cut_d, 10 + cut_d], [32, 58], color=RED, lw=2.5)
    ax1.text(18, 45, "4× DEPTH RAILS = 520.0 mm (20.47\")  [Cut 64.2 mm / 2.5\" off 1 end]", fontsize=9.2, weight="bold", va="center")
    ax1.text(10 + full_d + 10, 45, "Tap cut end 1/4\"-20", fontsize=9, weight="bold", color=RED, va="center")
    full_h = 508.0 * 0.68; cut_h = 230.2 * 0.68
    ax1.add_patch(Rectangle((10, 4), cut_h, 18, fc=GREEN_LT, ec=GREEN, lw=1.5))
    ax1.add_patch(Rectangle((10 + cut_h, 4), full_h - cut_h, 18, fc=GREY_FILL, ec="#888", lw=1.0, ls="--"))
    ax1.text(16, 13, "4× HEIGHT = 230.2 mm", fontsize=9.2, weight="bold", va="center")
    ax1.text(10 + full_h + 10, 13, "Practice tapping on the 4 offcuts first!", fontsize=9, weight="bold", color=GREEN, va="center")

    # Top-right: Tap Guide + OK/NO rule
    ax2 = fig.add_axes([0.59, 0.47, 0.38, 0.35])
    ax2.set_xlim(0, 100); ax2.set_ylim(0, 100); ax2.axis("off")
    ax2.text(2, 93, "(2)  SLIP TAP GUIDE (P10) OVER CUT END", fontsize=11, weight="bold", color=BLACK)
    ax2.add_patch(Rectangle((6, 36), 36, 30, fc=GREY_FILL, ec=BLACK, lw=1.5))
    ax2.add_patch(Polygon([(30, 28), (58, 28), (58, 74), (30, 74), (30, 66), (42, 66), (42, 36), (30, 36)],
                          closed=True, fc=ORANGE, ec=BLACK, lw=1.5))
    ax2.add_patch(Rectangle((42, 47), 16, 8, fc="white", ec=BLACK, lw=1))
    ax2.add_patch(Rectangle((34, 48.5), 48, 5, fc=BLUE, ec=BLACK, lw=1.2))
    ax2.text(46, 80, "P10 Tap Guide", fontsize=9.5, weight="bold", color=ORANGE, ha="center")
    ok_no_box(ax2, 4, 0, 92, 24, "Use P10 Guide + Cutting Oil; back out 1/4 turn every 1/2 turn",
              "Never tap freehand without the P10 guide or dry without oil")

    # Bottom-left: Front Panel Cutout Map
    ax3 = fig.add_axes([0.03, 0.03, 0.54, 0.41])
    ax3.set_aspect("equal"); ax3.axis("off")
    pw, ph = 444.0, 237.0
    ax3.add_patch(Rectangle((0, 0), pw, ph, fc="#343a40", ec=BLACK, lw=2))
    ax3.text(pw / 2, ph + 16, "(3)  FRONT PANEL CUTOUTS — 444 × 237 mm  (X from Inboard Left Edge, Z from Bottom)",
             fontsize=10.2, weight="bold", ha="center", color=BLACK)
    ports = [
        ("L14-30\nØ60\n(39,50)", 39, 50, "c", 60, GOLD_LT, GOLD),
        ("L14-30\nØ60\n(39,120)", 39, 120, "c", 60, GOLD_LT, GOLD),
        ("12V Ø29\n(39,175)", 39, 175, "c", 29, BLUE_LT, BLUE),
        ("SB50\n48×37\n(92,40)", 92, 40, "r", (48, 37), RED_LT, RED),
        ("SB50\n48×37\n(92,96)", 92, 96, "r", (48, 37), RED_LT, RED),
        ("USB Ø22\n(92,140)", 92, 140, "c", 22, GREEN_LT, GREEN),
        ("USB Ø22\n(92,173)", 92, 173, "c", 22, GREEN_LT, GREEN),
        ("12V Ø29\n(124,135)", 124, 135, "c", 29, BLUE_LT, BLUE),
        ("12V Ø29\n(124,175)", 124, 175, "c", 29, BLUE_LT, BLUE),
        ("SB175\n26×56\n(247,88)", 247, 88, "r", (26, 56), ORANGE_LT, ORANGE),
    ]
    for lbl, x, z, kind, sz, fc, ec in ports:
        if kind == "c":
            ax3.add_patch(Circle((x, z), sz / 2, fc=fc, ec=ec, lw=1.5))
        else:
            w_, h_ = sz
            ax3.add_patch(Rectangle((x - w_ / 2, z - h_ / 2), w_, h_, fc=fc, ec=ec, lw=1.5))
        ax3.text(x, z, lbl, ha="center", va="center", fontsize=5.8, weight="bold", color=BLACK)
    ax3.text(-8, ph / 2, "INBOARD EDGE (X = 0)", rotation=90, ha="right", va="center", fontsize=8.5, weight="bold", color=BLUE)
    ax3.set_xlim(-45, pw + 25); ax3.set_ylim(-25, ph + 32)

    # Bottom-right: Back & Side Panels
    ax4 = fig.add_axes([0.59, 0.03, 0.38, 0.41])
    ax4.set_aspect("equal"); ax4.axis("off")
    ax4.add_patch(Rectangle((0, 0), pw, ph, fc="#495057", ec=BLACK, lw=2))
    ax4.text(pw / 2, ph + 16, "(4)  BACK PANEL (444 × 237 mm) + 2× SIDE PANELS (527.5 × 237 mm)",
             fontsize=10.0, weight="bold", ha="center", color=BLACK)
    gx_x, gx_z, gx_w, gx_h = 72, 138, 128, 86
    ax4.add_patch(Rectangle((gx_x - gx_w / 2, gx_z - gx_h / 2), gx_w, gx_h, fc=ORANGE_LT, ec=ORANGE, lw=2))
    ax4.text(gx_x, gx_z, "GX Touch 50\n128 × 86 mm\n(80 mm from inboard rail,\n160 mm up from floor)",
             ha="center", va="center", fontsize=7.8, weight="bold", color=BLACK)
    ax4.set_xlim(-25, pw + 25); ax4.set_ylim(-25, ph + 32)

    path = os.path.join(OUT, "page-01-rails-panels.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 2: BATTERY TRAYS — HEAT-SET INSERTS (5 PER TRAY = 10 TOTAL)
# =====================================================================================================================
def page_02_tray_inserts():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "2", "BATTERY TRAYS (×2) — PRESS 10× M4 STANDARD INSERTS",
                "Soldering Iron (220–240°C PETG / 250–260°C ASA)  |  NO DRILLING NEEDED (Ø5.6 mm Holes Printed to Size)",
                [("P1", "2", "Battery Trays", ORANGE, ORANGE_LT),
                 ("H5", "10", "M4 Std 7.9mm (94180A353)", GREEN, GREEN_LT)])

    # Left: 3D CAD render of print_tray_battery_0
    ax3d = fig.add_axes([0.02, 0.10, 0.44, 0.72], projection="3d")
    render_3d_axes(ax3d, "", only_names={"print_tray_battery_0"}, elev=30, azim=-50, zoom=1.18)
    ax3d.set_title("3D Part View: print_tray_battery_0 & _1 (242 × 167 × 36 mm)", fontsize=11.5, weight="bold", pad=10)

    # Right: IKEA 2D Diagram + OK/NO flush check
    ax = fig.add_axes([0.48, 0.04, 0.50, 0.78])
    ax.set_xlim(-20, 270); ax.set_ylim(-85, 220); ax.axis("off")

    fd, fw = 242.0, 167.0
    ax.add_patch(Rectangle((0, 15), fd, fw, fc=ORANGE_LT, ec=BLACK, lw=2))
    ax.add_patch(Rectangle((6, 21), fd - 12, 140, fc="white", ec=BLACK, lw=1.2))
    ax.add_patch(Rectangle((0, 15 + fw - 21), fd, 21, fc="#f5b895", ec=BLACK, lw=1.5))
    ax.text(fd / 2, 15 + fw - 18, "21 mm THICK INBOARD WALL (Toward Center Column)", ha="center", va="center", fontsize=8.5, weight="bold")

    for hx in (81, 161):
        ax.add_patch(Circle((hx, 15 + fw - 8), 6.0, fc=GREEN, ec="white", lw=1.5))
    callout(ax, (81, 15 + fw - 8), (121, 128),
            "(1)  2× H5 (M4 Standard 7.9 mm) per tray\nPress STRAIGHT DOWN into top of 21 mm wall\n(X = 81 mm & 161 mm from back end)",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=9.0)

    for hx in (40, 100, 140, 200):
        ax.add_patch(Rectangle((hx - 4.5, 15 + fw - 2), 9, 7, fc=GREEN, ec=BLACK, lw=1.2))
    callout(ax, (140, 15 + fw + 3), (121, 62),
            "(2)  3× H5 (M4 Standard 7.9 mm) per tray\nPress HORIZONTALLY into outer column face (Z = 17 mm):\n• Tray 0 (Back): X = 40, 100, 140 mm\n• Tray 1 (Front): X = 40, 120, 200 mm",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=8.8)

    for (cx, cy) in ((70, 18), (172, 18), (3, 44), (3, 155)):
        ax.add_patch(Circle((cx, cy), 4.5, fc="white", ec=BLUE, lw=1.6))
    callout(ax, (70, 18), (121, -18),
            "(3)  4× Countersunk 1/4\"-20 Holes Inside Pocket:\nDO NOT PUT INSERTS HERE! (Rail screws H2 go here in Step 8)",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.8)

    ok_no_box(ax, 5, -80, 232, 42,
              "Press every brass insert FLUSH with plastic surface",
              "Never leave insert proud or push 1/4\"-20 holes")

    path = os.path.join(OUT, "page-02-tray-inserts.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 3: BREAKER SHELVES, POSTS & GARMIN HANGER — HEAT-SET INSERTS & FOAM PADS
# =====================================================================================================================
def page_03_shelf_post_inserts():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "3", "DROP SHELVES, POSTS & GARMIN — INSERTS & FOAM PADS",
                "Soldering Iron (230°C)  |  7/32\" (5.6 mm) Drill Bit (for Garmin & Posts only)",
                [("H7", "4", "M5 6.7mm (Shelves)", RED, RED_LT),
                 ("H6", "2", "M4 Short 4.7mm (Garmin)", BLUE, BLUE_LT),
                 ("H5", "2", "M4 Std 7.9mm (Posts)", GREEN, GREEN_LT)])

    # Left: 3D view of Breaker Drop Shelf
    ax3d = fig.add_axes([0.02, 0.12, 0.36, 0.70], projection="3d")
    render_3d_axes(ax3d, "", only_names={"print_breaker_shelf_0"}, elev=26, azim=-48, zoom=1.18)
    ax3d.set_title("P2: Breaker Drop Shelf (×2)", fontsize=11.5, weight="bold", pad=8)

    # Middle: Breaker Shelf 2D top + Foam Pad
    ax1 = fig.add_axes([0.39, 0.05, 0.30, 0.77])
    ax1.set_xlim(-15, 185); ax1.set_ylim(-75, 225); ax1.axis("off")
    ax1.add_patch(Rectangle((20, 20), 130, 168, fc=ORANGE_LT, ec=BLACK, lw=1.8))
    ax1.add_patch(Rectangle((20, 20), 130, 6, fc=ORANGE, ec=BLACK, lw=1.2))
    ax1.add_patch(Rectangle((20, 20 + 147), 130, 21, fc="#f5b895", ec=BLACK, lw=1.2))
    for bx, by in ((53, 125), (110, 152)):
        ax1.add_patch(Circle((bx, by), 5.8, fc=RED, ec="white", lw=1.5))
    callout(ax1, (53, 125), (85, 82),
            "(1)  2× H7 (M5 6.7 mm) per shelf\nPress STRAIGHT DOWN into top face\n(No drilling — Ø6.4 mm printed)",
            color=RED, bg=RED_LT, ec=RED, fs=8.6)
    ax1.add_patch(Rectangle((5, -60), 160, 56, fc="#343a40", ec=BLACK, lw=1.6))
    ax1.text(85, -32, "(2)  PEEL & STICK 130 × 140 mm\nEPDM FOAM PAD UNDERNEATH\nthe flat bottom of each shelf plate now!",
             color="white", fontsize=8.5, weight="bold", ha="center", va="center")

    # Right: Garmin Hanger + Inverter Posts
    ax2 = fig.add_axes([0.70, 0.05, 0.28, 0.77])
    ax2.set_xlim(0, 180); ax2.set_ylim(-75, 225); ax2.axis("off")
    ax2.add_patch(Rectangle((25, 75), 130, 115, fc=ORANGE_LT, ec=BLACK, lw=1.8))
    ax2.text(90, 176, "P8: Upper Garmin Hanger", ha="center", fontsize=9.5, weight="bold")
    for gx_ in (47.5, 132.5):
        ax2.add_patch(Circle((gx_, 132), 5.5, fc=BLUE, ec="white", lw=1.5))
    callout(ax2, (47.5, 132), (90, 94),
            "(3)  Drill 2 pilots to Ø5.6 mm (7/32\")\nPress 2× H6 (M4 Short 4.7 mm)",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.4)

    for px, lbl in ((30, "P6: Post 0"), (120, "P6: Post 1")):
        ax2.add_patch(Rectangle((px, -60), 30, 105, fc=ORANGE_LT, ec=BLACK, lw=1.8))
        ax2.add_patch(Circle((px + 15, 45), 5.5, fc=GREEN, ec="white", lw=1.5))
        ax2.text(px + 15, -30, lbl, ha="center", va="center", rotation=90, fontsize=9, weight="bold")
    callout(ax2, (45, 45), (90, 14),
            "(4)  Drill top end to Ø5.6 mm (7/32\")\nPress 1× H5 (M4 Std 7.9 mm) in each post",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=8.2)

    path = os.path.join(OUT, "page-03-shelf-post-inserts.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 4: INVERTER PLATE SUB-ASSEMBLY (6 TILES + 8 SPLINES + 22 INSERTS + UNITS)
# =====================================================================================================================
def page_04_plate_subassembly():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "4", "INVERTER PLATE — GLUE 6 TILES, SET 22 INSERTS & MOUNT GEAR",
                "CA Glue  |  Drills: 7/32\" (5.6 mm) & 1/4\" (6.4 mm)  |  Soldering Iron  |  2.5 mm & 3 mm Hex Keys",
                [("H6", "14", "M4 Short 4.7mm (Ø5.6)", BLUE, BLUE_LT),
                 ("H7", "8", "M5 6.7mm (Ø6.4)", RED, RED_LT),
                 ("H9", "8", "M4×8 (Cerbo+Orion)", DARK, GREY_FILL)])

    W_pl, H_pl = 505.5, 256.0
    zp = 21.0; px0 = X0 + 18.0 - 10.0

    # Left: Column Face
    ax1 = fig.add_axes([0.02, 0.05, 0.47, 0.78])
    ax1.set_aspect("equal"); ax1.axis("off")
    ax1.text(W_pl / 2, H_pl + 38, "(1)  COLUMN FACE (Facing Batteries) — 14× H6 (Blue) + 4× H7 (Red)",
             ha="center", fontsize=11, weight="bold", color=BLACK)
    ax1.text(W_pl / 2, H_pl + 18, "Glue Tiles 00..21 + 4 Upper Splines  |  Drill Blue → Ø5.6 mm, Red → Ø6.4 mm",
             ha="center", fontsize=8.8, weight="bold", color=BLUE)
    ax1.add_patch(Rectangle((0, 0), W_pl, H_pl, fc=ORANGE_LT, ec=BLACK, lw=2))
    for col_i in range(3):
        for row_i in range(2):
            ax1.text(col_i * 168.5 + 84, row_i * 128 + 52, f"Tile {col_i}{row_i}", ha="center", va="center", fontsize=13, weight="bold", color="#d8bea8")
    for cx in (168.5, 337.0):
        ax1.plot([cx, cx], [0, H_pl], color=BLACK, lw=1.2, ls="--")
        for sz in (162, 218):
            ax1.add_patch(Rectangle((cx - 30, sz - 9), 60, 18, fc=ORANGE, ec=BLACK, lw=1))
    ax1.add_patch(Rectangle((0, 116), W_pl, 24, fc="#f5ceb0", ec=BLACK, lw=0.8, ls=":"))

    wx = (D - B - 18.0 - 4.0 - 70.0) - px0; wz = 42.0 - zp
    ax1.add_patch(FancyBboxPatch((wx, wz), 70, 70, boxstyle="round,pad=0,rounding_size=10", fc="white", ec=BLACK, lw=1.5))
    ax1.text(wx + 35, wz + 35, "70×70\nWindow", ha="center", va="center", fontsize=8, weight="bold")

    sill_xs = [32.0, 146.7, 226.7, 278.8, 358.8, 473.5]
    for sx in sill_xs:
        ax1.add_patch(Circle((sx, 7.0), 6.5, fc=BLUE, ec="white", lw=1.3))
    callout(ax1, (sill_xs[2], 7.0), (W_pl / 2, -40),
            "6× H6 (M4 Short) along bottom edge (Z = 7 mm) — Leave empty for Step 11",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.5)

    units_info = [
        ("mppt", 50.0, 80.0, "MPPT 100/30\n4× H7 (M5) + 4× M5×8\n(Leave 3mm proud & hang)", RED, RED_LT),
        ("cerbo", 205.0, 188.0, "Cerbo GX\n4× H6 (M4 Short)\n+ 4× H9 (M4×8)", BLUE, BLUE_LT),
        ("orion", 390.0, 118.0, "Orion XS\n4× H6 (M4 Short)\n+ 4× H9 (M4×8)", BLUE, BLUE_LT),
    ]
    for ukey, x0_box, z0_box, lbl, col, bg in units_info:
        c = cage.COMPONENTS[ukey]
        ux, uz = x0_box - px0, z0_box - zp
        ax1.add_patch(Rectangle((ux, uz), c.w, c.h, fc=bg, ec=col, lw=1.6, ls="--", alpha=0.9))
        ax1.text(ux + c.w / 2, uz + c.h / 2, lbl, ha="center", va="center", fontsize=7.6, weight="bold")
        for (hu, hv) in cage.HOLES[ukey]:
            ax1.add_patch(Circle((ux + hu, uz + hv), 6.5, fc=col, ec="white", lw=1.3))
    ax1.set_xlim(-20, W_pl + 20); ax1.set_ylim(-65, H_pl + 55)

    # Right: Inverter Face + 3mm proud keyhole rule
    ax2 = fig.add_axes([0.51, 0.05, 0.47, 0.78])
    ax2.set_aspect("equal"); ax2.axis("off")
    ax2.text(W_pl / 2, H_pl + 38, "(2)  INVERTER FACE (Facing MultiPlus) — 4× H7 (M5) + 4× M5×10 LEFT 3 mm PROUD!",
             ha="center", fontsize=10.8, weight="bold", color=BLACK)
    ax2.text(W_pl / 2, H_pl + 18, "Glue 4 Lower Splines  |  Drill 4 Red Keyhole Pilots to Ø6.4 mm (1/4\") → Press 4× H7",
             ha="center", fontsize=8.8, weight="bold", color=RED)
    ax2.add_patch(Rectangle((0, 0), W_pl, H_pl, fc=ORANGE_LT, ec=BLACK, lw=2))
    inv_x0 = W_pl - ((cage.V13["inv_x"] - px0) + 375.0); inv_z0 = 22.0 - zp
    ax2.add_patch(Rectangle((inv_x0, inv_z0), 375.0, 249.0, fc=BLUE_LT, ec=BLUE, lw=1.6, ls="--", alpha=0.55))
    ax2.text(inv_x0 + 187.5, inv_z0 + 135, "MultiPlus Footprint\n(Hooks onto these 4 proud M5 screws in Step 12!)",
             ha="center", va="center", fontsize=9.5, weight="bold", color=BLUE)
    mp_pts = []
    for (hu, hv) in cage.HOLES["multiplus_1200_long"]:
        mx = W_pl - ((cage.V13["inv_x"] - px0) + hu); mz = inv_z0 + hv
        mp_pts.append((mx, mz))
        ax2.add_patch(Circle((mx, mz), 7.5, fc=RED, ec="white", lw=1.5))
    for cx in (W_pl - 168.5, W_pl - 337.0):
        ax2.plot([cx, cx], [0, H_pl], color=BLACK, lw=1.2, ls="--")
        for sz in (38, 94):
            ax2.add_patch(Rectangle((cx - 30, sz - 9), 60, 18, fc=ORANGE, ec=BLACK, lw=1))
    callout(ax2, mp_pts[0], (W_pl / 2, -40),
            "[OK] Drive 4× M5×10 + Washers (H11) into H7 inserts and LEAVE HEADS 3 mm PROUD!\n[NO!] Do NOT tighten flat — MultiPlus keyholes must slide behind the screw heads!",
            color=RED, bg=RED_LT, ec=RED, fs=8.3)
    ax2.set_xlim(-20, W_pl + 20); ax2.set_ylim(-65, H_pl + 55)

    path = os.path.join(OUT, "page-04-plate-subassembly.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 5: BUS SHELF (0 + 1 + 2) & GARMIN HANGER SUB-ASSEMBLIES
# =====================================================================================================================
def page_05_bus_subassembly():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "5", "BUS SHELF (PLATES 0 + 1 + 2) & GARMIN SUB-ASSEMBLIES",
                "CA Glue  |  1/4\" (6.4 mm) Drill  |  Soldering Iron  |  2.5 mm & 3 mm Hex Keys",
                [("P3", "3", "Bus Shelf 0, 1, 2", ORANGE, ORANGE_LT),
                 ("H7", "6", "M5 6.7mm Inserts", RED, RED_LT),
                 ("H11", "6", "M5×12 + 2 Washers", GOLD, GOLD_LT),
                 ("H8", "2", "M4×10 (Garmin)", BLUE, BLUE_LT)])

    ax1 = fig.add_axes([0.03, 0.06, 0.62, 0.76])
    ax1.set_aspect("equal"); ax1.axis("off")
    ax1.text(260, 195, "(1)  JOIN 3 BUS SHELF PLATES (521.5 mm TOTAL) — GLUE 20 mm WALL HALF-LAPS",
             ha="center", fontsize=11, weight="bold", color=BLACK)
    b0, b1, b2 = 194.7, 326.8, 521.5
    ax1.add_patch(Rectangle((0, 0), b0, 110, fc=ORANGE_LT, ec=BLACK, lw=1.8))
    ax1.add_patch(Rectangle((b0, 0), b1 - b0, 110, fc="#ffd8a8", ec=BLACK, lw=2.2))
    ax1.add_patch(Rectangle((b1, 0), b2 - b1, 110, fc=ORANGE_LT, ec=BLACK, lw=1.8))
    ax1.text(b0 / 2, 122, "Plate 0 (Back)\n214.7 mm", ha="center", fontsize=9, weight="bold")
    ax1.text((b0 + b1) / 2, 126, "Plate 1 (Middle)\n152.0 mm (Shortened!)", ha="center", fontsize=9, weight="bold", color=RED,
             bbox=dict(boxstyle="round,pad=0.25", fc=RED_LT, ec=RED))
    ax1.text((b1 + b2) / 2, 122, "Plate 2 (Front)\n194.7 mm", ha="center", fontsize=9, weight="bold")
    for lx in (b0, b1):
        ax1.add_patch(Rectangle((lx, 0), 20, 8, fc=ORANGE, ec=BLACK, lw=1))
        ax1.add_patch(Rectangle((lx, 102), 20, 8, fc=ORANGE, ec=BLACK, lw=1))
        ax1.text(lx + 10, -14, "CA Glue Lap", ha="center", va="top", fontsize=8.5, weight="bold", color=ORANGE)

    ax1.add_patch(Rectangle((205, 16), 120, 44, fc=BLUE_LT, ec=BLUE, lw=1.6))
    ax1.text(265, 38, "SmartShunt 500A\n2× H7 + 2× M5×12", ha="center", va="center", fontsize=8, weight="bold", color=BLUE)
    for sx in (217, 313):
        ax1.add_patch(Circle((sx, 38), 5.2, fc=RED, ec="white", lw=1.2))
    for bx, lbl in ((35, "Positive (+) Bus Bar\n2× H7 + 2× M5×12"), (345, "Negative (−) Bus Bar\n2× H7 + 2× M5×12")):
        ax1.add_patch(Rectangle((bx, 62), 145, 32, fc=GOLD_LT, ec=GOLD, lw=1.6))
        ax1.text(bx + 72.5, 78, lbl, ha="center", va="center", fontsize=8, weight="bold")
        for hx in (bx + 18, bx + 127):
            ax1.add_patch(Circle((hx, 78), 5.2, fc=RED, ec="white", lw=1.2))
    callout(ax1, (217, 38), (260, -52),
            "(2)  Use real SmartShunt & Bus Bars as drill template → Drill 6× Ø6.4 mm (1/4\")\n→ Press 6× H7 (M5) inserts → Bolt all 3 units down with 6× M5×12 (H11)!",
            color=RED, bg=RED_LT, ec=RED, fs=8.6)
    ax1.set_xlim(-30, 555); ax1.set_ylim(-80, 215)

    ax2 = fig.add_axes([0.67, 0.06, 0.30, 0.76])
    ax2.set_aspect("equal"); ax2.axis("off")
    ax2.text(80, 195, "(3)  GARMIN HANGER SUB-ASSEMBLY", ha="center", fontsize=11, weight="bold", color=BLACK)
    ax2.add_patch(Rectangle((15, 20), 130, 149, fc=ORANGE_LT, ec=BLACK, lw=1.8))
    ax2.add_patch(Rectangle((17.5, 42), 125, 75, fc="#343a40", ec=BLACK, lw=1.6))
    ax2.text(80, 80, "Garmin PowerSwitch\n(Click into bracket)", ha="center", va="center", fontsize=9, weight="bold", color="white")
    for gx_ in (37.5, 122.5):
        ax2.add_patch(Circle((gx_, 79.5), 5.5, fc=BLUE, ec="white", lw=1.5))
    callout(ax2, (37.5, 79.5), (80, -25),
            "Bolt bracket to P8 with\n2× H8 (M4 × 10 Button-Head)",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=9)
    ax2.set_xlim(-10, 170); ax2.set_ylim(-60, 215)

    path = os.path.join(OUT, "page-05-bus-subassembly.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 6: ASSEMBLE FRAME, SLIDE IN 4 PANELS & LOAD 24 DROP-IN T-NUTS
# =====================================================================================================================
def page_06_frame_tnuts():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "6", "BOLT FRAME, SLIDE IN 4 PANELS & LOAD 24× T-NUTS",
                "Corner-Cube Driver  |  Tape Measure / Caliper",
                [("F1", "12", "Rails + 8 Cubes", DARK, GREY_FILL),
                 ("H1", "24", "1/4\"-20 Drop-In T-Nuts", BLUE, BLUE_LT)])

    # Left: 3D view of Frame + Panels
    ax3d = fig.add_axes([0.01, 0.06, 0.43, 0.76], projection="3d")
    render_3d_axes(ax3d, r"^(cube_|bar_|panel_)", elev=24, azim=-50)
    ax3d.set_title("(1) Slide 4 Panels into Centre Slots Before Closing Corners", fontsize=10.5, weight="bold", pad=6)

    # Right: 2D T-Nut Map
    ax = fig.add_axes([0.46, 0.06, 0.52, 0.76])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY_FILL, ec=BLACK, lw=1.4))
    for cx in (0, D - B):
        for cy in (0, W - B):
            ax.add_patch(Rectangle((cx, cy), B, B, fc=BLACK, ec=BLACK))

    for x in (70, 172, 349.5, 451.5):
        ax.plot(X0 + x, B, marker="^", color=BLUE, ms=8.5)
        ax.text(X0 + x, B + 10, f"{x:.0f}", ha="center", fontsize=8, weight="bold", color=BLUE)
    for x in (81, 161, 360.5, 440.5):
        ax.plot(X0 + x, 4, marker="v", color=RED, ms=8.5)
        ax.text(X0 + x, -15, f"{x:.0f}", ha="center", fontsize=8, weight="bold", color=RED)
    for x in (341.5, 421.5):
        ax.plot(X0 + x, W - B, marker="v", color=BLUE, ms=8.5)
        ax.plot(X0 + x, W - 4, marker="^", color=RED, ms=8.5)
        ax.text(X0 + x, W - B - 16, f"{x:.1f}", ha="center", fontsize=8, weight="bold")
    for y in (29, 140, 198, 238, 281):
        ax.plot(B, Y0 + y, marker=">", color=BLUE, ms=8)
        ax.text(B + 9, Y0 + y, f"{y}", va="center", fontsize=8, weight="bold", color=BLUE)
        ax.plot(D - B, Y0 + y, marker="<", color=BLUE, ms=8)
        ax.text(D - B - 9, Y0 + y, f"{y}", ha="right", va="center", fontsize=8, weight="bold", color=BLUE)
    ax.plot(4, Y0 + 291, marker=">", color=RED, ms=8.5)
    ax.text(-8, Y0 + 291, "TOP: 291", ha="right", va="center", fontsize=8, weight="bold", color=RED)
    ax.plot(D - 4, Y0 + 291, marker="<", color=RED, ms=8.5)
    ax.text(D + 8, Y0 + 291, "TOP: 291", ha="left", va="center", fontsize=8, weight="bold", color=RED)

    ax.add_patch(FancyBboxPatch((80, 90), 410, 295, boxstyle="round,pad=0.35", fc="white", ec=BLACK, lw=1.4))
    ax.text(285, 358, "(2)  LOAD 24× H1 DROP-IN T-NUTS INTO INNER SLOTS", ha="center", fontsize=10.5, weight="bold")
    txt = (
        "BLUE = BOTTOM RAILS (16× H1 at Z = 12.5 mm):\n"
        " • Outboard (4×): X = 70, 172, 350, 452 mm\n"
        " • Back (5×):     Y = 29, 140, 198, 238, 281 mm\n"
        " • Front (5×):    Y = 29, 140, 198, 238, 281 mm\n"
        " • Inboard (2×):  X = 341.5, 421.5 mm\n\n"
        "RED = TOP RAILS (8× H1 at Z = 269.2 mm, v12s):\n"
        " • Outboard (4×): X = 81, 161, 360.5, 440.5 mm\n"
        " • Back & Front (2×): Y = 291 mm each\n"
        " • Inboard (2×):  X = 341.5, 421.5 mm"
    )
    ax.text(95, 212, txt, ha="left", va="center", fontsize=8.4, linespacing=1.38, weight="bold", color=DARK)
    ax.set_xlim(-75, D + 75); ax.set_ylim(-45, W + 35)

    path = os.path.join(OUT, "page-06-frame-tnuts.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 7: INSTALL INVERTER POSTS (POST 0 & POST 1)
# =====================================================================================================================
def page_07_posts():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "7", "INSTALL INVERTER POSTS (POST 0 & POST 1)",
                "5/32\" Hex Key  |  Tape Measure",
                [("P6", "2", "Posts 0 & 1", ORANGE, ORANGE_LT),
                 ("H4", "2", "1/4\"-20 × 7/8\" Button-Head", BLUE, BLUE_LT)])

    ax3d = fig.add_axes([0.01, 0.06, 0.44, 0.76], projection="3d")
    render_3d_axes(ax3d, r"^print_post_inverter_", [r"^(cube_|bar_)"])
    ax3d.set_title("3D View: Posts Stand on Back & Front Width Rails", fontsize=11, weight="bold", pad=6)

    ax = fig.add_axes([0.47, 0.06, 0.50, 0.76])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY_FILL, ec=BLACK, lw=1.4))
    p0, p1 = bb["print_post_inverter_0"], bb["print_post_inverter_1"]
    for p in (p0, p1):
        ax.add_patch(Rectangle((p.xmin, p.ymin), p.xlen, p.ylen, fc=ORANGE, ec=BLACK, lw=1.5))
    yc = (p0.ymin + p0.ymax) / 2
    ax.add_patch(FancyArrowPatch((D * 0.5, Y0), (D * 0.5, yc), arrowstyle="<|-|>", mutation_scale=14, lw=1.6, color=BLACK))
    ax.text(D * 0.5, (Y0 + yc) / 2, "281 mm from Outboard Rail\n(to Post Centre & T-Nut)", ha="center", va="center",
            fontsize=9.5, weight="bold", bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=BLACK))

    callout(ax, (p0.xmax, yc), (165, 395), "(1)  Post 0 on BACK Rail\n(Slot faces Front)", color=ORANGE, bg=ORANGE_LT, ec=ORANGE)
    callout(ax, (p1.xmin, yc), (405, 395), "(2)  Post 1 on FRONT Rail\n(Slot faces Back)", color=ORANGE, bg=ORANGE_LT, ec=ORANGE)
    callout(ax, (p0.xmin + 4, yc), (285, 85),
            "(3)  Drive 1× H4 (1/4\"-20 × 7/8\" Button-Head) per post\nthrough lower sill hole (Z = 12.5 mm) into T-nut at Y = 281 mm",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=9.2)
    ax.set_xlim(-45, D + 45); ax.set_ylim(-35, W + 35)

    path = os.path.join(OUT, "page-07-posts.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 8: INSTALL BATTERY TRAYS (TRAY 0 & TRAY 1)
# =====================================================================================================================
def page_08_trays():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "8", "BOLT BATTERY TRAYS TO BOTTOM RAILS (8× H2 SCREWS)",
                "5/32\" Hex Key",
                [("P1", "2", "Trays 0 & 1", ORANGE, ORANGE_LT),
                 ("H2", "8", "1/4\"-20 × 1/2\" Flat-Head", BLUE, BLUE_LT)])

    ax3d = fig.add_axes([0.01, 0.06, 0.44, 0.76], projection="3d")
    render_3d_axes(ax3d, r"^print_tray_battery_", [r"^(cube_|bar_|print_post_inverter_)"])
    ax3d.set_title("3D View: Trays Pushed into Back & Front Outboard Corners", fontsize=11, weight="bold", pad=6)

    ax = fig.add_axes([0.47, 0.06, 0.50, 0.76])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY_FILL, ec=BLACK, lw=1.4))
    t0, t1 = bb["print_tray_battery_0"], bb["print_tray_battery_1"]
    for idx, (tr, lbl, x_nuts) in enumerate(((t0, "P1: Tray 0\n(Back)", (70, 172)), (t1, "P1: Tray 1\n(Front)", (349.5, 451.5)))):
        ax.add_patch(Rectangle((tr.xmin, tr.ymin), tr.xlen, tr.ylen, fc=ORANGE, ec=BLACK, lw=1.4))
        ax.add_patch(Rectangle((tr.xmin + 6, tr.ymin + 6), tr.xlen - 12, 140, fc="#fff5eb", ec=BLACK, lw=1))
        ax.text((tr.xmin + tr.xmax) / 2, tr.ymin + 76, lbl, ha="center", va="center", fontsize=10.5, weight="bold")
        for xn in x_nuts:
            ax.add_patch(Circle((X0 + xn, tr.ymin + 10), 6, fc=BLUE, ec="white", lw=1.2))
        for yn in (29, 140):
            bx = tr.xmin + 10 if idx == 0 else tr.xmax - 10
            ax.add_patch(Circle((bx, Y0 + yn), 6, fc=BLUE, ec="white", lw=1.2))

    callout(ax, (X0 + 172, t0.ymin + 10), (285, 255),
            "(1)  4× H2 (1/4\"-20 × 1/2\" Flat-Head) through OUTER wall\ninto Bottom Outboard Rail (X = 70, 172 & 349.5, 451.5)",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.8)
    callout(ax, (t0.xmin + 10, Y0 + 140), (285, 355),
            "(2)  4× H2 (1/4\"-20 × 1/2\" Flat-Head) through END walls\ninto Back & Front Width Rails (Y = 29 & 140 mm)",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.8)
    ok_no_box(ax, 55, 405, 460, 62,
              "All 8× H2 screw heads MUST sit FLUSH inside countersinks",
              "Never leave a screw head proud inside the battery pocket!")
    ax.set_xlim(-45, D + 45); ax.set_ylim(-35, W + 35)

    path = os.path.join(OUT, "page-08-trays.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 9: DROP IN BATTERIES FIRST, THEN CLAMP WITH BREAKER DROP SHELVES & BREAKERS
# =====================================================================================================================
def page_09_batteries_shelves():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "9", "DROP IN BATTERIES FIRST, THEN BOLT DROP SHELVES & BREAKERS",
                "2.5 mm Hex Key (H8 Foot Screws)  |  5/32\" Hex Key (H2 Hanger Screws)  |  3 mm Hex Key (H11 Breakers)",
                [("P2", "2", "Drop Shelves", ORANGE, ORANGE_LT),
                 ("H8", "4", "M4×10 (Feet FIRST)", GREEN, GREEN_LT),
                 ("H2", "4", "1/4-20×1/2\" (Hanger 2ND)", BLUE, BLUE_LT),
                 ("H11", "4", "M5×10 + Washers", RED, RED_LT)])

    ax3d = fig.add_axes([0.01, 0.06, 0.45, 0.76], projection="3d")
    render_3d_axes(ax3d, r"^(battery_|print_breaker_shelf_|power_breaker_shelf_)",
                   [r"^(cube_|bar_|print_post_inverter_|print_tray_battery_)"])
    ax3d.set_title("3D View: Batteries In First → Shelves Clamp On Top", fontsize=11, weight="bold", pad=6)

    # Right: IKEA Cross-Section showing exact sequence (1) Battery -> (2) Foot M4 -> (3) Top Hanger -> (4) Breaker
    ax = fig.add_axes([0.48, 0.06, 0.49, 0.76])
    ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), B, B, fc=GREY_FILL, ec=BLACK, lw=1.4))
    ax.add_patch(Rectangle((0, H - B), B, B, fc=GREY_FILL, ec=BLACK, lw=1.4))
    ax.add_patch(Polygon([(26, 0), (193, 0), (193, 36), (172, 36), (172, 6), (32, 6), (32, 36), (26, 36)],
                         closed=True, fc=ORANGE_LT, ec=BLACK, lw=1.5))
    ax.add_patch(Rectangle((32.5, 6), 139, 208, fc=BLUE_LT, ec=BLUE, lw=1.8))
    ax.text(102, 130, "(1)  LOWER BOTH\nSUPERPACK 60Ah\nBATTERIES IN FIRST!\n(Cannot pass under\nshelf once installed)",
            ha="center", va="center", fontsize=10, weight="bold", color=BLUE)
    ax.add_patch(Rectangle((32.5, 214), 139, 3, fc=BLACK, ec=BLACK))
    ax.add_patch(Polygon([(25, 215), (178, 215), (178, 36), (193, 36), (193, 42), (184, 42), (184, 239),
                          (178, 239), (178, 221), (31, 221), (31, 278.7), (25, 278.7)],
                         closed=True, fc=ORANGE, ec=BLACK, lw=1.5))
    ax.add_patch(Rectangle((117, 221), 49, 44, fc=GOLD, ec=BLACK, lw=1.5))
    ax.text(141.5, 243, "(4) Breaker\n2× M5×10", ha="center", va="center", fontsize=8, weight="bold")

    callout(ax, (186, 42), (118, 65),
            "(2)  TIGHTEN FOOT FIRST:\n2× H8 (M4 × 10) straight down\ninto 21 mm tray wall inserts",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=8.8)
    callout(ax, (25, 269.2), (122, 282),
            "(3)  TIGHTEN HANGER SECOND:\n2× H2 (1/4\"-20 × 1/2\") into Top Rail\n(Compresses foam pad 1 mm onto battery!)",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.8)
    ax.set_xlim(-15, 225); ax.set_ylim(-15, 315)

    path = os.path.join(OUT, "page-09-batteries-shelves.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 10: DROP IN ASSEMBLED BUS SHELF (6× M4 LIP SCREWS + 4× 1/4-20 RAIL SCREWS)
# =====================================================================================================================
def page_10_bus_shelf():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "10", "DROP IN ASSEMBLED BUS SHELF INTO CENTER COLUMN",
                "2.5 mm Hex Key (6× H8 Lip Screws)  |  5/32\" Hex Key (4× H2 End-Wall Rail Screws)",
                [("P3", "1", "Bus Shelf Assembly", ORANGE, ORANGE_LT),
                 ("H8", "6", "M4×10 (Into Trays)", GREEN, GREEN_LT),
                 ("H2", "4", "1/4-20×1/2\" (Into Rails)", BLUE, BLUE_LT)])

    ax3d = fig.add_axes([0.01, 0.06, 0.44, 0.76], projection="3d")
    render_3d_axes(ax3d, r"^(print_bus_shelf_|power_busbar_|power_shunt_|victron_smartshunt_)",
                   [r"^(cube_|bar_|print_post_inverter_|print_tray_battery_|battery_|print_breaker_shelf_|power_breaker_shelf_)"])
    ax3d.set_title("3D View: Bus Shelf Drops Between Trays & Posts", fontsize=11, weight="bold", pad=6)

    ax = fig.add_axes([0.47, 0.06, 0.50, 0.76])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY_FILL, ec=BLACK, lw=1.4))
    for nm, b_ in bb.items():
        if re.match(r"^(print_tray_battery_|print_post_inverter_)", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc="#eee", ec="#999", lw=0.8))
        elif re.match(r"^print_bus_shelf_", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc=ORANGE, ec=BLACK, lw=1.3))

    t0_x, t1_x = bb["print_tray_battery_0"].xmin, bb["print_tray_battery_1"].xmin
    lip_y = bb["print_bus_shelf_0"].ymin
    for hx in [t0_x + 40, t0_x + 100, t0_x + 140, t1_x + 40, t1_x + 120, t1_x + 200]:
        ax.add_patch(Circle((hx, lip_y + 4), 6.0, fc=GREEN, ec="white", lw=1.3))
    for yn in (198, 238):
        ax.add_patch(Circle((X0 + 6, Y0 + yn), 6.0, fc=BLUE, ec="white", lw=1.3))
        ax.add_patch(Circle((D - B - 6, Y0 + yn), 6.0, fc=BLUE, ec="white", lw=1.3))

    callout(ax, (t0_x + 100, lip_y + 4), (285, 330),
            "(1)  Drive 6× H8 (M4 × 10 Button-Head) horizontally\nthrough Bus Shelf lip into Tray 0 & Tray 1 M4 inserts",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=9.0)
    callout(ax, (X0 + 6, Y0 + 238), (285, 420),
            "(2)  Drive 4× H2 (1/4\"-20 × 1/2\" Flat-Head)\nthrough Back & Front end walls into Width Rails (Y = 198, 238)",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=9.0)
    ax.set_xlim(-45, D + 45); ax.set_ylim(-35, W + 35)

    path = os.path.join(OUT, "page-10-bus-shelf.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 11: SLIDE IN INVERTER PLATE, BOLT SILL, POST CLIPS & GARMIN HANGERS
# =====================================================================================================================
def page_11_plate_clips_garmin():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "11", "SLIDE IN INVERTER PLATE, LOCK CLIPS & MOUNT GARMIN HANGERS",
                "2.5 mm Hex Key (H9 Sill + H10 Clips)  |  5/32\" Hex Key (H3 Clips + H2 Garmin Plates)",
                [("H9", "6", "M4×8 (Plate Sill)", BLUE, BLUE_LT),
                 ("H10", "2", "M4×35 + 2× H3 (Clips)", RED, RED_LT),
                 ("H2", "4", "1/4-20×1/2\" (Garmin)", GREEN, GREEN_LT)])

    ax3d = fig.add_axes([0.01, 0.06, 0.44, 0.76], projection="3d")
    render_3d_axes(ax3d, r"^(print_plate_inverter_|victron_mppt_|victron_cerbo_|victron_orion_|print_post_clip_|print_garmin_hanger|garmin_powerswitch_hanger)",
                   [r"^(cube_|bar_|print_post_inverter_|print_tray_battery_|battery_|print_breaker_shelf_|power_breaker_shelf_|print_bus_shelf_)"])
    ax3d.set_title("3D View: Plate Slides Into Posts + Garmin on Inboard Rail", fontsize=10.5, weight="bold", pad=6)

    ax = fig.add_axes([0.47, 0.06, 0.50, 0.76])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY_FILL, ec=BLACK, lw=1.4))
    for nm, b_ in bb.items():
        if re.match(r"^(print_tray_battery_|print_bus_shelf_|print_post_inverter_)", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc="#eee", ec="#999", lw=0.8))
        elif re.match(r"^(print_plate_inverter_|victron_mppt_|victron_cerbo_|victron_orion_|print_garmin_hanger)", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc=ORANGE, ec=BLACK, lw=1.2))

    yp = cage.V13["plate_y"]
    for sx in (65, 179.7, 259.7, 311.8, 391.8, 506.5):
        ax.add_patch(Circle((sx, yp - 2), 5.5, fc=BLUE, ec="white", lw=1.2))
    for cx in (X0 + 8, D - B - 8):
        ax.add_patch(Circle((cx, Y0 + 291), 6.5, fc=RED, ec="white", lw=1.4))
    for gx in (X0 + 341.5, X0 + 421.5):
        ax.add_patch(Circle((gx, W - B - 3), 6.0, fc=GREEN, ec="white", lw=1.3))

    callout(ax, (259.7, yp - 2), (285, 110),
            "(1)  Slide Plate down into Post 0 & Post 1 slots\n(2)  Drive 6× H9 (M4 × 8) through Bus Shelf wall into Plate bottom band",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.8)
    callout(ax, (X0 + 8, Y0 + 291), (200, 415),
            "(3)  Post Clips P7 (v12s): 1× H10 (M4×35) down\n+ 1× H3 (1/4-20×7/8\") into Top Width Rail (Y = 291)",
            color=RED, bg=RED_LT, ec=RED, fs=8.6)
    callout(ax, (X0 + 341.5, W - B - 3), (365, 335),
            "(4)  Garmin Upper & Lower Plates (P8):\n4× H2 (1/4-20×1/2\") into Top & Bottom Inboard Rails\n(X = 341.5 & 421.5 mm)",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=8.6)
    ax.set_xlim(-45, D + 45); ax.set_ylim(-35, W + 35)

    path = os.path.join(OUT, "page-11-plate-clips-garmin.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 12: HOOK MULTIPLUS ON KEYHOLES, CONNECT 4 AWG DC LUGS, INSTALL PORTS & LID
# =====================================================================================================================
def page_12_multiplus_wiring_lid():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "12", "HANG MULTIPLUS ON KEYHOLES, CONNECT 4 AWG LUGS & FIT LID",
                "3 mm Hex Key (MultiPlus Keyholes)  |  10 mm / 13 mm Socket (M6 & M8 DC Studs)  |  Phillips Driver",
                [("H11", "4", "Snug M5×10 Keyholes", BLUE, BLUE_LT),
                 ("P9", "1", "GX Touch Bezel", ORANGE, ORANGE_LT),
                 ("CBL", "6", "4 AWG DC Cables", RED, RED_LT)])

    ax3d = fig.add_axes([0.01, 0.06, 0.44, 0.76], projection="3d")
    render_3d_axes(ax3d, r"^(victron_multiplus_|socket_|gx_touch|print_touch_bezel)",
                   [r"^(cube_|bar_|print_post_inverter_|print_tray_battery_|battery_|print_breaker_shelf_|power_breaker_shelf_|print_bus_shelf_|print_plate_inverter_|victron_mppt_|victron_cerbo_|victron_orion_|print_garmin_hanger)"])
    ax3d.set_title("3D View: MultiPlus Hung Inboard + Front Ports & Rear Display", fontsize=10.5, weight="bold", pad=6)

    ax = fig.add_axes([0.47, 0.06, 0.50, 0.76])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY_FILL, ec=BLACK, lw=1.4))
    for nm, b_ in bb.items():
        if re.match(r"^(print_tray_battery_|print_bus_shelf_|print_plate_inverter_|print_garmin_hanger)", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc="#eee", ec="#999", lw=0.8))
    mp = bb["victron_multiplus_long"]
    ax.add_patch(Rectangle((mp.xmin, mp.ymin), mp.xlen, mp.ylen, fc=BLUE, ec=BLACK, lw=1.6))
    ax.text((mp.xmin + mp.xmax) / 2, (mp.ymin + mp.ymax) / 2,
            "(1)  HOOK MULTIPLUS ONTO\n4 PROUD M5×10 SCREWS\n& SNUG FROM ABOVE!",
            ha="center", va="center", fontsize=9.5, weight="bold", color="white")

    ax.annotate("", xy=(140, 265), xytext=(120, 155), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=RED))
    ax.annotate("", xy=(190, 265), xytext=(400, 155), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=RED))
    ax.annotate("", xy=(265, 225), xytext=(95, 115), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=BLACK))
    ax.annotate("", xy=(295, 225), xytext=(375, 115), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=BLACK))
    ax.annotate("", xy=(430, 330), xytext=(485, 270), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=RED))
    ax.annotate("", xy=(415, 315), xytext=(465, 270), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=BLACK))

    callout(ax, (140, 265), (140, 232),
            "(2)  RED 4 AWG (+):\nBattery (+) → Breaker → (+) Bus Bar",
            color=RED, bg=RED_LT, ec=RED, fs=8.5)
    callout(ax, (280, 225), (285, 95),
            "(3)  BLACK 4 AWG (−):\nBattery (−) → SmartShunt → (−) Bus Bar",
            color=BLACK, bg=GREY_FILL, ec=BLACK, fs=8.5)
    callout(ax, (475, 285), (435, 195),
            "(4)  MultiPlus 4 AWG (+ & −)\nthrough 70×70 Front Plate Window",
            color=BLUE, bg=BLUE_LT, ec=BLUE, fs=8.5)
    callout(ax, (D - 4, 380), (415, 425),
            "(5)  Mount GX Touch 50 (Back),\n10 Front Ports & Top Lid Panel!",
            color=GREEN, bg=GREEN_LT, ec=GREEN, fs=8.5)
    ax.set_xlim(-45, D + 45); ax.set_ylim(-35, W + 35)

    path = os.path.join(OUT, "page-12-multiplus-wiring-lid.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


if __name__ == "__main__":
    page_00_inventory()
    page_01_rails_panels()
    page_02_tray_inserts()
    page_03_shelf_post_inserts()
    page_04_plate_subassembly()
    page_05_bus_subassembly()
    page_06_frame_tnuts()
    page_07_posts()
    page_08_trays()
    page_09_batteries_shelves()
    page_10_bus_shelf()
    page_11_plate_clips_garmin()
    page_12_multiplus_wiring_lid()
