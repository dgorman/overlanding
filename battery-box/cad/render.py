"""Shaded PNG views of the cage assembly (no browser needed).

Tessellates every assembly part, applies the same colour scheme as the web
viewer, and rasterises with matplotlib's painter-sorted Poly3DCollection.
Good enough for README diagrams; use viewer/index.html for interactive 3D.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import cage

COLORS = {  # name prefix -> rgba
    "icebox": (0.45, 0.45, 0.47, 0.55),
    "bar": (0.72, 0.74, 0.76, 1),
    "panel": (0.2, 0.2, 0.2, 0.22),
    "lid": (0.2, 0.2, 0.2, 0.15),

    "print": (0.85, 0.33, 0.12, 1),
    "card": (0.18, 0.18, 0.18, 0.95),
    "victron": (0.15, 0.39, 0.92, 1),
    "garmin": (0.08, 0.08, 0.08, 1),
    "power": (0.79, 0.64, 0.15, 1),
    "battery": (0.12, 0.5, 0.95, 0.9),
    "socket": (0.3, 0.3, 0.3, 1),
}
LIGHT = np.array([0.4, -0.7, 0.6]); LIGHT /= np.linalg.norm(LIGHT)


def subdivide(tri, max_edge=35.0, depth=0):
    """Split big triangles so the painter's sort has small, local polygons."""
    if depth > 5:
        return tri
    e = np.linalg.norm(tri[:, [1, 2, 0]] - tri, axis=2).max(axis=1)
    big, small = tri[e > max_edge], tri[e <= max_edge]
    if len(big) == 0:
        return tri
    a, b, c = big[:, 0], big[:, 1], big[:, 2]
    ab, bc, ca = (a + b) / 2, (b + c) / 2, (c + a) / 2
    kids = np.concatenate([np.stack([a, ab, ca], 1), np.stack([ab, b, bc], 1),
                           np.stack([ca, bc, c], 1), np.stack([ab, bc, ca], 1)])
    return np.concatenate([small, subdivide(kids, max_edge, depth + 1)])


def part_tris(shape, tol=1.5):
    verts, tris = shape.tessellate(tol, 0.3)
    v = np.array([(p.x, p.y, p.z) for p in verts])
    return subdivide(v[np.array(tris)])


def collect(asm, hide=(), lift=0.0):
    polys, cols = [], []
    for child in asm.children:
        nm = child.name.replace("print_pack_panel", "panel_pack").replace("print_pack_lid", "lid_pack")   # the printed pack skin hides with the panels
        key = next((k for k in COLORS if nm.startswith(k)), "print")
        if key in hide:
            continue
        tri = part_tris(child.obj.val() if hasattr(child.obj, "val") else child.obj)
        if lift and (child.name.endswith("__card") or child.name.startswith("card_")):
            tri = tri + np.array([0, 0, lift])
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        shade = 0.55 + 0.45 * np.clip(n @ LIGHT, 0, 1)
        base = np.array(COLORS[key])
        c = np.tile(base, (len(tri), 1)); c[:, :3] *= shade[:, None]
        polys.append(tri); cols.append(c)
    return np.concatenate(polys), np.concatenate(cols)


def render(asm, path, elev=28, azim=-55, hide=("lid",), lift=0.0, title=""):
    tri, col = collect(asm, hide, lift)
    fig = plt.figure(figsize=(14, 8), dpi=110)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(tri, facecolors=col, edgecolors="none", linewidths=0))
    lo, hi = tri.reshape(-1, 3).min(0), tri.reshape(-1, 3).max(0)
    pad = 15
    ax.set_xlim(lo[0] - pad, hi[0] + pad); ax.set_ylim(lo[1] - pad, hi[1] + pad); ax.set_zlim(lo[2] - pad, hi[2] + pad)
    ax.set_box_aspect(tuple(hi - lo + 2 * pad), zoom=1.12)
    ax.view_init(elev=elev, azim=azim); ax.set_proj_type("ortho")
    ax.set_axis_off(); fig.patch.set_facecolor("white")
    if title:
        fig.text(0.02, 0.97, title, fontsize=13, va="top", family="sans-serif")
    fig.tight_layout(pad=0); fig.savefig(path, facecolor="white"); plt.close(fig)
    print("wrote", path)


if __name__ == "__main__":
    asm = cage.build()
    os.makedirs(cage.OUT, exist_ok=True)
    d = cage.RENDERS; os.makedirs(d, exist_ok=True)
    render(asm, os.path.join(d, "with-icebox.png"), 22, 35, hide=("lid",),
           title=("487 mm cube from 12 uncut kit bars" if cage.P["frame_source"] == "kit"
                  else "v9: bus deck on the battery rack, two unpluggable cards, 539 x 345 x 559" if cage.P["card_plane"] == "v9"
                  else "v8: four SuperPack 60Ah in two touching stacks, three cards across, 598 x 345 x 559" if cage.P["card_plane"] == "v8"
                  else "v7: four SuperPack 60Ah in two touching stacks, lengthwise cards in front, 345 mm wide" if cage.P["card_plane"] == "v7"
                  else "v6: side-mount cards front to back" if cage.P["card_plane"] == "xz"
                  else "A second IceBox 1.3 frame as the cage")
                 + ", standing against the IceBox 1.3 slotted back panel")
    render(asm, os.path.join(d, "iso-front.png"), 24, 35, hide=("lid", "panel", "icebox"),
           title=("Front-inboard iso, panels hidden: two cards (inverter, charge) and the bus deck on the battery rack" if cage.P["card_plane"] == "v9"
                  else "Front-inboard iso, panels hidden: three cards across (inverter, charge, distribution), battery stacks behind" if cage.P["card_plane"] == "v8"
                  else "Front-inboard iso, panels hidden: lengthwise cards in front, two touching battery stacks behind the cross-bar" if cage.P["card_plane"] == "v7"
                  else "Front-inboard iso, panels hidden: inverter card along the inboard wall, dist card beside it, batteries outboard" if cage.P["card_plane"] == "xz"
                  else "Front-inboard iso, panels hidden: dist card in front, inverter/charger card behind it, batteries at the back"))
    render(asm, os.path.join(d, "iso-back.png"), 24, 215, hide=("lid", "panel", "icebox"),
           title="Back-outboard iso, panels hidden: " + ("three batteries upright, fourth on its long side on the shelf" if cage.P["batt_layout"] == "row3_top1"
                  else "battery rack with the bus deck on top, two cards in front" if cage.P["card_plane"] == "v9"
                  else "two touching stacks of SuperPack 60Ah at the IceBox end, three cards across in front" if cage.P["card_plane"] == "v8"
                  else "two touching stacks of SuperPack 60Ah at the IceBox end, cross-bar, cards in front" if cage.P["card_plane"] == "v7"
                  else ("four Lithium Smart 200Ah in a 2 x 2 printed rack, cards along the inboard wall" if cage.BS["arrange"] == "2x2" else "two Lithium Smart 200Ah end to end in the outboard column, cards along the inboard wall") if cage.P["card_plane"] == "xz" else "two upright stacks of two batteries"))
    render(asm, os.path.join(d, "cards-lifted.png"), 24, 35, hide=("lid", "panel", "icebox"), lift=cage.in_H * 0.8, title="All three cards lifted out the top")
    render(asm, os.path.join(d, "front.png"), 0, 0, hide=("lid", "panel", "icebox"), title="Front elevation, panels hidden")
    render(asm, os.path.join(d, "top.png"), 90, -90, hide=("lid", "icebox"), title="Top-down, lid off: rear layer (left) and cards (right)")
    render(asm, os.path.join(d, "with-icebox-top.png"), 90, -90, hide=("lid",), title="Top-down with the IceBox")
