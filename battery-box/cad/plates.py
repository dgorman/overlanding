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
    "plate_tray_rail_brackets": (on_side, [f"print_tray_rail_bracket_{k}.stl" for k in ("00", "01", "10", "11")]),
}

for name, (orient, files) in PLATES.items():
    out, x = [], 0.0
    for fn in files:
        tris = normalise(orient(read(os.path.join(STL, fn))))
        w = max(v[0] for t in tris for v in t); h = max(v[2] for t in tris for v in t); d = max(v[1] for t in tris for v in t)
        out += [[(v[0] + x, v[1], v[2]) for v in t] for t in tris]
        print(f"  {fn}: {w:.0f} x {d:.0f} footprint, {h:.0f} tall, at x {x:.0f}")
        x += w + GAP
    assert x - GAP <= BED and max(v[1] for t in out for v in t) <= BED
    write(os.path.join(STL, name + ".stl"), out); print("wrote", name + ".stl", f"({x - GAP:.0f} mm wide)")
