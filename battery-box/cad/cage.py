"""4Runner electronics card cage — parametric CadQuery model.

Run:  .venv/bin/python cage.py          (from battery-box/cad)
Out:  ../viewer/cage.json                coloured assembly (glTF, embedded buffer) for the web viewer
      ../stl/*.stl                       one STL per printable part (committed)
      ../renders/*.png                   shaded views (render.py)
      out/views/*.svg|png                line drawings (gitignored)

Coordinate system (mm):
  X = along the long axis of the box.  x=0 is the IceBox end (the end that
      butts against the IceBox 1.3 slotted back panel).
  Y = across the box.  y=0 is the outboard side (against the vehicle wall);
      +Y is the inboard / serviceable side where the socket panel lives.
  Z = up, 0 at the underside of the frame.

Everything is driven from the P / COMPONENTS / layout tables below.
Dimensions tagged "verify" have not been measured on the real part yet.
"""
from __future__ import annotations

import base64
import json
import os
import struct
import subprocess
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
    # Inner clear space of the box.  Scaled from the photos of the plywood
    # box; measure the real one before cutting bars.  (verify)
    in_L=1000.0,   # keeps today's ~40" footprint; Phase 2 wants ~1200 (see README)
    in_W=290.0,    # two SuperPacks side by side (2 x 138) + tray walls
    in_H=260.0,    # SuperPack 213 + tray 4 + ~40 for M6 terminals / cables

    bar=25.4,        # Goose Gear MaxLite 1" extrusion (profile verify)
    # Frame sourcing: NO off-the-shelf extrusion.  The 4 Goose Gear mod kits
    # supply the aluminium (assumed 2 bars per kit); everything else prints.
    kit_bars=8,
    bar_stock=635.0,   # length of one kit bar.  UNKNOWN until they arrive (verify)
    rail_seg_max=250.0,  # printed rail segments must fit the 256 mm bed
    splice_len=60.0,     # printed internal splice between a bar and a printed segment

    # IceBox 1.3, 25" deep: 19-3/16 W x 22 H x 25 D (Goose Gear).  Its slotted
    # back panel faces the cage's x=0 end.
    icebox_W=487.4, icebox_H=558.8, icebox_D=635.0,
    icebox_gap=0.0,    # air gap between IceBox back panel and the cage end
    icebox_y=0.0,      # IceBox outboard face offset from the cage's outboard face
    show_icebox=True,
    cube=25.4,       # printed 3-way corner cube, same section as the bar
    panel_t=6.0,     # side/floor/lid panels: 6 mm phenolic ply or HDPE
    card_t=6.0,      # card plate thickness
    card_clear=0.6,  # per-side slip in the guide channel

    # Card underside height above the floor panel top.  Must clear the
    # tallest thing on the lower level (MultiPlus lying flat = 100) + wiring.
    card_z=150.0,
    card_margin=4.0,  # gap between card edge and side panels
    # The card covers only the MultiPlus / electronics zone.  A bulkhead at
    # bulk_x separates it from the battery zone so the card lifts out without
    # touching the battery.
    bulk_x=245.0,
    bulk_t=6.0,

    guide_w=18.0,    # printed card guide: U-channel width (along the end wall)
    guide_d=14.0,    # how far it stands off the end wall
    guide_wall=3.0,

    ledge_w=12.0,    # printed support ledge under the card, along the long walls
    ledge_t=8.0,

    socket_panel_h=70.0,   # printed socket insert on the inboard wall
    socket_panel_t=5.0,
    socket_z=160.0,        # socket centreline height above the floor panel (above the card)
)

@dataclass
class Comp:
    name: str   # prefix drives viewer colouring: victron / garmin / power / battery / misc
    w: float    # along X
    d: float    # along Y
    h: float    # along Z, as mounted
    note: str = ""

# Component envelopes AS MOUNTED (box-aligned, not datasheet h x w x d).
COMPONENTS = {
    # lower level (on the floor)
    "multiplus": Comp("victron_multiplus", 360, 240, 100, "MultiPlus 12/800/35-16 120V, lying flat as today (6.4 kg)"),
    "mppt":      Comp("victron_mppt", 186, 70, 130, "SmartSolar MPPT 100/30, vertical, terminals down (1.3 kg)"),
    "battery":   Comp("battery", 229, 138, 213, "Victron Lithium SuperPack 12.8V/60Ah, 9.5 kg, M6 terminals (x2)"),
    # on the card, top face
    "cerbo":     Comp("victron_cerbo", 154, 78, 48, "Cerbo GX"),
    "orion":     Comp("victron_orion", 123, 137, 40, "Orion XS 12/12-50A, flat as today (Victron prefers vertical)"),
    "shunt":     Comp("power_shunt", 120, 54, 46, "SmartShunt 500A"),
    "garmin":    Comp("garmin_powerswitch", 125, 75, 32, "Garmin PowerSwitch"),
    "busbar_p":  Comp("power_busbar_pos", 155, 32, 35, "5-stud covered bus bar (+)"),
    "busbar_n":  Comp("power_busbar_neg", 155, 32, 35, "5-stud covered bus bar (-)"),
    "breaker_a": Comp("power_breaker_a", 48, 74, 43, "surface-mount breaker"),
    "breaker_b": Comp("power_breaker_b", 48, 74, 43, "surface-mount breaker"),
    # end-panel ingress for the solar panels: 2 x Anderson SB50 panel mounts
    "anderson":  Comp("socket_anderson", 10, 48, 36, "Anderson SB50 panel-mount, solar in (verify hole 48 x 36)"),
}

# Lower level: x from the IceBox end; y centred across the box unless given.
FLOOR_LAYOUT = [
    dict(comp="battery",   x=8,   y=4,   tag="battery_outboard"),
    dict(comp="battery",   x=8,   y=146, tag="battery_inboard"),
    dict(comp="multiplus", x=262, y=None, tag="victron_multiplus"),   # under the card, centred
    dict(comp="mppt",      x=700, y=12,  tag="victron_mppt"),         # standing, under the card, outboard
]

# Card: x,y = lower-left corner relative to the card's own corner.
CARD_LAYOUT = [
    # nearest the bulkhead / batteries: protection + distribution
    dict(comp="breaker_a", x=15,  y=30,  side="top"),
    dict(comp="breaker_b", x=15,  y=170, side="top"),
    dict(comp="busbar_p",  x=85,  y=20,  side="top"),
    dict(comp="shunt",     x=85,  y=115, side="top"),
    dict(comp="busbar_n",  x=85,  y=230, side="top"),
    # middle: charge sources + loads
    dict(comp="orion",     x=270, y=20,  side="top"),
    dict(comp="garmin",    x=270, y=190, side="top"),
    # far end: brains
    dict(comp="cerbo",     x=430, y=20,  side="top"),
]

# Anderson SB50 panel mounts in the far end panel, lower level, near the MPPT:
# (y centre, z centre above floor panel)
ANDERSONS = [(150, 60), (215, 60)]

# Panel-mount sockets on the inboard wall insert: (x centre, hole dia)
SOCKETS = [(580, 29), (625, 29), (670, 29), (715, 29), (765, 22)]

# ----------------------------------------------------------------------------
# Derived
# ----------------------------------------------------------------------------
B, C, T = P["bar"], P["cube"], P["panel_t"]
in_L, in_W, in_H = P["in_L"], P["in_W"], P["in_H"]
out_L = in_L + 2 * T + 2 * B      # panels sit inside the bars
out_W = in_W + 2 * T + 2 * B
out_H = in_H + 2 * T + 2 * B
floor_top = B + T                 # z of the floor panel's top face
card_z = floor_top + P["card_z"]  # z of the card's underside
zone_x0 = P["bulk_x"] + P["bulk_t"]      # card zone starts after the bulkhead
zone_L = in_L - zone_x0
card_L = zone_L - 2 * (P["guide_d"] - P["guide_wall"]) - 2 * P["card_clear"]
card_W = in_W - 2 * P["card_margin"]
card_x0 = B + T + zone_x0 + (zone_L - card_L) / 2
card_y0 = B + T + (in_W - card_W) / 2


def box(w, d, h, at=(0, 0, 0)):
    return cq.Workplane("XY").box(w, d, h, centered=False).translate(at)


# ----------------------------------------------------------------------------
# Parts
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


def allocate_rails():
    """Decide which rails are kit aluminium and which are printed.

    Short rails (4 width + 4 height) come first: one bar yields one width rail
    plus one height rail when stock >= their sum, otherwise one rail per bar.
    Whatever bars remain go to the long rails, one bar each, with the
    remainder of each long rail printed in segments.  Returns a dict of
    rail name -> list of (kind, length) runs along the rail."""
    stock = P["bar_stock"]; bars = P["kit_bars"]
    L_long, L_w, L_h = out_L - 2 * C, out_W - 2 * C, out_H - 2 * C
    runs = {}
    short = [("w", L_w)] * 4 + [("h", L_h)] * 4
    pairs = stock >= L_w + L_h
    bars_short = 4 if pairs else 8
    bars_used = min(bars, bars_short)
    covered = bars_used * (2 if pairs else 1)
    for i, (k, ln) in enumerate(short):
        runs[f"{k}{i % 4}"] = [("bar" if i < covered else "print", ln)]
    left = bars - bars_used
    for i in range(4):
        if left > 0 and stock > 0:
            left -= 1
            bar_ln = min(stock, L_long)
            segs = [("bar", bar_ln)]
            rest = L_long - bar_ln
        else:
            segs, rest = [], L_long
        while rest > 0.5:
            seg = min(P["rail_seg_max"], rest)
            segs.append(("print", seg)); rest -= seg
        runs[f"l{i}"] = segs
    return runs


def printed_rail(length: float):
    """Printed 1" square rail segment with a T-slot on each face, a 6.8 mm
    centre bore for a through-bolt / splice pin.  Same envelope as the bar so
    cubes, guides and ledges don't care which one they touch."""
    r = bar(length, "x")
    r = r.cut(cq.Workplane("YZ").circle(3.4).extrude(length))
    return r


def splice():
    """Printed internal splice: a cross-shaped key that slides into the four
    T-slots of both the bar and the printed segment it joins."""
    k = cq.Workplane("YZ").rect(6.2, B - 3).extrude(P["splice_len"])
    k = k.union(cq.Workplane("YZ").rect(B - 3, 6.2).extrude(P["splice_len"]))
    return k


def icebox_parts():
    """Reference model of the IceBox 1.3 (25" deep) sitting with its slotted
    back panel against the cage's x=0 end.  Names start with icebox_ so the
    viewer can ghost/toggle it.  Slot pattern is approximated from photos."""
    W, H, D = P["icebox_W"], P["icebox_H"], P["icebox_D"]
    x0 = -D - P["icebox_gap"]; y0 = P["icebox_y"]
    parts = []
    cube = corner_cube()
    for i, x in enumerate((x0, x0 + D - C)):
        for j, y in enumerate((y0, y0 + W - C)):
            for k, z in enumerate((0, H - C)):
                parts.append((f"icebox_cube_{i}{j}{k}", cube.translate((x, y, z))))
    for y in (y0, y0 + W - B):
        for z in (0, H - B):
            parts.append((f"icebox_bar_x_{int(y)}_{int(z)}", bar(D - 2 * C, "x").translate((x0 + C, y + B / 2, z + B / 2))))
    for x in (x0, x0 + D - B):
        for z in (0, H - B):
            parts.append((f"icebox_bar_y_{int(x)}_{int(z)}", bar(W - 2 * C, "y").translate((x + B / 2, y0 + C, z + B / 2))))
        for y in (y0, y0 + W - B):
            parts.append((f"icebox_bar_z_{int(x)}_{int(y)}", bar(H - 2 * C, "z").translate((x + B / 2, y + B / 2, C))))
    # panels: top deck, floor, two sides, slotted back
    parts.append(("icebox_panel_top", box(D - 2 * B, W - 2 * B, T, (x0 + B, y0 + B, H - B - T))))
    parts.append(("icebox_panel_floor", box(D - 2 * B, W - 2 * B, T, (x0 + B, y0 + B, B))))
    parts.append(("icebox_panel_side_out", box(D - 2 * B, T, H - 2 * B, (x0 + B, y0 + B, B))))
    parts.append(("icebox_panel_side_in", box(D - 2 * B, T, H - 2 * B, (x0 + B, y0 + W - B - T, B))))
    back = box(T, W - 2 * B, H - 2 * B, (x0 + D - B - T, y0 + B, B))
    slot_w, slot_h, pitch_y, pitch_z = 72.0, 22.0, 92.0, 46.0
    rows = int((H - 2 * B - 120) / pitch_z)
    for r in range(rows):
        z = B + 60 + r * pitch_z
        off = (pitch_y / 2) if r % 2 else 0
        y = y0 + B + 40 + off
        while y + slot_w < y0 + W - B - 30:
            cutter = (cq.Workplane("YZ").center(y + slot_w / 2, z + slot_h / 2)
                      .slot2D(slot_w, slot_h).extrude(T + 2).translate((x0 + D - B - T - 1, 0, 0)))
            back = back.cut(cutter)
            y += pitch_y
    parts.append(("icebox_panel_back_slotted", back))
    # fridge tray: a shallow open box on the floor, pulled 60 mm proud of the front
    tray = box(D - 2 * B + 60, 381, 40, (x0 + B - 60, y0 + (W - 381) / 2, B + T))
    tray = tray.cut(box(D - 2 * B + 60 - 8, 381 - 8, 40, (x0 + B - 56, y0 + (W - 381) / 2 + 4, B + T + 4)))
    parts.append(("icebox_tray", tray))
    return parts


def corner_cube():
    """Printed 3-way corner, visual twin of the Goose Gear black corner cube.
    Three bores take the bar ends' 1/4-20 end-tap screws."""
    cube = box(C, C, C).edges().fillet(2.0)
    for axis in ("x", "y", "z"):
        hole = cq.Workplane("XY").circle(3.4).extrude(C + 2).translate((0, 0, -1))
        if axis == "x":
            hole = hole.rotate((0, 0, 0), (0, 1, 0), 90)
        elif axis == "y":
            hole = hole.rotate((0, 0, 0), (1, 0, 0), -90)
        cube = cube.cut(hole.translate((C / 2, C / 2, C / 2)))
    return cube


def card_guide(height: float):
    """Printed U-channel at each end wall; the card edge drops into it.
    Bolts to the vertical bar's inner slot with a T-nut."""
    gw = P["card_t"] + 2 * P["card_clear"]
    g = box(P["guide_d"], P["guide_w"], height)
    g = g.cut(box(P["guide_d"] - P["guide_wall"] + 1, gw, height + 1,
                  (-1, (P["guide_w"] - gw) / 2, -0.5)))
    flare = (cq.Workplane("XZ").polyline([(0, height - 8), (P["guide_d"] - P["guide_wall"], height - 8),
                                           (P["guide_d"] - P["guide_wall"] + 3, height + 1), (-1, height + 1)])
             .close().extrude(-P["guide_w"]))
    return g.cut(flare)


def ledge(length: float):
    return box(length, P["ledge_w"], P["ledge_t"])


def battery_tray(c: Comp, n: int = 2):
    """Printed floor tray with n side-by-side bays, 20 mm lips, strap slots.
    Wider than the P1S bed: print as two halves split at the centre wall."""
    lip, wall = 20.0, 4.0
    W = n * c.d + (n + 1) * wall
    t = box(c.w + 2 * wall, W, lip + 4)
    for i in range(n):
        t = t.cut(box(c.w, c.d, lip + 5, (wall, wall + i * (c.d + wall), 4)))
    for x in (c.w * 0.25, c.w * 0.75):
        t = t.cut(box(30, W + 2, 6, (x - 15, -1, 6)))
    return t


def multiplus_cradles(c: Comp):
    """Four printed corner cradles that locate the MultiPlus lying flat.
    Yields (name, shape) so each prints separately."""
    for (sx, sy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
        k = box(40, 40, 24).cut(box(32, 32, 25, (8 if sx == 0 else 0, 8 if sy == 0 else 0, 4)))
        yield f"print_cradle_multiplus_{sx}{sy}", k.translate((sx * (c.w - 32), sy * (c.d - 32), 0))


def mppt_bracket(c: Comp):
    """Printed stand holding the MPPT vertical at the far end; keyholes on
    Victron's 176 x 71.5 mm pattern."""
    base = box(c.w + 16, 30, 6)
    back = box(c.w + 16, 6, c.h + 10, (0, 24, 0))
    br = base.union(back)
    for dx in (-88, 88):
        for dz in (c.h / 2 - 35.75 + 8, c.h / 2 + 35.75 + 8):
            br = br.cut(cq.Workplane("XZ").center(c.w / 2 + 8 + dx, dz).circle(2.6)
                        .extrude(-40).translate((0, 20, 0)))
    return br


def socket_panel():
    """Printed insert in the inboard panel carrying the panel-mount sockets."""
    xs = [x for x, _ in SOCKETS]
    w = max(xs) - min(xs) + 60
    sp = box(w, P["socket_panel_t"], P["socket_panel_h"],
             (min(xs) - 30, out_W - B - T - P["socket_panel_t"] + T,
              floor_top + P["socket_z"] - P["socket_panel_h"] / 2))
    for x, dia in SOCKETS:
        sp = sp.cut(cq.Workplane("XZ").center(x, floor_top + P["socket_z"]).circle(dia / 2).extrude(-out_W))
    return sp


def lid_handle():
    return box(60, 12, 18).edges("|Y").fillet(5)


# ----------------------------------------------------------------------------
# Assembly
# ----------------------------------------------------------------------------
GRAY, ORANGE, BLACK, PANEL = (0.72, 0.74, 0.76), (0.85, 0.33, 0.12), (0.12, 0.12, 0.12), (0.2, 0.2, 0.2)
BLUE, GOLD, BATT = (0.15, 0.39, 0.92), (0.79, 0.64, 0.15), (0.12, 0.5, 0.95)


def add(a, shape, name, rgb, alpha=1.0):
    a.add(shape, name=name, color=cq.Color(*rgb, alpha))


def build() -> cq.Assembly:
    a = cq.Assembly(name="cage")

    # --- frame: 8 corner cubes + 12 bars ------------------------------------
    cube = corner_cube()
    for i, x in enumerate((0, out_L - C)):
        for j, y in enumerate((0, out_W - C)):
            for k, z in enumerate((0, out_H - C)):
                add(a, cube.translate((x, y, z)), f"print_cube_{i}{j}{k}", BLACK)
    runs = allocate_rails()
    long_pos = [(y, z) for y in (0, out_W - B) for z in (0, out_H - B)]
    for i, (y, z) in enumerate(long_pos):
        x = C
        for j, (kind, ln) in enumerate(runs[f"l{i}"]):
            if kind == "bar":
                add(a, bar(ln, "x").translate((x, y + B / 2, z + B / 2)), f"bar_long_{i}_{j}", GRAY)
            else:
                add(a, printed_rail(ln).translate((x, y + B / 2, z + B / 2)), f"print_rail_{i}_{j}", ORANGE)
            if j > 0:  # splice straddling the joint
                add(a, splice().translate((x - P["splice_len"] / 2, y + B / 2, z + B / 2)), f"print_splice_{i}_{j}", ORANGE)
            x += ln
    for i, x in enumerate((0, out_L - B)):
        for k, z in enumerate((0, out_H - B)):
            kind = runs[f"w{i * 2 + k}"][0][0]
            shp = bar(out_W - 2 * C, "y").translate((x + B / 2, C, z + B / 2))
            add(a, shp, f"{'bar' if kind == 'bar' else 'print_rail'}_w_{i}{k}", GRAY if kind == "bar" else ORANGE)
        for k, y in enumerate((0, out_W - B)):
            kind = runs[f"h{i * 2 + k}"][0][0]
            shp = bar(out_H - 2 * C, "z").translate((x + B / 2, y + B / 2, C))
            add(a, shp, f"{'bar' if kind == 'bar' else 'print_rail'}_h_{i}{k}", GRAY if kind == "bar" else ORANGE)

    # --- IceBox 1.3 reference -------------------------------------------------
    if P["show_icebox"]:
        for nm, shp in icebox_parts():
            col = BLACK if "cube" in nm else GRAY if "bar" in nm else (0.35, 0.35, 0.35)
            add(a, shp, nm, col)

    # --- panels (phenolic ply / HDPE, cut to size; not printed) --------------
    add(a, box(in_L + 2 * T, in_W + 2 * T, T, (B, B, B)), "panel_floor", PANEL)
    add(a, box(in_L + 2 * T, T, in_H + 2 * T, (B, B, B)), "panel_side_outboard", PANEL)
    sp = socket_panel()
    bb = sp.val().BoundingBox()
    inboard = box(in_L + 2 * T, T, in_H + 2 * T, (B, out_W - B - T, B))
    inboard = inboard.cut(box(bb.xlen, T + 2, bb.zlen, (bb.xmin, out_W - B - T - 1, bb.zmin)))
    add(a, inboard, "panel_side_inboard", PANEL)
    add(a, box(T, in_W, in_H + 2 * T, (B, B + T, B)), "panel_end_icebox", PANEL)
    far = box(T, in_W, in_H + 2 * T, (out_L - B - T, B + T, B))
    ca = COMPONENTS["anderson"]
    for (y, z) in ANDERSONS:
        far = far.cut(box(T + 2, ca.h, ca.d, (out_L - B - T - 1, B + T + y - ca.h / 2, floor_top + z - ca.d / 2)))
    add(a, far, "panel_end_far", PANEL)
    add(a, box(in_L + 2 * T, in_W + 2 * T, T, (B, B, out_H - B - T)), "lid_panel", PANEL)
    for x in (out_L * 0.3, out_L * 0.7):
        add(a, lid_handle().translate((x - 30, out_W / 2 - 6, out_H - B)), f"lid_handle_{int(x)}", BLACK)
    add(a, sp, "print_socket_panel", ORANGE)

    # --- bulkhead between battery zone and card zone --------------------------
    add(a, box(P["bulk_t"], in_W, in_H - 2, (B + T + P["bulk_x"], B + T, floor_top)), "panel_bulkhead", PANEL)

    # --- printed internals ---------------------------------------------------
    guide_z0 = card_z - 25                 # start a little below the card seat
    guide_h = floor_top + in_H - 2 - guide_z0
    for i, x in enumerate((B + T + zone_x0, out_L - B - T - P["guide_d"])):
        for j, y in enumerate((B + T + 20, out_W - B - T - 20 - P["guide_w"])):
            g = card_guide(guide_h)
            if i == 1:
                g = g.mirror("YZ").translate((P["guide_d"], 0, 0))
            add(a, g.translate((x, y, guide_z0)), f"print_guide_{i}{j}", ORANGE)
    for i, y in enumerate((B + T, out_W - B - T - P["ledge_w"])):
        for j, x in enumerate((B + T + zone_x0 + 60, out_L - B - T - 60 - 160)):
            add(a, ledge(160).translate((x, y, card_z - P["ledge_t"])), f"print_ledge_{i}{j}", ORANGE)

    # --- lower level ---------------------------------------------------------
    tray_done = False
    for pl in FLOOR_LAYOUT:
        c = COMPONENTS[pl["comp"]]
        x = B + T + pl["x"]
        y = B + T + (in_W - c.d) / 2 if pl["y"] is None else B + T + pl["y"]
        if pl["comp"] == "battery":
            if not tray_done:
                add(a, battery_tray(c).translate((x - 4, y - 4, floor_top)), "print_tray_battery", ORANGE)
                tray_done = True
            z = floor_top + 4
        elif pl["comp"] == "multiplus":
            for nm, k in multiplus_cradles(c):
                add(a, k.translate((x, y, floor_top)), nm, ORANGE)
            z = floor_top + 4
        elif pl["comp"] == "mppt":
            add(a, mppt_bracket(c).translate((x - 8, y - 24, floor_top)), "print_bracket_mppt", ORANGE)
            z = floor_top + 8
        else:
            z = floor_top
        add(a, box(c.w, c.d, c.h, (x, y, z)).edges("|Z").fillet(4), pl["tag"], BATT if c.name == "battery" else BLUE)

    # --- card + card-mounted components -------------------------------------
    add(a, box(card_L, card_W, P["card_t"], (card_x0, card_y0, card_z)), "card_plate", (0.18, 0.18, 0.18))
    for pl in CARD_LAYOUT:
        c = COMPONENTS[pl["comp"]]
        x, y = card_x0 + pl["x"], card_y0 + pl["y"]
        z = card_z + P["card_t"] if pl["side"] == "top" else card_z - c.h
        col = (BLUE if c.name.startswith("victron") else (0.08, 0.08, 0.08) if c.name.startswith("garmin")
               else GOLD if c.name.startswith("power") else (0.85, 0.85, 0.85))
        add(a, box(c.w, c.d, c.h, (x, y, z)).edges("|Z").fillet(3), f"{c.name}__card", col)

    for x, dia in SOCKETS:
        s = (cq.Workplane("XZ").center(x, floor_top + P["socket_z"]).circle(dia / 2 + 3)
             .extrude(40).translate((0, out_W - B - T, 0)))
        add(a, s, f"socket_{x}", (0.3, 0.3, 0.3))
    c = COMPONENTS["anderson"]
    for i, (y, z) in enumerate(ANDERSONS):
        body = box(50, c.h, c.d, (out_L - B - T - 40, B + T + y - c.h / 2, floor_top + z - c.d / 2))
        add(a, body, f"socket_anderson_{i}", (0.3, 0.3, 0.3))
    return a


# ----------------------------------------------------------------------------
# Export + report
# ----------------------------------------------------------------------------
def glb_to_json(glb_path: str, json_path: str):
    """Rewrite a GLB as JSON glTF with the binary chunk embedded as base64.
    The web viewer can fetch a .json next to the page where it cannot fetch a
    .glb (artifact hosting serves a fixed list of types)."""
    d = open(glb_path, "rb").read()
    assert d[:4] == b"glTF"
    off, js, binary = 12, None, None
    while off < len(d):
        ln, typ = struct.unpack("<II", d[off:off + 8])
        chunk = d[off + 8:off + 8 + ln]
        off += 8 + ln
        if typ == 0x4E4F534A:
            js = json.loads(chunk)
        elif typ == 0x004E4942:
            binary = chunk
    js["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(binary).decode()
    with open(json_path, "w") as f:
        json.dump(js, f)


def export(a: cq.Assembly):
    os.makedirs(os.path.join(OUT, "views"), exist_ok=True)
    os.makedirs(VIEWER, exist_ok=True)
    os.makedirs(STL, exist_ok=True)
    glb = os.path.join(OUT, "cage.glb")
    a.export(glb)
    glb_to_json(glb, os.path.join(VIEWER, "cage.json"))
    print("== Printed parts (P1P/P1S bed 256 x 256 x 256) ==")
    for child in a.children:
        if child.name.startswith("print_"):
            cq.exporters.export(child.obj, os.path.join(STL, f"{child.name}.stl"))
            bb = child.obj.val().BoundingBox()
            dims = sorted((bb.xlen, bb.ylen, bb.zlen), reverse=True)
            flag = "" if dims[0] <= 256 and dims[1] <= 256 else "  <-- exceeds bed, split or rotate"
            print(f"  {child.name:28s} {dims[0]:6.1f} x {dims[1]:6.1f} x {dims[2]:6.1f}{flag}")
    comp = cq.Compound.makeCompound([ch.obj.val() for ch in a.children
                                     if not ch.name.startswith(("lid", "panel", "icebox"))])
    for name, d in {"iso": (1, -1.2, 0.9), "top": (0, 0, 1), "front": (0, -1, 0), "end": (1, 0, 0)}.items():
        svg = os.path.join(OUT, "views", f"{name}.svg")
        cq.exporters.export(comp, svg, opt={"width": 1600, "height": 700, "projectionDir": d,
                                             "showHidden": False, "strokeWidth": 0.5})
        subprocess.run(["qlmanage", "-t", "-s", "1600", "-o", os.path.join(OUT, "views"), svg],
                       capture_output=True)


def report():
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.2f} in)"
    print("== Box ==")
    print(f"outer L x W x H : {mm(out_L)} x {mm(out_W)} x {mm(out_H)}")
    print(f"inner L x W x H : {mm(in_L)} x {mm(in_W)} x {mm(in_H)}")
    print(f"card            : {mm(card_L)} x {mm(card_W)} x {P['card_t']:.0f} mm, underside {P['card_z']:.0f} mm above floor")
    print(f"headroom on card: {in_H - P['card_z'] - P['card_t']:.0f} mm")
    print(f"== Rails: {P['kit_bars']} kit bars @ {mm(P['bar_stock'])} (stock length UNVERIFIED) ==")
    print(f"  need 4 x long {mm(out_L - 2 * C)}, 4 x width {mm(out_W - 2 * C)}, 4 x height {mm(out_H - 2 * C)}")
    runs = allocate_rails()
    tot_bar = sum(ln for r in runs.values() for k, ln in r if k == "bar")
    tot_prt = sum(ln for r in runs.values() for k, ln in r if k == "print")
    for name, r in runs.items():
        print(f"  {name:3s} " + " + ".join(f"{k} {ln:.0f}" for k, ln in r))
    print(f"  aluminium used {mm(tot_bar)}, printed rail {mm(tot_prt)} in "
          f"{sum(1 for r in runs.values() for k, _ in r if k == 'print')} segments")
    print(f"== IceBox 1.3 next to the cage: cage end {mm(out_W)} wide x {mm(out_H)} tall against a "
          f"{mm(P['icebox_W'])} x {mm(P['icebox_H'])} slotted panel; cage top is {mm(P['icebox_H'] - out_H)} below the IceBox deck ==")
    print("== Panels (6 mm) ==")
    print(f"  floor + lid  {mm(in_L + 2 * T)} x {mm(in_W + 2 * T)}")
    print(f"  2 sides      {mm(in_L + 2 * T)} x {mm(in_H + 2 * T)}")
    print(f"  2 ends       {mm(in_W)} x {mm(in_H + 2 * T)}")
    print("== Fit checks ==")
    for pl in FLOOR_LAYOUT:
        c = COMPONENTS[pl["comp"]]
        probs = []
        if pl["x"] + c.w > in_L: probs.append("X overflow")
        if c.d > in_W: probs.append("too wide")
        under_card = pl["x"] + c.w > P["bulk_x"]
        if under_card and c.h + 8 > P["card_z"]: probs.append("hits card")
        if not under_card and c.h + 8 > in_H: probs.append("hits lid")
        if pl["y"] is not None and pl["y"] + c.d > in_W: probs.append("Y overflow")
        print(f"  floor {pl['tag']:20s} {c.w:>4.0f}x{c.d:>4.0f}x{c.h:>4.0f} @({pl['x']:.0f},{pl['y'] if pl['y'] is not None else 'ctr'}) {' '.join(probs) or 'ok'}")
    batt = COMPONENTS["battery"]
    print(f"  battery top {batt.h + 4:.0f} mm, lid underside {in_H:.0f} mm -> {in_H - batt.h - 4:.0f} mm for terminals/cables")
    for pl in CARD_LAYOUT:
        c = COMPONENTS[pl["comp"]]
        probs = []
        if pl["x"] + c.w > card_L: probs.append("X overflow")
        if pl["y"] + c.d > card_W: probs.append("Y overflow")
        if pl["side"] == "top":
            head = in_H - P["card_z"] - P["card_t"]
        else:  # under the card: MultiPlus occupies the first 406 mm of the zone
            mp = COMPONENTS["multiplus"]
            mp_end = next(f["x"] for f in FLOOR_LAYOUT if f["comp"] == "multiplus") + mp.w - zone_x0
            head = P["card_z"] - (mp.h + 4 if pl["x"] < mp_end else 8)
            # MPPT standing in the same zone: check Y overlap
            mp2 = COMPONENTS["mppt"]; f2 = next(f for f in FLOOR_LAYOUT if f["comp"] == "mppt")
            if (pl["x"] + zone_x0 < f2["x"] + mp2.w and pl["x"] + zone_x0 + c.w > f2["x"]
                    and pl["y"] < f2["y"] + mp2.d and pl["y"] + c.d > f2["y"]):
                probs.append("over the MPPT")
        if c.h > head: probs.append(f"too tall by {c.h - head:.0f}")
        print(f"  card  {pl['side']:6s} {c.name:20s} {c.w:>4.0f}x{c.d:>4.0f}x{c.h:>4.0f} @({pl['x']},{pl['y']}) {' '.join(probs) or 'ok'}")


if __name__ == "__main__":
    asm = build()
    report()
    export(asm)
    print("wrote", os.path.abspath(os.path.join(VIEWER, "cage.json")))
