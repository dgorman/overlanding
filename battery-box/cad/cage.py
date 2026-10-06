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
    # v7: four SuperPack 60Ah in two touching stacks at the IceBox end; inverter/charger and
    # distribution cards lengthwise in the front part of the depth.  Width from the batteries.
    "v7": dict(frame_source="icebox", frame_W=487.4, frame_H=558.8, frame_D=762.0,
               batt_layout="v7", dist_forward=False, inverter="multiplus_1200_up",
               card_plane="v7", column=["battery", "battery"], arrange="2x2", col_on_plate=True,
               narrow=True, tray_for="battery", align="right", height="icebox", depth="fit", card_len=280.0,
               card_style="solid"),
    # v8: v7's battery bay, then THREE cards ACROSS the box (facing like v4): inverter, charge/brains,
    # distribution.  The 12/1200 only costs its 100 mm thickness in depth.
    "v8": dict(frame_source="icebox", frame_W=487.4, frame_H=558.8, frame_D=762.0,
               batt_layout="v8", dist_forward=False, inverter="multiplus_1200_up",
               card_plane="v8", column=["battery", "battery"], arrange="2x2", col_on_plate=True,
               narrow=True, tray_for="battery", align="right", height="icebox", depth="fit8",
               card_style="solid"),
    # v9: v8 with a fixed BUS DECK on top of the battery rack (bus bars, breakers, shunt, connector
    # receptacles) so each of the two remaining cards unplugs and lifts out on its own.
    "v9": dict(frame_source="icebox", frame_W=487.4, frame_H=558.8, frame_D=762.0,
               batt_layout="v9", dist_forward=False, inverter="multiplus_1200_up", leg=12.0,
               card_plane="v9", column=["battery", "battery"], arrange="2x2", col_on_plate=True,
               narrow=True, tray_for="battery", align="right", height="icebox", depth="fit9",
               card_style="solid", post_standoff=18.0),
    "v10": dict(frame_source="icebox", frame_W=487.4, frame_H=558.8, frame_D=762.0,
               batt_layout="v9", dist_forward=False, inverter="multiplus_1200_up", leg=12.0,
               card_plane="v9", column=["battery", "battery"], arrange="2x2", col_on_plate=True,
               narrow=True, tray_for="battery", align="right", height="icebox", depth="fit10",
               card_style="solid", post_standoff=18.0, deck="full"),
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
    post_standoff=0.0,   # posts moved inboard off the rail by this much (v9: 18 -> 249 mm wide cards, 2 tiles each)
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
P.setdefault("deck", "cards")      # "full": v10, the bus deck runs the length of the box and carries the charge-card units
P.setdefault("col_on_plate", False)   # True: no floor panel under the battery column; trays sit on the Goose Gear plate (z=0)
P.setdefault("narrow", False)
P.setdefault("tray_for", None)        # size the battery trays for this battery key (None = the column's own)
P.setdefault("pedal_gap", 0.0)        # extra width to keep free beside the column (0 = tight)
P.setdefault("align", "left")         # which IceBox face the (narrower) cage is flush with, as seen in the viewer's Front view
P.setdefault("height", "icebox")      # "fit": frame height = battery stack + lid clearance (v7)
P.setdefault("depth", "icebox")       # "fit": frame depth = battery bay + cross-bar + card_len (v7): the port wall comes in to the gear
P.setdefault("card_len", 280.0)
P.setdefault("card_style", "sheet")   # "lattice": printed 4-tile ribbed cards instead of 6 mm sheet
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
    "multiplus_1200_up": Comp("victron_multiplus", 249, 101, 375, "MultiPlus 12/1200/50-16 120V upright, terminals down (8.2 kg); body 374.6 tall, the datasheet's 406 includes the bracket"),
    "cerbo_up":  Comp("victron_cerbo", 78, 48, 154, "Cerbo GX turned 90 deg"),
    "multiplus_ii": Comp("victron_multiplus", 578, 148, 277, "MultiPlus-II 12/3000/120-50 120V on its side (19 kg) - 578 long"),
    "multiplus_4k": Comp("victron_multiplus", 631, 164, 277, "MultiPlus-II 12/4k/160-50 120V on its side (22 kg) - 631 long"),
    "mppt":      Comp("victron_mppt", 186, 70, 130, "SmartSolar MPPT 100/30, upright, terminals down (1.3 kg)"),
    "orion":     Comp("victron_orion", 123, 40, 137, "Orion XS 12/12-50A, upright, terminals down (0.33 kg)"),
    "cerbo":     Comp("victron_cerbo", 154, 48, 78, "Cerbo GX"),
    "garmin":    Comp("garmin_powerswitch", 125, 32, 75, "Garmin PowerSwitch"),
    "garmin_up": Comp("garmin_powerswitch", 75, 32, 125, "Garmin PowerSwitch turned 90 deg"),
    # v10: units lying flat on the full-length deck (w along Y, d along X, h up)
    "mppt_flat":  Comp("victron_mppt", 186, 130, 70, "MPPT 100/30 flat on the deck, fins up (Victron asks for vertical mounting)"),
    "orion_flat": Comp("victron_orion", 123, 137, 40, "Orion XS flat on the deck"),
    "cerbo_flat": Comp("victron_cerbo", 154, 78, 48, "Cerbo GX flat on the deck"),
    "garmin_flat": Comp("garmin_powerswitch", 75, 125, 32, "Garmin PowerSwitch flat on the deck"),
    "shunt_y":    Comp("power_shunt", 120, 54, 46, "SmartShunt on the deck, long axis across"),
    "busbar_px":  Comp("power_busbar_pos", 35, 155, 32, "5-stud covered bus bar (+), along the depth"),
    "busbar_nx":  Comp("power_busbar_neg", 35, 155, 32, "5-stud covered bus bar (-), along the depth"),
    "shunt":     Comp("power_shunt", 120, 46, 54, "SmartShunt 500A"),
    "busbar_p":  Comp("power_busbar_pos", 155, 35, 32, "5-stud covered bus bar (+)"),
    "busbar_n":  Comp("power_busbar_neg", 155, 35, 32, "5-stud covered bus bar (-)"),
    "breaker_a": Comp("power_breaker_a", 48, 43, 74, "battery breaker, surface mount"),
    "breaker_b": Comp("power_breaker_b", 48, 43, 74, "battery breaker, surface mount"),
    "anderson":  Comp("socket_anderson", 48, 10, 36, "Anderson SB50 panel mount, solar in (verify hole 48 x 36)"),
    "sb175":     Comp("socket_sb175", 79, 56, 26, "Anderson SB175 housing (Anderson STEP 55.6 x 79.4 x 25.5), 4 AWG contacts, inverter DC; mates along its 79 mm axis, laid across the deck"),
    "sb50":      Comp("socket_sb50", 48, 37, 16, "Anderson SB50 housing (Anderson STEP 36.5 x 48 x 16), 6-12 AWG contacts; mates along its 48 mm axis, laid across the deck"),
    "sb175_x":   Comp("socket_sb175", 56, 79, 26, "Anderson SB175 on the deck, mating axis along the depth (+X)"),
    "sb50_x":    Comp("socket_sb50", 37, 48, 16, "Anderson SB50 on the deck, mating axis along the depth (+X)"),
    "sb175_v":   Comp("socket_sb175", 56, 26, 79, "Anderson SB175 standing on a card's rear face, mating face up"),
    "sb50_v":    Comp("socket_sb50", 37, 16, 48, "Anderson SB50 standing on a card face, mating face up"),
    "shunt_x":   Comp("power_shunt", 54, 120, 46, "SmartShunt turned 90 deg on the deck"),
    "pp45_v":    Comp("socket_pp45", 32, 16, 25, "Anderson Powerpole PP45 block, 8 poles = 4 circuits, 10 AWG contacts; Garmin outputs to the front-panel sockets; mating face up"),
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
V8 = dict(bay_gap=10.0, inv_gap=8.0, charge_gap=8.0, dist_gap=8.0, front=8.0, charge_depth=70.0, dist_depth=46.0)
# v10 full-length deck: the inverter card and its posts pass through a slot in the deck; slot_back is the gap from
# the card's rear face to the middle plate's end (the post is 9.6 behind the card + 2), slot_front from the card's
# front face to the front plate (post 14.4 ahead + 2); front_plate is the plate ahead of the card (MPPT 130 + Cerbo 78 + gaps)
V10 = dict(slot_back=12.0, slot_front=17.0, front_plate=220.0)
if P["narrow"] and P["card_plane"] in ("v7", "v8", "v9"):
    _b = COMPONENTS["battery"]
    V7 = dict(wall=(6.0 if P["card_plane"] == "v9" else 4.0), leg=P.get("leg", 9.0), end_gap=15.0, bay_slack=2.0, bar_gap=5.0,
              lip=(30.0 if P["card_plane"] == "v9" else 20.0))   # v9 rack: 6 mm walls, 30 mm lips, 12 mm split legs
    V7["tray_w"] = _b.w + 2 * V7["wall"]                          # 146
    V7["bay_W"] = 2 * V7["tray_w"] + V7["bay_slack"]              # two touching stacks
    V7["bay_D"] = V7["end_gap"] + _b.d + 2 * V7["wall"] + V7["leg"]  # back gap (leg inside) + tray + front leg
    out_W = round(B + V7["bay_W"] + B, 1)
    if P["height"] == "fit":
        _stack = 4 + 2 * _b.h + 14.0 + 10.0 + 14.0          # tray floor, two batteries, lug room, shelf, lug room
        out_H = round(_stack + 6.0, 1)                       # 6 mm under the lid
        in_H = out_H - 2 * B - T
    if P["depth"] == "fit":
        _posts = 2 * (P["post_d"] - P["slot_depth"]) + 2 * P["card_clear"]
        in_D = round(V7["bay_D"] + V7["bar_gap"] + B + 2 + _posts + P["card_len"] + 1, 1)
        out_D = in_D + 2 * B
    if P["depth"] == "fit9":
        _inv = COMPONENTS[P["inverter"]]
        V8["bay_gap"] = 70.0     # wiring room between the deck/battery lugs and the inverter card (pigtails up to the deck)
        V8["front"] = 45.0       # grace between the charge card's parts and the front-panel inlets/sockets
        V8["inv_gap"] = 26.0     # the charge card's rear-face SB50s (16 deep) + clearance
        V8["x_inv"] = V7["bay_D"] + V8["bay_gap"]
        V8["x_charge"] = V8["x_inv"] + P["card_t"] + 10.0 + _inv.d + V8["inv_gap"]
        in_D = round(V8["x_charge"] + P["card_t"] + V8["charge_depth"] + V8["charge_gap"] + V8["front"], 1)
        out_D = in_D + 2 * B
    if P["depth"] == "fit10":
        # v10: no charge card.  The deck continues past the inverter card (through a slot) as a front plate that
        # carries the MPPT, Cerbo and Garmin; the Orion sits on the deck's middle plate behind the card.
        _inv = COMPONENTS[P["inverter"]]
        V8["bay_gap"] = 70.0
        V8["inv_gap"] = 26.0
        V8["front"] = 0.0
        V8["x_inv"] = V7["bay_D"] + V8["bay_gap"]
        V8["x_charge"] = None
        in_D = round(V8["x_inv"] + P["card_t"] + V10["slot_front"] + V10["front_plate"] + 2, 1)
        out_D = in_D + 2 * B
    if P["depth"] == "fit8":
        _inv = COMPONENTS[P["inverter"]]
        V8["x_inv"] = V7["bay_D"] + V8["bay_gap"]                                 # inverter card rear face (from x_in0)
        V8["x_charge"] = V8["x_inv"] + P["card_t"] + 10.0 + _inv.d + V8["inv_gap"]
        V8["x_dist"] = V8["x_charge"] + P["card_t"] + V8["charge_depth"] + V8["charge_gap"]
        in_D = round(V8["x_dist"] + P["card_t"] + V8["dist_depth"] + V8["dist_gap"] + V8["front"], 1)
        out_D = in_D + 2 * B
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
if P["card_plane"] == "v7":
    ANDERSONS = []
    SOCKETS = [(20, 29), (60, 29), (100, 29), (140, 22)]              # over the outboard cable space
if P["card_plane"] in ("v8", "v9"):
    ANDERSONS = []
    SOCKETS = [(40, 29), (85, 29), (130, 29), (175, 22), (215, 22)]   # lower band of the front panel
    P["socket_z"] = 80.0
N_BATT = 4
post_h = in_H                                          # floor panel top to the underside of the top rails


def box(w, d, h, at=(0, 0, 0)):
    return cq.Workplane("XY").box(w, d, h, centered=False).translate(at)


STEP_DIR = os.path.join(HERE, "step")
STEP_FILES = {   # component key -> Victron STEP file (downloaded into cad/step/, see components.md)
    "multiplus_ii": "MultiPlus-II-12-3000-120V.step",
    "multiplus":    "MultiPlus-12-800-120V.step",
    "multiplus_1200": "MultiPlus-12-1200-120V.step",
    "multiplus_1200_up": "MultiPlus-12-1200-120V.step",
    "cerbo_up":     "Cerbo-GX.step",
    "smart200":     "Lithium-Smart-12.8V-160Ah-200Ah.step",
    "smart100":     "Lithium-Smart-12.8V-100Ah.step",
    "battery":      "Lithium-SuperPack-12.8V-60Ah.step",
    "mppt":         "SmartSolar-MPPT-100-30.step",
    "orion":        "Orion-XS-12-12-50A.step",
    "cerbo":        "Cerbo-GX.step",
    "shunt":        "SmartShunt-500A.step",
    "bms":          "VE.Bus-BMS-V2.step",
    "sb175":        "anderson_sb175_housing.stp",
    "sb50":         "anderson_sb50_housing.stp",
    "sb175_x":      "anderson_sb175_housing.stp",
    "sb50_x":       "anderson_sb50_housing.stp",
    "sb175_v":      "anderson_sb175_housing.stp",
    "sb50_v":       "anderson_sb50_housing.stp",
    "shunt_x":      "SmartShunt-500A.step",
    "mppt_flat":    "SmartSolar-MPPT-100-30.step",
    "orion_flat":   "Orion-XS-12-12-50A.step",
    "cerbo_flat":   "Cerbo-GX.step",
    "shunt_y":      "SmartShunt-500A.step",
}
MATED = {"sb175": 133.4, "sb50": 81.3, "sb175_x": 133.4, "sb50_x": 81.3, "sb175_v": 133.4, "sb50_v": 81.3, "pp45_v": 41.0}   # Anderson mated-pair lengths
HOUSING = {"sb175": 79.4, "sb50": 48.0, "pp45": 24.6}   # housing length along the mating axis
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
            if foot_dir == "y":   # plate toward -Y over the depth rail, from the rail's outer face to the slot wall
                S = P["post_standoff"]
                f = box(P["post_w"], B + S + P["post_d"] - P["slot_depth"], P["foot_t"], (0, -B - S, z0))
                if z0 == 0 and P["card_plane"] in ("v7", "v8", "v9"):
                    # the floor panel stops at the rail: step the foot down T so it sits on the rail top
                    f = f.union(box(P["post_w"], B - 0.5, T, (0, -B - S, -T)))
                hx, hy = P["post_w"] / 2, (foot_hole if foot_hole is not None else -S - B / 2)
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
    if P["card_plane"] not in ("v7", "v8", "v9"):
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
    if not P["col_on_plate"] and P["card_plane"] not in ("v7", "v8", "v9"):
        for j, y in enumerate(joist_ys):
            add(a, bar(joist_len, "x").translate((C, y_in0 + y, B / 2)), f"bar_joist_{j}", GRAY)

    if P["card_plane"] == "v9":
        build_v9(a)
        if P["show_icebox"]:
            for nm, shp in icebox_parts():
                col = BLACK if "cube" in nm else GRAY if "bar" in nm else (0.35, 0.35, 0.35)
                add(a, shp, nm, col)
        return a
    if P["card_plane"] == "v8":
        build_v8(a)
        if P["show_icebox"]:
            for nm, shp in icebox_parts():
                col = BLACK if "cube" in nm else GRAY if "bar" in nm else (0.35, 0.35, 0.35)
                add(a, shp, nm, col)
        return a
    if P["card_plane"] == "v7":
        build_v7(a)
        if P["show_icebox"]:
            for nm, shp in icebox_parts():
                col = BLACK if "cube" in nm else GRAY if "bar" in nm else (0.35, 0.35, 0.35)
                add(a, shp, nm, col)
        return a
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
# v7: battery bay (2 x 2 SuperPack 60Ah, stacks touching) at the IceBox end,
# a kit-bar cross-member top and bottom at the bay's front edge, and the two
# cards lengthwise in front of it (posts on the cross-bars and the front rail).
# ----------------------------------------------------------------------------
V7_INV_LAYOUT = [   # inverter card (280 x 494): the 12/1200 upright, terminals down, alone
    dict(comp="multiplus_1200_up", x=15, z=20),
]
V7_DIST_LAYOUT = [  # distribution card (280 x 494), parts face -Y (toward the outboard cable space)
    dict(comp="breaker_a", x=15,  z=20),     # column A
    dict(comp="breaker_b", x=75,  z=20),
    dict(comp="busbar_n",  x=15,  z=110),
    dict(comp="busbar_p",  x=15,  z=155),
    dict(comp="mppt",      x=15,  z=210),
    dict(comp="garmin",    x=15,  z=355),
    dict(comp="shunt",     x=150, z=20),     # column B
    dict(comp="orion",     x=150, z=95),
    dict(comp="cerbo_up",  x=190, z=250),
]


LAT = dict(rib=8.0, pitch=45.0, border=12.0, t=6.0, tile_max=250.0, spline=(60.0, 18.0, 3.0), lap=24.0,
           boss_r=11.0, insert_hole=4.6)     # M5 heat-set insert: 4.6 mm pilot in a 22 mm solid boss

# Mounting holes per unit, (along, up) from the unit's lower-left as mounted; from the Victron
# dimension drawings in components.md.  "verify" = not published, measured from photos.
HOLES = {
    "cerbo":            [(5.5, 10), (148.5, 10), (5.5, 68), (148.5, 68)],                 # 143 x 58, 4 x M4
    "cerbo_up":         [(10, 5.5), (10, 148.5), (68, 5.5), (68, 148.5)],
    "orion":            [(6.9, 12), (116.2, 12), (6.9, 125), (116.2, 125)],               # 109.3 x 113, 4 x M4
    "mppt":             [(5, 33.5), (181, 33.5), (5, 105), (181, 105)],                   # keyholes 176 x 71.5
    "shunt":            [(9.5, 27), (110.5, 27)],                                         # 2 x M6 at 101
    "multiplus_1200_up": [(14.2, 68.0), (234.8, 68.0), (14.2, 311.8), (234.8, 311.8)],    # keyholes 220.6 x 243.8, upper pair 62.8 below the body top, M6
    "multiplus_1200":   [(99.4, 14.7), (343.2, 14.7), (99.4, 235.3), (343.2, 235.3)],
    "busbar_n":         [(12, 16), (143, 16)],      # verify
    "busbar_p":         [(12, 16), (143, 16)],      # verify
    "breaker_a":        [(24, 8), (24, 66)],        # verify (285-series: 2 x 1/4")
    "breaker_b":        [(24, 8), (24, 66)],        # verify
    "garmin":           [(20, 37), (105, 37)],      # verify (Garmin bracket, 2 screws)
    "bms":              [(10, 10), (112, 10), (10, 96), (112, 96)],   # verify
}
INSERT = {"mppt": "M5", "orion": "M4", "cerbo": "M4", "cerbo_up": "M4", "shunt": "M6", "busbar_n": "M5", "busbar_p": "M5",
          "breaker_a": "M6", "breaker_b": "M6", "garmin": "M4", "bms": "M4"}
HOLES["garmin_up"] = [(37, 20), (37, 105)]
INSERT["garmin_up"] = INSERT["garmin"]
FASTENER = {   # how each unit attaches to a printed card
    "multiplus_1200_up": "4 x M6 x 25 through-bolt + printed 40 x 40 backing plate behind each keyhole; weight on the two printed feet",
    "multiplus_1200":    "4 x M6 x 25 through-bolt + printed backing plates; weight on the two printed feet",
    "mppt":   "4 x M5 x 10 pan head into heat-set inserts; hang on the keyholes, then tighten",
    "orion":  "4 x M4 x 10 into M4 heat-set inserts",
    "cerbo":  "4 x M4 x 8 into M4 heat-set inserts", "cerbo_up": "4 x M4 x 8 into M4 heat-set inserts",
    "shunt":  "2 x M6 x 12 into M6 heat-set inserts",
    "busbar_n": "2 x M5 x 10 into inserts", "busbar_p": "2 x M5 x 10 into inserts",
    "breaker_a": "2 x M6 x 12 into inserts", "breaker_b": "2 x M6 x 12 into inserts",
    "garmin": "2 x M4 x 10 into inserts through its bracket", "garmin_up": "2 x M4 x 10 into inserts through its bracket", "bms": "4 x M4 x 8 into inserts",
}


def lattice_card_tiles(L, H, x0, y_plate, z0, prefix, patches=(), solids=()):
    """A printable card: ribbed tiles (<= tile_max each way) with a solid
    12 mm border, 8 mm ribs on a 45 mm pitch, 6 mm thick so the edges ride
    in the same post slots as a sheet.  Tiles join with 3 mm printed splines
    glued across the ribs on the back (+Y) face.  Yields (name, shape)."""
    nx = int(-(-L // LAT["tile_max"])); nz = int(-(-H // LAT["tile_max"]))
    tw, th = L / nx, H / nz
    t, rib, b = LAT["t"], LAT["rib"], LAT["border"]
    tiles = []
    lap = LAT["lap"]            # horizontal joints are HALF-LAPS: the lower tile keeps the back half of a
    for i in range(nx):         # lap-wide strip past the joint line, the upper tile the front half.  Each tile
        for j in range(nz):     # prints flat with its rabbet facing up (lower tiles back face down, upper tiles
            z_lo = 0.0 if j == 0 else -lap / 2                       # front face down): no supports.
            z_hi = th if j == nz - 1 else th + lap / 2
            tile = box(tw, t, z_hi - z_lo, (0, 0, z_lo))
            if j < nz - 1:   # top edge: remove the FRONT half of the strip
                tile = tile.cut(box(tw + 2, t / 2 + 1, lap + 1, (-1, -1, th - lap / 2)))
            if j > 0:        # bottom edge: remove the BACK half of the strip
                tile = tile.cut(box(tw + 2, t / 2 + 1, lap + 1, (-1, t / 2, -lap / 2 - 1)))
            for jl in (j, j + 1):   # 3 x M4 through-bolts across each lap this tile is part of
                if 0 < jl < nz:
                    for xc in (L * 0.25 - i * tw, L * 0.5 - i * tw, L * 0.75 - i * tw):
                        if 0 < xc < tw:
                            tile = tile.cut(cq.Workplane("XZ").center(xc, (jl - j) * th).circle(2.3).extrude(-t - 2).translate((0, 1, 0)))
            # openings between ribs, inside the border (card_style "solid" keeps the plate full)
            ox, oz = b, b
            while P["card_style"] != "solid" and ox + rib < tw - b:
                w = min(LAT["pitch"] - rib, tw - b - ox)
                oz = b
                while oz + rib < th - b:
                    h = min(LAT["pitch"] - rib, th - b - oz)
                    if w > 12 and h > 12:
                        tile = tile.cut(box(w, t + 2, h, (ox, -1, oz)))
                    oz += LAT["pitch"]
                ox += LAT["pitch"]
            # solid regions (e.g. under the inverter) so a unit can be shifted and re-drilled
            for (su, sv, sw, sh) in (solids if P["card_style"] != "solid" else ()):   # solid cards: nothing to fill (would refill the lap)
                u0, v0 = su - i * tw, sv - j * th
                if u0 < tw and v0 < th and u0 + sw > 0 and v0 + sh > 0:
                    tile = tile.union(box(sw, t, sh, (u0, 0, v0)).intersect(box(tw, t, th)))
            # solid bosses with insert pilot holes where a unit's mounting holes land on this tile
            for (pu, pv) in patches:
                u, v = pu - i * tw, pv - j * th
                if -LAT["boss_r"] < u < tw + LAT["boss_r"] and -LAT["boss_r"] < v < th + LAT["boss_r"]:
                    boss = cq.Workplane("XZ").center(u, v).circle(LAT["boss_r"]).extrude(-t).intersect(box(tw, t, th))
                    tile = tile.union(boss).cut(cq.Workplane("XZ").center(u, v).circle(LAT["insert_hole"] / 2).extrude(-t - 2).translate((0, 1, 0)))
            tiles.append((f"print_{prefix}_tile_{i}{j}", tile.translate((x0 + i * tw, y_plate, z0 + j * th))))
    # splines sit in 3 mm pockets recessed into the back (+Y) face so the back of the card is flush
    sl, sw, st = LAT["spline"]
    splines = []
    for i in range(1, nx):            # vertical joints
        for zc in (z0 + H * 0.25, z0 + H * 0.5, z0 + H * 0.75):
            splines.append((f"print_{prefix}_spline_v{i}_{int(zc)}", box(sl, st, sw, (x0 + i * tw - sl / 2, y_plate + t - st, zc - sw / 2))))
    for nm, tile in tiles:
        for _, sp in splines:
            bb = sp.val().BoundingBox()
            tile = tile.cut(box(bb.xlen + 0.4, st + 1, bb.zlen + 0.4, (bb.xmin - 0.2, bb.ymin, bb.zmin - 0.2)))
        yield nm, tile
    for nm, sp in splines:
        yield nm, sp


def v7_geometry():
    inv = COMPONENTS[P["inverter"]]
    bay_x1 = x_in0 + V7["bay_D"]                     # front face of the bay (legs included)
    bar_x = bay_x1 + V7["bar_gap"]                   # cross-bars (kit bar, 25.4 square)
    cards_x0 = bar_x + B + 2                         # posts start here
    card_L = (x_in0 + in_D) - cards_x0 - 2 * (P["post_d"] - P["slot_depth"]) - 2 * P["card_clear"]
    card_x0 = cards_x0 + (P["post_d"] - P["slot_depth"]) + P["card_clear"]
    wall_in = out_W - B
    inv_plate = wall_in - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"] - 1 - P["card_t"]
    inv_lo = inv_plate - BS["standoff"] - inv.d
    dist_plate = inv_lo - BS["gap"] - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"] - P["card_t"]
    parts_lo = dist_plate - 48.0
    return dict(bay_x1=bay_x1, bar_x=bar_x, cards_x0=cards_x0, card_L=card_L, card_x0=card_x0,
                inv_plate=inv_plate, inv_lo=inv_lo, dist_plate=dist_plate, parts_lo=parts_lo,
                spare_W=parts_lo - BS["gap"] - y_in0)


def build_v7(a):
    g = v7_geometry()
    b = COMPONENTS["battery"]; wall, L = V7["wall"], V7["leg"]
    # --- battery bay: two touching stacks of two, on the plate --------------
    tx = x_in0 + V7["end_gap"]
    for sidx in range(2):
        ty = y_in0 + 1 + sidx * V7["tray_w"]
        fd, fw = b.d + 2 * wall, V7["tray_w"]
        tray = box(fd, fw, 24).cut(box(b.d, b.w, 25, (wall, wall, 4)))
        add(a, tray.translate((tx, ty, 0)), f"print_tray_battery_{sidx}", ORANGE)
        z = 4.0
        for lvl in range(2):
            at = (tx + wall, ty + wall, z)
            add(a, victron_shape("battery", b.d, b.w, b.h, at, box(b.d, b.w, b.h, at).edges("|Z").fillet(6)), f"battery_{sidx}_{lvl}", BATT)
            z += b.h
            if lvl == 0:
                z += P["term_clear"]
                sh = box(fd + 2 * L, fw, P["shelf_t"] + 12)
                sh = sh.cut(box(b.d, b.w, 13, (L + wall, wall, P["shelf_t"])))
                sh = sh.cut(box(fd - 2 * wall - 30, fw - 2 * wall - 30, P["shelf_t"] + 1, (L + wall + 15, wall + 15, -0.5)))
                add(a, sh.translate((tx - L, ty, z)), f"print_shelf_{sidx}", ORANGE)
                for (lx, ly) in ((tx - L, ty), (tx - L, ty + fw - L), (tx + fd, ty), (tx + fd, ty + fw - L)):
                    leg = box(L, L, z)
                    foot = box(L, L + 16, 6, (0, -8, 0)).cut(cq.Workplane("XY").center(L / 2, L / 2).circle(3.4).extrude(7))
                    add(a, leg.union(foot).translate((lx, ly, 0)), f"print_leg_{sidx}_{int(lx)}_{int(ly)}", ORANGE)
                z += P["shelf_t"]
    g["stack_top"] = z + P["term_clear"]

    # --- cross-members: two spare kit bars cut to the inner width -------------
    for zb, nm in ((0, "bot"), (out_H - B, "top")):
        add(a, bar(in_W, "y").translate((g["bar_x"] + B / 2, B, zb + B / 2)), f"bar_cross_{nm}", GRAY)
        for y in (B, out_W - B - 30):   # printed corner brackets tying the cross-bar to the depth rails
            add(a, box(30, 30, 25).translate((g["bar_x"] - 2, y, zb + (B if zb == 0 else -25))), f"print_bracket_{nm}_{int(y)}", ORANGE)

    # --- floor panel under the card zone only ---------------------------------
    add(a, box(x_in0 + in_D - g["bar_x"] - B, in_W, T, (g["bar_x"] + B, y_in0, B)), "panel_floor_front", PANEL)

    # --- the two lengthwise cards + posts --------------------------------------
    plate_h = in_H - 8
    inv = COMPONENTS[P["inverter"]]
    for name, py_plate, layout in (("inverter", g["inv_plate"], V7_INV_LAYOUT), ("dist", g["dist_plate"], V7_DIST_LAYOUT)):
        patches = [(pl["x"] + du, pl["z"] + dv) for pl in layout for (du, dv) in HOLES.get(pl["comp"], [])]
        solids = [(pl["x"] - 10, pl["z"] - 10, COMPONENTS[pl["comp"]].w + 20, COMPONENTS[pl["comp"]].h + 20)
                  for pl in layout if pl["comp"].startswith("multiplus")]
        if P["card_style"] in ("lattice", "solid"):
            for nm, shp in lattice_card_tiles(g["card_L"], plate_h, g["card_x0"], py_plate, floor_top + 2, f"card_{name}", patches, solids):
                add(a, shp, nm + "__card", ORANGE if "spline" in nm else DARK)
        else:
            add(a, box(g["card_L"], P["card_t"], plate_h, (g["card_x0"], py_plate, floor_top + 2)), f"card_{name}_plate", DARK)
        py = py_plate - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"]
        for end, x in (("back", g["cards_x0"]), ("front", out_D - B - P["post_d"])):
            for k, (z, gp) in enumerate(post_xz(end)):
                add(a, gp.translate((x, py, floor_top + z)), f"print_post_{name}_{end}_{k}", ORANGE)
        for pl in layout:
            c = COMPONENTS[pl["comp"]]
            depth_off = BS["standoff"] if pl["comp"].startswith("multiplus") else 0
            if pl["comp"].startswith("multiplus"):
                for xx in (pl["x"] + 25, pl["x"] + c.w - 85):
                    add(a, box(60, BS["standoff"] + 4, 18, (g["card_x0"] + xx, py_plate - BS["standoff"] - 4, floor_top + 2 + pl["z"] - 18)), f"print_feet_mp_{int(xx)}__card", ORANGE)
            at = (g["card_x0"] + pl["x"], py_plate - depth_off - c.d, floor_top + 2 + pl["z"])
            col = BLUE if c.name.startswith("victron") else (0.08, 0.08, 0.08) if c.name.startswith("garmin") else GOLD
            add(a, victron_shape(pl["comp"], c.w, c.d, c.h, at, box(c.w, c.d, c.h, at).edges("|Y").fillet(3)), c.name + "__card", col)
    BS["_g7"] = g
    return g


FEET_H = 18.0        # printed feet under the MultiPlus: it stands on these, the bolts only hold it to the card
# v9: bus deck on top of the battery rack (x along the depth from the bay's back, y across; parts stand up)
DECK_EXT = 40.0      # the deck runs forward over the wiring gap by this much, to carry the connector row
V9_DECK_LAYOUT = [   # deck is ~295 (x, depth) x 294 (y); x from the deck's back edge
    dict(comp="busbar_n",  x=20,  y=20),
    dict(comp="breaker_a", x=20,  y=190),
    dict(comp="breaker_b", x=20,  y=245),
    dict(comp="busbar_p",  x=65,  y=20),
    dict(comp="shunt_x",   x=70,  y=236),
    # fixed connector halves bolted to the deck, mating axis along the depth, facing the cards (+X).
    # The pigtail's flying half mates in front and pulls off forward (25 / 15 mm) on the deck's extension.
    dict(comp="sb175_x",   x=115, y=20),    # inverter DC
    dict(comp="sb50_x",    x=160, y=90),    # MPPT
    dict(comp="sb50_x",    x=160, y=135),   # Orion
    dict(comp="sb50_x",    x=160, y=180),   # Garmin + Cerbo feed
]
# v10: everything on the deck.  Rear + middle plates: x from the deck's back edge (0..312), y from its outboard edge.
# Hand windows over the battery lugs sit at x 26..146, y 45..105 and 196..256; the bus bars run along the depth
# between them; breakers beside each window at the deck edges; shunt and Orion on the middle zone.
V10_DECK_LAYOUT = [
    dict(comp="busbar_nx",  x=0,   y=108),
    dict(comp="busbar_px",  x=0,   y=158),
    dict(comp="breaker_a",  x=150, y=0),
    dict(comp="breaker_b",  x=150, y=250),
    dict(comp="orion_flat", x=158, y=49),    # straddles the rear/middle plate joint; its screws tie the plates
    dict(comp="shunt_y",    x=200, y=182),
]
# front plate (ahead of the inverter card): x from the plate's back edge (0..220)
V10_FRONT_LAYOUT = [
    dict(comp="mppt_flat",   x=0,   y=5),
    dict(comp="garmin_flat", x=0,   y=200),
    dict(comp="cerbo_flat",  x=140, y=25),
]
# fixed halves on the cards themselves, standing with the mating face UP, so the pigtail lifts off before the card
# v9 cards are cut down CARD_TRIM so the connector stack at the top of each card leaves CONN_LID_ROOM under the
# lid for the pigtail cables, which exit the mated halves upward.  Connector z is computed from the lid.
CARD_TRIM = 50.0
LEG_LAP = (215.0, 252.0)   # v9 rack legs: half-lap joint between the two printed segments (both stay under 256 tall)
SHELF_SCREW_Z = 240.0      # shelf end-wall M4 (shelf underside 231 + 9): passes through both lap halves
CONN_LID_ROOM = 60.0
def _conn_z(kind):
    """card-relative z of a card-mounted fixed half so the mated pair tops out CONN_LID_ROOM under the lid"""
    mated = MATED[kind]
    return (out_H - CONN_LID_ROOM) - (floor_top + 2) - mated
V9_INV_REAR = [dict(comp="sb175_v", y=150, z=None)]
V9_CHARGE_REAR = [dict(comp="sb50_v", y=y, z=None) for y in (15, 62, 109, 156, 203)]   # MPPT, Orion, Garmin+Cerbo, solar in, alternator in
V9_CHARGE_FRONT = [dict(comp="pp45_v", y=20, z=None)]   # Garmin -> front-panel sockets: PP45 block at the top of the front face
V9_INV_LAYOUT = [    # inverter card (249 wide = the MultiPlus): the SB175 pigtail leaves the top rear corner and mates on the deck
    dict(comp="multiplus_1200_up", y=0, z=2 + FEET_H),
]
V9_CHARGE_LAYOUT = [
    dict(comp="mppt",  y=12,  z=20),
    dict(comp="orion", y=12,  z=175),      # keep units >= 10 mm from the card edge: the post lip reaches 8 mm past the card face
    dict(comp="cerbo", y=12,  z=340),
    dict(comp="garmin_up", y=140, z=175),   # PowerSwitch turned 90 deg beside the Orion
]
V8_INV_LAYOUT = [    # inverter card, parts face +X (forward); y from the card's outboard end, z from its bottom
    dict(comp="multiplus_1200_up", y=13, z=2 + FEET_H),
    dict(comp="shunt", y=80, z=410),
]
V8_CHARGE_LAYOUT = [
    dict(comp="mppt",  y=12,  z=20),
    dict(comp="orion", y=12,  z=175),
    dict(comp="cerbo", y=12,  z=340),
    dict(comp="garmin", y=145, z=175),
]
V8_DIST_LAYOUT = [   # keep parts above z=130: the socket bodies sit in the front panel's lower band
    dict(comp="busbar_n",  y=10,  z=140),
    dict(comp="busbar_p",  y=10,  z=185),
    dict(comp="breaker_a", y=10,  z=240),
    dict(comp="breaker_b", y=70,  z=240),
]


def build_v8(a, nine=False):
    g = dict()
    b = COMPONENTS["battery"]; wall, L = V7["wall"], V7["leg"]
    # --- battery bay (same rack as v7) -------------------------------------
    tx = x_in0 + V7["end_gap"]
    for sidx in range(2):
        ty = y_in0 + 1 + sidx * V7["tray_w"]
        fd, fw = b.d + 2 * wall, V7["tray_w"]
        lip = V7["lip"]
        tray = box(fd, fw, lip + 4).cut(box(b.d, b.w, lip + 5, (wall, wall, 4)))
        if nine:
            # one 25 mm cam strap per battery runs LENGTHWISE: through the back end wall, along a 2 mm channel
            # under the battery, out through the front end wall, up and over the top, buckle in the 70 mm wiring
            # gap in front.  (Crosswise slots can't work: the trays touch each other and sit 1 mm from the rail.)
            tray = tray.cut(box(fd + 2, 28, 5, (-1, wall + b.w / 2 - 14, 2)))
            # corner pads outside the end walls: a vertical M4 heat-set insert in 13 mm of plastic (pad + wall)
            # takes the leg's foot tab.  6 mm pads keep the tray at 253 mm on the bed.
            for (px, py) in ((-6, 12), (-6, fw - 32), (fd, 12), (fd, fw - 32)):
                tray = tray.union(box(6, 20, lip + 4, (px, py, 0)))
            for (px, py) in ((-6, 12), (-6, fw - 32), (fd, 12), (fd, fw - 32)):
                hx = px + 6.0 if px < 0 else px
                tray = tray.cut(cq.Workplane("XY").center(hx, py + 10).circle(2.8).extrude(13).translate((0, 0, lip + 4 - 12)))
        else:
            for sx in (b.d * 0.3, b.d * 0.7):   # strap slots through the floor for 25 mm cam straps
                tray = tray.cut(box(28, fw + 2, 5, (wall + sx - 14, -1, 2)))
        for (hx, hy) in ((wall + 20, wall + 20), (wall + b.d - 20, wall + 20), (wall + 20, wall + b.w - 20), (wall + b.d - 20, wall + b.w - 20)):
            tray = tray.cut(cq.Workplane("XY").center(hx, hy).circle(3.4).extrude(5))   # M6 to the Goose Gear plate
        if nine:
            # L tabs tie each tray to the bottom rails so the frame carries the stacks when the box is lifted
            # as one unit.  The tray floor stays flat on the plate: the rail top (z = B) is below the wall top,
            # so a flange grown out of the top of the outer side wall lies on the rail and bolts down into its
            # T-slot with a 1/4-20 T-nut.  Tray-local coordinates: x 0..fd, y 0..fw, z 0 on the plate.
            rail_lo = -(1 + B) if sidx == 0 else fw + 1              # rail spans rail_lo .. rail_lo + B (1 mm gap)
            for sx in (40, fd - 80):
                fl = box(40, B + 1 + 8, (lip + 4) - B, (sx, rail_lo if sidx == 0 else fw - 8, B))   # rail top -> wall top, 8 mm onto the wall
                fl = fl.cut(cq.Workplane("XY").center(sx + 20, rail_lo + B / 2).circle(3.4).extrude(lip + 5))
                tray = tray.union(fl)
            # back rail: the tray + flange would be 282 mm (over the bed), so the back tabs are separate L
            # brackets.  The tray's back wall gets two 6 mm pads with M5 heat-set inserts (12 mm of wall);
            # the bracket bolts to a pad with 2 x M5 and its flange lies on the back width rail with a T-nut.
            for sy in (18, fw - 58):          # clear of the strap slot (y 61..89) and merged with the corner pads
                pad = box(6, 40, lip + 4, (-6, sy, 0))
                for hz in (10, 24):
                    pad = pad.cut(cq.Workplane("YZ").center(sy + 20, hz).circle(3.2).extrude(10).translate((-7, 0, 0)))
                tray = tray.union(pad)
                rail_x = -(V7["end_gap"] + B)                         # back width rail, tray-local x
                br = box(8, 40, lip + 4, (-14, sy, 0)).union(box(-6 - rail_x, 40, (lip + 4) - B, (rail_x, sy, B)))
                br = br.cut(cq.Workplane("XY").center(rail_x + B / 2, sy + 20).circle(3.4).extrude(lip + 5))
                for hz in (10, 24):
                    br = br.cut(cq.Workplane("YZ").center(sy + 20, hz).circle(2.7).extrude(10).translate((-15, 0, 0)))
                add(a, br.translate((tx, ty, 0)), f"print_tray_tab_{sidx}_{int(sy)}", ORANGE)
        add(a, tray.translate((tx, ty, 0)), f"print_tray_battery_{sidx}", ORANGE)
        z = 4.0
        for lvl in range(2):
            at = (tx + wall, ty + wall, z)
            add(a, victron_shape("battery", b.d, b.w, b.h, at, box(b.d, b.w, b.h, at).edges("|Z").fillet(6)), f"battery_{sidx}_{lvl}", BATT)
            z += b.h
            if lvl == 0:
                z += P["term_clear"]
                if nine:   # shelf sits on the lower battery between the legs, 15 mm lip, screw tabs into the legs
                    sh = box(fd, fw, P["shelf_t"] + 15)
                    sh = sh.cut(box(b.d, b.w, 16, (wall, wall, P["shelf_t"])))
                    sh = sh.cut(box(fd - 2 * wall - 30, fw - 2 * wall - 30, P["shelf_t"] + 1, (wall + 15, wall + 15, -0.5)))
                    # the legs stand at the shelf's end walls: an M4 through each end wall into an insert in the leg
                    for (hy) in (L / 2, fw - L / 2):
                        sh = sh.cut(cq.Workplane("YZ").center(hy, P["shelf_t"] / 2 + 4).circle(2.3).extrude(fd + 2).translate((-1, 0, 0)))
                    sh = sh.cut(box(fd + 2, 28, 5, (-1, wall + b.w / 2 - 14, P["shelf_t"] - 2)))   # lengthwise strap channel
                    add(a, sh.translate((tx, ty, z)), f"print_shelf_{sidx}", ORANGE)
                else:
                    sh = box(fd + 2 * L, fw, P["shelf_t"] + 12)
                    sh = sh.cut(box(b.d, b.w, 13, (L + wall, wall, P["shelf_t"])))
                    sh = sh.cut(box(fd - 2 * wall - 30, fw - 2 * wall - 30, P["shelf_t"] + 1, (L + wall + 15, wall + 15, -0.5)))
                    add(a, sh.translate((tx - L, ty, z)), f"print_shelf_{sidx}", ORANGE)
                leg_h = z if not nine else (4 + 2 * b.h + P["term_clear"] + P["shelf_t"] + P["term_clear"])   # v9: legs run up to the bus deck
                for (lx, ly) in ((tx - L, ty), (tx - L, ty + fw - L), (tx + fd, ty), (tx + fd, ty + fw - L)):
                    if nine:
                        # Leg = two segments joined by a 37 mm HALF-LAP (z 215..252, both print under 256).  The shelf's
                        # M4 passes through the shelf end wall and BOTH lap halves at z 240, so one screw pins the
                        # shelf and the joint.  The lower segment stands on the plate and has a foot tab lying on the
                        # tray's wall top, M4 down into the corner pad's insert: lift the tray and the leg comes with
                        # it.  The upper segment ends in a 14 mm boss with a 16 mm tab reaching under the deck; the
                        # deck's M4 lands in that tab, 10 mm inside the deck edge.
                        back, outer = lx < tx, (ly == ty)
                        lap0, lap1 = LEG_LAP
                        wall_half = (L / 2, L) if back else (0, L / 2)          # half of the lap nearest the tray wall
                        free_half = (0, L / 2) if back else (L / 2, L)
                        lower = box(L, L, lap0).union(box(L / 2, L, lap1 - lap0, (free_half[0], 0, lap0)))
                        tx0, tx1 = (0, 18) if back else (-6, L)                 # foot tab over the pad + wall top
                        ty0, ty1 = (0, 32) if outer else (-20, L)
                        hx, hy = (12.0 if back else 0.0), (22 if outer else -10)
                        tab = box(tx1 - tx0, ty1 - ty0, 6, (tx0, ty0, lip + 4))
                        lower = lower.union(tab).cut(cq.Workplane("XY").center(hx, hy).circle(2.3).extrude(8).translate((0, 0, lip + 3)))
                        upper = box(L / 2, L, lap1 - lap0, (wall_half[0], 0, lap0)).union(box(L, L, leg_h - lap1, (0, 0, lap1)))
                        bx0 = 0 if back else -16
                        boss = box(L + 16, L, 14, (bx0, 0, leg_h - 14))
                        bhx = L / 2 + (12 if back else -12)
                        upper = upper.union(boss).cut(cq.Workplane("XY").center(bhx, L / 2).circle(2.3).extrude(11).translate((0, 0, leg_h - 10)))
                        shelf_screw = cq.Workplane("YZ").center(L / 2, SHELF_SCREW_Z).circle(1.65).extrude(L + 2).translate((-1, 0, 0))
                        add(a, lower.cut(shelf_screw).translate((lx, ly, 0)), f"print_leg_{sidx}_{int(lx)}_{int(ly)}_lower", ORANGE)
                        add(a, upper.cut(shelf_screw).translate((lx, ly, 0)), f"print_leg_{sidx}_{int(lx)}_{int(ly)}_upper", ORANGE)
                    else:
                        leg = box(L, L, leg_h)
                        foot = box(L, L + 16, 6, (0, -8, 0)).cut(cq.Workplane("XY").center(L / 2, L / 2).circle(3.4).extrude(7))
                        add(a, leg.union(foot).translate((lx, ly, 0)), f"print_leg_{sidx}_{int(lx)}_{int(ly)}", ORANGE)
                z += P["shelf_t"]
    g["stack_top"] = z + P["term_clear"]
    g["bay_x1"] = x_in0 + V7["bay_D"]
    if nine:
        # --- bus deck: printed plate on the rack legs, over both stacks ------------
        dz = g["stack_top"]
        dx0 = tx - L / 2 + 4                                      # 4 mm inside the back leg centreline
        dL = (tx + fd + L / 2 - 4) - dx0                          # .. to 4 mm inside the front one: 245, fits the bed
        FULL = P["deck"] == "full"
        card_x = x_in0 + V8["x_inv"]
        ext = (card_x - V10["slot_back"] - (dx0 + dL)) if FULL else DECK_EXT
        g["deck_x0"], g["deck_L"] = dx0, dL + ext
        cy0_ = y_in0 + (in_W - (in_W - 2 * (P["post_standoff"] + P["post_d"] - P["slot_depth"]) - 2 * P["card_clear"])) / 2
        for half in range(2):   # extension plates over the wiring gap, splined to the main halves
            hw = V7["bay_W"] / 2
            ep = box(ext, hw, P["card_t"], (dx0 + dL, y_in0 + 1 + half * hw, dz))
            if FULL and half == 1:   # notch for the inverter card's SB175 pigtail half, which rises through the deck plane
                c175 = COMPONENTS["sb175_v"]; y175 = cy0_ + V9_INV_REAR[0]["y"]
                ep = ep.cut(box(c175.d + 6 + V10["slot_back"], c175.w + 8, P["card_t"] + 2, (card_x - c175.d - 4, y175 - 4, dz - 1)))
            add(a, ep, f"print_bus_deck_ext_{half}", ORANGE)
            add(a, box(60, 18, 3, (dx0 + dL - 30, y_in0 + 1 + half * hw + hw / 2 - 9, dz - 3)), f"print_bus_deck_ext_spline_{half}", ORANGE)
        if FULL:
            # front plates ahead of the inverter card, carrying the MPPT, Garmin and Cerbo; they rest on ledges
            # screwed to the card's guide posts and on ties to the front corner bars (mirror of the rear deck ties)
            fx0 = card_x + P["card_t"] + V10["slot_front"]
            fL = V10["front_plate"]
            g["front_x0"], g["front_L"] = fx0, fL
            for half in range(2):
                hw = V7["bay_W"] / 2
                add(a, box(fL, hw, P["card_t"], (fx0, y_in0 + 1 + half * hw, dz)), f"print_bus_deck_front_{half}", ORANGE)
            for xs in (fL * 0.3, fL * 0.7):
                add(a, box(18, 60, 3, (fx0 + xs - 9, y_in0 + 1 + V7["bay_W"] / 2 - 30, dz - 3)), f"print_bus_deck_front_spline_{int(xs)}", ORANGE)
            px_ = card_x - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"]
            for j, py in enumerate((y_in0 + P["post_standoff"], out_W - B - P["post_d"] - P["post_standoff"])):
                for side, lx in (("back", px_ - 30), ("front", px_ + P["post_w"])):   # ledge block on the post's rear / front face
                    ledge = box(30, P["post_d"], 20, (lx, py, dz - 20))
                    ledge = ledge.cut(cq.Workplane("XY").center(lx + 15, py + P["post_d"] / 2).circle(2.3).extrude(12).translate((0, 0, dz - 11)))   # M4 insert for the plate
                    for hz in (dz - 6, dz - 15):   # 2 x M4 along X into inserts in the post
                        ledge = ledge.cut(cq.Workplane("YZ").center(py + P["post_d"] / 2, hz).circle(2.3).extrude(32).translate((lx - 1, 0, 0)))
                    add(a, ledge, f"print_post_ledge_{side}_{j}", ORANGE)
            for side in range(2):
                tie = (box(B, 6, 32, (0, B, dz - 20)).union(box(58, 6, 6, (0, B, dz + P["card_t"])))
                       .union(box(58 - dx0, 46 - B, 6, (dx0, B, dz + P["card_t"]))))
                tie = tie.cut(cq.Workplane("XZ").center(B / 2, dz - 8).circle(3.4).extrude(-(B + 8)).translate((0, B - 1, 0)))
                for hx in (45, 54):
                    tie = tie.cut(cq.Workplane("XY").center(hx, 36).circle(2.3).extrude(8).translate((0, 0, dz + P["card_t"] - 1)))
                tie = tie.mirror("YZ").translate((out_D, 0, 0))
                if side == 1:
                    tie = tie.mirror("XZ").translate((0, out_W, 0))
                add(a, tie, f"print_deck_tie_front_{side}", ORANGE)
        for half in range(2):   # two printable halves, one over each stack, splined at the centre line, M4 into the leg bosses
            hw = V7["bay_W"] / 2
            deck = box(dL, hw, P["card_t"], (dx0, y_in0 + 1 + half * hw, dz))
            deck = deck.cut(box(120, 60, P["card_t"] + 2, (x_in0 + 40, y_in0 + 1 + half * hw + hw / 2 - 30, dz - 1)))   # hand window over the lugs
            for (hx, ly) in ((tx + 6, y_in0 + 1 + half * V7["tray_w"]), (tx + fd - 6, y_in0 + 1 + half * V7["tray_w"]),
                             (tx + 6, y_in0 + 1 + half * V7["tray_w"] + fw - L), (tx + fd - 6, y_in0 + 1 + half * V7["tray_w"] + fw - L)):
                deck = deck.cut(cq.Workplane("XY").center(hx, ly + L / 2).circle(2.3).extrude(P["card_t"] + 2).translate((0, 0, dz - 1)))
            add(a, deck, f"print_bus_deck_{half}", ORANGE)
        # deck ties: the deck's two back corners bolt to the vertical corner bars (T-nut in the bar's inboard-facing
        # slot) through a printed bracket: a plate on the bar, a bridge over the leg boss, a pad with 2 x M4 on the deck.
        # The rack is then a closed cell: frame -> tray tabs -> trays -> leg tabs -> legs -> deck -> ties -> frame.
        for side in range(2):
            tie = (box(B, 6, 32, (0, B, dz - 20))                      # on the corner bar's +Y face
                   .union(box(58, 6, 6, (0, B, dz + P["card_t"])))      # bridge, over the leg boss, onto the deck top
                   .union(box(58 - dx0, 46 - B, 6, (dx0, B, dz + P["card_t"]))))   # pad on the deck, clear of the bus bar
            tie = tie.cut(cq.Workplane("XZ").center(B / 2, dz - 8).circle(3.4).extrude(-(B + 8)).translate((0, B - 1, 0)))
            for hx in (45, 54):
                tie = tie.cut(cq.Workplane("XY").center(hx, 36).circle(2.3).extrude(8).translate((0, 0, dz + P["card_t"] - 1)))
            if side == 1:
                tie = tie.mirror("XZ").translate((0, out_W, 0))
            add(a, tie, f"print_deck_tie_{side}", ORANGE)
        for xs in (dL * 0.25, dL * 0.5, dL * 0.75):
            add(a, box(18, 60, 3, (dx0 + xs - 9, y_in0 + 1 + V7["bay_W"] / 2 - 30, dz - 3)), f"print_bus_deck_spline_{int(xs)}", ORANGE)
        deck_items = ([(dx0, pl) for pl in V10_DECK_LAYOUT] + [(g["front_x0"], pl) for pl in V10_FRONT_LAYOUT]) if FULL \
            else [(dx0, pl) for pl in V9_DECK_LAYOUT]
        for ox, pl in deck_items:
            c = COMPONENTS[pl["comp"]]
            at = (ox + pl["x"], y_in0 + 1 + pl["y"], dz + P["card_t"])
            col = (0.3, 0.3, 0.3) if c.name.startswith("socket") else GOLD
            add(a, victron_shape(pl["comp"], c.d, c.w, c.h, at, box(c.d, c.w, c.h, at).edges("|Z").fillet(3)), c.name + f"_{int(pl['x'])}_{int(pl['y'])}", col)
            if pl["comp"] in MATED:   # the pigtail's flying half, mated in front (+X); it stays with the pigtail, not the card
                overlap = 2 * c.d - MATED[pl["comp"]]
                at2 = (at[0] + c.d - overlap, at[1], at[2])
                add(a, victron_shape(pl["comp"], c.d, c.w, c.h, at2, box(c.d, c.w, c.h, at2).edges("|Z").fillet(3)),
                    c.name + f"_plug_{int(pl['x'])}_{int(pl['y'])}", (0.1, 0.6, 0.4))
        g["deck_z"] = dz

    # --- floor panel under the card zone ----------------------------------------
    add(a, box(x_in0 + in_D - g["bay_x1"], in_W, T, (g["bay_x1"], y_in0, B)), "panel_floor_front", PANEL)

    # --- three cards across the box, posts on the side depth rails ---------------
    cw = in_W - 2 * (P["post_standoff"] + P["post_d"] - P["slot_depth"]) - 2 * P["card_clear"]
    cy0 = y_in0 + (in_W - cw) / 2
    ch = in_H - 8 - (CARD_TRIM if nine else 0)
    inv = COMPONENTS[P["inverter"]]
    if nine and P["deck"] == "full":
        cards = (("inverter", x_in0 + V8["x_inv"], V9_INV_LAYOUT, 10.0),)
        card_conn = {"inverter": (V9_INV_REAR, [])}
    elif nine:
        cards = (("inverter", x_in0 + V8["x_inv"], V9_INV_LAYOUT, 10.0),
                 ("charge", x_in0 + V8["x_charge"], V9_CHARGE_LAYOUT, 0.0))
        card_conn = {"inverter": (V9_INV_REAR, []), "charge": (V9_CHARGE_REAR, V9_CHARGE_FRONT)}
    else:
        cards = (("inverter", x_in0 + V8["x_inv"], V8_INV_LAYOUT, 10.0),
                 ("charge", x_in0 + V8["x_charge"], V8_CHARGE_LAYOUT, 0.0),
                 ("dist", x_in0 + V8["x_dist"], V8_DIST_LAYOUT, 0.0))
    g.update(cw=cw, cy0=cy0, ch=ch, cards={n: x for n, x, _, _ in cards})
    for name, cx, layout, standoff in cards:
        patches = [(pl["y"] + du, pl["z"] + dv) for pl in layout for (du, dv) in HOLES.get(pl["comp"], [])]
        solids = [(pl["y"] - 10, pl["z"] - 10, COMPONENTS[pl["comp"]].w + 20, COMPONENTS[pl["comp"]].h + 20)
                  for pl in layout if pl["comp"].startswith("multiplus")]
        if P["card_style"] in ("lattice", "solid"):
            for nm, shp in lattice_card_tiles_yz(cw, ch, cx, cy0, floor_top + 2, f"card_{name}", patches, solids):
                add(a, shp, nm + "__card", ORANGE if "spline" in nm else DARK)
            # the MultiPlus bolts get M6 fender washers (30 mm) on the back face, not printed plates: the back stays flush
        else:
            add(a, box(P["card_t"], cw, ch, (cx, cy0, floor_top + 2)), f"card_{name}_plate", DARK)
        px = cx - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"]
        for j, y in enumerate((y_in0 + P["post_standoff"], out_W - B - P["post_d"] - P["post_standoff"])):
            for k, (z, gp) in enumerate(guide_post_segments()):
                if j == 1:
                    gp = gp.mirror("XZ").translate((0, P["post_d"], 0))
                add(a, gp.translate((px, y, floor_top + z)), f"print_post_{name}_{j}_{k}", ORANGE)
        for pl in layout:
            c = COMPONENTS[pl["comp"]]
            if pl["comp"].startswith("multiplus"):
                for yy in (pl["y"] + 25, pl["y"] + c.w - 85):   # two 60 mm wide feet under the housing, 18 tall, standoff deep
                    add(a, box(standoff + 4, 60, FEET_H, (cx + P["card_t"], cy0 + yy, floor_top + 2 + pl["z"] - FEET_H)), f"print_feet_mp_{int(yy)}__card", ORANGE)
            at = (cx + P["card_t"] + standoff, cy0 + pl["y"], floor_top + 2 + pl["z"])
            col = BLUE if c.name.startswith("victron") else (0.08, 0.08, 0.08) if c.name.startswith("garmin") else (0.3, 0.3, 0.3) if c.name.startswith("socket") else GOLD
            # parts face +X: their depth d runs along X, width w along Y
            add(a, victron_shape(pl["comp"], c.d, c.w, c.h, at, box(c.d, c.w, c.h, at).edges("|X").fillet(3)),
                c.name + f"_{int(pl['y'])}_{int(pl['z'])}__card", col)
        if nine:   # the card's own fixed connector halves, standing with the mating face up; pigtail halves mated above them
            rear, front = card_conn[name]
            for side, lst in (("rear", rear), ("front", front)):
                for pl in lst:
                    c = COMPONENTS[pl["comp"]]
                    if pl["z"] is None:
                        pl["z"] = _conn_z(pl["comp"])
                    cxs = cx - c.d if side == "rear" else cx + P["card_t"]
                    # the front-face Powerpole sits above the MPPT/Cerbo zone; keep it clear of the 70 mm-deep MPPT
                    at = (cxs, cy0 + pl["y"], floor_top + 2 + pl["z"])
                    add(a, victron_shape(pl["comp"], c.d, c.w, c.h, at, box(c.d, c.w, c.h, at).edges("|Z").fillet(3)),
                        c.name + f"_{name}_{side}_{int(pl['y'])}__card", (0.3, 0.3, 0.3))
                    overlap = 2 * c.h - MATED[pl["comp"]]
                    at2 = (cxs, cy0 + pl["y"], floor_top + 2 + pl["z"] + c.h - overlap)
                    add(a, victron_shape(pl["comp"], c.d, c.w, c.h, at2, box(c.d, c.w, c.h, at2).edges("|Z").fillet(3)),
                        c.name + f"_pigtail_{name}_{side}_{int(pl['y'])}", (0.1, 0.6, 0.4))
    BS["_g8"] = g
    return g


def build_v9(a):
    return build_v8(a, nine=True)


def lattice_card_tiles_yz(W, H, x_plate, y0, z0, prefix, patches=(), solids=()):
    """Same ribbed tiles as lattice_card_tiles, for a card in the YZ plane."""
    for nm, shp in lattice_card_tiles(W, H, 0.0, 0.0, 0.0, prefix, patches, solids):
        shp = shp.rotate((0, 0, 0), (0, 0, 1), 90)          # X -> Y
        yield nm, shp.translate((x_plate + LAT["t"], y0, z0))


def dims_v8():
    g = BS.get("_g8") or {}
    inv = COMPONENTS[P["inverter"]]
    top = out_H + 40; D = []
    def dim(p1, p2, label, off): D.append(dict(a=p1, b=p2, label=label, off=off))
    dim([0, 0, top], [out_D, 0, top], f"depth {out_D:.0f} mm ({out_D / 25.4:.1f} in)", [0, -60, 0])
    dim([0, 0, top], [0, out_W, top], f"width {out_W:.0f} mm ({out_W / 25.4:.1f} in)", [-60, 0, 0])
    dim([out_D + 60, 0, 0], [out_D + 60, 0, out_H], f"height {out_H:.0f} mm ({out_H / 25.4:.1f} in)", [40, 0, 0])
    y = -30; z = 40
    dim([x_in0, y, z], [x_in0 + V7["bay_D"], y, z], f"battery bay {V7['bay_D']:.0f}", [0, -40, 0])
    xi, xc, xd = x_in0 + V8["x_inv"], x_in0 + V8["x_charge"], x_in0 + V8["x_dist"]
    dim([x_in0 + V7["bay_D"], y, z], [xi, y, z], f"gap {V8['bay_gap']:.0f}", [0, -80, 0])
    dim([xi, y, z], [xc, y, z], f"inverter card + 12/1200 {xc - xi:.0f}", [0, -40, 0])
    dim([xc, y, z], [xd, y, z], f"charge card + MPPT {xd - xc:.0f}", [0, -80, 0])
    dim([xd, y, z], [x_in0 + in_D, y, z], f"distribution card {x_in0 + in_D - xd:.0f}", [0, -40, 0])
    dim([x_in0 - 30, y_in0 + V7["tray_w"] / 2, 0], [x_in0 - 30, y_in0 + V7["tray_w"] / 2, g.get("stack_top", 468)], f"stack {g.get('stack_top', 468):.0f} of {out_H:.0f}", [-40, 0, 0])
    dim([xi, out_W + 30, floor_top + 2], [xi, out_W + 30, floor_top + 2 + g.get("ch", in_H - 8)], f"cards {g.get('ch', in_H - 8):.0f} tall x {g.get('cw', in_W - 17):.0f} wide", [0, 40, 0])
    return D


def dims_v9():
    g = BS.get("_g8") or {}
    top = out_H + 40; D = []
    def dim(p1, p2, label, off): D.append(dict(a=p1, b=p2, label=label, off=off))
    dim([0, 0, top], [out_D, 0, top], f"depth {out_D:.0f} mm ({out_D / 25.4:.1f} in)", [0, -60, 0])
    dim([0, 0, top], [0, out_W, top], f"width {out_W:.0f} mm ({out_W / 25.4:.1f} in)", [-60, 0, 0])
    dim([out_D + 60, 0, 0], [out_D + 60, 0, out_H], f"height {out_H:.0f} mm ({out_H / 25.4:.1f} in)", [40, 0, 0])
    y = -30; z = 40
    xi = x_in0 + V8["x_inv"]
    dim([x_in0, y, z], [x_in0 + V7["bay_D"], y, z], f"battery bay + bus deck {V7['bay_D']:.0f}", [0, -40, 0])
    dim([x_in0 + V7["bay_D"], y, z], [xi, y, z], f"wiring gap {V8['bay_gap']:.0f}", [0, -80, 0])
    if P["deck"] == "full":
        fx0 = g.get("front_x0", xi + 23)
        dim([xi, y, z], [fx0, y, z], f"inverter card + slot {fx0 - xi:.0f}", [0, -40, 0])
        dim([fx0, y, z], [x_in0 + in_D, y, z], f"front deck plate {x_in0 + in_D - fx0:.0f}", [0, -80, 0])
    else:
        xc = x_in0 + V8["x_charge"]
        dim([xi, y, z], [xc, y, z], f"inverter card {xc - xi:.0f}", [0, -40, 0])
        dim([xc, y, z], [x_in0 + in_D - V8["front"], y, z], f"charge card {x_in0 + in_D - V8['front'] - xc:.0f}", [0, -80, 0])
        dim([x_in0 + in_D - V8["front"], y, z], [x_in0 + in_D, y, z], f"port grace {V8['front']:.0f}", [0, -40, 0])
    dz = g.get("deck_z", 468)
    dim([x_in0 - 30, y_in0 + 60, 0], [x_in0 - 30, y_in0 + 60, dz], f"rack + deck at {dz:.0f}", [-40, 0, 0])
    dim([x_in0 - 30, y_in0 + 60, dz], [x_in0 - 30, y_in0 + 60, out_H], f"{out_H - dz:.0f} over the deck", [-90, 0, 0])
    return D


CABLE_SPEC = [   # (run, Victron recommendation, fuse, connector)
    ("Battery stacks -> bus deck (per stack, 2 x 60Ah)", "6 AWG (SuperPack 60Ah: 30 A each; Victron M6 terminals)", "breaker per stack on the deck", "lugs on the deck bus bars"),
    ("Bus deck -> MultiPlus 12/1200", "4 AWG / 21 mm2 as built (Victron lists 35 mm2; 2 AWG did not fit the terminals), keep the run under 1 m", "150 A (Victron) at the deck", "Anderson SB175 with 4 AWG contacts"),
    ("Bus deck -> Orion XS 12/12-50 output", "6 AWG / 16 mm2 (Victron: 50 A, < 5 m)", "60-70 A", "Anderson SB50, 6 AWG contacts"),
    ("Alternator -> Orion XS input", "6 AWG, 60-70 A fuse at the start battery", "60-70 A", "Anderson SB50 at the front panel"),
    ("Bus deck -> MPPT 100/30 battery side", "10 AWG / 6 mm2 (Victron: 30 A)", "40 A", "Anderson SB50, 10 AWG contacts"),
    ("Solar array -> MPPT PV side", "10 AWG; PV fuse per Victron if > 1 string", "per string", "Anderson SB50 at the front panel"),
    ("Bus deck -> Garmin PowerSwitch feed", "10 AWG (Garmin: 50 A max on the PowerSwitch)", "60 A", "Anderson SB50, 10 AWG contacts"),
    ("Bus deck -> Cerbo GX", "16 AWG", "3 A", "Anderson Powerpole 15"),
    ("Garmin PowerSwitch outputs -> front-panel sockets", "10 AWG, one circuit per socket (Garmin: 30 A per channel max)", "Garmin's own per-channel protection", "Anderson Powerpole PP45 block (8 poles / 4 circuits) at the top of the charge card's front face; mates upward"),
    ("Shore AC in / inverter AC out", "12 AWG, per the MultiPlus AC in/out ratings", "AC breaker in the MultiPlus", "L14-30 inlet / outlet at the front panel"),
]


def report_v9():
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.2f} in)"
    g = BS.get("_g8") or {}; inv = COMPONENTS[P["inverter"]]
    if P["deck"] == "full":
        return report_v10()
    print("== Variant 'v9': v8 + a fixed bus deck on the battery rack; two cards, each unplugs and lifts out alone ==")
    print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}  -> {487.4 - out_W:.0f} mm ({(487.4 - out_W) / 25.4:.1f} in) narrower, "
          f"{762 - out_D:.0f} mm ({(762 - out_D) / 25.4:.1f} in) shorter in depth than the IceBox, same height")
    print(f"depth chain     : bay + deck {V7['bay_D']:.0f} | gap {V8['bay_gap']:.0f} | inverter card {P['card_t']:.0f}+10+{inv.d:.0f}+{V8['inv_gap']:.0f} "
          f"| charge card {P['card_t']:.0f}+{V8['charge_depth']:.0f}+{V8['charge_gap']:.0f} | front {V8['front']:.0f}")
    dz = g.get("deck_z", 468)
    print(f"bus deck        : printed 6 mm plate on the rack legs at {dz:.0f} mm, {out_H - dz:.0f} mm under the lid; carries bus bars, 2 breakers, shunt, "
          f"SB175 + 3 x SB50 receptacles at its front edge; hand window over the battery lugs")
    cw, ch = g.get("cw", in_W - 17), g.get("ch", in_H - 8)
    print(f"cards           : 2 x {mm(cw)} x {mm(ch)} solid printed tiles (cut down {CARD_TRIM:.0f} for wire room under the lid)")
    for name, layout in (("inverter", V9_INV_LAYOUT), ("charge", V9_CHARGE_LAYOUT)):
        for pl in layout:
            c = COMPONENTS[pl["comp"]]; bad = []
            if pl["y"] + c.w > cw: bad.append("Y overflow")
            if pl["z"] + c.h > ch: bad.append("Z overflow")
            print(f"  {name:8s} {c.name:20s} {c.w:>4.0f}x{c.h:>4.0f}x{c.d:>3.0f} @({pl['y']},{pl['z']}) {' '.join(bad) or 'ok'}")
    for pl in V9_DECK_LAYOUT:
        c = COMPONENTS[pl["comp"]]
        bad = []
        if pl["x"] + c.d > V7["bay_D"] - V7["end_gap"] + V7["leg"]: bad.append("X overflow")
        if pl["y"] + c.w > V7["bay_W"]: bad.append("Y overflow")
        if dz + 6 + c.h > out_H: bad.append("hits the lid")
        print(f"  deck     {c.name:20s} {c.d:>4.0f}x{c.w:>4.0f}x{c.h:>3.0f} @({pl['x']},{pl['y']}) {' '.join(bad) or 'ok'}")
    o175, o50 = 2 * HOUSING["sb175"] - MATED["sb175"], 2 * HOUSING["sb50"] - MATED["sb50"]
    dL = g.get("deck_L", 295)
    ch_ = in_H - 8 - CARD_TRIM
    z175, z50 = _conn_z("sb175_v"), _conn_z("sb50_v")
    print(f"connectors      : cards cut down {CARD_TRIM:.0f} mm to {ch_:.0f} tall; every card has its own fixed Anderson halves at the top of its rear face, mating face UP. "
          f"The mated pigtail halves top out {CONN_LID_ROOM:.0f} mm under the lid (their cables exit upward into that room). "
          f"Inverter card: SB175 housing at card z {z175:.0f}-{z175 + HOUSING['sb175']:.0f} ({ch_ - z175 - HOUSING['sb175']:.0f} below the card top). "
          f"Charge card: 5 x SB50 at z {z50:.0f}-{z50 + HOUSING['sb50']:.0f} ({ch_ - z50 - HOUSING['sb50']:.0f} below the card top): MPPT, Orion, Garmin+Cerbo, solar in, alternator in. "
          f"Pull-up travel {o175:.0f} / {o50:.0f} mm.")
    print(f"                  deck end: fixed halves point at the cards on the deck's {DECK_EXT:.0f} mm extension; pigtail halves pull forward "
          f"{o175:.0f}/{o50:.0f} mm: SB175 needs x<={115 + 2 * HOUSING['sb175'] - o175 + o175:.0f} of the deck's {dL:.0f} "
          f"({'ok' if 115 + 2 * HOUSING['sb175'] - o175 + o175 <= dL else 'TOO SHORT'}); SB50s need x<={160 + 2 * HOUSING['sb50'] - o50 + o50:.0f} "
          f"({'ok' if 160 + 2 * HOUSING['sb50'] - o50 + o50 <= dL else 'TOO SHORT'}); deck front edge to the inverter card {x_in0 + V8['x_inv'] - (g.get('deck_x0', 0) + dL):.0f} mm")
    print("== Battery rack (v9) ==")
    print(f"  trays: {V7['wall']:.0f} mm walls, {V7['lip']:.0f} mm lips, corner pads with M4 inserts for the leg foot tabs, one lengthwise 25 mm cam strap per battery (channel under the battery, slots through the end walls, buckle in the front wiring gap); 4 x M6 into the plate optional")
    print(f"  legs: 12 mm square, two segments on a half-lap at z {LEG_LAP[0]:.0f}-{LEG_LAP[1]:.0f}; lower stands on the plate with a foot tab M4'd into the tray pad; the shelf M4 at z {SHELF_SCREW_Z:.0f} passes through both lap halves; upper ends in a boss tab with an M4 insert 9 mm inside the deck edge")
    print(f"  deck ties: 2 printed brackets at the deck's back corners, T-nut into the corner bars + 2 x M4 through the deck -> the rack is a closed cell frame-trays-legs-deck-frame")
    print(f"  lift as a unit: each tray has 2 integral L tabs whose flanges lie on the outer bottom depth rail and bolt into its T-slot (1/4-20 T-nuts), "
          f"plus 2 printed L brackets (2 x M5 into pads on the back wall, T-nut into the back width rail); 4 T-nut bolts per tray carry the stack when the box is lifted by the frame")
    print(f"  guide posts: bottom foot steps down {T:.0f} mm past the floor panel and sits on the depth rail (T-nut on the slot centreline); top foot bolts up into the top rail")
    print(f"  legs: 8 x 12 mm ASA; they locate the shelves and carry the deck (~3 kg) in compression, and hang from the tray pads when the box is lifted")
    print(f"  shelves: 10 mm ring, 15 mm lip, {P['term_clear']:.0f} mm above the lower battery for the lugs; 4 x M4 through the end walls into the leg laps carry the upper battery")
    print(f"  per stack under 1 g braking: {2 * 7.5:.0f} kg sideways -> tray lip + 4 x M6 + strap; upper battery {7.5:.0f} kg -> shelf lip + 4 x M4 + strap")
    print("== Cables and connectors (Victron manuals) ==")
    for run, size, fuse, conn in CABLE_SPEC:
        print(f"  {run:48s} {size:52s} fuse {fuse:28s} {conn}")
    print("== Service ==")
    print("  lid off -> unplug the card's connectors on the deck -> lift the card. Batteries: unplug all, unbolt the deck, lift it, lift the batteries.")
    print(f"  est. mass ~{4 * 7.5 + 8.2 + 1.3 + 0.33 + 0.5 + 0.3 + 0.3 + 1.5 + 3.0 + 13.0:.0f} kg")


def report_v10():
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.2f} in)"
    g = BS.get("_g8") or {}; inv = COMPONENTS[P["inverter"]]
    print("== Variant 'v10': v9 with the bus deck run the length of the box; the charge card's units lie on the deck; one card (inverter) ==")
    print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}  -> {762 - out_D:.0f} mm ({(762 - out_D) / 25.4:.1f} in) shorter than the IceBox, "
          f"{661 - out_D:.0f} mm shorter than v9")
    print(f"depth chain     : bay {V7['bay_D']:.0f} | gap {V8['bay_gap']:.0f} | card {P['card_t']:.0f} + slot {V10['slot_front']:.0f} | front deck plate {V10['front_plate']:.0f} | 2")
    dz = g.get("deck_z", 468)
    print(f"deck            : {out_H - dz - P['card_t']:.0f} mm between the deck top and the lid; plates: rear 2 x 245 x 151, middle 2 x {g.get('deck_L', 0) - 245:.0f} x 151, "
          f"front 2 x {V10['front_plate']:.0f} x 151; slot {V10['slot_back']:.0f} + card + {V10['slot_front']:.0f} for the inverter card and its posts")
    zones = {"rear+middle": (g.get("deck_L", 312), V7["bay_W"]), "front": (V10["front_plate"], V7["bay_W"])}
    for zone, lay in (("rear+middle", V10_DECK_LAYOUT), ("front", V10_FRONT_LAYOUT)):
        L_, W_ = zones[zone]
        for pl in lay:
            c = COMPONENTS[pl["comp"]]; bad = []
            if pl["x"] + c.d > L_: bad.append("X overflow")
            if pl["y"] + c.w > W_: bad.append("Y overflow")
            if dz + P["card_t"] + c.h > out_H: bad.append("hits the lid")
            print(f"  {zone:12s} {c.name:20s} {c.d:>4.0f}x{c.w:>4.0f}x{c.h:>3.0f} @({pl['x']},{pl['y']}) {' '.join(bad) or 'ok'}  "
                  f"({out_H - dz - P['card_t'] - c.h:.0f} mm to the lid)")
    used = sum(COMPONENTS[pl["comp"]].d * COMPONENTS[pl["comp"]].w for pl in V10_DECK_LAYOUT + V10_FRONT_LAYOUT) + 2 * 120 * 60
    area = (g.get("deck_L", 312) + V10["front_plate"]) * V7["bay_W"]
    print(f"  deck area {area / 100:.0f} cm2, units + hand windows {used / 100:.0f} cm2 -> {100 * used / area:.0f} % covered")
    print("  caveats: Victron asks for the MPPT 100/30 (and prefers the Orion XS) mounted vertically for convection; flat on a deck in a closed box they will run hotter and the MPPT may derate.")
    print("  the MPPT, Orion, Cerbo and Garmin are now fixed to the deck: unscrew to service (no card, no Andersons for them); only the inverter card unplugs (SB175).")
    print(f"  the 7 mm problem: MPPT 186 + Orion 123 = 309 > {V7['bay_W']:.0f} deck width, so the Orion lives on the middle plate behind the card, not beside the MPPT.")
    print("== Cables and connectors (Victron manuals) ==")
    for run, size, fuse, conn in CABLE_SPEC:
        print(f"  {run:48s} {size:52s} fuse {fuse:28s} {conn}")


def report_v8():
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.2f} in)"
    g = BS.get("_g8") or {}; inv = COMPONENTS[P["inverter"]]
    print("== Variant 'v8': v7 battery bay + three cards ACROSS the box (inverter, charge, distribution) ==")
    print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}  -> {487.4 - out_W:.0f} mm ({(487.4 - out_W) / 25.4:.1f} in) narrower, "
          f"{762 - out_D:.0f} mm ({(762 - out_D) / 25.4:.1f} in) shorter in depth than the IceBox, same height")
    print(f"depth chain     : bay {V7['bay_D']:.0f} | gap {V8['bay_gap']:.0f} | inverter card {P['card_t']:.0f}+10+{inv.d:.0f}+{V8['inv_gap']:.0f} "
          f"| charge card {P['card_t']:.0f}+{V8['charge_depth']:.0f}+{V8['charge_gap']:.0f} | dist card {P['card_t']:.0f}+{V8['dist_depth']:.0f}+{V8['dist_gap']:.0f} | front {V8['front']:.0f}")
    print(f"kit bars: 4 width rails cut to {mm(out_W - 2 * C)} (4 of 16); from the IceBox: 4 height rails uncut, 4 depth rails cut to {mm(out_D - 2 * C)}; no cross-members")
    cw, ch = g.get("cw", in_W - 17), g.get("ch", in_H - 8)
    nx = int(-(-cw // LAT["tile_max"])); nz = int(-(-ch // LAT["tile_max"]))
    kind = "solid" if P["card_style"] == "solid" else "ribbed"
    print(f"cards           : 3 x {mm(cw)} wide x {mm(ch)} tall, printed {nx} x {nz} {kind} 6 mm tiles of {cw / nx:.0f} x {ch / nz:.0f} each "
          f"(~{nx * nz * (cw / nx) * (ch / nz) * 6 * 1.27e-3 * (1.0 if kind == 'solid' else 0.55):.0f} g PETG, ~{nx * nz * (2.3 if kind == 'solid' else 1.4):.0f} h per card); inverter {inv.w}x{inv.h} upright "
          f"({'fits' if inv.w + 13 <= cw and inv.h + 12 <= ch else 'DOES NOT FIT'})")
    for name, layout in (("inverter", V8_INV_LAYOUT), ("charge", V8_CHARGE_LAYOUT), ("dist", V8_DIST_LAYOUT)):
        for pl in layout:
            c = COMPONENTS[pl["comp"]]
            bad = []
            if pl["y"] + c.w > cw: bad.append("Y overflow")
            if pl["z"] + c.h > ch: bad.append("Z overflow")
            print(f"  {name:8s} {c.name:20s} {c.w:>4.0f}x{c.h:>4.0f}x{c.d:>3.0f} @({pl['y']},{pl['z']}) {' '.join(bad) or 'ok'}")
    print("== Attachment (printed cards) ==")
    inserts = {}
    for name, layout in (("inverter", V8_INV_LAYOUT), ("charge", V8_CHARGE_LAYOUT), ("dist", V8_DIST_LAYOUT)):
        for pl in layout:
            k = pl["comp"]; n = len(HOLES.get(k, []))
            print(f"  {name:8s} {COMPONENTS[k].name:20s} {n} holes: {FASTENER.get(k, 'verify')}")
            m = INSERT.get(k)
            if m: inserts[m] = inserts.get(m, 0) + n
    print(f"  heat-set inserts: " + ", ".join(f"{v} x {k}" for k, v in sorted(inserts.items())) + "; 4 x M6 through-bolts + 4 printed backing plates for the MultiPlus")
    print(f"  sockets in the front panel's lower band (z 50-110) in front of the distribution card, whose parts start at z=140")
    print(f"  bank 4 x SuperPack 60Ah = 240 Ah, 120 A; 12/1200 draws ~105 A; est. mass ~{4 * 7.5 + 8.2 + 1.3 + 0.33 + 0.5 + 0.3 + 0.3 + 1.5 + 4.0 + 14.0:.0f} kg")


def dims_v7():
    g = BS.get("_g7") or v7_geometry(); b = COMPONENTS["battery"]; inv = COMPONENTS[P["inverter"]]
    top = out_H + 40; D = []
    def dim(p1, p2, label, off): D.append(dict(a=p1, b=p2, label=label, off=off))
    dim([0, 0, top], [out_D, 0, top], f"depth {out_D:.0f} mm ({out_D / 25.4:.1f} in)", [0, -60, 0])
    dim([0, 0, top], [0, out_W, top], f"width {out_W:.0f} mm ({out_W / 25.4:.1f} in)", [-60, 0, 0])
    dim([out_D + 60, 0, 0], [out_D + 60, 0, out_H], f"height {out_H:.0f} mm ({out_H / 25.4:.1f} in)", [40, 0, 0])
    zc = g.get("stack_top", 480) + 20
    dim([x_in0 + 100, y_in0, zc], [x_in0 + 100, y_in0 + V7["bay_W"], zc], f"two stacks {V7['bay_W']:.0f} (batteries touching)", [0, 0, 30])
    dim([x_in0, -30, 40], [g["bay_x1"], -30, 40], f"battery bay {V7['bay_D']:.0f} deep", [0, -40, 0])
    dim([g["bar_x"], -30, 40], [g["bar_x"] + B, -30, 40], "cross-bar", [0, -80, 0])
    dim([g["card_x0"], -30, 40], [g["card_x0"] + g["card_L"], -30, 40], f"cards {g['card_L']:.0f} long", [0, -40, 0])
    xc = g["card_x0"] + 40; zc2 = floor_top + in_H - 20
    dim([xc, g["inv_lo"], zc2], [xc, g["inv_plate"], zc2], f"inverter {inv.d:.0f} + standoff", [0, 0, 30])
    dim([xc, g["dist_plate"] + P["card_t"], zc2], [xc, g["inv_lo"], zc2], f"gap {g['inv_lo'] - g['dist_plate'] - P['card_t']:.0f}", [0, 0, 60])
    dim([xc, g["parts_lo"], zc2], [xc, g["dist_plate"], zc2], "dist parts 48", [0, 0, 30])
    dim([xc, y_in0, zc2], [xc, g["parts_lo"], zc2], f"cable / Anderson space {g['spare_W']:.0f}", [0, 0, 60])
    dim([x_in0 - 30, y_in0 + V7["tray_w"] / 2, 0], [x_in0 - 30, y_in0 + V7["tray_w"] / 2, g.get("stack_top", 468)], f"stack {g.get('stack_top', 468):.0f} of {out_H:.0f}", [-40, 0, 0])
    return D


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
    for old in os.listdir(STL):          # part names carry positions; drop stale files from earlier layouts
        if old.endswith(".stl"):
            os.remove(os.path.join(STL, old))
    glb = os.path.join(OUT, "cage.glb"); a.export(glb, tolerance=1.5, angularTolerance=0.7)
    glb_to_json(glb, os.path.join(VIEWER, f"cage-{VARIANT}.json"))
    if P["card_plane"] in ("xz", "v7", "v8", "v9"):
        with open(os.path.join(VIEWER, f"dims-{VARIANT}.json"), "w") as f:
            json.dump({"xz": dims_bookshelf, "v7": dims_v7, "v8": dims_v8, "v9": dims_v9}[P["card_plane"]](), f)
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


def report_v7():
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.2f} in)"
    g = BS.get("_g7") or v7_geometry(); b = COMPONENTS["battery"]; inv = COMPONENTS[P["inverter"]]
    print("== Variant 'v7': IceBox-depth frame, two touching SuperPack stacks at the back, lengthwise cards in front ==")
    print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}  -> {487.4 - out_W:.0f} mm ({(487.4 - out_W) / 25.4:.1f} in) narrower "
          f"and {558.8 - out_H:.0f} mm ({(558.8 - out_H) / 25.4:.1f} in) shorter than the IceBox")
    print(f"kit bars: 4 width rails cut to {mm(out_W - 2 * C)} + 2 cross-members cut to {mm(in_W)} (6 of 16); "
          f"from the IceBox: 4 height rails {mm(out_H - 2 * C)} uncut, 4 depth rails cut from 711 to {mm(out_D - 2 * C)}")
    if P["card_style"] in ("lattice", "solid"):
        nx = int(-(-g["card_L"] // LAT["tile_max"])); nz = int(-(-(in_H - 8) // LAT["tile_max"]))
        kind = "solid" if P["card_style"] == "solid" else "ribbed"
        print(f"printed cards   : each card = {nx} x {nz} {kind} tiles of {g['card_L'] / nx:.0f} x {(in_H - 8) / nz:.0f} x {LAT['t']:.0f} mm "
              f"+ {3 * (nx - 1 + nz - 1)} splines; ~{nx * nz * (205 if kind == 'solid' else 110):.0f} g PETG and ~{nx * nz * (2.3 if kind == 'solid' else 1.4):.0f} h per card")
    st = g.get("stack_top", 2 * b.h + 4 + 2 * P["term_clear"] + P["shelf_t"])
    print(f"battery bay     : 2 stacks x {V7['tray_w']:.0f} = {V7['bay_W']:.0f} of {in_W:.0f} wide, {V7['bay_D']:.0f} deep, stack {st:.0f} of {out_H:.0f} tall to the lid ({out_H - st:.0f} spare)")
    print(f"cards           : {mm(g['card_L'])} long x {mm(in_H - 8)} tall; inverter {inv.w}x{inv.h} "
          f"({'fits' if inv.w <= g['card_L'] + 6 and inv.h + 12 <= in_H - 8 else 'DOES NOT FIT'}), "
          f"Y stack from the inboard wall: 17 | inverter {inv.d:.0f}+10 | {BS['gap']:.0f} | dist 52 | cable space {g['spare_W']:.0f}")
    for name, layout in (("inverter", V7_INV_LAYOUT), ("dist", V7_DIST_LAYOUT)):
        for pl in layout:
            c = COMPONENTS[pl["comp"]]
            bad = []
            if pl["x"] + c.w > g["card_L"] + 6: bad.append("X overflow")
            if pl["z"] + c.h > in_H - 8: bad.append("Z overflow")
            print(f"  {name:8s} {c.name:20s} {c.w:>4.0f}x{c.h:>4.0f}x{c.d:>3.0f} @({pl['x']},{pl['z']}) {' '.join(bad) or 'ok'}")
    print(f"  bank 4 x SuperPack 60Ah = 240 Ah (3.1 kWh), 120 A continuous; 12/1200 draws ~105 A at full output, charger 50 A (~4.8 h)")
    print(f"  lift: cards {mm(in_H - 8)} tall -> service from the top; batteries lift straight out of the bay")
    print(f"  est. mass ~{4 * 7.5 + 8.2 + 1.3 + 0.33 + 0.5 + 0.3 + 0.3 + 1.5 + 4.0 + 15.0:.0f} kg")


def report():
    if P["card_plane"] == "v9":
        return report_v9()
    if P["card_plane"] == "v8":
        return report_v8()
    if P["card_plane"] == "v7":
        return report_v7()
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


def clash_report(a: cq.Assembly, prefixes=("print_", "bar_", "battery_", "power_", "socket_", "victron_", "panel_", "lid_")):
    """Pairwise solid intersections between parts (bbox prefilter).  Anything over 1 mm3 is printed;
    judge the list by eye: a battery sitting in its tray should NOT appear, a leg inside a tray should."""
    parts = [(c.name, c.obj.val()) for c in a.children if any(c.name.startswith(p) for p in prefixes)]
    boxes = [(n, s.BoundingBox()) for n, s in parts]
    hits = []
    for i in range(len(parts)):
        ni, si = parts[i]; bi = boxes[i][1]
        for j in range(i + 1, len(parts)):
            nj, sj = parts[j]; bj = boxes[j][1]
            if bi.xmin > bj.xmax - 0.05 or bj.xmin > bi.xmax - 0.05 or bi.ymin > bj.ymax - 0.05 or bj.ymin > bi.ymax - 0.05 \
               or bi.zmin > bj.zmax - 0.05 or bj.zmin > bi.zmax - 0.05:
                continue
            try:
                v = si.intersect(sj).Volume()
            except Exception:
                v = -1
            if v > 1.0 or v < 0:
                hits.append((v, ni, nj))
    print(f"== Clash check: {len(parts)} parts, {len(hits)} overlapping pairs ==")
    for v, ni, nj in sorted(hits, reverse=True):
        print(f"  {v:10.0f} mm3  {ni}  x  {nj}")


if __name__ == "__main__":
    asm = build()
    report()
    if "--clash" in sys.argv:
        clash_report(asm)
    export(asm)
    print("wrote", os.path.abspath(os.path.join(VIEWER, f"cage-{VARIANT}.json")))
