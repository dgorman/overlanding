"""Step-by-step installation diagrams for the manual (MANUAL.md): builds v12s once and renders each assembly step with
the parts placed in that step in their colours and everything placed earlier in grey.  Also one image per printed part.
Run: .venv/bin/python manual.py v12s   (writes ../manual/img/)"""
import os, re, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import cage, render

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "manual", "img")
os.makedirs(OUT, exist_ok=True)
GREY = (0.72, 0.72, 0.74, 0.35)
PANEL = (0.25, 0.25, 0.27, 0.22)

STEPS = [  # (slug, title, new-part regex, context panels?)
    ("01-frame",     "Step 1: the frame, cubes and rails from the 25 in IceBox",          r"^(cube_|bar_)", False),
    ("02-panels",    "Step 2: the four panels slide into the rails' centre slots",        r"^panel_", True),
    ("03-posts",     "Step 3: the two inverter-plate posts, sill bolts into the width rails", r"^print_post_inverter_", False),
    ("04-trays",     "Step 4: the two battery trays, bolted to the outboard and width rails", r"^print_tray_battery_", False),
    ("05-batteries", "Step 5: batteries into the trays (before the shelves)",             r"^battery_", False),
    ("06-shelves",   "Step 6: breaker drop shelves over the batteries, then the breakers", r"^(print_breaker_shelf_|power_breaker_shelf_)", False),
    ("07-bus",       "Step 7: the bus shelf with the bus bars and shunt, bolted to both width rails", r"^(print_bus_shelf_|power_busbar_|power_shunt_)", False),
    ("08-plate",     "Step 8: the inverter plate with its units, the post clips, and the Garmin hanger on the inboard rail",    r"^(print_plate_inverter_|victron_mppt_|victron_cerbo_|victron_orion_|print_post_clip_|print_garmin_hanger|garmin_powerswitch_hanger)", False),
    ("09-inverter",  "Step 9: hang the MultiPlus on the plate",                           r"^victron_multiplus_", False),
    ("10-ports-lid", "Step 10: port bodies, pigtails and the lid",                        r"^(socket_|lid_|gx_touch|print_touch_bezel)", True),
]
HIDE_ALWAYS = re.compile(r"^icebox_")


def colour_for(name):
    key = next((k for k in render.COLORS if name.startswith(k)), "print")
    if name.startswith("cube_"):
        return (0.12, 0.12, 0.12, 1)
    return render.COLORS[key]


def render_set(asm, path, title, new_re, placed_res, elev, azim, panels_ctx):
    polys, cols = [], []
    for ch in asm.children:
        nm = ch.name
        if HIDE_ALWAYS.match(nm):
            continue
        is_new = re.match(new_re, nm) is not None
        placed = any(re.match(r, nm) for r in placed_res)
        if not (is_new or placed):
            continue
        if nm.startswith("lid_") and not is_new:
            continue                                   # the lid only shows in its own step
        if nm.startswith("panel_") and not is_new:
            if not panels_ctx:
                continue
            col = PANEL
        else:
            col = colour_for(nm) if is_new else GREY
        tri = render.part_tris(ch.obj.val())
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        shade = 0.55 + 0.45 * np.clip(n @ render.LIGHT, 0, 1)
        c = np.tile(np.array(col, dtype=float), (len(tri), 1)); c[:, :3] *= shade[:, None]
        polys.append(tri); cols.append(c)
    tri, col = np.concatenate(polys), np.concatenate(cols)
    fig = plt.figure(figsize=(13, 7.5), dpi=120)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(tri, facecolors=col, edgecolors="none", linewidths=0))
    lo, hi = np.array([0, 0, 0.0]), np.array([cage.out_D, cage.out_W, cage.out_H + 30.0])   # fixed box so steps line up
    pad = 15
    ax.set_xlim(lo[0] - pad, hi[0] + pad); ax.set_ylim(lo[1] - pad, hi[1] + pad); ax.set_zlim(lo[2] - pad, hi[2] + pad)
    ax.set_box_aspect(tuple(hi - lo + 2 * pad), zoom=1.15)
    ax.view_init(elev=elev, azim=azim); ax.set_proj_type("ortho"); ax.set_axis_off(); fig.patch.set_facecolor("white")
    fig.text(0.02, 0.97, title, fontsize=13, va="top", family="sans-serif", weight="bold")
    fig.text(0.02, 0.925, "orange / blue / gold = placed in this step;  grey = already in place;  front of the box (ports) is to the right",
             fontsize=9, va="top", family="sans-serif", color="#555")
    fig.tight_layout(pad=0); fig.savefig(path, facecolor="white"); plt.close(fig)
    print("wrote", path)


def render_part(asm, name, path):
    ch = next(c for c in asm.children if c.name == name)
    shp = ch.obj.val(); bb = shp.BoundingBox()
    tri = render.part_tris(shp)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    shade = 0.55 + 0.45 * np.clip(n @ render.LIGHT, 0, 1)
    c = np.tile(np.array(render.COLORS["print"], dtype=float), (len(tri), 1)); c[:, :3] *= shade[:, None]
    fig = plt.figure(figsize=(6, 4.5), dpi=120)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(tri, facecolors=c, edgecolors="none", linewidths=0))
    lo, hi = np.array([bb.xmin, bb.ymin, bb.zmin]), np.array([bb.xmax, bb.ymax, bb.zmax]); pad = 8
    ax.set_xlim(lo[0] - pad, hi[0] + pad); ax.set_ylim(lo[1] - pad, hi[1] + pad); ax.set_zlim(lo[2] - pad, hi[2] + pad)
    ax.set_box_aspect(tuple(hi - lo + 2 * pad), zoom=1.2)
    ax.view_init(elev=28, azim=-55); ax.set_proj_type("ortho"); ax.set_axis_off(); fig.patch.set_facecolor("white")
    fig.text(0.02, 0.96, f"{name}  {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f} mm", fontsize=10, va="top", family="sans-serif")
    fig.tight_layout(pad=0); fig.savefig(path, facecolor="white"); plt.close(fig)
    print("wrote", path)


if __name__ == "__main__":
    asm = cage.build()
    placed = []
    for slug, title, new_re, panels_ctx in STEPS:
        render_set(asm, os.path.join(OUT, f"{slug}.png"), title, new_re, placed, 24, -50, panels_ctx)
        if slug in ("03-posts", "04-trays", "06-shelves", "07-bus", "08-plate"):
            render_set(asm, os.path.join(OUT, f"{slug}-top.png"), title + " (from above)", new_re, placed, 90, -90, panels_ctx)
        placed.append(new_re)
    for name in ("print_tray_battery_0", "print_post_inverter_0", "print_post_clip_0",
                 "print_breaker_shelf_0", "print_bus_shelf_0", "print_bus_shelf_2", "print_garmin_hanger", "print_plate_inverter_tile_00", "print_plate_inverter_tile_21",
                 "print_plate_inverter_spline_",          # a prefix: the first spline, whatever its z in the name
                 "print_stack_strap_out_0"):
        name = next(c.name for c in asm.children if c.name.startswith(name))
        render_part(asm, name, os.path.join(OUT, f"part-{name}.png"))
