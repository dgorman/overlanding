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
import plates   # print orientation + print plates for the exported STLs

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
    # v12: v5's frame (a second IceBox 1.3, same width and depth) cut to HALF the IceBox height.  Not card based: four
    # batteries in one layer at the back, a bus shelf in the column beside them, the MultiPlus on its long side on a
    # fixed plate at the front, the charge gear on printed mounts inside the side and front panels.  Lid off = full access.
    # v12 is cut at v13's height (282) with v13's front panel, so a v12 build upgrades to v13 by reprinting the trays, bus
    # shelf and inverter plate only: frame, panels, lid, posts, clips and the port strip carry over
    "v12": dict(frame_source="icebox", frame_W=487.4, frame_H=282.0, frame_D=762.0,
                batt_layout="v12", dist_forward=False, inverter="multiplus_1200_up", card_plane="v12", col_on_plate=True,
                card_style="solid", box="v13", batt="battery", inverter_long="multiplus_ii_long"),   # MultiPlus-II ordered 2026-10-14
    # v12s: the 12/1200 and two SuperPack 60Ah in the same interior cut to 620 deep (24.4 in): the charge gear stacks on the plate.
    # No upgrade path (the MultiPlus-II and the 200Ah pair both need the full 762)
    # v12s: the build. The donor IceBox is the 25 in model (635 deep), so the depth rails go in UNCUT; only the height rails are cut
    "v12s": dict(frame_source="icebox", frame_W=488.1, frame_H=281.7, frame_D=571.5, bar=25.0, cube=25.75, shelf_end_len=584.2 / 3, garmin_hanger=True, gx_touch=True,   # AS BUILT 2026-10-30: 25 mm metric rails,
                 batt_layout="v12", dist_forward=False, inverter="multiplus_1200_up", card_plane="v12", col_on_plate=True,
                 card_style="solid", box="v13", batt="battery", inverter_long="multiplus_1200_long", stack_on_icebox=True,
                 perforated_back=True, clean_trays=True, plate_pilots=True, icebox_front="side", breaker_shelf=True, lap_bolts=False, tray_clr=0.5, strap=False, batt_body_h=208.0, shelf_pad=3.0, shelf_drop=2.0),   # front panel = a SOLID offcut of an IceBox side panel   # the IceBox's slot pattern on the back panel; trays without the unused
                                                                               # pads and floor holes; insert pilot holes in the plate under every unit
    # v12s_pack: v12s on the IceBox with pack2 standing on the floor in front of the box's port face, umbilical side toward it
    "v12s_pack": dict(frame_source="icebox", frame_W=488.1, frame_H=281.7, frame_D=571.5, bar=25.0, cube=25.75, shelf_end_len=584.2 / 3, garmin_hanger=True, gx_touch=True,   # 25.75 cubes, height rails 230.2, depth rails 520.0 (22.5 in)
                      batt_layout="v12", dist_forward=False, inverter="multiplus_1200_up", card_plane="v12", col_on_plate=True,
                      card_style="solid", box="v13", batt="battery", inverter_long="multiplus_1200_long", stack_on_icebox=True,
                      perforated_back=True, clean_trays=True, plate_pilots=True, icebox_front="side", breaker_shelf=True, lap_bolts=False, tray_clr=0.5, strap=False, batt_body_h=208.0, shelf_pad=3.0, shelf_drop=2.0, with_pack2=True),
    # pack2: the stacked add-on pack for v12s: 2 x 2 SuperPack 60Ah (two pairs, one above the other) in an all-printed cage,
    # bus bars + one breaker on a top shelf, SB175 umbilical inlet in its back panel.  Standalone model (frame_* = the pack's envelope)
    "pack2": dict(frame_source="icebox", frame_W=314.0, frame_H=572.0, frame_D=325.0, show_icebox=False,
                  batt_layout="v12", dist_forward=False, inverter="multiplus_1200_up", card_plane="pack2", col_on_plate=True,
                  card_style="solid"),
    "v12_1200": dict(frame_source="icebox", frame_W=487.4, frame_H=282.0, frame_D=762.0,            # the same with the 12/1200 (reference)
                     batt_layout="v12", dist_forward=False, inverter="multiplus_1200_up", card_plane="v12", col_on_plate=True,
                     card_style="solid", box="v13", batt="battery", inverter_long="multiplus_1200_long"),
    "v12_4batt": dict(frame_source="icebox", frame_W=487.4, frame_H=282.0, frame_D=762.0,   # the earlier v12 interior: 2 x 2 SuperPacks
                      batt_layout="v12", dist_forward=False, inverter="multiplus_1200_up", card_plane="v12", col_on_plate=True,
                      card_style="solid"),
    # v13: v12s with the lid panel captured in the 4 top rails' inner-face slots (z = 266.2 .. 272.2 mm), freeing the top rail
    # slots completely: symmetric U-bridge breaker shelves bolt down into both 14 mm tray side walls, the inverter plate (z 14..264)
    # sits in buttressed single-piece bottom-rail posts (no top clips), and the Garmin PowerSwitch + wire tie-down plate is a
    # single-piece 254 mm standing panel bolted to the bottom inboard rail.
    "v13": dict(frame_source="icebox", frame_W=488.1, frame_H=281.7, frame_D=571.5, bar=25.0, cube=25.75, shelf_end_len=584.2 / 3, garmin_hanger=True, gx_touch=True,
                batt_layout="v12", dist_forward=False, inverter="multiplus_1200_up", card_plane="v12", col_on_plate=True,
                card_style="solid", box="v13", batt="battery", inverter_long="multiplus_1200_long", stack_on_icebox=True,
                perforated_back=True, clean_trays=True, plate_pilots=True, icebox_front="side", breaker_shelf=True, lap_bolts=False, tray_clr=0.5, strap=False, batt_body_h=208.0, shelf_pad=3.0, shelf_drop=2.0, lid_slot=True),
    # v13_ii: v12 one inch taller for a 1500 W AC load: MultiPlus-II 12/3000 on its long side along the inboard side, two
    # Lithium Smart 200Ah end to end along the outboard side, the bus column between them
    "v13_ii": dict(frame_source="icebox", frame_W=487.4, frame_H=282.0, frame_D=762.0,
                   batt_layout="v12", dist_forward=False, inverter="multiplus_1200_up", card_plane="v12", col_on_plate=True,
                   card_style="solid", box="v13", batt="smart200", inverter_long="multiplus_ii_long"),
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
               card_style="solid", post_standoff=18.0, post_standoff_out=48.0, post_standoff_in=0.0, extra_width=12.0, deck="column"),
    "v11": dict(frame_source="icebox", frame_W=487.4, frame_H=558.8, frame_D=762.0,
               batt_layout="v9", dist_forward=False, inverter="multiplus_1200_up", leg=12.0,
               card_plane="v9", column=["battery", "battery"], arrange="2x2", col_on_plate=True,
               narrow=True, tray_for="battery", align="right", height="icebox", depth="fit11",
               card_style="solid", post_standoff=18.0, post_standoff_out=69.0, post_standoff_in=0.0, extra_width=33.0, deck="column", swap=True, term_clear=30.0),
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
    stack_on_icebox=False,   # True: draw the IceBox UNDER the box with the two rear faces flush (the box's port face and the IceBox's back panel)

    bar=25.4,            # Goose Gear MaxLite 1" extrusion (profile verify)
    cube=25.4,           # printed 3-way corner cube
    panel_t=6.0,         # panels: phenolic-faced ply (confirmed), 6 mm assumed; screwed to the OUTSIDE
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
    post_standoff_out=None, post_standoff_in=None,   # per-side overrides (v10: 48 / 0 shifts the inverter card inboard, freeing an 82 mm port bay outboard)
    extra_width=0.0,     # v10: widen the frame beyond the two trays so the SB175 pack inlet fits sideways beside the inverter
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
P.setdefault("deck", "cards")      # "column": v10, one battery stack + the charge card lengthwise beside it
P.setdefault("swap", False)        # v11: the MultiPlus takes the column, the charge gear takes the front card
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
    "multiplus_1200_long": Comp("victron_multiplus", 101, 375, 249, "MultiPlus 12/1200 on its long side along the box's depth (v12 on the v13 plate)"),
    "multiplus_ii_long": Comp("victron_multiplus", 148, 578, 277, "MultiPlus-II 12/3000/120-50 120V (578 x 277 x 148, 19 kg) on its long side along the box's depth, back on a plate, cable end forward"),
    "multiplus_4k": Comp("victron_multiplus", 631, 164, 277, "MultiPlus-II 12/4k/160-50 120V on its side (22 kg) - 631 long"),
    "mppt":      Comp("victron_mppt", 186, 70, 130, "SmartSolar MPPT 100/30, upright, terminals down (1.3 kg)"),
    "orion":     Comp("victron_orion", 123, 40, 137, "Orion XS 12/12-50A, upright, terminals down (0.33 kg)"),
    "cerbo":     Comp("victron_cerbo", 154, 48, 78, "Cerbo GX"),
    "cerbo_flat": Comp("victron_cerbo", 78, 154, 48, "Cerbo GX flat on a deck, mounting lugs down, connectors on the long edges"),
    "garmin":    Comp("garmin_powerswitch", 125, 32, 75, "Garmin PowerSwitch"),
    "garmin_up": Comp("garmin_powerswitch", 75, 32, 125, "Garmin PowerSwitch turned 90 deg"),
    "multiplus_1200_side": Comp("victron_multiplus", 375, 101, 249, "MultiPlus 12/1200 on its LONG side (v12 half-height box): 375 along the box's width, 249 tall"),
    "mppt_up":   Comp("victron_mppt", 130, 70, 186, "MPPT 100/30 upright on a side-panel mount, terminals down"),
    "shunt":     Comp("power_shunt", 120, 46, 54, "SmartShunt 500A"),
    "busbar_p":  Comp("power_busbar_pos", 155, 35, 32, "5-stud covered bus bar (+)"),
    "busbar_n":  Comp("power_busbar_neg", 155, 35, 32, "5-stud covered bus bar (-)"),
    "breaker_face": Comp("power_breaker", 81.28, 37.85, 48.13, "Bussmann 285 on the inverter plate's column face, long axis along the depth, lever outward"),
    "breaker_a": Comp("power_breaker_a", 48.13, 81.28, 37.85, "Eaton Bussmann 285150F-121-S Hi-Amp 150 A surface mount (owner's, 2026-10-24; was the 60 A 285060F): 81.28 long x 48.13 wide, 31.5 tall + 6.35 push-to-trip button, 1/4-28 studs; long axis along the depth"),
    "breaker_b": Comp("power_breaker_b", 48.13, 81.28, 37.85, "second Bussmann 285, long axis along the depth"),
    "garmin_edge": Comp("garmin_powerswitch", 32, 125, 75, "Garmin PowerSwitch on edge on a printed angle, long axis along the depth"),
    "anderson":  Comp("socket_anderson", 48, 10, 36, "Anderson SB50 panel mount, solar in (verify hole 48 x 36)"),
    "sb175":     Comp("socket_sb175", 79, 56, 26, "Anderson SB175 housing (Anderson STEP 55.6 x 79.4 x 25.5), 4 AWG contacts, inverter DC; mates along its 79 mm axis, laid across the deck"),
    "sb50":      Comp("socket_sb50", 48, 37, 16, "Anderson SB50 housing (Anderson STEP 36.5 x 48 x 16), 6-12 AWG contacts; mates along its 48 mm axis, laid across the deck"),
    "sb175_x":   Comp("socket_sb175", 56, 79, 26, "Anderson SB175 on the deck, mating axis along the depth (+X)"),
    "sb50_x":    Comp("socket_sb50", 37, 48, 16, "Anderson SB50 on the deck, mating axis along the depth (+X)"),
    "sb175_v":   Comp("socket_sb175", 56, 26, 79, "Anderson SB175 standing on a card's rear face, mating face up"),
    "sb175_h":   Comp("socket_sb175", 79, 26, 56, "Anderson SB175 lying on a lengthwise card's face above the MultiPlus, mating forward (+X)"),
    "sb50_v":    Comp("socket_sb50", 37, 16, 48, "Anderson SB50 standing on a card face, mating face up"),
    "shunt_x":   Comp("power_shunt", 46, 120, 35, "SmartShunt 500A lying on the shelf, studs up and toward the trays. Housing-only envelope: the cached STEP body drops the "
                                                 "studs (46.5 tall with them) and the 6.4 mm side connector (52.5 deep with it); the mounting slots are on the stud line, 12.5 from the stud edge"),
    "shunt_up":  Comp("power_shunt", 54, 46, 120, "SmartShunt standing on end on a card"),
    "shunt_y":   Comp("power_shunt", 120, 54, 46, "SmartShunt on the deck, long axis across the box"),
    "busbar_px": Comp("power_busbar_pos", 35, 155, 32, "5-stud covered bus bar (+), along the depth"),
    "gnd_bus":   Comp("power_busbar_gnd", 77, 25, 47, "Blue Sea 2701 DualBus 100 A (2 x 5 #8-32, 76.5 x 46.5 base) on the lower Garmin hanger plate: the common negative for the Garmin's port circuits"),
    "busbar_nx": Comp("power_busbar_neg", 35, 155, 32, "5-stud covered bus bar (-), along the depth"),
    "garmin_flat": Comp("garmin_powerswitch", 125, 75, 32, "Garmin PowerSwitch lying on the bus deck"),
    "garmin_flat_x": Comp("garmin_powerswitch", 75, 125, 32, "Garmin PowerSwitch lying flat on the bus shelf, long axis along the depth"),
    "pp45_x":    Comp("socket_pp45", 32, 25, 16, "Anderson Powerpole PP45 block on the deck's front edge, mating +X; Garmin outputs to the socket harness"),
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
if P["narrow"] and P["card_plane"] in ("v7", "v8", "v9"):
    _b = COMPONENTS["battery"]
    V7 = dict(wall=(6.0 if P["card_plane"] == "v9" else 4.0), leg=P.get("leg", 9.0), end_gap=15.0, bay_slack=2.0, bar_gap=5.0,
              lip=(30.0 if P["card_plane"] == "v9" else 20.0))   # v9 rack: 6 mm walls, 30 mm lips, 12 mm split legs
    V7["tray_w"] = _b.w + 2 * V7["wall"]                          # 146
    V7["bay_W"] = 2 * V7["tray_w"] + V7["bay_slack"]              # two touching stacks
    V7["bay_D"] = V7["end_gap"] + _b.d + 2 * V7["wall"] + V7["leg"]  # back gap (leg inside) + tray + front leg
    out_W = round(B + V7["bay_W"] + B + P["extra_width"], 1)
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
        V8["bay_gap"] = 20.0     # deck front edge is 10 mm inside the bay; the card's rear SB175 flying half (26 deep) clears it by 4
        V8["front"] = 10.0       # MPPT (the deepest unit) is at the TOP of the charge card; the panel-mounted sockets and
        V8["charge_gap"] = 4.0   # inlets all sit in the bottom band, where the card is empty, so the front grace is only
        V8["inv_gap"] = 22.0     # the MPPT's own clearance.  inv_gap: the charge card's rear-face SB50s (16 deep) + 6
        V8["x_inv"] = V7["bay_D"] + V8["bay_gap"]
        V8["x_charge"] = V8["x_inv"] + P["card_t"] + 10.0 + _inv.d + V8["inv_gap"]
        in_D = round(V8["x_charge"] + P["card_t"] + V8["charge_depth"] + V8["charge_gap"] + V8["front"], 1)
        out_D = in_D + 2 * B
    if P["depth"] == "fit10":
        # v10: two batteries in ONE stack; the charge card stands lengthwise in the freed column beside it, so
        # nothing but the inverter card is in front of the bay.  Ports go above the MultiPlus.
        _inv = COMPONENTS[P["inverter"]]
        V10 = dict(post_dx=16.0, post_standoff=12.0)   # column card posts: 16 (X) x post_w (Y), 12 off the inboard rail (SB50 room behind the card)
        V8["bay_gap"] = 10.0     # the inverter card's own posts' feet clear the rack's front leg tabs; the SB175 sits beside the deck
        V8["inv_gap"] = 0.0
        V8["front"] = 8.0
        V8["x_inv"] = V7["bay_D"] + V8["bay_gap"]
        V8["x_charge"] = None
        in_D = round(V8["x_inv"] + P["card_t"] + 10.0 + _inv.d + V8["front"], 1)
        out_D = in_D + 2 * B
    if P["depth"] == "fit11":
        # v11: v10 swapped.  The MultiPlus stands lengthwise in the column beside the stack (card 6 + feet 10 + 101 + 30
        # behind for its SB175 = 147 of the 163 mm column); the charge card is the front card, so the front zone is only
        # the MPPT's 70 + its rear SB50 row.
        V10 = dict(post_dx=16.0, post_standoff=21.0)   # column posts 21 off the inboard rail: 30 mm behind the card for its SB175, mating up
        V8["bay_gap"] = 28.0     # the charge card's rear-face SB50s (16) + 12: the 17.25 in (438 mm) limit is spent here (+6, which also
        V8["inv_gap"] = 0.0      #   lets the column card reach 264 so the flush MultiPlus clears the posts' 7 mm slot lips) ...
        V8["front"] = 11.0       # ... and in front of the MPPT (+1): 437.8 outer
        V8["x_inv"] = V7["bay_D"] + V8["bay_gap"]      # (x_inv is reused as the front card's rear face)
        V8["x_charge"] = None
        in_D = round(V8["x_inv"] + P["card_t"] + V8["charge_depth"] + 4.0 + V8["front"], 1)
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
if P["card_plane"] == "v12":
    ANDERSONS = []
    SOCKETS = []
if P["card_plane"] in ("v8", "v9"):
    ANDERSONS = []
    SOCKETS = [(40, 29), (85, 29), (130, 29), (175, 22), (215, 22)]   # lower band of the front panel
    P["socket_z"] = 90.0 if P["card_plane"] == "v9" else 80.0
    if P.get("deck") == "column":
        P["socket_z"] = 482.0   # v10: socket row above the MultiPlus (top at 428), 60 mm under the lid
# v9 front panel, bottom band (nothing deeper than the empty card band behind it): L14-30 shore inlet + inverter outlet
# (60 mm dia, 55 deep) and the two SB50 panel inlets for solar and alternator (37 x 48 face, 48 deep).  (y, z) from the
# inner corner; the 12 V / USB socket row sits above them at socket_z.
FRONT_INLETS = [("l14_30_in", 50, 34), ("l14_30_out", 120, 34), ("sb50_solar", 190, 9), ("sb50_alt", 240, 9)]
SIDE_PORTS = []
FRONT_PORTS = []   # v10: every external port in ONE VERTICAL LINE on the front panel, in the strip beside the inverter
if P.get("deck") == "column":
    # The inverter card is pushed inboard (posts 36 / 0 off the rails) so a 44 mm strip opens between the outboard corner bar
    # and the MultiPlus's side.  Ports stack there top to bottom; their bodies sit beside the inverter, never in its lift path.
    # 44 mm is too narrow for L14-30 twist-locks (63 mm flange): the MultiPlus 12/1200 is a 16 A unit, so the AC in/out are
    # IEC C20 inlet / C19 outlet (24 x 32 faces).  (kind, y centre from the outboard panel face, z centre absolute)
    FRONT_INLETS = []
    SOCKETS = []
    FRONT_PORTS = []
    # Ports on the y=0 SIDE WALL beside the inverter, bodies pointing +Y at the MultiPlus's side (82 mm away): between the
    # depth rails there is no corner bar, so the whole gap is usable; x between the inverter card's post (318) and the front
    # corner bar (429).  Everything fits, including the L14-30s (63 mm flange, 55 deep) and the SB175 (79 deep).
    # (side, kind, x, z, dia) - x/z are centres for round ports, lower-left corners for rectangular faces, absolute mm.
    SIDE_PORTS = [("out", "l14_30_in", 373, 65), ("out", "l14_30_out", 373, 135),
                  ("out", "sb50_solar", 335, 175), ("out", "sb50_alt", 380, 175),
                  ("out", "socket", 350, 250, 29), ("out", "socket", 395, 250, 29), ("out", "socket", 350, 290, 29),
                  ("out", "socket", 395, 290, 22), ("out", "socket", 372, 330, 22),
                  ("out", "sb175_pack", 360, 420)]
if P.get("swap"):   # v11: every port on the FRONT face, in the 78 mm strip between the pedal-side corner bar and the front card
    # (the card is pushed to the inboard rail: posts 69 / 0).  Front-facing ports work whichever side of the truck the IceBox is on.
    # Bodies sit beside the card, 80 mm clear of its guide post; nothing is in front of the MPPT.  (kind, y centre, z centre)
    SIDE_PORTS = []
    FRONT_PORTS = [("sb175_pack", 64, 68),
                   ("socket", 47, 130, 29), ("socket", 82, 130, 29), ("socket", 47, 170, 29), ("socket", 82, 170, 22), ("socket", 64, 210, 22),
                   ("sb50_solar", 64, 274), ("sb50_alt", 64, 330),
                   ("l14_30_in", 64, 400), ("l14_30_out", 64, 470)]
PORT_FACE = {"sb175": (26.0, 56.0, 79.0), "sb50": (37.0, 48.0, 48.0), "iec": (24.0, 32.0, 50.0)}   # (w, h, depth), face centred
if P["card_plane"] == "v12":   # v12 and v13 share one front panel: the port strip is the INBOARD 150 mm, three columns, under the top rail
    FRONT_PORTS = [("l14_30_in", 423, 65), ("l14_30_out", 423, 135), ("socket", 423, 190, 29),            # (v13's batteries run the outboard
                   ("sb50_solar", 370, 60), ("sb50_alt", 370, 116), ("socket", 370, 160, 22), ("socket", 370, 193, 22),   # side to the front; its plate's
                   ("socket", 338, 150, 29), ("socket", 338, 190, 29)]                                                   # front post ends at y 315)
if P.get("icebox_front") in ("bezel", "side"):   # v12s port strip: the same nine ports with 5 mm more between the SB50s and the socket columns
    FRONT_PORTS = [("l14_30_in", 423, 72), ("l14_30_out", 423, 142), ("socket", 423, 197, 29),
                   ("sb50_solar", 370, 62), ("sb50_alt", 370, 118), ("socket", 370, 162, 22), ("socket", 370, 195, 22),
                   ("socket", 338, 157, 29), ("socket", 338, 197, 29),
                   ("sb175_pack", 215, 110)]   # umbilical inlet for the add-on pack, in front of the bus column, clear of the breakers on the plate
INLET_BODY = {"l14": (60.0, 55.0), "sb50": (48.0, 37.0, 48.0), "sb175": (79.0, 56.0, 26.0)}   # (dia, depth) or (depth, w, h)
N_BATT = 4
post_h = in_H                                          # floor panel top to the underside of the top rails


def box(w, d, h, at=(0, 0, 0)):
    return cq.Workplane("XY").box(w, d, h, centered=False).translate(at)


STEP_DIR = os.path.join(HERE, "step")
STEP_FILES = {   # component key -> Victron STEP file (downloaded into cad/step/, see components.md)
    "multiplus_ii": "MultiPlus-II-12-3000-120V.step",
    "multiplus_ii_long": "MultiPlus-II-12-3000-120V.step",
    "multiplus_1200_long": "MultiPlus-12-1200-120V.step",
    "multiplus":    "MultiPlus-12-800-120V.step",
    "multiplus_1200": "MultiPlus-12-1200-120V.step",
    "multiplus_1200_up": "MultiPlus-12-1200-120V.step",
    "multiplus_1200_side": "MultiPlus-12-1200-120V.step",
    "mppt_up":      "SmartSolar-MPPT-100-30.step",
    "cerbo_up":     "Cerbo-GX.step",
    "smart200":     "Lithium-Smart-12.8V-160Ah-200Ah.step",
    "smart100":     "Lithium-Smart-12.8V-100Ah.step",
    "battery":      "Lithium-SuperPack-12.8V-60Ah.step",
    "mppt":         "SmartSolar-MPPT-100-30.step",
    "orion":        "Orion-XS-12-12-50A.step",
    "cerbo":        "Cerbo-GX.step",
    "cerbo_flat":   "Cerbo-GX.step",
    "shunt":        "SmartShunt-500A.step",
    "bms":          "VE.Bus-BMS-V2.step",
    "sb175":        "anderson_sb175_housing.stp",
    "sb50":         "anderson_sb50_housing.stp",
    "sb175_x":      "anderson_sb175_housing.stp",
    "sb50_x":       "anderson_sb50_housing.stp",
    "sb175_v":      "anderson_sb175_housing.stp",
    "sb175_h":      "anderson_sb175_housing.stp",
    "sb50_v":       "anderson_sb50_housing.stp",
    "shunt_x":      "SmartShunt-500A.step",
    "shunt_up":     "SmartShunt-500A.step",
    "shunt_y":      "SmartShunt-500A.step",
    "breaker_a":    "BlueSea-7148.step",   # download from bluesea.com product 7148 (Technical Documents > CAD), save under cad/step/
    "breaker_face": "BlueSea-7148.step",
    "breaker_b":    "BlueSea-7148.step",
}
MATED = {"sb175": 133.4, "sb50": 81.3, "sb175_x": 133.4, "sb50_x": 81.3, "sb175_v": 133.4, "sb50_v": 81.3, "pp45_v": 41.0, "pp45_x": 41.0, "sb175_h": 133.4}   # Anderson mated-pair lengths
HOUSING = {"sb175": 79.4, "sb50": 48.0, "pp45": 24.6}   # housing length along the mating axis
_STEP_CACHE = {}
# extra rotation (axis, degrees) applied after the extents match, for units
# the matcher lands upside down or backwards; checked in the renders
STEP_FLIP = {"mppt": ("x", 180),   # 180 about the card axis: fins to the card, terminals down
             "shunt_x": ("x", 180)}   # base plate down, studs up and toward -y (the trays); the extents match put it base-up, studs inboard (2026-11-01)


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


def breaker_shape(dx, dy, dz, at):
    """Eaton Bussmann 285-series Hi-Amp breaker (285150F-121-S) from the series drawing (no STEP published): an 8.13 mm base
    flange with the two mounting holes at the lower-left / upper-right corners, the body to 31.5, square stud insulators at
    the other two corners with the 1/4-28 studs inside, the push-to-trip button 6.35 above the body at mid-length, and the
    yellow reset lever standing out ~10 mm from the -dy side at mid-length (keep that side clear).  dx is the 81.28 length,
    dy the 48.13 width; holes are HOLES["breaker_a"] = (12.32, 10.73) and (68.96, 37.40)."""
    bh = dz - 6.35; base_h = 8.13
    base = box(dx, dy, base_h, at).edges("|Z").fillet(5)
    body = box(dx - 6, dy - 4, bh - base_h, (at[0] + 3, at[1] + 2, at[2] + base_h)).edges("|Z").fillet(7)
    shp = base.union(body)
    for (u, v) in ((12.32, 10.73), (dx - 12.32, dy - 10.73)):                      # the two 6.6 mm mounting holes through the flange, in
        shp = shp.cut(cq.Workplane("XY").center(at[0] + u, at[1] + v).circle(3.3).extrude(base_h + 2).translate((0, 0, at[2] - 1)))
        shp = shp.cut(cq.Workplane("XY").center(at[0] + u, at[1] + v).circle(7.0).extrude(dz).translate((0, 0, at[2] + base_h)))   # corner wells
    for (ex, ey) in ((14, dy / 2 + 13.33), (dx - 14, dy / 2 - 13.33)):            # stud insulators (16 sq) on the opposite diagonal, studs inside
        cap = box(16, 16, 9, (at[0] + ex - 8, at[1] + ey - 8, at[2] + bh - 1)).edges("|Z").fillet(2)
        stud = cq.Workplane("XY").center(at[0] + ex, at[1] + ey).circle(3.2).extrude(14).translate((0, 0, at[2] + bh - 2))
        shp = shp.union(cap).union(stud)
    button = box(12, 8, 6.35, (at[0] + dx / 2 - 6, at[1] + dy / 2 - 4, at[2] + bh)).edges("|Z").fillet(2)
    lever = box(14, 10 + 4, 6, (at[0] + dx / 2 - 7, at[1] - 10, at[2] + bh - 12)).edges("|Z").fillet(2)   # reset lever out of the -y side
    return shp.union(button).union(lever)


def unit_fallback(key, dx, dy, dz, at, axis="|Z", face=False):
    if key.startswith("breaker") and face:   # on a vertical plate at +y: build it flat (studs up), turn the studs toward -y
        shp = breaker_shape(dx, dz, dy, (0, 0, 0)).rotate((0, 0, 0), (1, 0, 0), 90)
        bb = shp.val().BoundingBox()
        return shp.translate((at[0] - bb.xmin, at[1] - bb.ymin, at[2] - bb.zmin))
    return breaker_shape(dx, dy, dz, at) if key.startswith("breaker") else box(dx, dy, dz, at).edges(axis).fillet(3)


def victron_shape(key, dx, dy, dz, at, fallback, flip=None, lugs=None):
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
    for fl in (STEP_FLIP.get(key), flip):   # the STEP's own fix-up, then the caller's (mount on the unit's far side)
        if fl is None:
            continue
        ax, deg = fl
        axis = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[ax]
        best = best.rotate((0, 0, 0), axis, deg); best_bb = best.BoundingBox()
    if lugs:   # ("y", +1): the mounting-lug face (the end slab that spans the unit's full outline) must be at +y; else turn 180 about the vertical
               # (a 6 mm slab: the MultiPlus 12/1200's keyhole tabs sit 4 mm inside its fan guard, and a 3 mm slab missed them)
        ax, side = lugs
        i = "xyz".index(ax)
        def slab_fill(end):
            lo = [best_bb.xmin, best_bb.ymin, best_bb.zmin]; hi = [best_bb.xmax, best_bb.ymax, best_bb.zmax]
            lo2, hi2 = list(lo), list(hi)
            if end < 0: hi2[i] = lo[i] + 6.0
            else: lo2[i] = hi[i] - 6.0
            sl = cq.Workplane("XY").box(hi2[0] - lo2[0], hi2[1] - lo2[1], hi2[2] - lo2[2], centered=False).translate(tuple(lo2)).val()
            b = best.intersect(sl).BoundingBox()
            ext = [b.xlen, b.ylen, b.zlen]; full = [hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]]
            return sum(ext[j] / full[j] for j in range(3) if j != i)
        if slab_fill(side) < slab_fill(-side):
            spin = (0, 0, 1) if ax != "z" else (1, 0, 0)
            best = best.rotate((0, 0, 0), spin, 180); best_bb = best.BoundingBox()
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
def guide_post_segments(foot_dir="y", foot_hole=None, standoff=None):
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
                S = P["post_standoff"] if standoff is None else standoff
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
    # the IceBox's top panel sits IN its top rails' centreline slots (confirmed 2026-10-21): its surface is B/2 - 3 = 9.7 mm
    # below the rail tops, so a box stacked on it stands rail on rail and nothing inside the box can bear on the lid
    parts.append(("icebox_panel_top", box(D - 2 * B + 6, W - 2 * B + 6, T, (x0 + B - 3, B - 3, H - B / 2 - 3))))
    parts.append(("icebox_panel_floor", box(D - 2 * B + 6, W - 2 * B + 6, T, (x0 + B - 3, B - 3, B / 2 - 3))))
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
    if P["stack_on_icebox"]:   # the box rides on the IceBox's deck: its port face flush with the IceBox's back panel
        parts = [(nm, shp.translate((out_D + P["icebox_gap"], 0, -H))) for nm, shp in parts]
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
    if P["card_plane"] == "pack2":
        build_pack2(a)
        return a

    # --- frame ---------------------------------------------------------------
    cube = corner_cube()
    for i, x in enumerate((0, out_D - C)):
        for j, y in enumerate((0, out_W - C)):
            for k, z in enumerate((0, out_H - C)):
                add(a, cube.translate((x, y, z)), (f"cube_{i}{j}{k}" if P["frame_source"] == "icebox" else f"print_cube_{i}{j}{k}"), BLACK)   # the IceBox's own cubes
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
    if P["card_plane"] not in ("v7", "v8", "v9", "v12"):
        floor = box(out_D, out_W, T, (0, 0, B))
        if P["col_on_plate"]:   # open floor under the battery column; trays sit on the Goose Gear plate
            floor = floor.cut(box(in_D, 200, T + 2, (x_in0, y_in0, B - 1)))
        add(a, floor, "panel_floor", PANEL)
    if P["card_plane"] != "v12":   # v12 builds its own slot-captured panels
        add(a, box(out_D, out_W, T, (0, 0, out_H)), "lid_panel", PANEL)
        for y in (out_W * 0.3, out_W * 0.7):
            add(a, lid_handle().translate((out_D / 2 - 6, y - 30, out_H + T)), f"lid_handle_{int(y)}", BLACK)
        outboard = box(out_D, T, out_H, (0, -T, 0))
        for port in SIDE_PORTS:   # v10: bodies point +Y from the y=0 wall's inner face, at the inverter's side
            if port[0] != "out":
                continue
            kind, x, z = port[1], port[2], port[3]
            if kind == "socket":
                r = port[4] / 2
                outboard = outboard.cut(cq.Workplane("XZ").center(x, z).circle(r).extrude(T + 2).translate((0, 1, 0)))
                add(a, cq.Workplane("XZ").center(x, z).circle(r + 3).extrude(-40), f"socket_{int(x)}_{int(z)}", (0.3, 0.3, 0.3))
            elif kind.startswith("l14"):
                outboard = outboard.cut(cq.Workplane("XZ").center(x, z).circle(30).extrude(T + 2).translate((0, 1, 0)))
                add(a, cq.Workplane("XZ").center(x, z).circle(30).extrude(-55), f"socket_{kind}", (0.3, 0.3, 0.3))
            else:
                w_, h_, d_ = PORT_FACE["sb175" if kind.startswith("sb175") else "sb50"]
                outboard = outboard.cut(box(w_, T + 2, h_, (x, -T - 1, z)))
                add(a, box(w_, d_, h_, (x, 0, z)), f"socket_{kind}", (0.3, 0.3, 0.3))
        add(a, outboard, "panel_side_outboard", PANEL)
        inboard = box(out_D, T, out_H, (0, out_W, 0))
        ca = COMPONENTS["anderson"]
        for (x, z) in ANDERSONS:
            inboard = inboard.cut(box(ca.w, T + 2, ca.h, (x_in0 + x - ca.w / 2, out_W - 1, floor_top + z - ca.h / 2)))
            add(a, box(ca.w, 40, ca.h, (x_in0 + x - ca.w / 2, out_W - 40, floor_top + z - ca.h / 2)),
                f"socket_anderson_{int(z)}", (0.3, 0.3, 0.3))
        for port in [q for q in SIDE_PORTS if q[0] == "in"]:   # bodies point -Y from the inboard panel's inner face
            kind, x, z = port[1], port[2], port[3]
            if kind == "socket":
                r = port[4] / 2
                inboard = inboard.cut(cq.Workplane("XZ").center(x, z).circle(r).extrude(-(T + 2)).translate((0, out_W - 1, 0)))
                add(a, cq.Workplane("XZ").center(x, z).circle(r + 3).extrude(40).translate((0, out_W, 0)), f"socket_{int(x)}", (0.3, 0.3, 0.3))
            elif kind.startswith("l14"):
                inboard = inboard.cut(cq.Workplane("XZ").center(x, z).circle(30).extrude(-(T + 2)).translate((0, out_W - 1, 0)))
                add(a, cq.Workplane("XZ").center(x, z).circle(30).extrude(55).translate((0, out_W, 0)), f"socket_{kind}", (0.3, 0.3, 0.3))
            else:
                d_, w_, h_ = INLET_BODY["sb175" if kind.startswith("sb175") else "sb50"]
                inboard = inboard.cut(box(w_, T + 2, h_, (x, out_W - 1, z)))
                add(a, box(w_, d_, h_, (x, out_W - d_, z)), f"socket_{kind}", (0.3, 0.3, 0.3))
        add(a, inboard, "panel_side_inboard", PANEL)
        back = box(T, out_W, out_H, (-T, 0, 0))
        back = back.cut(box(T + 2, 120, 30, (-T - 1, y_in0 + in_W / 2 - 60, floor_top + 40)))   # fridge cable to the IceBox slots
        add(a, back, "panel_back_icebox_side", PANEL)
        front = box(T, out_W, out_H, (out_D, 0, 0))
        for r in range(P["vent_rows"]):
            z = floor_top + 40 + r * 60
            for y in range(40, int(in_W) - 100, 70):
                front = front.cut(cq.Workplane("YZ").center(y_in0 + y + 30, z).slot2D(60, 10).extrude(out_D + T + 1))
        si = socket_insert() if SOCKETS else None
        if si is not None:
            bb = si.val().BoundingBox()
            front = front.cut(box(T + 2, bb.ylen, bb.zlen, (out_D - 1, bb.ymin, bb.zmin)))
        if P["card_plane"] == "v9":
            for nm, y, z in FRONT_INLETS:
                if nm.startswith("l14"):
                    front = front.cut(cq.Workplane("YZ").center(y_in0 + y, floor_top + z).circle(30).extrude(out_D + T + 1))
                    add(a, cq.Workplane("YZ").center(y_in0 + y, floor_top + z).circle(30).extrude(-55).translate((out_D, 0, 0)), f"socket_{nm}", (0.3, 0.3, 0.3))
                else:
                    d_, w_, h_ = INLET_BODY["sb175" if nm.startswith("sb175") else "sb50"]
                    front = front.cut(box(T + 2, w_, h_, (out_D - 1, y_in0 + y, floor_top + z)))
                    add(a, box(d_, w_, h_, (out_D - d_, y_in0 + y, floor_top + z)), f"socket_{nm}", (0.3, 0.3, 0.3))
        for port in FRONT_PORTS:   # v10 vertical port line; bodies point -X from the front panel's inner face
            kind, y, z = port[0], port[1], port[2]
            if kind == "socket":
                r = port[3] / 2
                front = front.cut(cq.Workplane("YZ").center(y, z).circle(r).extrude(T + 2).translate((out_D - 1, 0, 0)))
                add(a, cq.Workplane("YZ").center(y, z).circle(r + 3).extrude(-40).translate((out_D, 0, 0)), f"socket_{int(y)}_{int(z)}", (0.3, 0.3, 0.3))
            elif kind.startswith("l14"):
                front = front.cut(cq.Workplane("YZ").center(y, z).circle(30).extrude(T + 2).translate((out_D - 1, 0, 0)))
                add(a, cq.Workplane("YZ").center(y, z).circle(30).extrude(-55).translate((out_D, 0, 0)), f"socket_{kind}", (0.3, 0.3, 0.3))
            else:
                w_, h_, d_ = PORT_FACE["sb175" if kind.startswith("sb175") else "sb50" if kind.startswith("sb50") else "iec"]
                front = front.cut(box(T + 2, w_, h_, (out_D - 1, y - w_ / 2, z - h_ / 2)))
                add(a, box(d_, w_, h_, (out_D - d_, y - w_ / 2, z - h_ / 2)), f"socket_{kind}", (0.3, 0.3, 0.3))
        add(a, front, "panel_front_removable", PANEL)
        if si is not None:
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

    if P["card_plane"] == "v12":
        (build_v13 if P.get("box") == "v13" else build_v12)(a)
        if P.get("with_pack2"):   # pack2 on the vehicle floor in front of the box's port face, its SB175 back panel toward the box
            tmp = cq.Assembly()
            build_pack2(tmp)
            dz = -P["icebox_H"] if P["stack_on_icebox"] else 0.0
            for ch in tmp.children:
                shp = ch.obj.val().translate((out_D + 80.0, (out_W - PACK["W"]) / 2, dz))
                col = {"battery": BATT, "power": GOLD, "socket": (0.3, 0.3, 0.3), "lid": PANEL}.get(ch.name.split("_")[0], ORANGE if ch.name.startswith("print_") and "panel" not in ch.name and "lid" not in ch.name else PANEL)
                add(a, cq.Workplane("XY").add(shp), ch.name, col)
        if P["show_icebox"]:
            for nm, shp in icebox_parts():
                col = BLACK if "cube" in nm else GRAY if "bar" in nm else (0.35, 0.35, 0.35)
                add(a, shp, nm, col)
        return a
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
    "cerbo_flat":       [(5.5, 10), (148.5, 10), (5.5, 68), (148.5, 68)],                 # (x, y) on the deck
    "orion":            [(6.9, 12), (116.2, 12), (6.9, 125), (116.2, 125)],               # 109.3 x 113, 4 x M4
    "mppt":             [(5, 33.5), (181, 33.5), (5, 105), (181, 105)],                   # keyholes 176 x 71.5
    "shunt":            [(9.5, 27), (110.5, 27)],                                         # 2 x M6 at 101 (pattern assumed centred: see shunt_x)
    "shunt_x":          [(9.5, 12.5), (110.5, 12.5)],   # on the shelf: the two 6 x 9.8 slots sit ON THE STUD LINE, 12.5 mm from the stud-side edge of the
                                                        # 46 mm housing (33.6 from the housing edge), not centred (STEP, 2026-11-01: the shunt printed to the
                                                        # centred pattern sat 15.5 mm off the shelf lip, which is where the user's "11 mm closer" came from)
    "multiplus_1200_up": [(14.2, 68.0), (234.8, 68.0), (14.2, 311.8), (234.8, 311.8)],    # keyholes 220.6 x 243.8, upper pair 62.8 below the body top, M6
    "multiplus_1200":   [(99.4, 14.7), (343.2, 14.7), (99.4, 235.3), (343.2, 235.3)],
    "busbar_n":         [(11.5, 16), (143.5, 16)],  # 5-stud M8 covered bar: mounting ears 132 mm on centre (owner-measured 2026-10-31; was 131 'verify')
    "busbar_p":         [(11.5, 16), (143.5, 16)],  # same bar in red; both ears take an M5 into the shelf-floor insert
    "breaker_a":        [(12.32, 10.73), (68.96, 37.40)],   # Bussmann 285: two 6.6 mm holes on a 56.64 x 26.67 diagonal (x along the 81.28 length).
                                                            # Seen from above with the length to the right the diagonal runs lower-left to upper-right
                                                            # (series drawing, top view: hole top-left / bottom-right with the length vertical). The
                                                            # earlier (37.40, 10.73) order was the MIRROR and did not fit the printed shelf (2026-10-24).
    "breaker_b":        [(24, 8), (24, 66)],        # verify
    "garmin":           [(20, 37), (105, 37)],      # verify (Garmin bracket, 2 screws)
    "garmin_up":        [(37, 20), (37, 105)],      # the same bracket turned 90 deg (verify)
    "bms":              [(10, 10), (112, 10), (10, 96), (112, 96)],   # verify
}
INSERT = {"mppt": "M5", "orion": "M4", "cerbo": "M4", "cerbo_up": "M4", "cerbo_flat": "M4", "shunt": "M6", "shunt_x": "M5", "busbar_n": "M5", "busbar_p": "M5",
          "breaker_a": "M6", "breaker_b": "M6", "garmin": "M4", "bms": "M4"}
HOLES["garmin_up"] = [(37, 20), (37, 105)]
HOLES["multiplus_1200_side"] = [(68.0, 14.2), (311.8, 14.2), (68.0, 234.8), (311.8, 234.8)]   # the upright pattern turned on its side
HOLES["mppt_up"] = [(v, u) for (u, v) in HOLES.get("mppt", [])]          # upright: the 186 x 130 pattern transposed (keyholes 71.5 across, 176 up)
HOLES["breaker_face"] = [(12.32, 37.40), (68.96, 10.73)]                     # Bussmann 285 on its side: two 6.6 mm holes on a 56.64 x 26.67 diagonal (datasheet)
INSERT["breaker_face"] = "M5"
HOLES["multiplus_ii_long"] = [(50.0, 30.0), (528.0, 30.0), (289.0, 258.0)]   # two bottom holes + the top hook, turned on its side (verify, appendix G)
HOLES["multiplus_1200_long"] = [(68.0, 14.2), (311.8, 14.2), (68.0, 234.8), (311.8, 234.8)]   # the upright pattern turned on its side
INSERT["multiplus_1200_long"] = "M5"   # + washer: an M6 insert is longer than the 6 mm plate
INSERT["multiplus_ii_long"] = "M6"
INSERT["multiplus_1200_side"] = INSERT.get("multiplus_1200_up", "M6"); INSERT["mppt_up"] = INSERT["mppt"]
INSERT["garmin_up"] = INSERT["garmin"]
FASTENER = {   # how each unit attaches to a printed card
    "multiplus_1200_up": "4 x M6 x 25 through-bolt + printed 40 x 40 backing plate behind each keyhole; weight on the two printed feet",
    "multiplus_1200":    "4 x M6 x 25 through-bolt + printed backing plates; weight on the two printed feet",
    "mppt":   "4 x M5 x 10 pan head into heat-set inserts; hang on the keyholes, then tighten",
    "orion":  "4 x M4 x 10 into M4 heat-set inserts",
    "cerbo":  "4 x M4 x 8 into M4 heat-set inserts", "cerbo_up": "4 x M4 x 8 into M4 heat-set inserts",
    "cerbo_flat": "4 x M4 x 8 down through the lugs into M4 heat-set inserts in the pedestal bosses",
    "shunt":  "2 x M6 x 12 into M6 heat-set inserts", "shunt_x": "2 x M5 x 12 + washer into M5 heat-set inserts in the shelf floor",
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
    lap = LAT["lap"]            # horizontal joints are HALF-LAPS over a lap-wide strip past the joint line.  EVERY cut a
    # tile carries (its lap rabbets at the top and bottom edges, and its spline pockets) is on ONE face, which alternates
    # by row: even rows (0, 2, ..) cut into the BACK (+Y) face, odd rows into the FRONT (-Y) face, so the neighbours
    # across a joint always keep opposite halves and each tile prints on its untouched face with no bridge or overhang
    # (2026-10-25: before this the lower row's rabbet was on the front and its pockets on the back, leaving 18 mm
    # bridges under the lower tiles).
    cut_y = lambda j: (t / 2, t / 2 + 1) if j % 2 == 0 else (-1, t / 2 + 1)   # (y0, depth) of row j's cut face
    for i in range(nx):
        for j in range(nz):
            z_lo = 0.0 if j == 0 else -lap / 2
            z_hi = th if j == nz - 1 else th + lap / 2
            tile = box(tw, t, z_hi - z_lo, (0, 0, z_lo))
            cy, cd = cut_y(j)
            if j < nz - 1:   # top edge: remove this row's half of the strip
                tile = tile.cut(box(tw + 2, cd, lap + 1, (-1, cy, th - lap / 2)))
            if j > 0:        # bottom edge: the same half (the row below removed the other one)
                tile = tile.cut(box(tw + 2, cd, lap + 1, (-1, cy, -lap / 2 - 1)))
            for jl in ((j, j + 1) if P.get("lap_bolts", True) else ()):   # 3 x M4 through-bolts across each lap this tile is part of
                if 0 < jl < nz:                                              # (v12s: none; the units screwed across the lap and the splines hold it)
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
            for patch in patches:
                pu, pv = patch[0], patch[1]
                r_hole = patch[2] if len(patch) > 2 else LAT["insert_hole"] / 2
                u, v = pu - i * tw, pv - j * th
                if -LAT["boss_r"] < u < tw + LAT["boss_r"] and -LAT["boss_r"] < v < th + LAT["boss_r"]:
                    boss = cq.Workplane("XZ").center(u, v).circle(LAT["boss_r"]).extrude(-t).intersect(box(tw, t, th))
                    tile = tile.union(boss).cut(cq.Workplane("XZ").center(u, v).circle(r_hole).extrude(-t - 2).translate((0, -1, 0)))   # -1..t+1: THROUGH (2026-10-24: +1 left a 1 mm skin on the column face)
            if j < nz - 1:   # a boss near a joint must not refill the half-lap
                tile = tile.cut(box(tw + 2, cd, lap + 1, (-1, cy, th - lap / 2)))
            if j > 0:
                tile = tile.cut(box(tw + 2, cd, lap + 1, (-1, cy, -lap / 2 - 1)))
            tiles.append((f"print_{prefix}_tile_{i}{j}", tile.translate((x0 + i * tw, y_plate, z0 + j * th))))
    # splines sit flush in 3 mm pockets on the row's cut face (back for even rows, front for odd rows): two per row per
    # vertical joint, at 30 % and 70 % of the row height, so none straddles a horizontal lap
    sl, sw, st = LAT["spline"]
    splines = []
    for i in range(1, nx):            # vertical joints
        for j in range(nz):
            yf = (y_plate + t - st) if j % 2 == 0 else y_plate
            for zc in (z0 + j * th + th * 0.3, z0 + j * th + th * 0.7):
                splines.append((f"print_{prefix}_spline_v{i}_{int(zc)}", box(sl, st, sw, (x0 + i * tw - sl / 2, yf, zc - sw / 2))))
    for nm, tile in tiles:
        for _, sp in splines:
            bb = sp.val().BoundingBox()
            back = bb.ymin > y_plate + 0.1
            tile = tile.cut(box(bb.xlen + 0.4, st + 1, bb.zlen + 0.4, (bb.xmin - 0.2, bb.ymin if back else bb.ymin - 1, bb.zmin - 0.2)))
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
DECK_EXT = 0.0       # (was 40: the deck used to run forward to carry a connector row; the pigtails are lugged at the bus bars now)
V9_DECK_LAYOUT = [   # deck 245 (x, from its back edge) x 302 (y); hand windows x 20..120 at y 48..103 and 199..254
    dict(comp="busbar_nx", x=0,   y=108),   # bus bars along the depth, between the windows
    dict(comp="busbar_px", x=0,   y=150),
    dict(comp="breaker_a", x=125, y=0),     # one Blue Sea 7148 per stack, along the depth at the deck's edges
    dict(comp="breaker_b", x=125, y=243),
    dict(comp="shunt_y",   x=160, y=65),
    # No fixed Anderson halves on the deck: every pigtail is lugged to a bus bar or breaker here and plugs into the
    # card's own receptacle at the far end.  The Garmin PowerSwitch lies where the SB50 row was, fed straight off the
    # positive bus bar beside it; its four outputs leave through a PP45 block at the deck's front edge (mates +X).
    dict(comp="garmin_edge", x=118, y=190),   # PowerSwitch on edge on a printed angle
    dict(comp="pp45_x",    x=218, y=65),
]
# v10: deck over the single stack (245 x 151); hand window at x 26..146, y 45..105
V10_DECK_LAYOUT = [
    dict(comp="busbar_px", x=50,  y=5),
    dict(comp="busbar_nx", x=50,  y=110),
    dict(comp="breaker_a", x=125, y=46),    # the two batteries are paralleled: one Blue Sea 7148 in the + lead, between the bus bars
]
# v10 column card: XZ plane along the INBOARD wall, units face -Y (toward the stack), its SB50 row on the +Y (rear) face
# in the 21 mm behind the card.  x from the card's back end, z from its bottom.
V10_COL_LAYOUT = [
    dict(comp="mppt",      x=10,  z=306),   # top, vertical, terminals down (Victron)
    dict(comp="orion",     x=10,  z=150),
    dict(comp="garmin_up", x=140, z=150),
    dict(comp="cerbo",     x=10,  z=20),
    dict(comp="shunt_up",  x=172, z=20),
]
V10_COL_CONN = [dict(comp="sb50_v", x=x) for x in (12, 51, 90, 129, 168)] + [dict(comp="pp45_v", x=207)]
# v11 (swapped): the MultiPlus on the column card (249 along the card, on 10 mm feet), its SB175 on the rear face;
# the charge gear on the front card with the Garmin and the shunt in the (now port-free) bottom band
# MultiPlus FLUSH on the card (bolted through, no feet) at card x 9 so its body clears the posts' 8 mm slot lips; the card is 267 long
# (2 x 2 tiles) to carry it plus its 31 mm top mounting bracket (datasheet 406 = 375 body + bracket); the SB175 lies above the bracket.
V11_COL_LAYOUT = [dict(comp="multiplus_1200_up", x=7.5, z=2)]
V11_COL_CONN = [dict(comp="sb175_v", x=100)]         # SB175 on the card's REAR face, mating up, in the 30 mm behind the card (box widened for it)
MP_BRACKET = 31.0   # the MultiPlus 12/1200's wall bracket above the body
V11_DECK_LAYOUT = [dict(comp="busbar_px", x=68, y=5), dict(comp="busbar_nx", x=68, y=110),   # over the stack (x from the deck's back line at x_in0+2)
                   dict(comp="breaker_a", x=143, y=175)]                                      # on the extension's front plate over the inverter column
DECK_NOTCH = 32.0   # v11: the extension stops this far short of the inverter card: an open strip along its length for the
                    # SB175 lying above the inverter and the MultiPlus's DC and AC leads coming up the card
V11_CHARGE_LAYOUT = [dict(comp="mppt", y=12, z=306), dict(comp="orion", y=12, z=148), dict(comp="cerbo_up", y=140, z=148),
                     dict(comp="garmin", y=12, z=30), dict(comp="shunt_up", y=145, z=20)]
V11_CHARGE_REAR = [dict(comp="sb50_v", y=y, z=None) for y in (10, 48, 86, 124, 162)]   # 38 pitch: clear of the column's front post and its deck ledge
V11_CHARGE_FRONT = [dict(comp="pp45_v", y=205, z=None)]   # Garmin outputs, beside the MPPT   # clear of the back post body   # MPPT, Orion, Cerbo, solar in, alt in; Garmin outputs
# fixed halves on the cards themselves, standing with the mating face UP, so the pigtail lifts off before the card
# v9 cards are cut down CARD_TRIM so the connector stack at the top of each card leaves CONN_LID_ROOM under the
# lid for the pigtail cables, which exit the mated halves upward.  Connector z is computed from the lid.
CARD_TRIM = 50.0
LEG_LAP = (215.0, 252.0)   # v9 rack legs: half-lap joint between the two printed segments (both stay under 256 tall)
SHELF_SCREW_Z = 4 + 213 + P["term_clear"] + 9.0   # shelf end-wall M4 (shelf underside + 9): v9/v10 240, v11 256
CONN_LID_ROOM = 60.0
def _conn_z(kind):
    """card-relative z of a card-mounted fixed half so the mated pair tops out CONN_LID_ROOM under the lid"""
    mated = MATED[kind]
    return (out_H - CONN_LID_ROOM) - (floor_top + 2) - mated
V9_INV_REAR = [dict(comp="sb175_v", y=150, z=None)]   # MultiPlus DC: the only connector on this card
V9_CHARGE_REAR = [dict(comp="sb50_v", y=y, z=None) for y in (15, 62, 109, 156, 203)]   # MPPT, Orion, Cerbo, solar in, alternator in
V9_CHARGE_FRONT = []
V9_INV_LAYOUT = [    # inverter card (249 wide = the MultiPlus): the SB175 pigtail leaves the top rear corner and mates on the deck
    dict(comp="multiplus_1200_up", y=0, z=2 + FEET_H),
]
V9_CHARGE_LAYOUT = [   # MPPT (70 deep) at the TOP; the bottom band (z < 148) stays empty behind the panel sockets and inlets
    dict(comp="mppt",     y=12,  z=306),   # keep units >= 10 mm from the card edge: the post lip reaches 8 mm past the card face
    dict(comp="orion",    y=12,  z=148),
    dict(comp="cerbo_up", y=140, z=148),   # Cerbo turned 90 deg beside the Orion
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
    COL = P["deck"] == "column"
    tx = x_in0 + V7["end_gap"]
    for sidx in range(1 if COL else 2):
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
        if COL:   # the column floor halves bolt to this wall: 3 x M4 each through it (heads inside, before the battery goes in)
            for hx in (12, 44, 100, fd - 100, fd - 40, fd - 10):
                tray = tray.cut(cq.Workplane("XZ").center(hx, 17).circle(2.3).extrude(-(wall + 2)).translate((0, fw - wall - 1, 0)))
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
                        three = leg_h > 490          # v11 (30 mm lug room, legs 500): two segments would exceed the bed
                        if three:
                            lap0, lap1 = 180.0, 200.0   # laps at 180-200 and 380-400; the shelf screw (256) sits in the middle segment
                            lap2, lap3 = 380.0, 400.0
                        lower = box(L, L, lap0).union(box(L / 2, L, lap1 - lap0, (free_half[0], 0, lap0)))
                        tx0, tx1 = (0, 18) if back else (-6, L)                 # foot tab over the pad + wall top
                        ty0, ty1 = (0, 32) if outer else (-20, L)
                        hx, hy = (12.0 if back else 0.0), (22 if outer else -10)
                        tab = box(tx1 - tx0, ty1 - ty0, 6, (tx0, ty0, lip + 4))
                        lower = lower.union(tab).cut(cq.Workplane("XY").center(hx, hy).circle(2.3).extrude(8).translate((0, 0, lip + 3)))
                        if three:
                            middle = (box(L / 2, L, lap1 - lap0, (wall_half[0], 0, lap0)).union(box(L, L, lap2 - lap1, (0, 0, lap1)))
                                      .union(box(L / 2, L, lap3 - lap2, (free_half[0], 0, lap2))))
                            upper = box(L / 2, L, lap3 - lap2, (wall_half[0], 0, lap2)).union(box(L, L, leg_h - lap3, (0, 0, lap3)))
                            for hz in ((lap0 + lap1) / 2, (lap2 + lap3) / 2):   # an M4 pin through each lap
                                pin = cq.Workplane("YZ").center(L / 2, hz).circle(2.3).extrude(L + 2).translate((-1, 0, 0))
                                lower = lower.cut(pin); middle = middle.cut(pin); upper = upper.cut(pin)
                        else:
                            upper = box(L / 2, L, lap1 - lap0, (wall_half[0], 0, lap0)).union(box(L, L, leg_h - lap1, (0, 0, lap1)))
                        reach = 16
                        bx0 = 0 if back else -16
                        boss = box(L + reach, L, 14, (bx0, 0, leg_h - 14))
                        bhx = L / 2 + ((reach - 4) if back else -12)
                        upper = upper.union(boss).cut(cq.Workplane("XY").center(bhx, L / 2).circle(2.3).extrude(11).translate((0, 0, leg_h - 10)))
                        shelf_screw = cq.Workplane("YZ").center(L / 2, SHELF_SCREW_Z).circle(1.65).extrude(L + 2).translate((-1, 0, 0))
                        add(a, lower.cut(shelf_screw).translate((lx, ly, 0)), f"print_leg_{sidx}_{int(lx)}_{int(ly)}_lower", ORANGE)
                        if three:
                            add(a, middle.cut(shelf_screw).translate((lx, ly, 0)), f"print_leg_{sidx}_{int(lx)}_{int(ly)}_middle", ORANGE)
                        add(a, upper.cut(shelf_screw).translate((lx, ly, 0)), f"print_leg_{sidx}_{int(lx)}_{int(ly)}_upper", ORANGE)
                    else:
                        leg = box(L, L, leg_h)
                        foot = box(L, L + 16, 6, (0, -8, 0)).cut(cq.Workplane("XY").center(L / 2, L / 2).circle(3.4).extrude(7))
                        add(a, leg.union(foot).translate((lx, ly, 0)), f"print_leg_{sidx}_{int(lx)}_{int(ly)}", ORANGE)
                z += P["shelf_t"]
    g["stack_top"] = z + P["term_clear"]
    g["bay_x1"] = x_in0 + (V8["x_inv"] - 3 if COL else V7["bay_D"])   # v10: the column posts stand on the plate, floor starts at the card
    if nine:
        # --- bus deck: printed plate on the rack legs, over both stacks ------------
        dz = g["stack_top"]
        if COL and P["swap"]:
            # v11: the stack half runs post to post on the same back and front lines as the column extension (over the whole
            # of the back legs' boss tabs, 5 mm short of the front card's SB50 row), as two plates splined at the middle
            px_inv_ = x_in0 + V8["x_inv"] - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"]
            dx0 = x_in0 + 2
            dL = (px_inv_ - 2 - V10["post_dx"] + 5) - dx0
            hole_back = tx + 6
        else:
            dx0 = tx - L / 2 + 4                                      # 4 mm inside the back leg centreline
            dL = (tx + fd + L / 2 - 4) - dx0                          # .. to 4 mm inside the front one: 245, fits the bed
            hole_back = tx + 6
        g["deck_x0"], g["deck_L"] = dx0, dL + DECK_EXT
        for half in (range(2) if DECK_EXT > 0 else ()):   # extension plates over the wiring gap, splined to the main halves
            hw = V7["bay_W"] / 2
            add(a, box(DECK_EXT, hw, P["card_t"], (dx0 + dL, y_in0 + 1 + half * hw, dz)), f"print_bus_deck_ext_{half}", ORANGE)
            add(a, box(60, 18, 3, (dx0 + dL - 30, y_in0 + 1 + half * hw + hw / 2 - 9, dz - 3)), f"print_bus_deck_ext_spline_{half}", ORANGE)
        for half in range(1 if COL else 2):   # two printable halves, one over each stack, splined at the centre line, M4 into the leg bosses
            hw = V7["bay_W"] / 2
            if COL and P["swap"]:   # two plates, split at the middle like the extension, with two splines across the joint
                xm_ = dx0 + dL / 2
                plates = [box(xm_ - dx0, hw, P["card_t"], (dx0, y_in0 + 1 + half * hw, dz)), box(dx0 + dL - xm_, hw, P["card_t"], (xm_, y_in0 + 1 + half * hw, dz))]
            else:
                plates = [box(dL, hw, P["card_t"], (dx0, y_in0 + 1 + half * hw, dz))]
                plates[0] = plates[0].cut(box(100, 55, P["card_t"] + 2, (dx0 + 20, y_in0 + 1 + half * hw + hw / 2 - 27.5, dz - 1)))   # hand window over the lugs
            for (hx, ly) in ((hole_back, y_in0 + 1 + half * V7["tray_w"]), (tx + fd - 6, y_in0 + 1 + half * V7["tray_w"]),
                             (hole_back, y_in0 + 1 + half * V7["tray_w"] + fw - L), (tx + fd - 6, y_in0 + 1 + half * V7["tray_w"] + fw - L)):
                assert dx0 + 4 <= hx <= dx0 + dL - 4, ("leg hole outside the stack plate", hx)
                hole = cq.Workplane("XY").center(hx, ly + L / 2).circle(2.3).extrude(P["card_t"] + 2).translate((0, 0, dz - 1))
                plates = [pl.cut(hole) for pl in plates]
                g.setdefault("deck_holes", []).append(("leg", hx, ly + L / 2))
            if COL and P["swap"]:   # the joint cleats' holes on this side of the line
                for cx_ in (dx0 + 100, dx0 + dL - 100):
                    hole = cq.Workplane("XY").center(cx_, y_in0 + 1 + hw - 8).circle(2.3).extrude(P["card_t"] + 2).translate((0, 0, dz - 1))
                    plates = [pl.cut(hole) for pl in plates]
            for k, pl in enumerate(plates):
                add(a, pl, f"print_bus_deck_{half}" + ("" if k == 0 else "_front"), ORANGE)
            if COL and P["swap"]:
                for ys in (hw * 0.2, hw * 0.6):   # clear of the centre-line splines at the stack/extension joint
                    add(a, box(18, 60, 3, (xm_ - 9, y_in0 + 1 + half * hw + ys - 30, dz - 3)), f"print_bus_deck_{half}_spline_{int(ys)}", ORANGE)
        # deck ties: the deck's two back corners bolt to the vertical corner bars (T-nut in the bar's inboard-facing
        # slot) through a printed bracket: a plate on the bar, a bridge over the leg boss, a pad with 2 x M4 on the deck.
        # The rack is then a closed cell: frame -> tray tabs -> trays -> leg tabs -> legs -> deck -> ties -> frame.
        for side in range(1 if COL else 2):
            pad_end = 58
            tie = (box(B, 6, 32, (0, B, dz - 20))                      # on the corner bar's +Y face
                   .union(box(pad_end, 6, 6, (0, B, dz + P["card_t"])))      # bridge, over the leg boss, onto the deck top
                   .union(box(pad_end - dx0, 46 - B, 6, (dx0, B, dz + P["card_t"]))))   # pad on the deck, clear of the bus bar
            tie = tie.cut(cq.Workplane("XZ").center(B / 2, dz - 8).circle(3.4).extrude(-(B + 8)).translate((0, B - 1, 0)))
            for hx in (45, 54):
                tie = tie.cut(cq.Workplane("XY").center(hx, 36).circle(2.3).extrude(8).translate((0, 0, dz + P["card_t"] - 1)))
            if side == 1:
                tie = tie.mirror("XZ").translate((0, out_W, 0))
            add(a, tie, f"print_deck_tie_{side}", ORANGE)
        if COL and P["swap"]:
            # --- deck extension over the inverter column: one plate from the stack half's edge to a notch along the card.
            # It rests on the stack half's spline joint and on two ledges screwed to the column card's posts; the inverter
            # card can only lift once this plate is unbolted (2 x M4 at the ledges, 2 x M4 cleats to the stack half).
            S_col = V10["post_standoff"]; py_post = out_W - B - S_col - P["post_w"]
            card_y = py_post + (P["post_w"] - P["card_t"]) / 2
            y0_ext = y_in0 + 1 + V7["bay_W"] / 2                   # the stack half's inboard edge
            y1_ext = card_y - 1                                    # .. to the inverter card's face (its SB175 is behind the card now)
            px_inv = x_in0 + V8["x_inv"] - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"]
            back_post, front_post = x_in0 + 1, px_inv - 2 - V10["post_dx"]     # the column card's posts (x)
            xe0, xe1 = x_in0 + 2, front_post + 5                                 # plate runs post to post, clear of the front card's SB50 row
            xm = (xe0 + xe1) / 2                                       # 271 mm post to post: two plates, splined at the middle
            exts = [box(xm - xe0, y1_ext - y0_ext, P["card_t"], (xe0, y0_ext, dz)), box(xe1 - xm, y1_ext - y0_ext, P["card_t"], (xm, y0_ext, dz))]
            for i, (lx, ll, lx0) in enumerate(((back_post, 28.0, 0.0), (front_post, 12.0, -12.0))):   # the posts' integral ledges
                exts[i] = exts[i].cut(box(V10["post_dx"] + 2, 12, P["card_t"] + 2, (lx - 1, py_post - 1, dz - 1)))   # the post passes through
                hx_, hy_ = lx + lx0 + 8, py_post - ll / 2
                assert xe0 + 4 <= hx_ <= xe1 - 4 and y0_ext + 4 <= hy_ <= y1_ext - 4, ("ledge hole outside the extension plate", hx_, hy_)
                exts[i] = exts[i].cut(cq.Workplane("XY").center(hx_, hy_).circle(2.3).extrude(P["card_t"] + 2).translate((0, 0, dz - 1)))
                g.setdefault("deck_holes", []).append(("ledge", hx_, hy_))
            # two cleats under the stack-half / extension joint: 40 x 30 x 14 blocks with an M4 insert each side of the line;
            # both plates screw down into them, so the extension is held at four points and the splines only locate
            for k, cx_ in enumerate((xe0 + 100, xe1 - 100)):   # between the joint splines at 25 / 50 / 75 %
                cleat = box(40, 30, 14, (cx_ - 20, y0_ext - 15, dz - 14))
                for yy in (y0_ext - 8, y0_ext + 8):
                    cleat = cleat.cut(cq.Workplane("XY").center(cx_, yy).circle(2.3).extrude(11).translate((0, 0, dz - 10)))
                    hole = cq.Workplane("XY").center(cx_, yy).circle(2.3).extrude(P["card_t"] + 2).translate((0, 0, dz - 1))
                    exts = [e.cut(hole) for e in exts]
                add(a, cleat, f"print_deck_cleat_{k}", ORANGE)
            for i, ext in enumerate(exts):
                add(a, ext, f"print_bus_deck_ext_column_{i}", ORANGE)
            add(a, box(18, 60, 3, (xm - 9, (y0_ext + y1_ext) / 2 - 18, dz - 3)), "print_bus_deck_ext_column_spline", ORANGE)   # clear of the stack-half joint spline
            g["deck_ext_y"] = (y0_ext, y1_ext)
        for xs in (() if (COL and not P["swap"]) else (dL * 0.25, dL * 0.5, dL * 0.75)):
            add(a, box(18, 60, 3, (dx0 + xs - 9, y_in0 + 1 + V7["bay_W"] / 2 - 30, dz - 3)), f"print_bus_deck_spline_{int(xs)}", ORANGE)
        for pl in (V11_DECK_LAYOUT if (COL and P["swap"]) else V10_DECK_LAYOUT if COL else V9_DECK_LAYOUT):
            c = COMPONENTS[pl["comp"]]
            at = (dx0 + pl["x"], y_in0 + 1 + pl["y"], dz + P["card_t"])
            col = (0.3, 0.3, 0.3) if c.name.startswith("socket") else (0.08, 0.08, 0.08) if c.name.startswith("garmin") else GOLD
            add(a, victron_shape(pl["comp"], c.d, c.w, c.h, at, unit_fallback(pl["comp"], c.d, c.w, c.h, at)), c.name + f"_{int(pl['x'])}_{int(pl['y'])}", col)
            if pl["comp"] in MATED:   # the pigtail's flying half, mated in front (+X); it stays with the pigtail, not the card
                overlap = 2 * c.d - MATED[pl["comp"]]
                at2 = (at[0] + c.d - overlap, at[1], at[2])
                add(a, victron_shape(pl["comp"], c.d, c.w, c.h, at2, box(c.d, c.w, c.h, at2).edges("|Z").fillet(3)),
                    c.name + f"_plug_{int(pl['x'])}_{int(pl['y'])}", (0.1, 0.6, 0.4))
        g["deck_z"] = dz

    # --- floor panel under the card zone ----------------------------------------
    add(a, box(x_in0 + in_D - g["bay_x1"], in_W, T, (g["bay_x1"], y_in0, B)), "panel_floor_front", PANEL)

    # --- three cards across the box, posts on the side depth rails ---------------
    S_out = P["post_standoff"] if P["post_standoff_out"] is None else P["post_standoff_out"]
    S_in = P["post_standoff"] if P["post_standoff_in"] is None else P["post_standoff_in"]
    cw = in_W - (S_out + S_in) - 2 * (P["post_d"] - P["slot_depth"]) - 2 * P["card_clear"]
    cy0 = y_in0 + S_out + (P["post_d"] - P["slot_depth"]) + P["card_clear"]
    ch = in_H - 8 - (CARD_TRIM if nine else 0)
    inv = COMPONENTS[P["inverter"]]
    if nine and COL and P["swap"]:
        cards = (("charge", x_in0 + V8["x_inv"], V11_CHARGE_LAYOUT, 0.0),)
        card_conn = {"charge": (V11_CHARGE_REAR, V11_CHARGE_FRONT)}
        build_column_card(a, g, tx, y_in0 + 1, fd, fw, ch, layout=V11_COL_LAYOUT, conn=V11_COL_CONN, unit_standoff=0.5, feet=False, name="inverter",
                          full_height=False, card_len=267.0, slot=7.0)
        build_pack(a, out_D + PACK["gap_to_box"])
    elif nine and COL:
        cards = (("inverter", x_in0 + V8["x_inv"], V9_INV_LAYOUT, 10.0),)
        card_conn = {"inverter": (V9_INV_REAR, [])}
        build_column_card(a, g, tx, y_in0 + 1, fd, fw, ch)
        build_pack(a, out_D + PACK["gap_to_box"])
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
        for j, y in enumerate((y_in0 + S_out, out_W - B - P["post_d"] - S_in)):
            for k, (z, gp) in enumerate(guide_post_segments(standoff=(S_out, S_in)[j])):
                if j == 1:
                    gp = gp.mirror("XZ").translate((0, P["post_d"], 0))
                add(a, gp.translate((px, y, floor_top + z)), f"print_post_{name}_{j}_{k}", ORANGE)
        for pl in layout:
            c = COMPONENTS[pl["comp"]]
            if pl["comp"].startswith("multiplus"):
                for yy in (pl["y"] + 25, pl["y"] + c.w - 85):   # two 60 mm wide feet under the housing, 18 tall, standoff deep
                    add(a, box(standoff + 4, 60, FEET_H, (cx + P["card_t"], cy0 + yy, floor_top + 2 + pl["z"] - FEET_H)), f"print_feet_mp_{int(yy)}__card", ORANGE)
            at = (cx + P["card_t"] + standoff, cy0 + pl["y"], floor_top + 2 + pl["z"])
            if pl.get("face") == "rear":   # unit on the card's rear face (-X), facing the wiring gap
                at = (cx - c.d, cy0 + pl["y"], floor_top + 2 + pl["z"])
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


def column_post(end, h, slot=None, ledge_z=None, ledge_len=28.0, ledge_x0=0.0):
    """v10 column-card guide post: 16 (X) x post_w (Y), standing on the plate 12 mm off the inboard depth rail.  Card
    slot on the +X face (back post) or -X face (front post) from the card's bottom edge up; the solid sill below
    carries the card.  Feet reach +Y over the inboard rails: the bottom one lies on the bottom rail, the top one under
    the top rail, 1/4-20 T-nuts.  Three segments on 40 mm half-laps pinned by an M4 in the slot-bottom wall."""
    dx, dy, gw, S = V10["post_dx"], P["post_w"], P["card_t"] + 2 * P["card_clear"], V10["post_standoff"]
    sd = P["slot_depth"] if slot is None else slot
    n = 3; seg = h / n; lap = 20.0
    sill = floor_top + 2
    out = []
    for i in range(n):
        z_lo = i * seg - (lap if i > 0 else 0); z_hi = (i + 1) * seg + (lap if i < n - 1 else 0)
        g = box(dx, dy, z_hi - z_lo, (0, 0, z_lo))
        if i < n - 1:   # top lap: keep the -Y half
            g = g.cut(box(dx + 2, dy / 2 + 1, 2 * lap + 1, (-1, dy / 2, (i + 1) * seg - lap)))
        if i > 0:       # bottom lap: keep the +Y half
            g = g.cut(box(dx + 2, dy / 2 + 1, 2 * lap + 1, (-1, -1, i * seg - lap - 1)))
        if i == 0:      # two M4 inserts on the -Y face, in the solid sill, for the column floor plate's lip
            for hz in (10.0, 22.0):
                g = g.cut(cq.Workplane("XZ").center(dx / 2, hz).circle(2.3).extrude(-11).translate((0, -1, 0)))
        if i == 0:      # foot on the bottom rail
            g = g.union(box(dx, S + B, 6, (0, dy, B)).cut(cq.Workplane("XY").center(dx / 2, dy + S + B / 2).circle(3.4).extrude(8).translate((0, 0, B - 1))))
        if ledge_z is not None and z_lo < ledge_z - 14 < z_hi:
            # deck ledge, part of this segment: a 14 mm block on the -Y face under the deck plate's edge with an M4 insert
            # from above, and a 26 mm gusset below it, so the extension plate screws straight down into the post
            # ledge_x0 < 0 lets the ledge overhang the post's back face so its hole lands inside a plate that ends short of the post
            g = g.union(box(dx - ledge_x0, ledge_len, 14, (ledge_x0, -ledge_len, ledge_z - 14)))
            g = g.union(box(dx - ledge_x0, 12, 26, (ledge_x0, -12, ledge_z - 40)))
            g = g.cut(cq.Workplane("XY").center(ledge_x0 + 8, -ledge_len / 2).circle(2.3).extrude(11).translate((0, 0, ledge_z - 10)))
        if i == n - 1:  # foot under the top rail
            g = g.union(box(dx, S + B, 6, (0, dy, h - 6)).cut(cq.Workplane("XY").center(dx / 2, dy + S + B / 2).circle(3.4).extrude(8).translate((0, 0, h - 7))))
        slot_x = dx - sd if end == "back" else -1.0
        zs = max(z_lo, sill)
        if zs < z_hi:
            g = g.cut(box(sd + 1, gw, z_hi - zs + 1, (slot_x, (dy - gw) / 2, zs)))
        bx = 3.0 if end == "back" else dx - 3.0
        for j in (i, i + 1):   # lap bolt at each joint this segment is part of, in the slot-bottom wall
            if 0 < j < n:
                g = g.cut(cq.Workplane("XZ").center(bx, j * seg).circle(2.3).extrude(-(dy + 2)).translate((0, -1, 0)))
        out.append((i, g))
    return out


def build_column_card(a, g, tx, ty0, fd, fw, ch, layout=None, conn=None, unit_standoff=3.0, feet=False, name="charge", full_height=False,
                      card_len=250.0, slot=None):
    """v10: the charge card lengthwise along the inboard wall beside the single battery stack; units face -Y.
    v11: the same card carries the MultiPlus on feet, its SB175 on the rear face."""
    layout = V10_COL_LAYOUT if layout is None else layout
    conn = V10_COL_CONN if conn is None else conn
    if full_height:
        # no upward-mating connectors on this card, so it runs back up toward the top of the posts; 480 (not 494) keeps
        # each of its two tiles at 240 + the 12 mm lap = 252 on the bed
        ch = min(in_H - 8, 480.0)
    g["col_ch"] = ch
    dx, dy, S = V10["post_dx"], P["post_w"], V10["post_standoff"]
    py = out_W - B - S - dy                              # post body, 12 off the inboard rail
    px_inv = x_in0 + V8["x_inv"] - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"]   # the inverter card's post
    back_x, front_x = x_in0 + 1, px_inv - 2 - dx          # front post clears the inverter card's inboard post by 2
    h = out_H - B
    sd = P["slot_depth"] if slot is None else slot
    dz_deck = 4 + 2 * COMPONENTS["battery"].h + 2 * P["term_clear"] + P["shelf_t"]   # the deck's underside
    for end, x in (("back", back_x), ("front", front_x)):   # front ledge short (the front card's SB50 pigtails are 13 mm away) and
        for k, seg in column_post(end, h, slot=sd, ledge_z=(dz_deck if P["swap"] else None),   # overhanging 12 mm back so its hole is under the plate
                                  ledge_len=(28.0 if end == "back" else 12.0), ledge_x0=(0.0 if end == "back" else -12.0)):
            add(a, seg.translate((x, py, 0)), f"print_colpost_{end}_{k}", ORANGE)
    # --- column floor: a continuous 6 mm floor from the tray's inboard wall to the inverter card's posts, the full
    # width of the column, in two halves that butt at the middle (no lap, no glue: each half is bolted at both its
    # ends).  Along the tray a 34 mm lip bolts through the tray's inboard wall (2 x M4 per half, heads inside, fitted
    # before the battery); at each post a 28 mm lip bolts into the post's solid sill (2 x M4 inserts).  The tray's
    # inboard corners are tied to the frame through the posts, and the MultiPlus leads lie on the floor.
    y0f, y1f = ty0 + fw, py - 0.5
    px_front_card = x_in0 + V8["x_inv"] - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"]
    x_end = min(front_x + dx, px_front_card - 1)
    xm = (back_x + x_end) / 2
    for i, (xa, xb, post_x) in enumerate(((back_x, xm, back_x), (xm, x_end, front_x))):
        fl = box(xb - xa, y1f - y0f, 6, (xa, y0f, 0))
        la, lb = max(xa, tx), min(xb, tx + fd)
        fl = fl.union(box(lb - la, 6, 34, (la, y0f, 0)))                               # lip against the tray wall
        for hx in ((12, 44, 100) if i == 0 else (fd - 100, fd - 40, fd - 10)):
            if la + 6 < tx + hx < lb - 6:
                fl = fl.cut(cq.Workplane("XZ").center(tx + hx, 17).circle(2.3).extrude(-8).translate((0, y0f - 1, 0)))
        fl = fl.union(box(dx, 6, 28, (post_x, y1f - 6, 0)))                              # lip against the post's -Y face
        for hz in (10.0, 22.0):
            fl = fl.cut(cq.Workplane("XZ").center(post_x + dx / 2, hz).circle(2.3).extrude(-8).translate((0, y1f - 7, 0)))
        add(a, fl, f"print_column_floor_{'back' if i == 0 else 'front'}", ORANGE)
    card_y = py + (dy - P["card_t"]) / 2
    avail0, avail1 = back_x + dx - sd + P["card_clear"], front_x + sd - P["card_clear"]
    cL = min(card_len, avail1 - avail0)
    cx0 = avail0 + (avail1 - avail0 - cL) / 2
    g.update(col_card=(cx0, cL, card_y))
    patches = [(pl["x"] + du, pl["z"] + dv) for pl in layout for (du, dv) in HOLES.get(pl["comp"], [])]
    for nm, shp in lattice_card_tiles(cL, ch, cx0, card_y, floor_top + 2, f"card_{name}", patches):
        add(a, shp, nm + "__card", ORANGE if "spline" in nm else DARK)
    for pl in layout:   # units on the -Y face, toward the stack
        c = COMPONENTS[pl["comp"]]
        so = unit_standoff if pl["comp"].startswith("multiplus") else 3.0
        at = (cx0 + pl["x"], card_y - c.d - so, floor_top + 2 + pl["z"])   # 3 mm off the card: STEP bodies carry brackets past the bbox
        col = BLUE if c.name.startswith("victron") else (0.08, 0.08, 0.08) if c.name.startswith("garmin") else GOLD
        add(a, victron_shape(pl["comp"], c.w, c.d, c.h, at, box(c.w, c.d, c.h, at).edges("|Y").fillet(3)), c.name + f"_col_{int(pl['x'])}_{int(pl['z'])}__card", col)
        if pl["comp"].startswith("multiplus") and name == "inverter":   # its wall bracket: a 3 mm plate above the body, on the card
            add(a, box(c.w, 3, MP_BRACKET, (at[0], card_y - 3, at[2] + c.h)), f"victron_multiplus_bracket__card", BLUE)
        if pl["comp"] in MATED:   # a lying connector: the pigtail's flying half mates in front of it along the card (+X)
            overlap = 2 * c.w - MATED[pl["comp"]]
            at2 = (at[0] + c.w - overlap, at[1], at[2])
            add(a, victron_shape(pl["comp"], c.w, c.d, c.h, at2, box(c.w, c.d, c.h, at2).edges("|Y").fillet(3)), c.name + f"_plug_col_{int(pl['x'])}", (0.1, 0.6, 0.4))
        if feet and pl["comp"].startswith("multiplus"):   # two printed feet under the housing, standoff deep
            for xx in (pl["x"] + 25, pl["x"] + c.w - 85):
                add(a, box(60, so + 4, FEET_H, (cx0 + xx, card_y - so - 4, floor_top + 2 + pl["z"] - FEET_H)), f"print_feet_mp_col_{int(xx)}__card", ORANGE)
    for pl in conn:   # fixed halves at the top of the +Y (rear) face, mating up; pigtail halves above
        c = COMPONENTS[pl["comp"]]
        z = _conn_z(pl["comp"])
        at = (cx0 + pl["x"], card_y + P["card_t"], floor_top + 2 + z)
        add(a, victron_shape(pl["comp"], c.w, c.d, c.h, at, box(c.w, c.d, c.h, at).edges("|Z").fillet(3)), c.name + f"_{name}_col_{int(pl['x'])}__card", (0.3, 0.3, 0.3))
        overlap = 2 * c.h - MATED[pl["comp"]]
        at2 = (at[0], at[1], at[2] + c.h - overlap)
        add(a, victron_shape(pl["comp"], c.w, c.d, c.h, at2, box(c.w, c.d, c.h, at2).edges("|Z").fillet(3)), c.name + f"_pigtail_{name}_col_{int(pl['x'])}", (0.1, 0.6, 0.4))


PACK = dict(end_gap=15.0, front=10.0, gap_to_box=80.0, post=30.0, skin=6.0, lid_z=312.0)   # add-on pack: 2 x SuperPack side by side
P.setdefault("pack", "printed")   # "printed": corner posts + panels all ASA (no bars); "bars": kit bars + IceBox offcuts
for _a in sys.argv[1:]:
    if _a.startswith("--pack="):
        P["pack"] = _a.split("=", 1)[1]


def build_pack_printed_frame(a, ox, pD, pW, pH):
    """Printed pack cage: 4 corner posts (30 x 30, two half-lapped segments, foot tab M4'd into the tray's corner pad,
    M4 insert in the top for the lid), 6 mm panel tiles screwed to the posts' outer faces (2 x 2 per panel, half-lap /
    spline joints like the cards), 6 mm lid in four tiles with a handle.  Loads: the batteries stand on the floor
    through the trays; the posts only carry the deck, lid and the lift, so ASA is plenty."""
    po, sk = PACK["post"], PACK["skin"]
    b = COMPONENTS["battery"]; wall, lip = V7["wall"], V7["lip"]
    fd, fw = b.d + 2 * wall, V7["tray_w"]
    tx, ty0 = ox + sk + po + 6, sk
    h = pH - sk                                            # posts up to the lid underside
    lap0, lap1 = h / 2 - 20, h / 2 + 20
    for (px, py, back, outer) in ((tx - 6 - po, ty0, True, True), (tx - 6 - po, ty0 + 2 * fw - po, True, False),
                                  (tx + fd + 6, ty0, False, True), (tx + fd + 6, ty0 + 2 * fw - po, False, False)):
        lower = box(po, po, lap0).union(box(po, po / 2, lap1 - lap0, (0, 0 if outer else po / 2, lap0)))
        upper = box(po, po / 2, lap1 - lap0, (0, po / 2 if outer else 0, lap0)).union(box(po, po, h - lap1, (0, 0, lap1)))
        # foot tab over the tray pad + wall top (z 34), M4 down into the pad's insert
        tx0, tx1 = (po, po + 12) if back else (-12, 0)
        ty0_, ty1_ = (0, 32) if outer else (po - 32, po)
        hx = po + 6 if back else -6
        hy = 22 if outer else po - 22
        tab = box(tx1 - tx0, ty1_ - ty0_, 6, (tx0, ty0_, lip + 4))
        lower = lower.union(tab).cut(cq.Workplane("XY").center(hx, hy).circle(2.3).extrude(8).translate((0, 0, lip + 3)))
        upper = upper.cut(cq.Workplane("XY").center(po / 2, po / 2).circle(2.3).extrude(12).translate((0, 0, h - 11)))   # lid insert
        for hz in (lap0 + 10, lap1 - 10):   # 2 x M4 through the lap
            pin = cq.Workplane("XZ").center(po / 2, hz).circle(2.3).extrude(-(po + 2)).translate((0, -1, 0))
            lower = lower.cut(pin); upper = upper.cut(pin)
        for shp, nm in ((lower, "lower"), (upper, "upper")):
            add(a, shp.translate((px, py, 0)), f"print_pack_post_{int(px - ox)}_{int(py)}_{nm}", ORANGE)
    # panels: 2 x 2 tiles each, outside the posts; back panel gets the SB175 inlet
    H = pH - sk
    for nm, shp in lattice_card_tiles(pD - 2 * sk, H, ox + sk, 0.0, 0.0, "pack_panel_outboard"):
        add(a, shp, nm, PANEL)
    for nm, shp in lattice_card_tiles(pD - 2 * sk, H, ox + sk, pW - sk, 0.0, "pack_panel_inboard"):
        add(a, shp, nm, PANEL)
    for nm, shp in lattice_card_tiles_yz(pW, H, ox, 0.0, 0.0, "pack_panel_back"):
        add(a, shp, nm, PANEL)
    for nm, shp in lattice_card_tiles_yz(pW, H, ox + pD - sk, 0.0, 0.0, "pack_panel_front"):
        add(a, shp, nm, PANEL)
    for i, x in enumerate((ox, ox + pD / 2)):   # lid: 4 tiles, M4 into the posts' tops at the corners
        for j, y in enumerate((0, pW / 2)):
            add(a, box(pD / 2, pW / 2, sk, (x, y, pH - sk)), f"print_pack_lid_{i}{j}", PANEL)
    add(a, lid_handle().translate((ox + pD / 2 - 6, pW / 2 - 30, pH)), "lid_pack_handle", BLACK)


PACK2 = dict(post=30.0, skin=6.0, lug=30.0, top=60.0, rib=20.0)   # stacked add-on pack: 2 x 2 SuperPack 60Ah, bus + breaker on a top shelf


def build_pack2(a):
    """Stacked add-on pack for v12s: four SuperPack 60Ah as two side-by-side pairs, one pair above the other, in an all-printed
    cage.  Four 30 mm corner posts (three half-lapped segments, foot tabs M4'd into the lower trays' pads, M4 insert on top for
    the lid) carry two ledge levels: a mid-deck (two plates) that the upper trays bolt down onto, and a top shelf (two plates)
    with the two bus bars and the one 150 A breaker.  Ribs on the back and front panels' inner faces support the plates' edges
    between the posts.  SB175 umbilical inlet in the back panel at shelf level.  6 mm panel tiles outside the posts, lid on top."""
    po, sk, lug, rib = PACK2["post"], PACK2["skin"], PACK2["lug"], PACK2["rib"]
    b = COMPONENTS["battery"]; wall, lip = 6.0, 30.0                   # the v9 tray: 6 mm walls, 30 mm lip over a 4 mm floor
    fd, fw = b.d + 2 * wall, b.w + 2 * wall                            # 241 x 150
    pD = sk + po + 6 + fd + 6 + po + sk                                # 325
    pW = sk + 2 * fw + 2 + sk                                          # 314
    z_deck = 4 + b.h + lug                                             # 247: mid-deck plate sits here
    z_shelf = z_deck + 6 + 4 + b.h + lug                               # 500: top shelf plate
    z_lid = z_shelf + 6 + PACK2["top"]                                 # 566: lid underside; posts this tall
    pH = z_lid + sk
    PACK.update(D=pD, W=pW, H=pH)
    tx, ty0 = sk + po + 6, sk
    # --- posts: full solid with ledges, foot tab, insert, then split into three half-lapped segments ------------------
    h = z_lid; seams = (h / 3, 2 * h / 3); lapw = 40.0
    for (px, py, back, outer) in ((tx - 6 - po, ty0, True, True), (tx - 6 - po, ty0 + 2 * fw + 2 - po, True, False),
                                  (tx + fd + 6, ty0, False, True), (tx + fd + 6, ty0 + 2 * fw + 2 - po, False, False)):
        g = box(po, po, h)
        for zl in (z_deck, z_shelf):   # ledge 28 inward under each plate level, with a 12 mm block under it, M4 insert from the top
            lx = po if back else -28
            g = g.union(box(28, po, 6, (lx, 0, zl - 6))).union(box(28, po, 12, (lx, 0, zl - 18)))
            g = g.cut(cq.Workplane("XY").center(lx + 14, po / 2).circle(2.3).extrude(14).translate((0, 0, zl - 13)))
        tx0, tx1 = (po, po + 12) if back else (-12, 0)                 # foot tab over the lower tray's pad, M4 down into its insert
        ty0_, ty1_ = (0, 32) if outer else (po - 32, po)
        hx = po + 6 if back else -6; hy = 22 if outer else po - 22
        g = g.union(box(tx1 - tx0, ty1_ - ty0_, 6, (tx0, ty0_, lip + 4))).cut(cq.Workplane("XY").center(hx, hy).circle(2.3).extrude(8).translate((0, 0, lip + 3)))
        g = g.cut(cq.Workplane("XY").center(po / 2, po / 2).circle(2.3).extrude(12).translate((0, 0, h - 11)))      # lid insert
        for zs in seams:   # 2 x M4 pins through each lap
            for hz in (zs - 12, zs + 12):
                g = g.cut(cq.Workplane("XZ").center(po / 2, hz).circle(2.3).extrude(-(po + 2)).translate((0, -1, 0)))
        bounds = ((-1, seams[0] + lapw / 2), (seams[0] - lapw / 2, seams[1] + lapw / 2), (seams[1] - lapw / 2, h + 1))
        for k, (za, zb) in enumerate(bounds):
            seg = g.intersect(box(po + 80, po + 2, zb - za, (-40, -1, za)))
            if k > 0:   # bottom lap: keep the inner half (y po/2..po) -> cut the outer half
                seg = seg.cut(box(po + 82, po / 2 + 1, lapw + 1, (-41, -1, za - 0.5)))
            if k < 2:   # top lap: keep the outer half -> cut the inner half
                seg = seg.cut(box(po + 82, po / 2 + 1, lapw + 1, (-41, po / 2, zb - lapw - 0.5)))
            add(a, seg.translate((px, py, 0)), f"print_pack_post_{int(px)}_{int(py)}_{k}", ORANGE)
    # --- trays: lower pair on the floor (pads take the posts' foot tabs), upper pair bolted down onto the mid-deck ------
    for layer, zb in enumerate((0.0, z_deck + 6)):
        for sidx in range(2):
            ty = ty0 + sidx * (fw + 2)
            tray = box(fd, fw, lip + 4).cut(box(b.d, b.w, lip + 5, (wall, wall, 4)))
            tray = tray.cut(box(fd + 2, 28, 5, (-1, wall + b.w / 2 - 14, 2)))
            if layer == 0:
                for (px, py) in ((-6, 12), (-6, fw - 32), (fd, 12), (fd, fw - 32)):
                    tray = tray.union(box(6, 20, lip + 4, (px, py, 0)))
                    tray = tray.cut(cq.Workplane("XY").center(px + 6.0 if px < 0 else px, py + 10).circle(2.8).extrude(13).translate((0, 0, lip + 4 - 12)))
            else:   # 4 x M4 down through the floor into the deck plate's inserts (from inside the empty tray)
                for (hx, hy) in ((wall + 20, wall + 20), (wall + b.d - 20, wall + 20), (wall + 20, wall + b.w - 20), (wall + b.d - 20, wall + b.w - 20)):
                    tray = tray.cut(cq.Workplane("XY").center(hx, hy).circle(2.3).extrude(6).translate((0, 0, -1)))
            add(a, tray.translate((tx, ty, zb)), f"print_pack_tray_{layer}{sidx}", ORANGE)
            at = (tx + wall, ty + wall, zb + 4)
            add(a, victron_shape("battery", b.d, b.w, b.h, at, box(b.d, b.w, b.h, at).edges("|Z").fillet(6)), f"battery_pack_{layer}{sidx}", BATT)
    # --- mid-deck and top shelf: two plates each (253 x 151), corners on the post ledges, back/front edges on panel ribs ----
    for lvl, zp in (("deck", z_deck), ("shelf", z_shelf)):
        for sidx in range(2):
            y0 = ty0 + sidx * (fw + 1)
            pl = box(fd + 12, fw + 1, 6, (tx - 6, y0, zp))
            for (cx, cy) in ((tx - 6 + 14, y0 + (po / 2 if sidx == 0 else fw + 1 - po / 2)), (tx + fd + 6 - 14, y0 + (po / 2 if sidx == 0 else fw + 1 - po / 2))):
                pl = pl.cut(cq.Workplane("XY").center(cx, cy).circle(2.3).extrude(8).translate((0, 0, zp - 1)))   # M4 down into the ledge inserts
            if lvl == "deck":   # inserts for the upper tray's floor bolts
                for (hx, hy) in ((wall + 20, wall + 20), (wall + b.d - 20, wall + 20), (wall + 20, wall + b.w - 20), (wall + b.d - 20, wall + b.w - 20)):
                    pl = pl.cut(cq.Workplane("XY").center(tx + hx, ty0 + sidx * (fw + 2) + hy).circle(2.8).extrude(7).translate((0, 0, zp - 0.5)))
            add(a, pl, f"print_pack_{lvl}_{sidx}", ORANGE)
        for side, xr in (("back", sk), ("front", pD - sk - rib)):   # ribs on the back/front panels' inner faces between the posts
            rb = box(rib, pW - 2 * sk - 2 * po, rib, (xr, sk + po, zp - rib))
            for yc in (pW / 2 - 80, pW / 2, pW / 2 + 80):   # 3 x M4 through the panel into inserts in the rib
                rb = rb.cut(cq.Workplane("YZ").center(yc, zp - rib / 2).circle(2.8).extrude(8).translate((xr - (1 if side == "back" else -rib + 1 - 7), 0, 0)))
            add(a, rb, f"print_pack_rib_{lvl}_{side}", ORANGE)
    # --- bus bars and breaker on the top shelf, SB175 inlet in the back panel at shelf level --------------------------
    for comp, (bx, by) in (("busbar_p", (tx + 64, ty0 + 60)), ("busbar_n", (tx + 109, ty0 + 60)), ("breaker_a", (tx + 154, ty0 + 100))):   # clear of the SB175 body at the back
        c = COMPONENTS[comp]
        at = (bx, by, z_shelf + 6)
        add(a, victron_shape(comp, c.d, c.w, c.h, at, unit_fallback(comp, c.d, c.w, c.h, at)), f"power_pack_{comp}", GOLD)
    d_, w_, h_ = INLET_BODY["sb175"]
    add(a, box(d_, w_, h_, (sk, pW / 2 - w_ / 2, z_shelf + 14)), "socket_pack_sb175", (0.3, 0.3, 0.3))
    # --- panels (6 mm tiles outside the posts) and lid --------------------------------------------------------------------
    for nm, shp in lattice_card_tiles(pD - 2 * sk, z_lid, sk, 0.0, 0.0, "pack_panel_outboard"):
        add(a, shp, nm, PANEL)
    for nm, shp in lattice_card_tiles(pD - 2 * sk, z_lid, sk, pW - sk, 0.0, "pack_panel_inboard"):
        add(a, shp, nm, PANEL)
    for nm, shp in lattice_card_tiles_yz(pW, z_lid, 0.0, 0.0, 0.0, "pack_panel_back"):
        add(a, shp, nm, PANEL)
    for nm, shp in lattice_card_tiles_yz(pW, z_lid, pD - sk, 0.0, 0.0, "pack_panel_front"):
        add(a, shp, nm, PANEL)
    for i, x in enumerate((0, pD / 2)):
        for j, y in enumerate((0, pW / 2)):
            add(a, box(pD / 2, pW / 2, sk, (x, y, z_lid)), f"print_pack_lid_{i}{j}", PANEL)
    add(a, lid_handle().translate((pD / 2 - 6, pW / 2 - 30, pH)), "lid_pack_handle", BLACK)
    PACK.update(z_deck=z_deck, z_shelf=z_shelf, z_lid=z_lid)


def report_pack2():
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.1f} in)"
    D, W, H = PACK["D"], PACK["W"], PACK["H"]
    print("== Variant 'pack2': stacked add-on pack for v12s, 2 x 2 SuperPack 60Ah, all printed ==")
    print(f"outer D x W x H : {mm(D)} x {mm(W)} x {mm(H)}; the IceBox + v12s stack is {558.8 + 282:.0f} ({(558.8 + 282) / 25.4:.1f} in) tall, so {558.8 + 282 - H:.0f} mm of height is unused")
    print(f"layers          : lower pair on the floor, mid-deck at z {PACK['z_deck']:.0f} (30 mm lug room), upper pair on it, top shelf at z {PACK['z_shelf']:.0f} with the bus bars + one 150 A breaker, lid at {PACK['z_lid']:.0f}")
    print("  a third pair would need 247 more: 819 tall, 22 under the stack height, but the bus shelf would have to move to a side column")
    print("  electrical     : 4 x 60 Ah = 240 Ah, 120 A continuous; paralleled on the two bus bars, one breaker in the + lead to the SB175; 2 AWG umbilical to the")
    print("                   SB175 inlet on the v12s front panel (in front of its bus column); with the box's own pair: 360 Ah, 180 A")
    print("  assembly       : lower trays -> posts (foot tabs) -> back/front panels with their ribs -> mid-deck plates (M4 into ledges) -> upper trays (M4 down into deck")
    print("                   inserts) -> top shelf plates -> bus + breaker -> side panels -> batteries, lugs, lid.  Posts: 3 segments x ~209 with 2 M4 pins per lap")
    print(f"  weight         : ~{4 * 7.5 + 6:.0f} kg (batteries 30, prints ~6): two people, or strap handles through the side panels")


def build_pack(a, ox):
    """v10 add-on pack: the two displaced SuperPacks side by side in their own cage, built from the leftover stock.
    Height rails = the four IceBox depth-rail offcuts (uncut); width and depth rails cut from 8 kit bars.  Same trays,
    tabs, legs and deck halves as the main rack (one battery high), bus bars + 2 breakers on the deck, one SB175
    panel inlet on the back panel facing the main box.  Sits on the vehicle floor like the main box (no floor panel)."""
    b = COMPONENTS["battery"]; wall, L, lip = V7["wall"], V7["leg"], V7["lip"]
    fd, fw = b.d + 2 * wall, V7["tray_w"]
    PR = P["pack"] == "printed"
    if PR:
        # all-printed cage: four 30 mm ASA corner posts standing beside the tray end walls (foot tabs onto the tray pads
        # like the legs), 6 mm panel tiles screwed outside them, a 6 mm lid on their tops.  Narrower than the bar
        # version because there are no rails: the posts sit inside the trays' width.
        po, sk = PACK["post"], PACK["skin"]
        pD = sk + po + 6 + fd + 6 + po + sk
        pW = sk + 2 * fw + 2 + sk
        pH = PACK["lid_z"]
        PACK.update(D=pD, W=pW, H=pH, offcut=P["frame_D"] - out_D)
        build_pack_printed_frame(a, ox, pD, pW, pH)
        tx = ox + sk + po + 6
        py0 = sk
    else:
        pD = PACK["end_gap"] + fd + L + PACK["front"] + 2 * B
        pW = out_W
        offcut = P["frame_D"] - out_D                         # IceBox depth rail (frame_D - 2C) minus the main box's (out_D - 2C)
        pH = offcut + 2 * C
        PACK.update(D=pD, W=pW, H=pH, offcut=offcut)
        tx = ox + B + PACK["end_gap"]
        py0 = B + 1
    if not PR:
      cube = corner_cube()
      for i, x in enumerate((0, pD - C)):
          for j, y in enumerate((0, pW - C)):
              for k, z in enumerate((0, pH - C)):
                  add(a, cube.translate((ox + x, y, z)), f"print_pack_cube_{i}{j}{k}", BLACK)
      n = 0
      for x in (0, pD - B):
          for y in (0, pW - B):
              add(a, bar(pH - 2 * C, "z").translate((ox + x + B / 2, y + B / 2, C)), f"bar_pack_h{n}", GRAY); n += 1
          for z in (0, pH - B):
              add(a, bar(pW - 2 * C, "y").translate((ox + x + B / 2, C, z + B / 2)), f"bar_pack_w{n}", GRAY); n += 1
      for y in (0, pW - B):
          for z in (0, pH - B):
              add(a, bar(pD - 2 * C, "x").translate((ox + C, y + B / 2, z + B / 2)), f"bar_pack_d{n}", GRAY); n += 1
    # SB175 inlet on the back panel, facing the main box, just above the deck beside the breaker
    d_, w_, h_ = INLET_BODY["sb175"]; iy, iz = pW / 2 - w_ / 2, 4 + COMPONENTS["battery"].h + P["term_clear"] + 9.0
    if not PR:
        add(a, box(pD, T, pH, (ox, -T, 0)), "panel_pack_outboard", PANEL)
        add(a, box(pD, T, pH, (ox, pW, 0)), "panel_pack_inboard", PANEL)
        add(a, box(T, pW, pH, (ox + pD, 0, 0)), "panel_pack_front", PANEL)
        add(a, box(pD, pW, T, (ox, 0, pH)), "lid_pack", PANEL)
        back = box(T, pW, pH, (ox - T, 0, 0)).cut(box(T + 2, w_, h_, (ox - T - 1, iy, iz)))
        add(a, back, "panel_pack_back", PANEL)
        add(a, box(d_, w_, h_, (ox, iy, iz)), "socket_pack_sb175", (0.3, 0.3, 0.3))
    else:
        add(a, box(d_, w_, h_, (ox + PACK["skin"], iy, iz)), "socket_pack_sb175", (0.3, 0.3, 0.3))
    # trays, batteries, legs: the v9 rack one battery high
    for sidx in range(2):
        ty = py0 + sidx * fw
        tray = box(fd, fw, lip + 4).cut(box(b.d, b.w, lip + 5, (wall, wall, 4)))
        tray = tray.cut(box(fd + 2, 28, 5, (-1, wall + b.w / 2 - 14, 2)))
        for (px, py) in ((-6, 12), (-6, fw - 32), (fd, 12), (fd, fw - 32)):
            tray = tray.union(box(6, 20, lip + 4, (px, py, 0)))
        for (px, py) in ((-6, 12), (-6, fw - 32), (fd, 12), (fd, fw - 32)):
            tray = tray.cut(cq.Workplane("XY").center(px + 6.0 if px < 0 else px, py + 10).circle(2.8).extrude(13).translate((0, 0, lip + 4 - 12)))
        for (hx, hy) in ((wall + 20, wall + 20), (wall + b.d - 20, wall + 20), (wall + 20, wall + b.w - 20), (wall + b.d - 20, wall + b.w - 20)):
            tray = tray.cut(cq.Workplane("XY").center(hx, hy).circle(3.4).extrude(5))
        rail_lo = -(1 + B) if sidx == 0 else fw + 1
        for sx in (() if PR else (40, fd - 80)):
            fl = box(40, B + 1 + 8, (lip + 4) - B, (sx, rail_lo if sidx == 0 else fw - 8, B))
            tray = tray.union(fl.cut(cq.Workplane("XY").center(sx + 20, rail_lo + B / 2).circle(3.4).extrude(lip + 5)))
        add(a, tray.translate((tx, ty, 0)), f"print_pack_tray_{sidx}", ORANGE)
        at = (tx + wall, ty + wall, 4)
        add(a, victron_shape("battery", b.d, b.w, b.h, at, box(b.d, b.w, b.h, at).edges("|Z").fillet(6)), f"battery_pack_{sidx}", BATT)
        leg_h = 4 + b.h + P["term_clear"]
        for (lx, ly) in ((tx - L, ty), (tx - L, ty + fw - L), (tx + fd, ty), (tx + fd, ty + fw - L)):
            back, outer = lx < tx, (ly == ty)
            if PR and ((sidx == 0 and outer) or (sidx == 1 and not outer)):
                continue   # printed cage: the corner posts stand here and carry the deck corners on ledges
            leg = box(L, L, leg_h)
            tx0, tx1 = (0, 18) if back else (-6, L)
            ty0, ty1 = (0, 32) if outer else (-20, L)
            hx, hy = (12.0 if back else 0.0), (22 if outer else -10)
            leg = leg.union(box(tx1 - tx0, ty1 - ty0, 6, (tx0, ty0, lip + 4))).cut(cq.Workplane("XY").center(hx, hy).circle(2.3).extrude(8).translate((0, 0, lip + 3)))
            boss = box(L + 16, L, 14, (0 if back else -16, 0, leg_h - 14))
            leg = leg.union(boss).cut(cq.Workplane("XY").center(L / 2 + (12 if back else -12), L / 2).circle(2.3).extrude(11).translate((0, 0, leg_h - 10)))
            add(a, leg.translate((lx, ly, 0)), f"print_pack_leg_{sidx}_{int(lx - ox)}_{int(ly)}", ORANGE)
    # deck: two halves on the leg boss tabs, hand windows over the lugs, bus bars along the depth between them, breakers
    dz = 4 + b.h + P["term_clear"]
    dx0, dL = tx - L / 2 + 4, fd + 4
    for half in range(2):
        hw = V7["bay_W"] / 2
        deck = box(dL, hw, P["card_t"], (dx0, py0 + half * hw, dz))
        if not P["swap"]:
            deck = deck.cut(box(100, 55, P["card_t"] + 2, (dx0 + 20, py0 + half * hw + hw / 2 - 27.5, dz - 1)))
        for (hx, ly) in ((tx + 6, py0 + half * fw), (tx + fd - 6, py0 + half * fw), (tx + 6, py0 + half * fw + fw - L), (tx + fd - 6, py0 + half * fw + fw - L)):
            deck = deck.cut(cq.Workplane("XY").center(hx, ly + L / 2).circle(2.3).extrude(P["card_t"] + 2).translate((0, 0, dz - 1)))
        add(a, deck, f"print_pack_deck_{half}", ORANGE)
    for xs in (dL * 0.25, dL * 0.5, dL * 0.75):
        add(a, box(18, 60, 3, (dx0 + xs - 9, py0 + V7["bay_W"] / 2 - 30, dz - 3)), f"print_pack_deck_spline_{int(xs)}", ORANGE)
    if PR:   # deck corners rest on ledges printed on the posts (M4 insert 12 mm in, same holes as the leg boss tabs)
        for (lx, ly, back) in ((tx - 6, py0, True), (tx - 6, py0 + 2 * fw - L, True), (tx + fd + 6, py0, False), (tx + fd + 6, py0 + 2 * fw - L, False)):
            ledge = box(28, L, 14, (lx if back else lx - 28, ly, dz - 14))
            hx = tx + 6 if back else tx + fd - 6
            add(a, ledge.cut(cq.Workplane("XY").center(hx, ly + L / 2).circle(2.3).extrude(11).translate((0, 0, dz - 10))), f"print_pack_ledge_{int(lx - ox)}_{int(ly)}", ORANGE)
    # the two batteries are paralleled battery-to-battery; ONE Blue Sea 187 150 A in the + lead to the SB175, - straight to it
    for pl in (dict(comp="breaker_a", x=125, y=122),):
        c = COMPONENTS[pl["comp"]]
        at = (dx0 + pl["x"], py0 + pl["y"], dz + P["card_t"])
        add(a, victron_shape(pl["comp"], c.d, c.w, c.h, at, unit_fallback(pl["comp"], c.d, c.w, c.h, at)), "power_pack_" + c.name[6:] + f"_{int(pl['x'])}_{int(pl['y'])}", GOLD)


V12 = dict(end_gap=15.0, row_gap=2.0, plate_gap=10.0, standoff=2.0)


def v12_post(h, mirror=False, buttress=False):
    """Single-piece guide post for the fixed MultiPlus plate: 24 (X) x 18 (Y), standing on the plate against the depth
    rail's inner face.  The rails' top and bottom slots hold the box's panels, so the post ties in through the rails'
    INNER slots only: a horizontal 1/4-20 through its solid sill at z 12.7 (T-nut in the bottom rail), and a printed clip
    on its top that bolts into the top rail's inner slot the same way and screws down into the post (M4 insert).
    When buttress=True (v13 slot-captured lid), the post has no top clip; instead a 30 mm inboard base extension + 110 mm
    tall triangular gusset along the bottom width rail adds a second 1/4-20 sill bolt 28 mm inboard of the first.
    Card slot on the +Y face from z 30 (above the sill bolt).  254 tall: one print."""
    gw = P["card_t"] + 2 * P["card_clear"]
    g = box(P["post_w"], P["post_d"], h)
    g = g.cut(box(gw, P["slot_depth"] + 1, h, ((P["post_w"] - gw) / 2, P["post_d"] - P["slot_depth"], 30)))
    g = g.cut(cq.Workplane("XZ").center(P["post_w"] / 2, B / 2).circle(3.4).extrude(-(P["post_d"] + 2)).translate((0, -1, 0)))   # sill bolt
    if buttress:
        g = g.union(box(30.0, P["post_d"], B, (-30.0, 0, 0)))
        gus = cq.Workplane("XZ").polyline([(-30.0, B), (0.0, B), (0.0, 110.0)]).close().extrude(-P["post_d"])
        g = g.union(gus)
        g = g.cut(cq.Workplane("XZ").center(-16.0, B / 2).circle(3.4).extrude(-(P["post_d"] + 2)).translate((0, -1, 0)))         # 2nd sill bolt in gusset
    else:
        g = g.cut(cq.Workplane("XY").center(P["post_w"] / 2, P["post_d"] / 2).circle(2.8).extrude(12).translate((0, 0, h - 11)))   # clip M4 insert (Ø5.6 mm)
    if mirror:
        g = g.mirror("XZ").translate((0, P["post_d"], 0))
    return g


def v12_post_clip(mirror=False, h=B, bolt_z=B / 2):
    """Top clip for a v12 post: a 40 x 20 x h block sitting on the post's top beside the top rail; horizontal 1/4-20 into the
    rail's inner slot, M4 down into the post.  The rail bolt sits 10 mm OFF the plate line (the plate stands in the post's
    centre), so a hex key reaches its head past the plate's top edge; the clip overhangs the post 8 mm each side for it."""
    g = box(P["post_w"] + 16, 20, h, (-8, 0, 0))
    g = g.cut(cq.Workplane("XZ").center(P["post_w"] / 2 - 10, bolt_z).circle(3.4).extrude(-22).translate((0, -1, 0)))
    g = g.cut(cq.Workplane("XZ").center(P["post_w"] / 2 - 10, bolt_z).circle(6.5).extrude(-4).translate((0, 20 - 3.5, 0)))   # countersink, head on the inner face
    g = g.cut(cq.Workplane("XY").center(P["post_w"] / 2, P["post_d"] / 2).circle(2.3).extrude(h + 2).translate((0, 0, -1)))
    if mirror:
        g = g.mirror("XZ").translate((0, 20, 0))
    return g


def v12_inverter_plate(a, g, inv_key, px_):
    """The MultiPlus on its long side on a fixed two-tile plate at x = px_, in single-piece posts against the depth rails."""
    inv = COMPONENTS[inv_key]
    cw = in_W - 2 * (P["post_d"] - P["slot_depth"]) - 2 * P["card_clear"]
    cy0 = y_in0 + (in_W - cw) / 2
    ch = min(inv.h + 1, 254.0)                                    # 250 (<= 254 for the bed): from z 2 to 1 above the MultiPlus's top tabs; the plate sits between the
                                                                  # posts in the rail-free middle, so it may stand 21 mm above the posts, 2 under the lid
    hpost = min(out_H - B, 254.0)                                 # posts print in one piece; the clips make up the rest to the lid
    for j, y in enumerate((y_in0, out_W - B - P["post_d"])):
        ppx = px_ - (P["post_w"] - P["card_t"]) / 2 - P["card_clear"]
        add(a, v12_post(hpost, mirror=(j == 1)).translate((ppx, y, 0)), f"print_post_inverter_{j}", ORANGE)
        clip = v12_post_clip(mirror=(j == 1), h=out_H - hpost, bolt_z=out_H - hpost - B / 2)
        add(a, clip.translate((ppx, y if j == 0 else out_W - B - 20, hpost)), f"print_post_clip_{j}", ORANGE)
    patches = [(u + (cw - inv.w) / 2, v + 2) for (u, v) in HOLES[inv_key]]
    for nm, shp in lattice_card_tiles_yz(cw, ch, px_, cy0, 2.0, "plate_inverter", patches):
        if nm.endswith("tile_00"):   # corners notched 12 wide: at the bottom for the posts' solid sills (slots start at z 30),
            shp = shp.cut(box(P["card_t"] + 2, 12, 29, (px_ - 1, cy0 - 1, 1)))          # at the top for the clips on the posts
            shp = shp.cut(box(P["card_t"] + 2, 14, 40, (px_ - 1, cy0 - 1, hpost - 0.6)))
        if nm.endswith("tile_10"):
            shp = shp.cut(box(P["card_t"] + 2, 12, 29, (px_ - 1, cy0 + cw - 11, 1)))
            shp = shp.cut(box(P["card_t"] + 2, 14, 40, (px_ - 1, cy0 + cw - 13, hpost - 0.6)))
        add(a, shp, nm, ORANGE if "spline" in nm else DARK)
    at = (px_ + P["card_t"] + V12["standoff"], cy0 + (cw - inv.w) / 2, 2.0)
    add(a, victron_shape(inv_key, inv.d, inv.w, inv.h, at, box(inv.d, inv.w, inv.h, at).edges("|X").fillet(3)), "victron_multiplus_side", BLUE)
    g["inv_front"] = at[0] + inv.d

def v12_panels(a):
    """The four slot-captured 6 mm panels (front one with FRONT_PORTS cut and the port bodies added), the lid and its handles.
    Returns the front panel's inner face x."""
    # --- panels: 6 mm, captured in the rails' centreline slots (3 mm into each slot), the way the IceBox is built ---------
    pm = B / 2 - 3                                                  # panel's outer face, inside the bar envelope
    def slot_panel(along, thick_at, length, height_rails=True):
        # a panel between the bars with 3 mm tongues into the slots: the side tongues (into the corner bars) run the
        # bar height, the top/bottom tongues (into the rails) run between the corner cubes
        # the corner cubes (C) can be bigger than the rails (B): every tongue runs between the CUBES, not the rails,
        # so the panel's corners stop where the cube's inner faces are (25.75 cubes on 25 rails, 2026-10-30)
        e = C - B                                                   # how far a cube stands past the rail faces
        if along == "x":
            body = box(length, T, out_H - 2 * B, (B, thick_at, B)).union(box(length + 6, T, out_H - 2 * C, (B - 3, thick_at, C)))
            return body.union(box(length - 2 * e, T, out_H - 2 * B + 6, (C, thick_at, B - 3)))
        body = box(T, length, out_H - 2 * B, (thick_at, B, B)).union(box(T, length + 6, out_H - 2 * C, (thick_at, B - 3, C)))
        return body.union(box(T, length - 2 * e, out_H - 2 * B + 6, (thick_at, C, B - 3)))
    back = slot_panel("y", pm, in_W)                                                          # the IceBox's perforated rear panel, cut to height
    slot_w, slot_h, pitch_y, pitch_z = 72.0, 22.0, 92.0, 46.0
    def icebox_slots(panel, x_face, first_row, n_rows, z_shift):
        # the IceBox back panel's slot rows are at z = B + 60 + r * 46 (r = 0..7) with the odd rows staggered half a pitch;
        # the box's back panel is its bottom 237 mm (rows 0-3), the front panel the offcut above it (rows 4-7, shifted down)
        for r in range(first_row, first_row + n_rows):
            z = B + 60 + r * pitch_z - z_shift
            if z < B + 4 or z + slot_h > out_H - B - 4:
                continue
            y = B + 40 + ((pitch_y / 2) if r % 2 else 0)
            while y + slot_w < out_W - B - 30:
                panel = panel.cut(cq.Workplane("YZ").center(y + slot_w / 2, z + slot_h / 2).slot2D(slot_w, slot_h).extrude(T + 8).translate((x_face - 4, 0, 0)))
                y += pitch_y
        return panel
    if P.get("perforated_back"):
        back = icebox_slots(back, pm, 0, 4, 0.0)
    if P.get("gx_touch", False):
        # Victron GX Touch 50 FLUSH (136 x 94 x 12, 800x480) let into the BACK panel at its inboard end (user, 2026-10-30): the
        # panel's inner face is 30 mm from the MultiPlus's back end there, enough for the 12 mm body and a right-angle cable plug.
        # Cut-out modelled as the body (128 x 86); VERIFY against the flush kit's template before cutting. A printed trim bezel
        # (150 x 108 x 3, four M4 self-tappers into the ply) covers the slots the opening crosses.
        tw, th, td = 136.0, 94.0, 12.0
        cw_, ch_ = 128.0, 86.0
        yc, zc = out_W - B - 80.0, 160.0                            # bezel edge 5 mm clear of the inboard corner rail
        back = back.cut(box(T + 2, cw_, ch_, (pm - 1, yc - cw_ / 2, zc - ch_ / 2)))
        bezel = box(3.0, 150.0, 108.0, (pm - 3.0, yc - 75.0, zc - 54.0)).cut(box(5.0, cw_, ch_, (pm - 4.0, yc - cw_ / 2, zc - ch_ / 2)))
        for (by, bz) in ((yc - 70, zc - 49), (yc + 70, zc - 49), (yc - 70, zc + 49), (yc + 70, zc + 49)):
            bezel = bezel.cut(cq.Workplane("YZ").center(by, bz).circle(1.8).extrude(5).translate((pm - 4.0, 0, 0)))
        add(a, bezel, "print_touch_bezel", ORANGE)
        body = box(td, cw_, ch_, (pm - 3.0 + 3.0 - 3.0, yc - cw_ / 2, zc - ch_ / 2))                 # 3 mm proud of the bezel face, 9 inside
        face = box(3.0, tw, th, (pm - 6.0, yc - tw / 2, zc - th / 2))                                 # the glass and its flange, on the bezel
        add(a, body.translate((-3.0 + 3.0, 0, 0)).union(face), "gx_touch_50", BLACK)
        add(a, box(15.0, 40.0, 20.0, (pm - 3.0 + td, yc - 20.0, zc - 10.0)), "gx_touch_cable_plug", (0.3, 0.3, 0.3))   # right-angle plug room
    for nm, shp in (("panel_side_outboard_from_icebox", slot_panel("x", pm, in_D)),          # cut down from the IceBox's side panels
                    ("panel_side_inboard_from_icebox", slot_panel("x", out_W - pm - T, in_D)),
                    ("panel_back_perforated_from_icebox", back)):
        add(a, shp, nm, PANEL)
    front = slot_panel("y", out_D - pm - T, in_W)
    xf = out_D - pm - T                                            # the front panel's inner face
    if P.get("icebox_front") == "bezel":   # the slotted rear-panel offcut (IceBox rows 4-7) with a 139 x 210 opening for a printed port bezel behind it
        front = icebox_slots(front, xf, 4, 4, 237.0)
        opening = (318.0, 457.0, 34.0, 244.0)
        front = front.cut(box(T + 2, opening[1] - opening[0], opening[3] - opening[2], (xf - 1, opening[0], opening[2])))
        bezel = box(T, 461.0 - 308.0, 254.0 - 27.0, (xf - T, 308.0, 27.0))   # 153 x 227 x 6, one print, between the rails, 10 mm behind the opening's
        for (by, bz) in ((313, 60), (313, 140), (313, 220), (340, 249), (440, 249)):   # outboard edge; 5 x M4 countersunk from outside into
            front = front.cut(cq.Workplane("YZ").center(by, bz).circle(2.3).extrude(T + 2).translate((xf - 1, 0, 0)))   # inserts in the bezel
            bezel = bezel.cut(cq.Workplane("YZ").center(by, bz).circle(2.8).extrude(T + 2).translate((xf - T - 1, 0, 0)))
        xf_ports = xf - T                                          # the port bodies stand off the bezel's inner face
    else:
        bezel = None; xf_ports = xf
    for port in FRONT_PORTS:   # bodies point -X from the front panel's inner face
        kind, y, z = port[0], port[1], port[2]
        tgt = bezel if bezel is not None else front
        if kind == "socket":
            r = port[3] / 2
            tgt = tgt.cut(cq.Workplane("YZ").center(y, z).circle(r).extrude(T + 2).translate((xf_ports - 1, 0, 0)))
            add(a, cq.Workplane("YZ").center(y, z).circle(r + 3).extrude(-40).translate((xf_ports, 0, 0)), f"socket_{int(y)}_{int(z)}", (0.3, 0.3, 0.3))
        elif kind.startswith("l14"):
            tgt = tgt.cut(cq.Workplane("YZ").center(y, z).circle(30).extrude(T + 2).translate((xf_ports - 1, 0, 0)))
            add(a, cq.Workplane("YZ").center(y, z).circle(30).extrude(-55).translate((xf_ports, 0, 0)), f"socket_{kind}", (0.3, 0.3, 0.3))
        else:
            w_, h_, d_ = PORT_FACE["sb175" if kind.startswith("sb175") else "sb50"]
            tgt = tgt.cut(box(T + 2, w_, h_, (xf_ports - 1, y - w_ / 2, z - h_ / 2)))
            add(a, box(d_, w_, h_, (xf_ports - d_, y - w_ / 2, z - h_ / 2)), f"socket_{kind}", (0.3, 0.3, 0.3))
        if bezel is not None: bezel = tgt
        else: front = tgt
    # the front panel is PRINTED (the ports are cut in it): two tiles on a vertical 20 mm half-lap at mid-width, the outboard
    # tile keeping the outer half of the thickness across the lap, 3 x M4 through the lap (nuts on the bench); it slides into
    # the rails' slots like the sheet panels
    if bezel is not None or P.get("icebox_front") == "side":
        if bezel is not None:
            add(a, front, "panel_front_slotted_from_icebox", PANEL)
            add(a, bezel, "print_port_bezel", ORANGE)
        else:   # a solid offcut of an IceBox side panel (762 x 277 left after the side is cut to 237): the ports go straight through it
            add(a, front, "panel_front_solid_from_icebox_side", PANEL)
        if P.get("lid_slot"):   # v13: the lid sits in the 4 top rails' inner-face slots (z = out_H - B/2 - T/2 .. +T), 3 mm into each slot
            lz0 = out_H - B / 2 - T / 2
            lid = box(in_D + 6, out_W - 2 * C, T, (B - 3, C, lz0)).union(box(out_D - 2 * C, in_W + 6, T, (C, B - 3, lz0)))
            add(a, lid, "lid_from_icebox_top", PANEL)
            for y in (out_W * 0.3, out_W * 0.7):
                add(a, lid_handle().translate((out_D / 2 - 6, y - 30, lz0 + T)), f"lid_handle_{int(y)}", BLACK)
        else:
            add(a, box(out_D, out_W, T, (0, 0, out_H)), "lid_from_icebox_top", PANEL)
            for y in (out_W * 0.3, out_W * 0.7):
                add(a, lid_handle().translate((out_D / 2 - 6, y - 30, out_H + T)), f"lid_handle_{int(y)}", BLACK)
        return xf
    ymid, lw = B + in_W / 2, 20.0
    big = out_H + 40
    outb = front.intersect(box(40, ymid + lw / 2 + 20, big, (xf - 20, -20, -20))).cut(box(3.0 + 1, lw, big, (xf - 1, ymid - lw / 2, -20)))
    inb = front.intersect(box(40, out_W, big, (xf - 20, ymid - lw / 2, -20))).cut(box(T - 3.0 + 1, lw, big, (xf + 3.0, ymid - lw / 2, -20)))
    for zb in (60, 140, 220):
        bolt = cq.Workplane("YZ").center(ymid, zb).circle(2.3).extrude(T + 2).translate((xf - 1, 0, 0))
        outb, inb = outb.cut(bolt), inb.cut(bolt)
    add(a, outb, "print_panel_front_outboard", ORANGE)
    add(a, inb, "print_panel_front_inboard_ports", ORANGE)
    add(a, box(out_D, out_W, T, (0, 0, out_H)), "lid_from_icebox_top", PANEL)                    # the IceBox's top panel, uncut
    for y in (out_W * 0.3, out_W * 0.7):
        add(a, lid_handle().translate((out_D / 2 - 6, y - 30, out_H + T)), f"lid_handle_{int(y)}", BLACK)
    return xf


def build_v12(a):
    """Half-height IceBox footprint, not card based.  Back: 2 x 2 SuperPacks in one layer in the v9 trays (tabbed to the
    rails, bolted to each other).  Column beside them: a printed bus shelf (breakers, shunt, Cerbo flat on a pedestal, bus bars) with
    lips bolted to the trays and flanges on the inboard rail.  Front: the MultiPlus on its long side, bolted to a fixed
    two-tile plate in rail-footed posts; the Orion and the port strip on the front panel's inside, the MPPT (upright) and
    the Garmin on the inboard side panel's inside.  Everything is reached from the top with the lid off."""
    g = dict()
    b = COMPONENTS["battery"]; wall, lip = 6.0, 30.0
    fd, fw = b.d + 2 * wall, b.w + 2 * wall           # 241 x 150
    bay_D = V12["end_gap"] + 2 * (fd + 12) + V12["row_gap"]   # trays with their 6 mm pads, back to back
    g["bay_D"] = bay_D
    # --- trays: two rows, two columns ------------------------------------------
    for r in range(2):
        for c in range(2):
            tx = x_in0 + V12["end_gap"] + r * (fd + 12 + V12["row_gap"])
            ty = y_in0 + 1 + c * fw
            tray = box(fd, fw, lip + 4).cut(box(b.d, b.w, lip + 5, (wall, wall, 4)))
            tray = tray.cut(box(fd + 2, 28, 5, (-1, wall + b.w / 2 - 14, 2)))            # lengthwise strap channel
            for (px, py) in ((-6, 12), (-6, fw - 32), (fd, 12), (fd, fw - 32)):           # corner pads, M4 inserts
                tray = tray.union(box(6, 20, lip + 4, (px, py, 0)))
            for (px, py) in ((-6, 12), (-6, fw - 32), (fd, 12), (fd, fw - 32)):
                tray = tray.cut(cq.Workplane("XY").center(px + 6.0 if px < 0 else px, py + 10).circle(2.8).extrude(13).translate((0, 0, lip + 4 - 12)))
            for (hx, hy) in ((wall + 20, wall + 20), (wall + b.d - 20, wall + 20), (wall + 20, wall + b.w - 20), (wall + b.d - 20, wall + b.w - 20)):
                tray = tray.cut(cq.Workplane("XY").center(hx, hy).circle(3.4).extrude(5))   # M6 to the plate, optional
            if c == 0:   # outboard column: two countersunk 1/4-20 through the outer wall at the rail's slot height into T-nuts
                for sx in (60, fd - 60):   # (the rails' top slots hold the side panels, so the inner slot is the only one free)
                    tray = tray.cut(cq.Workplane("XZ").center(sx, B / 2).circle(3.4).extrude(-(wall + 2)).translate((0, -1, 0)))
                    tray = tray.cut(cq.Workplane("XZ").center(sx, B / 2).circle(6.5).extrude(-3).translate((0, wall + 0.5, 0)))   # countersink, head flush inside
            # row mates bolt through their touching side walls (2 x M5, on the bench); rows bolt pad to pad (M4)
            for hx in (60, 180):
                tray = tray.cut(cq.Workplane("XZ").center(hx, 17).circle(2.7).extrude(-(wall + 2)).translate((0, (fw - wall - 1) if c == 0 else -1, 0)))
            if c == 1:   # inboard column: 3 x M4 through the inboard wall into the bus shelf's lip inserts
                for hx in (40, 120, 200):
                    tray = tray.cut(cq.Workplane("XZ").center(hx, 17).circle(2.3).extrude(-(wall + 2)).translate((0, fw - wall - 1, 0)))
            add(a, tray.translate((tx, ty, 0)), f"print_tray_battery_{r}{c}", ORANGE)
            at = (tx + wall, ty + wall, 4)
            add(a, victron_shape("battery", b.d, b.w, b.h, at, box(b.d, b.w, b.h, at).edges("|Z").fillet(6)), f"battery_{r}{c}", BATT)
    # --- bus shelf in the column (y from the inboard trays' wall to the inboard rail) ---------------------------------
    y0s, y1s = y_in0 + 1 + 2 * fw, out_W - B - 1                 # 328.4 .. 436.0
    xs0, xs1 = x_in0 + 1, x_in0 + bay_D
    n_pl = 3; seg = (xs1 - xs0) / n_pl
    for i in range(n_pl):
        xa, xb = xs0 + i * seg, xs0 + (i + 1) * seg
        sh = box(xb - xa, y1s - y0s, 6, (xa, y0s, 0))
        sh = sh.union(box(xb - xa, 6, 34, (xa, y0s, 0)))                     # lip against the trays' inboard walls (M4 inserts)
        for hx in (40, 120, 200):
            for r in range(2):
                tx = x_in0 + V12["end_gap"] + r * (fd + 12 + V12["row_gap"])
                if xa + 6 < tx + hx < xb - 6:
                    sh = sh.cut(cq.Workplane("XZ").center(tx + hx, 17).circle(2.3).extrude(-8).translate((0, y0s - 1, 0)))
        sh = sh.union(box(xb - xa, 6, 34, (xa, y1s - 6, 0)))                 # outer wall, 1 mm off the inboard rail's inner face
        for sx in (xa + 40, xb - 40):   # two countersunk 1/4-20 through it at the rail's slot height, heads flush inside the shelf
            sh = sh.cut(cq.Workplane("XZ").center(sx, B / 2).circle(3.4).extrude(-8).translate((0, y1s - 7, 0)))
            sh = sh.cut(cq.Workplane("XZ").center(sx, B / 2).circle(6.5).extrude(-3).translate((0, y1s - 6 + 0.5 + 3, 0)))
        add(a, sh, f"print_bus_shelf_{i}", ORANGE)
    V12_SHELF = [dict(comp="breaker_a", x=40, y=8), dict(comp="breaker_b", x=135, y=8), dict(comp="shunt_x", x=230, y=8),
                 dict(comp="busbar_px", x=40, y=69), dict(comp="busbar_nx", x=200, y=69)]
    for pl in V12_SHELF:
        c = COMPONENTS[pl["comp"]]
        at = (xs0 + pl["x"], y0s + 6 + pl["y"], 6 + pl.get("z", 0))
        if pl["comp"] == "cerbo_flat":   # pedestal on the shelf: four M4-insert bosses under the lugs and a U wall (open on the rail side so the
            z0 = pl["z"]; cx, cy = at[0], at[1]                       # shelf's rail bolts stay reachable), lifting the Cerbo above the 34 mm lips
            ped = box(c.d + 8, 4, z0, (cx - 4, cy - 4, 6))                                       # wall along the tray side
            ew = y1s - 6 - 0.5 - (cy - 4)                                                      # end walls stop short of the shelf's outer wall
            ped = ped.union(box(4, ew, z0, (cx - 4, cy - 4, 6))).union(box(4, ew, z0, (cx + c.d, cy - 4, 6)))
            for (hx, hy) in HOLES["cerbo_flat"]:
                ped = ped.union(cq.Workplane("XY").center(cx + hx, cy + hy).circle(6).extrude(z0).translate((0, 0, 6)))
                ped = ped.cut(cq.Workplane("XY").center(cx + hx, cy + hy).circle(2.8).extrude(12).translate((0, 0, 6 + z0 - 12)))
            add(a, ped, "print_cerbo_pedestal", ORANGE)
        col = BLUE if c.name.startswith("victron") else GOLD
        add(a, victron_shape(pl["comp"], c.d, c.w, c.h, at, unit_fallback(pl["comp"], c.d, c.w, c.h, at)), c.name + f"_shelf_{int(pl['x'])}", col)
    # --- MultiPlus on its long side on a fixed plate at the front ----------------------------------------------------
    px_ = x_in0 + bay_D + V12["plate_gap"]
    v12_inverter_plate(a, g, "multiplus_1200_side", px_)
    xf = v12_panels(a)
    # --- front panel inside: the Garmin PowerSwitch on a printed mount beside the ports it feeds (mount screwed through ---
    ga = COMPONENTS["garmin"]                                      # the panel from outside into inserts)
    gy, gz = y_in0 + 20, 60.0                                      # outboard side: the port strip has the inboard 150 mm
    add(a, box(6, ga.w + 20, ga.h + 20, (xf - 6, gy - 10, gz - 10)), "print_mount_garmin", ORANGE)
    at = (xf - 6 - ga.d - 3, gy, gz)
    add(a, victron_shape("garmin", ga.d, ga.w, ga.h, at, box(ga.d, ga.w, ga.h, at).edges("|X").fillet(3)), "garmin_powerswitch_front", (0.08, 0.08, 0.08))
    # --- inboard side panel inside, over the bus shelf: Cerbo, Orion and MPPT (upright) on printed mounts, lugs to the panel
    pm = B / 2 - 3                                                 # panel's outer face, inside the bar envelope (as in v12_panels)
    yf = out_W - pm - T                                            # the inboard panel's inner face
    V12_WALL = (("cerbo", x_in0 + 25, 120.0, "cerbo"),            # long edges horizontal: plugs out the top and bottom edges
                ("orion", x_in0 + 215, 60.0, "orion"),            # over the shunt and the (-) bus bar, 22 mm clear of them
                ("mppt_up", x_in0 + 370, 38.0, "mppt"))           # nearest the MultiPlus, nothing on the shelf under it
    for comp, x0, z0, nm in V12_WALL:
        c = COMPONENTS[comp]
        add(a, box(c.w + 20, 6, c.h + 8, (x0 - 10, yf - 6, z0 - 4)), f"print_mount_{nm}", ORANGE)   # all under the top rail (229)
        at = (x0, yf - 6 - c.d - 3, z0)   # 3 mm off the mount: the STEP bodies carry brackets past the bbox
        add(a, victron_shape(comp, c.w, c.d, c.h, at, box(c.w, c.d, c.h, at).edges("|Y").fillet(3), lugs=("y", +1)), f"{c.name}_side", BLUE)
    BS["_g12"] = g
    return g


V13 = dict(end_gap=10.0, row_gap=2.0, floor=6.0, standoff=2.0, plate_y=303.0, col_wall=4.0, inv_x=46.0, shelf_x0=46.0, shelf_x1=730.0, tray_lap=20.0,
           lip_holes=(((40, 100, 160), (40, 150, 260)), ((40, 100, 160), (40, 150, 200))))   # (200Ah trays, 60Ah trays): x from each tray's back end, clear of the breakers
V13_COL = [dict(comp="shunt_x", x=215, y=1),                                                 # row 1: the SmartShunt (52 tall) under the Cerbo, which sits high
           dict(comp="busbar_px", x=60, y=62), dict(comp="busbar_nx", x=220, y=62)]           # row 2 (38 tall) under the MPPT: 42 mm under its terminals
V13_PLATE_UNITS = (("mppt_up", 70.0, 80.0, "mppt"), ("cerbo", 215.0, 130.0, "cerbo"), ("orion", 380.0, 80.0, "orion"),   # on the plate's column face;
                   ("garmin", 510.0, 40.0, "garmin"),                                                                      # nothing on the shelf under the Orion
                   ("breaker_face", 515.0, 175.0, "breaker1"), ("breaker_face", 612.0, 175.0, "breaker2"))                 # breakers high, 48 under the lid
V13_SHORT = dict(   # the 635 mm box (2026-10-24 layout): ONE ROW of charge gear along the top of the plate's column face, tops at the MPPT's
    # (266; the Orion 11 lower so its lugs clear the tile lap), the band under them open for the lugs and cables to the shelf's bus bars and
    # shunt; the Garmin turned 90 deg on the plate's INVERTER face above the cable window, 59 mm in front of the MultiPlus's cable end and
    # 18 mm behind the socket bodies, so only its feed passes through the window and its outputs run straight to the front-panel ports.
    # (comp, x, z, tag[, side]): side +1 = inverter face, default -1 = column face. Unit heights keep every insert out of the lap (z 137-161).
    units=(("mppt_up", 50.0, 80.0, "mppt"), ("cerbo", 190.0, 188.0, "cerbo"), ("orion", 354.0, 118.0, "orion"),
           ("breaker_face", out_D - 150.0, 110.0, "breaker1"), ("breaker_face", out_D - 150.0, 185.0, "breaker2")),   # (breakers: pre-drop-shelf, filtered out)
    # The window is placed from the FRONT rail (out_D - ...) so it rides with the box depth. At 571.5 deep (2026-10-30) the 63.5 mm
    # that used to separate the MultiPlus's cable end from the Garmin on the plate's inverter face is gone, so the Garmin LIES FLAT ON
    # THE BUS SHELF's front plate instead (col below), beside the window, its outputs 60 mm from the front-panel sockets.
    # 2026-11-01: ALL THREE on the TRAY side of the shelf, one stud line 17 mm from the lip's inner face (the bars 1 mm off the lip, ears 16 in;
    # the shunt's stud edge 4.5 off it, slots 12.5 in), so the (+) bar, shunt and (-) bar read as one straight bus and the inboard 57 mm band
    # under the plate's cable window is empty: the inverter, Orion and Garmin leads coming through the window land on bare shelf, not on a bus bar.
    # (Before: the bars sat in the inboard row under the window with the shunt alone on the tray side.)
    col=[dict(comp="shunt_x", x=226, y=4.5), dict(comp="busbar_px", x=45, y=1), dict(comp="busbar_nx", x=366, y=1)],
    # (shelf units: Ø6.4 mm M5 heat-set insert bores pre-printed in plates 0, 1, 2.  The Garmin hangs from the top
    # inboard rail on its own printed plate, see garmin_hanger in build_v13, 2026-10-30)
    window=(out_D - 145.0, out_D - 75.0, 40.0, 110.0),
    lip_holes=(((40, 100, 160), (40, 150, 260)), ((40, 100, 140), (40, 120, 200))))


COUNTERSINKS = []   # (part name, face point, unit axis INTO the part): every conical countersink, for check_countersinks (--clash)


def countersink(part, face_pt, axis):
    """An 82-degree countersink for a 1/4-20 flat head (13.2 mm at the face, 3.6 mm deep to the 6.8 mm hole), starting
    0.5 mm outside the face so the cut is through.  Registers itself so --clash can probe that it really opens the face.
    (2026-10-25: the earlier 'countersinks' were 13 mm counterbores placed 0.5 mm OFF the wall, in air: no cut at all on
    the trays, brackets and shelf front wall, so their flat heads would have stood 4 mm proud against the batteries.)"""
    ax = cq.Vector(*axis).normalized()
    pnt = cq.Vector(*face_pt) - ax * 0.5
    COUNTERSINKS.append((part, tuple(face_pt), tuple(axis)))
    return cq.Workplane("XY").add(cq.Solid.makeCone(7.0, 3.4, 4.1, pnt, ax))



# ----------------------------------------------------------------------------------------------------------------------
# Stack strap: ties the box to the IceBox it rides on (user, 2026-10-31, after the Goose Gear corner gusset in the photo:
# a 4 mm plate with button heads into the rails' outer slots).  The box stands RAIL ON RAIL on the IceBox (both frames
# are MaxLite 25 mm metric rail, 6.5 mm slot, 1/4-20 drop-in T-nuts; the panels sit in the rails' centre slots, so every
# outer rail face is bare), so the tie is a flat strap across the seam: two bolts into the box's bottom depth rail, two
# into the IceBox's top depth rail directly under it.  Nothing reaches round a corner, nothing meets a cube.
# ----------------------------------------------------------------------------------------------------------------------
STRAP = dict(
    t=4.0,            # plate thickness (user: 4 mm, like the Goose Gear gusset)
    w=60.0, h=46.0,   # along the rail x up the two rails: the 46 stays inside the two 25 mm rail faces (50) by 2 mm each way
    pitch_x=30.0,     # the two bolts along each rail
    pitch_z=25.75,    # slot centreline to slot centreline: 12.5 from each rail's face + the 0.375 each cube stands proud (cube on cube)
    hole=6.8,         # 1/4-20 clearance
    slot=2.4,         # the upper pair are vertical slots: the cubes stand 0.375 - 0.75 proud, so the seam gap is 0.75 - 1.5 and the pitch 25.75 - 26.5
    r=10.0,           # corner radius
    clear_cube=70.0,  # strap edge to the nearest corner cube along the rail: past the Goose Gear gusset on the IceBox's top corner (~65)
)
_DXF_DONE = set()


def stack_strap():
    """The strap lying flat in XY (x along the rail, y up the rails with the seam at y 0, thickness z 0..t), as it prints.
    rotate((1,0,0), 90) stands it on a rail face with the seam at z 0 and the plate at y -t..0 (the outboard face)."""
    s = STRAP; w, h, t = s["w"], s["h"], s["t"]
    pl = box(w, h, t, (-w / 2, -h / 2, 0)).edges("|Z").fillet(s["r"])
    for sx in (-s["pitch_x"] / 2, s["pitch_x"] / 2):
        pl = pl.cut(cq.Workplane("XY").center(sx, -s["pitch_z"] / 2).circle(s["hole"] / 2).extrude(t + 2).translate((0, 0, -1)))          # IceBox rail: round
        pl = pl.cut(cq.Workplane("XY").center(sx, s["pitch_z"] / 2).slot2D(s["hole"] + s["slot"], s["hole"], 90).extrude(t + 2).translate((0, 0, -1)))   # box rail: 2.4 mm of float
    return pl


def add_stack_straps(a):
    """Four straps, two per side of the box (outboard y 0, inboard y out_W), one near each end of the bottom depth rails, each
    clear_cube past the corner cube so it misses the IceBox's own Goose Gear gussets.  Also writes the outline as a DXF next
    to the STLs for anyone who would rather have it cut from 4 mm aluminium."""
    s = STRAP
    xs = (C + s["clear_cube"] + s["w"] / 2, out_D - C - s["clear_cube"] - s["w"] / 2)
    flat = stack_strap()
    up = flat.rotate((0, 0, 0), (1, 0, 0), 90)                     # plate at y -t..0, seam at z 0
    for i, x in enumerate(xs):
        add(a, up.translate((x, 0, 0)), f"print_stack_strap_out_{i}", ORANGE)
        add(a, up.translate((x, out_W + s["t"], 0)), f"print_stack_strap_in_{i}", ORANGE)
    if VARIANT not in _DXF_DONE:
        _DXF_DONE.add(VARIANT); os.makedirs(STL, exist_ok=True)
        cq.exporters.exportDXF(flat.faces("<Z"), os.path.join(STL, "print_stack_strap.dxf"))


def build_v13(a):
    """v12 grown one inch (282 tall) for a 1500 W AC load, MultiPlus-II 12/3000/120-50 as asked.  The II is 578 x 277 x 148
    and does not fit the v12 box any way up, so it lies on its LONG SIDE along the inboard side of the box: back on a
    printed plate that runs the depth, cable end forward into a 100 mm front zone where the ports are.  Two Lithium Smart
    12.8V/200Ah (400 A bank) stand end to end along the outboard side in v12-style trays; the bus column (breakers, shunt,
    bus bars) runs between the trays and the plate, and the MPPT, Orion and Cerbo hang on the plate's column face.
    Garmin flat on the floor in the front zone.  Ties: trays into the outboard rail's inner slot, plate in posts against
    the width rails (sill bolts + top clips) and bolted to the bus shelf's inboard wall."""
    g = dict()
    short = out_D < 700.0
    bkey = P.get("batt", "smart200"); small = bkey == "battery"   # v12: two SuperPack 60Ah in the same zone, trays 167 wide like v13's
    b = COMPONENTS[bkey]; wall, lip, fl = 6.0, 30.0, V13["floor"]
    clr = P.get("tray_clr", 1.0 if small else 1.5)   # pocket clearance each side (v12s: 0.5, a snug fit, user 2026-10-25)
    bs = COMPONENTS["smart200"]
    fw = bs.w + 2 * wall + 2 * 1.5                                 # 167: the shelf lip is in the same place for both batteries
    fd = b.d + 2 * wall + 2 * clr                                  # 336 (200Ah) or 243 (60Ah)
    pw = b.w + 2 * clr                                             # pocket width: 155 or 140
    direct = bool(P.get("clean_trays"))   # 2026-10-25: the trays BUTT the width rails and bolt straight into them (no brackets)
    if small and direct:
        txs = (x_in0, out_D - B - fd)   # tray 0's back wall on the back rail, tray 1's front wall on the front rail
    elif small:   # the two 60Ah trays sit at the two ends of the zone so both rail brackets reach their rails
        txs = (x_in0 + V13["end_gap"] + 6, out_D - B - 3 - 6 - fd)
    else:
        txs = tuple(x_in0 + V13["end_gap"] + 6 + r * (fd + 12 + V13["row_gap"]) for r in range(2))
    bay_D = txs[1] + fd + (0 if direct else 6) - x_in0
    g["bay_D"] = bay_D
    lip_holes = (V13_SHORT if short else V13)["lip_holes"][1 if small else 0]   # per tray, placed where the column has no part over the lip
    ty = y_in0 + 1
    for r in range(2):
        tx = txs[r]
        tray = box(fd, fw, lip + fl).cut(box(fd - 2 * wall, pw, lip + fl + 1, (wall, wall, fl)))
        if P.get("cube", B) > B + 0.05:   # the corner cube stands proud of both rail faces: a 2 mm notch down the tray's outer-end corner clears it
            tray = tray.cut(box(2.5, 2.5, lip + fl + 2, ((-1.0 if r == 0 else fd - 1.5), -1.0, -1.0)))
        if P.get("strap", True):   # v12s: no strap (the drop shelf is the hold-down), so no groove and no slots through the end walls
            tray = tray.cut(box(fd + 2, 28, 5, (-1, wall + pw / 2 - 14, fl - 2)))                  # lengthwise strap groove, 4 mm of floor under it
        pads = ((-6, 12), (-6, fw - 32), (fd, 12), (fd, fw - 32))
        if direct:                 # no pads: the end walls bolt to the rails themselves
            pads = ()
        elif P.get("clean_trays"):   # only the two pads that take this tray's rail brackets (back end of tray 0, front end of tray 1)
            pads = tuple(pd for pd in pads if (pd[0] < 0) == (r == 0))
        for (px, py) in pads:                                                                    # corner pads, M4 inserts from the top
            tray = tray.union(box(6, 20, lip + fl, (px, py, 0)))
        for (px, py) in pads:
            tray = tray.cut(cq.Workplane("XY").center(px + 6.0 if px < 0 else px, py + 10).circle(2.8).extrude(13).translate((0, 0, lip + fl - 12)))
        if not P.get("clean_trays"):
            for (hx, hy) in ((wall + 25, wall + 25), (wall + b.d - 25, wall + 25), (wall + 25, wall + pw - 25), (wall + b.d - 25, wall + pw - 25)):
                tray = tray.cut(cq.Workplane("XY").center(hx, hy).circle(3.4).extrude(fl + 1))     # M6 to the plate, optional
        for sx in (70, fd - 70):   # outboard wall: two countersunk 1/4-20 into the outboard rail's inner slot, heads flush inside
            tray = tray.cut(cq.Workplane("XZ").center(sx, B / 2).circle(3.4).extrude(-(wall + 2)).translate((0, -1, 0)))
            tray = tray.cut(countersink(f"print_tray_battery_{r}", (tx + sx, ty + wall, B / 2), (0, -1, 0)).translate((-tx, -ty, 0)))
        if direct:                 # end wall on the width rail: two countersunk 1/4-20 into its inner slot, heads flush inside the pocket
            xw = wall if r == 0 else fd - wall                                   # the wall's inner face
            for sy in (28, fw - 28):                                             # clear of the strap channel (62..90) and the side walls
                tray = tray.cut(cq.Workplane("YZ").center(sy, B / 2).circle(3.4).extrude(wall + 2).translate(((-1 if r == 0 else fd - wall - 1), 0, 0)))
                tray = tray.cut(countersink(f"print_tray_battery_{r}", (tx + xw, ty + sy, B / 2), ((-1, 0, 0) if r == 0 else (1, 0, 0))).translate((-tx, -ty, 0)))
        for hx in lip_holes[r]:   # inboard wall: 3 x M4 heat-set inserts in its outer face; the shelf's lip bolts to them from the column
            tray = tray.cut(cq.Workplane("XZ").center(hx, 17).circle(2.8).extrude(-8).translate((0, fw - 7, 0)))         # side (heads reachable from above)
        # the tray is 345 long, so it prints as two halves joined on a 20 mm half-lap at mid-length: the back half keeps the
        # floor's lower half and the walls' outer halves across the lap, the front half the rest; 2 x M4 down through the
        # floor lap (countersunk, under the battery) and 1 x M4 through each wall lap, nuts in pockets, all on the bench
        if fd + 12 > 256:
            mid, lw = fd / 2, V13["tray_lap"]
            a_keep = (box(lw, 4, 60, (mid - lw / 2, -1, -1)).union(box(lw, 4, 60, (mid - lw / 2, fw - 3, -1)))
                      .union(box(lw, fw + 2, fl / 2 + 1, (mid - lw / 2, -1, -1))))
            zone = box(lw, fw + 2, 60, (mid - lw / 2, -1, -1))
            half_a = tray.intersect(box(mid + lw / 2 + 10, fw + 20, 60, (-10, -10, -1))).cut(zone.cut(a_keep))
            half_b = tray.intersect(box(fd + 20, fw + 20, 60, (mid - lw / 2, -10, -1))).cut(a_keep)
            for hy in (fw * 0.3, fw * 0.7):
                bolt = cq.Workplane("XY").center(mid, hy).circle(2.3).extrude(fl + 2).translate((0, 0, -1))
                half_a, half_b = half_a.cut(bolt), half_b.cut(bolt)
            for yb in (-1, fw - wall - 1):
                bolt = cq.Workplane("XZ").center(mid, 20).circle(2.3).extrude(-(wall + 2)).translate((0, yb, 0))
                half_a, half_b = half_a.cut(bolt), half_b.cut(bolt)
            add(a, half_a.translate((tx, ty, 0)), f"print_tray_battery_{r}_back", ORANGE)
            add(a, half_b.translate((tx, ty, 0)), f"print_tray_battery_{r}_front", ORANGE)
        else:   # a 60Ah tray with its pads is 255: one print
            if P.get("breaker_shelf"):   # two M4 inserts down into the 21 mm inboard wall's top, under the drop shelf's foot (same in v12s and v13)
                xs_ = wall + clr + (b.d - 130) / 2
                for hx in (25, 105):
                    tray = tray.cut(cq.Workplane("XY").center(xs_ + hx, fw - wall - 15 + 13).circle(2.8).extrude(13).translate((0, 0, lip + fl - 12)))
            add(a, tray.translate((tx, ty, 0)), f"print_tray_battery_{r}", ORANGE)
        # L brackets from the tray's outer pads to the width rail behind it (r 0) or in front of it (r 1): the horizontal leg bolts
        # down into the pad's M4 insert, the vertical leg takes a countersunk 1/4-20 into the rail's inner slot (T-nut).
        # Not with direct trays (v12s since 2026-10-25): the end walls bolt to the rails themselves.
        for k, py in (() if direct else enumerate((12, fw - 32))):
            if r == 0:
                xr, hx = x_in0, tx                                       # rail inner face, pad insert centre (at the pad/wall boundary)
                br = box(hx + 5 - xr, 20, 6, (xr, 0, lip + fl)).union(box(6, 20, lip + fl + 6, (xr, 0, 0)))
                br = br.cut(cq.Workplane("YZ").center(10, B / 2).circle(3.4).extrude(8).translate((xr - 1, 0, 0)))
                br = br.cut(cq.Workplane("YZ").center(10, B / 2).circle(6.5).extrude(3).translate((xr + 6.5, 0, 0)))
            else:               # the front pads end 3 mm off the front rail, so the vertical leg stands beside the pad (y 20..40)
                xr, hx = out_D - B, tx + fd
                br = box(xr - (hx - 5), 40, 6, (hx - 5, 0, lip + fl)).union(box(6, 20, lip + fl + 6, (xr - 6, 20, 0)))
                br = br.cut(cq.Workplane("YZ").center(30, B / 2).circle(3.4).extrude(8).translate((xr - 7, 0, 0)))
                br = br.cut(cq.Workplane("YZ").center(30, B / 2).circle(6.5).extrude(3).translate((xr - 9.5, 0, 0)))
            br = br.cut(cq.Workplane("XY").center(hx, 10).circle(2.3).extrude(8).translate((0, 0, lip + fl - 1)))
            add(a, br.translate((0, ty + py, 0)), f"print_tray_rail_bracket_{r}{k}", ORANGE)
        at = (tx + wall + clr, ty + wall + clr, fl)
        add(a, victron_shape(bkey, b.d, b.w, b.h, at, box(b.d, b.w, b.h, at).edges("|Z").fillet(6)), f"battery_{r}", BATT)
        g[f"tx{r}"] = tx
    if P.get("breaker_shelf"):   # one drop shelf per battery, doubling as its HOLD-DOWN: a 6 mm plate on a 3 mm closed-cell pad pressed onto the
        body_h = P.get("batt_body_h", b.h); pad = P.get("shelf_pad", 3.0)   # SuperPack 60Ah: 213 overall is to the TOP OF THE TERMINALS; the flat body
        drop = P.get("shelf_drop", 0.0)                           # top is at 208 (Victron STEP: 5 mm studs), so the pad sits on the body with no gap
        zs = fl + body_h + pad - drop                             # (2026-10-24: the printed shelf stood ~3/8 in off the battery at 213 + 3; 2026-10-25:
                                                                  # 2 mm of daylight remained at 208 + 3, so shelf_drop=2 and the pad space is pad - drop)
        hz = out_H - B / 2                                        # 21 mm inboard wall (two M4 down into inserts in the wall top); the breaker on top
        for r in range(2):
            tx = txs[r]; xs = tx + wall + clr + (b.d - 130) / 2   # 130 long, centred on the battery, clear of the terminals at its ends
            yw = ty + fw - wall - 15                              # leg at the inner edge of the 21 mm inboard wall (y 172..193)
            wt = lip + fl                                         # wall top, z 36
            if P.get("lid_slot"):   # v13: uses the exact v12s battery tray; outboard leg stands down on the 6 mm outboard tray wall (y 26..32, z 36..239)
                                    # while the inboard leg + 15 mm foot bolts into the same 2 x M4 inserts in the 21 mm inboard tray wall (top rail slot 100% free)
                sh = box(130, yw + 6 - ty, 6, (xs, ty, zs))                                                       # plate from outboard leg to inboard leg (y 26..178)
                sh = sh.union(box(130, 6, zs + 24 - wt, (xs, ty, wt)))                                            # outboard leg down onto the 6 mm outboard tray wall + 18 mm lip
                sh = sh.union(box(130, 6, zs + 24 - wt, (xs, yw, wt)))                                            # inboard leg down onto the 21 mm inboard tray wall + 18 mm lip
                sh = sh.union(box(130, 15, 6, (xs, yw + 6, wt)))                                                  # inboard foot over the 21 mm wall top: 2 x M4 down into it
                for (gy, dy, rs) in ((ty + 6, 1, 18), (yw, -1, 5)):                                               # full-length 18 mm and 5 mm corner ribs above the plate
                    rib = cq.Workplane("YZ").polyline([(gy, zs + 6), (gy + rs * dy, zs + 6), (gy, zs + 6 + rs)]).close().extrude(130).translate((xs, 0, 0))
                    sh = sh.union(rib)
                for hx in (25, 105):
                    sh = sh.cut(cq.Workplane("XY").center(xs + hx, yw + 13).circle(2.3).extrude(8).translate((0, 0, wt - 1)))        # 2 x M4 down through the inboard foot
            else:
                sh = box(130, yw + 6 - y_in0, 6, (xs, y_in0, zs))                                                # plate from the rail face to the leg
                sh = sh.union(box(130, 6, out_H - 3 - zs, (xs, y_in0, zs)))                                      # hanger up the top rail's inner face
                sh = sh.union(box(130, 6, zs + 24 - wt, (xs, yw, wt)))                                            # leg down onto the wall top, 24 up past the plate as a lip
                sh = sh.union(box(130, 15, 6, (xs, yw + 6, wt)))                                                  # foot over the wall top: 2 x M4 down into it
                for (gy, dy, rs) in ((y_in0 + 6, 1, 18), (yw, -1, 5)):                                           # full-length ribs above the plate along the hanger (18)
                    rib = cq.Workplane("YZ").polyline([(gy, zs + 6), (gy + rs * dy, zs + 6), (gy, zs + 6 + rs)]).close().extrude(130).translate((xs, 0, 0))
                    sh = sh.union(rib)
                for hx in (25, 105):
                    sh = sh.cut(cq.Workplane("XZ").center(xs + hx, hz).circle(3.4).extrude(-8).translate((0, y_in0 - 1, 0)))          # 1/4-20 into the rail slot
                    sh = sh.cut(countersink(f"print_breaker_shelf_{r}", (xs + hx, y_in0 + 6, hz), (0, -1, 0)))                      # countersink on the inner face
                    sh = sh.cut(cq.Workplane("XY").center(xs + hx, yw + 13).circle(2.3).extrude(8).translate((0, 0, wt - 1)))        # M4 down through the foot
            bx, by = xs + 24, y_in0 + 92                           # breaker inboard of the hanger bolts (key path over the empty plate), 7 mm off the lip
            for (u, v) in HOLES["breaker_a"]:                      # its two 6.6 mm holes: M5 inserts (McMaster 94180A361, 6.4 mm pilot) in the shelf,
                sh = sh.cut(cq.Workplane("XY").center(bx + u, by + v).circle(3.2).extrude(8).translate((0, 0, zs - 1)))   # M5 x 12 + washer from above
            assert by + COMPONENTS["breaker_a"].w + 2 <= yw, "breaker flange runs into the lip rib"
            if not P.get("lid_slot"):
                assert zs + 6 + 18 < hz - 7, "hanger rib under the 1/4-20 countersink"
            add(a, sh, f"print_breaker_shelf_{r}", ORANGE)
            add(a, box(130, b.w + 2 * clr, pad - drop, (xs, ty + wall, fl + body_h)), f"pad_breaker_shelf_{r}", (0.15, 0.15, 0.15))   # foam pad on the body top, glued to the plate
            c = COMPONENTS["breaker_a"]
            at = (bx, by, zs + 6)
            add(a, victron_shape("breaker_a", c.d, c.w, c.h, at, unit_fallback("breaker_a", c.d, c.w, c.h, at)), f"power_breaker_shelf_{r}", GOLD)
            g[f"shelf_leg_{r}"] = (xs, yw)
    # --- bus shelf in the column between the trays and the inverter plate -----------------------------------------
    y0s, y1s = ty + fw, V13["plate_y"]                            # 190.4 .. 305: 114.6 wide
    xs0, xs1 = x_in0, out_D - B                                       # rail face to rail face (2026-10-25; was 46 .. out_D - 32, short of both)
    n_pl = 3; seg = (xs1 - xs0) / n_pl
    E = P.get("shelf_end_len", seg)                                    # v12s: the two END plates stay 194.7 as already printed for the
    bounds = [(xs0, xs0 + E), (xs0 + E, xs1 - E), (xs1 - E, xs1)]      # 635 box; the MIDDLE plate alone takes up the depth change
    assert bounds[1][1] - bounds[1][0] >= 100, "middle bus shelf plate too short for its two sill holes"
    for i in range(n_pl):
        xa, xb = bounds[i]
        sh = box(xb - xa, y1s - y0s, 6, (xa, y0s, 0))
        sh = sh.union(box(xb - xa, 6, 34, (xa, y0s, 0)))                     # lip against the trays' inboard walls (M4 inserts)
        for r in range(2):
            for hx in lip_holes[r]:
                hxa = g[f"tx{r}"] + hx
                if xa + 6 < hxa < xb - 6:
                    sh = sh.cut(cq.Workplane("XZ").center(hxa, 17).circle(2.3).extrude(-8).translate((0, y0s - 1, 0)))
        if i in (0, n_pl - 1):   # end plates: a 30 mm wall on the width rail's inner face, two countersunk 1/4-20 into its inner slot,
            xw0 = xa if i == 0 else xb - 6                                                   # the corner notched around the plate's post
            sh = sh.union(box(6, y1s - 11 - y0s, 30, (xw0, y0s, 0)))
            for yc in (y0s + 30, y1s - 40):
                sh = sh.cut(cq.Workplane("YZ").center(yc, B / 2).circle(3.4).extrude(8).translate((xw0 - 1, 0, 0)))
                sh = sh.cut(countersink(f"print_bus_shelf_{i}", (xw0 + 6 if i == 0 else xw0, yc, B / 2), ((-1, 0, 0) if i == 0 else (1, 0, 0))))
        sh = sh.union(box(xb - xa, V13["col_wall"], 34, (xa, y1s - V13["col_wall"], 0)))   # inboard wall = the inverter plate's sill: 2 x M4 through it into
        if i == n_pl - 1:
            sh = sh.cut(box(P["post_d"] + 4, 14, 40, (out_D - B - P["post_d"] - 2, y1s - 10, -1)))   # corner notched around the plate's front post
        if i == 0:
            sh = sh.cut(box(P["post_d"] + 4, 14, 40, (x_in0 - 2, y1s - 10, -1)))                     # and the back post
        for sx in (xa + 40, xb - 40):                                        # inserts in the plate's bottom band (bolts from the column side)
            sh = sh.cut(cq.Workplane("XZ").center(sx, 28).circle(2.3).extrude(-8).translate((0, y1s - 7, 0)))
            g.setdefault("sill_holes", []).append((sx, 28.0))                  # -> the plate gets a pilot for each (found missing 2026-10-25)
        # --- WALL half-laps (2026-10-23): the floor BUTTS; the lip and the inboard wall each carry a 20 mm half-lap, the tongue
        # being the OUTER half of the wall standing on the bed from the floor to the wall top (it fills a matching notch cut through
        # the next plate's wall and floor edge). Every plate prints flat with no bridge or overhang. The earlier FLOOR half-lap's
        # 3 mm pocket ceiling bridged 105 mm (open at the plate edge) and strung, and the U-channel plates cannot print upside down.
        # Tongues point forward (+X) from plates 0 and 1 into the back ends of plates 1 and 2. 0.3 mm thickness clearance, butts touch.
        cw = V13["col_wall"]
        for (yt, tw, out) in ((y0s, 3.0, -1), (y1s - cw / 2, cw / 2, +1)):   # (tongue y0, tongue thickness, which side is outside)
            if i < n_pl - 1:
                sh = sh.union(box(20, tw, 34, (xb, yt, 0)))
            if i > 0:
                sh = sh.cut(box(21, tw + 1.3, 36, (xa - 1, yt - (1.0 if out < 0 else 0.3), -1)))   # notch: wall half + 0.3, 1 mm past the face
            for sx in (([xb + 10] if i < n_pl - 1 else []) + ([xa + 10] if i > 0 else [])) if P.get("lap_bolts", True) else []:
                sh = sh.cut(cq.Workplane("XZ").center(sx, 26).circle(2.3).extrude(-8).translate((0, yt - (1 if out < 0 else 7 - tw), 0)))   # (not v12s)
        for xj in (bounds[1][0], bounds[2][0]):   # the trays' lip bolts must stay clear of the laps (hole in only one of the two wall halves)
            for r in range(2):
                for hx in lip_holes[r]:
                    assert not (xj - 6 < g[f"tx{r}"] + hx < xj + 26), f"shelf lip hole at x {g[f'tx{r}'] + hx:.1f} lands in the lap at {xj:.1f}"
        for pl in (V13_SHORT["col"] if short else V13_COL):   # pre-printed Ø6.4 mm M5 heat-set insert holes in the 6 mm shelf floor
            hkey = {"busbar_px": "busbar_p", "busbar_nx": "busbar_n"}.get(pl["comp"], pl["comp"])   # (shunt_x has its own, off-centre pattern)
            for (hu, hv) in HOLES.get(hkey, ()):
                hx_s, hy_s = pl["x"] + hu, y0s + 6 + pl["y"] + hv
                if xa + 6 < hx_s < xb - 6:
                    sh = sh.cut(cq.Workplane("XY").center(hx_s, hy_s).circle(3.2).extrude(8).translate((0, 0, -1)))
        add(a, sh, f"print_bus_shelf_{i}", ORANGE)
    for pl in (V13_SHORT["col"] if short else V13_COL):
        c = COMPONENTS[pl["comp"]]
        at = (pl["x"], y0s + 6 + pl["y"], 6)
        col = BLUE if c.name.startswith("victron") else GOLD
        add(a, victron_shape(pl["comp"], c.d, c.w, c.h, at, unit_fallback(pl["comp"], c.d, c.w, c.h, at)), c.name + f"_shelf_{int(pl['x'])}", col)
    # --- Garmin PowerSwitch on a printed HANGER PLATE from the top inboard rail (2026-10-30, user's idea) ------------
    # The lane between the MultiPlus (101 thick) and the inboard side panel is 76 mm wide, full depth and height, and the
    # top inboard rail's inner slot is claimed by nothing else.  A 6 mm plate hangs from that slot on two countersunk
    # 1/4-20 (drop-in nuts), its top 3 mm under the lid, and the Garmin's bracket screws to its face (M4 inserts): 6 + 32 mm
    # into the lane, 38 left for the AC cords and SB50 pigtails.  Placed behind the front-panel port bodies (which reach
    # 55 mm in from the panel), 130 mm from the sockets it feeds; its feed comes through the plate's cable window.
    if P.get("garmin_hanger", False):
        gw, gt, gz0 = 130.0, 6.0, 130.0                              # plate width (x), thickness, bottom edge
        gx0 = out_D - 25.0 - 55.0 - 20.0 - gw                        # 20 mm behind the port bodies
        gy = out_W - B - gt                                          # against the inboard rail's inner face
        hz = out_H - B / 2                                           # the top rail's inner slot centreline
        gc = COMPONENTS["garmin"]                                    # 125 wide x 32 deep x 75 tall, bracket on the back
        # cable-tie slots (4 x 10, in pairs 16 apart) wherever the plate is bare: a row above the Garmin and rows below it
        def tie_slots(plate, zrow, xs_):
            for sx in xs_:
                for dx in (-8.0, 8.0):
                    plate = plate.cut(box(4.0, gt + 2, 10.0, (sx + dx - 2.0, gy - 1, zrow - 5.0)))
            return plate
        if P.get("lid_slot"):   # v13: single-piece 254 mm standing panel bolted to the BOTTOM inboard rail (top rail slot stays free for the lid)
            lz0, lz1 = 2.0, 256.0
            hp_ = box(gw, gt, lz1 - lz0, (gx0, gy, lz0))
            for x_rib in (gx0, gx0 + gw - 6.0):                      # two 14 mm deep triangular bookend gusset ribs on the bottom rail (z 2..136)
                rib = (cq.Workplane("YZ").polyline([(gy, lz0), (gy - 14.0, lz0), (gy - 14.0, B), (gy, 136.0)])
                       .close().extrude(6.0).translate((x_rib, 0, 0)))
                hp_ = hp_.union(rib)
            for hx in (gx0 + 25.0, gx0 + gw - 25.0):
                hp_ = hp_.cut(cq.Workplane("XZ").center(hx, B / 2).circle(3.4).extrude(-(gt + 2)).translate((0, gy - 1, 0)))
                hp_ = hp_.cut(countersink("print_garmin_hanger", (hx, gy, B / 2), (0, 1, 0)))
            gx, gz = gx0 + (gw - gc.w) / 2, 142.0
            for (u, v) in HOLES["garmin"]:
                hp_ = hp_.cut(cq.Workplane("XZ").center(gx + u, gz + v).circle(2.8).extrude(-(gt + 2)).translate((0, gy - 1, 0)))
            for zrow in (40.0, 72.0, 104.0, 130.0, 236.0):
                hp_ = tie_slots(hp_, zrow, (gx0 + 30.0, gx0 + gw / 2, gx0 + gw - 30.0))
            add(a, hp_, "print_garmin_hanger", ORANGE)
        else:
            hp_ = box(gw, gt, out_H - 3.0 - gz0, (gx0, gy, gz0))
            for hx in (gx0 + 25.0, gx0 + gw - 25.0):
                hp_ = hp_.cut(cq.Workplane("XZ").center(hx, hz).circle(3.4).extrude(-(gt + 2)).translate((0, gy - 1, 0)))     # 1/4-20 into the slot
                hp_ = hp_.cut(countersink("print_garmin_hanger", (hx, gy, hz), (0, 1, 0)))                                     # head on the inner face
            gx, gz = gx0 + (gw - gc.w) / 2, 150.0
            for (u, v) in HOLES["garmin"]:                           # M4 inserts in the plate (short, 94180A351), Ø5.6 mm pre-printed bores
                hp_ = hp_.cut(cq.Workplane("XZ").center(gx + u, gz + v).circle(2.8).extrude(-(gt + 2)).translate((0, gy - 1, 0)))
            hp_ = tie_slots(hp_, 243.0, (gx0 + 30.0, gx0 + gw / 2, gx0 + gw - 30.0))
            hp_ = tie_slots(hp_, 138.0, (gx0 + 30.0, gx0 + gw / 2, gx0 + gw - 30.0))
            add(a, hp_, "print_garmin_hanger", ORANGE)
            # the LOWER plate (2026-10-31, user: run it to the bottom rail so wires can be tied to it): the full drop is 277, over the
            # bed, so a second plate stands on the bottom inboard rail's inner slot (free in the ledger) with its own two countersunk
            # 1/4-20, a 1 mm gap under the upper plate, and cable-tie slots on a 40 mm grid
            lz0, lz1 = 2.0, gz0 - 1.0
            lp_ = box(gw, gt, lz1 - lz0, (gx0, gy, lz0))
            for hx in (gx0 + 25.0, gx0 + gw - 25.0):
                lp_ = lp_.cut(cq.Workplane("XZ").center(hx, B / 2).circle(3.4).extrude(-(gt + 2)).translate((0, gy - 1, 0)))
                lp_ = lp_.cut(countersink("print_garmin_hanger_lower", (hx, gy, B / 2), (0, 1, 0)))
            for zrow in (40.0, 70.0, 100.0):
                lp_ = tie_slots(lp_, zrow, (gx0 + 30.0, gx0 + gw / 2, gx0 + gw - 30.0))
            add(a, lp_, "print_garmin_hanger_lower", ORANGE)
            # Garmin port-circuit GROUND BUS (2026-10-31, user's idea): the owner's Blue Sea 2701 DualBus (two 5 x #8-32 buses, bridged)
            # on the lower plate's inner face between the tie-slot rows, so every front-port negative lands beside the Garmin that
            # feeds it. Stand-in body only: its two #10 mounting holes are drilled through the plate from the part (as the Garmin's were).
            gb = COMPONENTS["gnd_bus"]
            gb_at = (gx0 + (gw - gb.w) / 2, gy - gb.d, 46.0)         # z 46..93: clear of the tie-slot rows at 40 and 100
            add(a, box(gb.w, gb.d, gb.h, gb_at).edges("|Y").fillet(3), "power_busbar_gnd_hanger", GOLD)
        at = (gx, gy - gc.d, gz)
        add(a, victron_shape("garmin", gc.w, gc.d, gc.h, at, unit_fallback("garmin", gc.w, gc.d, gc.h, at)), "garmin_powerswitch_hanger", BLACK)
        g["garmin_hanger_nuts"] = (gx0 + 25.0, gx0 + gw - 25.0)
    # --- inverter plate along the depth, in posts against the two width rails ---------------------------------------
    lid_slot = bool(P.get("lid_slot"))
    ikey = P.get("inverter_long", "multiplus_ii_long"); inv = COMPONENTS[ikey]
    iz = 2.0 if ikey == "multiplus_ii_long" else (15.0 if lid_slot else 22.0)   # v13 (lid_slot): z 15..264 (2.2 mm below the z 266.2 lid underside)
    yp = V13["plate_y"]; hpost = min(out_H - B, 254.0)            # posts print in one piece (254)
    px0, px1 = x_in0 + P["post_d"] - P["slot_depth"], out_D - B - P["post_d"] + P["slot_depth"]   # plate ends inside the post slots
    zp = 14.0 if lid_slot else 21.0
    hp = 250.0 if lid_slot else min(256.0, out_H - 2 - zp)        # v13 (lid_slot): z 14..264 (2.2 mm below the slot-captured lid)
    yt = yp + P["card_t"] / 2 + P["post_w"] / 2                   # the v12 post turned 90 deg: its slot (centred on the post) takes the plate
    for j, (xpost, xclip) in enumerate(((x_in0, x_in0), (out_D - B - P["post_d"], out_D - B - 20))):
        add(a, v12_post(hpost, mirror=(j == 1), buttress=lid_slot).rotate((0, 0, 0), (0, 0, 1), -90).translate((xpost, yt, 0)), f"print_post_inverter_{j}", ORANGE)
        if not lid_slot:
            clip = v12_post_clip(mirror=(j == 1), h=out_H - hpost, bolt_z=out_H - hpost - B / 2).rotate((0, 0, 0), (0, 0, 1), -90)
            add(a, clip.translate((xclip, yt, hpost)), f"print_post_clip_{j}", ORANGE)
    ux = V13["inv_x"]
    r_inv = 3.2 if INSERT.get(ikey) == "M5" else 2.8
    patches = [(ux - px0 + u, iz - zp + v, r_inv) for (u, v) in HOLES[ikey]]
    patches += [(sx - px0, sz - zp, 2.8) for (sx, sz) in g.get("sill_holes", ())]   # the 6 short M4 (Ø5.6 mm) in the bottom band, for the bus shelf wall's bolts
    raw_units = V13_SHORT["units"] if short else V13_PLATE_UNITS
    if lid_slot and short:                                                     # lower column units 7 mm so tops sit at z 259 (7.2 mm under lid) and clear the z 127..151 lap
        raw_units = tuple((c_, x_, z_ - 7.0, n_, *s_) for (c_, x_, z_, n_, *s_) in raw_units)
    if P.get("plate_pilots"):   # pre-printed Ø5.6 mm (M4) and Ø6.4 mm (M5) heat-set insert bores under every unit on the column face
        for comp, x0, z0, nm, *_side in raw_units:                             # bores go through: inserts set from the unit's side
            if P.get("breaker_shelf") and comp == "breaker_face":
                continue
            assert comp in HOLES, f"no HOLES pattern for {comp}: the plate would get no pilots under it"
            r_u = 3.2 if INSERT.get(comp) == "M5" else 2.8
            patches += [(x0 - px0 + u, z0 - zp + v, r_u) for (u, v) in HOLES[comp]]
            lap_lo, lap_hi = zp + hp / 2 - LAT["lap"] / 2, zp + hp / 2 + LAT["lap"] / 2         # the two tile rows' half-lap band
            for (u, v) in HOLES[comp]:
                assert not (lap_lo - 3 < z0 + v < lap_hi + 3), f"{comp} insert at z {z0 + v:.0f} lands in the tiles' lap ({lap_lo:.0f}-{lap_hi:.0f})"
    V13["window"] = V13_SHORT["window"] if short else (645.0, 712.0, 40.0, 118.0)    # x0, x1, z0, z1: low cable window in the plate's front tile, over the shelf's empty inboard band
    wx0, wx1, wz0, wz1 = V13["window"]
    window = cq.Workplane("XZ").center((wx0 + wx1) / 2, (wz0 + wz1) / 2).rect(wx1 - wx0, wz1 - wz0).extrude(-(P["card_t"] + 2)).edges("|Y").fillet(8).translate((0, yp - 1, 0))
    PLATE_PILOTS.update(x0=px0, y=yp, z0=zp, patches=list(patches))   # for check_plate_pilots (--clash)
    for nm, shp in lattice_card_tiles(px1 - px0, hp, px0, yp, zp, "plate_inverter", patches):
        if "tile" in nm:
            shp = shp.cut(window)
        shp = shp.cut(box(12, P["card_t"] + 2, 30 - zp + 1, (px0 - 1, yp - 1, zp - 1)))              # bottom corners clear the posts' solid sills
        shp = shp.cut(box(12, P["card_t"] + 2, 30 - zp + 1, (px1 - 11, yp - 1, zp - 1)))
        if not lid_slot:
            shp = shp.cut(box(14, P["card_t"] + 2, 40, (px0 - 1, yp - 1, hpost - 0.6)))              # top corners clear the post clips
            shp = shp.cut(box(14, P["card_t"] + 2, 40, (px1 - 13, yp - 1, hpost - 0.6)))
        add(a, shp, nm, ORANGE if "spline" in nm else DARK)
    at = (ux, yp + P["card_t"] + V13["standoff"], iz)
    add(a, victron_shape(ikey, inv.d, inv.w, inv.h, at, box(inv.d, inv.w, inv.h, at).edges("|Y").fillet(3), lugs=("y", -1)), "victron_multiplus_long", BLUE)
    g["inv_front"] = ux + inv.d
    # --- charge gear on the plate's column face (lugs to the plate, inserts in the plate) ---------------------------
    plate_units = [u for u in raw_units if not (P.get("breaker_shelf") and u[0] == "breaker_face")]
    for comp, x0, z0, nm, *side in plate_units:
        side = side[0] if side else -1                                   # -1: column face (default); +1: inverter face, in front of the MultiPlus
        c = COMPONENTS[comp]
        at = (x0, yp - c.d - 3 if side < 0 else yp + P["card_t"] + 3, z0)
        col = BLUE if c.name.startswith("victron") else (0.08, 0.08, 0.08) if c.name.startswith("garmin") else GOLD
        fb = unit_fallback(comp, c.w, c.d, c.h, at, axis="|Y", face=True)
        add(a, victron_shape(comp, c.w, c.d, c.h, at, fb, lugs=("y", -side)), f"{c.name}_{nm}_plate", col)
    # --- panels, ports, lid ------------------------------------------------------------------------------------------
    xf = v12_panels(a)
    g["xf"] = xf
    if P["stack_on_icebox"]:   # the four 4 mm straps that tie the box's bottom depth rails to the IceBox's top depth rails
        add_stack_straps(a)
    BS["_g12"] = g
    return g


def dims_v13():
    g = BS.get("_g12") or {}
    top = out_H + 40; D = []
    def dim(p1, p2, label, off): D.append(dict(a=p1, b=p2, label=label, off=off))
    dim([0, 0, top], [out_D, 0, top], f"depth {out_D:.0f} mm ({out_D / 25.4:.1f} in) = the IceBox", [0, -60, 0])
    dim([0, 0, top], [0, out_W, top], f"width {out_W:.0f} mm ({out_W / 25.4:.1f} in) = the IceBox", [-60, 0, 0])
    dim([out_D + 60, 0, 0], [out_D + 60, 0, out_H], f"height {out_H:.0f} mm ({out_H / 25.4:.1f} in), {P['icebox_H'] - out_H:.0f} under the IceBox", [40, 0, 0])
    dim([x_in0, -30, 40], [x_in0 + g.get("bay_D", 702), -30, 40], f"{'two Smart 200Ah end to end' if P.get('batt') == 'smart200' else 'two SuperPack 60Ah, one at each end'} {g.get('bay_D', 702):.0f}", [0, -40, 0])
    dim([V13["inv_x"], out_W + 30, 40], [g.get("inv_front", 638), out_W + 30, 40], f"{'MultiPlus-II' if P.get('inverter_long') == 'multiplus_ii_long' else 'MultiPlus 12/1200'} on its long side {g.get('inv_front', 638) - V13['inv_x']:.0f}", [0, 40, 0])
    dim([g.get("inv_front", 638), out_W + 30, 40], [x_in0 + in_D, out_W + 30, 40], f"front zone {x_in0 + in_D - g.get('inv_front', 638):.0f}: cable end + ports", [0, 80, 0])
    return D


def report_v13():
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.2f} in)"
    g = BS.get("_g12") or {}
    if P.get("batt") == "battery":
        ii = P.get("inverter_long") == "multiplus_ii_long"
        if P.get("lid_slot"):
            print(f"== Variant '{VARIANT}': slot-captured lid in the 4 top rails' inner-face slots (z = 266.2..272.2 mm), zero top-rail fasteners ==")
            print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}; lid recessed 9.5 mm below the top rail faces, just like the donor IceBox 1.3")
            print("  breaker decks : U-bridge drop shelves (z = 36..239 mm) standing on the 6 mm outboard tray wall + bolted to the 21 mm inboard tray wall (2 x M4); uses unmodified v12s trays; top outboard rail slot 100% free")
            print("  inverter card : plate lowered 7 mm to z = 14..264 mm (MultiPlus at z = 15..264 mm, MPPT/Cerbo tops at z = 259 mm), held by buttressed single-piece bottom-rail posts (2 x 1/4-20 sill bolts + 110 mm gusset each, no top clips)")
            print("  garmin panel  : single-piece 254 mm standing panel (z = 2..256 mm) with 14 mm bookend gusset ribs bolted to the bottom inboard rail (2 x 1/4-20); top inboard rail slot 100% free")
            return
        print(f"== Variant '{VARIANT}': v13's interior with two SuperPack 60Ah and the {'MultiPlus-II 12/3000 (ordered 2026-10-14)' if ii else 'MultiPlus 12/1200'}: upgrade to v13 = swap the trays and batteries ==")
        print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}; bank 2 x 60 Ah = 120 Ah, 60 A continuous (160 A for 10 s) -> about 700 W of AC continuous whatever the inverter")
        if out_D < 700:
            print(f"  short box      : depth rails {out_D - 2 * C:.1f} = the 25 in IceBox's, uncut; height rails cut to {out_H - 2 * C:.1f}; the plate's charge gear in one row, the Garmin on the inverter face by the ports; no room for a MultiPlus-II or a 200Ah pair")
        if ii:
            print("  with the II    : set its charger to 60 A (2 x 30 A SuperPack charge limit) in VEConfigure; its 13 W idle is 1 Ah/h from a 120 Ah bank; build the DC side")
            print("                   for v13 now (2/0 leads, 400 A class T, 250 A-class bars) so the battery upgrade touches nothing but the trays; the SuperPacks' own BMSs protect them")
        print("  upgrade        : the shelf, plate, posts, clips, panels, lid, window, port strip and inverter are v13's; print v13's two split trays, fit two Smart 200Ah + VE.Bus BMS")
        return
    print("== Variant 'v13': v12 one inch taller, MultiPlus-II 12/3000 + two Lithium Smart 200Ah ==")
    print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}  -> IceBox footprint, {P['icebox_H'] - out_H:.0f} mm ({(P['icebox_H'] - out_H) / 25.4:.1f} in) lower; height rails cut to {out_H - 2 * C:.0f}")
    print(f"layout          : outboard side: two Smart 200Ah end to end ({g.get('bay_D', 0):.0f} of the {in_D:.0f}) | column {V13['plate_y'] - (y_in0 + 1 + 167):.0f} wide: breakers and bus bars in two rows | "
          f"inboard side: the MultiPlus-II on its long side (578 along the depth, 148 into the box, 277 tall) on a {min(256.0, out_H - 23):.0f} mm plate | front {x_in0 + in_D - g.get('inv_front', 0):.0f}: its cable end, the Garmin flat, the ports on the inboard half of the front panel")
    print(f"height budget   : MultiPlus-II 277 on 2 mm shims = 279, lid at {out_H:.0f} ({out_H - 279:.0f} spare); batteries 237 + 6 floor + lugs 30 = 273 ({out_H - 273:.0f} spare); plate 21..277; posts {out_H - B:.0f} + clips")
    print("  electrical     : bank 2 x 200 Ah = 400 Ah (5.1 kWh), 400 A continuous (200 A each, Victron 'recommended'); the II draws ~220 A at 2400 W, 130 A at a 1500 W load;")
    print("                   its 120 A charger is within the bank's 200 A. NEEDS: VE.Bus BMS V2 (Smart batteries have no internal BMS; not yet placed), 2/0 AWG DC leads,")
    print("                   a 400 A class T fuse and 250 A-class bus bars in place of the 150 A 7148 breakers and 5-stud bars drawn here.")
    print("  caveats        : the MultiPlus-II manual hangs it on a wall by its hook and two holes (vertical, cables down); here it is turned 90 deg with the cable end")
    print("                   forward and hangs on the same hook and holes on a vertical plate -> confirm with Victron before building. Hook/hole positions are estimates.")
    print(f"  weight         : ~{2 * 20 + 19 + 1.3 + 0.33 + 0.5 + 0.3 + 2.5 + 19 + 5:.0f} kg (batteries 40, inverter 19, frame 19, prints ~5)")
    print("== Cables and connectors (Victron manuals) ==")
    for run, size, fuse, conn in CABLE_SPEC:
        print(f"  {run:48s} {size:52s} fuse {fuse:28s} {conn}")



def dims_v12():
    g = BS.get("_g12") or {}
    top = out_H + 40; D = []
    def dim(p1, p2, label, off): D.append(dict(a=p1, b=p2, label=label, off=off))
    dim([0, 0, top], [out_D, 0, top], f"depth {out_D:.0f} mm ({out_D / 25.4:.1f} in) = the IceBox", [0, -60, 0])
    dim([0, 0, top], [0, out_W, top], f"width {out_W:.0f} mm ({out_W / 25.4:.1f} in) = the IceBox", [-60, 0, 0])
    dim([out_D + 60, 0, 0], [out_D + 60, 0, out_H], f"height {out_H:.0f} mm ({out_H / 25.4:.1f} in), {P['icebox_H'] - out_H:.0f} under the IceBox", [40, 0, 0])
    bd = g.get("bay_D", 544)
    dim([x_in0, -30, 40], [x_in0 + bd, -30, 40], f"battery bay {bd:.0f}", [0, -40, 0])
    dim([x_in0 + bd, -30, 40], [x_in0 + in_D, -30, 40], f"inverter + front panel {in_D - bd:.0f}", [0, -80, 0])
    return D


def report_v12():
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.2f} in)"
    g = BS.get("_g12") or {}
    print("== Variant 'v12': half-height IceBox footprint, NOT card based: everything serviced from the top ==")
    print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}  -> same width and depth as the IceBox, {P['icebox_H'] - out_H:.0f} mm ({(P['icebox_H'] - out_H) / 25.4:.1f} in) lower")
    print(f"frame           : one IceBox 1.3 frame: width and depth rails uncut, the four height rails cut to {out_H - 2 * C:.0f} (offcuts {P['icebox_H'] - out_H:.0f} each)")
    bd = g.get("bay_D", 544)
    print(f"layout          : bay {bd:.0f} deep (2 x 2 SuperPacks in one layer, trays tabbed to the outboard and back rails, bolted to each other) | "
          f"column {in_W - 2 * 150 - 2:.0f} wide beside them with the bus shelf | front {in_D - bd:.0f}: fixed plate + MultiPlus on its long side ({g.get('inv_front', 0) - x_in0 - bd:.0f} used) + Orion and ports on the front panel")
    print(f"height budget   : the top rails only run along the edges, so the middle of the box is clear to the lid at {out_H:.0f}: MultiPlus on its long side 249 + 2 = 251 "
          f"({out_H - 251:.0f} under the lid) on a 250 plate, batteries 217 + lugs 19 = 236 ({out_H - 236:.0f} under the lid); under the rails (posts, panel mounts, ports) the limit is {out_H - B:.0f}: "
          f"MPPT upright 186 from z 38, posts 254 + {out_H - 254:.0f} clips")
    print(f"inboard wall    : Cerbo (174 mount) + Orion (143) + MPPT (150) on the panel between the back corner and the inverter posts, "
          f"{548.8 - (x_in0 + 15):.0f} available; the Garmin on the front panel's outboard side, the ports on its inboard 150 mm (v13's panel)")
    print(f"upgrade to v13  : same frame ({out_H:.0f} tall), panels, lid, posts, clips and port strip; reprint the trays, bus shelf and inverter plate, swap the MultiPlus and batteries")
    print("  no deck, no legs, no shelves, no cards: lid off and every unit is in reach.  Panel units (Orion, MPPT, Garmin) hang on printed mounts screwed")
    print("  through the panel from outside into inserts, fed by SB50 pigtails so a panel unbolts with its units; the MultiPlus is lugged straight to the bus bars.")
    print("  rail slots: the IceBox's panels are captured in the rails' centreline slots, so the rails' top and bottom slots are taken; every tie")
    print("  is a HORIZONTAL 1/4-20 into a rail's INNER slot: countersunk through the outboard trays' outer walls and the bus shelf's outer wall")
    print("  (heads flush inside), through the posts' sills, and through printed top clips on the posts into the top rails.  Panels sit inside the bar envelope.")
    print("  caveats: the MultiPlus is on its long side (Victron: vertical preferred, horizontal allowed with the terminals down -> here the terminals face the column); verify the STEP's terminal end in the render.")
    print("== Cables and connectors (Victron manuals) ==")
    for run, size, fuse, conn in CABLE_SPEC:
        print(f"  {run:48s} {size:52s} fuse {fuse:28s} {conn}")


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
    ice = P["icebox_W"] - out_W
    dim([-40, out_W - P["icebox_W"], top], [-40, 0, top], f"pedal room: {ice:.0f} mm ({ice / 25.4:.1f} in) inside the IceBox face", [0, 0, 50])
    y = -30; z = 40
    xi = x_in0 + V8["x_inv"]
    dim([x_in0, y, z], [x_in0 + V7["bay_D"], y, z], f"battery bay + bus deck {V7['bay_D']:.0f}", [0, -40, 0])
    dim([x_in0 + V7["bay_D"], y, z], [xi, y, z], f"wiring gap {V8['bay_gap']:.0f}", [0, -80, 0])
    if P["deck"] == "column":
        dim([xi, y, z], [x_in0 + in_D, y, z], (f"charge card {x_in0 + in_D - xi:.0f}" if P["swap"] else f"inverter card + MultiPlus {x_in0 + in_D - xi:.0f}"), [0, -40, 0])
        ox = out_D + PACK["gap_to_box"]; pD, pW, pH = PACK["D"], PACK["W"], PACK["H"]
        dim([ox, 0, pH + 40], [ox + pD, 0, pH + 40], f"pack depth {pD:.0f} mm ({pD / 25.4:.1f} in)", [0, -60, 0])
        dim([ox + pD + 60, 0, 0], [ox + pD + 60, 0, pH], f"pack height {pH:.0f} mm ({pH / 25.4:.1f} in)", [40, 0, 0])
        dim([out_D, -30, 40], [ox, -30, 40], f"SB175 jumper gap {PACK['gap_to_box']:.0f}", [0, -40, 0])
        return D
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
    ("Bus deck -> MultiPlus 12/1200", "4 AWG / 21 mm2 as built (Victron lists 35 mm2; 2 AWG did not fit the terminals), keep the run under 1 m", "150 A (Victron) at the deck", "lugged at the deck bus bars; Anderson SB175 (4 AWG contacts; takes 2 AWG if you ever upsize) on the inverter card's rear face"),
    ("Bus deck -> Orion XS 12/12-50 output", "6 AWG / 16 mm2 (Victron: 50 A, < 5 m)", "60-70 A", "lugged at the deck; Anderson SB50 (6 AWG contacts) on the charge card; runs in the outboard chase"),
    ("Alternator -> Orion XS input", "6 AWG, 60-70 A fuse at the start battery", "60-70 A", "Anderson SB50 at the front panel"),
    ("Bus deck -> MPPT 100/30 battery side", "10 AWG / 6 mm2 (Victron: 30 A)", "40 A", "lugged at the deck; Anderson SB50 (10 AWG contacts) on the charge card; runs in the outboard chase"),
    ("Solar array -> MPPT PV side", "10 AWG; PV fuse per Victron if > 1 string", "per string", "Anderson SB50 at the front panel"),
    ("Bus deck -> Garmin PowerSwitch feed", "10 AWG (Garmin: 50 A max on the PowerSwitch)", "60 A", "the Garmin sits on the deck beside the + bus bar: a 150 mm lead"),
    ("Bus deck -> Cerbo GX", "16 AWG", "3 A", "lugged at the deck; Anderson SB50 on the charge card; runs in the outboard chase"),
    ("Garmin PowerSwitch outputs -> front-panel sockets", "10 AWG, one circuit per socket (Garmin: 30 A per channel max)", "Garmin's own per-channel protection", "Anderson Powerpole PP45 block (8 poles / 4 circuits) at the deck's front edge, mating forward; the socket harness runs in the outboard chase to the front panel"),
    ("Shore AC in / inverter AC out", "12 AWG, per the MultiPlus AC in/out ratings", "AC breaker in the MultiPlus", "L14-30 inlet / outlet at the front panel"),
]


def report_v9():
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.2f} in)"
    g = BS.get("_g8") or {}; inv = COMPONENTS[P["inverter"]]
    if P["deck"] == "column":
        return report_v10()
    print("== Variant 'v9': v8 + a fixed bus deck on the battery rack; two cards, each unplugs and lifts out alone ==")
    print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}  -> {487.4 - out_W:.0f} mm ({(487.4 - out_W) / 25.4:.1f} in) narrower, "
          f"{762 - out_D:.0f} mm ({(762 - out_D) / 25.4:.1f} in) shorter in depth than the IceBox, same height")
    print(f"depth chain     : bay + deck {V7['bay_D']:.0f} | gap {V8['bay_gap']:.0f} | inverter card {P['card_t']:.0f}+10+{inv.d:.0f}+{V8['inv_gap']:.0f} "
          f"| charge card {P['card_t']:.0f}+{V8['charge_depth']:.0f}+{V8['charge_gap']:.0f} | front {V8['front']:.0f}")
    dz = g.get("deck_z", 468); dL = g.get("deck_L", 245)
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
        if pl["x"] + c.d > dL: bad.append("X overflow")
        if pl["y"] + c.w > V7["bay_W"]: bad.append("Y overflow")
        if dz + 6 + c.h > out_H: bad.append("hits the lid")
        print(f"  deck     {c.name:20s} {c.d:>4.0f}x{c.w:>4.0f}x{c.h:>3.0f} @({pl['x']},{pl['y']}) {' '.join(bad) or 'ok'}")
    o175, o50 = 2 * HOUSING["sb175"] - MATED["sb175"], 2 * HOUSING["sb50"] - MATED["sb50"]
    ch_ = in_H - 8 - CARD_TRIM
    z175, z50 = _conn_z("sb175_v"), _conn_z("sb50_v")
    print(f"connectors      : cards cut down {CARD_TRIM:.0f} mm to {ch_:.0f} tall; every card has its own fixed Anderson halves at the top of its rear face, mating face UP. "
          f"The mated pigtail halves top out {CONN_LID_ROOM:.0f} mm under the lid (their cables exit upward into that room). "
          f"Inverter card: SB175 housing at card z {z175:.0f}-{z175 + HOUSING['sb175']:.0f} ({ch_ - z175 - HOUSING['sb175']:.0f} below the card top). "
          f"Charge card: 5 x SB50 at z {z50:.0f}-{z50 + HOUSING['sb50']:.0f} ({ch_ - z50 - HOUSING['sb50']:.0f} below the card top): MPPT, Orion, Cerbo, solar in, alternator in. Inverter card also carries the Garmin feed SB50 and the PP45 output block. "
          f"Pull-up travel {o175:.0f} / {o50:.0f} mm.")
    chase = P["post_standoff"]
    print(f"                  deck end: no fixed halves; every pigtail is lugged at the bus bars/breakers.  Deck front edge to the inverter card's rear face "
          f"{x_in0 + V8['x_inv'] - (g.get('deck_x0', 0) + dL):.0f} mm = the SB175 housing (26) + 4.  The 4 AWG inverter pigtail exits its flying half upward "
          f"at {out_H - CONN_LID_ROOM:.0f} and bends back over the deck inside the {CONN_LID_ROOM:.0f} mm lid room (4 AWG bend radius ~45 mm; 2 AWG ~55 would be tight).  "
          f"Charge-card pigtails (5) run forward in the {chase:.0f} mm chase between the outboard rail and the guide posts, so the inverter card lifts without touching them.")
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
    print("  lid off -> lift that card's flying halves off its receptacles -> lift the card. Batteries: unplug all, unbolt the deck, lift it, lift the batteries.")
    print(f"  est. mass ~{4 * 7.5 + 8.2 + 1.3 + 0.33 + 0.5 + 0.3 + 0.3 + 1.5 + 3.0 + 13.0:.0f} kg")


def report_v10():
    mm = lambda v: f"{v:.0f} mm ({v / 25.4:.2f} in)"
    g = BS.get("_g8") or {}; inv = COMPONENTS[P["inverter"]]
    if P["swap"]:
        print("== Variant 'v11': v10 SWAPPED - the MultiPlus stands lengthwise in the column beside the stack, the charge gear is the front card ==")
    else:
        print("== Variant 'v10': TWO batteries in one stack; charge card lengthwise in the freed column; inverter card in front; ports on the side wall ==")
    print(f"outer D x W x H : {mm(out_D)} x {mm(out_W)} x {mm(out_H)}  -> {762 - out_D:.0f} mm ({(762 - out_D) / 25.4:.1f} in) shorter than the IceBox, "
          f"{568 - out_D:.0f} mm shorter than v9")
    if P["swap"]:
        print(f"depth chain     : bay {V7['bay_D']:.0f} | charge card's rear SB50 row {V8['bay_gap']:.0f} | charge card {P['card_t']:.0f}+{V8['charge_depth']:.0f}+4 | front {V8['front']:.0f}")
    else:
        print(f"depth chain     : bay {V7['bay_D']:.0f} | front column post + gap {V8['bay_gap']:.0f} | inverter card {P['card_t']:.0f}+10+{inv.d:.0f} | front {V8['front']:.0f}")
    cx0, cL, cy = g.get("col_card", (0, 250, 0))
    print(f"column card     : {cL:.0f} x {g.get('ch', 444):.0f} in the XZ plane along the inboard wall (plane y {cy:.0f}), units face the stack with "
          f"{cy - (y_in0 + 1 + V7['tray_w']):.0f} mm to the tray wall; SB50 row on the rear face in the {out_W - B - cy - P['card_t']:.0f} mm behind it; "
          f"posts {V10['post_dx']:.0f} x {P['post_w']:.0f} with feet on the inboard depth rails, three half-lapped segments")
    for pl in (V11_COL_LAYOUT if P["swap"] else V10_COL_LAYOUT):
        c = COMPONENTS[pl["comp"]]; bad = []
        if pl["x"] + c.w > cL: bad.append("X overflow")
        if pl["z"] + c.h > g.get("col_ch", 444): bad.append("Z overflow")
        print(f"  column   {c.name:20s} {c.w:>4.0f}x{c.h:>4.0f}x{c.d:>3.0f} @({pl['x']},{pl['z']}) {' '.join(bad) or 'ok'}")
    if P["swap"]:
        ey = g.get("deck_ext_y", (0, 0))
        print(f"column floor    : continuous 6 mm floor from the tray's inboard wall to the inverter card's posts, full column width, two halves butted at the middle "
              f"(each bolted at both ends: 3 x M4 through the tray wall, 2 x M4 into the post's sill); the tray's inboard corners are tied to the frame through the posts")
        print(f"lug room        : {P['term_clear']:.0f} mm between each battery top and the deck / shelf above it (4 AWG lug + M6 bolt head ~19, cable 9); no deck windows: "
              f"the leads run under the deck to its back edge and come up in the {V7['end_gap']:.0f} mm end gap behind it; terminals go at the back end of each battery")
        holes = g.get("deck_holes", [])
        print("fastener rule   : no loose nuts inside the box - every in-box fastener goes into a heat-set insert, a rail T-nut or self-taps; nuts only on bench sub-assemblies (MultiPlus bolts, card laps, panel ports)")
        print(f"deck fasteners  : {len([h for h in holes if h[0] == 'leg'])} x M4 into the leg boss tabs, {len([h for h in holes if h[0] == 'ledge'])} x M4 into the column posts' ledges, "
              f"4 x M4 into the two joint cleats, 2 x M4 into inserts in the deck + 1 T-nut at the back deck tie; every hole checked to lie >= 4 mm inside its plate")
        print(f"deck extension  : {ey[1] - ey[0]:.0f} mm wide, post to post in two splined plates over the inverter column, running to the inverter card's face "
              f"(cutouts where the two posts pass through).  HOW IT CONNECTS: each plate screws down (M4) into a ledge that is PART of the column post's top "
              f"segment (14 mm block on the post's -Y face, 26 mm gusset under it, insert from above), and into a cleat under the stack-half joint "
              f"(40 x 30 x 14, an insert each side of the line, the stack half screws into it too).  Four screws per plate, splines only locate; "
              f"the breaker lives on the front plate.  The inverter card lifts only after both plates are off.")
        col_w = out_W - B - (y_in0 + 1 + V7["tray_w"])
        print(f"column          : {col_w:.0f} mm wide; card 6 + MultiPlus 101 flush = 107, {out_W - B - cy - P['card_t']:.0f} mm behind the card for the SB175 (mating up), "
              f"MultiPlus face {cy - 101 - (y_in0 + 1 + V7['tray_w']):.0f} mm from the tray wall; card {cL:.0f} long (2 x 2 tiles) = body 249 + 7 mm slot lips + 0.5 each end, "
              f"bolted through at its keyholes (fender washers behind), top bracket {MP_BRACKET:.0f} mm above the body on the card")
        print(f"inverter SB175  : on the column card's REAR face at the top, mating UP into the 60 mm lid room, exactly like the front card's SB50s; "
              f"the card is back to {g.get('col_ch', 444):.0f} tall.  Unplug it from above after the deck's extension plates are off, then lift the card.")
        for pl in V11_CHARGE_LAYOUT:
            c = COMPONENTS[pl["comp"]]; bad = []
            if pl["y"] + c.w > g.get("cw", 249): bad.append("Y overflow")
            if pl["z"] + c.h > g.get("ch", 444): bad.append("Z overflow")
            print(f"  front    {c.name:20s} {c.w:>4.0f}x{c.h:>4.0f}x{c.d:>3.0f} @({pl['y']},{pl['z']}) {' '.join(bad) or 'ok'}")
    deck_w = (g.get("deck_ext_y", (0, 0))[1] - (y_in0 + 1)) if P["swap"] else V7["tray_w"]
    for pl in (V11_DECK_LAYOUT if P["swap"] else V10_DECK_LAYOUT):
        c = COMPONENTS[pl["comp"]]; bad = []
        if pl["x"] + c.d > 245: bad.append("X overflow")
        if pl["y"] + c.w > deck_w: bad.append("Y overflow")
        print(f"  deck     {c.name:20s} {c.d:>4.0f}x{c.w:>4.0f}x{c.h:>3.0f} @({pl['x']},{pl['y']}) {' '.join(bad) or 'ok'}")
    gap = g.get("cy0", 82)
    if P["swap"]:
        print(f"ports           : all on the FRONT face in one vertical strip, {gap - B:.0f} mm wide between the pedal-side corner bar and the front card "
              f"(card pushed to the inboard rail, posts {P['post_standoff_out']:.0f} / {P['post_standoff_in']:.0f}).  Bottom to top: SB175 pack inlet on end, "
              f"3 x 12 V + 2 x USB two per row, SB50 solar, SB50 alternator, L14-30 in, L14-30 out.  Bodies sit beside the card, {x_in0 + V8['x_inv'] - 9.6 + 24 - (x_in0 + in_D - 79):.0f} mm "
              f"behind the deepest one to the card's post; nothing is in front of the MPPT, and the box works mirrored for the IceBox on the other side.")
    who = "the front (charge) card" if P["swap"] else "the inverter"
    print(f"side-wall option: all on the y=0 side wall beside {who}, backs toward it: {gap:.0f} mm from the wall to the card's edge "
          f"(inverter card on posts {P['post_standoff_out']:.0f} / {P['post_standoff_in']:.0f} off the rails; frame widened {P['extra_width']:.0f} mm for the SB175's 79).  "
          f"2 x L14-30, 2 x SB50 inlets, 3 x 12 V, 2 x USB, SB175 pack inlet, in the 106 mm between the card's post and the front corner bar.")
    print(f"pedal room      : the box is flush with the IceBox on its +Y face; on the other side it sits {P['icebox_W'] - out_W:.0f} mm ({(P['icebox_W'] - out_W) / 25.4:.1f} in) inside the IceBox face")
    pD, pW, pH, off = PACK["D"], PACK["W"], PACK["H"], PACK["offcut"]
    print(f"== Add-on pack (rendered {PACK['gap_to_box']:.0f} mm in front of the box) ==")
    print(f"  {pD:.0f} x {pW:.0f} x {pH:.0f} mm ({pD / 25.4:.1f} x {pW / 25.4:.1f} x {pH / 25.4:.1f} in); 2 x SuperPack side by side in the v9 trays, "
          f"paralleled battery-to-battery; ONE Blue Sea 187 150 A on the deck in the + lead to the SB175, - straight to the SB175; "
          f"SB175 inlet on the back panel at z 240; 4 AWG jumpers to the SB175 beside the socket row on the main box's front panel")
    if P["pack"] == "printed":
        print(f"  ALL PRINTED (no bars): 4 corner posts 30 x 30 x {pH - PACK['skin']:.0f} in two half-lapped segments (foot tab M4 into the tray pad, M4 insert for the lid), "
              f"deck corners on post ledges + 4 inner legs, 4 panels of 2 x 2 six-mm tiles screwed outside the posts, lid in 4 tiles + handle.  "
              f"ASA: posts ~1.0 kg, panels ~2.3 kg, lid ~0.5 kg, trays/legs/deck ~1.3 kg -> ~5 kg, ~60 h; skip the side panels for an open cage: ~2.5 kg")
    else:
        print(f"  bars: 4 height rails = the IceBox depth-rail offcuts, {off:.0f} mm each, UNCUT ({P['frame_D']:.0f} - {out_D:.0f}); "
              f"4 width rails {pW - 2 * C:.0f} and 4 depth rails {pD - 2 * C:.0f} cut from 8 kit bars (437) = 4 modification kits; the main box uses none")
    print("== Battery / inverter tradeoff ==")
    print("  2 x SuperPack 60Ah = 120 Ah, 60 A continuous / 80 A for 10 s.  The MultiPlus 12/1200 draws ~105 A at full output:")
    print("  expect ~700 W continuous and ~1000 W for 10 s bursts; charge sources (MPPT 30 A, Orion 50 A) are within the 60 A charge limit.")
    print("  ~15 kg lighter than v9.  Both cards still unplug at their tops and lift out.")
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


PLATE_PILOTS = {}   # set by build_v13: where the inverter plate's pilots are, for the pin check below


def check_countersinks(a):
    """A 11 mm disc 1 mm thick just inside every registered countersink's face must meet no material."""
    bad = 0
    parts = {c.name: c.obj.val() for c in a.children}
    for (part, pt, axis) in COUNTERSINKS:
        ax = cq.Vector(*axis).normalized()
        probe = cq.Workplane("XY").add(cq.Solid.makeCylinder(5.5, 1.0, cq.Vector(*pt), ax)).val()
        vol = probe.intersect(parts[part]).Volume() if part in parts else -1
        if vol != 0 and vol > 1e-6 or vol < 0:
            bad += 1; print(f"  NO COUNTERSINK on {part} at {tuple(round(v, 1) for v in pt)}" + ("" if vol >= 0 else " (part not found)"))
    print(f"== Countersinks: {len(COUNTERSINKS)} registered, {bad} not cut ==")


def check_plate_pilots(a):
    """Push a 3.6 mm pin along Y through every pilot the plate was asked for and report any that is blocked (a pilot
    that a tile cut missed, or a skin left on one face).  Added 2026-10-25 after the six bottom-band pilots for the bus
    shelf wall turned out never to have been collected into the plate's patch list."""
    if not PLATE_PILOTS:
        return
    tiles = [c.obj.val() for c in a.children if "plate_inverter_tile" in c.name]
    solid = tiles[0]
    for t_ in tiles[1:]:
        solid = solid.fuse(t_)
    x0, y, z0, t = PLATE_PILOTS["x0"], PLATE_PILOTS["y"], PLATE_PILOTS["z0"], P["card_t"]
    blocked = []
    for patch in PLATE_PILOTS["patches"]:
        u, v = patch[0], patch[1]
        pin = cq.Workplane("XZ").center(x0 + u, z0 + v).circle(1.8).extrude(-(t + 4)).translate((0, y - 2, 0)).val()
        if pin.intersect(solid).Volume() > 1e-6:
            blocked.append((x0 + u, z0 + v))
    print(f"== Plate pilots: {len(PLATE_PILOTS['patches'])} asked for, {len(blocked)} blocked ==")
    for (x, z) in blocked:
        print(f"  BLOCKED pilot at x {x:.1f} z {z:.1f}")


def export(a: cq.Assembly):
    os.makedirs(OUT, exist_ok=True); os.makedirs(VIEWER, exist_ok=True); os.makedirs(STL, exist_ok=True)
    for old in os.listdir(STL):          # part names carry positions; drop stale files from earlier layouts
        if old.endswith(".stl") and not old.startswith(("print_tool_", "plate_")):   # tools.py / plates.py output, keep
            os.remove(os.path.join(STL, old))
    glb = os.path.join(OUT, "cage.glb"); a.export(glb, tolerance=1.5, angularTolerance=0.7)
    glb_to_json(glb, os.path.join(VIEWER, f"cage-{VARIANT}.json"))
    if P["card_plane"] in ("xz", "v7", "v8", "v9", "v12"):
        with open(os.path.join(VIEWER, f"dims-{VARIANT}.json"), "w") as f:
            json.dump({"xz": dims_bookshelf, "v7": dims_v7, "v8": dims_v8, "v9": dims_v9, "v12": dims_v13 if P.get("box") == "v13" else dims_v12}[P["card_plane"]](), f)
    print("== Printed parts (P1P/P1S bed 256 x 256 x 256) ==")
    seen = {}
    for child in a.children:
        if child.name.startswith("print_"):
            path = os.path.join(STL, f"{child.name.replace('__card', '')}.stl")
            cq.exporters.export(child.obj, path)
            tris = plates.reorient_file(path)      # the file lies in its print orientation at the origin (plates.ORIENT_RULES)
            dims = tuple(round(max(v[k] for t in tris for v in t), 1) for k in range(3))   # as it sits on the bed: x, y, height
            key = child.name.split("_")[1]
            seen.setdefault((key, dims), 0); seen[(key, dims)] += 1
    for (key, dims), n in seen.items():
        flag = "" if dims[0] <= 256 and dims[1] <= 256 and dims[2] <= 256 else "  <-- exceeds bed"
        print(f"  {n:2d} x {key:10s} {dims[0]:6.1f} x {dims[1]:6.1f} x {dims[2]:6.1f} tall{flag}")
    if any(c.name.startswith("print_") for c in a.children):
        try:
            plates.build_plates(STL, quiet=True)   # the plate_*.stl beds of grouped small parts
        except FileNotFoundError as e:
            print("  (no plates for this variant:", e.filename, ")")


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
    if P["card_plane"] == "pack2":
        return report_pack2()
    if P["card_plane"] == "v12":
        return report_v13() if P.get("box") == "v13" else report_v12()
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


def clash_report(a: cq.Assembly, prefixes=("print_", "cube_", "bar_", "battery_", "power_", "socket_", "victron_", "panel_", "lid_", "garmin_")):
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
                inter = si.intersect(sj); v = inter.Volume()
                if v > 1.0:   # a coplanar face contact (a battery on its tray floor) reports a sliver with no thickness: a touch, not a clash
                    ib = inter.BoundingBox()
                    if min(ib.xlen, ib.ylen, ib.zlen) < 0.05:
                        v = 0.0
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
        check_plate_pilots(asm)
        check_countersinks(asm)
        clash_report(asm)
    export(asm)
    print("wrote", os.path.abspath(os.path.join(VIEWER, f"cage-{VARIANT}.json")))
