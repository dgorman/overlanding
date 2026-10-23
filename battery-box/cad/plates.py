"""Print plates: several small STLs from stl/<variant>/ laid out on one 256 mm bed, each re-oriented for printing, written
as one STL (plate_*.stl, kept by cage.py's export).  Run: .venv/bin/python plates.py v12s"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "v12s"
STL = os.path.join(HERE, "..", "stl", VARIANT)
GAP, BED = 12.0, 256.0


def read(path):
    with open(path, "rb") as f:
        f.seek(80); n = struct.unpack("<I", f.read(4))[0]
        tris = [struct.unpack("<12f", f.read(50)[:48]) for _ in range(n)]
    return [[t[3:6], t[6:9], t[9:12]] for t in tris]


def on_side(tris):
    """Lay the L bracket's profile on the bed: the part's +Y face goes DOWN (both legs reach it), Y becomes the print height."""
    ymax = max(v[1] for t in tris for v in t)
    return [[(v[0], v[2], ymax - v[1]) for v in t] for t in tris]        # rotation about X (proper, no mirror) + shift


def edge_x_up(tris):
    """Stand the part on the face that is its +X end: X becomes the print height (a cyclic axis permutation, no mirror)."""
    return [[(v[1], v[2], v[0]) for v in t] for t in tris]


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


ROT = {   # proper rotations that bring the named bounding-box face to the bottom (no mirroring)
    (2, "min"): lambda v: v,
    (2, "max"): lambda v: (v[0], -v[1], -v[2]),
    (1, "min"): lambda v: (v[0], -v[2], v[1]),
    (1, "max"): lambda v: (v[0], v[2], -v[1]),
    (0, "min"): lambda v: (-v[2], v[1], v[0]),
    (0, "max"): lambda v: (v[2], v[1], -v[0]),
}


def flat(tris):
    """Lay the part on its largest flat face (a post's solid back, a clip's plain outer face): slots and countersinks
    face up, sideways bolt holes become vertical, and the long parts print lying down with the layers along them."""
    face = max(face_areas(tris).items(), key=lambda kv: kv[1])[0]
    f = ROT[face]
    return [[f(v) for v in t] for t in tris]


def top_down(tris):
    """Flip the part over: its top face goes on the bed (a bracket whose wide top leg is its only big flat face)."""
    f = ROT[(2, "max")]
    return [[f(v) for v in t] for t in tris]


def rot_z(tris, deg):
    import math
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[(v[0] * c - v[1] * s_, v[0] * s_ + v[1] * c, v[2]) for v in t] for t in tris]


def normalise(tris):
    x0 = min(v[0] for t in tris for v in t); y0 = min(v[1] for t in tris for v in t); z0 = min(v[2] for t in tris for v in t)
    return [[(v[0] - x0, v[1] - y0, v[2] - z0) for v in t] for t in tris]


def write(path, tris):
    with open(path, "wb") as f:
        f.write(b"\0" * 80); f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            ux, uy, uz = (b[i] - a[i] for i in range(3)); vx, vy, vz = (c[i] - a[i] for i in range(3))
            n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx); L = (sum(k * k for k in n) ** 0.5) or 1.0
            f.write(struct.pack("<12fH", *(k / L for k in n), *a, *b, *c, 0))


PLATES = {
    "plate_tray_rail_brackets": (on_side, [   # back pair on their sides (L profile flat); the FRONT pair upside down: their
        "print_tray_rail_bracket_00.stl", "print_tray_rail_bracket_01.stl",       # top leg is 14 x 40 and on its side it
        ("print_tray_rail_bracket_10.stl", 0, None, top_down),                      # became a 6 x 14 fin 40 tall that printed
        ("print_tray_rail_bracket_11.stl", 0, None, top_down)]),                    # badly (2026-10-22); flat it is a 14 x 40 base
    "plate_breaker_shelf": (edge_x_up, ["print_breaker_shelf_0.stl"]),   # one shelf, 130 mm edge vertical; print it twice (two do not fit a bed)
}

PLATES["plate_inverter_posts"] = (flat, [   # the two 254 posts lie flat on their backs at 45 deg so a brim fits
    ("print_post_inverter_0.stl", 45, (6, 32)), ("print_post_inverter_1.stl", 45, (32, 6)),   # on the 256 bed; the two
    ("print_post_clip_0.stl", 0, (6, 210)), ("print_post_clip_1.stl", 0, (205, 6))])          # clips sit in the free corners


def place(tris, rotz, at):
    tris = normalise(rot_z(tris, rotz)) if rotz else tris
    return [[(v[0] + at[0], v[1] + at[1], v[2]) for v in t] for t in tris]


for name, (orient, files) in PLATES.items():
    out, x, boxes, parts = [], 0.0, [], []
    for item in files:
        fn, rotz, at, o = (item + (orient,))[:4] if isinstance(item, tuple) else (item, 0, None, orient)
        tris = normalise(o(read(os.path.join(STL, fn))))
        w = max(v[0] for t in tris for v in t); h = max(v[2] for t in tris for v in t); d = max(v[1] for t in tris for v in t)
        if at is None:
            at = (x, 0.0); x += w + GAP
        tris = place(tris, rotz, at)
        bb = (min(v[0] for t in tris for v in t), min(v[1] for t in tris for v in t), max(v[0] for t in tris for v in t), max(v[1] for t in tris for v in t))
        boxes.append((fn, bb)); out += tris; parts.append((fn, tris))
        print(f"  {fn}: {w:.0f} x {d:.0f} footprint, {h:.0f} tall, rot {rotz}, bbox x {bb[0]:.0f}..{bb[2]:.0f} y {bb[1]:.0f}..{bb[3]:.0f}")
    assert max(v[0] for t in out for v in t) <= BED and max(v[1] for t in out for v in t) <= BED, name
    cells = {}   # 1 mm raster of every part's footprint: no two parts may share a cell
    for fn, _bb in boxes:
        pass
    import itertools
    def raster(tris):
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
    foot = [(fn, raster(tr)) for fn, tr in parts]
    for (f1, r1), (f2, r2) in itertools.combinations(foot, 2):
        assert not (r1 & r2), f"{name}: {f1} overlaps {f2} on the bed"
    write(os.path.join(STL, name + ".stl"), out); print("wrote", name + ".stl")
