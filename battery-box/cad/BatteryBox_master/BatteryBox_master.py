# Author: Dan Gorman / Antigravity CAD Generator
# Description: Parametric Autodesk Fusion assembly generator for the 4Runner Overlanding
#              Battery & Electronics Box (v12s / v12s_h2d for Bambu Lab H2D & P1P).

import os
import sys
import traceback
import adsk.core
import adsk.fusion

# ==============================================================================
# 1. TOP-LEVEL PARAMETRIC ARCHITECTURE (ALL DIMENSIONS IN MILLIMETERS)
# ==============================================================================

# Printer Target Preset:
#   "H2D" -> Bambu Lab H2D (350 x 320 x 325 mm bed): Inverter plate splits into 2 tiles (252.8 x 256 mm) + 2 splines, no horizontal lap.
#   "P1P" -> Bambu Lab P1P/P1S (256 x 256 x 256 mm bed): Inverter plate splits into 6 tiles (168.5 x 140 mm) + 8 splines with 24 mm half-laps.
PRINTER_PRESET: str = "H2D"
USE_REAL_VICTRON_STEPS: bool = True
STEP_MODELS_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "step_models")

BED_H2D: tuple[float, float, float] = (350.0, 320.0, 325.0)
BED_P1P: tuple[float, float, float] = (256.0, 256.0, 256.0)
TILE_MAX_MM: float = 340.0 if PRINTER_PRESET == "H2D" else 250.0

# Overall As-Built Enclosure Envelope (Cut-down 25" Goose Gear IceBox 1.3 Frame)
# Coordinate System:
#   X = Depth  (0.0 at rear panel against IceBox -> +571.5 mm at front port panel)
#   Y = Width  (0.0 at outboard vehicle-wall side -> +488.1 mm at inboard lane)
#   Z = Height (0.0 at bottom rail face -> +281.7 mm at top rail face, +6.0 mm flat lid)
BOX_DEPTH_X: float = 571.5
BOX_WIDTH_Y: float = 488.1
BOX_HEIGHT_Z: float = 281.7

# Metric 25-Series MaxLite Extrusion Frame, Corner Cubes & Slot-Captured Panels
RAIL_PROFILE: float = 25.0          # 25.0 x 25.0 mm metric 25-series extrusion
RAIL_SLOT_W: float = 6.5            # 6.5 mm T-slot opening (accepts 1/4"-20 drop-in T-nuts)
RAIL_SLOT_DEPTH: float = 3.5        # Visual & tongue capture slot depth
CORNER_CUBE: float = 25.75          # 25.75 mm 3-way corner cubes (stand 0.375-0.75 mm proud)
PANEL_THICK: float = 6.0            # 6.0 mm phenolic-faced okoume marine plywood panels
PANEL_TONGUE: float = 3.0           # 3.0 mm tongue captured inside rail centerline slots
PANEL_OUTER_OFFSET: float = RAIL_PROFILE / 2.0 - PANEL_TONGUE / 2.0  # 9.5 mm from outer rail face
LID_THICK: float = 6.0              # Flat 571.5 x 488.1 x 6.0 mm top lid resting on top rails

# Derived Rail Cut Lengths (Outside dim - 2 * 25.75 mm corner cubes)
HEIGHT_RAIL_LEN: float = BOX_HEIGHT_Z - 2.0 * CORNER_CUBE  # 230.2 mm
WIDTH_RAIL_LEN: float = BOX_WIDTH_Y - 2.0 * CORNER_CUBE    # 436.6 mm (uncut factory length)
DEPTH_RAIL_LEN: float = BOX_DEPTH_X - 2.0 * CORNER_CUBE    # 520.0 mm
INNER_X0: float = RAIL_PROFILE                              # 25.0 mm (back rail inner face)
INNER_X1: float = BOX_DEPTH_X - RAIL_PROFILE                # 546.5 mm (front rail inner face)
INNER_Y0: float = RAIL_PROFILE                              # 25.0 mm (outboard rail inner face)
INNER_Y1: float = BOX_WIDTH_Y - RAIL_PROFILE                # 463.1 mm (inboard rail inner face)
INNER_DEPTH_X: float = BOX_DEPTH_X - 2.0 * RAIL_PROFILE     # 521.5 mm rail-to-rail
INNER_WIDTH_Y: float = BOX_WIDTH_Y - 2.0 * RAIL_PROFILE     # 438.1 mm rail-to-rail

# Structural Fillets & Corner Radii
CUBE_FILLET_R: float = 1.5
STRAP_FILLET_R: float = 10.0
WINDOW_FILLET_R: float = 8.0
COMP_FILLET_R: float = 3.0
BATT_FILLET_R: float = 5.0

# Fastener & Heat-Set Insert Specifications (Zero Loose Nuts Inside Enclosure)
UNC_25_CLEAR_DIA: float = 6.8       # 1/4"-20 through-hole clearance (mm)
UNC_25_CSK_DIA: float = 13.2        # 82-deg flat-head countersink outer diameter (mm)
UNC_25_CSK_DEPTH: float = 3.6       # 82-deg flat-head countersink depth (mm)
M4_CLEAR_DIA: float = 4.6           # M4 button-head clearance hole (mm)
M4_INSERT_BORE_DIA: float = 5.6     # McMaster 94180A353 (std 7.9 mm) & 94180A351 (short 4.7 mm) pre-printed bore
M4_STD_INSERT_DEPTH: float = 12.0   # Melt-room blind bore depth in thick walls
M5_INSERT_BORE_DIA: float = 7.5     # McMaster 94180A361 tapered M5 insert (6.7 mm long) bench-tuned bore
M5_INSERT_MOUTH_DIA: float = 8.46   # 8-deg tapered entry mouth for flange seating
M5_TAPER_DEPTH: float = 3.4         # 8-deg tapered mouth depth (top 3.4 mm of M5 bore)
M5_BLIND_DEPTH: float = 9.5         # 6.7 mm insert + 2.8 mm melt room in 11.0 mm decks (leaves 1.5 mm solid floor)
M5_FAR_RELIEF_DIA: float = 9.0      # Far-face pocket diameter in 6.0 mm inverter plate so 6.7 mm M5 insert sits inside
M5_FAR_RELIEF_DEPTH: float = 1.3    # Far-face pocket depth in 6.0 mm inverter plate
M5_DECK_THICK: float = 11.0         # Deck thickness for Bus Shelf floor and Breaker Drop Shelves

# Outboard Zone: Battery Trays (x2) & Breaker Hold-Down Drop Shelves (x2)
BATT_L: float = 229.0               # Victron SuperPack 12.8V/60Ah length (along X)
BATT_W: float = 138.0               # Victron SuperPack 12.8V/60Ah width (along Y)
BATT_BODY_H: float = 208.0          # Flat case top height (M6 terminals add 5 mm to 213.0 mm total)
BATT_TOTAL_H: float = 213.0
TRAY_CLEARANCE: float = 0.5         # 0.5 mm per side snug pocket fit
TRAY_WALL_THICK: float = 6.0        # Outboard & end wall thickness
TRAY_INBOARD_WALL: float = 21.0     # Thickened inboard wall carrying M4 top & side inserts
TRAY_FLOOR_THICK: float = 6.0       # Tray floor thickness
TRAY_LIP_H: float = 30.0            # Pocket wall height above floor (total tray height = 36.0 mm)
TRAY_OUTER_LEN_X: float = BATT_L + 2.0 * TRAY_WALL_THICK + 2.0 * TRAY_CLEARANCE  # 242.0 mm
TRAY_OUTER_WID_Y: float = 167.0     # Matches standard column boundary (6.0 + 139.0 pocket + 22.0 / 21.0 wall)
TRAY_POCKET_LEN_X: float = BATT_L + 2.0 * TRAY_CLEARANCE  # 230.0 mm
TRAY_POCKET_WID_Y: float = BATT_W + 2.0 * TRAY_CLEARANCE  # 139.0 mm
TRAY_0_X0: float = INNER_X0                               # 25.0 mm (butts back width rail)
TRAY_1_X0: float = INNER_X1 - TRAY_OUTER_LEN_X            # 304.5 mm (butts front width rail)
TRAY_Y0: float = INNER_Y0 + 1.0                           # 26.0 mm (1 mm off outboard rail, walls bolt flush)
TRAY_CUBE_NOTCH: float = 2.5        # 2.5 x 2.5 mm corner notch clearing the 25.75 mm corner cube
TRAY_OUTBOARD_BOLT_DX: tuple[float, float] = (70.0, TRAY_OUTER_LEN_X - 70.0)  # (70.0, 172.0)
TRAY_END_BOLT_DY: tuple[float, float] = (28.0, TRAY_OUTER_WID_Y - 28.0)       # (28.0, 139.0)
TRAY_LIP_M4_DX: tuple[tuple[float, ...], tuple[float, ...]] = (
    (40.0, 100.0, 140.0),           # Tray 0 (back) horizontal M4 insert X offsets (Z = 17.0 mm)
    (40.0, 120.0, 200.0),           # Tray 1 (front) horizontal M4 insert X offsets (Z = 17.0 mm)
)

# Breaker Drop Shelves (Hold-Down + Eaton Bussmann 285 Mount + 4 AWG Wire Channel)
DROP_SHELF_LEN_X: float = 130.0
DROP_SHELF_PAD_THICK: float = 3.0
DROP_SHELF_DROP: float = 2.0        # Compresses 3 mm EPDM foam pad to 1.0 mm modeled gap
DROP_SHELF_Z0: float = TRAY_FLOOR_THICK + BATT_BODY_H + DROP_SHELF_PAD_THICK - DROP_SHELF_DROP  # 215.0 mm
DROP_SHELF_HANGER_BAND_Y: float = 13.0   # 13.0 mm upper band against top outboard rail (takes 3/4" flat-head screws)
DROP_SHELF_WIRE_RELIEF_Y: float = 7.5    # 7.5 mm back relief below rail (Y = 32.5 mm, flush with battery!) -> creates 17.0 mm 4 AWG wire channel against side panel!
DROP_SHELF_LEG_Y0: float = TRAY_Y0 + TRAY_OUTER_WID_Y - TRAY_WALL_THICK - 15.0  # 172.0 mm
DROP_SHELF_LEG_THICK: float = 6.0
DROP_SHELF_FOOT_WID: float = 15.0
DROP_SHELF_BOLT_DX: tuple[float, float] = (25.0, 105.0)

# Center Column: 3-Plate U-Channel Bus Shelf & Inboard Wire Routing Trough
BUS_SHELF_Y0: float = TRAY_Y0 + TRAY_OUTER_WID_Y          # 193.0 mm
BUS_SHELF_Y1: float = 303.0                               # 303.0 mm (110.0 mm wide column)
BUS_SHELF_WALL_H: float = 34.0                            # 34.0 mm side walls forming wire trough
BUS_SHELF_END_WALL_H: float = 30.0
BUS_SHELF_OUT_LIP_T: float = 6.0                          # 6.0 mm lip bolted to battery trays
BUS_SHELF_IN_WALL_T: float = 4.0                          # 4.0 mm sill wall bolted to inverter plate
BUS_SHELF_END_LEN: float = 584.2 / 3.0                    # 194.733 mm (end plates 0 & 2; middle plate 1 = 132.033 mm)
BUS_SHELF_LAP_LEN: float = 20.0                           # 20.0 mm vertical-wall half-laps
BUS_SHELF_RAIL_BOLT_Y: tuple[float, float] = (BUS_SHELF_Y0 + 30.0, BUS_SHELF_Y1 - 40.0)  # (223.0, 263.0)

# Single-Row Bus Line (23.0 mm from tray edge -> leaves 57.0 mm inboard wire trough clear under cable window)
BUSBAR_POS_X0: float = 43.0
BUSBAR_NEG_X0: float = 366.0
BUSBAR_Y0: float = BUS_SHELF_Y0 + BUS_SHELF_OUT_LIP_T + 1.0       # 200.0 mm
SMARTSHUNT_X0: float = 226.0
SMARTSHUNT_Y0: float = BUS_SHELF_Y0 + BUS_SHELF_OUT_LIP_T + 4.5   # 203.5 mm

# Inverter Mounting Plate & One-Piece Full-Height Slotted Guide Posts (H2D)
INVERTER_PLATE_Y0: float = 303.0
INVERTER_PLATE_THICK: float = 6.0
INVERTER_PLATE_CLEAR: float = 0.6
POST_W_Y: float = 24.0              # Post width along Y (294.0 .. 318.0 mm, centered on plate at Y=306.0)
POST_D_X: float = 18.0              # Post depth along X against back/front width rails
POST_H_Z: float = BOX_HEIGHT_Z - 3.0  # One-piece full-height H2D post (278.7 mm, 3 mm below lid; no separate clip needed!)
POST_SLOT_DEPTH_X: float = 10.0     # 10.0 mm deep continuous open-top slot capturing plate ends (Z = 30 .. 278.7 mm)
POST_SLOT_Z0: float = 30.0          # Solid sill below Z = 30.0 mm for 1/4"-20 rail bolt at Z = 12.5 mm
INVERTER_PLATE_X0: float = INNER_X0 + POST_D_X - POST_SLOT_DEPTH_X  # 33.0 mm
INVERTER_PLATE_X1: float = INNER_X1 - POST_D_X + POST_SLOT_DEPTH_X  # 538.5 mm (length = 505.5 mm)
INVERTER_PLATE_Z0: float = 21.0
INVERTER_PLATE_H: float = 256.0     # Z = 21.0 .. 277.0 mm
PLATE_LAP_WIDTH: float = 24.0       # Horizontal half-lap width when printed in 6 tiles (P1P preset)
SPLINE_DIM: tuple[float, float, float] = (60.0, 3.0, 18.0)  # (length X, thickness Y, width Z)

# Filleted 70 x 70 mm Cable Pass-Through Window in Inverter Plate (opens onto clear inboard wire trough)
CABLE_WINDOW_X0: float = BOX_DEPTH_X - 145.0              # 426.5 mm
CABLE_WINDOW_X1: float = BOX_DEPTH_X - 75.0               # 496.5 mm (70.0 mm wide)
CABLE_WINDOW_Z0: float = 40.0
CABLE_WINDOW_Z1: float = 110.0                            # 70.0 mm tall

# Inboard Wiring Lane: Two-Piece Full-Height Garmin Hanger & Wire-Management Tie-Slot Wall
GARMIN_HANGER_LEN_X: float = 130.0
GARMIN_HANGER_THICK_Y: float = 6.0
GARMIN_HANGER_X0: float = BOX_DEPTH_X - 25.0 - 55.0 - 20.0 - GARMIN_HANGER_LEN_X  # 341.5 mm (20 mm behind port bodies)
GARMIN_HANGER_Y0: float = INNER_Y1 - GARMIN_HANGER_THICK_Y                        # 457.1 mm (against inboard rail)
GARMIN_UPPER_Z0: float = 130.0
GARMIN_UPPER_Z1: float = BOX_HEIGHT_Z - 3.0               # 278.7 mm
GARMIN_LOWER_Z0: float = 2.0
GARMIN_LOWER_Z1: float = 129.0                            # 1.0 mm gap below upper hanger
GARMIN_RAIL_BOLT_DX: tuple[float, float] = (25.0, GARMIN_HANGER_LEN_X - 25.0)     # X = 366.5, 446.5 mm
TIE_SLOT_W_X: float = 4.0
TIE_SLOT_H_Z: float = 10.0
TIE_SLOT_PAIR_SPAN_X: float = 16.0                        # Slots at -8.0 and +8.0 mm from center
TIE_SLOT_CENTERS_DX: tuple[float, float, float] = (30.0, 65.0, 100.0)
TIE_SLOT_ROWS_UPPER_Z: tuple[float, float] = (138.0, 243.0)
TIE_SLOT_ROWS_LOWER_Z: tuple[float, float] = (40.0, 100.0)

# IceBox Stack Straps (x4 across bottom depth rail seam, 6.0 mm thick for 1/4"-20 x 1/2" countersinks)
STRAP_W_X: float = 60.0
STRAP_H_Z: float = 46.0
STRAP_T_Y: float = 6.0
STRAP_PITCH_X: float = 30.0
STRAP_PITCH_Z: float = 25.75
STRAP_SLOT_FLOAT_Z: float = 2.4
STRAP_CLEAR_CUBE_X: float = 70.0

# Component Envelopes & Mounting Hole Patterns (u, v from component lower-back corner)
COMP_SPECS: dict[str, dict] = {
    "multiplus_1200_long": {
        "dims": (375.0, 101.0, 249.0),  # (X depth, Y width, Z height) on long side
        "pos": (46.0, INVERTER_PLATE_Y0 + INVERTER_PLATE_THICK + 2.0, 22.0),
        "holes_xz": [(68.0, 14.2), (311.8, 14.2), (68.0, 234.8), (311.8, 234.8)],
        "insert": "M5",
        "face_side": +1,
    },
    "mppt_up": {
        "dims": (130.0, 70.0, 186.0),
        "pos": (50.0, INVERTER_PLATE_Y0 - 70.0 - 3.0, 62.0),  # Top holes at 62 + 181 = 243.0 mm (aligned with Cerbo & Orion)
        "holes_xz": [(33.5, 5.0), (105.0, 5.0), (33.5, 181.0), (105.0, 181.0)],
        "insert": "M5",
        "face_side": -1,
    },
    "cerbo": {
        "dims": (154.0, 48.0, 78.0),
        "pos": (190.0, INVERTER_PLATE_Y0 - 48.0 - 3.0, 175.0),  # Top holes at 175 + 68 = 243.0 mm (aligned with MPPT & Orion; top at 253 mm)
        "holes_xz": [(5.5, 10.0), (148.5, 10.0), (5.5, 68.0), (148.5, 68.0)],
        "insert": "M4",
        "face_side": -1,
    },
    "orion": {
        "dims": (123.0, 40.0, 137.0),
        "pos": (354.0, INVERTER_PLATE_Y0 - 40.0 - 3.0, 118.0),  # Top holes at 118 + 125 = 243.0 mm (aligned with MPPT & Cerbo)
        "holes_xz": [(6.9, 12.0), (116.2, 12.0), (6.9, 125.0), (116.2, 125.0)],
        "insert": "M4",
        "face_side": -1,
    },
    "breaker_285": {
        "dims": (81.28, 48.13, 37.85),  # 31.5 body + 6.35 trip button
        "holes_xy": [(12.32, 10.73), (68.96, 37.40)],
        "insert": "M5",
    },
    "busbar_5stud": {
        "dims": (155.0, 35.0, 32.0),
        "holes_xy": [(11.5, 16.0), (145.5, 16.0)],  # 134.0 mm center-to-center M5 mounting ears
        "insert": "M5",
    },
    "shunt_500a": {
        "dims": (120.0, 46.0, 35.0),
        "holes_xy": [(9.5, 12.5), (110.5, 12.5)],   # 101.0 mm centers along stud line (12.5 mm from stud edge)
        "insert": "M5",
    },
    "garmin_ps": {
        "dims": (125.0, 32.0, 75.0),
        "pos": (GARMIN_HANGER_X0 + 2.5, GARMIN_HANGER_Y0 - 32.0, 150.0),
        "holes_xz": [(20.0, 37.0), (105.0, 37.0)],
        "insert": "M4",
    },
    "gnd_bus_2701": {
        "dims": (76.5, 25.0, 46.5),
        "pos": (GARMIN_HANGER_X0 + (GARMIN_HANGER_LEN_X - 76.5) / 2.0, GARMIN_HANGER_Y0 - 25.0, 70.0 - 46.5 / 2.0),
        "holes_xz": [(9.65, 23.25), (66.85, 23.25)],  # 57.20 mm (2.252") centers along longitudinal centerline
        "insert": "M4",
    },
}

# Front Panel Port Cutouts: (name, shape, y_center_mm, z_center_mm, size_tuple_mm, inward_depth_mm)
FRONT_PANEL_PORTS: list[tuple[str, str, float, float, tuple[float, ...], float]] = [
    ("l14_30_shore_in", "circle", 423.0, 72.0, (60.0,), 55.0),
    ("l14_30_inv_out", "circle", 423.0, 142.0, (60.0,), 55.0),
    ("sb50_alt_in", "rect", 370.0, 118.0, (37.0, 48.0), 48.0),
    ("socket_usb_low", "circle", 370.0, 162.0, (22.0,), 40.0),
    ("socket_usb_high", "circle", 370.0, 195.0, (22.0,), 40.0),
    ("socket_12v_aux", "circle", 338.0, 157.0, (29.0,), 40.0),
    ("sb50_pack2_umbilical", "rect", 215.0, 110.0, (37.0, 48.0), 48.0),
]

# Rear Panel GX Touch 50 Cutout & Printed Bezel
GX_TOUCH_YC: float = BOX_WIDTH_Y - RAIL_PROFILE - 80.0     # 383.1 mm
GX_TOUCH_ZC: float = 160.0
GX_TOUCH_CUT_W_Y: float = 128.0
GX_TOUCH_CUT_H_Z: float = 86.0
GX_TOUCH_BEZEL_W_Y: float = 150.0
GX_TOUCH_BEZEL_H_Z: float = 108.0
GX_TOUCH_BEZEL_T_X: float = 3.0


# ==============================================================================
# 2. FUSION 360 GEOMETRY & FEATURE TREE HELPER FUNCTIONS
# ==============================================================================

def cm(mm_val: float) -> float:
    """Convert millimeters to Fusion's internal unit (centimeters)."""
    return mm_val * 0.1


def val(mm_val: float) -> adsk.core.ValueInput:
    """Create a Fusion ValueInput from a millimeter value."""
    return adsk.core.ValueInput.createByReal(cm(mm_val))


def pt3d(x_mm: float, y_mm: float, z_mm: float) -> adsk.core.Point3D:
    """Create a 3D world point in Fusion internal units (cm) from mm coordinates."""
    return adsk.core.Point3D.create(cm(x_mm), cm(y_mm), cm(z_mm))


def register_user_parameters(design: adsk.fusion.Design) -> None:
    """Register key top-level dimensions into Fusion's Change Parameters table."""
    params = [
        ("BOX_DEPTH_X", BOX_DEPTH_X, "mm", "Overall box depth (front-to-back)"),
        ("BOX_WIDTH_Y", BOX_WIDTH_Y, "mm", "Overall box width (outboard-to-inboard)"),
        ("BOX_HEIGHT_Z", BOX_HEIGHT_Z, "mm", "Overall box frame height (excluding 6mm top lid)"),
        ("RAIL_PROFILE", RAIL_PROFILE, "mm", "Metric 25-series extrusion width"),
        ("CORNER_CUBE", CORNER_CUBE, "mm", "Goose Gear corner cube dimension"),
        ("PANEL_THICK", PANEL_THICK, "mm", "Phenolic plywood panel thickness"),
        ("TRAY_CLEARANCE", TRAY_CLEARANCE, "mm", "Per-side battery pocket clearance"),
        ("M5_DECK_THICK", M5_DECK_THICK, "mm", "Thickened deck for blind M5 heat-set inserts"),
        ("DROP_SHELF_WIRE_RELIEF_Y", DROP_SHELF_WIRE_RELIEF_Y, "mm", "Back relief for 13.5mm 4-AWG wire channel"),
        ("TILE_MAX_MM", TILE_MAX_MM, "mm", f"Max inverter plate tile size ({PRINTER_PRESET} preset)"),
    ]
    user_params = design.userParameters
    for name, number, unit, comment in params:
        existing = user_params.itemByName(name)
        if not existing:
            user_params.add(name, adsk.core.ValueInput.createByString(f"{number} {unit}"), unit, comment)


def create_subcomponent(parent_comp: adsk.fusion.Component, name: str) -> adsk.fusion.Component:
    """Create a new child component inside parent_comp for a clean Browser tree (falls back to parent_comp if in single-part mode)."""
    try:
        occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = name
        return occ.component
    except Exception:
        return parent_comp


def create_offset_plane(comp: adsk.fusion.Component, axis: str, offset_mm: float) -> adsk.fusion.ConstructionPlane:
    """Create a construction plane parallel to XY ('z'), XZ ('y'), or YZ ('x') at exact world coordinate offset_mm."""
    axis_lower = axis.lower()
    if axis_lower == "z":
        base_plane = comp.xYConstructionPlane
        axis_vec = adsk.core.Vector3D.create(0, 0, 1)
    elif axis_lower == "y":
        base_plane = comp.xZConstructionPlane
        axis_vec = adsk.core.Vector3D.create(0, 1, 0)
    elif axis_lower == "x":
        base_plane = comp.yZConstructionPlane
        axis_vec = adsk.core.Vector3D.create(1, 0, 0)
    else:
        raise ValueError(f"Unknown axis: {axis}")

    normal = base_plane.geometry.normal
    sign = 1.0 if normal.dotProduct(axis_vec) >= 0.0 else -1.0
    plane_input = comp.constructionPlanes.createInput()
    plane_input.setByOffset(base_plane, val(offset_mm * sign))
    plane = comp.constructionPlanes.add(plane_input)
    plane.isLightBulbOn = False
    return plane


def sketch_world_point(sketch: adsk.fusion.Sketch, x_mm: float, y_mm: float, z_mm: float) -> adsk.core.Point3D:
    """Project a 3D world coordinate (mm) onto the 2D sketch plane (z = 0 in sketch space)."""
    pt_local = sketch.modelToSketchSpace(pt3d(x_mm, y_mm, z_mm))
    return adsk.core.Point3D.create(pt_local.x, pt_local.y, 0.0)


def extrude_all_profiles(
    comp: adsk.fusion.Component,
    sketch: adsk.fusion.Sketch,
    axis: str,
    thickness_mm: float,
    operation: int,
    target_body: adsk.fusion.BRepBody | None = None,
    body_name: str | None = None,
    taper_deg: float = 0.0,
) -> adsk.fusion.BRepBody | None:
    """Extrude all profiles in a sketch along world +X, +Y, or +Z by thickness_mm (signed), with optional taper angle."""
    sketch.isLightBulbOn = False
    if sketch.profiles.count == 0:
        return target_body

    profs = adsk.core.ObjectCollection.create()
    for i in range(sketch.profiles.count):
        profs.add(sketch.profiles.item(i))

    axis_vec = {
        "x": adsk.core.Vector3D.create(1, 0, 0),
        "y": adsk.core.Vector3D.create(0, 1, 0),
        "z": adsk.core.Vector3D.create(0, 0, 1),
    }[axis.lower()]

    sketch_normal = sketch.xDirection.crossProduct(sketch.yDirection)
    dir_sign = 1.0 if sketch_normal.dotProduct(axis_vec) >= 0.0 else -1.0
    signed_dist = thickness_mm * dir_sign

    ext_features = comp.features.extrudeFeatures
    ext_input = ext_features.createInput(profs, operation)
    if abs(taper_deg) > 1e-6:
        extent_def = adsk.fusion.DistanceExtentDefinition.create(val(abs(signed_dist)))
        ext_dir = (
            adsk.fusion.ExtentDirections.PositiveExtentDirection
            if signed_dist >= 0.0
            else adsk.fusion.ExtentDirections.NegativeExtentDirection
        )
        ext_input.setOneSideExtent(
            extent_def,
            ext_dir,
            adsk.core.ValueInput.createByString(f"{taper_deg} deg"),
        )
    else:
        ext_input.setDistanceExtent(False, val(signed_dist))
    if target_body is not None and operation in (
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        adsk.fusion.FeatureOperations.IntersectFeatureOperation,
    ):
        ext_input.participantBodies = [target_body]

    ext = ext_features.add(ext_input)
    if operation == adsk.fusion.FeatureOperations.NewBodyFeatureOperation and ext.bodies.count > 0:
        new_body = ext.bodies.item(0)
        if body_name:
            new_body.name = body_name
        return new_body
    return target_body


def add_box_feature(
    comp: adsk.fusion.Component,
    x0: float,
    y0: float,
    z0: float,
    dx: float,
    dy: float,
    dz: float,
    operation: int = adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    target_body: adsk.fusion.BRepBody | None = None,
    body_name: str | None = None,
) -> adsk.fusion.BRepBody | None:
    """Create a parametric rectangular box extrusion spanning (x0..x0+dx, y0..y0+dy, z0..z0+dz)."""
    plane = create_offset_plane(comp, "z", z0)
    sketch = comp.sketches.add(plane)
    p0 = sketch_world_point(sketch, x0, y0, z0)
    p1 = sketch_world_point(sketch, x0 + dx, y0 + dy, z0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(p0, p1)
    return extrude_all_profiles(comp, sketch, "z", dz, operation, target_body, body_name)


def cut_cylinders_on_plane(
    comp: adsk.fusion.Component,
    target_body: adsk.fusion.BRepBody,
    axis: str,
    plane_pos_mm: float,
    extrude_depth_mm: float,
    centers_and_radii: list[tuple[float, float, float, float]],
    taper_deg: float = 0.0,
) -> None:
    """Cut multiple circular or conical bores in a single clean sketch feature on an XY, XZ, or YZ offset plane."""
    if not centers_and_radii:
        return
    plane = create_offset_plane(comp, axis, plane_pos_mm)
    sketch = comp.sketches.add(plane)
    circles = sketch.sketchCurves.sketchCircles
    for wx, wy, wz, rad in centers_and_radii:
        cpt = sketch_world_point(sketch, wx, wy, wz)
        circles.addByCenterRadius(cpt, cm(rad))
    extrude_all_profiles(
        comp,
        sketch,
        axis,
        extrude_depth_mm,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        target_body,
        taper_deg=taper_deg,
    )


def cut_countersink_14_20(
    comp: adsk.fusion.Component,
    target_body: adsk.fusion.BRepBody,
    axis: str,
    face_pos_mm: float,
    inward_sign: float,
    centers_xyz: list[tuple[float, float, float]],
    wall_thick_mm: float = 6.0,
    with_floor_head_relief: bool = False,
) -> None:
    """Cut 1/4"-20 clearance holes (Ø6.8 mm), true 82-deg conical countersinks, and optional Ø14.0 x 5.0 mm floor head-relief pockets."""
    if not centers_xyz:
        return
    # 1. Through-hole shaft (Ø6.8 mm)
    through_holes = [
        (wx, wy, wz, UNC_25_CLEAR_DIA / 2.0) for (wx, wy, wz) in centers_xyz
    ]
    cut_cylinders_on_plane(
        comp,
        target_body,
        axis,
        face_pos_mm - inward_sign * 0.5,
        inward_sign * (wall_thick_mm + 2.0),
        through_holes,
    )
    # 2. True 82-degree conical countersink (r = 7.0 mm at 0.5 mm outside face, tapering at -41 deg over 4.1 mm down to Ø6.8 mm shaft)
    csk_cones = [
        (wx, wy, wz, 7.0) for (wx, wy, wz) in centers_xyz
    ]
    cut_cylinders_on_plane(
        comp,
        target_body,
        axis,
        face_pos_mm - inward_sign * 0.5,
        inward_sign * 4.1,
        csk_cones,
        taper_deg=-41.0,
    )
    # 3. Optional Ø14.0 x 10.0 mm floor head_relief pocket (carves 2x-long screw-head & insertion-angle clearance into tray & bus-shelf floors)
    if with_floor_head_relief:
        cut_cylinders_on_plane(
            comp,
            target_body,
            axis,
            face_pos_mm - inward_sign * 10.0,
            inward_sign * 10.05,
            csk_cones,
        )


def cut_blind_m5_tapered_bores(
    comp: adsk.fusion.Component,
    target_body: adsk.fusion.BRepBody,
    z_top_mm: float,
    xy_centers: list[tuple[float, float]],
) -> None:
    """Cut blind Ø7.5 x 9.5 mm M5 heat-set insert bores with true 8-deg tapered mouths (Ø8.46 x 3.4 mm) from z_top_mm."""
    if not xy_centers:
        return
    main_bores = [(x, y, z_top_mm, M5_INSERT_BORE_DIA / 2.0) for (x, y) in xy_centers]
    cut_cylinders_on_plane(comp, target_body, "z", z_top_mm + 0.2, -(M5_BLIND_DEPTH + 0.2), main_bores)
    mouth_bores = [(x, y, z_top_mm, M5_INSERT_MOUTH_DIA / 2.0) for (x, y) in xy_centers]
    cut_cylinders_on_plane(comp, target_body, "z", z_top_mm + 0.2, -(M5_TAPER_DEPTH + 0.2), mouth_bores, taper_deg=-8.0)


def fillet_parallel_edges(
    comp: adsk.fusion.Component,
    body: adsk.fusion.BRepBody,
    axis: str,
    radius_mm: float,
    bbox_filter: tuple[float, float, float, float, float, float] | None = None,
) -> None:
    """Apply a parametric FilletFeature to straight edges of `body` parallel to `axis` ('x', 'y', 'z', or 'all')."""
    if body is None or radius_mm <= 0.0:
        return
    axis_vec = {
        "x": adsk.core.Vector3D.create(1, 0, 0),
        "y": adsk.core.Vector3D.create(0, 1, 0),
        "z": adsk.core.Vector3D.create(0, 0, 1),
    }.get(axis.lower())

    edge_coll = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        geom = edge.geometry
        if (
            geom is None
            or edge.startVertex is None
            or edge.endVertex is None
            or geom.curveType != adsk.core.Curve3DTypes.Line3DCurveType
        ):
            continue
        p_start = edge.startVertex.geometry
        p_end = edge.endVertex.geometry
        if bbox_filter is not None:
            xmin, xmax, ymin, ymax, zmin, zmax = [cm(v) for v in bbox_filter]
            mx = 0.5 * (p_start.x + p_end.x)
            my = 0.5 * (p_start.y + p_end.y)
            mz = 0.5 * (p_start.z + p_end.z)
            if not (xmin <= mx <= xmax and ymin <= my <= ymax and zmin <= mz <= zmax):
                continue
        if axis_vec is not None:
            vec = p_start.vectorTo(p_end)
            if vec.length < 1e-4:
                continue
            vec.normalize()
            if abs(vec.dotProduct(axis_vec)) < 0.98:
                continue
        edge_coll.add(edge)

    if edge_coll.count > 0:
        try:
            fillets = comp.features.filletFeatures
            f_input = fillets.createInput()
            f_input.addConstantRadiusEdgeSet(edge_coll, val(radius_mm), True)
            fillets.add(f_input)
        except Exception:
            pass


def apply_color(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    body: adsk.fusion.BRepBody | None,
    palette_name: str,
    rgb: tuple[int, int, int],
) -> None:
    """Assign a clean visual RGB color appearance to a BRepBody."""
    if body is None:
        return
    try:
        appearances = design.appearances
        target_app = appearances.itemByName(palette_name)
        if not target_app:
            base_app = None
            if appearances.count > 0:
                base_app = appearances.item(0)
            else:
                lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
                if not lib:
                    lib = app.materialLibraries.item(0)
                if lib and lib.appearances.count > 0:
                    base_app = lib.appearances.item(0)
            if base_app:
                target_app = appearances.addByCopy(base_app, palette_name)
                for prop in target_app.appearanceProperties:
                    if prop.objectType == adsk.core.ColorProperty.classType():
                        c_prop = adsk.core.ColorProperty.cast(prop)
                        c_prop.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                        break
        if target_app:
            body.appearance = target_app
    except Exception:
        pass


# Color Palette (matches repo viewer & assembly manual)
COL_ALUMINUM = ("Mat_MaxLite_Aluminum", (184, 189, 194))
COL_CUBE_BLACK = ("Mat_Anodized_Black", (35, 35, 38))
COL_PANEL_PLY = ("Mat_Phenolic_Plywood", (52, 52, 56))
COL_PRINT_ORANGE = ("Mat_Printed_PETG_Orange", (217, 84, 31))
COL_PLATE_DARK = ("Mat_Printed_PAHT_CF", (46, 48, 52))
COL_VICTRON_BLUE = ("Mat_Victron_Blue", (38, 100, 235))
COL_BATT_BLUE = ("Mat_SuperPack_Blue", (31, 128, 242))
COL_POWER_GOLD = ("Mat_Bus_Breaker_Gold", (201, 163, 38))
COL_PORT_GRAY = ("Mat_Port_Housing", (78, 80, 84))
COL_FOAM_EPDM = ("Mat_EPDM_Foam", (40, 40, 40))


def color_imported_tree(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    comp: adsk.fusion.Component,
    color_spec: tuple[str, tuple[int, int, int]],
) -> None:
    """Recursively assign appearance to all BRepBodies inside an imported STEP component hierarchy."""
    for b_idx in range(comp.bRepBodies.count):
        apply_color(app, design, comp.bRepBodies.item(b_idx), *color_spec)
    for o_idx in range(comp.occurrences.count):
        sub_occ = comp.occurrences.item(o_idx)
        color_imported_tree(app, design, sub_occ.component, color_spec)


def import_positioned_step(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    target_comp: adsk.fusion.Component,
    step_filename: str,
    part_name: str,
    color_spec: tuple[str, tuple[int, int, int]],
) -> bool:
    """Import a pre-oriented, world-positioned STEP model from step_models/ into target_comp."""
    if not USE_REAL_VICTRON_STEPS:
        return False
    step_path = os.path.join(STEP_MODELS_DIR, step_filename)
    if not os.path.exists(step_path):
        return False
    try:
        import_mgr = app.importManager
        step_opts = import_mgr.createSTEPImportOptions(step_path)
        imported = import_mgr.importToTarget2(step_opts, target_comp)
        if imported.count == 0:
            return False
        for idx in range(imported.count):
            obj = imported.item(idx)
            if obj.objectType == adsk.fusion.Occurrence.classType():
                occ = adsk.fusion.Occurrence.cast(obj)
                occ.component.name = part_name
                color_imported_tree(app, design, occ.component, color_spec)
            elif obj.objectType == adsk.fusion.BRepBody.classType():
                body = adsk.fusion.BRepBody.cast(obj)
                body.name = part_name
                apply_color(app, design, body, *color_spec)
        return True
    except Exception:
        return False


def build_bussmann_285_breaker(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    comp: adsk.fusion.Component,
    br_x: float,
    br_y: float,
    br_z: float,
    b_dx: float,
    b_dy: float,
    b_dz: float,
    idx: int,
) -> None:
    """Build or import the exact Eaton Bussmann 285-Series 150A breaker (285150F-121-S) from cage.py."""
    name = f"eaton_bussmann_285_breaker_{idx}"
    if import_positioned_step(app, design, comp, f"{name}.step", name, COL_POWER_GOLD):
        return

    bh = b_dz - 6.35      # 31.5 mm body height
    base_h = 8.13         # 8.13 mm mounting flange
    brk = add_box_feature(comp, br_x, br_y, br_z, b_dx, b_dy, base_h, body_name=name)
    fillet_parallel_edges(comp, brk, "z", 5.0)

    # Upper housing body (inset 3 mm in X, 2 mm in Y)
    add_box_feature(
        comp, br_x + 3.0, br_y + 2.0, br_z + base_h,
        b_dx - 6.0, b_dy - 4.0, bh - base_h,
        adsk.fusion.FeatureOperations.JoinFeatureOperation, brk,
    )

    # 2x Ø6.6 mm mounting holes + Ø14.0 mm corner wells at (12.32, 10.73) and (68.96, 37.40)
    mount_holes = [
        (br_x + u, br_y + v, br_z, 3.3)
        for (u, v) in ((12.32, 10.73), (b_dx - 12.32, b_dy - 10.73))
    ]
    cut_cylinders_on_plane(comp, brk, "z", br_z - 0.5, base_h + 2.0, mount_holes)
    corner_wells = [
        (br_x + u, br_y + v, br_z + base_h, 7.0)
        for (u, v) in ((12.32, 10.73), (b_dx - 12.32, b_dy - 10.73))
    ]
    cut_cylinders_on_plane(comp, brk, "z", br_z + base_h, b_dz, corner_wells)

    # 2x 16x16x9 mm diagonal stud insulators + Ø6.4x14 mm 1/4"-28 terminal studs
    stud_plane = create_offset_plane(comp, "z", br_z + bh - 2.0)
    stud_sketch = comp.sketches.add(stud_plane)
    for ex, ey in ((14.0, b_dy / 2.0 + 13.33), (b_dx - 14.0, b_dy / 2.0 - 13.33)):
        add_box_feature(
            comp, br_x + ex - 8.0, br_y + ey - 8.0, br_z + bh - 1.0,
            16.0, 16.0, 9.0,
            adsk.fusion.FeatureOperations.JoinFeatureOperation, brk,
        )
        stud_sketch.sketchCurves.sketchCircles.addByCenterRadius(
            sketch_world_point(stud_sketch, br_x + ex, br_y + ey, br_z + bh - 2.0), cm(3.2)
        )
    extrude_all_profiles(
        comp, stud_sketch, "z", 14.0,
        adsk.fusion.FeatureOperations.JoinFeatureOperation, brk,
    )

    # Push-to-trip button (12 x 8 x 6.35 mm on top center) & Reset lever (protruding 10 mm out -Y side)
    add_box_feature(
        comp, br_x + b_dx / 2.0 - 6.0, br_y + b_dy / 2.0 - 4.0, br_z + bh,
        12.0, 8.0, 6.35,
        adsk.fusion.FeatureOperations.JoinFeatureOperation, brk,
    )
    add_box_feature(
        comp, br_x + b_dx / 2.0 - 7.0, br_y - 10.0, br_z + bh - 12.0,
        14.0, 14.0, 6.0,
        adsk.fusion.FeatureOperations.JoinFeatureOperation, brk,
    )
    apply_color(app, design, brk, *COL_POWER_GOLD)


# ==============================================================================
# 3. SUB-ASSEMBLY BUILDERS
# ==============================================================================

def build_frame_and_panels(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    root: adsk.fusion.Component,
) -> adsk.fusion.Component:
    """01_8020_Frame_And_Cubes & 01b_Enclosure_Panels_And_Lid: Separate components so panels can be toggled in 1 click."""
    comp = create_subcomponent(root, "01_8020_Frame_And_Cubes")
    panel_comp = create_subcomponent(root, "01b_Enclosure_Panels_And_Lid")
    B, C, T = RAIL_PROFILE, CORNER_CUBE, PANEL_THICK

    # 1. 8x Corner Cubes (25.75 mm) with 3-axis 1/4"-20 bores & filleted edges
    for i, x in enumerate((0.0, BOX_DEPTH_X - C)):
        for j, y in enumerate((0.0, BOX_WIDTH_Y - C)):
            for k, z in enumerate((0.0, BOX_HEIGHT_Z - C)):
                nm = f"cube_{i}{j}{k}"
                cb = add_box_feature(comp, x, y, z, C, C, C, body_name=nm)
                fillet_parallel_edges(comp, cb, "all", CUBE_FILLET_R)
                mid = C / 2.0
                cut_cylinders_on_plane(comp, cb, "z", z - 0.5, C + 1.0, [(x + mid, y + mid, z, 3.4)])
                cut_cylinders_on_plane(comp, cb, "x", x - 0.5, C + 1.0, [(x, y + mid, z + mid, 3.4)])
                cut_cylinders_on_plane(comp, cb, "y", y - 0.5, C + 1.0, [(x + mid, y, z + mid, 3.4)])
                apply_color(app, design, cb, *COL_CUBE_BLACK)

    # Helper to build a metric 25-series rail with 4 longitudinal T-slots in one clean sketch extrusion
    def add_slotted_rail(axis: str, x0: float, y0: float, z0: float, length: float, name: str) -> None:
        plane = create_offset_plane(comp, axis, {"x": x0, "y": y0, "z": z0}[axis])
        sketch = comp.sketches.add(plane)
        lines = sketch.sketchCurves.sketchLines

        if axis == "x":
            p0 = sketch_world_point(sketch, x0, y0, z0)
            p1 = sketch_world_point(sketch, x0, y0 + B, z0 + B)
        elif axis == "y":
            p0 = sketch_world_point(sketch, x0, y0, z0)
            p1 = sketch_world_point(sketch, x0 + B, y0, z0 + B)
        else:
            p0 = sketch_world_point(sketch, x0, y0, z0)
            p1 = sketch_world_point(sketch, x0 + B, y0 + B, z0)
        lines.addTwoPointRectangle(p0, p1)
        rail_body = extrude_all_profiles(
            comp, sketch, axis, length, adsk.fusion.FeatureOperations.NewBodyFeatureOperation, body_name=name
        )

        # Cut the 4 T-slots (6.4 mm wide x 3.0 mm deep) along the 4 faces
        slot_sketch = comp.sketches.add(plane)
        s_lines = slot_sketch.sketchCurves.sketchLines
        sw, sd = 6.4, 3.0
        mid = B / 2.0
        if axis == "x":
            rects = [
                (x0, y0 + mid - sw / 2, z0 - 0.1, x0, y0 + mid + sw / 2, z0 + sd),
                (x0, y0 + mid - sw / 2, z0 + B - sd, x0, y0 + mid + sw / 2, z0 + B + 0.1),
                (x0, y0 - 0.1, z0 + mid - sw / 2, x0, y0 + sd, z0 + mid + sw / 2),
                (x0, y0 + B - sd, z0 + mid - sw / 2, x0, y0 + B + 0.1, z0 + mid + sw / 2),
            ]
        elif axis == "y":
            rects = [
                (x0 + mid - sw / 2, y0, z0 - 0.1, x0 + mid + sw / 2, y0, z0 + sd),
                (x0 + mid - sw / 2, y0, z0 + B - sd, x0 + mid + sw / 2, y0, z0 + B + 0.1),
                (x0 - 0.1, y0, z0 + mid - sw / 2, x0 + sd, y0, z0 + mid + sw / 2),
                (x0 + B - sd, y0, z0 + mid - sw / 2, x0 + B + 0.1, y0, z0 + mid + sw / 2),
            ]
        else:
            rects = [
                (x0 + mid - sw / 2, y0 - 0.1, z0, x0 + mid + sw / 2, y0 + sd, z0),
                (x0 + mid - sw / 2, y0 + B - sd, z0, x0 + mid + sw / 2, y0 + B + 0.1, z0),
                (x0 - 0.1, y0 + mid - sw / 2, z0, x0 + sd, y0 + mid + sw / 2, z0),
                (x0 + B - sd, y0 + mid - sw / 2, z0, x0 + B + 0.1, y0 + mid + sw / 2, z0),
            ]
        for rx0, ry0, rz0, rx1, ry1, rz1 in rects:
            s_lines.addTwoPointRectangle(
                sketch_world_point(slot_sketch, rx0, ry0, rz0),
                sketch_world_point(slot_sketch, rx1, ry1, rz1),
            )
        extrude_all_profiles(
            comp, slot_sketch, axis, length, adsk.fusion.FeatureOperations.CutFeatureOperation, rail_body
        )
        apply_color(app, design, rail_body, *COL_ALUMINUM)

    # 2. 12x Rails (4 Height, 4 Width, 4 Depth)
    h_idx = 0
    for x in (0.0, BOX_DEPTH_X - B):
        for y in (0.0, BOX_WIDTH_Y - B):
            add_slotted_rail("z", x, y, C, HEIGHT_RAIL_LEN, f"bar_h{h_idx}")
            h_idx += 1
    w_idx = 0
    for x in (0.0, BOX_DEPTH_X - B):
        for z in (0.0, BOX_HEIGHT_Z - B):
            add_slotted_rail("y", x, C, z, WIDTH_RAIL_LEN, f"bar_w{w_idx}")
            w_idx += 1
    d_idx = 0
    for y in (0.0, BOX_WIDTH_Y - B):
        for z in (0.0, BOX_HEIGHT_Z - B):
            add_slotted_rail("x", C, y, z, DEPTH_RAIL_LEN, f"bar_d{d_idx}")
            d_idx += 1

    # 3. Slot-Captured 6 mm Panels (Outboard, Inboard, Perforated Back + GX Touch, Front Port Panel)
    pm = PANEL_OUTER_OFFSET  # 9.5 mm
    tongue = PANEL_TONGUE    # 3.0 mm

    def make_slot_panel(along: str, thick_pos: float, span_len: float, name: str) -> adsk.fusion.BRepBody:
        if along == "x":
            body = add_box_feature(
                panel_comp, B - tongue, thick_pos, B - tongue,
                span_len + 2.0 * tongue, T, BOX_HEIGHT_Z - 2.0 * B + 2.0 * tongue,
                body_name=name,
            )
            for cx0 in (B - tongue - 0.5, B + span_len + tongue - (C - B + tongue) + 0.5):
                for cz0 in (B - tongue - 0.5, BOX_HEIGHT_Z - C):
                    add_box_feature(
                        panel_comp, cx0, thick_pos - 0.5, cz0,
                        (C - B + tongue) + 0.5, T + 1.0, (C - B + tongue) + 0.5,
                        adsk.fusion.FeatureOperations.CutFeatureOperation, body,
                    )
            return body
        else:
            body = add_box_feature(
                panel_comp, thick_pos, B - tongue, B - tongue,
                T, span_len + 2.0 * tongue, BOX_HEIGHT_Z - 2.0 * B + 2.0 * tongue,
                body_name=name,
            )
            for cy0 in (B - tongue - 0.5, B + span_len + tongue - (C - B + tongue) + 0.5):
                for cz0 in (B - tongue - 0.5, BOX_HEIGHT_Z - C):
                    add_box_feature(
                        panel_comp, thick_pos - 0.5, cy0, cz0,
                        T + 1.0, (C - B + tongue) + 0.5, (C - B + tongue) + 0.5,
                        adsk.fusion.FeatureOperations.CutFeatureOperation, body,
                    )
            return body

    p_out = make_slot_panel("x", pm, INNER_DEPTH_X, "panel_side_outboard_from_icebox")
    apply_color(app, design, p_out, *COL_PANEL_PLY)

    p_in = make_slot_panel("x", BOX_WIDTH_Y - pm - T, INNER_DEPTH_X, "panel_side_inboard_from_icebox")
    apply_color(app, design, p_in, *COL_PANEL_PLY)

    # Back Panel: 2-tile H2D Printed Panel (split on 20 mm vertical half-lap at Y = 280..300 mm, 3x M4 bolts)
    end_lap_ymid = 290.0
    end_lap_w = 20.0
    p_back_out = add_box_feature(
        panel_comp, pm, B - tongue, B - tongue,
        T, (end_lap_ymid + end_lap_w / 2.0) - (B - tongue), BOX_HEIGHT_Z - 2.0 * B + 2.0 * tongue,
        body_name="print_panel_back_outboard",
    )
    for cz0 in (B - tongue - 0.5, BOX_HEIGHT_Z - C):
        add_box_feature(
            panel_comp, pm - 0.5, B - tongue - 0.5, cz0,
            T + 1.0, (C - B + tongue) + 0.5, (C - B + tongue) + 0.5,
            adsk.fusion.FeatureOperations.CutFeatureOperation, p_back_out,
        )
    # Half-lap rabbet on outboard tile: keep outer 3.0 mm (cut inner 3.0 mm across Y = 280..300 mm)
    add_box_feature(
        panel_comp, pm + T / 2.0, end_lap_ymid - end_lap_w / 2.0, B - tongue - 0.5,
        T / 2.0 + 0.5, end_lap_w + 0.5, BOX_HEIGHT_Z - 2.0 * B + 2.0 * tongue + 1.0,
        adsk.fusion.FeatureOperations.CutFeatureOperation, p_back_out,
    )
    # Ventilation slots on outboard back tile only (Y + slot_w < 270.0 mm)
    back_out_plane = create_offset_plane(panel_comp, "x", pm - 0.5)
    back_out_sketch = panel_comp.sketches.add(back_out_plane)
    bo_lines = back_out_sketch.sketchCurves.sketchLines
    slot_w, slot_h, pitch_y, pitch_z = 72.0, 22.0, 92.0, 46.0
    for r in range(4):
        sz = B + 60.0 + r * pitch_z
        if sz < B + 4.0 or sz + slot_h > BOX_HEIGHT_Z - B - 4.0:
            continue
        sy = B + 40.0 + (pitch_y / 2.0 if r % 2 == 1 else 0.0)
        while sy + slot_w < 270.0:
            bo_lines.addTwoPointRectangle(
                sketch_world_point(back_out_sketch, pm - 0.5, sy, sz),
                sketch_world_point(back_out_sketch, pm - 0.5, sy + slot_w, sz + slot_h),
            )
            sy += pitch_y
    extrude_all_profiles(panel_comp, back_out_sketch, "x", T + 1.0, adsk.fusion.FeatureOperations.CutFeatureOperation, p_back_out)
    back_lap_holes = [(pm, end_lap_ymid, zb, M4_CLEAR_DIA / 2.0) for zb in (60.0, 140.0, 220.0)]
    cut_cylinders_on_plane(panel_comp, p_back_out, "x", pm - 0.5, T + 1.0, back_lap_holes)
    apply_color(app, design, p_back_out, *COL_PRINT_ORANGE)

    p_back_in = add_box_feature(
        panel_comp, pm, end_lap_ymid - end_lap_w / 2.0, B - tongue,
        T, (B + INNER_WIDTH_Y + tongue) - (end_lap_ymid - end_lap_w / 2.0), BOX_HEIGHT_Z - 2.0 * B + 2.0 * tongue,
        body_name="print_panel_back_inboard_gx",
    )
    for cz0 in (B - tongue - 0.5, BOX_HEIGHT_Z - C):
        add_box_feature(
            panel_comp, pm - 0.5, B + INNER_WIDTH_Y + tongue - (C - B + tongue) + 0.5, cz0,
            T + 1.0, (C - B + tongue) + 0.5, (C - B + tongue) + 0.5,
            adsk.fusion.FeatureOperations.CutFeatureOperation, p_back_in,
        )
    # Half-lap rabbet on inboard tile: keep inner 3.0 mm (cut outer 3.0 mm across Y = 280..300 mm)
    add_box_feature(
        panel_comp, pm - 0.5, end_lap_ymid - end_lap_w / 2.0 - 0.5, B - tongue - 0.5,
        T / 2.0 + 0.5, end_lap_w + 0.5, BOX_HEIGHT_Z - 2.0 * B + 2.0 * tongue + 1.0,
        adsk.fusion.FeatureOperations.CutFeatureOperation, p_back_in,
    )
    # GX Touch 50 flush rectangular cutout (128 x 86 mm at Y=383.1, Z=160.0) in solid inboard tile
    add_box_feature(
        panel_comp, pm - 0.5, GX_TOUCH_YC - GX_TOUCH_CUT_W_Y / 2.0, GX_TOUCH_ZC - GX_TOUCH_CUT_H_Z / 2.0,
        T + 1.0, GX_TOUCH_CUT_W_Y, GX_TOUCH_CUT_H_Z,
        adsk.fusion.FeatureOperations.CutFeatureOperation, p_back_in,
    )
    cut_cylinders_on_plane(panel_comp, p_back_in, "x", pm - 0.5, T + 1.0, back_lap_holes)
    apply_color(app, design, p_back_in, *COL_PRINT_ORANGE)

    # Front Port Panel: 2-tile H2D Printed Panel (split on 20 mm vertical half-lap at Y = 280..300 mm, 3x M4 bolts)
    xf_inner = BOX_DEPTH_X - pm - T  # 556.0 mm
    p_front_out = add_box_feature(
        panel_comp, xf_inner, B - tongue, B - tongue,
        T, (end_lap_ymid + end_lap_w / 2.0) - (B - tongue), BOX_HEIGHT_Z - 2.0 * B + 2.0 * tongue,
        body_name="print_panel_front_outboard",
    )
    for cz0 in (B - tongue - 0.5, BOX_HEIGHT_Z - C):
        add_box_feature(
            panel_comp, xf_inner - 0.5, B - tongue - 0.5, cz0,
            T + 1.0, (C - B + tongue) + 0.5, (C - B + tongue) + 0.5,
            adsk.fusion.FeatureOperations.CutFeatureOperation, p_front_out,
        )
    # Half-lap rabbet on outboard front tile: keep outer 3.0 mm (cut inner 3.0 mm across Y = 280..300 mm)
    add_box_feature(
        panel_comp, xf_inner - 0.5, end_lap_ymid - end_lap_w / 2.0, B - tongue - 0.5,
        T / 2.0 + 0.5, end_lap_w + 0.5, BOX_HEIGHT_Z - 2.0 * B + 2.0 * tongue + 1.0,
        adsk.fusion.FeatureOperations.CutFeatureOperation, p_front_out,
    )

    p_front_in = add_box_feature(
        panel_comp, xf_inner, end_lap_ymid - end_lap_w / 2.0, B - tongue,
        T, (B + INNER_WIDTH_Y + tongue) - (end_lap_ymid - end_lap_w / 2.0), BOX_HEIGHT_Z - 2.0 * B + 2.0 * tongue,
        body_name="print_panel_front_inboard_ports",
    )
    for cz0 in (B - tongue - 0.5, BOX_HEIGHT_Z - C):
        add_box_feature(
            panel_comp, xf_inner - 0.5, B + INNER_WIDTH_Y + tongue - (C - B + tongue) + 0.5, cz0,
            T + 1.0, (C - B + tongue) + 0.5, (C - B + tongue) + 0.5,
            adsk.fusion.FeatureOperations.CutFeatureOperation, p_front_in,
        )
    # Half-lap rabbet on inboard front tile: keep inner 3.0 mm (cut outer 3.0 mm across Y = 280..300 mm)
    add_box_feature(
        panel_comp, xf_inner + T / 2.0, end_lap_ymid - end_lap_w / 2.0 - 0.5, B - tongue - 0.5,
        T / 2.0 + 0.5, end_lap_w + 0.5, BOX_HEIGHT_Z - 2.0 * B + 2.0 * tongue + 1.0,
        adsk.fusion.FeatureOperations.CutFeatureOperation, p_front_in,
    )

    for target_front, y_filter in ((p_front_out, lambda y: y < end_lap_ymid), (p_front_in, lambda y: y >= end_lap_ymid)):
        f_plane = create_offset_plane(panel_comp, "x", xf_inner - 0.5)
        f_sketch = panel_comp.sketches.add(f_plane)
        f_circles = f_sketch.sketchCurves.sketchCircles
        f_lines = f_sketch.sketchCurves.sketchLines
        for _pname, pkind, py, pz, psize, _pdepth in FRONT_PANEL_PORTS:
            if not y_filter(py):
                continue
            if pkind == "circle":
                rad = psize[0] / 2.0
                f_circles.addByCenterRadius(sketch_world_point(f_sketch, xf_inner - 0.5, py, pz), cm(rad))
            else:
                pw, ph = psize[0], psize[1]
                f_lines.addTwoPointRectangle(
                    sketch_world_point(f_sketch, xf_inner - 0.5, py - pw / 2.0, pz - ph / 2.0),
                    sketch_world_point(f_sketch, xf_inner - 0.5, py + pw / 2.0, pz + ph / 2.0),
                )
        extrude_all_profiles(panel_comp, f_sketch, "x", T + 1.0, adsk.fusion.FeatureOperations.CutFeatureOperation, target_front)

    front_lap_holes = [(xf_inner, end_lap_ymid, zb, M4_CLEAR_DIA / 2.0) for zb in (60.0, 140.0, 220.0)]
    cut_cylinders_on_plane(panel_comp, p_front_out, "x", xf_inner - 0.5, T + 1.0, front_lap_holes)
    cut_cylinders_on_plane(panel_comp, p_front_in, "x", xf_inner - 0.5, T + 1.0, front_lap_holes)
    apply_color(app, design, p_front_out, *COL_PRINT_ORANGE)
    apply_color(app, design, p_front_in, *COL_PRINT_ORANGE)

    # 4. Top Flat Lid Panel (571.5 x 488.1 x 6.0 mm, no top handles)
    lid = add_box_feature(panel_comp, 0.0, 0.0, BOX_HEIGHT_Z, BOX_DEPTH_X, BOX_WIDTH_Y, LID_THICK, body_name="lid_from_icebox_top")
    apply_color(app, design, lid, *COL_PANEL_PLY)

    # 5. 4x Printed IceBox Stack Straps (60 x 46 x 6 mm across bottom depth rail seam, 82° countersunk)
    strap_xs = (
        C + STRAP_CLEAR_CUBE_X + STRAP_W_X / 2.0,
        BOX_DEPTH_X - C - STRAP_CLEAR_CUBE_X - STRAP_W_X / 2.0,
    )
    for idx, sx in enumerate(strap_xs):
        for side_tag, y_start, y_outer, dir_in in (
            ("out", -STRAP_T_Y, -STRAP_T_Y, +1),
            ("in", BOX_WIDTH_Y, BOX_WIDTH_Y + STRAP_T_Y, -1),
        ):
            st_name = f"print_stack_strap_{side_tag}_{idx}"
            st = add_box_feature(
                comp,
                sx - STRAP_W_X / 2.0,
                y_start,
                -STRAP_H_Z / 2.0,
                STRAP_W_X,
                STRAP_T_Y,
                STRAP_H_Z,
                body_name=st_name,
            )
            fillet_parallel_edges(comp, st, "y", STRAP_FILLET_R)
            hole_list = []
            csk_centers = []
            for dx in (-STRAP_PITCH_X / 2.0, STRAP_PITCH_X / 2.0):
                hole_list.append((sx + dx, y_start, -STRAP_PITCH_Z / 2.0, UNC_25_CLEAR_DIA / 2.0))
                hole_list.append((sx + dx, y_start, +STRAP_PITCH_Z / 2.0, UNC_25_CLEAR_DIA / 2.0))
                hole_list.append((sx + dx, y_start, +STRAP_PITCH_Z / 2.0 + STRAP_SLOT_FLOAT_Z / 2.0, UNC_25_CLEAR_DIA / 2.0))
                hole_list.append((sx + dx, y_start, +STRAP_PITCH_Z / 2.0 - STRAP_SLOT_FLOAT_Z / 2.0, UNC_25_CLEAR_DIA / 2.0))
                csk_centers.append((sx + dx, y_outer, -STRAP_PITCH_Z / 2.0))
                csk_centers.append((sx + dx, y_outer, +STRAP_PITCH_Z / 2.0 - STRAP_SLOT_FLOAT_Z / 2.0))
                csk_centers.append((sx + dx, y_outer, +STRAP_PITCH_Z / 2.0))
                csk_centers.append((sx + dx, y_outer, +STRAP_PITCH_Z / 2.0 + STRAP_SLOT_FLOAT_Z / 2.0))
            cut_cylinders_on_plane(comp, st, "y", y_start - 0.5, STRAP_T_Y + 1.0, hole_list)
            cut_countersink_14_20(comp, st, "y", y_outer, dir_in, csk_centers, with_floor_head_relief=False)
            apply_color(app, design, st, *COL_PRINT_ORANGE)

    return comp


def build_battery_zone_outboard(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    root: adsk.fusion.Component,
) -> adsk.fusion.Component:
    """02_Battery_Zone_Outboard: 2 Single-Print Battery Trays, 2 Breaker Drop Shelves (with 4 AWG wire channels) & EPDM Pads."""
    comp = create_subcomponent(root, "02_Battery_Zone_Outboard")
    fd, fw, fl, lip = TRAY_OUTER_LEN_X, TRAY_OUTER_WID_Y, TRAY_FLOOR_THICK, TRAY_LIP_H
    wall, pw = TRAY_WALL_THICK, TRAY_POCKET_WID_Y
    tray_xs = (TRAY_0_X0, TRAY_1_X0)

    for r in range(2):
        tx = tray_xs[r]
        ty = TRAY_Y0
        t_name = f"print_tray_battery_{r}"

        # 1. Base tray block (242 x 167 x 36 mm)
        tray = add_box_feature(comp, tx, ty, 0.0, fd, fw, fl + lip, body_name=t_name)

        # 2. Pocket cutout (230 x 139 x 30 mm from Z = 6.0 to 36.0 mm)
        add_box_feature(
            comp, tx + wall, ty + wall, fl,
            TRAY_POCKET_LEN_X, pw, lip + 1.0,
            adsk.fusion.FeatureOperations.CutFeatureOperation, tray,
        )

        # 3. 2.5 x 2.5 mm outer-end corner notch clearing the 25.75 mm corner cube
        notch_x = tx - 0.5 if r == 0 else tx + fd - TRAY_CUBE_NOTCH + 0.5
        add_box_feature(
            comp, notch_x, ty - 0.5, -0.5,
            TRAY_CUBE_NOTCH, TRAY_CUBE_NOTCH, fl + lip + 1.0,
            adsk.fusion.FeatureOperations.CutFeatureOperation, tray,
        )

        # 4. Outboard wall: 2x 1/4"-20 countersunk rail holes + floor head_relief pockets (Z = 12.5 mm)
        out_bolts = [(tx + sx, ty + wall, RAIL_PROFILE / 2.0) for sx in TRAY_OUTBOARD_BOLT_DX]
        cut_countersink_14_20(comp, tray, "y", ty + wall, -1.0, out_bolts, wall, with_floor_head_relief=True)

        # 5. End wall on width rail: 2x 1/4"-20 countersunk rail holes + floor head_relief pockets (Z = 12.5 mm)
        xw_inner = tx + wall if r == 0 else tx + fd - wall
        inward_dir = -1.0 if r == 0 else 1.0
        end_bolts = [(xw_inner, ty + sy, RAIL_PROFILE / 2.0) for sy in TRAY_END_BOLT_DY]
        cut_countersink_14_20(comp, tray, "x", xw_inner, inward_dir, end_bolts, wall, with_floor_head_relief=True)

        # 6. Inboard wall column face (+Y): 3x M4 heat-set insert bores (Ø5.6 x 8 mm at Z = 17.0 mm)
        m4_side_bores = [
            (tx + hx, ty + fw, 17.0, M4_INSERT_BORE_DIA / 2.0) for hx in TRAY_LIP_M4_DX[r]
        ]
        cut_cylinders_on_plane(comp, tray, "y", ty + fw + 0.5, -8.5, m4_side_bores)

        # 7. Inboard 21 mm wall top (+Z): 2x M4 heat-set insert bores (Ø5.6 x 12 mm) for Breaker Drop Shelf feet
        xs_shelf = tx + wall + TRAY_CLEARANCE + (BATT_L - DROP_SHELF_LEN_X) / 2.0
        m4_top_bores = [
            (xs_shelf + hx, DROP_SHELF_LEG_Y0 + 13.0, fl + lip, M4_INSERT_BORE_DIA / 2.0)
            for hx in DROP_SHELF_BOLT_DX
        ]
        cut_cylinders_on_plane(comp, tray, "z", fl + lip + 0.5, -12.5, m4_top_bores)
        apply_color(app, design, tray, *COL_PRINT_ORANGE)

        # --- Breaker Drop Shelf (Hold-Down + Bussmann 285 Mount + 13.5 mm 4 AWG Wire Channel) ---
        s_name = f"print_breaker_shelf_{r}"
        xs = xs_shelf
        zs = DROP_SHELF_Z0  # 215.0 mm
        yw = DROP_SHELF_LEG_Y0  # 172.0 mm
        wt = fl + lip  # 36.0 mm
        hb = DROP_SHELF_HANGER_BAND_Y  # 13.0 mm
        rel = DROP_SHELF_WIRE_RELIEF_Y  # 7.5 mm (Y = 32.5 mm, flush with battery)
        yf_hanger = INNER_Y0 + hb  # 38.0 mm

        # Deck plate (Y = 32.5..178, Z = 215..226)
        shelf_body = add_box_feature(
            comp, xs, INNER_Y0 + rel, zs,
            DROP_SHELF_LEN_X, (yw + DROP_SHELF_LEG_THICK) - (INNER_Y0 + rel), M5_DECK_THICK,
            body_name=s_name,
        )
        # Lower hanger with 7.5 mm back relief (flush with battery) for 17.0 mm 4 AWG wire channel (Y = 32.5..38, Z = 215..256.7)
        add_box_feature(
            comp, xs, INNER_Y0 + rel, zs,
            DROP_SHELF_LEN_X, yf_hanger - (INNER_Y0 + rel), (BOX_HEIGHT_Z - RAIL_PROFILE) - zs,
            adsk.fusion.FeatureOperations.JoinFeatureOperation, shelf_body,
        )
        # Upper 13 mm hanger band bearing on top outboard rail (Y = 25..38, Z = 256.7..278.7)
        add_box_feature(
            comp, xs, INNER_Y0, BOX_HEIGHT_Z - RAIL_PROFILE,
            DROP_SHELF_LEN_X, hb, (BOX_HEIGHT_Z - 3.0) - (BOX_HEIGHT_Z - RAIL_PROFILE),
            adsk.fusion.FeatureOperations.JoinFeatureOperation, shelf_body,
        )
        # Inboard vertical leg down to tray wall top + 13 mm lip above deck (Y = 172..178, Z = 36..239)
        add_box_feature(
            comp, xs, yw, wt,
            DROP_SHELF_LEN_X, DROP_SHELF_LEG_THICK, (zs + 24.0) - wt,
            adsk.fusion.FeatureOperations.JoinFeatureOperation, shelf_body,
        )
        # Inboard horizontal foot over 21 mm tray wall (Y = 178..193, Z = 36..42)
        add_box_feature(
            comp, xs, yw + DROP_SHELF_LEG_THICK, wt,
            DROP_SHELF_LEN_X, DROP_SHELF_FOOT_WID, 6.0,
            adsk.fusion.FeatureOperations.JoinFeatureOperation, shelf_body,
        )
        # 18 mm & 5 mm triangular stiffening ribs along hanger front face and inboard lip
        rib_plane = create_offset_plane(comp, "x", xs)
        rib_sketch = comp.sketches.add(rib_plane)
        rib_lines = rib_sketch.sketchCurves.sketchLines
        p_r1 = sketch_world_point(rib_sketch, xs, yf_hanger, zs + M5_DECK_THICK)
        p_r2 = sketch_world_point(rib_sketch, xs, yf_hanger + 18.0, zs + M5_DECK_THICK)
        p_r3 = sketch_world_point(rib_sketch, xs, yf_hanger, zs + M5_DECK_THICK + 18.0)
        rib_lines.addByTwoPoints(p_r1, p_r2)
        rib_lines.addByTwoPoints(p_r2, p_r3)
        rib_lines.addByTwoPoints(p_r3, p_r1)
        p_l1 = sketch_world_point(rib_sketch, xs, yw, zs + M5_DECK_THICK)
        p_l2 = sketch_world_point(rib_sketch, xs, yw - 5.0, zs + M5_DECK_THICK)
        p_l3 = sketch_world_point(rib_sketch, xs, yw, zs + M5_DECK_THICK + 5.0)
        rib_lines.addByTwoPoints(p_l1, p_l2)
        rib_lines.addByTwoPoints(p_l2, p_l3)
        rib_lines.addByTwoPoints(p_l3, p_l1)
        extrude_all_profiles(
            comp, rib_sketch, "x", DROP_SHELF_LEN_X,
            adsk.fusion.FeatureOperations.JoinFeatureOperation, shelf_body,
        )

        # 2x 1/4"-20 countersunk hanger bolts into top outboard rail (Z = 269.2 mm)
        hz_top = BOX_HEIGHT_Z - RAIL_PROFILE / 2.0
        hanger_bolts = [(xs + hx, yf_hanger, hz_top) for hx in DROP_SHELF_BOLT_DX]
        cut_countersink_14_20(comp, shelf_body, "y", yf_hanger, -1.0, hanger_bolts, hb)

        # 2x M4 foot clearance holes (Ø4.6 mm) down into tray wall inserts
        foot_holes = [(xs + hx, yw + 13.0, wt + 6.0, M4_CLEAR_DIA / 2.0) for hx in DROP_SHELF_BOLT_DX]
        cut_cylinders_on_plane(comp, shelf_body, "z", wt + 6.5, -8.0, foot_holes)

        # 2x Blind M5 tapered bores (Ø7.5 x 9.5 mm) for Eaton Bussmann 285 breaker
        bx, by = xs + 24.0, INNER_Y0 + 92.0
        brk_holes = [(bx + u, by + v) for (u, v) in COMP_SPECS["breaker_285"]["holes_xy"]]
        cut_blind_m5_tapered_bores(comp, shelf_body, zs + M5_DECK_THICK, brk_holes)
        apply_color(app, design, shelf_body, *COL_PRINT_ORANGE)

        # Closed-cell EPDM Foam Hold-Down Pad (130 x 139 x 1 mm compressed between battery top and shelf)
        pad_h = DROP_SHELF_PAD_THICK - DROP_SHELF_DROP  # 1.0 mm
        pad_body = add_box_feature(
            comp, xs, ty + wall, fl + BATT_BODY_H,
            DROP_SHELF_LEN_X, pw, pad_h,
            body_name=f"pad_breaker_shelf_{r}",
        )
        apply_color(app, design, pad_body, *COL_FOAM_EPDM)

    return comp


def build_center_bus_column(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    root: adsk.fusion.Component,
) -> tuple[adsk.fusion.Component, list[tuple[float, float]]]:
    """03_Center_Bus_Column: 3 Wall-Half-Lapped Bus Shelf Plates, Blind M5 Bus/Shunt Bores & 57 mm Wire Trough."""
    comp = create_subcomponent(root, "03_Center_Bus_Column")
    y0s, y1s = BUS_SHELF_Y0, BUS_SHELF_Y1  # 193.0 .. 303.0 mm
    xs0, xs1 = INNER_X0, INNER_X1          # 25.0 .. 546.5 mm
    E = BUS_SHELF_END_LEN                  # 194.733 mm
    bounds = [(xs0, xs0 + E), (xs0 + E, xs1 - E), (xs1 - E, xs1)]
    tray_xs = (TRAY_0_X0, TRAY_1_X0)
    cw = BUS_SHELF_IN_WALL_T               # 4.0 mm
    lap = BUS_SHELF_LAP_LEN                # 20.0 mm

    all_m5_floor_xy: list[tuple[float, float]] = []
    for x0_bar in (BUSBAR_POS_X0, BUSBAR_NEG_X0):
        for hu, hv in COMP_SPECS["busbar_5stud"]["holes_xy"]:
            all_m5_floor_xy.append((x0_bar + hu, BUSBAR_Y0 + hv))
    for hu, hv in COMP_SPECS["shunt_500a"]["holes_xy"]:
        all_m5_floor_xy.append((SMARTSHUNT_X0 + hu, SMARTSHUNT_Y0 + hv))

    sill_holes_xz: list[tuple[float, float]] = []

    for i in range(3):
        xa, xb = bounds[i]
        p_len = xb - xa
        b_name = f"print_bus_shelf_{i}"

        # 1. Base 11.0 mm floor + 6.0 mm outboard lip (Z=0..34) + 4.0 mm inboard sill wall (Z=0..34)
        sh = add_box_feature(comp, xa, y0s, 0.0, p_len, y1s - y0s, M5_DECK_THICK, body_name=b_name)
        add_box_feature(
            comp, xa, y0s, M5_DECK_THICK, p_len, BUS_SHELF_OUT_LIP_T, BUS_SHELF_WALL_H - M5_DECK_THICK,
            adsk.fusion.FeatureOperations.JoinFeatureOperation, sh,
        )
        add_box_feature(
            comp, xa, y1s - cw, M5_DECK_THICK, p_len, cw, BUS_SHELF_WALL_H - M5_DECK_THICK,
            adsk.fusion.FeatureOperations.JoinFeatureOperation, sh,
        )

        # 2. End walls on Plates 0 and 2 (6.0 mm thick, Z = 0..30 mm, notched around inverter posts)
        if i in (0, 2):
            xw0 = xa if i == 0 else xb - 6.0
            add_box_feature(
                comp, xw0, y0s, M5_DECK_THICK, 6.0, (y1s - 11.0) - y0s, BUS_SHELF_END_WALL_H - M5_DECK_THICK,
                adsk.fusion.FeatureOperations.JoinFeatureOperation, sh,
            )
            notch_x0 = INNER_X0 - 1.0 if i == 0 else INNER_X1 - POST_D_X - 2.0
            add_box_feature(
                comp, notch_x0, y1s - 10.0, -0.5, POST_D_X + 3.0, 12.0, BUS_SHELF_WALL_H + 1.0,
                adsk.fusion.FeatureOperations.CutFeatureOperation, sh,
            )
            face_x = xw0 + 6.0 if i == 0 else xw0
            in_sign = -1.0 if i == 0 else 1.0
            rail_pts = [(face_x, yc, RAIL_PROFILE / 2.0) for yc in BUS_SHELF_RAIL_BOLT_Y]
            cut_countersink_14_20(comp, sh, "x", face_x, in_sign, rail_pts, 6.0, with_floor_head_relief=True)

        # 3. 20.0 mm vertical wall half-laps
        for yt, tw, out_dir in ((y0s, 3.0, -1), (y1s - cw / 2.0, cw / 2.0, +1)):
            if i < 2:
                add_box_feature(
                    comp, xb, yt, 0.0, lap, tw, BUS_SHELF_WALL_H,
                    adsk.fusion.FeatureOperations.JoinFeatureOperation, sh,
                )
            if i > 0:
                add_box_feature(
                    comp, xa - 0.5, yt - (0.5 if out_dir < 0 else 0.3), -0.5,
                    lap + 0.5, tw + 0.8, BUS_SHELF_WALL_H + 1.0,
                    adsk.fusion.FeatureOperations.CutFeatureOperation, sh,
                )

        # 4. Outboard lip M4 clearance holes (Ø4.6 mm at Z = 17.0 mm into battery tray M4 inserts)
        lip_holes = []
        for r in range(2):
            for hx in TRAY_LIP_M4_DX[r]:
                hxa = tray_xs[r] + hx
                if xa + 6.0 < hxa < xb - 6.0:
                    lip_holes.append((hxa, y0s, 17.0, M4_CLEAR_DIA / 2.0))
        cut_cylinders_on_plane(comp, sh, "y", y0s - 0.5, BUS_SHELF_OUT_LIP_T + 1.0, lip_holes)

        # 5. Inboard sill wall M4 clearance holes (2 per plate at Z = 28.0 mm into inverter plate bottom band)
        sill_pts = []
        for sx in (xa + 40.0, xb - 40.0):
            sill_pts.append((sx, y1s - cw, 28.0, M4_CLEAR_DIA / 2.0))
            sill_holes_xz.append((sx, 28.0))
        cut_cylinders_on_plane(comp, sh, "y", y1s - cw - 0.5, cw + 1.0, sill_pts)

        # 6. Blind M5 tapered heat-set insert bores in the 11 mm floor
        plate_m5 = [(mx, my) for (mx, my) in all_m5_floor_xy if xa + 6.0 < mx < xb - 6.0]
        cut_blind_m5_tapered_bores(comp, sh, M5_DECK_THICK, plate_m5)
        apply_color(app, design, sh, *COL_PRINT_ORANGE)

    return comp, sill_holes_xz


def build_inverter_plate_assembly(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    root: adsk.fusion.Component,
    sill_holes_xz: list[tuple[float, float]],
) -> adsk.fusion.Component:
    """04_Inverter_Plate_Assembly: 2 Slotted Posts, 2 Top Clips, H2D (2-tile) or P1P (6-tile) Plate, Splines & 70x70 Cable Window."""
    comp = create_subcomponent(root, f"04_Inverter_Plate_{PRINTER_PRESET}")
    yp = INVERTER_PLATE_Y0      # 303.0 mm
    pt = INVERTER_PLATE_THICK   # 6.0 mm
    px0, px1 = INVERTER_PLATE_X0, INVERTER_PLATE_X1  # 33.0 .. 538.5 mm (L = 505.5 mm)
    zp, hp = INVERTER_PLATE_Z0, INVERTER_PLATE_H     # 21.0 .. 277.0 mm (H = 256.0 mm)

    # 1. 2x One-Piece Full-Height Slotted Inverter Posts (Z = 0 .. 278.7 mm, continuous open-top slot + integral top rail ear)
    post_y0 = yp + pt / 2.0 - POST_W_Y / 2.0  # 294.0 mm (spans Y = 294.0 .. 318.0 mm)
    post_y1 = post_y0 + POST_W_Y              # 318.0 mm
    slot_w_y = pt + 2.0 * INVERTER_PLATE_CLEAR  # 7.2 mm
    slot_y0 = post_y0 + (POST_W_Y - slot_w_y) / 2.0

    for j, xpost in enumerate((INNER_X0, INNER_X1 - POST_D_X)):
        p_name = f"print_post_inverter_{j}"
        post = add_box_feature(comp, xpost, post_y0, 0.0, POST_D_X, POST_W_Y, POST_H_Z, body_name=p_name)

        # Integral 12 mm top rail mounting ear on inboard (+Y) side (Y = 318..330, Z = 254..278.7 mm)
        add_box_feature(
            comp, xpost, post_y1, 254.0,
            POST_D_X, 12.0, POST_H_Z - 254.0,
            adsk.fusion.FeatureOperations.JoinFeatureOperation, post,
        )
        # 12 mm triangular gusset under top ear (Y = 318..330, Z = 242..254 mm)
        g_plane = create_offset_plane(comp, "x", xpost)
        g_sketch = comp.sketches.add(g_plane)
        g_lines = g_sketch.sketchCurves.sketchLines
        gp1 = sketch_world_point(g_sketch, xpost, post_y1, 242.0)
        gp2 = sketch_world_point(g_sketch, xpost, post_y1 + 12.0, 254.0)
        gp3 = sketch_world_point(g_sketch, xpost, post_y1, 254.0)
        g_lines.addByTwoPoints(gp1, gp2)
        g_lines.addByTwoPoints(gp2, gp3)
        g_lines.addByTwoPoints(gp3, gp1)
        extrude_all_profiles(
            comp, g_sketch, "x", POST_D_X,
            adsk.fusion.FeatureOperations.JoinFeatureOperation, post,
        )

        # Continuous open-top plate slot (Z = 30.0 .. 278.7 mm)
        slot_x0 = (xpost + POST_D_X - POST_SLOT_DEPTH_X) if j == 0 else (xpost - 0.5)
        add_box_feature(
            comp, slot_x0, slot_y0, POST_SLOT_Z0,
            POST_SLOT_DEPTH_X + 0.5, slot_w_y, POST_H_Z - POST_SLOT_Z0 + 1.0,
            adsk.fusion.FeatureOperations.CutFeatureOperation, post,
        )

        # Bottom sill (Z = 12.5 mm, Y = 306.0 mm) & Top ear (Z = 269.2 mm, Y = 320.0 mm) 82-deg countersunk 1/4"-20 rail holes
        p_face_x = (xpost + POST_D_X) if j == 0 else xpost
        p_in_sign = -1.0 if j == 0 else 1.0
        cut_countersink_14_20(
            comp, post, "x", p_face_x, p_in_sign,
            [
                (p_face_x, post_y0 + POST_W_Y / 2.0, RAIL_PROFILE / 2.0),
                (p_face_x, post_y1 + 2.0, BOX_HEIGHT_Z - RAIL_PROFILE / 2.0),
            ],
            POST_D_X,
            with_floor_head_relief=False,
        )
        apply_color(app, design, post, *COL_PRINT_ORANGE)

    # 2. Collect all 22 Pre-Printed Heat-Set Insert Bores on the Inverter Plate
    plate_bores: list[tuple[float, float, float, int]] = []
    for sx, sz in sill_holes_xz:
        plate_bores.append((sx, sz, M4_INSERT_BORE_DIA / 2.0, -1))
    for ckey in ("multiplus_1200_long", "mppt_up", "cerbo", "orion"):
        spec = COMP_SPECS[ckey]
        cx0, _cy0, cz0 = spec["pos"]
        rad = (M5_INSERT_BORE_DIA if spec["insert"] == "M5" else M4_INSERT_BORE_DIA) / 2.0
        f_side = spec["face_side"]
        for du, dv in spec["holes_xz"]:
            plate_bores.append((cx0 + du, cz0 + dv, rad, f_side))

    # 3. Build Inverter Plate Tiles & Splines (2 tiles for Bambu H2D, 6 tiles for Bambu P1P)
    L = px1 - px0  # 505.5 mm
    H = hp         # 256.0 mm
    nx = int(-(-L // TILE_MAX_MM))  # 2 on H2D (340 mm), 3 on P1P (250 mm)
    nz = int(-(-H // TILE_MAX_MM))  # 1 on H2D (340 mm), 2 on P1P (250 mm)
    tw, th = L / nx, H / nz
    lap = PLATE_LAP_WIDTH           # 24.0 mm
    sl, st, sw = SPLINE_DIM         # (60.0, 3.0, 18.0)

    spline_boxes: list[tuple[str, float, float, float]] = []
    for i in range(1, nx):
        for j in range(nz):
            yf_sp = (yp + pt - st) if j % 2 == 0 else yp
            for z_frac in (0.3, 0.7):
                zc = zp + j * th + th * z_frac
                sp_name = f"print_plate_inverter_spline_v{i}_{int(zc)}"
                spline_boxes.append((sp_name, px0 + i * tw - sl / 2.0, yf_sp, zc - sw / 2.0))

    for i in range(nx):
        for j in range(nz):
            tx0 = px0 + i * tw
            tz_lo = zp if j == 0 else (zp + j * th - lap / 2.0)
            tz_hi = (zp + H) if j == nz - 1 else (zp + (j + 1) * th + lap / 2.0)
            t_name = f"print_plate_inverter_tile_{i}{j}"

            tile = add_box_feature(comp, tx0, yp, tz_lo, tw, pt, tz_hi - tz_lo, body_name=t_name)

            cy_cut = (yp + pt / 2.0) if j % 2 == 0 else (yp - 0.5)
            cd_cut = pt / 2.0 + 0.5
            if j < nz - 1:
                add_box_feature(
                    comp, tx0 - 0.5, cy_cut, zp + (j + 1) * th - lap / 2.0,
                    tw + 1.0, cd_cut, lap + 0.5,
                    adsk.fusion.FeatureOperations.CutFeatureOperation, tile,
                )
            if j > 0:
                add_box_feature(
                    comp, tx0 - 0.5, cy_cut, zp + j * th - lap / 2.0 - 0.5,
                    tw + 1.0, cd_cut, lap + 0.5,
                    adsk.fusion.FeatureOperations.CutFeatureOperation, tile,
                )

            for _sp_nm, spx, spy, spz in spline_boxes:
                if spx + sl > tx0 and spx < tx0 + tw and spz + sw > tz_lo and spz < tz_hi:
                    back_side = spy > yp + 0.1
                    add_box_feature(
                        comp, spx - 0.2, spy if back_side else spy - 0.5, spz - 0.2,
                        sl + 0.4, st + 0.5, sw + 0.4,
                        adsk.fusion.FeatureOperations.CutFeatureOperation, tile,
                    )

            if i == 0 and j == 0:
                add_box_feature(
                    comp, px0 - 0.5, yp - 0.5, zp - 0.5, 12.5, pt + 1.0, POST_SLOT_Z0 - zp + 0.5,
                    adsk.fusion.FeatureOperations.CutFeatureOperation, tile,
                )
            if i == nx - 1 and j == 0:
                add_box_feature(
                    comp, px1 - 12.0, yp - 0.5, zp - 0.5, 12.5, pt + 1.0, POST_SLOT_Z0 - zp + 0.5,
                    adsk.fusion.FeatureOperations.CutFeatureOperation, tile,
                )

            # 70 x 70 mm Filleted Cable Pass-Through Window (X = 426.5..496.5, Z = 40..110 mm)
            if CABLE_WINDOW_X1 > tx0 and CABLE_WINDOW_X0 < tx0 + tw and CABLE_WINDOW_Z1 > tz_lo and CABLE_WINDOW_Z0 < tz_hi:
                add_box_feature(
                    comp, CABLE_WINDOW_X0, yp - 0.5, CABLE_WINDOW_Z0,
                    CABLE_WINDOW_X1 - CABLE_WINDOW_X0, pt + 1.0, CABLE_WINDOW_Z1 - CABLE_WINDOW_Z0,
                    adsk.fusion.FeatureOperations.CutFeatureOperation, tile,
                )
                fillet_parallel_edges(
                    comp, tile, "y", WINDOW_FILLET_R,
                    (CABLE_WINDOW_X0 - 1.0, CABLE_WINDOW_X1 + 1.0, yp - 1.0, yp + pt + 1.0, CABLE_WINDOW_Z0 - 1.0, CABLE_WINDOW_Z1 + 1.0),
                )

            through_bores = []
            far_rel_neg = []
            far_rel_pos = []
            for bx, bz, brad, fside in plate_bores:
                if tx0 <= bx <= tx0 + tw and tz_lo <= bz <= tz_hi:
                    through_bores.append((bx, yp, bz, brad))
                    if brad > 3.5:
                        if fside > 0:
                            far_rel_neg.append((bx, yp, bz, M5_FAR_RELIEF_DIA / 2.0))
                        else:
                            far_rel_pos.append((bx, yp + pt, bz, M5_FAR_RELIEF_DIA / 2.0))
            cut_cylinders_on_plane(comp, tile, "y", yp - 0.5, pt + 1.0, through_bores)
            cut_cylinders_on_plane(comp, tile, "y", yp - 0.2, M5_FAR_RELIEF_DEPTH + 0.2, far_rel_neg)
            cut_cylinders_on_plane(comp, tile, "y", yp + pt + 0.2, -(M5_FAR_RELIEF_DEPTH + 0.2), far_rel_pos)

            apply_color(app, design, tile, *COL_PLATE_DARK)

    for sp_name, spx, spy, spz in spline_boxes:
        sp_body = add_box_feature(comp, spx, spy, spz, sl, st, sw, body_name=sp_name)
        apply_color(app, design, sp_body, *COL_PRINT_ORANGE)

    return comp


def build_inboard_garmin_lane(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    root: adsk.fusion.Component,
) -> adsk.fusion.Component:
    """05_Inboard_Garmin_Lane: Upper & Lower Garmin Hanger Plates with 5 Rows of Paired Wire-Management Tie Slots & GX Touch Bezel."""
    comp = create_subcomponent(root, "05_Inboard_Garmin_Lane")
    gw, gt = GARMIN_HANGER_LEN_X, GARMIN_HANGER_THICK_Y
    gx0, gy = GARMIN_HANGER_X0, GARMIN_HANGER_Y0

    def cut_zip_tie_slot_rows(target_body: adsk.fusion.BRepBody, z_rows: tuple[float, ...]) -> None:
        plane = create_offset_plane(comp, "y", gy - 0.5)
        sketch = comp.sketches.add(plane)
        lines = sketch.sketchCurves.sketchLines
        for zrow in z_rows:
            for dcx in TIE_SLOT_CENTERS_DX:
                sx = gx0 + dcx
                for dx_pair in (-TIE_SLOT_PAIR_SPAN_X / 2.0, +TIE_SLOT_PAIR_SPAN_X / 2.0):
                    x_slot = sx + dx_pair - TIE_SLOT_W_X / 2.0
                    z_slot = zrow - TIE_SLOT_H_Z / 2.0
                    lines.addTwoPointRectangle(
                        sketch_world_point(sketch, x_slot, gy - 0.5, z_slot),
                        sketch_world_point(sketch, x_slot + TIE_SLOT_W_X, gy - 0.5, z_slot + TIE_SLOT_H_Z),
                    )
        extrude_all_profiles(comp, sketch, "y", gt + 1.0, adsk.fusion.FeatureOperations.CutFeatureOperation, target_body)

    # 1. Upper Garmin Hanger Plate (Z = 130.0 .. 278.7 mm)
    u_hanger = add_box_feature(
        comp, gx0, gy, GARMIN_UPPER_Z0, gw, gt, GARMIN_UPPER_Z1 - GARMIN_UPPER_Z0,
        body_name="print_garmin_hanger",
    )
    hz_top = BOX_HEIGHT_Z - RAIL_PROFILE / 2.0
    u_rail_bolts = [(gx0 + dx, gy, hz_top) for dx in GARMIN_RAIL_BOLT_DX]
    cut_countersink_14_20(comp, u_hanger, "y", gy, +1.0, u_rail_bolts, gt)

    g_spec = COMP_SPECS["garmin_ps"]
    gx_unit, _gy_unit, gz_unit = g_spec["pos"]
    g_m4_bores = [
        (gx_unit + u, gy, gz_unit + v, M4_INSERT_BORE_DIA / 2.0) for (u, v) in g_spec["holes_xz"]
    ]
    cut_cylinders_on_plane(comp, u_hanger, "y", gy - 0.5, gt + 1.0, g_m4_bores)
    cut_zip_tie_slot_rows(u_hanger, TIE_SLOT_ROWS_UPPER_Z)
    apply_color(app, design, u_hanger, *COL_PRINT_ORANGE)

    # 2. Lower Garmin Wire-Management & Blue Sea 2701 Hanger Plate (Z = 2.0 .. 129.0 mm)
    l_hanger = add_box_feature(
        comp, gx0, gy, GARMIN_LOWER_Z0, gw, gt, GARMIN_LOWER_Z1 - GARMIN_LOWER_Z0,
        body_name="print_garmin_hanger_lower",
    )
    l_rail_bolts = [(gx0 + dx, gy, RAIL_PROFILE / 2.0) for dx in GARMIN_RAIL_BOLT_DX]
    cut_countersink_14_20(comp, l_hanger, "y", gy, +1.0, l_rail_bolts, gt)
    gb_spec = COMP_SPECS["gnd_bus_2701"]
    gb_x0, _gb_y0, gb_z0 = gb_spec["pos"]
    gb_m4_bores = [
        (gb_x0 + u, gy, gb_z0 + v, M4_INSERT_BORE_DIA / 2.0) for (u, v) in gb_spec["holes_xz"]
    ]
    cut_cylinders_on_plane(comp, l_hanger, "y", gy - 0.5, gt + 1.0, gb_m4_bores)
    cut_zip_tie_slot_rows(l_hanger, TIE_SLOT_ROWS_LOWER_Z)
    apply_color(app, design, l_hanger, *COL_PRINT_ORANGE)

    return comp


def build_electrical_components(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    root: adsk.fusion.Component,
) -> adsk.fusion.Component:
    """06_Electrical_Components: Real Victron STEP Models & Detailed Eaton Bussmann 285 Breakers (with parametric fallback)."""
    comp = create_subcomponent(root, "06_Electrical_Components")
    tray_xs = (TRAY_0_X0, TRAY_1_X0)

    # 1. 2x Victron SuperPack 12.8V/60Ah Batteries (Real Victron STEP or parametric fallback)
    for r in range(2):
        bx0 = tray_xs[r] + TRAY_WALL_THICK + TRAY_CLEARANCE
        by0 = TRAY_Y0 + TRAY_WALL_THICK + TRAY_CLEARANCE
        bz0 = TRAY_FLOOR_THICK
        b_name = f"victron_superpack_60ah_{r}"
        if not import_positioned_step(app, design, comp, f"{b_name}.step", b_name, COL_BATT_BLUE):
            batt = add_box_feature(
                comp, bx0, by0, bz0, BATT_L, BATT_W, BATT_BODY_H,
                body_name=b_name,
            )
            fillet_parallel_edges(comp, batt, "z", BATT_FILLET_R)
            term_plane = create_offset_plane(comp, "z", bz0 + BATT_BODY_H)
            term_sketch = comp.sketches.add(term_plane)
            for tx_off in (28.0, BATT_L - 28.0):
                term_sketch.sketchCurves.sketchCircles.addByCenterRadius(
                    sketch_world_point(term_sketch, bx0 + tx_off, by0 + BATT_W / 2.0, bz0 + BATT_BODY_H), cm(6.0)
                )
            extrude_all_profiles(
                comp, term_sketch, "z", BATT_TOTAL_H - BATT_BODY_H,
                adsk.fusion.FeatureOperations.JoinFeatureOperation, batt,
            )
            apply_color(app, design, batt, *COL_BATT_BLUE)

        # 2. 2x Eaton Bussmann 285-Series 150A Breakers on Drop Shelves (Exact series drawing geometry)
        xs_shelf = bx0 + (BATT_L - DROP_SHELF_LEN_X) / 2.0
        br_x = xs_shelf + 24.0
        br_y = INNER_Y0 + 92.0
        br_z = DROP_SHELF_Z0 + M5_DECK_THICK  # 226.0 mm
        b_dx, b_dy, b_dz = COMP_SPECS["breaker_285"]["dims"]
        build_bussmann_285_breaker(app, design, comp, br_x, br_y, br_z, b_dx, b_dy, b_dz, r)

    # 3. 2x Covered 5-Stud M8 Bus Bars (+ Red and - Black) & Real Victron SmartShunt 500A STEP
    bb_dx, bb_dy, bb_dz = COMP_SPECS["busbar_5stud"]["dims"]
    bus_pos = add_box_feature(
        comp, BUSBAR_POS_X0, BUSBAR_Y0, M5_DECK_THICK, bb_dx, bb_dy, bb_dz,
        body_name="power_busbar_5stud_pos",
    )
    fillet_parallel_edges(comp, bus_pos, "z", COMP_FILLET_R)
    apply_color(app, design, bus_pos, *COL_POWER_GOLD)

    bus_neg = add_box_feature(
        comp, BUSBAR_NEG_X0, BUSBAR_Y0, M5_DECK_THICK, bb_dx, bb_dy, bb_dz,
        body_name="power_busbar_5stud_neg",
    )
    fillet_parallel_edges(comp, bus_neg, "z", COMP_FILLET_R)
    apply_color(app, design, bus_neg, *COL_POWER_GOLD)

    if not import_positioned_step(
        app, design, comp, "victron_smartshunt_500a.step", "victron_smartshunt_500a", COL_POWER_GOLD
    ):
        sh_dx, sh_dy, sh_dz = COMP_SPECS["shunt_500a"]["dims"]
        shunt = add_box_feature(
            comp, SMARTSHUNT_X0, SMARTSHUNT_Y0, M5_DECK_THICK, sh_dx, sh_dy, sh_dz,
            body_name="victron_smartshunt_500a",
        )
        sh_plane = create_offset_plane(comp, "z", M5_DECK_THICK + sh_dz)
        sh_sketch = comp.sketches.add(sh_plane)
        for sx_stud in (32.5, 87.5):
            sh_sketch.sketchCurves.sketchCircles.addByCenterRadius(
                sketch_world_point(sh_sketch, SMARTSHUNT_X0 + sx_stud, SMARTSHUNT_Y0 + 12.5, M5_DECK_THICK + sh_dz),
                cm(5.0),
            )
        extrude_all_profiles(
            comp, sh_sketch, "z", 11.5, adsk.fusion.FeatureOperations.JoinFeatureOperation, shunt
        )
        apply_color(app, design, shunt, *COL_POWER_GOLD)

    # 4. Inverter Plate Units: Real Victron STEP Models (MultiPlus, SmartSolar MPPT 100/30, Cerbo GX & Orion XS 50A)
    for key, label, step_fn in (
        ("multiplus_1200_long", "victron_multiplus_12_800_1200", "victron_multiplus_12_1200.step"),
        ("mppt_up", "victron_smartsolar_mppt_100_30", "victron_smartsolar_mppt_100_30.step"),
        ("cerbo", "victron_cerbo_gx", "victron_cerbo_gx.step"),
        ("orion", "victron_orion_xs_12_12_50a", "victron_orion_xs_50a.step"),
    ):
        if not import_positioned_step(app, design, comp, step_fn, label, COL_VICTRON_BLUE):
            spec = COMP_SPECS[key]
            dx, dy, dz = spec["dims"]
            px, py, pz = spec["pos"]
            ubody = add_box_feature(comp, px, py, pz, dx, dy, dz, body_name=label)
            fillet_parallel_edges(comp, ubody, "y", COMP_FILLET_R)
            apply_color(app, design, ubody, *COL_VICTRON_BLUE)

    # 5. Inboard Lane Units: Garmin PowerSwitch & Blue Sea 2701 Ground Bus
    g_dx, g_dy, g_dz = COMP_SPECS["garmin_ps"]["dims"]
    gx, gy, gz = COMP_SPECS["garmin_ps"]["pos"]
    garmin = add_box_feature(comp, gx, gy, gz, g_dx, g_dy, g_dz, body_name="garmin_powerswitch")
    fillet_parallel_edges(comp, garmin, "y", COMP_FILLET_R)
    apply_color(app, design, garmin, *COL_CUBE_BLACK)

    if not import_positioned_step(
        app, design, comp, "bluesea_2701_ground_bus.step", "bluesea_2701_ground_bus", COL_POWER_GOLD
    ):
        gb_dx, gb_dy, gb_dz = COMP_SPECS["gnd_bus_2701"]["dims"]
        gbx, gby, gbz = COMP_SPECS["gnd_bus_2701"]["pos"]
        base_t = 9.0
        gbus = add_box_feature(
            comp, gbx, gby + gb_dy - base_t, gbz, gb_dx, base_t, gb_dz, body_name="bluesea_2701_ground_bus"
        )
        fillet_parallel_edges(comp, gbus, "y", 4.0)
        # Raised end mounting ears + center insulating barrier
        for ex0 in (gbx, gbx + gb_dx - 19.3):
            add_box_feature(
                comp, ex0, gby + gb_dy - 17.0, gbz + gb_dz / 2.0 - 9.0,
                19.3, 17.0, 18.0,
                adsk.fusion.FeatureOperations.JoinFeatureOperation, gbus,
            )
        add_box_feature(
            comp, gbx + 17.5, gby, gbz + gb_dz / 2.0 - 2.5,
            gb_dx - 35.0, gb_dy, 5.0,
            adsk.fusion.FeatureOperations.JoinFeatureOperation, gbus,
        )
        # 2x Ø5.0 mm mounting holes + Ø9.5 mm counterbores at 57.20 mm centers
        gb_thru = [(gbx + u, gby, gbz + v, 2.5) for (u, v) in COMP_SPECS["gnd_bus_2701"]["holes_xz"]]
        gb_cb = [(gbx + u, gby + gb_dy - 17.0, gbz + v, 4.75) for (u, v) in COMP_SPECS["gnd_bus_2701"]["holes_xz"]]
        cut_cylinders_on_plane(comp, gbus, "y", gby - 0.5, gb_dy + 1.0, gb_thru)
        cut_cylinders_on_plane(comp, gbus, "y", gby + gb_dy - 17.5, 9.0, gb_cb)
        apply_color(app, design, gbus, *COL_POWER_GOLD)

    # 6. Rear Panel GX Touch 50 Display + Right-Angle Cable Plug Clearance Envelope (flush on printed back panel)
    pm = PANEL_OUTER_OFFSET
    gxt = add_box_feature(
        comp,
        pm - 3.0,
        GX_TOUCH_YC - 136.0 / 2.0,
        GX_TOUCH_ZC - 94.0 / 2.0,
        3.0,
        136.0,
        94.0,
        body_name="victron_gx_touch_50",
    )
    add_box_feature(
        comp,
        pm,
        GX_TOUCH_YC - GX_TOUCH_CUT_W_Y / 2.0,
        GX_TOUCH_ZC - GX_TOUCH_CUT_H_Z / 2.0,
        12.0,
        GX_TOUCH_CUT_W_Y,
        GX_TOUCH_CUT_H_Z,
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        gxt,
    )
    add_box_feature(
        comp,
        pm + 12.0,
        GX_TOUCH_YC - 20.0,
        GX_TOUCH_ZC - 10.0,
        15.0,
        40.0,
        20.0,
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        gxt,
    )
    apply_color(app, design, gxt, *COL_CUBE_BLACK)

    # 7. Front Panel Port Inward Bodies (Real Anderson SB175 & SB50 STEP housings + Flanged AC Inlets & 12V/USB Sockets)
    xf_inner = BOX_DEPTH_X - pm - PANEL_THICK  # 556.0 mm
    step_port_map = {
        "sb50_pack2_umbilical": "anderson_sb50_pack2.step",
        "sb50_alt_in": "anderson_sb50_alt.step",
    }
    for pname, pkind, py, pz, psize, pdepth in FRONT_PANEL_PORTS:
        if pname in step_port_map and import_positioned_step(
            app, design, comp, step_port_map[pname], f"port_{pname}", COL_PORT_GRAY
        ):
            continue
        if pkind == "circle":
            r_hole = psize[0] / 2.0
            is_ac = pname.startswith("l14")
            r_flange = r_hole + (1.5 if is_ac else 2.5)
            t_flange = 3.5 if is_ac else 2.5
            r_barrel = (r_hole - 4.0) if is_ac else (r_hole - 0.2)
            d_barrel = 42.0 if is_ac else 28.0
            # Outer front flange on panel face (+X)
            f_plane = create_offset_plane(comp, "x", xf_inner + PANEL_THICK)
            f_sketch = comp.sketches.add(f_plane)
            f_sketch.sketchCurves.sketchCircles.addByCenterRadius(
                sketch_world_point(f_sketch, xf_inner + PANEL_THICK, py, pz), cm(r_flange)
            )
            pbody = extrude_all_profiles(
                comp, f_sketch, "x", t_flange,
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                body_name=f"port_{pname}",
            )
            # Rear barrel (-X)
            b_plane = create_offset_plane(comp, "x", xf_inner + PANEL_THICK)
            b_sketch = comp.sketches.add(b_plane)
            b_sketch.sketchCurves.sketchCircles.addByCenterRadius(
                sketch_world_point(b_sketch, xf_inner + PANEL_THICK, py, pz), cm(r_barrel)
            )
            extrude_all_profiles(
                comp, b_sketch, "x", -(PANEL_THICK + d_barrel),
                adsk.fusion.FeatureOperations.JoinFeatureOperation,
                target_body=pbody,
            )
            # Rear boot / terminal block (-X)
            r_boot = 18.0 if is_ac else (r_hole * 0.55)
            d_boot = (pdepth - d_barrel) if is_ac else 12.0
            bt_plane = create_offset_plane(comp, "x", xf_inner - d_barrel)
            bt_sketch = comp.sketches.add(bt_plane)
            bt_sketch.sketchCurves.sketchCircles.addByCenterRadius(
                sketch_world_point(bt_sketch, xf_inner - d_barrel, py, pz), cm(r_boot)
            )
            extrude_all_profiles(
                comp, bt_sketch, "x", -d_boot,
                adsk.fusion.FeatureOperations.JoinFeatureOperation,
                target_body=pbody,
            )
        else:
            pw, ph = psize[0], psize[1]
            pbody = add_box_feature(
                comp, xf_inner - pdepth, py - pw / 2.0, pz - ph / 2.0,
                pdepth, pw, ph, body_name=f"port_{pname}",
            )
        apply_color(app, design, pbody, *COL_PORT_GRAY)

    return comp


# ==============================================================================
# 4. MAIN ENTRY POINT FOR AUTODESK FUSION
# ==============================================================================

def run(context: dict) -> None:
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Use the active empty design if one is already open, otherwise create a new one
        design = adsk.fusion.Design.cast(app.activeProduct)
        if (
            design is None
            or design.rootComponent.bRepBodies.count > 0
            or design.rootComponent.occurrences.count > 0
        ):
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            doc.name = f"4Runner_Battery_Box_v12s_{PRINTER_PRESET}"
            design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType

        # Set document display units to millimeters
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        register_user_parameters(design)

        root = design.rootComponent

        # Build the 6 structured sub-assemblies
        build_frame_and_panels(app, design, root)
        build_battery_zone_outboard(app, design, root)
        _bus_comp, sill_holes_xz = build_center_bus_column(app, design, root)
        build_inverter_plate_assembly(app, design, root, sill_holes_xz)
        build_inboard_garmin_lane(app, design, root)
        build_electrical_components(app, design, root)

        # Fit camera to full assembly in isometric view
        vp = app.activeViewport
        if vp:
            vp.fit()

        tile_desc = "2-tile H2D (252.8 x 256 mm)" if PRINTER_PRESET == "H2D" else "6-tile P1P (168.5 x 140 mm)"
        ui.messageBox(
            f"4Runner Battery Box (master / {PRINTER_PRESET}) generated successfully!\n\n"
            f"• Envelope: {BOX_DEPTH_X} × {BOX_WIDTH_Y} × {BOX_HEIGHT_Z} mm (+ {LID_THICK} mm lid)\n"
            f"• Inverter Plate: {tile_desc} in 1-piece full-height slotted posts\n"
            f"• All heat-set insert bores (incl. Blue Sea 2701 M4s), rail T-nut countersinks,\n"
            f"  7 front ports (2× L14-30, 2× SB50, 3× round sockets), 70×70 mm cable window,\n"
            f"  17 mm 4 AWG drop-shelf wire channels, and 57 mm bus-shelf wire trough modeled.",
            "master / v12s_h2d Assembly Complete",
        )

    except Exception:
        if ui:
            ui.messageBox(f"Script execution failed:\n{traceback.format_exc()}", "Fusion Script Error")
    finally:
        # Evict module from Fusion's persistent sys.modules cache so subsequent runs always reload from disk
        sys.modules.pop(__name__, None)
