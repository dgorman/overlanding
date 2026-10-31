"""Generate a 13-page IKEA-style visual assembly manual (../manual/ikea/page-00..12.png) for IKEA-MANUAL.md.
Uses macOS Verdana / Futura (IKEA's classic instruction fonts), Hardware Bag callouts (BAG A, BAG B, BAG C, BAG D),
minimal text badges, and graphic Warning (!) / Checkmark (✓) / Cross (✗) comparison boxes across every page.

Run: .venv/bin/python ikea_manual.py v12s"""
import os, re, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, FancyBboxPatch, Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import cage, render

# Register classic IKEA fonts (Verdana & Futura) from macOS Supplemental Fonts if present
for fp in (
    "/System/Library/Fonts/Supplemental/Verdana.ttf",
    "/System/Library/Fonts/Supplemental/Verdana Bold.ttf",
    "/System/Library/Fonts/Supplemental/Verdana Italic.ttf",
    "/System/Library/Fonts/Supplemental/Verdana Bold Italic.ttf",
    "/System/Library/Fonts/Supplemental/Futura.ttc",
):
    if os.path.exists(fp):
        fm.fontManager.addfont(fp)
matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.sans-serif"] = ["Verdana", "Futura", "Helvetica Neue", "DejaVu Sans"]

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


# =====================================================================================================================
# IKEA GRAPHIC PRIMITIVES: HARDWARE BAGS, CALLOUT PILLS & GRAPHIC WARNING (!) / OK (✓) / NO (✗) PANELS
# =====================================================================================================================
def draw_bag_icon(ax, x, y, w, h, bag_letter, col=BLUE):
    """Draw a miniature hardware zip-bag icon labeled 'BAG A', 'BAG B', etc."""
    # Main clear bag body
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04", fc="white", ec=col, lw=1.4))
    # Top zip-lock header strip
    ax.add_patch(Rectangle((x, y + h * 0.72), w, h * 0.28, fc=col, ec=col, lw=0.8))
    ax.plot([x + w * 0.12, x + w * 0.88], [y + h * 0.86, y + h * 0.86], color=YELLOW, lw=1.2)
    ax.text(x + w / 2, y + h * 0.36, f"BAG\n{bag_letter}", color=col, fontsize=6.5, weight="bold",
            ha="center", va="center", linespacing=0.9)


def ikea_header(fig, step_num, title, tools_str, hw_badges):
    """Draw an iconic IKEA top strip with 3 non-overlapping rows: Title, Tools, and Bag/Part Pills."""
    ax = fig.add_axes([0.02, 0.85, 0.96, 0.13])
    ax.set_xlim(0, 100); ax.set_ylim(0, 12); ax.axis("off")
    ax.add_patch(Rectangle((0, 0.4), 100, 11.2, fc="white", ec=BLACK, lw=2.2))
    ax.add_patch(Rectangle((0, 0.4), 11.0, 11.2, fc=BLACK, ec=BLACK))
    ax.text(5.5, 6.0, str(step_num), color="white", fontsize=27, weight="bold", ha="center", va="center")

    # Row 1: Punchy Title
    ax.text(12.8, 9.5, title, color=BLACK, fontsize=14.2, weight="bold", ha="left", va="center")
    # Row 2: Tools
    ax.text(12.8, 6.6, f"TOOLS:  {tools_str}", color="#444", fontsize=8.6, weight="bold", ha="left", va="center")
    ax.plot([11.0, 100], [5.1, 5.1], color="#d0d4dc", lw=1.0)

    # Row 3: Hardware Bag & Part Pills
    x_left = 12.8
    for bag_or_part, code, qty, label, col, bg in hw_badges:
        pill_txt = f"{code} × {qty}   {label}"
        w_box = max(13.0, len(pill_txt) * 0.44 + 6.2)
        ax.add_patch(FancyBboxPatch((x_left, 0.9), w_box, 3.8, boxstyle="round,pad=0.12", fc=bg, ec=col, lw=1.4))
        if bag_or_part.startswith("BAG"):
            b_let = bag_or_part.split()[-1]
            draw_bag_icon(ax, x_left + 0.4, 1.15, 3.2, 3.3, b_let, col=col)
        else:
            ax.add_patch(Circle((x_left + 2.0, 2.8), 1.35, fc=col, ec="white", lw=0.9))
            ax.text(x_left + 2.0, 2.8, bag_or_part, color="white", fontsize=6.8, weight="bold", ha="center", va="center")
        ax.text(x_left + 4.2, 2.8, pill_txt, color=BLACK, fontsize=8.2, weight="bold", ha="left", va="center")
        x_left += w_box + 1.0


def bag_callout(ax, xy_targets, xytext, bag, code, qty, sub="", col=BLUE, bg=BLUE_LT):
    """Draw a minimal IKEA hardware bag callout pill with arrows to target hole(s) — almost zero text."""
    if isinstance(xy_targets, tuple) and len(xy_targets) == 2 and not isinstance(xy_targets[0], (tuple, list)):
        xy_targets = [xy_targets]
    for xy in xy_targets:
        ax.annotate("", xy=xy, xytext=xytext,
                    arrowprops=dict(arrowstyle="-|>", lw=1.8, color=col, shrinkA=12, shrinkB=3))
    label = f"[{bag}]  {code} × {qty}"
    if sub:
        label += f"\n{sub}"
    ax.text(xytext[0], xytext[1], label, fontsize=9.2, weight="bold", color=BLACK, ha="center", va="center",
            linespacing=1.15, bbox=dict(boxstyle="round,pad=0.38", fc=bg, ec=col, lw=1.8))


def no_callout(ax, xy_targets, xytext, bad_code="A1", right_note=""):
    """Draw a bold IKEA 'DO NOT INSERT HERE' callout with '!' and NO hardware code."""
    if isinstance(xy_targets, tuple) and len(xy_targets) == 2 and not isinstance(xy_targets[0], (tuple, list)):
        xy_targets = [xy_targets]
    for xy in xy_targets:
        ax.annotate("", xy=xy, xytext=xytext,
                    arrowprops=dict(arrowstyle="-|>", lw=1.8, color=RED, shrinkA=12, shrinkB=3))
    txt = f"[!]  NO {bad_code}"
    if right_note:
        txt += f"   ({right_note})"
    ax.text(xytext[0], xytext[1], txt, fontsize=9.2, weight="bold", color=RED, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.36", fc=RED_LT, ec=RED, lw=1.8))


def draw_warning_triangle(ax, cx, cy, r):
    """Draw an iconic IKEA Warning Triangle with a bold '!' in the center."""
    pts = [(cx, cy + r * 0.95), (cx - r * 0.92, cy - r * 0.78), (cx + r * 0.92, cy - r * 0.78)]
    ax.add_patch(Polygon(pts, closed=True, fc=YELLOW, ec=BLACK, lw=2.2, joinstyle="round"))
    ax.text(cx, cy - r * 0.18, "!", color=BLACK, fontsize=20, weight="bold", ha="center", va="center")


def draw_check_badge(ax, cx, cy, r, ok=True):
    """Draw a circular vector checkmark (green) or vector X (red) badge without relying on font glyphs."""
    col = GREEN if ok else RED
    ax.add_patch(Circle((cx, cy), r, fc=col, ec="white", lw=1.2, zorder=5))
    if ok:
        ax.plot([cx - r * 0.45, cx - r * 0.08, cx + r * 0.48],
                [cy - r * 0.02, cy - r * 0.42, cy + r * 0.42],
                color="white", lw=2.3, solid_capstyle="round", zorder=6)
    else:
        d = r * 0.40
        ax.plot([cx - d, cx + d], [cy - d, cy + d], color="white", lw=2.3, solid_capstyle="round", zorder=6)
        ax.plot([cx - d, cx + d], [cy + d, cy - d], color="white", lw=2.3, solid_capstyle="round", zorder=6)


def draw_red_x(ax, x, y, w, h):
    """Draw a bold IKEA red 'X' across a bad graphic."""
    ax.plot([x, x + w], [y, y + h], color=RED, lw=3.2, zorder=6)
    ax.plot([x, x + w], [y + h, y], color=RED, lw=3.2, zorder=6)


def ikea_ux_panel( fig, rect, mode, ok_lbl, no_lbl ):
    """Create a dedicated IKEA Warning (!) + Visual GOOD (✓) vs BAD (✗) comparison box at `rect=[l,b,w,h]`."""
    ax = fig.add_axes(rect)
    ax.set_xlim(0, 100); ax.set_ylim(0, 32); ax.axis("off")

    # Outer IKEA frame
    ax.add_patch(FancyBboxPatch((0.8, 0.8), 98.4, 30.4, boxstyle="round,pad=0.3", fc="#f8f9fa", ec=BLACK, lw=2.0))
    # Left Warning (!) column
    ax.plot([16.5, 16.5], [0.8, 31.2], color=BLACK, lw=1.6)
    draw_warning_triangle(ax, 8.6, 16.5, 6.8)

    # Good (✓) sub-card (x = 18.5 .. 57.5)
    ax.add_patch(FancyBboxPatch((18.5, 2.5), 39.0, 27.0, boxstyle="round,pad=0.2", fc="white", ec=GREEN, lw=1.8))
    draw_check_badge(ax, 22.2, 25.5, 2.6, ok=True)
    ax.text(38.0, 5.2, ok_lbl, color=GREEN, fontsize=9.2, weight="bold", ha="center", va="center")

    # Bad (✗) sub-card (x = 59.5 .. 98.0)
    ax.add_patch(FancyBboxPatch((59.5, 2.5), 38.0, 27.0, boxstyle="round,pad=0.2", fc="white", ec=RED, lw=1.8))
    draw_check_badge(ax, 63.2, 25.5, 2.6, ok=False)
    ax.text(78.5, 5.2, no_lbl, color=RED, fontsize=9.2, weight="bold", ha="center", va="center")

    # Draw mode-specific mini cross-section graphics inside Good (center ~38, y=10..26) & Bad (center ~79, y=10..26)
    if mode == "insert_flush":
        # GOOD: plastic block + gold insert flush with top surface
        ax.add_patch(Rectangle((27, 10), 22, 11, fc=ORANGE_LT, ec=BLACK, lw=1.3))
        ax.add_patch(Rectangle((34.5, 13), 7, 8, fc=GOLD, ec=BLACK, lw=1.3))
        ax.plot([25, 51], [21, 21], color=GREEN, lw=1.8, ls="--")
        # BAD: plastic block + gold insert sticking up proud & crooked
        ax.add_patch(Rectangle((68, 10), 22, 11, fc=ORANGE_LT, ec=BLACK, lw=1.3))
        ax.add_patch(Rectangle((75.5, 16), 7, 9, fc=GOLD, ec=BLACK, lw=1.3))
        draw_red_x(ax, 72, 12, 14, 14)
    elif mode == "tap_guide":
        # GOOD: rail + orange P10 cap + straight 90° tap
        ax.add_patch(Rectangle((26, 11), 12, 10, fc=GREY_FILL, ec=BLACK, lw=1.2))
        ax.add_patch(Rectangle((35, 9.5), 7, 13, fc=ORANGE, ec=BLACK, lw=1.2))
        ax.plot([36, 51], [16, 16], color=BLUE, lw=3.0)
        # BAD: rail alone + crooked tap
        ax.add_patch(Rectangle((68, 11), 12, 10, fc=GREY_FILL, ec=BLACK, lw=1.2))
        ax.plot([76, 91], [15, 23], color=RED, lw=3.0)
        draw_red_x(ax, 72, 11, 16, 14)
    elif mode == "proud_3mm":
        # GOOD: plate + M5 screw head standing 3mm proud + keyhole slot
        ax.add_patch(Rectangle((28, 10), 6, 15, fc=ORANGE_LT, ec=BLACK, lw=1.2))
        ax.add_patch(Rectangle((34, 16), 5, 3, fc=DARK, ec=BLACK, lw=1))
        ax.add_patch(Rectangle((39, 13.5), 3, 8, fc=RED, ec=BLACK, lw=1.2))
        ax.text(46, 17.5, "3 mm", color=GREEN, fontsize=8, weight="bold", va="center")
        # BAD: screw tightened flat against plate
        ax.add_patch(Rectangle((70, 10), 6, 15, fc=ORANGE_LT, ec=BLACK, lw=1.2))
        ax.add_patch(Rectangle((76, 13.5), 3, 8, fc=RED, ec=BLACK, lw=1.2))
        draw_red_x(ax, 71, 11, 14, 13)
    elif mode == "csink_flush":
        # GOOD: V-countersink with flat-head screw flush
        ax.add_patch(Rectangle((27, 11), 22, 9, fc=ORANGE_LT, ec=BLACK, lw=1.2))
        ax.add_patch(Polygon([(34, 20), (42, 20), (39.5, 16), (36.5, 16)], closed=True, fc=BLUE, ec=BLACK, lw=1))
        ax.plot([25, 51], [20, 20], color=GREEN, lw=1.8, ls="--")
        # BAD: button-head / proud screw sticking above floor
        ax.add_patch(Rectangle((68, 11), 22, 9, fc=ORANGE_LT, ec=BLACK, lw=1.2))
        ax.add_patch(Rectangle((75, 20), 8, 4.5, fc=RED, ec=BLACK, lw=1.2))
        draw_red_x(ax, 72, 12, 14, 14)
    elif mode == "battery_first":
        # GOOD: 1. Battery -> 2. Shelf
        ax.add_patch(Rectangle((28, 10), 11, 12, fc=BLUE_LT, ec=BLUE, lw=1.4))
        ax.text(33.5, 16, "1", color=BLUE, fontsize=9, weight="bold", ha="center", va="center")
        ax.add_patch(Rectangle((41, 18), 10, 4, fc=ORANGE, ec=BLACK, lw=1.2))
        ax.text(46, 13, "2", color=ORANGE, fontsize=9, weight="bold", ha="center", va="center")
        # BAD: Shelf blocking battery
        ax.add_patch(Rectangle((71, 10), 14, 4, fc=ORANGE, ec=BLACK, lw=1.2))
        ax.add_patch(Rectangle((73, 16), 10, 9, fc=BLUE_LT, ec=RED, lw=1.4))
        draw_red_x(ax, 70, 10, 16, 15)
    else:
        # Generic clean graphic bars
        ax.add_patch(Rectangle((28, 12), 20, 9, fc=GREEN_LT, ec=GREEN, lw=1.5))
        ax.add_patch(Rectangle((69, 12), 20, 9, fc=RED_LT, ec=RED, lw=1.5))
        draw_red_x(ax, 72, 11, 14, 11)


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


# =====================================================================================================================
# PAGE 0: HARDWARE BAGS (BAG A..D) & 3D-PRINTED PARTS (P1..P10)
# =====================================================================================================================
def page_00_inventory():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "0", "HARDWARE BAGS (A – D) & PARTS CHECKLIST",
                "Hex Keys: 2.5, 3, 4, 5 mm + 5/32\"  |  Soldering Iron (230°C)  |  Drills: 7/32\" (5.6 mm) & 1/4\" (6.4 mm)",
                [("BAG A", "A1–A3", "46", "Brass Inserts", GREEN, GREEN_LT),
                 ("BAG B", "B1–B4", "48", "1/4\"-20 Rail HW", BLUE, BLUE_LT),
                 ("BAG C", "C1–C3", "28", "M4 Screws", DARK, GREY_FILL),
                 ("BAG D", "D1–D4", "28", "M5 Screws + Washers", RED, RED_LT)])

    ax = fig.add_axes([0.02, 0.03, 0.96, 0.80])
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    # Left half: 4 Hardware Bags (BAG A, BAG B, BAG C, BAG D)
    ax.add_patch(Rectangle((0, 0), 48.5, 98, fc="white", ec=BLACK, lw=1.8))
    ax.add_patch(Rectangle((0, 91), 48.5, 7, fc=BLACK, ec=BLACK))
    ax.text(24.25, 94.5, "HARDWARE BAGS (BAG A  •  BAG B  •  BAG C  •  BAG D)", color="white", fontsize=11.5, weight="bold", ha="center", va="center")

    bags = [
        ("A", "BAG A — BRASS HEAT-SET INSERTS (STEPS 2–5)", GREEN, GREEN_LT, [
            ("A1", "12×", "M4 Standard Insert, 7.9 mm (94180A353)"),
            ("A2", "16×", "M4 Short Insert, 4.7 mm (94180A351)"),
            ("A3", "18×", "M5 Insert, 6.7 mm (94180A361)"),
        ]),
        ("B", "BAG B — 1/4\"-20 RAIL FASTENERS (STEPS 6–11)", BLUE, BLUE_LT, [
            ("B1", "24×", "1/4\"-20 Drop-In T-Nut (6000N501)"),
            ("B2", "20×", "1/4\"-20 × 1/2\" Flat-Head (92210A537)"),
            ("B3", "2×",  "1/4\"-20 × 7/8\" Flat-Head (92210A541)"),
            ("B4", "2×",  "1/4\"-20 × 7/8\" Button-Head (92949A541)"),
        ]),
        ("C", "BAG C — M4 BUTTON-HEAD SCREWS (STEPS 4–11)", DARK, GREY_FILL, [
            ("C1", "12×", "M4 × 10 mm Button-Head (92095A190)"),
            ("C2", "14×", "M4 × 8 mm Button-Head (92095A189)"),
            ("C3", "2×",  "M4 × 35 mm Button-Head (92095A199)"),
        ]),
        ("D", "BAG D — M5 SCREWS & WASHERS (STEPS 4, 5, 9, 12)", RED, RED_LT, [
            ("D1", "8×",  "M5 × 10 mm + 8× Washers (92095A210)"),
            ("D2", "4×",  "M5 × 8 mm Button-Head (92095A209)"),
            ("D3", "6×",  "M5 × 12 mm + 2× Washers (92095A211)"),
        ]),
    ]
    y_cursor = 88.5
    for b_let, b_title, col, bg, items in bags:
        h_group = len(items) * 5.0 + 4.0
        ax.add_patch(FancyBboxPatch((1.2, y_cursor - h_group + 1.5), 46.1, h_group, boxstyle="round,pad=0.15", fc=bg, ec=col, lw=1.4))
        draw_bag_icon(ax, 2.2, y_cursor - 5.2, 4.5, 5.8, b_let, col=col)
        ax.text(8.0, y_cursor - 1.0, b_title, color=col, fontsize=8.8, weight="bold", ha="left", va="center")
        y_row = y_cursor - 4.7
        for code, qty, desc in items:
            ax.add_patch(Circle((9.4, y_row), 1.45, fc=col, ec="white", lw=0.8))
            ax.text(9.4, y_row, code, color="white", fontsize=7.2, weight="bold", ha="center", va="center")
            ax.text(11.8, y_row, qty, color=BLACK, fontsize=9.2, weight="bold", ha="left", va="center")
            ax.text(16.5, y_row, desc, color=BLACK, fontsize=8.3, weight="bold", ha="left", va="center")
            y_row -= 4.9
        y_cursor -= h_group + 1.5

    # Right half: Printed Parts (P1 .. P10) & Frame Parts (F1)
    ax.add_patch(Rectangle((51.5, 0), 48.5, 98, fc="white", ec=BLACK, lw=1.8))
    ax.add_patch(Rectangle((51.5, 91), 48.5, 7, fc=BLACK, ec=BLACK))
    ax.text(75.75, 94.5, "3D-PRINTED PARTS (P1 – P10) & FRAME RAILS (F1)", color="white", fontsize=11.5, weight="bold", ha="center", va="center")

    parts_list = [
        ("P1", "2×", "Battery Trays (print_tray_battery_0 & _1)", "242 × 167 × 36 mm (Identical in v12s & v13)"),
        ("P2", "2×", "Breaker Drop Shelves (print_breaker_shelf_0 & _1)", "130 × 168 × 243 mm + 2× EPDM Foam Pads"),
        ("P3", "3×", "Bus Shelf Plates (0: 215mm, 1: 152mm, 2: 195mm)", "Middle Plate 1 is 152 mm for 22.5\" box"),
        ("P4", "6×", "Inverter Plate Tiles (00, 01, 10, 11, 20, 21)", "168.5 × 140 × 6 mm (505.5 × 256 mm total)"),
        ("P5", "8×", "Inverter Plate Splines (plate_inverter_splines)", "60 × 18 × 3 mm (Glued across tile joints)"),
        ("P6", "2×", "Inverter Posts (print_post_inverter_0 & _1)", "254 × 24 × 18 mm (Back = 0, Front = 1)"),
        ("P7", "2×", "Inverter Post Clips (print_post_clip_0 & _1)", "40 × 20 × 28 mm (v12s only)"),
        ("P8", "2×", "Garmin Hanger Upper & Lower Plates", "130 × 149 mm (upper) + 130 × 127 mm (lower)"),
        ("P9", "1×", "GX Touch 50 Trim Bezel (print_touch_bezel)", "150 × 108 × 3 mm (Rear panel display frame)"),
        ("P10", "1×", "25 mm Rail-End Tap Guide (print_tool_tap_guide)", "46 × 46 × 32 mm cap — PRINT FIRST"),
        ("F1", "12×", "Aluminum Rails + 8× Corner Cubes (25.75 mm)", "4× Width (436.6), 4× Depth (520.0), 4× Height (230.2)"),
    ]
    for i, (code, qty, name, sub) in enumerate(parts_list):
        y = 85.5 - i * 7.8
        col = ORANGE if code.startswith("P") else "#495057"
        bg = ORANGE_LT if code.startswith("P") else GREY_FILL
        ax.add_patch(FancyBboxPatch((53.0, y - 2.8), 45.5, 6.4, boxstyle="round,pad=0.15", fc=bg, ec=col, lw=1.2))
        ax.add_patch(Circle((56.0, y + 0.4), 2.1, fc=col, ec="white", lw=1))
        ax.text(56.0, y + 0.4, code, color="white", fontsize=8.2, weight="bold", ha="center", va="center")
        ax.text(59.5, y + 0.4, qty, color=BLACK, fontsize=11.0, weight="bold", ha="left", va="center")
        ax.text(65.5, y + 1.5, name, color=BLACK, fontsize=8.8, weight="bold", ha="left", va="center")
        ax.text(65.5, y - 1.3, sub, color="#444", fontsize=7.8, ha="left", va="center")

    path = os.path.join(OUT, "page-00-inventory.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 1: CUT & TAP RAILS + CUT PANELS
# =====================================================================================================================
def page_01_rails_panels():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "1", "CUT & TAP RAILS (F1) + CUT PANELS",
                "Mitre Saw (80T)  |  1/4\"-20 Tap + Cutting Oil  |  Hole Saws: Ø22, Ø29, Ø60 mm + Jigsaw",
                [("PART", "P10", "1", "Tap Guide Cap", ORANGE, ORANGE_LT),
                 ("PART", "F1", "12", "Frame Rails", DARK, GREY_FILL)])

    ax1 = fig.add_axes([0.03, 0.47, 0.54, 0.35])
    ax1.set_xlim(0, 680); ax1.set_ylim(0, 110); ax1.axis("off")
    ax1.text(0, 102, "1.  CUT ONE END ONLY — KEEP FACTORY THREADS ON OTHER END", fontsize=10.5, weight="bold", color=BLACK)
    w_len = 436.6 * 0.68
    ax1.add_patch(Rectangle((10, 68), w_len, 18, fc=GREY_FILL, ec=BLACK, lw=1.4))
    ax1.text(18, 77, "4× WIDTH = 436.6 mm (NO CUT)", fontsize=9.2, weight="bold", va="center")
    full_d = 584.2 * 0.68; cut_d = 520.0 * 0.68
    ax1.add_patch(Rectangle((10, 36), cut_d, 18, fc=BLUE_LT, ec=BLUE, lw=1.5))
    ax1.add_patch(Rectangle((10 + cut_d, 36), full_d - cut_d, 18, fc=RED_LT, ec=RED, lw=1.2, ls="--"))
    ax1.plot([10 + cut_d, 10 + cut_d], [32, 58], color=RED, lw=2.5)
    ax1.text(18, 45, "4× DEPTH = 520.0 mm  (−64.2 mm / −2.5\")", fontsize=9.2, weight="bold", va="center")
    ax1.text(10 + full_d + 10, 45, "Tap 1/4\"-20", fontsize=9, weight="bold", color=RED, va="center")
    full_h = 508.0 * 0.68; cut_h = 230.2 * 0.68
    ax1.add_patch(Rectangle((10, 4), cut_h, 18, fc=GREEN_LT, ec=GREEN, lw=1.5))
    ax1.add_patch(Rectangle((10 + cut_h, 4), full_h - cut_h, 18, fc=GREY_FILL, ec="#888", lw=1.0, ls="--"))
    ax1.text(16, 13, "4× HEIGHT = 230.2 mm", fontsize=9.2, weight="bold", va="center")
    ax1.text(10 + full_h + 10, 13, "Tap 1/4\"-20", fontsize=9, weight="bold", color=GREEN, va="center")

    ax2 = fig.add_axes([0.59, 0.61, 0.38, 0.21])
    ax2.set_xlim(0, 100); ax2.set_ylim(22, 95); ax2.axis("off")
    ax2.text(2, 88, "2.  TAP CUT END WITH P10 GUIDE", fontsize=10.5, weight="bold", color=BLACK)
    ax2.add_patch(Rectangle((8, 36), 34, 28, fc=GREY_FILL, ec=BLACK, lw=1.5))
    ax2.add_patch(Polygon([(30, 28), (58, 28), (58, 72), (30, 72), (30, 64), (42, 64), (42, 36), (30, 36)],
                          closed=True, fc=ORANGE, ec=BLACK, lw=1.5))
    ax2.add_patch(Rectangle((42, 46), 16, 8, fc="white", ec=BLACK, lw=1))
    ax2.add_patch(Rectangle((34, 47.5), 48, 5, fc=BLUE, ec=BLACK, lw=1.2))
    ax2.text(44, 77, "P10", fontsize=9.5, weight="bold", color=ORANGE, ha="center")

    ikea_ux_panel(fig, [0.59, 0.44, 0.38, 0.16], "tap_guide", "P10 + OIL (90°)", "NO! FREEHAND")

    ax3 = fig.add_axes([0.03, 0.03, 0.54, 0.40])
    ax3.set_aspect("equal"); ax3.axis("off")
    pw, ph = 444.0, 237.0
    ax3.add_patch(Rectangle((0, 0), pw, ph, fc="#343a40", ec=BLACK, lw=2))
    ax3.text(pw / 2, ph + 14, "3.  FRONT PANEL — 444 × 237 mm  (X, Z in mm)", fontsize=10.0, weight="bold", ha="center")
    ports = [
        ("Ø60\n(39,50)", 39, 50, "c", 60, GOLD_LT, GOLD),
        ("Ø60\n(39,120)", 39, 120, "c", 60, GOLD_LT, GOLD),
        ("Ø29\n(39,175)", 39, 175, "c", 29, BLUE_LT, BLUE),
        ("48×37\n(92,40)", 92, 40, "r", (48, 37), RED_LT, RED),
        ("48×37\n(92,96)", 92, 96, "r", (48, 37), RED_LT, RED),
        ("Ø22\n(92,140)", 92, 140, "c", 22, GREEN_LT, GREEN),
        ("Ø22\n(92,173)", 92, 173, "c", 22, GREEN_LT, GREEN),
        ("Ø29\n(124,135)", 124, 135, "c", 29, BLUE_LT, BLUE),
        ("Ø29\n(124,175)", 124, 175, "c", 29, BLUE_LT, BLUE),
        ("26×56\n(247,88)", 247, 88, "r", (26, 56), ORANGE_LT, ORANGE),
    ]
    for lbl, x, z, kind, sz, fc, ec in ports:
        if kind == "c":
            ax3.add_patch(Circle((x, z), sz / 2, fc=fc, ec=ec, lw=1.5))
        else:
            w_, h_ = sz
            ax3.add_patch(Rectangle((x - w_ / 2, z - h_ / 2), w_, h_, fc=fc, ec=ec, lw=1.5))
        ax3.text(x, z, lbl, ha="center", va="center", fontsize=6.0, weight="bold", color=BLACK)
    ax3.text(-8, ph / 2, "INBOARD (X=0)", rotation=90, ha="right", va="center", fontsize=8.5, weight="bold", color=BLUE)
    ax3.set_xlim(-45, pw + 25); ax3.set_ylim(-20, ph + 30)

    ax4 = fig.add_axes([0.59, 0.03, 0.38, 0.39])
    ax4.set_aspect("equal"); ax4.axis("off")
    ax4.add_patch(Rectangle((0, 0), pw, ph, fc="#495057", ec=BLACK, lw=2))
    ax4.text(pw / 2, ph + 14, "4.  BACK PANEL (444 × 237) + 2× SIDES (527.5 × 237)", fontsize=9.5, weight="bold", ha="center")
    gx_x, gx_z, gx_w, gx_h = 72, 138, 128, 86
    ax4.add_patch(Rectangle((gx_x - gx_w / 2, gx_z - gx_h / 2), gx_w, gx_h, fc=ORANGE_LT, ec=ORANGE, lw=2))
    ax4.text(gx_x, gx_z, "GX Touch 50\n128 × 86 mm\n(X=72, Z=138)", ha="center", va="center", fontsize=8.0, weight="bold")
    ax4.set_xlim(-20, pw + 20); ax4.set_ylim(-20, ph + 30)

    path = os.path.join(OUT, "page-01-rails-panels.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 2: BATTERY TRAYS — PRESS 10× A1 INSERTS (BAG A)
# =====================================================================================================================
def page_02_tray_inserts():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "2", "BATTERY TRAYS (P1 × 2) — PRESS 10× A1 INSERTS",
                "Soldering Iron (220–240°C)  |  NO DRILLING",
                [("PART", "P1", "2", "Battery Trays", ORANGE, ORANGE_LT),
                 ("BAG A", "A1", "10", "M4 Standard 7.9 mm", GREEN, GREEN_LT)])

    # Left: 3D CAD render of print_tray_battery_0
    ax3d = fig.add_axes([0.02, 0.10, 0.44, 0.72], projection="3d")
    render_3d_axes(ax3d, "", only_names={"print_tray_battery_0"}, elev=30, azim=-50, zoom=1.18)
    ax3d.set_title("P1 × 2  (print_tray_battery_0 & _1)", fontsize=11.5, weight="bold", pad=10)

    # Top-Right: Clean IKEA 2D Diagram with Bag Callouts (minimal text!)
    ax = fig.add_axes([0.48, 0.24, 0.50, 0.59])
    ax.set_xlim(-25, 265); ax.set_ylim(-35, 205); ax.axis("off")

    fd, fw = 242.0, 167.0
    ax.add_patch(Rectangle((0, 15), fd, fw, fc=ORANGE_LT, ec=BLACK, lw=2))
    ax.add_patch(Rectangle((6, 21), fd - 12, 140, fc="white", ec=BLACK, lw=1.2))
    ax.add_patch(Rectangle((0, 15 + fw - 21), fd, 21, fc="#f5b895", ec=BLACK, lw=1.5))
    ax.text(fd / 2, 15 + fw - 18, "21 mm INBOARD WALL", ha="center", va="center", fontsize=8.5, weight="bold")

    # (1) 2x A1 on top of 21 mm wall
    top_pts = [(81, 15 + fw - 8), (161, 15 + fw - 8)]
    for hx, hy in top_pts:
        ax.add_patch(Circle((hx, hy), 6.2, fc=GREEN, ec="white", lw=1.5, zorder=4))
    bag_callout(ax, top_pts, (70, 118), "BAG A", "A1", "2", sub="TOP (×2 Trays = 4)", col=GREEN, bg=GREEN_LT)

    # (2) 3x A1 horizontally into outer column face
    side_pts = [(40, 15 + fw + 3), (100, 15 + fw + 3), (140, 15 + fw + 3), (200, 15 + fw + 3)]
    for hx, hy in side_pts:
        ax.add_patch(Rectangle((hx - 4.5, hy - 5), 9, 7, fc=GREEN, ec=BLACK, lw=1.2, zorder=4))
    bag_callout(ax, [(100, 15 + fw + 3), (140, 15 + fw + 3)], (175, 118),
                "BAG A", "A1", "3", sub="SIDE (×2 Trays = 6)", col=GREEN, bg=GREEN_LT)

    # (3) 4x Countersunk B2 holes — NO A1 INSERTS!
    csink_pts = [(70, 18), (172, 18), (3, 44), (3, 155)]
    for cx, cy in csink_pts:
        ax.add_patch(Circle((cx, cy), 5.0, fc="white", ec=RED, lw=1.8, zorder=4))
    no_callout(ax, [(70, 18), (172, 18)], (121, -18), bad_code="A1", right_note="Step 8: BAG B • B2")

    # Bottom-Right: Iconic IKEA Warning (!) + Flush (✓) vs Proud (✗) graphic UX panel
    ikea_ux_panel(fig, [0.48, 0.04, 0.49, 0.18], "insert_flush", "FLUSH (0 mm)", "NO! PROUD / TILTED")

    path = os.path.join(OUT, "page-02-tray-inserts.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 3: BREAKER SHELVES (P2), GARMIN (P8) & POSTS (P6) — BAG A INSERTS & FOAM PADS
# =====================================================================================================================
def page_03_shelf_post_inserts():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "3", "DROP SHELVES (P2), GARMIN (P8) & POSTS (P6) — BAG A",
                "Soldering Iron (230°C)  |  7/32\" (5.6 mm) Drill (P6 & P8 only)",
                [("BAG A", "A3", "4", "M5 6.7 mm (P2)", RED, RED_LT),
                 ("BAG A", "A2", "2", "M4 Short 4.7 mm (P8)", BLUE, BLUE_LT),
                 ("BAG A", "A1", "2", "M4 Std 7.9 mm (P6)", GREEN, GREEN_LT)])

    ax3d = fig.add_axes([0.02, 0.24, 0.35, 0.58], projection="3d")
    render_3d_axes(ax3d, "", only_names={"print_breaker_shelf_0"}, elev=26, azim=-48, zoom=1.18)
    ax3d.set_title("P2 × 2  (Breaker Drop Shelves)", fontsize=11.5, weight="bold", pad=8)

    ax1 = fig.add_axes([0.38, 0.24, 0.30, 0.58])
    ax1.set_xlim(-15, 185); ax1.set_ylim(-50, 210); ax1.axis("off")
    ax1.add_patch(Rectangle((20, 20), 130, 168, fc=ORANGE_LT, ec=BLACK, lw=1.8))
    ax1.add_patch(Rectangle((20, 20), 130, 6, fc=ORANGE, ec=BLACK, lw=1.2))
    ax1.add_patch(Rectangle((20, 20 + 147), 130, 21, fc="#f5b895", ec=BLACK, lw=1.2))
    pts_p2 = [(53, 125), (110, 152)]
    for bx, by in pts_p2:
        ax1.add_patch(Circle((bx, by), 5.8, fc=RED, ec="white", lw=1.5, zorder=4))
    bag_callout(ax1, pts_p2, (85, 72), "BAG A", "A3", "2", sub="×2 Shelves = 4", col=RED, bg=RED_LT)

    ax1.add_patch(Rectangle((12, -38), 146, 42, fc="#343a40", ec=BLACK, lw=1.6))
    ax1.text(85, -17, "STICK EPDM FOAM PAD (×2)\nUNDER SHELF PLATE", color="white", fontsize=8.8, weight="bold", ha="center", va="center")

    ax2 = fig.add_axes([0.70, 0.24, 0.28, 0.58])
    ax2.set_xlim(0, 180); ax2.set_ylim(-50, 210); ax2.axis("off")
    ax2.add_patch(Rectangle((25, 85), 130, 105, fc=ORANGE_LT, ec=BLACK, lw=1.8))
    ax2.text(90, 175, "P8 (Upper Garmin)", ha="center", fontsize=9.2, weight="bold")
    pts_p8 = [(47.5, 138), (132.5, 138)]
    for gx_, gy_ in pts_p8:
        ax2.add_patch(Circle((gx_, gy_), 5.5, fc=BLUE, ec="white", lw=1.5, zorder=4))
    bag_callout(ax2, pts_p8, (90, 102), "BAG A", "A2", "2", sub="Ø5.6 Drill", col=BLUE, bg=BLUE_LT)

    for px, lbl in ((30, "P6: Post 0"), (120, "P6: Post 1")):
        ax2.add_patch(Rectangle((px, -42), 30, 100, fc=ORANGE_LT, ec=BLACK, lw=1.8))
        ax2.add_patch(Circle((px + 15, 58), 5.5, fc=GREEN, ec="white", lw=1.5, zorder=4))
        ax2.text(px + 15, 5, lbl, ha="center", va="center", rotation=90, fontsize=8.8, weight="bold")
    bag_callout(ax2, [(45, 58), (135, 58)], (90, 15), "BAG A", "A1", "2", sub="Ø5.6 Top End", col=GREEN, bg=GREEN_LT)

    ikea_ux_panel(fig, [0.26, 0.04, 0.48, 0.17], "insert_flush", "FLUSH + FOAM UNDER", "NO! PROUD INSERT")

    path = os.path.join(OUT, "page-03-shelf-post-inserts.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 4: INVERTER PLATE SUB-ASSEMBLY (P4 + P5 + BAG A / C / D)
# =====================================================================================================================
def page_04_plate_subassembly():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "4", "INVERTER PLATE (P4 + P5) — BAG A, BAG C & BAG D",
                "CA Glue  |  Drills: Ø5.6 & Ø6.4 mm  |  Soldering Iron  |  2.5 mm & 3 mm Hex Keys",
                [("BAG A", "A2", "14", "M4 Short (Ø5.6)", BLUE, BLUE_LT),
                 ("BAG A", "A3", "8", "M5 6.7 mm (Ø6.4)", RED, RED_LT),
                 ("BAG C", "C2", "8", "M4 × 8 (Cerbo/Orion)", DARK, GREY_FILL),
                 ("BAG D", "D1+D2", "8", "4× D1 + 4× D2", GOLD, GOLD_LT)])

    W_pl, H_pl = 505.5, 256.0
    zp = 21.0; px0 = X0 + 18.0 - 10.0

    # Left: Column Face
    ax1 = fig.add_axes([0.02, 0.22, 0.47, 0.62])
    ax1.set_aspect("equal"); ax1.axis("off")
    ax1.text(W_pl / 2, H_pl + 22, "1.  COLUMN FACE — 14× A2 (Ø5.6) + 4× A3 (Ø6.4)", ha="center", fontsize=10.5, weight="bold")
    ax1.add_patch(Rectangle((0, 0), W_pl, H_pl, fc=ORANGE_LT, ec=BLACK, lw=2))
    for cx in (168.5, 337.0):
        ax1.plot([cx, cx], [0, H_pl], color=BLACK, lw=1.2, ls="--")
        for sz in (162, 218):
            ax1.add_patch(Rectangle((cx - 30, sz - 9), 60, 18, fc=ORANGE, ec=BLACK, lw=1))

    wx = (D - B - 18.0 - 4.0 - 70.0) - px0; wz = 42.0 - zp
    ax1.add_patch(FancyBboxPatch((wx, wz), 70, 70, boxstyle="round,pad=0,rounding_size=10", fc="white", ec=BLACK, lw=1.5))

    sill_xs = [32.0, 146.7, 226.7, 278.8, 358.8, 473.5]
    for sx in sill_xs:
        ax1.add_patch(Circle((sx, 7.0), 6.5, fc=BLUE, ec="white", lw=1.3, zorder=4))
    bag_callout(ax1, [(226.7, 7.0), (278.8, 7.0)], (W_pl / 2, -38), "BAG A", "A2", "6", sub="Bottom Sill (Z=7)", col=BLUE, bg=BLUE_LT)

    units_info = [
        ("mppt", 50.0, 80.0, "MPPT\n[BAG A] A3 × 4\n[BAG D] D2 × 4", RED, RED_LT),
        ("cerbo", 205.0, 188.0, "Cerbo GX\n[BAG A] A2 × 4\n[BAG C] C2 × 4", BLUE, BLUE_LT),
        ("orion", 390.0, 118.0, "Orion XS\n[BAG A] A2 × 4\n[BAG C] C2 × 4", BLUE, BLUE_LT),
    ]
    for ukey, x0_box, z0_box, lbl, col, bg in units_info:
        c = cage.COMPONENTS[ukey]
        ux, uz = x0_box - px0, z0_box - zp
        ax1.add_patch(Rectangle((ux, uz), c.w, c.h, fc=bg, ec=col, lw=1.6, ls="--", alpha=0.92))
        ax1.text(ux + c.w / 2, uz + c.h / 2, lbl, ha="center", va="center", fontsize=8.0, weight="bold")
        for (hu, hv) in cage.HOLES[ukey]:
            ax1.add_patch(Circle((ux + hu, uz + hv), 6.5, fc=col, ec="white", lw=1.3))
    ax1.set_xlim(-20, W_pl + 20); ax1.set_ylim(-65, H_pl + 40)

    # Right: Inverter Face
    ax2 = fig.add_axes([0.51, 0.22, 0.47, 0.62])
    ax2.set_aspect("equal"); ax2.axis("off")
    ax2.text(W_pl / 2, H_pl + 22, "2.  INVERTER FACE — 4× A3 + 4× D1 (LEAVE 3 mm GAP!)", ha="center", fontsize=10.5, weight="bold")
    ax2.add_patch(Rectangle((0, 0), W_pl, H_pl, fc=ORANGE_LT, ec=BLACK, lw=2))
    inv_x0 = W_pl - ((cage.V13["inv_x"] - px0) + 375.0); inv_z0 = 22.0 - zp
    ax2.add_patch(Rectangle((inv_x0, inv_z0), 375.0, 249.0, fc=BLUE_LT, ec=BLUE, lw=1.6, ls="--", alpha=0.55))
    mp_pts = []
    for (hu, hv) in cage.HOLES["multiplus_1200_long"]:
        mx = W_pl - ((cage.V13["inv_x"] - px0) + hu); mz = inv_z0 + hv
        mp_pts.append((mx, mz))
        ax2.add_patch(Circle((mx, mz), 7.5, fc=RED, ec="white", lw=1.5, zorder=4))
    for cx in (W_pl - 168.5, W_pl - 337.0):
        ax2.plot([cx, cx], [0, H_pl], color=BLACK, lw=1.2, ls="--")
        for sz in (38, 94):
            ax2.add_patch(Rectangle((cx - 30, sz - 9), 60, 18, fc=ORANGE, ec=BLACK, lw=1))
    bag_callout(ax2, [mp_pts[0], mp_pts[1]], (W_pl / 2, 125), "BAG A", "A3", "4", sub="+ [BAG D] D1 × 4 (3 mm GAP)", col=RED, bg=RED_LT)
    ax2.set_xlim(-20, W_pl + 20); ax2.set_ylim(-65, H_pl + 40)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "proud_3mm", "3 mm GAP (KEYHOLE)", "NO! TIGHT TO PLATE")

    path = os.path.join(OUT, "page-04-plate-subassembly.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 5: BUS SHELF (P3) & GARMIN (P8) SUB-ASSEMBLIES — BAG A, BAG C & BAG D
# =====================================================================================================================
def page_05_bus_subassembly():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "5", "BUS SHELF (P3 × 3) & GARMIN (P8) — BAG A, BAG C & BAG D",
                "CA Glue  |  1/4\" (6.4 mm) Drill  |  Soldering Iron  |  2.5 mm & 3 mm Hex Keys",
                [("PART", "P3", "3", "Plates 0, 1 (152mm), 2", ORANGE, ORANGE_LT),
                 ("BAG A", "A3", "6", "M5 6.7 mm", RED, RED_LT),
                 ("BAG D", "D3", "6", "M5 × 12 + 2 Washers", GOLD, GOLD_LT),
                 ("BAG C", "C1", "2", "M4 × 10 (Garmin)", BLUE, BLUE_LT)])

    ax1 = fig.add_axes([0.03, 0.23, 0.62, 0.60])
    ax1.set_aspect("equal"); ax1.axis("off")
    b0, b1, b2 = 194.7, 326.8, 521.5
    ax1.add_patch(Rectangle((0, 0), b0, 110, fc=ORANGE_LT, ec=BLACK, lw=1.8))
    ax1.add_patch(Rectangle((b0, 0), b1 - b0, 110, fc="#ffd8a8", ec=BLACK, lw=2.2))
    ax1.add_patch(Rectangle((b1, 0), b2 - b1, 110, fc=ORANGE_LT, ec=BLACK, lw=1.8))
    ax1.text(b0 / 2, 124, "P3-0 (215 mm)", ha="center", fontsize=9.2, weight="bold")
    ax1.text((b0 + b1) / 2, 124, "P3-1 (152 mm)", ha="center", fontsize=9.2, weight="bold", color=RED)
    ax1.text((b1 + b2) / 2, 124, "P3-2 (195 mm)", ha="center", fontsize=9.2, weight="bold")

    ax1.add_patch(Rectangle((205, 16), 120, 44, fc=BLUE_LT, ec=BLUE, lw=1.6))
    ax1.text(265, 38, "SmartShunt", ha="center", va="center", fontsize=8.5, weight="bold", color=BLUE)
    sh_pts = [(217, 38), (313, 38)]
    for sx, sy in sh_pts:
        ax1.add_patch(Circle((sx, sy), 5.2, fc=RED, ec="white", lw=1.2, zorder=4))
    for bx, lbl in ((35, "+ Bus Bar"), (345, "− Bus Bar")):
        ax1.add_patch(Rectangle((bx, 62), 145, 32, fc=GOLD_LT, ec=GOLD, lw=1.6))
        ax1.text(bx + 72.5, 78, lbl, ha="center", va="center", fontsize=8.5, weight="bold")
        for hx in (bx + 18, bx + 127):
            ax1.add_patch(Circle((hx, 78), 5.2, fc=RED, ec="white", lw=1.2, zorder=4))
    bag_callout(ax1, sh_pts, (265, -36), "BAG A", "A3", "6", sub="+ [BAG D] D3 × 6 (Ø6.4 Drill)", col=RED, bg=RED_LT)
    ax1.set_xlim(-25, 550); ax1.set_ylim(-65, 155)

    ax2 = fig.add_axes([0.67, 0.23, 0.30, 0.60])
    ax2.set_aspect("equal"); ax2.axis("off")
    ax2.add_patch(Rectangle((15, 20), 130, 149, fc=ORANGE_LT, ec=BLACK, lw=1.8))
    ax2.add_patch(Rectangle((17.5, 42), 125, 75, fc="#343a40", ec=BLACK, lw=1.6))
    ax2.text(80, 80, "Garmin", ha="center", va="center", fontsize=9.5, weight="bold", color="white")
    g_pts = [(37.5, 79.5), (122.5, 79.5)]
    for gx_, gy_ in g_pts:
        ax2.add_patch(Circle((gx_, gy_), 5.5, fc=BLUE, ec="white", lw=1.5, zorder=4))
    bag_callout(ax2, g_pts, (80, -18), "BAG C", "C1", "2", col=BLUE, bg=BLUE_LT)
    ax2.set_xlim(-10, 170); ax2.set_ylim(-45, 185)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "insert_flush", "MARK HOLES WITH UNIT", "NO! FREEHAND GUESS")

    path = os.path.join(OUT, "page-05-bus-subassembly.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 6: ASSEMBLE FRAME & PRE-LOAD 24× B1 T-NUTS (BAG B)
# =====================================================================================================================
def page_06_frame_tnuts():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "6", "ASSEMBLE FRAME (F1) & LOAD 24× B1 T-NUTS",
                "Corner-Cube Driver  |  Tape Measure",
                [("PART", "F1", "12", "Rails + 8 Cubes", DARK, GREY_FILL),
                 ("BAG B", "B1", "24", "1/4\"-20 Drop-In T-Nuts", BLUE, BLUE_LT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.43, 0.60], projection="3d")
    render_3d_axes(ax3d, r"^(cube_|bar_|panel_)", elev=24, azim=-50)
    ax3d.set_title("1.  Bolt Rails + Slide 4 Panels into Slots", fontsize=10.5, weight="bold", pad=6)

    ax = fig.add_axes([0.46, 0.22, 0.52, 0.60])
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
        ax.text(X0 + x, W - B - 16, f"{x:.0f}", ha="center", fontsize=8, weight="bold")
    for y in (29, 140, 198, 238, 281):
        ax.plot(B, Y0 + y, marker=">", color=BLUE, ms=8)
        ax.text(B + 9, Y0 + y, f"{y}", va="center", fontsize=8, weight="bold", color=BLUE)
        ax.plot(D - B, Y0 + y, marker="<", color=BLUE, ms=8)
        ax.text(D - B - 9, Y0 + y, f"{y}", ha="right", va="center", fontsize=8, weight="bold", color=BLUE)
    ax.plot(4, Y0 + 291, marker=">", color=RED, ms=8.5)
    ax.plot(D - 4, Y0 + 291, marker="<", color=RED, ms=8.5)

    bag_callout(ax, [(X0 + 172, B), (B, Y0 + 198)], (285, 295), "BAG B", "B1", "16", sub="BOTTOM RAILS (Blue)", col=BLUE, bg=BLUE_LT)
    bag_callout(ax, [(X0 + 161, 4)], (285, 155), "BAG B", "B1", "8", sub="TOP RAILS (Red)", col=RED, bg=RED_LT)
    ax.set_xlim(-55, D + 55); ax.set_ylim(-35, W + 25)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "generic", "LOAD 24× B1 NOW", "NO! EMPTY SLOTS")

    path = os.path.join(OUT, "page-06-frame-tnuts.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 7: INSTALL INVERTER POSTS (P6 × 2) WITH BAG B • B4
# =====================================================================================================================
def page_07_posts():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "7", "INVERTER POSTS (P6 × 2) — BAG B • B4",
                "5/32\" Hex Key  |  Tape Measure",
                [("PART", "P6", "2", "Posts 0 & 1", ORANGE, ORANGE_LT),
                 ("BAG B", "B4", "2", "1/4\"-20 × 7/8\" Button-Head", BLUE, BLUE_LT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.44, 0.60], projection="3d")
    render_3d_axes(ax3d, r"^print_post_inverter_", [r"^(cube_|bar_)"])
    ax3d.set_title("P6 × 2  (Y = 281 mm)", fontsize=11, weight="bold", pad=6)

    ax = fig.add_axes([0.47, 0.22, 0.50, 0.60])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY_FILL, ec=BLACK, lw=1.4))
    p0, p1 = bb["print_post_inverter_0"], bb["print_post_inverter_1"]
    for p in (p0, p1):
        ax.add_patch(Rectangle((p.xmin, p.ymin), p.xlen, p.ylen, fc=ORANGE, ec=BLACK, lw=1.5))
    yc = (p0.ymin + p0.ymax) / 2
    ax.add_patch(FancyArrowPatch((D * 0.5, Y0), (D * 0.5, yc), arrowstyle="<|-|>", mutation_scale=14, lw=1.6, color=BLACK))
    ax.text(D * 0.5, (Y0 + yc) / 2, "Y = 281 mm", ha="center", va="center",
            fontsize=9.5, weight="bold", bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=BLACK))

    bag_callout(ax, [(p0.xmin + 4, yc), (p1.xmax - 4, yc)], (285, 360), "BAG B", "B4", "2", sub="Into B1 at Y=281", col=BLUE, bg=BLUE_LT)
    ax.set_xlim(-45, D + 45); ax.set_ylim(-25, W + 25)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "generic", "SLOTS FACE INWARD", "NO! SLOTS OUTWARD")

    path = os.path.join(OUT, "page-07-posts.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 8: INSTALL BATTERY TRAYS (P1 × 2) WITH BAG B • B2
# =====================================================================================================================
def page_08_trays():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "8", "BATTERY TRAYS (P1 × 2) — BAG B • B2",
                "5/32\" Hex Key",
                [("PART", "P1", "2", "Trays 0 & 1", ORANGE, ORANGE_LT),
                 ("BAG B", "B2", "8", "1/4\"-20 × 1/2\" Flat-Head", BLUE, BLUE_LT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.44, 0.60], projection="3d")
    render_3d_axes(ax3d, r"^print_tray_battery_", [r"^(cube_|bar_|print_post_inverter_)"])
    ax3d.set_title("P1 × 2  (Back = Tray 0, Front = Tray 1)", fontsize=11, weight="bold", pad=6)

    ax = fig.add_axes([0.47, 0.22, 0.50, 0.60])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY_FILL, ec=BLACK, lw=1.4))
    t0, t1 = bb["print_tray_battery_0"], bb["print_tray_battery_1"]
    out_pts, end_pts = [], []
    for idx, (tr, lbl, x_nuts) in enumerate(((t0, "P1-0", (70, 172)), (t1, "P1-1", (349.5, 451.5)))):
        ax.add_patch(Rectangle((tr.xmin, tr.ymin), tr.xlen, tr.ylen, fc=ORANGE, ec=BLACK, lw=1.4))
        ax.add_patch(Rectangle((tr.xmin + 6, tr.ymin + 6), tr.xlen - 12, 140, fc="#fff5eb", ec=BLACK, lw=1))
        ax.text((tr.xmin + tr.xmax) / 2, tr.ymin + 76, lbl, ha="center", va="center", fontsize=11, weight="bold")
        for xn in x_nuts:
            pt = (X0 + xn, tr.ymin + 10)
            out_pts.append(pt)
            ax.add_patch(Circle(pt, 6, fc=BLUE, ec="white", lw=1.2, zorder=4))
        for yn in (29, 140):
            bx = tr.xmin + 10 if idx == 0 else tr.xmax - 10
            pt = (bx, Y0 + yn)
            end_pts.append(pt)
            ax.add_patch(Circle(pt, 6, fc=BLUE, ec="white", lw=1.2, zorder=4))

    bag_callout(ax, [out_pts[1], out_pts[2]], (285, 255), "BAG B", "B2", "4", sub="OUTER WALL", col=BLUE, bg=BLUE_LT)
    bag_callout(ax, [end_pts[1], end_pts[3]], (285, 365), "BAG B", "B2", "4", sub="END WALLS", col=BLUE, bg=BLUE_LT)
    ax.set_xlim(-45, D + 45); ax.set_ylim(-25, W + 25)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "csink_flush", "B2 FLUSH IN FLOOR", "NO! PROUD HEAD")

    path = os.path.join(OUT, "page-08-trays.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 9: DROP IN BATTERIES FIRST, THEN CLAMP DROP SHELVES (P2) — BAG C, BAG B & BAG D
# =====================================================================================================================
def page_09_batteries_shelves():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "9", "BATTERIES (1st) + DROP SHELVES (P2) — BAG C, B & D",
                "2.5 mm Hex Key (C1)  |  5/32\" Hex Key (B2)  |  3 mm Hex Key (D1)",
                [("PART", "P2", "2", "Drop Shelves", ORANGE, ORANGE_LT),
                 ("BAG C", "C1", "4", "M4 × 10 (Feet 1st)", GREEN, GREEN_LT),
                 ("BAG B", "B2", "4", "1/4-20 × 1/2\" (Top 2nd)", BLUE, BLUE_LT),
                 ("BAG D", "D1", "4", "M5 × 10 + Washers", RED, RED_LT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.45, 0.60], projection="3d")
    render_3d_axes(ax3d, r"^(battery_|print_breaker_shelf_|power_breaker_shelf_)",
                   [r"^(cube_|bar_|print_post_inverter_|print_tray_battery_)"])
    ax3d.set_title("1. Batteries In   /   2. Shelves Clamp On Top", fontsize=11, weight="bold", pad=6)

    ax = fig.add_axes([0.48, 0.22, 0.49, 0.60])
    ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), B, B, fc=GREY_FILL, ec=BLACK, lw=1.4))
    ax.add_patch(Rectangle((0, H - B), B, B, fc=GREY_FILL, ec=BLACK, lw=1.4))
    ax.add_patch(Polygon([(26, 0), (193, 0), (193, 36), (172, 36), (172, 6), (32, 6), (32, 36), (26, 36)],
                         closed=True, fc=ORANGE_LT, ec=BLACK, lw=1.5))
    ax.add_patch(Rectangle((32.5, 6), 139, 208, fc=BLUE_LT, ec=BLUE, lw=1.8))
    ax.text(102, 130, "1.  BATTERY IN FIRST\n(×2)", ha="center", va="center", fontsize=11, weight="bold", color=BLUE)
    ax.add_patch(Rectangle((32.5, 214), 139, 3, fc=BLACK, ec=BLACK))
    ax.add_patch(Polygon([(25, 215), (178, 215), (178, 36), (193, 36), (193, 42), (184, 42), (184, 239),
                          (178, 239), (178, 221), (31, 221), (31, 278.7), (25, 278.7)],
                         closed=True, fc=ORANGE, ec=BLACK, lw=1.5))
    ax.add_patch(Rectangle((117, 221), 49, 44, fc=GOLD, ec=BLACK, lw=1.5))

    bag_callout(ax, (186, 42), (105, 58), "BAG C", "C1", "4", sub="2. FOOT FIRST", col=GREEN, bg=GREEN_LT)
    bag_callout(ax, (25, 269.2), (82, 282), "BAG B", "B2", "4", sub="3. TOP HANGER", col=BLUE, bg=BLUE_LT)
    bag_callout(ax, (141.5, 243), (185, 282), "BAG D", "D1", "4", sub="4. BREAKERS", col=RED, bg=RED_LT)
    ax.set_xlim(-15, 235); ax.set_ylim(-10, 310)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "battery_first", "1. BATTERY  2. SHELF", "NO! SHELF BEFORE BAT")

    path = os.path.join(OUT, "page-09-batteries-shelves.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 10: DROP IN BUS SHELF (P3) — BAG C • C1 & BAG B • B2
# =====================================================================================================================
def page_10_bus_shelf():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "10", "BUS SHELF (P3) INTO CENTER BAY — BAG C & BAG B",
                "2.5 mm Hex Key (C1)  |  5/32\" Hex Key (B2)",
                [("PART", "P3", "1", "Bus Shelf Assembly", ORANGE, ORANGE_LT),
                 ("BAG C", "C1", "6", "M4 × 10 (Lip to Trays)", GREEN, GREEN_LT),
                 ("BAG B", "B2", "4", "1/4-20 × 1/2\" (Ends to Rails)", BLUE, BLUE_LT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.44, 0.60], projection="3d")
    render_3d_axes(ax3d, r"^(print_bus_shelf_|power_busbar_|power_shunt_|victron_smartshunt_)",
                   [r"^(cube_|bar_|print_post_inverter_|print_tray_battery_|battery_|print_breaker_shelf_|power_breaker_shelf_)"])
    ax3d.set_title("P3 Drops Between Trays & Posts", fontsize=11, weight="bold", pad=6)

    ax = fig.add_axes([0.47, 0.22, 0.50, 0.60])
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
    lip_pts = [(hx, lip_y + 4) for hx in [t0_x + 40, t0_x + 100, t0_x + 140, t1_x + 40, t1_x + 120, t1_x + 200]]
    for pt in lip_pts:
        ax.add_patch(Circle(pt, 6.0, fc=GREEN, ec="white", lw=1.3, zorder=4))
    end_pts = []
    for yn in (198, 238):
        end_pts.extend([(X0 + 6, Y0 + yn), (D - B - 6, Y0 + yn)])
        ax.add_patch(Circle((X0 + 6, Y0 + yn), 6.0, fc=BLUE, ec="white", lw=1.3, zorder=4))
        ax.add_patch(Circle((D - B - 6, Y0 + yn), 6.0, fc=BLUE, ec="white", lw=1.3, zorder=4))

    bag_callout(ax, [lip_pts[1], lip_pts[4]], (285, 325), "BAG C", "C1", "6", sub="LIP TO TRAYS", col=GREEN, bg=GREEN_LT)
    bag_callout(ax, [end_pts[2], end_pts[3]], (285, 415), "BAG B", "B2", "4", sub="ENDS TO RAILS", col=BLUE, bg=BLUE_LT)
    ax.set_xlim(-45, D + 45); ax.set_ylim(-25, W + 25)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "generic", "ALL 6× C1 + 4× B2", "NO! UNBOLTED LIP")

    path = os.path.join(OUT, "page-10-bus-shelf.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 11: SLIDE IN INVERTER PLATE, LOCK CLIPS (P7) & GARMIN (P8) — BAG C & BAG B
# =====================================================================================================================
def page_11_plate_clips_garmin():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "11", "INVERTER PLATE, CLIPS (P7) & GARMIN (P8) — BAG C & B",
                "2.5 mm Hex Key (C2, C3)  |  5/32\" Hex Key (B2, B3)",
                [("BAG C", "C2", "6", "M4 × 8 (Plate Sill)", BLUE, BLUE_LT),
                 ("BAG C", "C3+B3", "2+2", "Post Clips (P7)", RED, RED_LT),
                 ("BAG B", "B2", "4", "1/4-20 × 1/2\" (Garmin)", GREEN, GREEN_LT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.44, 0.60], projection="3d")
    render_3d_axes(ax3d, r"^(print_plate_inverter_|victron_mppt_|victron_cerbo_|victron_orion_|print_post_clip_|print_garmin_hanger|garmin_powerswitch_hanger)",
                   [r"^(cube_|bar_|print_post_inverter_|print_tray_battery_|battery_|print_breaker_shelf_|power_breaker_shelf_|print_bus_shelf_)"])
    ax3d.set_title("Plate Slides Into Posts + Garmin on Inboard Rail", fontsize=10.5, weight="bold", pad=6)

    ax = fig.add_axes([0.47, 0.22, 0.50, 0.60])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY_FILL, ec=BLACK, lw=1.4))
    for nm, b_ in bb.items():
        if re.match(r"^(print_tray_battery_|print_bus_shelf_|print_post_inverter_)", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc="#eee", ec="#999", lw=0.8))
        elif re.match(r"^(print_plate_inverter_|victron_mppt_|victron_cerbo_|victron_orion_|print_garmin_hanger)", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc=ORANGE, ec=BLACK, lw=1.2))

    yp = cage.V13["plate_y"]
    sill_pts = [(sx, yp - 2) for sx in (65, 179.7, 259.7, 311.8, 391.8, 506.5)]
    for pt in sill_pts:
        ax.add_patch(Circle(pt, 5.5, fc=BLUE, ec="white", lw=1.2, zorder=4))
    clip_pts = [(X0 + 8, Y0 + 291), (D - B - 8, Y0 + 291)]
    for pt in clip_pts:
        ax.add_patch(Circle(pt, 6.5, fc=RED, ec="white", lw=1.4, zorder=4))
    gar_pts = [(X0 + 341.5, W - B - 3), (X0 + 421.5, W - B - 3)]
    for pt in gar_pts:
        ax.add_patch(Circle(pt, 6.0, fc=GREEN, ec="white", lw=1.3, zorder=4))

    bag_callout(ax, [sill_pts[2], sill_pts[3]], (285, 105), "BAG C", "C2", "6", sub="SILL (Z=28)", col=BLUE, bg=BLUE_LT)
    bag_callout(ax, [clip_pts[0]], (165, 415), "BAG C", "C3+B3", "2", sub="P7 CLIPS", col=RED, bg=RED_LT)
    bag_callout(ax, gar_pts, (405, 340), "BAG B", "B2", "4", sub="P8 GARMIN", col=GREEN, bg=GREEN_LT)
    ax.set_xlim(-45, D + 45); ax.set_ylim(-25, W + 25)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "generic", "SEAT PLATE IN SLOTS", "NO! MISSED SILL")

    path = os.path.join(OUT, "page-11-plate-clips-garmin.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 12: HANG MULTIPLUS ON D1 KEYHOLES, CONNECT 4 AWG CABLES & FIT LID
# =====================================================================================================================
def page_12_multiplus_wiring_lid():
    fig = plt.figure(figsize=(15, 9.6), dpi=120)
    ikea_header(fig, "12", "MULTIPLUS KEYHOLES (BAG D • D1), CABLES & LID",
                "3 mm Hex Key (D1 Keyholes)  |  10 mm / 13 mm Socket  |  Phillips Driver",
                [("BAG D", "D1", "4", "Snug M5 × 10 Keyholes", BLUE, BLUE_LT),
                 ("PART", "P9", "1", "GX Touch Bezel", ORANGE, ORANGE_LT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.44, 0.60], projection="3d")
    render_3d_axes(ax3d, r"^(victron_multiplus_|socket_|gx_touch|print_touch_bezel)",
                   [r"^(cube_|bar_|print_post_inverter_|print_tray_battery_|battery_|print_breaker_shelf_|power_breaker_shelf_|print_bus_shelf_|print_plate_inverter_|victron_mppt_|victron_cerbo_|victron_orion_|print_garmin_hanger)"])
    ax3d.set_title("Hang MultiPlus + Connect 4 AWG + Close Lid", fontsize=10.5, weight="bold", pad=6)

    ax = fig.add_axes([0.47, 0.22, 0.50, 0.60])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY_FILL, ec=BLACK, lw=1.4))
    for nm, b_ in bb.items():
        if re.match(r"^(print_tray_battery_|print_bus_shelf_|print_plate_inverter_|print_garmin_hanger)", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc="#eee", ec="#999", lw=0.8))
    mp = bb["victron_multiplus_long"]
    ax.add_patch(Rectangle((mp.xmin, mp.ymin), mp.xlen, mp.ylen, fc=BLUE, ec=BLACK, lw=1.6))

    bag_callout(ax, ((mp.xmin + mp.xmax) / 2, mp.ymin + 10), (260, 415), "BAG D", "D1", "4", sub="HOOK & TIGHTEN", col=BLUE, bg=BLUE_LT)

    ax.annotate("", xy=(140, 265), xytext=(120, 155), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=RED))
    ax.annotate("", xy=(190, 265), xytext=(400, 155), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=RED))
    ax.annotate("", xy=(265, 225), xytext=(95, 115), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=BLACK))
    ax.annotate("", xy=(295, 225), xytext=(375, 115), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=BLACK))
    ax.annotate("", xy=(430, 330), xytext=(485, 270), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=RED))
    ax.annotate("", xy=(415, 315), xytext=(465, 270), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=BLACK))

    ax.text(140, 232, "4 AWG (+)", fontsize=9, weight="bold", color=RED, ha="center",
            bbox=dict(boxstyle="round,pad=0.25", fc=RED_LT, ec=RED, lw=1.5))
    ax.text(285, 95, "4 AWG (−)", fontsize=9, weight="bold", color=BLACK, ha="center",
            bbox=dict(boxstyle="round,pad=0.25", fc=GREY_FILL, ec=BLACK, lw=1.5))
    ax.set_xlim(-45, D + 45); ax.set_ylim(-25, W + 25)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "proud_3mm", "SNUG ALL 4× D1", "NO! LOOSE LUGS")

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
