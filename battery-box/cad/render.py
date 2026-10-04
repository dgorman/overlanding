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
    "bar": (0.72, 0.74, 0.76, 1),
    "panel": (0.2, 0.2, 0.2, 0.22),
    "lid": (0.2, 0.2, 0.2, 0.15),
    "misc": (0.85, 0.85, 0.85, 1),
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
        key = next((k for k in COLORS if child.name.startswith(k)), "print")
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
    d = os.path.join(cage.HERE, "..", "renders"); os.makedirs(d, exist_ok=True)
    render(asm, os.path.join(d, "iso-inboard.png"), 28, -35, title="Inboard iso, lid off: battery zone (left), card over the MultiPlus (right)")
    render(asm, os.path.join(d, "iso-outboard.png"), 28, 145, title="Outboard iso, lid off")
    render(asm, os.path.join(d, "iso-card-lifted.png"), 28, -35, lift=cage.in_H * 0.9, title="Card lifted straight up out of its guides")
    render(asm, os.path.join(d, "iso-no-panels.png"), 28, -35, hide=("lid", "panel"), title="Frame + printed parts only (panels hidden)")
    render(asm, os.path.join(d, "top.png"), 90, -90, title="Top-down, lid off")
    render(asm, os.path.join(d, "end-icebox.png"), 0, 180, hide=("lid", "panel"), title="End view from the IceBox side, panels hidden")
