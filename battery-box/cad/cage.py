"""4Runner electronics card cage, v2 "slab" — parametric CadQuery model.

The box is an extension of the Goose Gear IceBox 1.3: exactly its width and
height (19-3/16" x 22"), as shallow as the parts allow, standing against the
IceBox's slotted back panel.  Heavy things sit low in a rear layer; a pair of
vertical cards drop into side guides and carry the MultiPlus and the small
electronics.

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
from dataclasses import dataclass

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
STL = os.path.join(HERE, "..", "stl")
VIEWER = os.path.join(HERE, "..", "viewer")

# ----------------------------------------------------------------------------
# Parameters (mm)
# ----------------------------------------------------------------------------
P = dict(
    # IceBox 1.3, 25" deep (Goose Gear): 19-3/16 W x 22 H x 25 D.  The cage
    # copies W and H exactly.
    icebox_W=487.4, icebox_H=558.8, icebox_D=635.0,
    icebox_gap=0.0,      # air gap between IceBox back panel and the cage
    show_icebox=True,

    bar=25.4,            # Goose Gear MaxLite 1" extrusion (profile verify)
    cube=25.4,           # printed 3-way corner cube
    panel_t=6.0,         # panels: 6 mm phenolic ply / HDPE
    card_t=6.0,
    card_clear=0.6,

    # Depth budget = exactly half an IceBox (317.5 outer).  rear_depth holds
    # the batteries (138 deep) in their tray + the distribution card;
    # front_depth holds the MultiPlus (100 deep) hanging on the lower card.
    rear_depth=144.0,
    front_depth=104.7,

    # Frame sourcing: NO off-the-shelf extrusion and NO printed rail (the
    # MaxLite die can't be copied).  8 mod kits = 16 bars; each bar is an
    # IceBox width rail, i.e. 19-3/16" minus two 1" cubes.  (verify on arrival)
    kit_bars=16,
    bar_stock=436.6,
    rail_seg_max=250.0,  # only used if the bar pool runs out
    splice_len=60.0,     # printed cross key joining two bar pieces

    guide_w=18.0,        # printed U-channel: width along the side wall... (Y is the wall normal here)
    guide_d=14.0,        # stand-off from the side wall into the box
    guide_wall=3.0,
    guide_seg_max=250.0,

    shelf_t=10.0,        # printed mid-shelf between the stacked batteries
    tray_lip=20.0,
    term_clear=14.0,     # clearance above each battery for lugs (verify: is the terminal inside the 213?)

    # cards: lower carries the MultiPlus, upper the small electronics,
    # dist card (rear layer, beside the batteries) the shunt/breakers/bus/Cerbo
    lower_card_h=254.0,
    dist_card_x=10.0,    # rear face of the dist card from the back panel
    socket_z=430.0,      # 12V socket centreline on the front panel (above the MultiPlus band)
    socket_panel_h=60.0,
    socket_panel_t=5.0,
    vent_rows=3,         # vent slots in the front panel over the MultiPlus band
)


@dataclass
class Comp:
    name: str   # prefix drives viewer colouring: victron / garmin / power / battery / socket
    w: float    # along Y (width) as mounted
    d: float    # along X (depth) as mounted
    h: float    # along Z as mounted
    note: str = ""


COMPONENTS = {
    "battery":   Comp("battery", 229, 138, 213, "Victron Lithium SuperPack 12.8V/60Ah, 9.5 kg, M6 top terminals (x2, stacked)"),
    "multiplus": Comp("victron_multiplus", 360, 100, 240, "MultiPlus 12/800/35-16 120V on its side on the lower card (6.4 kg)"),
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
DIST_CARD_LAYOUT = [
    dict(comp="breaker_a", y=20,  z=20),
    dict(comp="breaker_b", y=85,  z=20),
    dict(comp="shunt",     y=20,  z=115),
    dict(comp="busbar_n",  y=4,   z=190),
    dict(comp="busbar_p",  y=4,   z=240),
    dict(comp="cerbo",     y=4,   z=300),
]
# Upper card (charge sources + loads), y, z relative to the card's lower-left.
UPPER_CARD_LAYOUT = [
    dict(comp="mppt",   y=20,  z=12),
    dict(comp="orion",  y=240, z=12),
    dict(comp="garmin", y=20,  z=155),
]
# Lower card: MultiPlus on its side, centred.
# Front-panel 12 V / USB sockets: (y centre, hole dia)
SOCKETS = [(70, 29), (115, 29), (160, 29), (205, 29), (255, 22)]
# Anderson SB50s in the inboard side panel, rear layer: (x centre, z centre)
ANDERSONS = [(110, 100), (110, 150)]

# ----------------------------------------------------------------------------
# Derived
# ----------------------------------------------------------------------------
B, C, T = P["bar"], P["cube"], P["panel_t"]
out_W, out_H = P["icebox_W"], P["icebox_H"]
in_W = out_W - 2 * B - 2 * T
in_H = out_H - 2 * B - 2 * T
in_D = P["rear_depth"] + P["card_t"] + P["front_depth"]
out_D = in_D + 2 * T + 2 * B
x_in0, y_in0, floor_top = B + T, B + T, B + T       # inner origin
card_x = x_in0 + P["rear_depth"]                   # rear face of the cards
card_W = in_W - 2 * (P["guide_d"] - P["guide_wall"]) - 2 * P["card_clear"]
card_y0 = y_in0 + (in_W - card_W) / 2
lower_h = P["lower_card_h"]
upper_h = in_H - lower_h - 6                       # 6 mm under the lid
batt = COMPONENTS["battery"]
col_W = batt.w + 8                                 # battery column width incl. tray walls
dist_y0 = y_in0 + col_W + 2 + (P["guide_d"] - P["guide_wall"]) + P["card_clear"]
dist_W = (out_W - B - T - (P["guide_d"] - P["guide_wall"]) - P["card_clear"]) - dist_y0
dist_h = in_H - 8


def box(w, d, h, at=(0, 0, 0)):
    return cq.Workplane("XY").box(w, d, h, centered=False).translate(at)


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
def card_guide_segments():
    """Printed U-channel on each side wall, full inner height, in segments."""
    gw = P["card_t"] + 2 * P["card_clear"]
    total = in_H - 2
    segs, z = [], 0.0
    while z < total - 0.5:
        h = min(P["guide_seg_max"], total - z)
        g = box(P["guide_w"], P["guide_d"], h)                      # w along X here, stands off wall in Y
        g = g.cut(box(gw, P["guide_d"] - P["guide_wall"] + 1, h + 1, ((P["guide_w"] - gw) / 2, -1, -0.5)))
        if z + h >= total - 0.5:  # top segment: flare
            flare = (cq.Workplane("XZ").polyline([((P["guide_w"] - gw) / 2, h - 8), ((P["guide_w"] + gw) / 2, h - 8),
                                                   ((P["guide_w"] + gw) / 2 + 2.5, h + 1), ((P["guide_w"] - gw) / 2 - 2.5, h + 1)])
                     .close().extrude(-(P["guide_d"] - P["guide_wall"])))
            g = g.cut(flare)
        segs.append((z, g)); z += h
    return segs


def battery_tray():
    lip, wall = P["tray_lip"], 4.0
    t = box(batt.d + 2 * wall, batt.w + 2 * wall, lip + 4)
    t = t.cut(box(batt.d, batt.w, lip + 5, (wall, wall, 4)))
    for y in (batt.w * 0.25, batt.w * 0.75):   # strap slots across the depth
        t = t.cut(box(batt.d + 2 * wall + 2, 30, 6, (-1, y - 15, 6)))
    return t


def mid_shelf():
    """Printed cradle that sits on the lower battery and locates the upper one.
    A 10 mm plate with a 12 mm lip on the upper side; bolts to the side rail."""
    wall = 4.0
    s = box(batt.d + 2 * wall, batt.w + 2 * wall, P["shelf_t"] + 12)
    s = s.cut(box(batt.d, batt.w, 13, (wall, wall, P["shelf_t"])))
    s = s.cut(box(batt.d - 30, batt.w - 30, P["shelf_t"] + 1, (wall + 15, wall + 15, -0.5)))  # weight-saving window
    return s


def multiplus_feet():
    """Two printed feet on the lower card that take the MultiPlus weight."""
    return box(40, 50, 10).edges("|Z").fillet(3)


def socket_insert():
    ys = [y for y, _ in SOCKETS]
    w = max(ys) - min(ys) + 60
    sp = box(P["socket_panel_t"], w, P["socket_panel_h"],
             (out_D - B - T, y_in0 + min(ys) - 30, floor_top + P["socket_z"] - P["socket_panel_h"] / 2))
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
    parts.append(("icebox_panel_top", box(D - 2 * B, W - 2 * B, T, (x0 + B, B, H - B - T))))
    parts.append(("icebox_panel_floor", box(D - 2 * B, W - 2 * B, T, (x0 + B, B, B))))
    parts.append(("icebox_panel_side_out", box(D - 2 * B, T, H - 2 * B, (x0 + B, B, B))))
    parts.append(("icebox_panel_side_in", box(D - 2 * B, T, H - 2 * B, (x0 + B, W - B - T, B))))
    back = box(T, W - 2 * B, H - 2 * B, (x0 + D - B - T, B, B))
    slot_w, slot_h, pitch_y, pitch_z = 72.0, 22.0, 92.0, 46.0
    rows = int((H - 2 * B - 120) / pitch_z)
    for r in range(rows):
        z = B + 60 + r * pitch_z
        y = B + 40 + ((pitch_y / 2) if r % 2 else 0)
        while y + slot_w < W - B - 30:
            cutter = (cq.Workplane("YZ").center(y + slot_w / 2, z + slot_h / 2)
                      .slot2D(slot_w, slot_h).extrude(T + 2).translate((x0 + D - B - T - 1, 0, 0)))
            back = back.cut(cutter); y += pitch_y
    parts.append(("icebox_panel_back_slotted", back))
    tray = box(D - 2 * B + 60, 381, 40, (x0 + B - 60, (W - 381) / 2, B + T))
    tray = tray.cut(box(D - 2 * B + 52, 373, 40, (x0 + B - 56, (W - 381) / 2 + 4, B + T + 4)))
    parts.append(("icebox_tray", tray))
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

    # --- panels --------------------------------------------------------------
    add(a, box(in_D + 2 * T, in_W + 2 * T, T, (B, B, B)), "panel_floor", PANEL)
    add(a, box(in_D + 2 * T, in_W + 2 * T, T, (B, B, out_H - B - T)), "lid_panel", PANEL)
    for y in (out_W * 0.3, out_W * 0.7):
        add(a, lid_handle().translate((out_D / 2 - 6, y - 30, out_H - B)), f"lid_handle_{int(y)}", BLACK)
    add(a, box(in_D + 2 * T, T, in_H + 2 * T, (B, B, B)), "panel_side_outboard", PANEL)
    inboard = box(in_D + 2 * T, T, in_H + 2 * T, (B, out_W - B - T, B))
    ca = COMPONENTS["anderson"]
    for (x, z) in ANDERSONS:
        inboard = inboard.cut(box(ca.w, T + 2, ca.h, (x_in0 + x - ca.w / 2, out_W - B - T - 1, floor_top + z - ca.h / 2)))
        add(a, box(ca.w, 40, ca.h, (x_in0 + x - ca.w / 2, out_W - B - T - 40, floor_top + z - ca.h / 2)),
            f"socket_anderson_{int(z)}", (0.3, 0.3, 0.3))
    add(a, inboard, "panel_side_inboard", PANEL)
    # back panel (touches the IceBox): cable pass-through slot low down
    back = box(T, in_W, in_H + 2 * T, (B, y_in0, B))
    back = back.cut(box(T + 2, 120, 30, (B - 1, y_in0 + col_W + 20, floor_top + 40)))
    add(a, back, "panel_back_icebox_side", PANEL)
    # front panel (removable): vent slots over the MultiPlus band + socket insert
    front = box(T, in_W, in_H + 2 * T, (out_D - B - T, y_in0, B))
    for r in range(P["vent_rows"]):
        z = floor_top + 40 + r * 60
        for y in range(40, int(in_W) - 100, 70):
            front = front.cut(cq.Workplane("YZ").center(y_in0 + y + 30, z).slot2D(60, 10).extrude(out_D + 1))
    si = socket_insert()
    bb = si.val().BoundingBox()
    front = front.cut(box(T + 2, bb.ylen, bb.zlen, (out_D - B - T - 1, bb.ymin, bb.zmin)))
    add(a, front, "panel_front_removable", PANEL)
    add(a, si, "print_socket_insert", ORANGE)
    for y, dia in SOCKETS:
        s = (cq.Workplane("YZ").center(y_in0 + y, floor_top + P["socket_z"]).circle(dia / 2 + 3)
             .extrude(-40).translate((out_D - B - T, 0, 0)))
        add(a, s, f"socket_{y}", (0.3, 0.3, 0.3))

    # --- rear layer: battery column (outboard), stacked -----------------------
    bx, by = x_in0 + 4, y_in0 + 4
    add(a, battery_tray().translate((x_in0, y_in0, floor_top)), "print_tray_battery", ORANGE)
    z_lo = floor_top + 4
    add(a, box(batt.d, batt.w, batt.h, (bx, by, z_lo)).edges("|Z").fillet(6), "battery_lower", BATT)
    z_shelf = z_lo + batt.h + P["term_clear"]
    add(a, mid_shelf().translate((x_in0, y_in0, z_shelf)), "print_shelf_mid", ORANGE)
    z_hi = z_shelf + P["shelf_t"]
    add(a, box(batt.d, batt.w, batt.h, (bx, by, z_hi)).edges("|Z").fillet(6), "battery_upper", BATT)

    # --- rear layer: distribution card, inboard of the batteries ---------------
    dx = x_in0 + P["dist_card_x"]
    add(a, box(P["card_t"], dist_W, dist_h, (dx, dist_y0, floor_top + 2)), "card_dist_plate", DARK)
    for pl in DIST_CARD_LAYOUT:
        c = COMPONENTS[pl["comp"]]
        col = BLUE if c.name.startswith("victron") else GOLD
        add(a, box(c.d, c.w, c.h, (dx + P["card_t"], dist_y0 + pl["y"], floor_top + 2 + pl["z"])).edges("|X").fillet(3),
            c.name + "__card", col)
    # its guides: one on the inboard wall, one on a printed divider post next to the batteries
    gx = dx - (P["guide_w"] - P["card_t"]) / 2 - P["card_clear"]
    for k, (z, g) in enumerate(card_guide_segments()):
        add(a, g.mirror("XZ").translate((gx, out_W - B - T, floor_top + z)), f"print_guide_dist_wall_{k}", ORANGE)
        add(a, g.translate((gx, y_in0 + col_W + 2, floor_top + z)), f"print_guide_dist_post_{k}", ORANGE)

    # --- card guides (both side walls) ---------------------------------------
    for j, y in enumerate((y_in0, out_W - B - T - P["guide_d"])):
        for k, (z, g) in enumerate(card_guide_segments()):
            if j == 1:
                g = g.mirror("XZ").translate((0, P["guide_d"], 0))
            add(a, g.translate((card_x - (P["guide_w"] - P["card_t"]) / 2 - P["card_clear"], y, floor_top + z)),
                f"print_guide_{j}_{k}", ORANGE)

    # --- lower card: MultiPlus on its side -----------------------------------
    add(a, box(P["card_t"], card_W, lower_h, (card_x, card_y0, floor_top + 2)), "card_lower_plate", DARK)
    mp = COMPONENTS["multiplus"]
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
# Export + report
# ----------------------------------------------------------------------------
def glb_to_json(glb_path: str, json_path: str):
    d = open(glb_path, "rb").read()
    assert d[:4] == b"glTF"
    off, js, binary = 12, None, None
    while off < len(d):
        ln, typ = struct.unpack("<II", d[off:off + 8]); chunk = d[off + 8:off + 8 + ln]; off += 8 + ln
        if typ == 0x4E4F534A: js = json.loads(chunk)
        elif typ == 0x004E4942: binary = chunk
    js["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(binary).decode()
    with open(json_path, "w") as f:
        json.dump(js, f)


def export(a: cq.Assembly):
    os.makedirs(OUT, exist_ok=True); os.makedirs(VIEWER, exist_ok=True); os.makedirs(STL, exist_ok=True)
    glb = os.path.join(OUT, "cage.glb"); a.export(glb); glb_to_json(glb, os.path.join(VIEWER, "cage.json"))
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


def report():
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.2f} in)"
    print("== Box (extension of the IceBox 1.3 footprint) ==")
    print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}   (W, H = IceBox)")
    print(f"inner D x W x H : {mm(in_D)} x {mm(in_W)} x {mm(in_H)}")
    print(f"rear layer {P['rear_depth']:.0f} deep (batteries {batt.d}), cards at x={card_x - x_in0:.0f}, front layer {P['front_depth']:.0f} deep (MultiPlus {COMPONENTS['multiplus'].d})")
    print(f"cards           : lower {mm(card_W)} x {mm(lower_h)}, upper {mm(card_W)} x {mm(upper_h)}, dist {mm(dist_W)} x {mm(dist_h)}, all 6 mm")
    print(f"lift clearance  : upper card needs {mm(out_H + upper_h)} plate-to-ceiling; lower {mm(out_H + lower_h)}; dist {mm(out_H + dist_h)} (or tilt it out forward)")
    stack_top = 4 + 2 * batt.h + P["term_clear"] + P["shelf_t"] + P["term_clear"]
    print(f"battery stack   : {stack_top:.0f} mm incl. lug clearance vs {in_H:.0f} inner -> {in_H - stack_top:.0f} mm spare")
    runs, pool = allocate_rails()
    print(f"== Rails from {P['kit_bars']} kit bars @ {mm(P['bar_stock'])} (= IceBox width rail; verify on arrival) ==")
    for name, r in runs.items():
        print(f"  {name:3s} " + " + ".join(f"{k} {ln:.0f}" + (f" (bar {b + 1})" if b is not None else "") for k, ln, b in r))
    n_print = sum(1 for r in runs.values() for k, _, _ in r if k == "print")
    n_splice = sum(max(0, len(r) - 1) for r in runs.values())
    used = [i for i, rem in enumerate(pool) if rem < P["bar_stock"] - 0.01]
    print(f"  bars touched {len(used)} of {P['kit_bars']}, untouched {P['kit_bars'] - len(used)}, "
          f"printed rail segments {n_print}, splices {n_splice}")
    print("  cut plan per bar:")
    for i in used:
        pieces = [f"{ln:.0f} -> {name}" for name, r in runs.items() for k, ln, b in r if b == i]
        print(f"    bar {i + 1:2d}: " + ", ".join(pieces) + f"; offcut {pool[i]:.0f}")
    print("== Panels (6 mm) ==")
    print(f"  floor + lid   {mm(in_D + 2 * T)} x {mm(in_W + 2 * T)}")
    print(f"  2 sides       {mm(in_D + 2 * T)} x {mm(in_H + 2 * T)}")
    print(f"  back + front  {mm(in_W)} x {mm(in_H + 2 * T)}")
    print("== Fit checks ==")
    mp = COMPONENTS["multiplus"]
    print(f"  lower card: MultiPlus {mp.w}x{mp.h} on {card_W:.0f}x{lower_h:.0f} -> {'ok' if mp.w <= card_W and mp.h + 10 <= lower_h else 'DOES NOT FIT'}; depth {mp.d} of {P['front_depth']:.0f}")
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
        if P["dist_card_x"] + P["card_t"] + c.d > P["rear_depth"]: bad.append("too deep")
        print(f"  dist card  {c.name:20s} {c.w:>4.0f}x{c.h:>4.0f}x{c.d:>3.0f} @({pl['y']},{pl['z']}) {' '.join(bad) or 'ok'}")
    kg = 2 * 9.5 + 6.4 + 1.3 + 0.33 + 0.5 + 0.3 + 0.3 + 1.0 + 3.0 + 4.0
    print(f"  est. mass ~{kg:.0f} kg; box depth {out_D:.0f} -> tie it to the IceBox panel / plate")


if __name__ == "__main__":
    asm = build()
    report()
    export(asm)
    print("wrote", os.path.abspath(os.path.join(VIEWER, "cage.json")))
