"""Generate a 13-page IKEA-style visual assembly manual (../manual/ikea/page-00..12.png) for IKEA-MANUAL.md.
Uses OpenCascade exact analytic Hidden-Line Removal (HLRBRep_Algo) for smooth vector CAD line-art (zero jagged STL facets),
clean Helvetica Neue / Futura Regular & Bold typography at 200 DPI, drawn fastener icons, hardware bag callouts (BAG A–D),
and calm monochrome IKEA Warning (!) / Good vs. Crossed-Out graphic panels.

Run: .venv/bin/python ikea_manual.py v12s"""
import math, os, re, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, FancyBboxPatch, Polygon
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
from OCP.BRepLib import BRepLib
import cage, render

# Use smooth macOS geometric/grotesque sans-serifs (Helvetica Neue / Futura / Arial)
for fp in (
    "/System/Library/Fonts/Supplemental/Futura.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
):
    if os.path.exists(fp):
        fm.fontManager.addfont(fp)
matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.sans-serif"] = ["Helvetica Neue", "Futura", "Arial", "DejaVu Sans"]
matplotlib.rcParams["lines.solid_capstyle"] = "round"
matplotlib.rcParams["lines.solid_joinstyle"] = "round"

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "manual", "ikea")
os.makedirs(OUT, exist_ok=True)
DPI = 200

asm = cage.build()
bb = {ch.name: ch.obj.val().BoundingBox() for ch in asm.children}
shapes = {ch.name: ch.obj.val() for ch in asm.children}
B, C, D, W, H = cage.B, cage.C, cage.out_D, cage.out_W, cage.out_H
X0, Y0 = cage.x_in0, cage.y_in0

# Calm, editorial IKEA monochrome + soft warm-grey/ivory palette (no harsh neon borders)
INK = "#1a1a1a"          # Soft charcoal black for primary line art
INK_SUB = "#4b5563"      # Slate grey for secondary labels & dimensions
CTX_EDGE = "#9ca3af"     # Subtle technical grey for already-installed context parts
CTX_FILL = "#f8fafc"     # Near-white fill for context parts
ACT_FILL = "#f3ede2"     # Warm IKEA birch/ivory highlight for active 3D-printed parts
BLUE_FILL = "#e6f0fa"    # Soft powder blue for batteries / Victron units
BRASS = "#d4a017"        # Soft brass accent for heat-set inserts
BRASS_LT = "#fef9e7"
YELLOW = "#ffdb00"       # Classic IKEA warning triangle yellow
RED_X = "#c92a2a"        # Clean cross-out red
GREEN_OK = "#1b7f37"
BORDER_LT = "#d1d5db"
BG_SOFT = "#f9fafb"


# =====================================================================================================================
# EXACT ANALYTIC CAD HIDDEN-LINE REMOVAL (HLRBRep_Algo) — SMOOTH VECTOR LINE ART (ZERO STL FACETS)
# =====================================================================================================================
def _extract_hlr_segs(comp, deflection=0.12):
    if comp is None or comp.IsNull():
        return []
    BRepLib.BuildCurves3d_s(comp)
    segs = []
    exp = TopExp_Explorer(comp, TopAbs_EDGE)
    while exp.More():
        e = TopoDS.Edge_s(exp.Current())
        c = BRepAdaptor_Curve(e)
        g = GCPnts_QuasiUniformDeflection(c, deflection)
        if g.IsDone() and g.NbPoints() >= 2:
            pts = [(g.Value(i).X(), g.Value(i).Y()) for i in range(1, g.NbPoints() + 1)]
            segs.append(pts)
        exp.Next()
    return segs


def render_3d_hlr(ax, new_re, old_res=(), elev=26, azim=-50, only_names=None, title=""):
    """Render 3D CAD geometry into a 2D axis using OpenCascade exact analytic Hidden-Line Removal (HLRBRep_Algo).
    Context parts are drawn in calm warm grey; active newly-installed parts are drawn in crisp charcoal ink."""
    el, az = math.radians(elev), math.radians(azim)
    dx, dy, dz = math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)
    rx, ry, rz = -math.sin(az), math.cos(az), 0.0

    algo = HLRBRep_Algo()
    active_shapes, context_shapes = [], []

    for ch in asm.children:
        nm = ch.name
        if nm.startswith("icebox_"):
            continue
        if only_names is not None:
            if nm not in only_names:
                continue
            is_new = True
        else:
            is_new = re.match(new_re, nm) is not None
            is_old = any(re.match(r, nm) for r in old_res)
            if not (is_new or is_old):
                continue
            if nm.startswith("lid_") and not is_new:
                continue
            if nm.startswith("panel_") and not is_new:
                continue

        s_wrapped = ch.obj.val().wrapped
        algo.Add(s_wrapped)
        if is_new:
            active_shapes.append(s_wrapped)
        else:
            context_shapes.append(s_wrapped)

    # Run OpenCascade exact analytic Hidden-Line Removal
    proj = HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(dx, dy, dz), gp_Dir(rx, ry, rz)))
    algo.Projector(proj)
    algo.Update()
    algo.Hide()
    hlr = HLRBRep_HLRToShape(algo)

    # 1. Context edges (thin, calm warm grey)
    ctx_segs = []
    for s in context_shapes:
        ctx_segs.extend(_extract_hlr_segs(hlr.VCompound(s)))
        ctx_segs.extend(_extract_hlr_segs(hlr.OutLineVCompound(s)))
    if ctx_segs:
        ax.add_collection(LineCollection(ctx_segs, colors=CTX_EDGE, linewidths=0.58, capstyle="round", joinstyle="round", antialiased=True))

    # 2. Active part edges (subtle warm highlight halo + crisp IKEA charcoal ink)
    act_inner, act_outer = [], []
    for s in active_shapes:
        act_inner.extend(_extract_hlr_segs(hlr.VCompound(s)))
        act_outer.extend(_extract_hlr_segs(hlr.OutLineVCompound(s)))
    if act_inner or act_outer:
        ax.add_collection(LineCollection(act_inner + act_outer, colors="#f59e0b", linewidths=2.6, alpha=0.22, capstyle="round", joinstyle="round", antialiased=True))
    if act_inner:
        ax.add_collection(LineCollection(act_inner, colors=INK, linewidths=0.95, capstyle="round", joinstyle="round", antialiased=True))
    if act_outer:
        ax.add_collection(LineCollection(act_outer, colors=INK, linewidths=1.40, capstyle="round", joinstyle="round", antialiased=True))

    # Auto-frame with clean aspect ratio
    all_pts = np.concatenate([ np.asarray(seg) for seg in (ctx_segs + act_inner + act_outer) ], axis=0)
    lo, hi = all_pts.min(axis=0), all_pts.max(axis=0)
    span = max(hi[0] - lo[0], hi[1] - lo[1]) * 0.56
    mid = (lo + hi) * 0.5
    ax.set_xlim(mid[0] - span, mid[0] + span)
    ax.set_ylim(mid[1] - span * 0.86, mid[1] + span * 1.02)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.text(0.5, 0.97, title, transform=ax.transAxes, ha="center", va="top",
                fontsize=10.5, weight="normal", color=INK_SUB)


# =====================================================================================================================
# IKEA GRAPHIC PRIMITIVES: HARDWARE BAGS, FASTENER LINE-ART ICONS & MONOCHROME WARNING (!) PANELS
# =====================================================================================================================
def draw_bag_icon(ax, x, y, w, h, bag_letter, r=0.55):
    """Draw a clean IKEA monochrome hardware zip-bag icon with rounded corners labeled 'BAG A', 'BAG B', etc."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc="white", ec=INK, lw=1.1))
    ax.add_patch(FancyBboxPatch((x, y + h * 0.72), w, h * 0.28, boxstyle=f"round,pad=0,rounding_size={r*0.6}", fc=INK, ec=INK, lw=0.5))
    ax.plot([x + w * 0.16, x + w * 0.84], [y + h * 0.86, y + h * 0.86], color="white", lw=0.9)
    ax.text(x + w / 2, y + h * 0.36, f"BAG\n{bag_letter}", color=INK, fontsize=6.2, weight="bold",
            ha="center", va="center", linespacing=0.92)


def draw_fastener_icon(ax, cx, cy, w, h, kind="insert"):
    """Draw a clean 2D technical line-art silhouette of a heat-set insert, T-nut, flat screw, or button screw."""
    if kind == "insert":
        # Brass knurled cylinder with diagonal knurl ticks
        ax.add_patch(Rectangle((cx - w * 0.35, cy - h * 0.42), w * 0.70, h * 0.84, fc=BRASS_LT, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((cx - w * 0.42, cy + h * 0.18), w * 0.84, h * 0.24, fc=BRASS, ec=INK, lw=1.0))
        for ky in (-0.22, -0.02):
            ax.plot([cx - w * 0.32, cx + w * 0.32], [cy + h * ky, cy + h * (ky + 0.12)], color=INK, lw=0.7)
    elif kind == "tnut":
        # Roll-in T-nut profile
        pts = [(cx - w * 0.45, cy - h * 0.15), (cx + w * 0.45, cy - h * 0.15),
               (cx + w * 0.45, cy + h * 0.15), (cx + w * 0.22, cy + h * 0.38),
               (cx - w * 0.22, cy + h * 0.38), (cx - w * 0.45, cy + h * 0.15)]
        ax.add_patch(Polygon(pts, closed=True, fc=CTX_FILL, ec=INK, lw=1.0))
        ax.plot([cx, cx], [cy - h * 0.15, cy + h * 0.38], color=INK, lw=0.8, ls=":")
    elif kind == "flat_screw":
        # 82-deg flat-head countersunk screw
        head = [(cx - w * 0.45, cy + h * 0.42), (cx + w * 0.45, cy + h * 0.42),
                (cx + w * 0.18, cy + h * 0.12), (cx - w * 0.18, cy + h * 0.12)]
        ax.add_patch(Polygon(head, closed=True, fc=CTX_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((cx - w * 0.18, cy - h * 0.42), w * 0.36, h * 0.54, fc="white", ec=INK, lw=0.9))
        for ty in (-0.28, -0.12, 0.02):
            ax.plot([cx - w * 0.18, cx + w * 0.18], [cy + h * ty, cy + h * ty], color=INK, lw=0.6)
    else:
        # Domed button-head screw
        ax.add_patch(FancyBboxPatch((cx - w * 0.42, cy + h * 0.12), w * 0.84, h * 0.28,
                                    boxstyle="round,pad=0.02,rounding_size=0.12", fc=CTX_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((cx - w * 0.18, cy - h * 0.42), w * 0.36, h * 0.54, fc="white", ec=INK, lw=0.9))
        for ty in (-0.28, -0.12, 0.02):
            ax.plot([cx - w * 0.18, cx + w * 0.18], [cy + h * ty, cy + h * ty], color=INK, lw=0.6)


def ikea_header(fig, step_num, title, tools_str, hw_badges):
    """Draw a clean, calm IKEA top strip with smooth rounded corners in true 1:1 equal-aspect coordinates."""
    ax = fig.add_axes([0.02, 0.85, 0.96, 0.13])
    # 138.5 x 12.0 matches the physical 14.4" x 1.248" aspect ratio (11.54:1) so all rounded corners are true circular arcs
    ax.set_xlim(0, 138.5); ax.set_ylim(0, 12.0); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.3, 0.4), 137.9, 11.2, boxstyle="round,pad=0,rounding_size=1.8", fc="white", ec=INK, lw=1.5))
    ax.add_patch(FancyBboxPatch((0.3, 0.4), 14.0, 11.2, boxstyle="round,pad=0,rounding_size=1.8", fc=INK, ec=INK))
    ax.text(7.3, 6.0, str(step_num), color="white", fontsize=26, weight="bold", ha="center", va="center")

    # Row 1: Step Title
    ax.text(16.8, 9.4, title, color=INK, fontsize=13.5, weight="bold", ha="left", va="center")
    # Row 2: Tools
    ax.text(16.8, 6.5, f"Tools:  {tools_str}", color=INK_SUB, fontsize=8.8, weight="normal", ha="left", va="center")
    ax.plot([14.3, 138.2], [5.0, 5.0], color=BORDER_LT, lw=0.9)

    # Row 3: Rounded hardware pills with drawn bag icon + fastener silhouette
    x_left = 16.8
    for bag_or_part, code, qty, label, _col, _bg in hw_badges:
        pill_txt = f"{qty}×  {code}"
        sub_txt = f"  ({label})"
        w_box = max(18.5, (len(pill_txt) + len(sub_txt)) * 0.52 + 9.0)
        ax.add_patch(FancyBboxPatch((x_left, 0.95), w_box, 3.55, boxstyle="round,pad=0,rounding_size=1.35", fc=BG_SOFT, ec=BORDER_LT, lw=1.0))
        if bag_or_part.startswith("BAG"):
            b_let = bag_or_part.split()[-1]
            draw_bag_icon(ax, x_left + 0.55, 1.12, 3.6, 3.2, b_let, r=0.55)
            kind = "insert" if b_let == "A" else ("tnut" if code == "B1" else ("flat_screw" if code in ("B2", "B3") else "btn_screw"))
            draw_fastener_icon(ax, x_left + 5.6, 2.72, 2.3, 2.6, kind=kind)
            tx = x_left + 7.5
        else:
            w_code = max(4.2, len(code) * 1.15 + 1.2)
            ax.add_patch(FancyBboxPatch((x_left + 0.65, 1.35), w_code, 2.75, boxstyle="round,pad=0,rounding_size=0.85", fc=ACT_FILL, ec=INK, lw=0.9))
            ax.text(x_left + 0.65 + w_code / 2, 2.72, code, color=INK, fontsize=7.5, weight="bold", ha="center", va="center")
            tx = x_left + w_code + 1.5
        ax.text(tx, 2.72, f"{qty}×  {code}", color=INK, fontsize=8.8, weight="bold", ha="left", va="center")
        ax.text(tx + len(f"{qty}×  {code}") * 0.66 + 1.0, 2.72, label, color=INK_SUB, fontsize=8.0, weight="normal", ha="left", va="center")
        x_left += w_box + 1.2


def bag_callout(ax, xy_targets, xytext, bag, code, qty, sub="", col=INK, bg="white"):
    """Draw a clean, calm IKEA callout pill with generously rounded corners."""
    if isinstance(xy_targets, tuple) and len(xy_targets) == 2 and not isinstance(xy_targets[0], (tuple, list)):
        xy_targets = [xy_targets]
    for xy in xy_targets:
        ax.annotate("", xy=xy, xytext=xytext,
                    arrowprops=dict(arrowstyle="-|>", lw=1.1, color=INK, shrinkA=10, shrinkB=2,
                                    mutation_scale=10))
    header = f"{qty}×  {code}  ({bag})"
    body = f"{header}\n{sub}" if sub else header
    ax.text(xytext[0], xytext[1], body, fontsize=8.8, weight="normal", color=INK, ha="center", va="center",
            linespacing=1.22, bbox=dict(boxstyle="round,pad=0.52,rounding_size=0.85", fc="white", ec=INK, lw=1.1))


def no_callout(ax, xy_targets, xytext, bad_code="A1", right_note=""):
    """Draw a clean IKEA 'DO NOT INSERT HERE' callout with generously rounded corners."""
    if isinstance(xy_targets, tuple) and len(xy_targets) == 2 and not isinstance(xy_targets[0], (tuple, list)):
        xy_targets = [xy_targets]
    for xy in xy_targets:
        ax.annotate("", xy=xy, xytext=xytext,
                    arrowprops=dict(arrowstyle="-|>", lw=1.1, color=RED_X, ls="--", shrinkA=10, shrinkB=2,
                                    mutation_scale=10))
    txt = f"!   No {bad_code}"
    if right_note:
        txt += f"  ({right_note})"
    ax.text(xytext[0], xytext[1], txt, fontsize=8.6, weight="normal", color=RED_X, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.48,rounding_size=0.85", fc="white", ec=RED_X, lw=1.1))


def draw_warning_triangle(ax, cx, cy, r):
    """Draw an authentic IKEA Warning Triangle in true equal-aspect coordinates."""
    pts = [(cx, cy + r * 0.95), (cx - r * 0.90, cy - r * 0.75), (cx + r * 0.90, cy - r * 0.75)]
    ax.add_patch(Polygon(pts, closed=True, fc=YELLOW, ec=INK, lw=1.8, joinstyle="round"))
    ax.text(cx, cy - r * 0.16, "!", color=INK, fontsize=17, weight="bold", ha="center", va="center")


def draw_check_badge(ax, cx, cy, r, ok=True):
    """Draw a true circular checkmark or X badge in equal-aspect coordinates."""
    col = INK if ok else RED_X
    ax.add_patch(Circle((cx, cy), r, fc="white", ec=col, lw=1.4, zorder=5))
    if ok:
        ax.plot([cx - r * 0.42, cx - r * 0.08, cx + r * 0.45],
                [cy - r * 0.02, cy - r * 0.38, cy + r * 0.38],
                color=col, lw=1.8, solid_capstyle="round", zorder=6)
    else:
        d = r * 0.38
        ax.plot([cx - d, cx + d], [cy - d, cy + d], color=col, lw=1.8, solid_capstyle="round", zorder=6)
        ax.plot([cx - d, cx + d], [cy + d, cy - d], color=col, lw=1.8, solid_capstyle="round", zorder=6)


def draw_red_x(ax, x, y, w, h):
    """Draw a clean diagonal cross across the 'bad' graphic."""
    ax.plot([x, x + w], [y, y + h], color=RED_X, lw=2.0, zorder=6)
    ax.plot([x, x + w], [y + h, y], color=RED_X, lw=2.0, zorder=6)


def ikea_ux_panel(fig, rect, mode, ok_lbl, no_lbl):
    """Draw a calm, monochrome IKEA Warning (!) + Visual GOOD vs BAD line-art panel with smooth rounded corners."""
    ax = fig.add_axes(rect)
    # Use 140 x 32 with set_aspect('equal') so circles, triangles, and rounded corners are true circular arcs!
    ax.set_xlim(0, 140); ax.set_ylim(0, 32); ax.set_aspect("equal"); ax.axis("off")

    # Clean outer monochrome frame with generous 4.2-unit corner radius
    ax.add_patch(FancyBboxPatch((1.0, 1.0), 138.0, 30.0, boxstyle="round,pad=0,rounding_size=4.2", fc="white", ec=INK, lw=1.4))
    ax.plot([24.0, 24.0], [1.5, 30.5], color=BORDER_LT, lw=1.1)
    ax.plot([82.0, 82.0], [3.5, 28.5], color=BORDER_LT, lw=0.9, ls="--")
    draw_warning_triangle(ax, 12.5, 16.0, 7.8)

    # Good sub-panel (x = 25 .. 81)
    draw_check_badge(ax, 30.5, 25.0, 3.0, ok=True)
    ax.text(53.5, 4.8, ok_lbl, color=INK, fontsize=8.4, weight="normal", ha="center", va="center")

    # Bad sub-panel (x = 83 .. 138)
    draw_check_badge(ax, 88.5, 25.0, 3.0, ok=False)
    ax.text(111.0, 4.8, no_lbl, color=INK_SUB, fontsize=8.4, weight="normal", ha="center", va="center")

    # Line-art illustrations
    if mode == "insert_flush":
        # GOOD: plastic cross-section + knurled brass insert sitting flush with top surface
        ax.add_patch(Rectangle((38, 10), 30, 11, fc=ACT_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((48.5, 13), 9, 8, fc=BRASS_LT, ec=INK, lw=1.1))
        for ky in (15, 18):
            ax.plot([49, 57], [ky, ky + 1.5], color=INK, lw=0.6)
        ax.plot([35, 71], [21, 21], color=INK, lw=0.9, ls="--")
        # BAD: proud / tilted insert
        ax.add_patch(Rectangle((96, 10), 30, 11, fc=ACT_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((106.5, 16), 9, 9, fc=BRASS_LT, ec=INK, lw=1.1))
        draw_red_x(ax, 101, 11, 20, 15)
    elif mode == "tap_guide":
        ax.add_patch(Rectangle((36, 11), 16, 10, fc=CTX_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((49, 9.5), 9, 13, fc=ACT_FILL, ec=INK, lw=1.1))
        ax.plot([50, 70], [16, 16], color=INK, lw=2.2)
        ax.add_patch(Rectangle((96, 11), 16, 10, fc=CTX_FILL, ec=INK, lw=1.0))
        ax.plot([108, 126], [15, 23], color=INK, lw=2.2)
        draw_red_x(ax, 100, 11, 22, 14)
    elif mode == "proud_3mm":
        ax.add_patch(Rectangle((40, 9), 8, 16, fc=ACT_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((48, 15.5), 6, 3, fc=CTX_FILL, ec=INK, lw=0.9))
        ax.add_patch(Rectangle((54, 13), 4, 8, fc=INK, ec=INK, lw=1.0))
        ax.text(64, 17, "3 mm", color=INK, fontsize=8.0, weight="normal", va="center")
        ax.add_patch(Rectangle((100, 9), 8, 16, fc=ACT_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((108, 13), 4, 8, fc=INK, ec=INK, lw=1.0))
        draw_red_x(ax, 100, 10, 18, 14)
    elif mode == "csink_flush":
        ax.add_patch(Rectangle((38, 11), 30, 9, fc=ACT_FILL, ec=INK, lw=1.0))
        ax.add_patch(Polygon([(48, 20), (58, 20), (55, 15.5), (51, 15.5)], closed=True, fc=CTX_FILL, ec=INK, lw=1.0))
        ax.plot([35, 71], [20, 20], color=INK, lw=0.9, ls="--")
        ax.add_patch(Rectangle((96, 11), 30, 9, fc=ACT_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((106, 20), 10, 4.5, fc=CTX_FILL, ec=INK, lw=1.0))
        draw_red_x(ax, 101, 12, 20, 14)
    elif mode == "battery_first":
        ax.add_patch(Rectangle((38, 10), 14, 13, fc=BLUE_FILL, ec=INK, lw=1.0))
        ax.text(45, 16.5, "1", color=INK, fontsize=9, weight="bold", ha="center", va="center")
        ax.add_patch(Rectangle((55, 19), 13, 4, fc=ACT_FILL, ec=INK, lw=1.0))
        ax.text(61.5, 14, "2", color=INK, fontsize=9, weight="bold", ha="center", va="center")
        ax.add_patch(Rectangle((99, 10), 20, 4, fc=ACT_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((102, 16), 14, 10, fc=BLUE_FILL, ec=INK, lw=1.0))
        draw_red_x(ax, 98, 10, 22, 16)
    elif mode == "tnuts_slot":
        # GOOD: rail profile with T-nut inside slot
        ax.add_patch(Rectangle((38, 10), 30, 12, fc=CTX_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((46, 13), 14, 6, fc=ACT_FILL, ec=INK, lw=1.1))
        ax.text(53, 16, "B1", color=INK, fontsize=7.5, weight="bold", ha="center", va="center")
        # BAD: empty rail slot
        ax.add_patch(Rectangle((96, 10), 30, 12, fc=CTX_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((104, 14), 14, 4, fc="white", ec=INK, lw=0.8, ls="--"))
        draw_red_x(ax, 100, 10, 22, 13)
    elif mode == "post_slot":
        # GOOD: two posts with U-slots facing inward toward each other
        ax.add_patch(Polygon([(37, 10), (45, 10), (45, 14), (41, 14), (41, 18), (45, 18), (45, 22), (37, 22)], closed=True, fc=ACT_FILL, ec=INK, lw=1.0))
        ax.add_patch(Polygon([(69, 10), (61, 10), (61, 14), (65, 14), (65, 18), (61, 18), (61, 22), (69, 22)], closed=True, fc=ACT_FILL, ec=INK, lw=1.0))
        ax.plot([46, 60], [16, 16], color=INK, lw=0.9, ls="--")
        # BAD: slots facing outward
        ax.add_patch(Polygon([(105, 10), (97, 10), (97, 14), (101, 14), (101, 18), (97, 18), (97, 22), (105, 22)], closed=True, fc=ACT_FILL, ec=INK, lw=1.0))
        ax.add_patch(Polygon([(117, 10), (125, 10), (125, 14), (121, 14), (121, 18), (125, 18), (125, 22), (117, 22)], closed=True, fc=ACT_FILL, ec=INK, lw=1.0))
        draw_red_x(ax, 99, 10, 24, 13)
    else:
        # Detailed bolted joint vs gap
        ax.add_patch(Rectangle((38, 10), 15, 12, fc=CTX_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((53, 10), 15, 12, fc=ACT_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((49, 14.5), 8, 3, fc=INK, ec=INK))
        ax.add_patch(Rectangle((95, 10), 14, 12, fc=CTX_FILL, ec=INK, lw=1.0))
        ax.add_patch(Rectangle((113, 11), 14, 12, fc=ACT_FILL, ec=INK, lw=1.0))
        draw_red_x(ax, 100, 10, 22, 13)


# =====================================================================================================================
# PAGE 0: HARDWARE BAGS (BAG A..D) & 3D-PRINTED PARTS (P1..P10)
# =====================================================================================================================
def page_00_inventory():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "0", "HARDWARE BAGS (A – D) & PARTS CHECKLIST",
                "Hex Keys: 2.5, 3, 4, 5 mm + 5/32\"   |   Soldering Iron (220–240°C)   |   NO DRILLING (all 46 insert holes pre-printed)",
                [("BAG A", "A1–A3", "46", "Brass Inserts", INK, BG_SOFT),
                 ("BAG B", "B1–B4", "48", "1/4\"-20 Rail HW", INK, BG_SOFT),
                 ("BAG C", "C1–C3", "28", "M4 Screws", INK, BG_SOFT),
                 ("BAG D", "D1–D3", "28", "M5 Screws + Washers", INK, BG_SOFT)])

    ax = fig.add_axes([0.02, 0.03, 0.96, 0.80])
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    # Left half: 4 Hardware Bags (BAG A, BAG B, BAG C, BAG D)
    ax.add_patch(FancyBboxPatch((0.2, 0.4), 48.1, 97.2, boxstyle="round,pad=0,rounding_size=2.0", fc="white", ec=INK, lw=1.4))
    ax.add_patch(FancyBboxPatch((0.2, 91.2), 48.1, 6.4, boxstyle="round,pad=0,rounding_size=2.0", fc=INK, ec=INK))
    ax.text(24.25, 94.4, "HARDWARE BAGS (BAG A  •  BAG B  •  BAG C  •  BAG D)", color="white", fontsize=11.0, weight="bold", ha="center", va="center")

    bags = [
        ("A", "BAG A — BRASS HEAT-SET INSERTS (STEPS 2–5, NO DRILLING)", "insert", [
            ("A1", "12×", "M4 Standard Insert, 7.9 mm (94180A353) — Ø5.6 mm bore"),
            ("A2", "16×", "M4 Short Insert, 4.7 mm (94180A351) — Ø5.6 mm bore"),
            ("A3", "18×", "M5 Insert, 6.7 mm (94180A361) — Ø6.4 mm bore"),
        ]),
        ("B", "BAG B — 1/4\"-20 RAIL FASTENERS (STEPS 6–11)", "tnut", [
            ("B1", "24×", "1/4\"-20 Drop-In T-Nut (6000N501)"),
            ("B2", "20×", "1/4\"-20 × 1/2\" Flat-Head (92210A537)"),
            ("B3", "2×",  "1/4\"-20 × 7/8\" Flat-Head (92210A541)"),
            ("B4", "2×",  "1/4\"-20 × 7/8\" Button-Head (92949A541)"),
        ]),
        ("C", "BAG C — M4 BUTTON-HEAD SCREWS (STEPS 4–11)", "btn_screw", [
            ("C1", "12×", "M4 × 10 mm Button-Head (92095A190)"),
            ("C2", "14×", "M4 × 8 mm Button-Head (92095A189)"),
            ("C3", "2×",  "M4 × 35 mm Button-Head (92095A199)"),
        ]),
        ("D", "BAG D — M5 SCREWS & WASHERS (STEPS 4, 5, 9, 13)", "btn_screw", [
            ("D1", "8×",  "M5 × 10 mm + 8× Washers (92095A210)"),
            ("D2", "4×",  "M5 × 8 mm Button-Head (92095A209)"),
            ("D3", "6×",  "M5 × 12 mm + 2× Washers (92095A211)"),
        ]),
    ]
    y_cursor = 88.5
    for b_let, b_title, default_kind, items in bags:
        h_group = len(items) * 5.0 + 4.0
        ax.add_patch(FancyBboxPatch((1.4, y_cursor - h_group + 1.5), 45.7, h_group, boxstyle="round,pad=0.15,rounding_size=1.8", fc=BG_SOFT, ec=BORDER_LT, lw=1.1))
        draw_bag_icon(ax, 2.5, y_cursor - 5.2, 4.2, 5.6, b_let, r=0.75)
        ax.text(8.0, y_cursor - 1.0, b_title, color=INK, fontsize=8.8, weight="bold", ha="left", va="center")
        y_row = y_cursor - 4.7
        for code, qty, desc in items:
            fkind = "tnut" if code == "B1" else ("flat_screw" if code in ("B2", "B3") else default_kind)
            draw_fastener_icon(ax, 9.2, y_row, 1.8, 3.0, kind=fkind)
            ax.text(11.4, y_row, code, color=INK, fontsize=8.4, weight="bold", ha="left", va="center")
            ax.text(15.2, y_row, qty, color=INK, fontsize=9.2, weight="bold", ha="left", va="center")
            ax.text(19.8, y_row, desc, color=INK_SUB, fontsize=8.4, weight="normal", ha="left", va="center")
            y_row -= 4.9
        y_cursor -= h_group + 1.5

    # Right half: Printed Parts (P1 .. P10) & Frame Parts (F1)
    ax.add_patch(FancyBboxPatch((51.7, 0.4), 48.1, 97.2, boxstyle="round,pad=0,rounding_size=2.0", fc="white", ec=INK, lw=1.4))
    ax.add_patch(FancyBboxPatch((51.7, 91.2), 48.1, 6.4, boxstyle="round,pad=0,rounding_size=2.0", fc=INK, ec=INK))
    ax.text(75.75, 94.4, "3D-PRINTED PARTS (P1 – P10) & 22.5\" FRAME (F1)", color="white", fontsize=11.0, weight="bold", ha="center", va="center")

    parts_list = [
        ("P1", "2×", "Battery Trays (print_tray_battery_0 & _1)", "242 × 167 × 36 mm (Pre-printed Ø5.6 mm A1 bores)"),
        ("P2", "2×", "Breaker Drop Shelves (print_breaker_shelf_0 & _1)", "130 × 168 × 243 mm + 2× EPDM Foam Pads"),
        ("P3", "3×", "Bus Shelf Plates (0: 215mm, 1: 152mm, 2: 195mm)", "Pre-printed Ø6.4 mm A3 bores; Plate 1 = 152 mm (22.5\" box)"),
        ("P4", "6×", "Inverter Plate Tiles (00, 01, 10, 11, 20, 21)", "168.5 × 140 × 6 mm (Pre-printed Ø5.6 & Ø6.4 mm bores)"),
        ("P5", "8×", "Inverter Plate Splines (plate_inverter_splines)", "60 × 18 × 3 mm (Glued across tile joints)"),
        ("P6", "2×", "Inverter Posts (print_post_inverter_0 & _1)", "254 × 24 × 18 mm (Pre-printed Ø5.6 mm top A1 bore)"),
        ("P7", "2×", "Inverter Post Clips (print_post_clip_0 & _1)", "40 × 20 × 28 mm (v12s only)"),
        ("P8", "2×", "Garmin Hanger Upper & Lower Plates", "130 × 149 mm (Pre-printed Ø5.6 mm A2 bores) + 130 × 127 mm"),
        ("P9", "1×", "GX Touch 50 Trim Bezel (print_touch_bezel)", "150 × 108 × 3 mm (Rear panel display frame, Step 12)"),
        ("P10", "1×", "25 mm Rail-End Tap Guide (print_tool_tap_guide)", "46 × 46 × 32 mm cap — Print first for Step 1"),
        ("F1", "12×", "Rails (4× 436.6, 4× 520.0, 4× 230.2) + 5× Panels", "22.5\" Box: 2× Sides (527.5×237), Front/Back (444×237), Lid"),
    ]
    for i, (code, qty, name, sub) in enumerate(parts_list):
        y = 85.5 - i * 7.8
        bg = ACT_FILL if code.startswith("P") else BG_SOFT
        ax.add_patch(FancyBboxPatch((53.0, y - 2.8), 45.5, 6.4, boxstyle="round,pad=0.15,rounding_size=1.5", fc=bg, ec=BORDER_LT, lw=1.0))
        ax.add_patch(FancyBboxPatch((54.2, y - 1.2), 3.8, 3.4, boxstyle="round,pad=0.08,rounding_size=0.8", fc="white", ec=INK, lw=1.0))
        ax.text(56.1, y + 0.5, code, color=INK, fontsize=8.4, weight="bold", ha="center", va="center")
        ax.text(59.6, y + 0.5, qty, color=INK, fontsize=10.5, weight="bold", ha="left", va="center")
        ax.text(65.0, y + 1.5, name, color=INK, fontsize=8.8, weight="bold", ha="left", va="center")
        ax.text(65.0, y - 1.3, sub, color=INK_SUB, fontsize=8.0, weight="normal", ha="left", va="center")

    path = os.path.join(OUT, "page-00-inventory.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 1: CUT & TAP RAILS + CUT PANELS (22.5" / 571.5 mm BOX — DOWN 2.5" FROM 25")
# =====================================================================================================================
def page_01_rails_panels():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "1", "22.5\" BOX (571.5 mm) — CUT & TAP RAILS (F1) + CUT 5 PANELS",
                "Mitre Saw (80T)   |   1/4\"-20 Tap + Cutting Oil   |   Hole Saws: Ø22, Ø29, Ø60 mm + Jigsaw",
                [("PART", "P10", "1", "Tap Guide Cap", INK, BG_SOFT),
                 ("PART", "F1", "12+5", "12 Rails + 5 Panels (22.5\" Box)", INK, BG_SOFT)])

    ax1 = fig.add_axes([0.03, 0.47, 0.54, 0.35])
    ax1.set_xlim(0, 680); ax1.set_ylim(0, 112); ax1.axis("off")
    ax1.text(0, 104, "1.  Cut 12× Rails (F1) for 22.5\" (571.5 mm) Box — Cut ONE end only, keep factory threads", fontsize=9.8, weight="bold", color=INK)
    w_len = 436.6 * 0.68
    ax1.add_patch(Rectangle((10, 68), w_len, 18, fc=CTX_FILL, ec=INK, lw=1.2))
    ax1.text(18, 77, "4× Width (Y) = 436.6 mm (17.19\") — UNCUT", fontsize=8.8, weight="bold", va="center", color=INK)
    ax1.text(10 + w_len + 10, 77, "3× donor + 1× Mod Kit bar", fontsize=8.4, weight="normal", color=INK_SUB, va="center")
    full_d = 584.2 * 0.68; cut_d = 520.0 * 0.68
    ax1.add_patch(Rectangle((10, 36), cut_d, 18, fc=ACT_FILL, ec=INK, lw=1.2))
    ax1.add_patch(Rectangle((10 + cut_d, 36), full_d - cut_d, 18, fc="white", ec=CTX_EDGE, lw=0.9, ls="--"))
    ax1.plot([10 + cut_d, 10 + cut_d], [32, 58], color=RED_X, lw=1.8)
    ax1.text(18, 45, "4× Depth (X) = 520.0 mm (20.47\")  [−64.2 mm / −2.5\" off 584.2 mm]", fontsize=8.8, weight="bold", va="center", color=INK)
    ax1.text(10 + full_d + 10, 45, "Tap 1/4\"-20", fontsize=8.6, weight="bold", color=RED_X, va="center")
    full_h = 508.0 * 0.68; cut_h = 230.2 * 0.68
    ax1.add_patch(Rectangle((10, 4), cut_h, 18, fc=ACT_FILL, ec=INK, lw=1.2))
    ax1.add_patch(Rectangle((10 + cut_h, 4), full_h - cut_h, 18, fc="white", ec=CTX_EDGE, lw=0.9, ls="--"))
    ax1.plot([10 + cut_h, 10 + cut_h], [0, 26], color=RED_X, lw=1.8)
    ax1.text(16, 13, "4× Height (Z) = 230.2 mm (9.06\")", fontsize=8.8, weight="bold", va="center", color=INK)
    ax1.text(10 + cut_h + 8, 13, "[−277.8 mm off 508.0 mm]  —  Tap 1/4\"-20", fontsize=8.4, weight="normal", color=INK_SUB, va="center")

    ax2 = fig.add_axes([0.59, 0.61, 0.38, 0.21])
    ax2.set_xlim(0, 100); ax2.set_ylim(22, 95); ax2.axis("off")
    ax2.text(2, 88, "2.  Tap 8× cut rail ends with P10 guide", fontsize=10.0, weight="bold", color=INK)
    ax2.add_patch(Rectangle((8, 36), 34, 28, fc=CTX_FILL, ec=INK, lw=1.2))
    ax2.add_patch(Polygon([(30, 28), (58, 28), (58, 72), (30, 72), (30, 64), (42, 64), (42, 36), (30, 36)],
                          closed=True, fc=ACT_FILL, ec=INK, lw=1.2))
    ax2.add_patch(Rectangle((42, 46), 16, 8, fc="white", ec=INK, lw=0.9))
    ax2.add_patch(Rectangle((34, 47.5), 48, 5, fc=INK_SUB, ec=INK, lw=1.0))
    ax2.text(44, 77, "P10", fontsize=9.2, weight="bold", color=INK, ha="center")

    ikea_ux_panel(fig, [0.59, 0.44, 0.38, 0.16], "tap_guide", "P10 + Oil (90°)", "Not freehand")

    ax3 = fig.add_axes([0.03, 0.03, 0.48, 0.40])
    ax3.set_aspect("equal"); ax3.axis("off")
    pw, ph = 444.0, 237.0
    ax3.add_patch(Rectangle((0, 0), pw, ph, fc=CTX_FILL, ec=INK, lw=1.5))
    ax3.text(pw / 2, ph + 14, "3.  Front Panel — 444.0 × 237.0 mm  (10 Port Cutouts, X from Inboard)", fontsize=9.4, weight="bold", ha="center", color=INK)
    ports = [
        ("Ø60\n(39,50)", 39, 50, "c", 60),
        ("Ø60\n(39,120)", 39, 120, "c", 60),
        ("Ø29\n(39,175)", 39, 175, "c", 29),
        ("48×37\n(92,40)", 92, 40, "r", (48, 37)),
        ("48×37\n(92,96)", 92, 96, "r", (48, 37)),
        ("Ø22\n(92,140)", 92, 140, "c", 22),
        ("Ø22\n(92,173)", 92, 173, "c", 22),
        ("Ø29\n(124,135)", 124, 135, "c", 29),
        ("Ø29\n(124,175)", 124, 175, "c", 29),
        ("26×56\n(247,88)", 247, 88, "r", (26, 56)),
    ]
    for lbl, x, z, kind, sz in ports:
        if kind == "c":
            ax3.add_patch(Circle((x, z), sz / 2, fc="white", ec=INK, lw=1.1))
        else:
            w_, h_ = sz
            ax3.add_patch(Rectangle((x - w_ / 2, z - h_ / 2), w_, h_, fc="white", ec=INK, lw=1.1))
        ax3.text(x, z, lbl, ha="center", va="center", fontsize=5.8, weight="normal", color=INK)
    ax3.text(-8, ph / 2, "Inboard (X=0)", rotation=90, ha="right", va="center", fontsize=8.0, weight="normal", color=INK_SUB)
    ax3.set_xlim(-40, pw + 20); ax3.set_ylim(-20, ph + 30)

    ax4 = fig.add_axes([0.53, 0.03, 0.44, 0.40])
    ax4.set_xlim(0, 100); ax4.set_ylim(0, 62); ax4.set_aspect("equal"); ax4.axis("off")
    ax4.text(50, 59, "4.  Back Panel (444 × 237) + 2× Side Panels (527.5 × 237) + Lid", fontsize=9.4, weight="bold", ha="center", color=INK)
    # Left of ax4: Back Panel with GX Touch 50 cutout
    ax4.add_patch(Rectangle((2, 19), 46, 34, fc=CTX_FILL, ec=INK, lw=1.3))
    ax4.add_patch(Rectangle((4.5, 33), 14, 12, fc="white", ec=INK, lw=1.1))
    ax4.text(11.5, 39, "GX Touch\n128×86", ha="center", va="center", fontsize=6.5, weight="bold", color=INK)
    ax4.text(25, 25, "Back Panel\n444.0 × 237.0 mm\n(Cutout center X=83, Z=138)", ha="center", va="center", fontsize=7.2, color=INK)
    # Right of ax4: 2x Side Panels shortened 2.5" (64.2 mm) from 591.7 mm -> 527.5 x 237.0 mm
    ax4.add_patch(Rectangle((52, 19), 38, 34, fc=ACT_FILL, ec=INK, lw=1.3))
    ax4.add_patch(Rectangle((90, 19), 7, 34, fc="white", ec=CTX_EDGE, lw=0.9, ls="--"))
    ax4.plot([90, 90], [17, 55], color=RED_X, lw=1.6)
    ax4.text(71, 36, "2× Side Panels\n527.5 × 237.0 mm\n(20.77\" × 9.33\")\n[−64.2 mm / −2.5\" off 591.7]", ha="center", va="center", fontsize=7.2, weight="bold", color=INK)
    # Bottom summary pill for Lid & 22.5" Panel Schedule
    ax4.add_patch(FancyBboxPatch((2, 1.5), 95, 13.5, boxstyle="round,pad=0,rounding_size=2.2", fc=BG_SOFT, ec=INK, lw=1.0))
    ax4.text(49.5, 8.2, "1× Top Lid Panel (22.5\" Box):   571.5 × 488.1 mm (22.50\" × 19.22\", v12s flat lid)\n"
                        "or  527.5 × 444.0 mm (20.77\" × 17.48\", v13 slot-captured lid — shortened 2.5\" from 591.7 mm)",
             ha="center", va="center", fontsize=7.4, weight="normal", color=INK, linespacing=1.25)

    path = os.path.join(OUT, "page-01-rails-panels.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 2: BATTERY TRAYS — PRESS 10× A1 INSERTS + SOLDERING IRON HEAT-SERT GUIDE
# =====================================================================================================================
def page_02_tray_inserts():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "2", "BATTERY TRAYS (P1 × 2) — PRESS 10× A1 INSERTS (NO DRILLING)",
                "Soldering Iron (220–240°C PETG / 250–260°C ASA)   |   Flat Metal Ruler   |   NO DRILLING",
                [("PART", "P1", "2", "Battery Trays", INK, BG_SOFT),
                 ("BAG A", "A1", "10", "M4 Standard 7.9 mm (Ø5.6 bore)", INK, BG_SOFT)])

    # Left: Exact analytic HLR vector CAD view of print_tray_battery_0
    ax3d = fig.add_axes([0.02, 0.25, 0.43, 0.58])
    render_3d_hlr(ax3d, "", only_names={"print_tray_battery_0"}, elev=28, azim=-48,
                  title="P1 × 2  (print_tray_battery_0 & _1 — Ø5.6 mm holes pre-printed)")

    # Top-Right: Calm IKEA 2D technical drawing
    ax = fig.add_axes([0.47, 0.26, 0.51, 0.57])
    ax.set_xlim(-25, 265); ax.set_ylim(-35, 205); ax.set_aspect("equal"); ax.axis("off")

    fd, fw = 242.0, 167.0
    ax.add_patch(Rectangle((0, 15), fd, fw, fc=CTX_FILL, ec=INK, lw=1.4))
    ax.add_patch(Rectangle((6, 21), fd - 12, 140, fc="white", ec=INK, lw=1.0))
    ax.add_patch(Rectangle((0, 15 + fw - 21), fd, 21, fc=ACT_FILL, ec=INK, lw=1.2))
    ax.text(fd / 2, 15 + fw + 13, "21 mm Inboard Wall (Pre-printed Ø5.6 mm bores)", ha="center", va="center", fontsize=8.2, weight="bold", color=INK)

    # (1) 2x A1 on top of 21 mm wall
    top_pts = [(81, 15 + fw - 8), (161, 15 + fw - 8)]
    for hx, hy in top_pts:
        ax.add_patch(Circle((hx, hy), 5.5, fc=BRASS, ec=INK, lw=1.1, zorder=4))
    bag_callout(ax, top_pts, (68, 114), "BAG A", "A1", "2", sub="Top wall (×2 Trays = 4)")

    # (2) 3x A1 horizontally into outer column face
    side_pts = [(40, 15 + fw + 3), (100, 15 + fw + 3), (140, 15 + fw + 3), (200, 15 + fw + 3)]
    for hx, hy in side_pts:
        ax.add_patch(Rectangle((hx - 4.0, hy - 4.5), 8, 6, fc=BRASS, ec=INK, lw=1.0, zorder=4))
    bag_callout(ax, [(100, 15 + fw + 3), (140, 15 + fw + 3)], (175, 114),
                "BAG A", "A1", "3", sub="Side wall (×2 Trays = 6)")

    # (3) 4x Countersunk B2 holes — NO A1 INSERTS!
    csink_pts = [(70, 18), (172, 18), (3, 44), (3, 155)]
    for cx, cy in csink_pts:
        ax.add_patch(Circle((cx, cy), 4.5, fc="white", ec=INK, lw=1.0, zorder=4))
    no_callout(ax, [(70, 18), (172, 18)], (121, -18), bad_code="A1", right_note="Step 8: BAG B • B2")

    # Bottom Full-Width: 3-Step Soldering Iron "Heat-Sert" Guide + Flush vs Proud check
    ax_g = fig.add_axes([0.02, 0.03, 0.56, 0.19])
    ax_g.set_xlim(0, 168); ax_g.set_ylim(0, 34); ax_g.set_aspect("equal"); ax_g.axis("off")
    ax_g.add_patch(FancyBboxPatch((0.8, 1.0), 166.4, 32.0, boxstyle="round,pad=0,rounding_size=3.8", fc=BG_SOFT, ec=INK, lw=1.4))
    ax_g.add_patch(FancyBboxPatch((0.8, 25.5), 166.4, 7.5, boxstyle="round,pad=0,rounding_size=3.2", fc=INK, ec=INK))
    ax_g.text(84.0, 29.2, "HOW TO INSTALL BRASS HEAT-SERTS WITH A SOLDERING IRON  (ALL 46 HOLES PRE-PRINTED — NO DRILLING)",
              color="white", fontsize=8.4, weight="bold", ha="center", va="center")
    steps_hs = [
        (4.0,  "1. Set Iron Temp", "220–240°C (PETG)\n250–260°C (ASA/ABS)\nUse conical tip or M4/M5 adapter"),
        (59.0, "2. Tapered End Down (90°)", "Set narrow pilot collar into\npre-printed bore; press straight\ndown 2–3 s until nearly flush"),
        (115.0, "3. Flatten Dead Flush", "Withdraw iron straight up &\nimmediately press flat with a\nmetal ruler for 3 s to cool"),
    ]
    for sx, stitle, sbody in steps_hs:
        ax_g.add_patch(FancyBboxPatch((sx, 3.0), 50.5, 20.5, boxstyle="round,pad=0,rounding_size=2.2", fc="white", ec=BORDER_LT, lw=1.0))
        ax_g.text(sx + 25.25, 19.8, stitle, color=INK, fontsize=8.0, weight="bold", ha="center", va="center")
        ax_g.text(sx + 25.25, 10.2, sbody, color=INK_SUB, fontsize=7.1, weight="normal", ha="center", va="center", linespacing=1.22)

    ikea_ux_panel(fig, [0.60, 0.03, 0.38, 0.19], "insert_flush", "Flush (0 mm)", "Not proud / tilted")

    path = os.path.join(OUT, "page-02-tray-inserts.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 3: BREAKER SHELVES (P2), GARMIN (P8) & POSTS (P6) — BAG A INSERTS & FOAM PADS
# =====================================================================================================================
def page_03_shelf_post_inserts():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "3", "DROP SHELVES (P2), GARMIN (P8) & POSTS (P6) — BAG A (NO DRILLING)",
                "Soldering Iron (220–240°C)   |   All Ø5.6 & Ø6.4 mm holes pre-printed — No drilling",
                [("BAG A", "A3", "4", "M5 6.7 mm (P2)", INK, BG_SOFT),
                 ("BAG A", "A2", "2", "M4 Short 4.7 mm (P8)", INK, BG_SOFT),
                 ("BAG A", "A1", "2", "M4 Std 7.9 mm (P6)", INK, BG_SOFT)])

    ax3d = fig.add_axes([0.02, 0.24, 0.35, 0.58])
    render_3d_hlr(ax3d, "", only_names={"print_breaker_shelf_0"}, elev=26, azim=-48,
                  title="P2 × 2  (Breaker Drop Shelves)")

    ax1 = fig.add_axes([0.38, 0.24, 0.30, 0.58])
    ax1.set_xlim(-15, 185); ax1.set_ylim(-50, 210); ax1.set_aspect("equal"); ax1.axis("off")
    ax1.add_patch(Rectangle((20, 20), 130, 168, fc=CTX_FILL, ec=INK, lw=1.3))
    ax1.add_patch(Rectangle((20, 20), 130, 6, fc=ACT_FILL, ec=INK, lw=1.0))
    ax1.add_patch(Rectangle((20, 20 + 147), 130, 21, fc=ACT_FILL, ec=INK, lw=1.0))
    pts_p2 = [(53, 125), (110, 152)]
    for bx, by in pts_p2:
        ax1.add_patch(Circle((bx, by), 5.2, fc=BRASS, ec=INK, lw=1.1, zorder=4))
    bag_callout(ax1, pts_p2, (85, 72), "BAG A", "A3", "2", sub="×2 Shelves = 4 (Ø6.4 bore)")

    ax1.add_patch(FancyBboxPatch((14, -36), 142, 38, boxstyle="round,pad=0.2,rounding_size=5.0", fc=BG_SOFT, ec=INK, lw=1.1))
    ax1.text(85, -17, "Stick EPDM foam pad (×2)\nunderneath shelf plate", color=INK, fontsize=8.5, weight="normal", ha="center", va="center")

    ax2 = fig.add_axes([0.70, 0.24, 0.28, 0.58])
    ax2.set_xlim(0, 180); ax2.set_ylim(-50, 210); ax2.set_aspect("equal"); ax2.axis("off")
    ax2.add_patch(Rectangle((25, 85), 130, 105, fc=CTX_FILL, ec=INK, lw=1.3))
    ax2.text(90, 175, "P8 (Upper Garmin)", ha="center", fontsize=8.8, weight="normal", color=INK_SUB)
    pts_p8 = [(47.5, 138), (132.5, 138)]
    for gx_, gy_ in pts_p8:
        ax2.add_patch(Circle((gx_, gy_), 5.0, fc=BRASS, ec=INK, lw=1.1, zorder=4))
    bag_callout(ax2, pts_p8, (90, 102), "BAG A", "A2", "2", sub="Pre-printed Ø5.6 bore")

    for px, lbl in ((30, "P6: Post 0"), (120, "P6: Post 1")):
        ax2.add_patch(Rectangle((px, -42), 30, 100, fc=CTX_FILL, ec=INK, lw=1.3))
        ax2.add_patch(Circle((px + 15, 58), 5.0, fc=BRASS, ec=INK, lw=1.1, zorder=4))
        ax2.text(px + 15, 5, lbl, ha="center", va="center", rotation=90, fontsize=8.4, weight="normal", color=INK_SUB)
    bag_callout(ax2, [(45, 58), (135, 58)], (90, 14), "BAG A", "A1", "2", sub="Top end (Ø5.6 bore)")

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "insert_flush", "Flush + foam under", "Not proud / tilted")

    path = os.path.join(OUT, "page-03-shelf-post-inserts.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 4: INVERTER PLATE SUB-ASSEMBLY (P4 + P5 + BAG A / C / D)
# =====================================================================================================================
def page_04_plate_subassembly():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "4", "INVERTER PLATE (P4 + P5) — BAG A, BAG C & BAG D (NO DRILLING)",
                "CA Glue   |   Soldering Iron (220–240°C)   |   2.5 mm & 3 mm Hex Keys   |   NO DRILLING",
                [("BAG A", "A2", "14", "M4 Short (Ø5.6 bore)", INK, BG_SOFT),
                 ("BAG A", "A3", "8", "M5 6.7 mm (Ø6.4 bore)", INK, BG_SOFT),
                 ("BAG C", "C2", "8", "M4 × 8 (Cerbo/Orion)", INK, BG_SOFT),
                 ("BAG D", "D1+D2", "8", "4× D1 + 4× D2", INK, BG_SOFT)])

    W_pl, H_pl = 505.5, 256.0
    zp = 21.0; px0 = X0 + 18.0 - 10.0

    # Left: Column Face
    ax1 = fig.add_axes([0.02, 0.22, 0.47, 0.62])
    ax1.set_aspect("equal"); ax1.axis("off")
    ax1.text(W_pl / 2, H_pl + 22, "1.  Column Face — 14× A2 (Ø5.6) + 4× A3 (Ø6.4)  [Pre-printed]", ha="center", fontsize=9.8, weight="bold", color=INK)
    ax1.add_patch(Rectangle((0, 0), W_pl, H_pl, fc=CTX_FILL, ec=INK, lw=1.5))
    for cx in (168.5, 337.0):
        ax1.plot([cx, cx], [0, H_pl], color=CTX_EDGE, lw=0.9, ls="--")
        for sz in (162, 218):
            ax1.add_patch(Rectangle((cx - 30, sz - 9), 60, 18, fc=ACT_FILL, ec=INK, lw=0.9))

    wx = (D - 145.0) - px0; wz = 40.0 - zp
    ax1.add_patch(FancyBboxPatch((wx, wz), 70, 70, boxstyle="round,pad=0,rounding_size=10", fc="white", ec=INK, lw=1.1))
    ax1.text(wx + 35, wz + 35, "70×70\nWindow", ha="center", va="center", fontsize=7.2, color=INK_SUB)

    sill_xs = [32.0, 146.7, 226.7, 278.8, 358.8, 473.5]
    for sx in sill_xs:
        ax1.add_patch(Circle((sx, 7.0), 5.8, fc=BRASS, ec=INK, lw=1.0, zorder=4))
    bag_callout(ax1, [(226.7, 7.0), (278.8, 7.0)], (W_pl / 2, -38), "BAG A", "A2", "6", sub="Bottom sill (Z=7)")

    units_info = [
        ("mppt_up", 50.0, 80.0, "MPPT 100/30\n(130 × 186 mm)\n4× A3 (BAG A)\n4× D2 (BAG D)"),
        ("cerbo", 190.0, 188.0, "Cerbo GX\n4× A2 (BAG A)\n4× C2 (BAG C)"),
        ("orion", 354.0, 118.0, "Orion XS\n4× A2 (BAG A)\n4× C2 (BAG C)"),
    ]
    for ukey, x0_box, z0_box, lbl in units_info:
        c = cage.COMPONENTS[ukey]
        ux, uz = x0_box - px0, z0_box - zp
        ax1.add_patch(Rectangle((ux, uz), c.w, c.h, fc="white", ec=INK, lw=1.15, ls="--"))
        ax1.text(ux + c.w / 2, uz + c.h / 2, lbl, ha="center", va="center", fontsize=7.6, weight="normal", color=INK)
        for (hu, hv) in cage.HOLES[ukey]:
            ax1.add_patch(Circle((ux + hu, uz + hv), 5.8, fc=BRASS, ec=INK, lw=1.0, zorder=4))
    ax1.set_xlim(-20, W_pl + 20); ax1.set_ylim(-65, H_pl + 40)

    # Right: Inverter Face
    ax2 = fig.add_axes([0.51, 0.22, 0.47, 0.62])
    ax2.set_aspect("equal"); ax2.axis("off")
    ax2.text(W_pl / 2, H_pl + 22, "2.  Inverter Face — 4× A3 + 4× D1 (leave 3 mm gap)", ha="center", fontsize=9.8, weight="bold", color=INK)
    ax2.add_patch(Rectangle((0, 0), W_pl, H_pl, fc=CTX_FILL, ec=INK, lw=1.5))
    inv_x0 = W_pl - ((cage.V13["inv_x"] - px0) + 375.0); inv_z0 = 22.0 - zp
    ax2.add_patch(Rectangle((inv_x0, inv_z0), 375.0, 249.0, fc="white", ec=INK_SUB, lw=1.1, ls="--"))
    mp_pts = []
    for (hu, hv) in cage.HOLES["multiplus_1200_long"]:
        mx = W_pl - ((cage.V13["inv_x"] - px0) + hu); mz = inv_z0 + hv
        mp_pts.append((mx, mz))
        ax2.add_patch(Circle((mx, mz), 6.5, fc=BRASS, ec=INK, lw=1.1, zorder=4))
    for cx in (W_pl - 168.5, W_pl - 337.0):
        ax2.plot([cx, cx], [0, H_pl], color=CTX_EDGE, lw=0.9, ls="--")
        for sz in (38, 94):
            ax2.add_patch(Rectangle((cx - 30, sz - 9), 60, 18, fc=ACT_FILL, ec=INK, lw=0.9))
    bag_callout(ax2, [mp_pts[0], mp_pts[1]], (W_pl / 2, 125), "BAG A", "A3", "4", sub="+ 4× D1 (BAG D) — leave 3 mm gap")
    ax2.set_xlim(-20, W_pl + 20); ax2.set_ylim(-65, H_pl + 40)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "proud_3mm", "3 mm gap (keyhole)", "Not tight to plate")

    path = os.path.join(OUT, "page-04-plate-subassembly.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 5: BUS SHELF (P3) & GARMIN (P8) SUB-ASSEMBLIES — BAG A, BAG C & BAG D
# =====================================================================================================================
def page_05_bus_subassembly():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "5", "BUS SHELF (P3 × 3) & GARMIN (P8) — BAG A, BAG C & BAG D (NO DRILLING)",
                "CA Glue   |   Soldering Iron (220–240°C)   |   2.5 mm & 3 mm Hex Keys   |   NO DRILLING",
                [("PART", "P3", "3", "Plates 0, 1 (152mm), 2", INK, BG_SOFT),
                 ("BAG A", "A3", "6", "M5 6.7 mm (Ø6.4 bore)", INK, BG_SOFT),
                 ("BAG D", "D3", "6", "M5 × 12 + 2 Washers", INK, BG_SOFT),
                 ("BAG C", "C1", "2", "M4 × 10 (Garmin)", INK, BG_SOFT)])

    ax1 = fig.add_axes([0.03, 0.23, 0.62, 0.60])
    ax1.set_aspect("equal"); ax1.axis("off")
    b0, b1, b2 = 194.7, 326.8, 521.5
    ax1.add_patch(Rectangle((0, 0), b0, 110, fc=CTX_FILL, ec=INK, lw=1.3))
    ax1.add_patch(Rectangle((b0, 0), b1 - b0, 110, fc=ACT_FILL, ec=INK, lw=1.5))
    ax1.add_patch(Rectangle((b1, 0), b2 - b1, 110, fc=CTX_FILL, ec=INK, lw=1.3))
    ax1.text(b0 / 2, 124, "P3-0 (215 mm)", ha="center", fontsize=9.0, weight="normal", color=INK)
    ax1.text((b0 + b1) / 2, 124, "P3-1 (152 mm — 22.5\" box)", ha="center", fontsize=9.0, weight="bold", color=INK)
    ax1.text((b1 + b2) / 2, 124, "P3-2 (195 mm)", ha="center", fontsize=9.0, weight="normal", color=INK)

    ax1.add_patch(Rectangle((201, 16), 120, 44, fc="white", ec=INK, lw=1.2))
    ax1.text(261, 38, "SmartShunt", ha="center", va="center", fontsize=8.4, weight="normal", color=INK)
    sh_pts = [(213, 38), (309, 38)]
    for sx, sy in sh_pts:
        ax1.add_patch(Circle((sx, sy), 4.8, fc=BRASS, ec=INK, lw=1.0, zorder=4))
    for bx, lbl in ((20, "+ Bus Bar"), (341, "− Bus Bar")):
        ax1.add_patch(Rectangle((bx, 62), 145, 32, fc="white", ec=INK, lw=1.2))
        ax1.text(bx + 72.5, 78, lbl, ha="center", va="center", fontsize=8.4, weight="normal", color=INK)
        for hx in (bx + 18, bx + 127):
            ax1.add_patch(Circle((hx, 78), 4.8, fc=BRASS, ec=INK, lw=1.0, zorder=4))
    bag_callout(ax1, sh_pts, (261, -36), "BAG A", "A3", "6", sub="+ 6× D3 (BAG D) — Pre-printed Ø6.4 mm bores")
    ax1.set_xlim(-25, 550); ax1.set_ylim(-65, 155)

    ax2 = fig.add_axes([0.67, 0.23, 0.30, 0.60])
    ax2.set_aspect("equal"); ax2.axis("off")
    ax2.add_patch(Rectangle((15, 20), 130, 149, fc=CTX_FILL, ec=INK, lw=1.3))
    ax2.add_patch(Rectangle((17.5, 42), 125, 75, fc="white", ec=INK, lw=1.2))
    ax2.text(80, 80, "Garmin", ha="center", va="center", fontsize=9.0, weight="normal", color=INK)
    g_pts = [(37.5, 79.5), (122.5, 79.5)]
    for gx_, gy_ in g_pts:
        ax2.add_patch(Circle((gx_, gy_), 5.0, fc=BRASS, ec=INK, lw=1.0, zorder=4))
    bag_callout(ax2, g_pts, (80, -18), "BAG C", "C1", "2")
    ax2.set_xlim(-10, 170); ax2.set_ylim(-45, 185)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "insert_flush", "Flush in Ø6.4 mm bores", "Not proud / tilted")

    path = os.path.join(OUT, "page-05-bus-subassembly.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 6: ASSEMBLE FRAME & PRE-LOAD 24× B1 T-NUTS (BAG B)
# =====================================================================================================================
def page_06_frame_tnuts():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "6", "ASSEMBLE FRAME (F1) & LOAD 24× B1 T-NUTS",
                "Corner-Cube Driver   |   Tape Measure",
                [("PART", "F1", "12", "Rails + 8 Cubes", INK, BG_SOFT),
                 ("BAG B", "B1", "24", "1/4\"-20 Drop-In T-Nuts", INK, BG_SOFT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.43, 0.60])
    render_3d_hlr(ax3d, r"^(cube_|bar_|panel_)", elev=24, azim=-50,
                  title="1.  Bolt rails + slide 4 panels into slots")

    ax = fig.add_axes([0.46, 0.22, 0.52, 0.60])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=CTX_FILL, ec=INK, lw=1.2))
    for cx in (0, D - B):
        for cy in (0, W - B):
            ax.add_patch(Rectangle((cx, cy), B, B, fc=INK, ec=INK))

    for x in (70, 172, 349.5, 451.5):
        ax.plot(X0 + x, B, marker="^", color=INK, ms=7.5)
        ax.text(X0 + x, B + 10, f"{x:.0f}", ha="center", fontsize=7.8, weight="normal", color=INK)
    for x in (81, 161, 360.5, 440.5):
        ax.plot(X0 + x, 4, marker="v", color=INK_SUB, ms=7.5)
        ax.text(X0 + x, -15, f"{x:.0f}", ha="center", fontsize=7.8, weight="normal", color=INK_SUB)
    for x in (341.5, 421.5):
        ax.plot(X0 + x, W - B, marker="v", color=INK, ms=7.5)
        ax.plot(X0 + x, W - 4, marker="^", color=INK_SUB, ms=7.5)
        ax.text(X0 + x, W - B - 16, f"{x:.0f}", ha="center", fontsize=7.8, weight="normal", color=INK)
    for y in (29, 140, 198, 238, 281):
        ax.plot(B, Y0 + y, marker=">", color=INK, ms=7.5)
        ax.text(B + 9, Y0 + y, f"{y}", va="center", fontsize=7.8, weight="normal", color=INK)
        ax.plot(D - B, Y0 + y, marker="<", color=INK, ms=7.5)
        ax.text(D - B - 9, Y0 + y, f"{y}", ha="right", va="center", fontsize=7.8, weight="normal", color=INK)
    ax.plot(4, Y0 + 291, marker=">", color=INK_SUB, ms=7.5)
    ax.plot(D - 4, Y0 + 291, marker="<", color=INK_SUB, ms=7.5)

    bag_callout(ax, [(X0 + 172, B), (B, Y0 + 198)], (285, 295), "BAG B", "B1", "16", sub="Bottom rails (Z=12.5)")
    bag_callout(ax, [(X0 + 161, 4)], (285, 155), "BAG B", "B1", "8", sub="Top rails (Z=269)")
    ax.set_xlim(-55, D + 55); ax.set_ylim(-35, W + 25)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "tnuts_slot", "Load 24× B1 now", "Not empty slots")

    path = os.path.join(OUT, "page-06-frame-tnuts.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 7: INSTALL INVERTER POSTS (P6 × 2) WITH BAG B • B4
# =====================================================================================================================
def page_07_posts():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "7", "INVERTER POSTS (P6 × 2) — BAG B • B4",
                "5/32\" Hex Key   |   Tape Measure",
                [("PART", "P6", "2", "Posts 0 & 1", INK, BG_SOFT),
                 ("BAG B", "B4", "2", "1/4\"-20 × 7/8\" Button-Head", INK, BG_SOFT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.44, 0.60])
    render_3d_hlr(ax3d, r"^print_post_inverter_", [r"^(cube_|bar_)"],
                  title="P6 × 2  (Y = 281 mm)")

    ax = fig.add_axes([0.47, 0.22, 0.50, 0.60])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=CTX_FILL, ec=INK, lw=1.2))
    p0, p1 = bb["print_post_inverter_0"], bb["print_post_inverter_1"]
    for p in (p0, p1):
        ax.add_patch(Rectangle((p.xmin, p.ymin), p.xlen, p.ylen, fc=ACT_FILL, ec=INK, lw=1.3))
    yc = (p0.ymin + p0.ymax) / 2
    ax.add_patch(FancyArrowPatch((D * 0.5, Y0), (D * 0.5, yc), arrowstyle="<|-|>", mutation_scale=12, lw=1.1, color=INK))
    ax.text(D * 0.5, (Y0 + yc) / 2, "Y = 281 mm", ha="center", va="center",
            fontsize=8.8, weight="normal", color=INK, bbox=dict(boxstyle="round,pad=0.45,rounding_size=0.8", fc="white", ec=INK, lw=0.9))

    bag_callout(ax, [(p0.xmin + 4, yc), (p1.xmax - 4, yc)], (285, 360), "BAG B", "B4", "2", sub="Into B1 at Y=281")
    ax.set_xlim(-45, D + 45); ax.set_ylim(-25, W + 25)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "post_slot", "Slots face inward", "Not outward")

    path = os.path.join(OUT, "page-07-posts.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 8: INSTALL BATTERY TRAYS (P1 × 2) WITH BAG B • B2
# =====================================================================================================================
def page_08_trays():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "8", "BATTERY TRAYS (P1 × 2) — BAG B • B2",
                "5/32\" Hex Key",
                [("PART", "P1", "2", "Trays 0 & 1", INK, BG_SOFT),
                 ("BAG B", "B2", "8", "1/4\"-20 × 1/2\" Flat-Head", INK, BG_SOFT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.44, 0.60])
    render_3d_hlr(ax3d, r"^print_tray_battery_", [r"^(cube_|bar_|print_post_inverter_)"],
                  title="P1 × 2  (Back = Tray 0, Front = Tray 1)")

    ax = fig.add_axes([0.47, 0.22, 0.50, 0.60])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=CTX_FILL, ec=INK, lw=1.2))
    t0, t1 = bb["print_tray_battery_0"], bb["print_tray_battery_1"]
    out_pts, end_pts = [], []
    for idx, (tr, lbl, x_nuts) in enumerate(((t0, "P1-0", (70, 172)), (t1, "P1-1", (349.5, 451.5)))):
        ax.add_patch(Rectangle((tr.xmin, tr.ymin), tr.xlen, tr.ylen, fc=ACT_FILL, ec=INK, lw=1.3))
        ax.add_patch(Rectangle((tr.xmin + 6, tr.ymin + 6), tr.xlen - 12, 140, fc="white", ec=INK, lw=0.9))
        ax.text((tr.xmin + tr.xmax) / 2, tr.ymin + 76, lbl, ha="center", va="center", fontsize=10, weight="bold", color=INK)
        for xn in x_nuts:
            pt = (X0 + xn, tr.ymin + 10)
            out_pts.append(pt)
            ax.add_patch(Circle(pt, 5.2, fc=CTX_FILL, ec=INK, lw=1.0, zorder=4))
        for yn in (29, 140):
            bx = tr.xmin + 10 if idx == 0 else tr.xmax - 10
            pt = (bx, Y0 + yn)
            end_pts.append(pt)
            ax.add_patch(Circle(pt, 5.2, fc=CTX_FILL, ec=INK, lw=1.0, zorder=4))

    bag_callout(ax, [out_pts[1], out_pts[2]], (285, 255), "BAG B", "B2", "4", sub="Outer wall")
    bag_callout(ax, [end_pts[1], end_pts[3]], (285, 365), "BAG B", "B2", "4", sub="End walls")
    ax.set_xlim(-45, D + 45); ax.set_ylim(-25, W + 25)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "csink_flush", "B2 flush in floor", "Not proud head")

    path = os.path.join(OUT, "page-08-trays.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 9: DROP IN BATTERIES FIRST, THEN CLAMP DROP SHELVES (P2) — BAG C, BAG B & BAG D
# =====================================================================================================================
def page_09_batteries_shelves():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "9", "BATTERIES (1st) + DROP SHELVES (P2) — BAG C, B & D",
                "2.5 mm Hex Key (C1)   |   5/32\" Hex Key (B2)   |   3 mm Hex Key (D1)",
                [("PART", "P2", "2", "Drop Shelves", INK, BG_SOFT),
                 ("BAG C", "C1", "4", "M4 × 10 (Feet 1st)", INK, BG_SOFT),
                 ("BAG B", "B2", "4", "1/4-20 × 1/2\" (Top 2nd)", INK, BG_SOFT),
                 ("BAG D", "D1", "4", "M5 × 10 + Washers", INK, BG_SOFT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.45, 0.60])
    render_3d_hlr(ax3d, r"^(battery_|print_breaker_shelf_|power_breaker_shelf_)",
                  [r"^(cube_|bar_|print_post_inverter_|print_tray_battery_)"],
                  title="1. Batteries in   /   2. Shelves clamp on top")

    ax = fig.add_axes([0.48, 0.22, 0.49, 0.60])
    ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), B, B, fc=CTX_FILL, ec=INK, lw=1.2))
    ax.add_patch(Rectangle((0, H - B), B, B, fc=CTX_FILL, ec=INK, lw=1.2))
    ax.add_patch(Polygon([(26, 0), (193, 0), (193, 36), (172, 36), (172, 6), (32, 6), (32, 36), (26, 36)],
                         closed=True, fc=CTX_FILL, ec=INK, lw=1.2))
    ax.add_patch(Rectangle((32.5, 6), 139, 208, fc=BLUE_FILL, ec=INK, lw=1.3))
    ax.text(102, 130, "1.  Battery in first\n(×2)", ha="center", va="center", fontsize=10.2, weight="bold", color=INK)
    ax.add_patch(Rectangle((32.5, 214), 139, 3, fc=INK, ec=INK))
    ax.add_patch(Polygon([(25, 215), (178, 215), (178, 36), (193, 36), (193, 42), (184, 42), (184, 239),
                          (178, 239), (178, 221), (31, 221), (31, 278.7), (25, 278.7)],
                         closed=True, fc=ACT_FILL, ec=INK, lw=1.3))
    ax.add_patch(Rectangle((117, 221), 49, 44, fc=BRASS_LT, ec=INK, lw=1.2))

    bag_callout(ax, (186, 42), (105, 58), "BAG C", "C1", "4", sub="2. Foot first")
    bag_callout(ax, (25, 269.2), (82, 282), "BAG B", "B2", "4", sub="3. Top hanger")
    bag_callout(ax, (141.5, 243), (185, 282), "BAG D", "D1", "4", sub="4. Breakers")
    ax.set_xlim(-15, 235); ax.set_ylim(-10, 310)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "battery_first", "1. Battery  2. Shelf", "Not shelf before bat")

    path = os.path.join(OUT, "page-09-batteries-shelves.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 10: DROP IN BUS SHELF (P3) — BAG C • C1 & BAG B • B2
# =====================================================================================================================
def page_10_bus_shelf():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "10", "BUS SHELF (P3) INTO CENTER BAY — BAG C & BAG B",
                "2.5 mm Hex Key (C1)   |   5/32\" Hex Key (B2)",
                [("PART", "P3", "1", "Bus Shelf Assembly", INK, BG_SOFT),
                 ("BAG C", "C1", "6", "M4 × 10 (Lip to Trays)", INK, BG_SOFT),
                 ("BAG B", "B2", "4", "1/4-20 × 1/2\" (Ends to Rails)", INK, BG_SOFT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.44, 0.60])
    render_3d_hlr(ax3d, r"^(print_bus_shelf_|power_busbar_|power_shunt_|victron_smartshunt_)",
                  [r"^(cube_|bar_|print_post_inverter_|print_tray_battery_|battery_|print_breaker_shelf_|power_breaker_shelf_)"],
                  elev=36, azim=125, title="P3 drops between trays & posts")

    ax = fig.add_axes([0.47, 0.22, 0.50, 0.60])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=CTX_FILL, ec=INK, lw=1.2))
    for nm, b_ in bb.items():
        if re.match(r"^(print_tray_battery_|print_post_inverter_)", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc=CTX_FILL, ec=CTX_EDGE, lw=0.8))
        elif re.match(r"^print_bus_shelf_", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc=ACT_FILL, ec=INK, lw=1.2))

    t0_x, t1_x = bb["print_tray_battery_0"].xmin, bb["print_tray_battery_1"].xmin
    lip_y = bb["print_bus_shelf_0"].ymin
    lip_pts = [(hx, lip_y + 4) for hx in [t0_x + 40, t0_x + 100, t0_x + 140, t1_x + 40, t1_x + 120, t1_x + 200]]
    for pt in lip_pts:
        ax.add_patch(Circle(pt, 5.2, fc="white", ec=INK, lw=1.0, zorder=4))
    end_pts = []
    for yn in (198, 238):
        end_pts.extend([(X0 + 6, Y0 + yn), (D - B - 6, Y0 + yn)])
        ax.add_patch(Circle((X0 + 6, Y0 + yn), 5.2, fc="white", ec=INK, lw=1.0, zorder=4))
        ax.add_patch(Circle((D - B - 6, Y0 + yn), 5.2, fc="white", ec=INK, lw=1.0, zorder=4))

    bag_callout(ax, [lip_pts[1], lip_pts[4]], (285, 325), "BAG C", "C1", "6", sub="Lip to trays")
    bag_callout(ax, [end_pts[2], end_pts[3]], (285, 415), "BAG B", "B2", "4", sub="Ends to rails")
    ax.set_xlim(-45, D + 45); ax.set_ylim(-25, W + 25)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "generic", "All 6× C1 + 4× B2", "Not unbolted lip")

    path = os.path.join(OUT, "page-10-bus-shelf.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 11: SLIDE IN INVERTER PLATE, LOCK CLIPS (P7) & GARMIN (P8) — BAG C & BAG B
# =====================================================================================================================
def page_11_plate_clips_garmin():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "11", "INVERTER PLATE, CLIPS (P7) & GARMIN (P8) — BAG C & B",
                "2.5 mm Hex Key (C2, C3)   |   5/32\" Hex Key (B2, B3)",
                [("BAG C", "C2", "6", "M4 × 8 (Plate Sill)", INK, BG_SOFT),
                 ("BAG C", "C3+B3", "2+2", "Post Clips (P7)", INK, BG_SOFT),
                 ("BAG B", "B2", "4", "1/4-20 × 1/2\" (Garmin)", INK, BG_SOFT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.44, 0.60])
    render_3d_hlr(ax3d, r"^(print_plate_inverter_|victron_mppt_|victron_cerbo_|victron_orion_|print_post_clip_|print_garmin_hanger|garmin_powerswitch_hanger)",
                  [r"^(cube_|bar_|print_post_inverter_|print_tray_battery_|battery_|print_breaker_shelf_|power_breaker_shelf_|print_bus_shelf_)"],
                  elev=28, azim=125, title="Plate slides into posts + Garmin on inboard rail")

    ax = fig.add_axes([0.47, 0.22, 0.50, 0.60])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=CTX_FILL, ec=INK, lw=1.2))
    for nm, b_ in bb.items():
        if re.match(r"^(print_tray_battery_|print_bus_shelf_|print_post_inverter_)", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc=CTX_FILL, ec=CTX_EDGE, lw=0.8))
        elif re.match(r"^(print_plate_inverter_|victron_mppt_|victron_cerbo_|victron_orion_|print_garmin_hanger)", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc=ACT_FILL, ec=INK, lw=1.1))

    yp = cage.V13["plate_y"]
    sill_pts = [(sx, yp - 2) for sx in (65, 179.7, 259.7, 311.8, 391.8, 506.5)]
    for pt in sill_pts:
        ax.add_patch(Circle(pt, 5.0, fc="white", ec=INK, lw=1.0, zorder=4))
    clip_pts = [(X0 + 8, Y0 + 291), (D - B - 8, Y0 + 291)]
    for pt in clip_pts:
        ax.add_patch(Circle(pt, 5.5, fc="white", ec=INK, lw=1.1, zorder=4))
    gar_pts = [(X0 + 341.5, W - B - 3), (X0 + 421.5, W - B - 3)]
    for pt in gar_pts:
        ax.add_patch(Circle(pt, 5.2, fc="white", ec=INK, lw=1.0, zorder=4))

    bag_callout(ax, [sill_pts[2], sill_pts[3]], (285, 105), "BAG C", "C2", "6", sub="Sill (Z=28)")
    bag_callout(ax, [clip_pts[0]], (165, 415), "BAG C", "C3+B3", "2", sub="P7 clips")
    bag_callout(ax, gar_pts, (405, 340), "BAG B", "B2", "4", sub="P8 Garmin")
    ax.set_xlim(-45, D + 45); ax.set_ylim(-25, W + 25)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "generic", "Seat plate in slots", "Not missed sill")

    path = os.path.join(OUT, "page-11-plate-clips-garmin.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 12: INSTALL GX TOUCH 50 DISPLAY PANEL (P9 BEZEL) & 10 FRONT PANEL PORTS
# =====================================================================================================================
def page_12_gx_touch_ports():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "12", "GX TOUCH 50 DISPLAY (P9 BEZEL) & 10 FRONT PANEL PORTS",
                "Phillips #2 Driver   |   Route HDMI + USB Cable to Cerbo GX Before Hanging MultiPlus",
                [("PART", "P9", "1", "GX Touch Bezel (150×108×3)", INK, BG_SOFT),
                 ("PART", "GX50", "1", "Victron GX Touch 50", INK, BG_SOFT),
                 ("PART", "PORTS", "10", "Front Panel Sockets", INK, BG_SOFT)])

    # Left: 3D HLR view from rear-inboard corner showing P9 Bezel + GX Touch 50 in Back Panel + Cerbo GX + Front Ports
    ax3d = fig.add_axes([0.01, 0.22, 0.44, 0.60])
    render_3d_hlr(ax3d, r"^(gx_touch|print_touch_bezel|victron_cerbo_|socket_)",
                  [r"^(cube_|bar_|panel_back_|panel_front_|print_plate_inverter_|print_garmin_hanger)"],
                  elev=26, azim=-135, title="P9 Bezel + GX Touch 50 on Back Panel  (HDMI+USB to Cerbo GX)")

    # Top-Right: Back Panel GX Touch 50 + P9 Bezel Assembly Diagram
    ax1 = fig.add_axes([0.47, 0.46, 0.50, 0.37])
    ax1.set_xlim(0, 240); ax1.set_ylim(0, 125); ax1.set_aspect("equal"); ax1.axis("off")
    ax1.text(120, 118, "1.  Back Panel (Outside View, Inboard End) — Mount P9 Bezel & GX Touch 50",
             ha="center", fontsize=9.8, weight="bold", color=INK)

    # Back panel outline section
    ax1.add_patch(Rectangle((12, 8), 118, 98, fc=CTX_FILL, ec=INK, lw=1.3))
    # Perforation slots behind bezel
    for sy in (24, 48, 72):
        ax1.add_patch(FancyBboxPatch((22, sy), 34, 8, boxstyle="round,pad=0,rounding_size=3.5", fc="white", ec=CTX_EDGE, lw=0.7))
    # P9 Trim Bezel (150 x 108 scaled)
    ax1.add_patch(FancyBboxPatch((28, 16), 84, 64, boxstyle="round,pad=0,rounding_size=2.5", fc=ACT_FILL, ec=INK, lw=1.4))
    # Cutout / GX Touch 50 screen (136 x 94)
    ax1.add_patch(FancyBboxPatch((35, 22), 70, 52, boxstyle="round,pad=0,rounding_size=2.0", fc=BLUE_FILL, ec=INK, lw=1.3))
    ax1.text(70, 48, "GX Touch 50\n(136 × 94 mm)\nSeats into P9\n128 × 86 cutout", ha="center", va="center", fontsize=7.6, weight="bold", color=INK)
    # 4 corner screw holes on P9 (140 x 98 mm centers)
    screw_pts = [(31.5, 19.5), (108.5, 19.5), (31.5, 76.5), (108.5, 76.5)]
    for sx, sy in screw_pts:
        ax1.add_patch(Circle((sx, sy), 2.2, fc="white", ec=INK, lw=1.0, zorder=4))

    bag_callout(ax1, [screw_pts[1], screw_pts[3]], (182, 82), "PART", "P9", "1",
                sub="150×108×3 Bezel + 4× #6×1/2\" screws\n(X=80 mm from inboard rail, Z=160 mm)")
    bag_callout(ax1, [(105, 48)], (182, 28), "CABLE", "HDMI+USB", "1",
                sub="Route inside 30 mm rear gap\nPlug into Cerbo GX (HDMI + USB)")

    # Bottom-Right: 10 Front Panel Ports Installation + Cable Routing Summary
    ax2 = fig.add_axes([0.47, 0.22, 0.50, 0.22])
    ax2.set_xlim(0, 240); ax2.set_ylim(0, 72); ax2.set_aspect("equal"); ax2.axis("off")
    ax2.add_patch(FancyBboxPatch((2, 2), 236, 66, boxstyle="round,pad=0,rounding_size=4.0", fc=BG_SOFT, ec=INK, lw=1.2))
    ax2.text(120, 58, "2.  Mount 10× Front Panel Ports & Connect Pigtails Before Hanging MultiPlus",
             ha="center", va="center", fontsize=9.2, weight="bold", color=INK)
    port_steps = [
        (8,   "AC Twist-Lock (×2)", "L14-30 Shore In (Z=50)\nL14-30 AC Out (Z=120)\n at X=39 mm from inboard"),
        (86,  "Anderson Flush (×3)", "2× SB50 Solar/Alt (X=92)\n1× SB175 Aux Pack (X=247)\nBolt flanges to front panel"),
        (164, "12V & USB Sockets (×5)", "3× 12V Cig Ø29 (X=39, 124)\n2× Dual USB-C Ø22 (X=92)\nTighten rear locking rings"),
    ]
    for px, ptitle, pbody in port_steps:
        ax2.add_patch(FancyBboxPatch((px, 6), 70, 42, boxstyle="round,pad=0,rounding_size=2.5", fc="white", ec=BORDER_LT, lw=0.9))
        ax2.text(px + 35, 40, ptitle, ha="center", va="center", fontsize=7.8, weight="bold", color=INK)
        ax2.text(px + 35, 20, pbody, ha="center", va="center", fontsize=6.9, color=INK_SUB, linespacing=1.2)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "csink_flush", "P9 Bezel + HDMI to Cerbo", "Not without P9 bezel")

    path = os.path.join(OUT, "page-12-gx-touch-ports.png")
    fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


# =====================================================================================================================
# PAGE 13: HANG MULTIPLUS ON D1 KEYHOLES, CONNECT 4 AWG CABLES & FIT LID
# =====================================================================================================================
def page_13_multiplus_wiring_lid():
    fig = plt.figure(figsize=(15, 9.6), dpi=DPI)
    ikea_header(fig, "13", "MULTIPLUS KEYHOLES (BAG D • D1), 4 AWG CABLES & LID",
                "3 mm Hex Key (D1 Keyholes)   |   10 mm / 13 mm Socket   |   Torque Wrench",
                [("BAG D", "D1", "4", "Snug M5 × 10 Keyholes", INK, BG_SOFT),
                 ("PART", "LID", "1", "Top Lid (571.5 × 488.1 mm)", INK, BG_SOFT)])

    ax3d = fig.add_axes([0.01, 0.22, 0.44, 0.60])
    render_3d_hlr(ax3d, r"^(victron_multiplus_)",
                  [r"^(cube_|bar_|print_post_inverter_|print_tray_battery_|battery_|print_breaker_shelf_|power_breaker_shelf_|print_bus_shelf_|print_plate_inverter_|victron_mppt_|victron_cerbo_|victron_orion_|print_garmin_hanger|gx_touch|print_touch_bezel|socket_)"],
                  elev=26, azim=128, title="Hang MultiPlus on 4× D1 + connect 4 AWG + close lid")

    ax = fig.add_axes([0.47, 0.22, 0.50, 0.60])
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=CTX_FILL, ec=INK, lw=1.2))
    for nm, b_ in bb.items():
        if re.match(r"^(print_tray_battery_|print_bus_shelf_|print_plate_inverter_|print_garmin_hanger)", nm):
            ax.add_patch(Rectangle((b_.xmin, b_.ymin), b_.xlen, b_.ylen, fc=CTX_FILL, ec=CTX_EDGE, lw=0.8))
    mp = bb["victron_multiplus_long"]
    ax.add_patch(Rectangle((mp.xmin, mp.ymin), mp.xlen, mp.ylen, fc=BLUE_FILL, ec=INK, lw=1.3))

    bag_callout(ax, ((mp.xmin + mp.xmax) / 2, mp.ymin + 10), (260, 415), "BAG D", "D1", "4", sub="Hook & tighten")

    ax.annotate("", xy=(140, 265), xytext=(120, 155), arrowprops=dict(arrowstyle="-|>", lw=2.2, color=RED_X))
    ax.annotate("", xy=(190, 265), xytext=(400, 155), arrowprops=dict(arrowstyle="-|>", lw=2.2, color=RED_X))
    ax.annotate("", xy=(265, 225), xytext=(95, 115), arrowprops=dict(arrowstyle="-|>", lw=2.2, color=INK))
    ax.annotate("", xy=(295, 225), xytext=(375, 115), arrowprops=dict(arrowstyle="-|>", lw=2.2, color=INK))
    ax.annotate("", xy=(430, 330), xytext=(485, 270), arrowprops=dict(arrowstyle="-|>", lw=2.2, color=RED_X))
    ax.annotate("", xy=(415, 315), xytext=(465, 270), arrowprops=dict(arrowstyle="-|>", lw=2.2, color=INK))

    ax.text(140, 232, "4 AWG (+)", fontsize=8.4, weight="normal", color=RED_X, ha="center",
            bbox=dict(boxstyle="round,pad=0.45,rounding_size=0.8", fc="white", ec=RED_X, lw=1.0))
    ax.text(285, 95, "4 AWG (−)", fontsize=8.4, weight="normal", color=INK, ha="center",
            bbox=dict(boxstyle="round,pad=0.45,rounding_size=0.8", fc="white", ec=INK, lw=1.0))
    ax.set_xlim(-45, D + 45); ax.set_ylim(-25, W + 25)

    ikea_ux_panel(fig, [0.26, 0.03, 0.48, 0.17], "proud_3mm", "Snug all 4× D1", "Not loose lugs")

    path = os.path.join(OUT, "page-13-multiplus-wiring-lid.png")
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
    page_12_gx_touch_ports()
    page_13_multiplus_wiring_lid()
