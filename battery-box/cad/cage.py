"""4Runner electronics card cage, v4 "cube, four batteries" — CadQuery model.

Every rail is one UNCUT Goose Gear mod-kit bar (437 mm, the IceBox 1.3 width
rail), so the frame is a 487.4 mm cube: the IceBox's width in all three
directions, 71 mm shorter than the IceBox.  It stands against the IceBox's
slotted back panel.

Rear layer: three SuperPacks upright in a row plus a fourth lying on its
long side on a printed shelf above them (Victron allows upright or long
side).  Main cards (MultiPlus; then MPPT + Orion) drop into printed posts
bolted to the rails.  The distribution card stands in the FRONT layer,
facing the removable front panel, so every output is next to the sockets.

Run:  .venv/bin/python cage.py          (from battery-box/cad)
Out:  ../viewer/cage.json                glTF with embedded buffer for the web viewer
      ../stl/*.stl                       one STL per printable part (committed)
      ../renders/*.png                   shaded views (render.py)

Coordinate system (mm):
  X = depth.  0 at the face that touches the IceBox back panel, +X toward the
      front (service) face.  The IceBox itself lives at x < 0.
  Y = width.  0 at the outboard side (vehicle wall), +Y inboard.
  Z = up, 0 at the bottom of the frame.

Everything is driven from the P / COMPONENTS / layout tables.  Dimensions
tagged "verify" have not been measured on the real part yet.
"""
from __future__ import annotations

import base64
import json
import os
import struct
import sys
from dataclasses import dataclass

import cadquery as cq

# ----------------------------------------------------------------------------
# Variants:  python cage.py cube     (v4: 487 mm cube from 12 uncut kit bars)
#            python cage.py icebox   (v5: a second IceBox 1.3 frame, gutted)
# ----------------------------------------------------------------------------
VARIANT = next((a for a in sys.argv[1:] if not a.startswith("-")), os.environ.get("CAGE_VARIANT", "cube"))
VARIANTS = {
    "cube":   dict(frame_source="kit", frame_W=None, frame_H=None, frame_D=None,
                   batt_layout="row3_top1", dist_forward=False, inverter="multiplus"),
    "icebox": dict(frame_source="icebox", frame_W=487.4, frame_H=558.8, frame_D=762.0,
                   batt_layout="stack2x2", dist_forward=True, inverter="multiplus"),
    # v6 draft: cards run FRONT TO BACK along the inboard wall so the
    # MultiPlus-II (578 long) fits on its side; one battery column outboard.
    # v6: side-mount cards, the owner's MultiPlus 12/1200/50, four 200Ah Smarts 2 x 2 in a printed rack.
    # narrow=True sizes the frame width from the Y stack (column + cards) instead of the IceBox width.
    "bookshelf": dict(frame_source="icebox", frame_W=487.4, frame_H=558.8, frame_D=762.0,
                      batt_layout="column", dist_forward=False, inverter="multiplus_1200",
                      card_plane="xz", column=["smart200", "smart200"], arrange="2x2", col_on_plate=True,
                      narrow=True, tray_for="smart200", align="right"),
    # v6 alt: same, two 200Ah end to end (no rack)
    "bookshelf2": dict(frame_source="icebox", frame_W=487.4, frame_H=558.8, frame_D=762.0,
                       batt_layout="column", dist_forward=False, inverter="multiplus_1200",
                       card_plane="xz", column=["smart200", "smart200"], arrange="inline", col_on_plate=True,
                       narrow=True, tray_for="smart200", align="right"),
    # v6 check: the owner's four SuperPack 60Ah dropped into the same 200Ah trays
    "bookshelf60": dict(frame_source="icebox", frame_W=487.4, frame_H=558.8, frame_D=762.0,
                        batt_layout="column", dist_forward=False, inverter="multiplus_1200",
                        card_plane="xz", column=["battery", "battery"], arrange="2x2", col_on_plate=True,
                        narrow=True, tray_for="smart200", align="right"),
}
# --inverter=multiplus|multiplus_ii|multiplus_4k overrides the variant's inverter
for _a in sys.argv[1:]:
    if _a.startswith("--inverter="):
        VARIANTS[VARIANT]["inverter"] = _a.split("=", 1)[1]
assert VARIANT in VARIANTS, f"unknown variant {VARIANT}; pick one of {list(VARIANTS)}"

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", VARIANT)
STL = os.path.join(HERE, "..", "stl", VARIANT)
VIEWER = os.path.join(HERE, "..", "viewer")
RENDERS = os.path.join(HERE, "..", "renders", VARIANT)

# ----------------------------------------------------------------------------
# Parameters (mm)
# ----------------------------------------------------------------------------
P = dict(
    # IceBox 1.3, 25" deep (Goose Gear): 19-3/16 W x 22 H x 25 D.  The cage
    # copies W and H exactly.
    icebox_W=487.4, icebox_H=558.8, icebox_D=762.0,   # owner's IceBox 1.3 is the 30" deep one
    icebox_gap=12.0,     # frame-to-frame: IceBox back panel + cage back panel
    show_icebox=True,

    bar=25.4,            # Goose Gear MaxLite 1" extrusion (profile verify)
    cube=25.4,           # printed 3-way corner cube
    panel_t=6.0,         # panels: 6 mm phenolic ply / HDPE, screwed to the OUTSIDE
                         # of the bars with T-nuts (Goose Gear style); the floor
                         # panel rests on the bottom rails inside the frame
    card_t=6.0,
    card_clear=0.6,

    # Depth budget inside a 437 mm cube: rear layer = battery depth (229) +
    # tray walls; the front layer holds the MultiPlus (100) off the lower
    # card, then the distribution card dist_gap behind the MultiPlus face.
    rear_depth=240.0,
    dist_gap=6.0,
    n_batt_row=3,        # upright batteries across the width
    batt_on_top=True,    # fourth battery on its long side on a printed shelf

    # Frame sourcing: NO off-the-shelf extrusion, NO printed rail, and NO
    # cutting: all 12 rails are full kit bars (8 kits = 16 bars, 4 spare).
    # Each bar is an IceBox width rail, 19-3/16" minus two 1" cubes.  (verify)
    kit_bars=16,
    bar_stock=436.6,
    rail_seg_max=250.0,  # only used if the bar pool runs out
    splice_len=60.0,     # printed cross key joining two bar pieces

    # Card guides are printed POSTS that bolt into the T-slots of the top and
    # bottom rails (no side panels needed).  Cross-section post_w (X) x post_d
    # (Y); the card edge sits in a slot slot_depth deep on the card side.
    post_w=24.0,
    post_d=18.0,
    slot_depth=10.0,
    post_seg_max=216.0,  # 2 segments + 20 mm tenon stay under the 256 mm bed
    foot_t=6.0,
    foot_len=40.0,       # reaches from the post over the rail centreline

    shelf_t=10.0,        # printed mid-shelf between the stacked batteries
    tray_lip=20.0,
    term_clear=14.0,     # clearance above each battery for lugs (verify: is the terminal inside the 213?)

    # cards: lower carries the MultiPlus, upper the small electronics,
    # dist card (rear layer, beside the batteries) the shunt/breakers/bus/Cerbo
    lower_card_h=254.0,  # raised automatically if the inverter needs more
    socket_z=385.0,      # 12V socket centreline on the front panel: top band, above the dist card's parts
    socket_panel_h=60.0,
    socket_panel_t=5.0,
    vent_rows=3,         # vent slots in the front panel over the MultiPlus band
)
P.setdefault("card_plane", "yz")
P.setdefault("col_on_plate", False)   # True: no floor panel under the battery column; trays sit on the Goose Gear plate (z=0)
P.setdefault("narrow", False)
P.setdefault("tray_for", None)        # size the battery trays for this battery key (None = the column's own)
P.setdefault("pedal_gap", 0.0)        # extra width to keep free beside the column (0 = tight)
P.setdefault("align", "left")         # which IceBox face the (narrower) cage is flush with, as seen in the viewer's Front view
P.update(VARIANTS[VARIANT])


@dataclass
class Comp:
    name: str   # prefix drives viewer colouring: victron / garmin / power / battery / socket
    w: float    # along Y (width) as mounted
    d: float    # along X (depth) as mounted
    h: float    # along Z as mounted
    note: str = ""


COMPONENTS = {
    "battery":   Comp("battery", 138, 229, 213, "Victron Lithium SuperPack 12.8V/60Ah, 9.5 kg, M6 top terminals: 3 upright in a row"),
    "battery_side": Comp("battery_top", 229, 213, 138, "4th SuperPack on its long side on the shelf (Victron: upright or long side only)"),
    # v6 battery: Lithium Smart 12.8/100, long axis along the depth
    "smart100":  Comp("battery", 152, 321, 197, "Victron Lithium Smart 12.8V/100Ah, 14 kg, M8, 100 A rec / 200 A max, needs VE.Bus BMS V2"),
    "smart160":  Comp("battery", 152, 321, 237, "Victron Lithium Smart 12.8V/160Ah, 18 kg, 160 A rec / 320 A max"),
    "smart200":  Comp("battery", 152, 321, 237, "Victron Lithium Smart 12.8V/200Ah, 20 kg, 200 A rec / 400 A max"),
    "superpack100": Comp("battery", 169, 306, 215, "Victron SuperPack 12.8V/100Ah, 10.5 kg, 100 A cont / 150 A peak, internal BMS"),
    "bms":       Comp("power_bms", 122, 23, 106, "VE.Bus BMS V2 (from Victron STEP: 122 x 106 x 23)"),
    # inverter candidates, as mounted on their side on the lower card (w along Y, h up, d off the card)
    "multiplus":    Comp("victron_multiplus", 360, 100, 240, "MultiPlus 12/800/35-16 120V on its side (6.4 kg)"),
    "multiplus_1200": Comp("victron_multiplus", 406, 100, 250, "MultiPlus 12/1200/50-16 120V on its side (8.2 kg)"),
    "multiplus_ii": Comp("victron_multiplus", 578, 148, 277, "MultiPlus-II 12/3000/120-50 120V on its side (19 kg) - 578 long"),
    "multiplus_4k": Comp("victron_multiplus", 631, 164, 277, "MultiPlus-II 12/4k/160-50 120V on its side (22 kg) - 631 long"),
    "mppt":      Comp("victron_mppt", 186, 70, 130, "SmartSolar MPPT 100/30, upright, terminals down (1.3 kg)"),
    "orion":     Comp("victron_orion", 123, 40, 137, "Orion XS 12/12-50A, upright, terminals down (0.33 kg)"),
    "cerbo":     Comp("victron_cerbo", 154, 48, 78, "Cerbo GX"),
    "garmin":    Comp("garmin_powerswitch", 125, 32, 75, "Garmin PowerSwitch"),
    "shunt":     Comp("power_shunt", 120, 46, 54, "SmartShunt 500A"),
    "busbar_p":  Comp("power_busbar_pos", 155, 35, 32, "5-stud covered bus bar (+)"),
    "busbar_n":  Comp("power_busbar_neg", 155, 35, 32, "5-stud covered bus bar (-)"),
    "breaker_a": Comp("power_breaker_a", 48, 43, 74, "battery breaker, surface mount"),
    "breaker_b": Comp("power_breaker_b", 48, 43, 74, "battery breaker, surface mount"),
    "anderson":  Comp("socket_anderson", 48, 10, 36, "Anderson SB50 panel mount, solar in (verify hole 48 x 36)"),
}

# Distribution card (rear layer, inboard of the battery column, slides down
# its own guides).  y, z = lower-left corner relative to the card.
DIST_CARD_LAYOUT = [   # full-width card in the front layer; keep parts below z=350 (sockets above)
    dict(comp="breaker_a", y=20,  z=12),
    dict(comp="breaker_b", y=85,  z=12),
    dict(comp="shunt",     y=160, z=20),
    dict(comp="busbar_n",  y=20,  z=110),
    dict(comp="busbar_p",  y=20,  z=160),
    dict(comp="mppt",      y=225, z=90),    # upright, terminals down, next to the shunt
    dict(comp="cerbo",     y=20,  z=230),
    dict(comp="garmin",    y=200, z=235),
]
# Upper card: now only the Orion (room for a second one).
UPPER_CARD_LAYOUT = [
    dict(comp="orion",  y=20,  z=12),
]
# Lower card: MultiPlus on its side, centred.
# Front-panel 12 V / USB sockets: (y centre, hole dia)
SOCKETS = [(70, 29), (115, 29), (160, 29), (205, 29), (255, 22)]
# Anderson SB50s in the inboard side panel, rear layer: (x centre, z centre)
ANDERSONS = None   # set after in_D is known: inboard side panel, front layer, 42 mm behind the front panel

# ----------------------------------------------------------------------------
# Derived
# ----------------------------------------------------------------------------
B, C, T = P["bar"], P["cube"], P["panel_t"]
if P["frame_source"] == "kit":
    out_W = out_H = out_D = P["bar_stock"] + 2 * C     # cube: every rail is one uncut bar
else:
    out_W, out_H, out_D = P["frame_W"], P["frame_H"], P["frame_D"]   # a stock IceBox 1.3 frame
if P["narrow"] and P["card_plane"] == "xz":
    # width = bar | post+plate | inverter + standoff | gap | dist plate + parts | gap | column (tray + vents) | bar
    _tray = COMPONENTS[P["tray_for"] or P["column"][0]]
    _col_need = _tray.w + 2 * 4 + 2 * 20.0            # tray outer width + 20 mm vent each side
    _inv = COMPONENTS[P["inverter"]]
    out_W = B + 17.0 + _inv.d + 10.0 + 4.0 + (P["card_t"] + 46.0) + 4.0 + _col_need + 2.0 + P["pedal_gap"] + B
    out_W = round(out_W, 1)
in_W = out_W - 2 * B                                   # clear width between the vertical bars
in_H = out_H - 2 * B - T                               # floor panel (on the bottom rails) to the top rails
in_D = out_D - 2 * B
P["front_depth"] = in_D - P["rear_depth"] - P["card_t"]
x_in0, y_in0, floor_top = B, B, B + T                  # inner origin
card_x = x_in0 + P["rear_depth"]                       # rear face of the cards
card_W = in_W - 2 * (P["post_d"] - P["slot_depth"]) - 2 * P["card_clear"]
card_y0 = y_in0 + (in_W - card_W) / 2
lower_h = max(P["lower_card_h"], COMPONENTS[VARIANTS[VARIANT]["inverter"]].h + 14)
upper_h = in_H - lower_h - 6                           # 6 mm under the top rails
batt = COMPONENTS["battery"]
batt_top = COMPONENTS["battery_side"]
row_W = P["n_batt_row"] * (batt.w + 4) + 4             # tray row width incl. walls
INV = COMPONENTS[P["inverter"]]
dist_deep = max(COMPONENTS[pl["comp"]].d for pl in DIST_CARD_LAYOUT)
if P["dist_forward"]:   # as far forward as the socket bodies allow (12 mm behind them)
    dist_x = x_in0 + in_D - 40 - dist_deep - 12 - P["card_t"]
else:                   # tight behind the inverter
    dist_x = card_x + P["card_t"] + INV.d + P["dist_gap"]
dist_W, dist_y0 = card_W, card_y0
dist_h = in_H - 8
shelf_z = floor_top + 4 + batt.h + P["term_clear"]     # underside of the printed shelf
ANDERSONS = [(in_D - 42, 100), (in_D - 42, 150)]
if P["card_plane"] == "xz":   # Andersons move to the front panel: (y centre, z centre), handled below
    ANDERSONS = []
    SOCKETS = [(40, 29), (85, 29), (130, 29), (175, 22), (215, 22)]   # over the battery column
N_BATT = 4
post_h = in_H                                          # floor panel top to the underside of the top rails


def box(w, d, h, at=(0, 0, 0)):
    return cq.Workplane("XY").box(w, d, h, centered=False).translate(at)


STEP_DIR = os.path.join(HERE, "step")
STEP_FILES = {   # component key -> Victron STEP file (downloaded into cad/step/, see components.md)
    "multiplus_ii": "MultiPlus-II-12-3000-120V.step",
    "multiplus":    "MultiPlus-12-800-120V.step",
    "multiplus_1200": "MultiPlus-12-1200-120V.step",
    "smart200":     "Lithium-Smart-12.8V-160Ah-200Ah.step",
    "smart100":     "Lithium-Smart-12.8V-100Ah.step",
    "battery":      "Lithium-SuperPack-12.8V-60Ah.step",
    "mppt":         "SmartSolar-MPPT-100-30.step",
    "orion":        "Orion-XS-12-12-50A.step",
    "cerbo":        "Cerbo-GX.step",
    "shunt":        "SmartShunt-500A.step",
    "bms":          "VE.Bus-BMS-V2.step",
}
_STEP_CACHE = {}
# extra rotation (axis, degrees) applied after the extents match, for units
# the matcher lands upside down or backwards; checked in the renders
STEP_FLIP = {"mppt": ("x", 180)}   # 180 about the card axis: fins to the card, terminals down


def load_victron(key):
    """Import a Victron STEP once, keep only the housing-sized solids (the
    files carry every screw and PCB inside), and cache the result as BREP in
    cad/step/cache/ so later builds load in a second instead of minutes."""
    fn = STEP_FILES.get(key)
    if not fn:
        return None
    path = os.path.join(STEP_DIR, fn)
    if not os.path.exists(path):
        return None
    if key in _STEP_CACHE:
        return _STEP_CACHE[key]
    cache_dir = os.path.join(STEP_DIR, "cache"); os.makedirs(cache_dir, exist_ok=True)
    brep = os.path.join(cache_dir, key + ".brep")
    if os.path.exists(brep):
        shp = cq.Shape.importBrep(brep)
    else:
        print(f"  importing {fn} (first time, slow) ...", flush=True)
        raw = cq.importers.importStep(path).val()
        solids = raw.Solids()
        if len(solids) > 1:
            bb = raw.BoundingBox(); total = bb.xlen * bb.ylen * bb.zlen
            def bbvol(sld):
                b = sld.BoundingBox(); return b.xlen * b.ylen * b.zlen
            keep = [sld for sld in solids if bbvol(sld) >= 0.03 * total]
            if not keep:
                keep = sorted(solids, key=bbvol, reverse=True)[:3]
            shp = cq.Compound.makeCompound(keep)
            print(f"  kept {len(keep)} of {len(solids)} solids")
        else:
            shp = raw
        shp.exportBrep(brep)
    _STEP_CACHE[key] = shp
    return shp


def victron_shape(key, dx, dy, dz, at, fallback):
    """Return the real Victron STEP body oriented so its extents match
    (dx, dy, dz) with its bounding-box corner at `at`; else the fallback box.
    Orientation: try the axis permutations until the sorted extents line up;
    the terminal face is then checked by the caller's own layout."""
    try:
        body = load_victron(key)
    except Exception as e:   # noqa: BLE001
        print(f"  (step import failed for {key}: {e}; using box)")
        return fallback
    if body is None:
        return fallback
    fn = STEP_FILES[key]
    want = (dx, dy, dz)
    rots = [((0, 0, 0),), ((0, 0, 90),), ((90, 0, 0),), ((0, 90, 0),), ((90, 0, 0), (0, 0, 90)), ((0, 90, 0), (0, 0, 90))]
    best, best_err = None, 1e9
    for seq in rots:
        shp = body
        for (rx, ry, rz) in seq:
            if rx: shp = shp.rotate((0, 0, 0), (1, 0, 0), rx)
            if ry: shp = shp.rotate((0, 0, 0), (0, 1, 0), ry)
            if rz: shp = shp.rotate((0, 0, 0), (0, 0, 1), rz)
        bb = shp.BoundingBox()
        err = abs(bb.xlen - dx) + abs(bb.ylen - dy) + abs(bb.zlen - dz)
        if err < best_err:
            best, best_err, best_bb = shp, err, bb
    if best_err > 0.15 * (dx + dy + dz):
        print(f"  (step {fn} extents don't match {want}; using box)")
        return fallback
    if key in STEP_FLIP:
        ax, deg = STEP_FLIP[key]
        axis = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[ax]
        best = best.rotate((0, 0, 0), axis, deg); best_bb = best.BoundingBox()
    shp = best.translate((at[0] - best_bb.xmin, at[1] - best_bb.ymin, at[2] - best_bb.zmin))
    return cq.Workplane("XY").add(shp)


# ----------------------------------------------------------------------------
# Frame parts
# ----------------------------------------------------------------------------
def bar(length: float, axis: str):
    """1" square bar with a shallow slot hint on each face (visual only)."""
    b = cq.Workplane("YZ").rect(B, B).extrude(length)
    for ang in (0, 90, 180, 270):
        slot = (cq.Workplane("YZ").center(0, B / 2 - 1.5).rect(6.4, 3)
                .extrude(length).rotate((0, 0, 0), (1, 0, 0), ang))
        b = b.cut(slot)
    if axis == "y":
        b = b.rotate((0, 0, 0), (0, 0, 1), 90)
    elif axis == "z":
        b = b.rotate((0, 0, 0), (0, 1, 0), -90)
    return b


def printed_rail(length: float, axis: str):
    """Printed rail segment, same envelope + slots as the bar, 6.8 mm centre bore."""
    r = bar(length, "x").cut(cq.Workplane("YZ").circle(3.4).extrude(length))
    if axis == "y":
        r = r.rotate((0, 0, 0), (0, 0, 1), 90)
    elif axis == "z":
        r = r.rotate((0, 0, 0), (0, 1, 0), -90)
    return r


def splice(axis: str):
    """Printed cross key that slides into the four slots on both sides of a joint."""
    k = cq.Workplane("YZ").rect(6.2, B - 3).extrude(P["splice_len"])
    k = k.union(cq.Workplane("YZ").rect(B - 3, 6.2).extrude(P["splice_len"]))
    if axis == "y":
        k = k.rotate((0, 0, 0), (0, 0, 1), 90)
    elif axis == "z":
        k = k.rotate((0, 0, 0), (0, 1, 0), -90)
    return k


def corner_cube():
    cube = box(C, C, C).edges().fillet(2.0)
    for axis in ("x", "y", "z"):
        hole = cq.Workplane("XY").circle(3.4).extrude(C + 2).translate((0, 0, -1))
        if axis == "x":
            hole = hole.rotate((0, 0, 0), (0, 1, 0), 90)
        elif axis == "y":
            hole = hole.rotate((0, 0, 0), (1, 0, 0), -90)
        cube = cube.cut(hole.translate((C / 2, C / 2, C / 2)))
    return cube


def allocate_rails():
    """Cut-plan allocator.  Rails are filled from a pool of kit bars in
    priority order (height, width, depth).  A rail longer than one bar gets a
    full bar plus a piece cut from the bar with the most left; every joint
    gets a printed splice.  Printed segments appear only if the pool runs dry.
    Returns ({rail: [(kind, length, bar_id), ...]}, [remaining per bar])."""
    pool = [P["bar_stock"]] * P["kit_bars"]
    want = [("h", out_H - 2 * C)] * 4 + [("w", out_W - 2 * C)] * 4 + [("d", out_D - 2 * C)] * 4
    runs, counts = {}, {"h": 0, "w": 0, "d": 0}
    for kind, ln in want:
        name = f"{kind}{counts[kind]}"; counts[kind] += 1
        segs, rest = [], ln
        while rest > 0.5:
            # prefer a bar that can finish the rail in one piece, else the fullest bar
            fits = [i for i, r in enumerate(pool) if r >= rest - 0.01]
            i = min(fits, key=lambda k: pool[k]) if fits else max(range(len(pool)), key=lambda k: pool[k])
            if pool[i] < 1:
                seg = min(P["rail_seg_max"], rest); segs.append(("print", seg, None)); rest -= seg; continue
            take = min(pool[i], rest); pool[i] -= take; segs.append(("bar", take, i)); rest -= take
        runs[name] = segs
    return runs, pool


def add_rail(a, name, axis, origin, segs, color_bar, color_print):
    """Lay segments end to end from origin along axis; splices at joints."""
    x, y, z = origin
    for j, (kind, ln, _bar) in enumerate(segs):
        if kind == "bar":
            shp = bar(ln, axis); col = color_bar; tag = f"bar_{name}_{j}"
        else:
            shp = printed_rail(ln, axis); col = color_print; tag = f"print_rail_{name}_{j}"
        a.add(shp.translate((x, y, z)), name=tag, color=cq.Color(*col))
        if j > 0:
            off = {"x": (-P["splice_len"] / 2, 0, 0), "y": (0, -P["splice_len"] / 2, 0), "z": (0, 0, -P["splice_len"] / 2)}[axis]
            a.add(splice(axis).translate((x + off[0], y + off[1], z + off[2])),
                  name=f"print_splice_{name}_{j}", color=cq.Color(*color_print))
        if axis == "x": x += ln
        elif axis == "y": y += ln
        else: z += ln


# ----------------------------------------------------------------------------
# Printed interior parts
# ----------------------------------------------------------------------------
def guide_post_segments(foot_dir="y", foot_hole=None):
    """Printed guide post: a post_w x post_d bar with a card slot on its +Y
    face, in segments that fit the bed.  The bottom segment has a foot that
    sits on the floor panel and bolts through it into the bottom rail's
    T-slot; the top segment has a foot that bolts up into the top rail.
    Segments join with a 20 mm printed tenon.  Yields (z, shape)."""
    gw = P["card_t"] + 2 * P["card_clear"]
    total = post_h
    n = int(-(-total // P["post_seg_max"]))
    seg_h = total / n
    out, z = [], 0.0
    for i in range(n):
        h = seg_h
        g = box(P["post_w"], P["post_d"], h)
        g = g.cut(box(gw, P["slot_depth"] + 1, h + 1, ((P["post_w"] - gw) / 2, P["post_d"] - P["slot_depth"], -0.5)))
        def foot_at(z0):
            if foot_dir == "y":   # plate toward -Y over the depth rail, hole on the rail centreline
                f = box(P["post_w"], P["foot_len"], P["foot_t"], (0, -P["foot_len"] + P["post_d"] - P["slot_depth"], z0))
                hx, hy = P["post_w"] / 2, (foot_hole if foot_hole is not None else -(B / 2 + T) + 2)
            else:                 # plate toward -X over the back width rail
                f = box(P["foot_len"], P["post_d"], P["foot_t"], (-P["foot_len"] + P["post_w"] - 4, 0, z0))
                hx, hy = (foot_hole if foot_hole is not None else -(B / 2 + T) + 2), P["post_d"] / 2
            return f.cut(cq.Workplane("XY").center(hx, hy).circle(3.4).extrude(z0 + P["foot_t"] + 1))
        if i == 0:
            g = g.union(foot_at(0))
        if i == n - 1:
            g = g.union(foot_at(h - P["foot_t"]))
            flare = (cq.Workplane("XZ").polyline([((P["post_w"] - gw) / 2, h - 8), ((P["post_w"] + gw) / 2, h - 8),
                                                   ((P["post_w"] + gw) / 2 + 2.5, h + 1), ((P["post_w"] - gw) / 2 - 2.5, h + 1)])
                     .close().extrude(-(P["slot_depth"] + 1)).translate((0, P["post_d"] + 1, 0)))
            g = g.cut(flare)
        else:        # tenon on top to locate the next segment
            g = g.union(box(P["post_w"] - 8, P["post_d"] - P["slot_depth"] - 4, 20, (4, 2, h)))
        out.append((z, g)); z += h
    return out


def battery_tray():
    """One bay per upright battery (three butt side by side across the
    width so each fits the bed): 20 mm lips, a strap slot across X, 4 mm walls."""
    lip, wall = P["tray_lip"], 4.0
    t = box(batt.d + 2 * wall, batt.w + 2 * wall, lip + 4)
    t = t.cut(box(batt.d, batt.w, lip + 5, (wall, wall, 4)))
    t = t.cut(box(batt.d + 2 * wall + 2, 30, 6, (-1, batt.w / 2 + wall - 15, 6)))
    return t


def top_shelf_half(side: int):
    """Printed shelf over the three upright batteries carrying the fourth on
    its long side; two halves (bed size) that meet at the row centre.  Flat
    bearing surface the full size of the battery face, 12 mm lip, 10 mm thick."""
    wall = 4.0
    W = row_W / 2
    h = box(batt.d + 2 * wall, W, P["shelf_t"] + 12)
    px = (batt.d + 2 * wall - batt_top.d) / 2
    py = (row_W - batt_top.w) / 2 - side * W
    h = h.cut(box(batt_top.d, batt_top.w, 13, (px, py, P["shelf_t"])))
    tx = -22 + 4
    ty = -4 if side == 0 else W - 16
    tab = box(22, 20, P["shelf_t"], (tx, ty, 0)).cut(cq.Workplane("XY").center(tx + 9, ty + 10).circle(3.4).extrude(P["shelf_t"] + 1))
    return h.union(tab)


def stack_shelf():
    """Printed mid-shelf for an upright 2-high stack: sits on the lower
    battery's rim, 12 mm lip locates the upper one, a tab bolts back into the
    back width rail's inner-face slot so the stack can't walk."""
    wall = 4.0
    sh = box(batt.d + 2 * wall, batt.w + 2 * wall, P["shelf_t"] + 12)
    sh = sh.cut(box(batt.d, batt.w, 13, (wall, wall, P["shelf_t"])))
    sh = sh.cut(box(batt.d - 30, batt.w - 30, P["shelf_t"] + 1, (wall + 15, wall + 15, -0.5)))
    tab = box(22, 24, P["shelf_t"], (-18, (batt.w + 2 * wall - 24) / 2, 0))
    tab = tab.cut(cq.Workplane("XY").center(-9, (batt.w + 2 * wall) / 2).circle(3.4).extrude(P["shelf_t"] + 1))
    return sh.union(tab)


def multiplus_feet():
    """Two printed feet on the lower card that take the MultiPlus weight."""
    return box(40, 50, 10).edges("|Z").fillet(3)


def socket_insert():
    ys = [y for y, _ in SOCKETS]
    w = max(ys) - min(ys) + 60
    sp = box(P["socket_panel_t"], w, P["socket_panel_h"],
             (out_D, y_in0 + min(ys) - 30, floor_top + P["socket_z"] - P["socket_panel_h"] / 2))
    for y, dia in SOCKETS:
        sp = sp.cut(cq.Workplane("YZ").center(y_in0 + y, floor_top + P["socket_z"]).circle(dia / 2)
                    .extrude(out_D + 1))
    return sp


def lid_handle():
    return box(12, 60, 18).edges("|X").fillet(5)


def icebox_parts():
    """Reference IceBox 1.3 at x<0, same Y/Z envelope as the cage."""
    W, H, D = P["icebox_W"], P["icebox_H"], P["icebox_D"]
    x0 = -D - P["icebox_gap"]
    yoff = (out_W - W) if P["align"] == "right" else 0.0     # right-justified: cage +Y face flush with the IceBox +Y face
    parts = []
    cube = corner_cube()
    for i, x in enumerate((x0, x0 + D - C)):
        for j, y in enumerate((0, W - C)):
            for k, z in enumerate((0, H - C)):
                parts.append((f"icebox_cube_{i}{j}{k}", cube.translate((x, y, z))))
    for y in (0, W - B):
        for z in (0, H - B):
            parts.append((f"icebox_bar_x_{int(y)}_{int(z)}", bar(D - 2 * C, "x").translate((x0 + C, y + B / 2, z + B / 2))))
    for x in (x0, x0 + D - B):
        for z in (0, H - B):
            parts.append((f"icebox_bar_y_{int(x)}_{int(z)}", bar(W - 2 * C, "y").translate((x + B / 2, C, z + B / 2))))
        for y in (0, W - B):
            parts.append((f"icebox_bar_z_{int(x)}_{int(y)}", bar(H - 2 * C, "z").translate((x + B / 2, y + B / 2, C))))
    parts.append(("icebox_panel_top", box(D, W, T, (x0, 0, H))))
    parts.append(("icebox_panel_floor", box(D - 2 * B, W - 2 * B, T, (x0 + B, B, B))))
    parts.append(("icebox_panel_side_out", box(D, T, H, (x0, -T, 0))))
    parts.append(("icebox_panel_side_in", box(D, T, H, (x0, W, 0))))
    back = box(T, W, H, (x0 + D, 0, 0))
    slot_w, slot_h, pitch_y, pitch_z = 72.0, 22.0, 92.0, 46.0
    rows = int((H - 2 * B - 120) / pitch_z)
    for r in range(rows):
        z = B + 60 + r * pitch_z
        y = B + 40 + ((pitch_y / 2) if r % 2 else 0)
        while y + slot_w < W - B - 30:
            cutter = (cq.Workplane("YZ").center(y + slot_w / 2, z + slot_h / 2)
                      .slot2D(slot_w, slot_h).extrude(T + 2).translate((x0 + D - 1, 0, 0)))
            back = back.cut(cutter); y += pitch_y
    parts.append(("icebox_panel_back_slotted", back))
    tray = box(D - 2 * B + 60, 381, 40, (x0 + B - 60, (W - 381) / 2, B + T))
    tray = tray.cut(box(D - 2 * B + 52, 373, 40, (x0 + B - 56, (W - 381) / 2 + 4, B + T + 4)))
    parts.append(("icebox_tray", tray))
    if yoff:
        parts = [(n, shp.translate((0, yoff, 0))) for n, shp in parts]
    return parts


# ----------------------------------------------------------------------------
# Assembly
# ----------------------------------------------------------------------------
GRAY, ORANGE, BLACK, PANEL = (0.72, 0.74, 0.76), (0.85, 0.33, 0.12), (0.12, 0.12, 0.12), (0.2, 0.2, 0.2)
BLUE, GOLD, BATT, DARK = (0.15, 0.39, 0.92), (0.79, 0.64, 0.15), (0.12, 0.5, 0.95), (0.18, 0.18, 0.18)


def add(a, shape, name, rgb):
    a.add(shape, name=name, color=cq.Color(*rgb))


def build() -> cq.Assembly:
    a = cq.Assembly(name="cage")

    # --- frame ---------------------------------------------------------------
    cube = corner_cube()
    for i, x in enumerate((0, out_D - C)):
        for j, y in enumerate((0, out_W - C)):
            for k, z in enumerate((0, out_H - C)):
                add(a, cube.translate((x, y, z)), f"print_cube_{i}{j}{k}", BLACK)
    if P["frame_source"] == "icebox":
        runs = {f"h{i}": [("bar", out_H - 2 * C, None)] for i in range(4)}
        runs.update({f"w{i}": [("bar", out_W - 2 * C, None)] for i in range(4)})
        runs.update({f"d{i}": [("bar", out_D - 2 * C, None)] for i in range(4)})
    else:
        runs, _ = allocate_rails()
    hi = iter(range(4)); wi = iter(range(4)); di = iter(range(4))
    for x in (0, out_D - B):
        for y in (0, out_W - B):
            n = f"h{next(hi)}"; add_rail(a, n, "z", (x + B / 2, y + B / 2, C), runs[n], GRAY, ORANGE)
        for z in (0, out_H - B):
            n = f"w{next(wi)}"; add_rail(a, n, "y", (x + B / 2, C, z + B / 2), runs[n], GRAY, ORANGE)
    for y in (0, out_W - B):
        for z in (0, out_H - B):
            n = f"d{next(di)}"; add_rail(a, n, "x", (C, y + B / 2, z + B / 2), runs[n], GRAY, ORANGE)

    # --- panels: floor on the bottom rails; everything else on the outside ----
    floor = box(out_D, out_W, T, (0, 0, B))
    if P["col_on_plate"]:   # open floor under the battery column; trays sit on the Goose Gear plate
        floor = floor.cut(box(in_D, 200, T + 2, (x_in0, y_in0, B - 1)))
    add(a, floor, "panel_floor", PANEL)
    add(a, box(out_D, out_W, T, (0, 0, out_H)), "lid_panel", PANEL)
    for y in (out_W * 0.3, out_W * 0.7):
        add(a, lid_handle().translate((out_D / 2 - 6, y - 30, out_H + T)), f"lid_handle_{int(y)}", BLACK)
    add(a, box(out_D, T, out_H, (0, -T, 0)), "panel_side_outboard", PANEL)
    inboard = box(out_D, T, out_H, (0, out_W, 0))
    ca = COMPONENTS["anderson"]
    for (x, z) in ANDERSONS:
        inboard = inboard.cut(box(ca.w, T + 2, ca.h, (x_in0 + x - ca.w / 2, out_W - 1, floor_top + z - ca.h / 2)))
        add(a, box(ca.w, 40, ca.h, (x_in0 + x - ca.w / 2, out_W - 40, floor_top + z - ca.h / 2)),
            f"socket_anderson_{int(z)}", (0.3, 0.3, 0.3))
    add(a, inboard, "panel_side_inboard", PANEL)
    back = box(T, out_W, out_H, (-T, 0, 0))
    back = back.cut(box(T + 2, 120, 30, (-T - 1, y_in0 + in_W / 2 - 60, floor_top + 40)))   # fridge cable to the IceBox slots
    add(a, back, "panel_back_icebox_side", PANEL)
    front = box(T, out_W, out_H, (out_D, 0, 0))
    for r in range(P["vent_rows"]):
        z = floor_top + 40 + r * 60
        for y in range(40, int(in_W) - 100, 70):
            front = front.cut(cq.Workplane("YZ").center(y_in0 + y + 30, z).slot2D(60, 10).extrude(out_D + T + 1))
    si = socket_insert()
    bb = si.val().BoundingBox()
    front = front.cut(box(T + 2, bb.ylen, bb.zlen, (out_D - 1, bb.ymin, bb.zmin)))
    add(a, front, "panel_front_removable", PANEL)
    add(a, si, "print_socket_insert", ORANGE)
    for y, dia in SOCKETS:
        sck = (cq.Workplane("YZ").center(y_in0 + y, floor_top + P["socket_z"]).circle(dia / 2 + 3)
               .extrude(-40).translate((out_D, 0, 0)))
        add(a, sck, f"socket_{y}", (0.3, 0.3, 0.3))

    # --- floor joists: two spare bars under the battery zone ------------------
    joist_len = out_D - 2 * C
    joist_ys = (row_W * 0.3, row_W * 0.7) if P["card_plane"] == "yz" else (30.0, 130.0)
    if not P["col_on_plate"]:
        for j, y in enumerate(joist_ys):
            add(a, bar(joist_len, "x").translate((C, y_in0 + y, B / 2)), f"bar_joist_{j}", GRAY)

    if P["card_plane"] == "xz":
        build_bookshelf(a)
        if P["show_icebox"]:
            for nm, shp in icebox_parts():
                col = BLACK if "cube" in nm else GRAY if "bar" in nm else (0.35, 0.35, 0.35)
                add(a, shp, nm, col)
        return a

    if P["batt_layout"] == "row3_top1":
        # --- three batteries upright in a row, fourth on its long side on top ---
        for i in range(P["n_batt_row"]):
            ty = y_in0 + i * (batt.w + 4)
            add(a, battery_tray().translate((x_in0, ty, floor_top)), f"print_tray_battery_{i}", ORANGE)
            add(a, box(batt.d, batt.w, batt.h, (x_in0 + 4, ty + 4, floor_top + 4)).edges("|Z").fillet(6), f"battery_{i}", BATT)
        for side in (0, 1):
            add(a, top_shelf_half(side).translate((x_in0, y_in0 + side * row_W / 2, shelf_z)), f"print_shelf_top_{side}", ORANGE)
        bx = x_in0 + (batt.d + 8 - batt_top.d) / 2
        by = y_in0 + (row_W - batt_top.w) / 2
        add(a, box(batt_top.d, batt_top.w, batt_top.h, (bx, by, shelf_z + P["shelf_t"])).edges("|X").fillet(6), "battery_top", BATT)
    else:
        # --- two upright stacks of two, one against each side wall, channel between
        for i in range(2):
            ty = y_in0 if i == 0 else out_W - B - (batt.w + 8)
            add(a, battery_tray().translate((x_in0, ty, floor_top)), f"print_tray_battery_{i}", ORANGE)
            add(a, box(batt.d, batt.w, batt.h, (x_in0 + 4, ty + 4, floor_top + 4)).edges("|Z").fillet(6), f"battery_{i}_lower", BATT)
            add(a, stack_shelf().translate((x_in0, ty, shelf_z)), f"print_shelf_stack_{i}", ORANGE)
            add(a, box(batt.d, batt.w, batt.h, (x_in0 + 4, ty + 4, shelf_z + P["shelf_t"])).edges("|Z").fillet(6), f"battery_{i}_upper", BATT)

    # --- distribution card: FRONT layer, parts facing the front panel ---------
    add(a, box(P["card_t"], dist_W, dist_h, (dist_x, dist_y0, floor_top + 2)), "card_dist_plate", DARK)
    for pl in DIST_CARD_LAYOUT:
        c = COMPONENTS[pl["comp"]]
        col = BLUE if c.name.startswith("victron") else (0.08, 0.08, 0.08) if c.name.startswith("garmin") else GOLD
        add(a, box(c.d, c.w, c.h, (dist_x + P["card_t"], dist_y0 + pl["y"], floor_top + 2 + pl["z"])).edges("|X").fillet(3),
            c.name + "__card", col)
    gx = dist_x - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"]
    for j, y in enumerate((y_in0, out_W - B - P["post_d"])):
        for k, (z, g) in enumerate(guide_post_segments()):
            if j == 1:
                g = g.mirror("XZ").translate((0, P["post_d"], 0))
            add(a, g.translate((gx, y, floor_top + z)), f"print_post_dist_{j}_{k}", ORANGE)

    # --- guide posts for the main cards: bolt to the top/bottom depth rails ---
    px = card_x - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"]
    for j, y in enumerate((y_in0, out_W - B - P["post_d"])):
        for k, (z, g) in enumerate(guide_post_segments()):
            if j == 1:
                g = g.mirror("XZ").translate((0, P["post_d"], 0))
            add(a, g.translate((px, y, floor_top + z)), f"print_post_main_{j}_{k}", ORANGE)

    # --- lower card: MultiPlus on its side -----------------------------------
    lower = box(P["card_t"], card_W, lower_h, (card_x, card_y0, floor_top + 2))
    for y in (card_y0 + 12, card_y0 + card_W - 72):   # 60 x 60 notches: 6 AWG battery runs pass under
        lower = lower.cut(box(P["card_t"] + 2, 60, 60, (card_x - 1, y, floor_top + 2 - 1)))
    add(a, lower, "card_lower_plate", DARK)
    mp = INV
    mpy = card_y0 + (card_W - mp.w) / 2; mpz = floor_top + 2 + 10
    for y in (mpy + 30, mpy + mp.w - 80):
        add(a, multiplus_feet().translate((card_x + P["card_t"], y, floor_top + 2)), f"print_feet_mp_{int(y)}__card", ORANGE)
    add(a, box(mp.d, mp.w, mp.h, (card_x + P["card_t"], mpy, mpz)).edges("|X").fillet(4), mp.name + "__card", BLUE)

    # --- upper card: small electronics ---------------------------------------
    uz = floor_top + 2 + lower_h + 1
    add(a, box(P["card_t"], card_W, upper_h, (card_x, card_y0, uz)), "card_upper_plate", DARK)
    for pl in UPPER_CARD_LAYOUT:
        c = COMPONENTS[pl["comp"]]
        col = BLUE if c.name.startswith("victron") else (0.08, 0.08, 0.08)
        add(a, box(c.d, c.w, c.h, (card_x + P["card_t"], card_y0 + pl["y"], uz + pl["z"])).edges("|X").fillet(3),
            c.name + "__card", col)

    # --- IceBox reference ----------------------------------------------------
    if P["show_icebox"]:
        for nm, shp in icebox_parts():
            col = BLACK if "cube" in nm else GRAY if "bar" in nm else (0.35, 0.35, 0.35)
            add(a, shp, nm, col)
    return a


# ----------------------------------------------------------------------------
# v6 "bookshelf": cards in the XZ plane, sliding down between posts on the
# back and front width rails.  Stacking along Y from the inboard wall:
#   inboard panel | post | inverter card | 12 mm standoff | MultiPlus-II (148)
#   | 8 | dist card posts/plate | parts (<=48) | 8 | battery column | outboard
# ----------------------------------------------------------------------------
BS = dict(standoff=10.0, gap=4.0, part_depth=46.0,   # deepest dist-card part is now the shunt (Cerbo moved up)
          column=P.get("column", ["smart200", "smart200"]),   # --column=a,b overrides
          arrange=P.get("arrange", "inline"),  # inline = end to end | stack = one on top | 2x2 = both
          vent=20.0,                           # Victron: 20 mm free on all four sides of a Lithium Smart
          vent_end=20.0,                       # end gaps; the 2x2 has to drop these to 15 to fit
          leg=24.0, leg2=14.0)
for _a in sys.argv[1:]:
    if _a.startswith("--column="):
        BS["column"] = _a.split("=", 1)[1].split(",")
    if _a.startswith("--arrange="):
        BS["arrange"] = _a.split("=", 1)[1]
# ceiling over the battery column: the lid panel, not the top rails (the
# column sits inboard of the perimeter rails).  With col_on_plate the column
# starts at the plate (z=0) instead of on the floor panel.
col_z0 = 0.0 if P["col_on_plate"] else floor_top
in_H_lid = out_H - col_z0
BS_DIST_LAYOUT = [   # x, z relative to the dist card's lower-back corner; parts face the batteries (-Y)
    dict(comp="breaker_a", x=20,  z=20),
    dict(comp="breaker_b", x=85,  z=20),
    dict(comp="shunt",     x=160, z=25),
    dict(comp="bms",       x=300, z=20),
    dict(comp="busbar_n",  x=20,  z=120),
    dict(comp="busbar_p",  x=20,  z=170),
    dict(comp="garmin",    x=380, z=120),
]
BS_INV_UPPER = [     # on the inverter card, above the MultiPlus-II (parts face -Y)
    dict(comp="mppt",  x=60,  dz=15),
    dict(comp="orion", x=300, dz=15),
    dict(comp="cerbo", x=480, dz=15),
]


def bs_geometry():
    """Y positions of the bookshelf stack; returns a dict of absolute values."""
    inv = COMPONENTS[P["inverter"]]
    wall_in = out_W - B                               # inner face of the inboard rails
    inv_plate_hi = wall_in - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"] - 1
    inv_plate_lo = inv_plate_hi - P["card_t"]
    inv_lo = inv_plate_lo - BS["standoff"] - inv.d     # MultiPlus-II -Y face
    dist_plate_hi = inv_lo - BS["gap"] - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"]
    dist_plate_lo = dist_plate_hi - P["card_t"]
    parts_lo = dist_plate_lo - BS["part_depth"]
    bay_hi = parts_lo - BS["gap"]
    return dict(inv_plate=inv_plate_lo, inv_lo=inv_lo, dist_plate=dist_plate_lo, parts_lo=parts_lo,
                bay_lo=y_in0, bay_hi=bay_hi, bay_W=bay_hi - y_in0,
                card_L=in_D - 2 * (P["post_d"] - P["slot_depth"]) - 2 * P["card_clear"],
                card_x0=x_in0 + (P["post_d"] - P["slot_depth"]) + P["card_clear"])


def post_xz(end: str):
    """Guide post for an XZ-plane card: slot faces +X (back post) or -X
    (front post); the foot reaches over the back / front width rail."""
    segs = []
    for z, g in guide_post_segments(foot_hole=-(B / 2 + 0.0) + 0.0):
        g = g.rotate((0, 0, 0), (0, 0, 1), -90)            # slot now faces +X, foot toward -X
        g = g.translate((0, P["post_w"], 0))                  # keep the body in +Y of its origin
        if end == "front":
            g = g.mirror("YZ").translate((P["post_d"], 0, 0))
        segs.append((z, g))
    return segs


def battery_leg(h: float):
    """Printed front leg under the mid-shelf, standing on the floor panel,
    bolted through it into a joist bar."""
    leg = box(24, 24, h)
    foot = box(44, 24, 6, (-10, 0, 0)).cut(cq.Workplane("XY").center(0, 12).circle(3.4).extrude(7))
    return leg.union(foot)


def build_bookshelf(a):
    g = bs_geometry()
    inv = COMPONENTS[P["inverter"]]
    bat = COMPONENTS["smart100"]

    # --- inverter/charger card: plate, posts, MultiPlus-II on standoffs, MPPT + Orion above
    plate_h = in_H - 8
    add(a, box(g["card_L"], P["card_t"], plate_h, (g["card_x0"], g["inv_plate"], floor_top + 2)), "card_inverter_plate", DARK)
    for name, y in (("inverter", g["inv_plate"]), ("dist", g["dist_plate"])):
        py = y - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"]
        for end, x in (("back", x_in0), ("front", out_D - B - P["post_d"])):
            for k, (z, gp) in enumerate(post_xz(end)):
                add(a, gp.translate((x, py, floor_top + z)), f"print_post_{name}_{end}_{k}", ORANGE)
    ix = x_in0 + (in_D - inv.w) / 2
    iz = floor_top + 2 + 10
    for x in (ix + 40, ix + inv.w - 100):
        add(a, box(60, BS["standoff"], 10, (x, g["inv_lo"], floor_top + 2)), f"print_feet_mp_{int(x)}__card", ORANGE)
    add(a, victron_shape(P["inverter"], inv.w, inv.d, inv.h, (ix, g["inv_lo"], iz),
                         box(inv.w, inv.d, inv.h, (ix, g["inv_lo"], iz)).edges("|Y").fillet(4)), inv.name + "__card", BLUE)
    z_above = iz + inv.h
    for pl in BS_INV_UPPER:
        c = COMPONENTS[pl["comp"]]
        at = (x_in0 + pl["x"], g["inv_plate"] - c.d, z_above + pl["dz"])
        add(a, victron_shape(pl["comp"], c.w, c.d, c.h, at, box(c.w, c.d, c.h, at).edges("|Y").fillet(3)), c.name + "__card", BLUE)

    # --- distribution card: plate + parts facing the battery column (-Y)
    add(a, box(g["card_L"], P["card_t"], plate_h, (g["card_x0"], g["dist_plate"], floor_top + 2)), "card_dist_plate", DARK)
    for pl in BS_DIST_LAYOUT:
        c = COMPONENTS[pl["comp"]]
        col = BLUE if c.name.startswith("victron") else (0.08, 0.08, 0.08) if c.name.startswith("garmin") else GOLD
        at = (g["card_x0"] + pl["x"], g["dist_plate"] - c.d, floor_top + 2 + pl["z"])
        add(a, victron_shape(pl["comp"], c.w, c.d, c.h, at, box(c.w, c.d, c.h, at).edges("|Y").fillet(3)), c.name + "__card", col)

    # --- battery column, outboard, from the IceBox end.
    #   inline: one printed tray per battery, end to end, 20 mm vent gaps.
    #   stack : one stack; printed rack = tray + mid-shelf + 4 legs (24 mm) at
    #           the stack's front/back faces, bolted through the floor into the joists.
    #   2x2   : two stacks end to end; legs are 16 mm so three rows of them fit.
    two = BS["arrange"] == "2x2"
    if two:
        BS["vent_end"] = 15.0
    wall, vent, vent_end = (3.0 if two else 4.0), BS["vent"], BS["vent_end"]
    col = [COMPONENTS[k] for k in BS["column"]]
    tray_c = COMPONENTS[P["tray_for"]] if P["tray_for"] else max(col, key=lambda c: c.w * c.d)
    fw = max(tray_c.w, max(c.w for c in col)) + 2 * wall
    ty = y_in0 + vent - wall                       # 20 mm vent to the outboard panel
    positions = 2 if two else 1
    L = BS["leg2"] if two else BS["leg"]
    x = x_in0 + vent_end - wall
    zmax = col_z0 + 4
    for pos in range(positions if BS["arrange"] != "inline" else len(col)):
        td = max(tray_c.d, max(c.d for c in col))          # tray pocket length
        if BS["arrange"] == "inline":
            c = col[pos]
            tray = box(td + 2 * wall, fw, 24).cut(box(td, fw - 2 * wall, 25, (wall, wall, 4)))
            add(a, tray.translate((x, ty, col_z0)), f"print_tray_battery_{pos}", ORANGE)
            at = (x + wall + (td - c.d) / 2, ty + wall + (fw - 2 * wall - c.w) / 2, col_z0 + 4)
            add(a, victron_shape(BS["column"][pos], c.d, c.w, c.h, at, box(c.d, c.w, c.h, at).edges("|Z").fillet(6)), f"battery_{pos}", BATT)
            zmax = max(zmax, col_z0 + 4 + c.h)
            x += td + 2 * wall + vent - 2 * wall
            continue
        fd = td + 2 * wall
        tx = x if (two and pos == 0) else x + L      # 2x2: back legs sit inside the end vent gap
        tray = box(fd, fw, 24).cut(box(fd - 2 * wall, fw - 2 * wall, 25, (wall, wall, 4)))
        add(a, tray.translate((tx, ty, col_z0)), f"print_tray_battery_{pos}", ORANGE)
        z = col_z0 + 4
        for i, c in enumerate(col):
            at = (tx + (fd - c.d) / 2, ty + (fw - c.w) / 2, z)
            add(a, victron_shape(BS["column"][i], c.d, c.w, c.h, at, box(c.d, c.w, c.h, at).edges("|Z").fillet(6)), f"battery_{pos}_{i}", BATT)
            z += c.h
            if i < len(col) - 1:
                z += P["term_clear"]
                nxt = col[i + 1]
                sh = box(fd + 2 * L, fw, P["shelf_t"] + 12)
                sh = sh.cut(box(nxt.d, nxt.w, 13, (L + (fd - nxt.d) / 2, (fw - nxt.w) / 2, P["shelf_t"])))
                sh = sh.cut(box(fd - 2 * wall - 30, fw - 2 * wall - 30, P["shelf_t"] + 1, (L + wall + 15, wall + 15, -0.5)))
                add(a, sh.translate((tx - L, ty, z)), f"print_shelf_{pos}_{i}", ORANGE)
                legs = [(tx - L, ty), (tx - L, ty + fw - L)]
                if pos == positions - 1:          # front legs only on the last position (shared row between stacks)
                    legs += [(tx + fd, ty), (tx + fd, ty + fw - L)]
                if two and pos == 0:
                    legs = [(tx - L, ty), (tx - L, ty + fw - L)]
                for (lx, ly) in legs:
                    leg = box(L, L, z - col_z0)
                    foot = box(L, L + 16, 6, (0, -8, 0)).cut(cq.Workplane("XY").center(L / 2, L / 2).circle(3.4).extrude(7))
                    add(a, leg.union(foot).translate((lx, ly, col_z0)), f"print_leg_{pos}_{i}_{int(lx)}_{int(ly)}", ORANGE)
                z += P["shelf_t"]
        zmax = max(zmax, z)
        x = tx + fd
    g["col_depth_used"] = x + L - x_in0 + vent_end
    z = zmax
    g["stack_top"] = z - col_z0 + P["term_clear"]
    BS["_g"] = g
    g["col_W_used"] = fw
    return g


# ----------------------------------------------------------------------------
# Export + report
# ----------------------------------------------------------------------------
def glb_to_json(glb_path: str, json_path: str):
    """Rewrite a GLB as JSON glTF with the binary chunk embedded as base64,
    after repacking every mesh into ONE primitive (positions + uint16/32
    indices, no normals).  CadQuery writes one primitive per face, and the
    accessor metadata for tens of thousands of faces dwarfs the geometry.
    The viewer recomputes normals on load."""
    import numpy as np
    d = open(glb_path, "rb").read()
    assert d[:4] == b"glTF"
    off, js, binary = 12, None, None
    while off < len(d):
        ln, typ = struct.unpack("<II", d[off:off + 8]); chunk = d[off + 8:off + 8 + ln]; off += 8 + ln
        if typ == 0x4E4F534A: js = json.loads(chunk)
        elif typ == 0x004E4942: binary = chunk

    def read(acc_i):
        acc = js["accessors"][acc_i]; bv = js["bufferViews"][acc["bufferView"]]
        start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        ctype = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}[acc["componentType"]]
        n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[acc["type"]]
        arr = np.frombuffer(binary, dtype=ctype, count=acc["count"] * n, offset=start)
        return arr.reshape(acc["count"], n) if n > 1 else arr

    out = bytearray(); views, accs, meshes = [], [], []
    for m in js["meshes"]:
        pos_parts, idx_parts, base, mat = [], [], 0, None
        for prim in m["primitives"]:
            P_ = read(prim["attributes"]["POSITION"]).astype(np.float32)
            I_ = read(prim["indices"]).astype(np.uint32) if "indices" in prim else np.arange(len(P_), dtype=np.uint32)
            pos_parts.append(P_); idx_parts.append(I_ + base); base += len(P_); mat = prim.get("material", mat)
        pos = np.concatenate(pos_parts); idx = np.concatenate(idx_parts)
        idx = idx.astype(np.uint16) if len(pos) < 65535 else idx.astype(np.uint32)
        def put(arr, target):
            while len(out) % 4: out.append(0)
            start = len(out); out.extend(arr.tobytes())
            views.append(dict(buffer=0, byteOffset=start, byteLength=len(arr.tobytes()), target=target))
            return len(views) - 1
        pv = put(pos, 34962); iv = put(idx, 34963)
        accs.append(dict(bufferView=pv, componentType=5126, count=len(pos), type="VEC3",
                         min=pos.min(0).tolist(), max=pos.max(0).tolist()))
        accs.append(dict(bufferView=iv, componentType=5123 if idx.dtype == np.uint16 else 5125, count=len(idx), type="SCALAR"))
        prim = dict(attributes=dict(POSITION=len(accs) - 2), indices=len(accs) - 1, mode=4)
        if mat is not None:
            prim["material"] = mat
        meshes.append(dict(name=m.get("name", ""), primitives=[prim]))
    js["bufferViews"], js["accessors"], js["meshes"] = views, accs, meshes
    js["buffers"] = [dict(byteLength=len(out), uri="data:application/octet-stream;base64," + base64.b64encode(bytes(out)).decode())]
    with open(json_path, "w") as f:
        json.dump(js, f, separators=(",", ":"))


def dims_bookshelf():
    """Dimension lines for the viewer: [x1,y1,z1], [x2,y2,z2], label, offset dir."""
    g = BS.get("_g") or bs_geometry(); inv = COMPONENTS[P["inverter"]]
    g.setdefault("col_depth_used", 0.0); g.setdefault("stack_top", 0.0)
    col = [COMPONENTS[k] for k in BS["column"]]
    tray_c = COMPONENTS[P["tray_for"]] if P["tray_for"] else col[0]
    two = BS["arrange"] == "2x2"
    wall = 3.0 if two else 4.0
    fw = max(tray_c.w, max(c.w for c in col)) + 2 * wall
    ty = y_in0 + BS["vent"] - wall
    top = out_H + 40
    D = []
    def dim(p1, p2, label, off): D.append(dict(a=p1, b=p2, label=label, off=off))
    dim([0, 0, top], [out_D, 0, top], f"depth {out_D:.0f} mm ({out_D / 25.4:.1f} in)", [0, -60, 0])
    dim([0, 0, top], [0, out_W, top], f"width {out_W:.0f} mm ({out_W / 25.4:.1f} in)", [-60, 0, 0])
    dim([out_D + 60, 0, 0], [out_D + 60, 0, out_H], f"height {out_H:.0f} mm ({out_H / 25.4:.1f} in)", [40, 0, 0])
    zc = col_z0 + 4 + max(c.h for c in col) + 30
    dim([x_in0 + 60, y_in0, zc], [x_in0 + 60, ty + fw, zc], f"battery tray {fw:.0f}", [0, 0, 30])
    dim([x_in0 + 60, ty + fw, zc], [x_in0 + 60, g["parts_lo"], zc], f"gap to dist parts {g['parts_lo'] - (ty + fw):.0f}", [0, 0, 30])
    dim([x_in0 + 60, g["parts_lo"], zc], [x_in0 + 60, g["dist_plate"], zc], f"dist parts {g['dist_plate'] - g['parts_lo']:.0f}", [0, 0, 60])
    dim([x_in0 + 60, g["dist_plate"] + P["card_t"], zc], [x_in0 + 60, g["inv_lo"], zc], f"gap {g['inv_lo'] - g['dist_plate'] - P['card_t']:.0f}", [0, 0, 60])
    dim([x_in0 + 60, g["inv_lo"], zc], [x_in0 + 60, g["inv_plate"], zc], f"inverter {inv.d:.0f} + standoff", [0, 0, 30])
    dim([x_in0 + 60, y_in0, zc + 60], [x_in0 + 60, g["bay_hi"], zc + 60], f"battery column {g['bay_W']:.0f} mm", [0, 0, 90])
    dim([x_in0, ty - 20, col_z0 + 20], [x_in0 + g["col_depth_used"], ty - 20, col_z0 + 20], f"battery rack {g['col_depth_used']:.0f} mm", [0, -40, 0])
    if two:
        st = g["stack_top"]
        dim([x_in0 - 30, ty + fw / 2, col_z0], [x_in0 - 30, ty + fw / 2, col_z0 + st], f"stack {st:.0f} of {in_H_lid:.0f}", [-40, 0, 0])
    dim([g["card_x0"], out_W + 30, floor_top + 2], [g["card_x0"] + g["card_L"], out_W + 30, floor_top + 2], f"cards {g['card_L']:.0f} long", [0, 40, 0])
    return D


def export(a: cq.Assembly):
    os.makedirs(OUT, exist_ok=True); os.makedirs(VIEWER, exist_ok=True); os.makedirs(STL, exist_ok=True)
    glb = os.path.join(OUT, "cage.glb"); a.export(glb, tolerance=1.5, angularTolerance=0.7)
    glb_to_json(glb, os.path.join(VIEWER, f"cage-{VARIANT}.json"))
    if P["card_plane"] == "xz":
        with open(os.path.join(VIEWER, f"dims-{VARIANT}.json"), "w") as f:
            json.dump(dims_bookshelf(), f)
    print("== Printed parts (P1P/P1S bed 256 x 256 x 256) ==")
    seen = {}
    for child in a.children:
        if child.name.startswith("print_"):
            cq.exporters.export(child.obj, os.path.join(STL, f"{child.name.replace('__card', '')}.stl"))
            bb = child.obj.val().BoundingBox()
            dims = tuple(round(v, 1) for v in sorted((bb.xlen, bb.ylen, bb.zlen), reverse=True))
            key = child.name.split("_")[1]
            seen.setdefault((key, dims), 0); seen[(key, dims)] += 1
    for (key, dims), n in seen.items():
        flag = "" if dims[0] <= 256 and dims[1] <= 256 else "  <-- exceeds bed"
        print(f"  {n:2d} x {key:10s} {dims[0]:6.1f} x {dims[1]:6.1f} x {dims[2]:6.1f}{flag}")


def report_bookshelf():
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.2f} in)"
    g = bs_geometry(); inv = COMPONENTS[P["inverter"]]; bat = COMPONENTS["smart100"]
    print(f"== Variant 'bookshelf' (v6 draft): IceBox 1.3 frame, cards front-to-back along the inboard wall ==")
    print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}; inner {mm(in_D)} x {mm(in_W)} x {mm(in_H)}")
    if P["narrow"]:
        print(f"NARROW frame    : width {mm(out_W)} instead of the IceBox's 487 -> {487.4 - out_W:.0f} mm ({(487.4 - out_W) / 25.4:.1f} in) narrower; "
              f"the 4 width rails are cut to {mm(out_W - 2 * C)} (kit bars are 437); cage flush with the IceBox's {P['align']} face")
    tray_c = COMPONENTS[P["tray_for"]] if P["tray_for"] else None
    if tray_c and tray_c.name != COMPONENTS[BS["column"][0]].name or (tray_c and P["tray_for"] != BS["column"][0]):
        bc = COMPONENTS[BS["column"][0]]
        print(f"trays sized for {P['tray_for']} ({tray_c.d}x{tray_c.w} pocket): {BS['column'][0]} is {bc.d}x{bc.w} -> "
              f"{tray_c.d - bc.d:.0f} mm slack in length, {tray_c.w - bc.w:.0f} mm in width, {'fits' if bc.d <= tray_c.d and bc.w <= tray_c.w else 'DOES NOT FIT'}"
              + ("; needs printed spacer blocks to stop it sliding" if tray_c.d - bc.d > 20 else ""))
    print(f"Y stack from the inboard wall: post/plate {out_W - B - g['inv_plate']:.0f} | inverter {inv.d:.0f} (+{BS['standoff']:.0f} standoff) "
          f"| gap {BS['gap']:.0f} | dist card + parts {P['card_t'] + BS['part_depth']:.0f} | gap {BS['gap']:.0f} | battery column {g['bay_W']:.0f}")
    print(f"cards           : {mm(g['card_L'])} long x {mm(in_H - 8)} tall; inverter {inv.w} long on a {g['card_L']:.0f} card "
          f"({'overhangs' if inv.w > g['card_L'] else 'fits'} the card by {abs(inv.w - g['card_L']):.0f} mm, {in_D - inv.w:.0f} mm clear of the end rails)")
    print(f"inverter card   : {inv.note.split(' on')[0]} {inv.w}x{inv.d}x{inv.h} on its side, {in_H - 12 - inv.h:.0f} mm above it for MPPT + Orion + Cerbo")
    col = [COMPONENTS[k] for k in BS["column"]]
    vent = BS["vent"]
    wide = max(c.w for c in col) + 2 * vent
    n = len(col) * (2 if BS["arrange"] == "2x2" else 1)
    if BS["arrange"] == "inline":
        deep = sum(c.d for c in col) + (len(col) + 1) * vent
        tall = 4 + max(c.h for c in col) + P["term_clear"]
        print(f"battery column  : {mm(g['bay_W'])} wide x {mm(in_D)} deep, standing on the {'Goose Gear plate (no floor under it)' if P['col_on_plate'] else 'floor panel'}; "
              + " + ".join(BS["column"]) + " end to end -> "
              f"{deep:.0f} of {in_D:.0f} deep ({'ok' if deep <= in_D else 'TOO DEEP by %.0f' % (deep - in_D)}), "
              f"{wide:.0f} of {g['bay_W']:.0f} wide incl. 20 mm vents ({'ok' if wide <= g['bay_W'] else 'TOO WIDE by %.0f' % (wide - g['bay_W'])}), "
              f"{tall:.0f} of {in_H_lid:.0f} tall to the lid; no shelf, no legs")
    else:
        L = BS["leg2"] if BS["arrange"] == "2x2" else BS["leg"]
        stack = 4 + sum(c.h for c in col) + (len(col) - 1) * (P["term_clear"] + P["shelf_t"]) + P["term_clear"]
        pos = 2 if BS["arrange"] == "2x2" else 1
        wall = 3.0 if pos == 2 else 4.0
        vent_end = 15.0 if pos == 2 else vent
        deep = pos * (max(c.d for c in col) + 2 * wall) + (pos - 1) * L + 2 * vent_end + (0 if pos == 2 else 2 * L)
        print(f"battery column  : {mm(g['bay_W'])} wide x {mm(in_D)} deep, standing on the {'Goose Gear plate (no floor under it)' if P['col_on_plate'] else 'floor panel'}; {pos} stack(s) of " + " + ".join(BS["column"]) +
              f" -> {stack:.0f} of {in_H_lid:.0f} tall to the lid ({in_H_lid - stack:.0f} spare above the top lugs), "
              f"{wide:.0f} of {g['bay_W']:.0f} wide incl. vents ({'ok' if wide <= g['bay_W'] else 'TOO WIDE by %.0f' % (wide - g['bay_W'])}), "
              f"rack {deep:.0f} of {in_D:.0f} deep with {vent_end:.0f} mm end gaps and {L:.0f} mm legs ({'ok' if deep <= in_D else 'TOO DEEP by %.0f' % (deep - in_D)})")
    ich = {"multiplus": 35, "multiplus_1200": 50, "multiplus_ii": 120, "multiplus_4k": 160}[P["inverter"]]
    ah = {"smart100": 100, "smart160": 160, "smart200": 200, "superpack100": 100, "battery": 60}
    amps = {"smart100": 100, "smart160": 160, "smart200": 200, "superpack100": 100, "battery": 30}
    mult = 2 if BS["arrange"] == "2x2" else 1
    ich = {"multiplus": 35, "multiplus_1200": 50, "multiplus_ii": 120, "multiplus_4k": 160}[P["inverter"]]
    ah = {"smart100": 100, "smart160": 160, "smart200": 200, "superpack100": 100, "battery": 60}
    amps = {"smart100": 100, "smart160": 160, "smart200": 200, "superpack100": 100, "battery": 30}
    print(f"  bank {n} batteries = {mult * sum(ah[k] for k in BS['column'])} Ah ({mult * sum(ah[k] for k in BS['column']) * 12.8 / 1000:.1f} kWh), "
          f"{mult * sum(amps[k] for k in BS['column'])} A recommended continuous; inverter draws ~{ {'multiplus': 70, 'multiplus_1200': 105, 'multiplus_ii': 220, 'multiplus_4k': 310}[P['inverter']] } A at full output, "
          f"charger {ich} A (empty to full ~{mult * sum(ah[k] for k in BS['column']) / ich:.1f} h)")
    print(f"lift clearance  : both cards {mm(in_H - 8)} tall -> {mm(out_H + in_H - 8)} plate-to-ceiling; in the vehicle service is from the top with the lid off")
    bkg = {"smart100": 14, "smart160": 18, "smart200": 20, "superpack100": 10.5, "battery": 7.5}
    ikg = {"multiplus": 6.4, "multiplus_1200": 8.2, "multiplus_ii": 19.0, "multiplus_4k": 22.0}[P["inverter"]]
    kg = mult * sum(bkg[k] for k in BS["column"]) + ikg + 1.3 + 0.33 + 0.5 + 0.3 + 0.3 + 1.5 + 4.0 + 19.0
    print(f"  est. mass ~{kg:.0f} kg")


def report():
    if P["card_plane"] == "xz":
        return report_bookshelf()
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.2f} in)"
    kind = "437 mm cube frame from 12 uncut kit bars" if P["frame_source"] == "kit" else "a second IceBox 1.3 frame, fridge slide removed"
    print(f"== Variant '{VARIANT}': {kind} ==")
    print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}   ({P['icebox_H'] - out_H:.0f} mm below the IceBox deck)")
    print(f"inner D x W x H : {mm(in_D)} x {mm(in_W)} x {mm(in_H)}")
    print(f"rear layer {P['rear_depth']:.0f} deep (batteries {batt.d}), main cards at x={card_x - x_in0:.0f}, "
          f"MultiPlus to x={card_x - x_in0 + 6 + COMPONENTS['multiplus'].d:.0f}, dist card at x={dist_x - x_in0:.0f}, "
          f"its parts to x={dist_x - x_in0 + 6 + 48:.0f}, front panel at x={in_D:.0f} (sockets reach back to {in_D - 40:.0f})")
    print(f"cards           : inverter/charger (lower) {mm(card_W)} x {mm(lower_h)}, upper {mm(card_W)} x {mm(upper_h)}, distribution {mm(dist_W)} x {mm(dist_h)}, all 6 mm")
    print(f"lift clearance  : upper card needs {mm(out_H + upper_h)} plate-to-ceiling; inverter/charger card {mm(out_H + lower_h)}; distribution card {mm(out_H + dist_h)} (or tilt it out forward)")
    if P["batt_layout"] == "row3_top1":
        top = shelf_z - floor_top + P["shelf_t"] + batt_top.h
        print(f"battery bay     : row of {P['n_batt_row']} = {row_W:.0f} of {in_W:.0f} wide; 4th on its side on top -> "
              f"{top:.0f} of {in_H:.0f} tall ({in_H - top:.0f} spare)")
    else:
        top = shelf_z - floor_top + P["shelf_t"] + batt.h + P["term_clear"]
        print(f"battery bay     : 2 upright stacks of 2 against the side walls, {batt.w + 8:.0f} wide each, {batt.d + 8:.0f} deep; "
              f"stack {top:.0f} of {in_H:.0f} tall incl. lug clearance ({in_H - top:.0f} spare); "
              f"centre channel {in_W - 2 * (batt.w + 8):.0f} mm wide (a third stack would fit)")
    if P["frame_source"] == "icebox":
        print("== Rails: stock IceBox 1.3 frame; the 16 kit bars are not needed (2 could be floor joists) ==")
        runs, pool = {}, []
    else:
        runs, pool = allocate_rails()
        print(f"== Rails from {P['kit_bars']} kit bars @ {mm(P['bar_stock'])} (= IceBox width rail; verify on arrival) ==")
    for name, r in runs.items():
        print(f"  {name:3s} " + " + ".join(f"{k} {ln:.0f}" + (f" (bar {b + 1})" if b is not None else "") for k, ln, b in r))
    if runs:
        n_print = sum(1 for r in runs.values() for k, _, _ in r if k == "print")
        n_splice = sum(max(0, len(r) - 1) for r in runs.values())
        used = [i for i, rem in enumerate(pool) if rem < P["bar_stock"] - 0.01]
        print(f"  bars touched {len(used)} of {P['kit_bars']}, untouched {P['kit_bars'] - len(used)}, "
              f"printed rail segments {n_print}, splices {n_splice}")
    print("== Panels (6 mm) ==")
    print(f"  floor + lid   {mm(in_D + 2 * T)} x {mm(in_W + 2 * T)}")
    print(f"  2 sides       {mm(in_D + 2 * T)} x {mm(in_H + 2 * T)}")
    print(f"  back + front  {mm(in_W)} x {mm(in_H + 2 * T)}")
    print("== Fit checks ==")
    mp = INV
    fits = mp.w <= card_W and mp.h + 10 <= lower_h and lower_h + 6 <= in_H
    print(f"  inverter/charger card: {mp.note.split(' on')[0]} {mp.w}x{mp.h}x{mp.d} on {card_W:.0f}x{lower_h:.0f} -> "
          f"{'ok' if fits else 'DOES NOT FIT: ' + ('too long for the card width by %.0f mm' % (mp.w - card_W) if mp.w > card_W else 'too tall')}"
          f"; upright would need {mp.w + 10:.0f} of {in_H:.0f} mm height")
    for pl in UPPER_CARD_LAYOUT:
        c = COMPONENTS[pl["comp"]]
        bad = []
        if pl["y"] + c.w > card_W: bad.append("Y overflow")
        if pl["z"] + c.h > upper_h: bad.append("Z overflow")
        if c.d > P["front_depth"]: bad.append("too deep")
        print(f"  upper card {c.name:20s} {c.w:>4.0f}x{c.h:>4.0f}x{c.d:>3.0f} @({pl['y']},{pl['z']}) {' '.join(bad) or 'ok'}")
    for pl in DIST_CARD_LAYOUT:
        c = COMPONENTS[pl["comp"]]
        bad = []
        if pl["y"] + c.w > dist_W: bad.append("Y overflow")
        if pl["z"] + c.h > dist_h: bad.append("Z overflow")
        if dist_x + P["card_t"] + c.d > x_in0 + in_D - 40 and pl["z"] + c.h > P["socket_z"] - 35: bad.append("behind the sockets")
        print(f"  distribution {c.name:20s} {c.w:>4.0f}x{c.h:>4.0f}x{c.d:>3.0f} @({pl['y']},{pl['z']}) {' '.join(bad) or 'ok'}")
    kg = N_BATT * 9.5 + {"multiplus": 6.4, "multiplus_ii": 19.0, "multiplus_4k": 22.0}[P["inverter"]] + 1.3 + 0.33 + 0.5 + 0.3 + 0.3 + 1.5 + 3.0 + (5.0 if P["frame_source"] == "kit" else 19.0)
    print(f"  est. mass ~{kg:.0f} kg; box depth {out_D:.0f} -> tie it to the IceBox panel / plate")


if __name__ == "__main__":
    asm = build()
    report()
    export(asm)
    print("wrote", os.path.abspath(os.path.join(VIEWER, f"cage-{VARIANT}.json")))
