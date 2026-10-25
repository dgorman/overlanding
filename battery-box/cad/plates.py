"""Print orientation and print plates for the stl/<variant>/ files.

cage.py's export calls reorient_file() on every print_*.stl it writes, so each file on disk already lies the way it
prints (ORIENT_RULES below), at the origin, and then build_plates() groups the small parts onto plate_*.stl beds.
Run standalone to rebuild the plates from the (already oriented) files:  .venv/bin/python plates.py v12s
"""
import itertools, math, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP, BED = 12.0, 256.0


# --- binary STL in / out ------------------------------------------------------------------------------------------
def read(path):
    with open(path, "rb") as f:
        f.seek(80); n = struct.unpack("<I", f.read(4))[0]
        tris = [struct.unpack("<12f", f.read(50)[:48]) for _ in range(n)]
    return [[t[3:6], t[6:9], t[9:12]] for t in tris]


def write(path, tris):
    with open(path, "wb") as f:
        f.write(b"\0" * 80); f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            ux, uy, uz = (b[i] - a[i] for i in range(3)); vx, vy, vz = (c[i] - a[i] for i in range(3))
            n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx); L = (sum(k * k for k in n) ** 0.5) or 1.0
            f.write(struct.pack("<12fH", *(k / L for k in n), *a, *b, *c, 0))


def normalise(tris):
    """Move the part so its bounding box starts at the origin (the bed is z = 0)."""
    lo = [min(v[k] for t in tris for v in t) for k in range(3)]
    return [[(v[0] - lo[0], v[1] - lo[1], v[2] - lo[2]) for v in t] for t in tris]


# --- orientations (proper rotations only, never a mirror) ----------------------------------------------------------
ROT = {   # bring the named bounding-box face to the bottom
    (2, "min"): lambda v: v,
    (2, "max"): lambda v: (v[0], -v[1], -v[2]),
    (1, "min"): lambda v: (v[0], -v[2], v[1]),
    (1, "max"): lambda v: (v[0], v[2], -v[1]),
    (0, "min"): lambda v: (-v[2], v[1], v[0]),
    (0, "max"): lambda v: (v[2], v[1], -v[0]),
}


def face_areas(tris):
    """Flat area lying on each of the six bounding-box faces: {(axis, 'min'|'max'): mm2}."""
    lo = [min(v[k] for t in tris for v in t) for k in range(3)]; hi = [max(v[k] for t in tris for v in t) for k in range(3)]
    area = {}
    for a, b, c in tris:
        for k in range(3):
            for side, ref in (("min", lo[k]), ("max", hi[k])):
                if all(abs(v[k] - ref) < 1e-3 for v in (a, b, c)):
                    ux, uy, uz = (b[i] - a[i] for i in range(3)); vx, vy, vz = (c[i] - a[i] for i in range(3))
                    area[(k, side)] = area.get((k, side), 0.0) + 0.5 * ((uy * vz - uz * vy) ** 2 + (uz * vx - ux * vz) ** 2 + (ux * vy - uy * vx) ** 2) ** 0.5
    return area


def face_down(face):
    f = ROT[face]
    return lambda tris: [[f(v) for v in t] for t in tris]


as_modelled = face_down((2, "min"))
top_down = face_down((2, "max"))          # flipped over: the top face on the bed
on_side_y = face_down((1, "max"))         # the +Y face on the bed (an L bracket's profile lies flat)
edge_x_up = face_down((0, "min"))         # stood on its -X end: X becomes the print height (the drop shelf)


def flat(tris):
    """Lie on the largest flat face: a post's solid back, a clip's plain outer face, a tile's plain back."""
    return face_down(max(face_areas(tris).items(), key=lambda kv: kv[1])[0])(tris)


ORIENT_RULES = [   # (file-name prefix, orientation); first match wins; anything else prints as modelled
    ("print_tray_rail_bracket_0", on_side_y),   # back pair: L profile flat on the bed
    ("print_tray_rail_bracket_1", top_down),    # front pair: on their 14 x 40 top leg (on the side that leg is a fin)
    ("print_breaker_shelf", edge_x_up),         # 130 mm edge vertical: every wall upright, the plate and leg need no support
    ("print_post_inverter", flat),              # on the solid back, slot up, sill bolt hole vertical
    ("print_post_clip", flat),                  # on the plain outer face, countersink up
    ("print_plate_inverter_tile", flat),        # on the plain back: pilot holes and the half-lap rabbets face up
    ("print_plate_inverter_spline", flat),
    ("print_tool_tap_guide", top_down),         # pocket up (modelled pocket-down)
]


def orient_for(name):
    for prefix, fn in ORIENT_RULES:
        if name.startswith(prefix):
            return fn
    return as_modelled


def reorient_file(path):
    """Rewrite one exported print_*.stl lying in its print orientation at the origin."""
    name = os.path.basename(path)
    tris = normalise(orient_for(name)(read(path)))
    write(path, tris)
    return tris


# --- plates --------------------------------------------------------------------------------------------------------
def rot_z(tris, deg):
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[(v[0] * c - v[1] * s_, v[0] * s_ + v[1] * c, v[2]) for v in t] for t in tris]


PLATES = {   # plate name: list of (file, rotation about Z, (x, y) of the bounding box corner or None = next in a row)
    "plate_tray_rail_brackets": [("print_tray_rail_bracket_00.stl", 0, None), ("print_tray_rail_bracket_01.stl", 0, None),
                                 ("print_tray_rail_bracket_10.stl", 0, None), ("print_tray_rail_bracket_11.stl", 0, None)],
    "plate_tray_rail_brackets_front": [("print_tray_rail_bracket_10.stl", 0, None), ("print_tray_rail_bracket_11.stl", 0, None)],
    "plate_breaker_shelf": [("print_breaker_shelf_0.stl", 0, None)],   # one shelf (print it twice: two do not fit a bed)
    "plate_inverter_splines": [("print_plate_inverter_spline_*.stl", 0, None)],   # all the plate's splines in a row
    "plate_inverter_posts": [("print_post_inverter_0.stl", 45, (6, 32)), ("print_post_inverter_1.stl", 45, (32, 6)),   # 254 posts at
                             ("print_post_clip_0.stl", 0, (6, 210)), ("print_post_clip_1.stl", 0, (205, 6))],        # 45 deg, clips in the corners
}


def raster(tris):
    """1 mm cells under the part's footprint (triangles projected on the bed)."""
    got = set()
    for a, b, c in tris:
        xs = [a[0], b[0], c[0]]; ys = [a[1], b[1], c[1]]
        for gx in range(int(min(xs)), int(max(xs)) + 1):
            for gy in range(int(min(ys)), int(max(ys)) + 1):
                px, py = gx + 0.5, gy + 0.5
                d1 = (px - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (py - b[1])
                d2 = (px - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (py - c[1])
                d3 = (px - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (py - a[1])
                if not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0)):
                    got.add((gx, gy))
    return got


def build_plates(stl_dir, quiet=False):
    for name, items in PLATES.items():
        out, x, parts, y_row, row_h = [], 0.0, [], 0.0, 0.0
        import glob
        expanded = []
        for fn, rotz, at in items:   # a glob entry stands for every matching file
            expanded += [(os.path.basename(m), rotz, at) for m in sorted(glob.glob(os.path.join(stl_dir, fn)))] if "*" in fn else [(fn, rotz, at)]
        for fn, rotz, at in expanded:
            tris = read(os.path.join(stl_dir, fn))                       # already oriented by reorient_file
            if rotz:
                tris = normalise(rot_z(tris, rotz))
            w = max(v[0] for t in tris for v in t); d = max(v[1] for t in tris for v in t); h = max(v[2] for t in tris for v in t)
            if at is None:                       # next in a row, wrapping to a new row when the bed is full
                if x + w > BED:
                    x, y_row, row_h = 0.0, y_row + row_h + GAP, 0.0
                at = (x, y_row); x += w + GAP; row_h = max(row_h, d)
            tris = [[(v[0] + at[0], v[1] + at[1], v[2]) for v in t] for t in tris]
            parts.append((fn, tris)); out += tris
            if not quiet:
                print(f"  {fn}: {w:.0f} x {d:.0f} footprint, {h:.0f} tall, at ({at[0]:.0f}, {at[1]:.0f})")
        assert max(v[0] for t in out for v in t) <= BED and max(v[1] for t in out for v in t) <= BED, f"{name} exceeds the bed"
        foot = [(fn, raster(tr)) for fn, tr in parts]
        for (f1, r1), (f2, r2) in itertools.combinations(foot, 2):
            assert not (r1 & r2), f"{name}: {f1} overlaps {f2} on the bed"
        write(os.path.join(stl_dir, name + ".stl"), out)
        print(f"wrote {name}.stl")


if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "v12s"
    build_plates(os.path.join(HERE, "..", "stl", variant))
