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
    "icebox": dict(frame_source="icebox", frame_W=487.4, frame_H=558.8, frame_D=635.0,
                   batt_layout="stack2x2", dist_forward=True, inverter="multiplus"),
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
    icebox_W=487.4, icebox_H=558.8, icebox_D=635.0,
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
    # inverter candidates, as mounted on their side on the lower card (w along Y, h up, d off the card)
    "multiplus":    Comp("victron_multiplus", 360, 100, 240, "MultiPlus 12/800/35-16 120V on its side (6.4 kg)"),
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
N_BATT = 4
post_h = in_H                                          # floor panel top to the underside of the top rails


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
    add(a, box(out_D, out_W, T, (0, 0, B)), "panel_floor", PANEL)
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
    for j, y in enumerate((row_W * 0.3, row_W * 0.7)):
        add(a, bar(joist_len, "x").translate((C, y_in0 + y, B / 2)), f"bar_joist_{j}", GRAY)

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
    glb = os.path.join(OUT, "cage.glb"); a.export(glb); glb_to_json(glb, os.path.join(VIEWER, f"cage-{VARIANT}.json"))
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
