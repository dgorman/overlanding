# Dual-Nozzle Front Enclosure Panels & Removable Accessory MOLLE Panel — Production Spec

Source geometry verified directly from `stl/master/print_panel_front_outboard_multicolor.3mf`, `stl/master/print_panel_front_outboard.stl`, `stl/master/print_panel_front_outboard_inlay_white.stl`, `stl/master/print_panel_front_inboard_ports_multicolor.3mf`, `stl/master/print_panel_front_inboard_ports.stl`, `stl/master/print_panel_front_inboard_ports_inlay_white.stl`, `stl/master/print_panel_front_outboard_molle.stl`, and `cad/cage.py`.

![Dual-Nozzle Front Enclosure Panels & Accessory MOLLE Engineering Drawing](./front_inboard_ports_verification.png)

---

## 1. Dual-Nozzle Bambu H2D Setup (`print_panel_front_outboard_multicolor.3mf` & `print_panel_front_inboard_ports_multicolor.3mf`)

Open either `.3mf` in **Bambu Studio** with the H2D dual-nozzle printer selected (`Textured PEI` face down at `Z = 0`):

- **`print_panel_front_outboard_multicolor.3mf` (`245.5 × 278.0 × 6.25 mm` on bed — `2 × SB50` Stacked Near Lap: `AUX BATT` & `DC IN`):**
  - **Extruder 1 (Body — Black PETG):** `print_panel_front_outboard`
  - **Extruder 2 (Flush `0.60 mm` / `3 × 0.20 mm` White PETG Inlay):** `print_panel_front_outboard_inlay_white`
  - **Enable support:** **`UNCHECKED` (NO supports needed!)** — `print_panel_front_outboard` carries the `Z = 0.000..3.125 mm` base half-lap flap resting directly on the Textured PEI plate.
- **`print_panel_front_inboard_ports_multicolor.3mf` (`245.5 × 186.1 × 6.25 mm` on bed — 6-Port Strip: `AC IN`, `AC OUT`, `4 × DC OUT`):**
  - **Extruder 1 (Body — Black PETG):** `print_panel_front_inboard_ports`
  - **Extruder 2 (Flush `0.60 mm` / `3 × 0.20 mm` White PETG Inlay):** `print_panel_front_inboard_ports_inlay_white`
  - **Enable support:** **`ON` (`Support critical regions only`)** in Bambu Studio — holds the `Z = 3.200..6.100 mm` overhanging right-edge half-lap flap (`+0.075 mm` clearance over `3.125 mm` mating flap + `-0.15 mm` seam relief).
- **Recommended slicer settings:** `0.20 mm` Standard layer height, `4` wall loops, `25%` Gyroid/Grid infill, `White` mapped to the flush text/ring nozzle and `Black` mapped to the panel body + support nozzle.

---

## 2. Port & Flush White Inlay Coordinates (Installed Exterior View)

### A. Outboard Front Tile — `print_panel_front_outboard` (`278.0 W × 245.5 H × 6.25 T mm`)
Origin: **Left** `u = 0.0 mm` (`Y = 22.0 mm`, `3.0 mm` outboard rail slot tongue), **Bottom** `v = 0.0 mm` (`Z = 18.1 mm`, `6.9 mm` bottom rail slot tongue; right `20.0 mm` `u = 258.0..278.0 mm` is the `Z = 0..3.125 mm` front half-lap flap):

| Port ID | Label | Center `(u, v)` mm | Cutout & Bolt Geometry | Flush White PETG Inlay (`Z = 0..0.60 mm`) |
| :--- | :--- | :--- | :--- | :--- |
| **`sb50_pack`** *(Upper)* | **`AUX BATT`** | `(225.0, 177.8)` (`Y=247`) | **`29.0 W × 53.0 H mm`** + `4 × Ø4.30 mm` M4 @ `45°` (`36.07 × 60.07 mm` C-C) | **White Rounded Box:** `55.0 × 79.0 mm` ID (`R7.5`) / `58.6 × 82.6 mm` OD (`R9.3`) |
| **`sb50_alt`** *(Lower)* | **`DC IN`** | `(225.0, 71.8)` (`Y=247`) | **`29.0 W × 53.0 H mm`** + `4 × Ø4.30 mm` M4 @ `45°` (`36.07 × 60.07 mm` C-C) | **White Rounded Box:** `55.0 × 79.0 mm` ID (`R7.5`) / `58.6 × 82.6 mm` OD (`R9.3`) |

Both SB50 housings sit vertically stacked at `Y = 247.0 mm` (`3.7 mm` clear of the `Y = 280.0..300.0` half-lap, `7.7 mm` clear of the trimmed MOLLE right edge at `Y = 210.0 mm`, and `15.5 mm` clear of the SB50 dust covers).

### B. Inboard Front Tile — `print_panel_front_inboard_ports` (`186.1 W × 245.5 H × 6.25 T mm`)
Origin: **Left** `u = 0.0 mm` (`Y = 280.0 mm`, `20.0 mm` half-lap joint `u = 0..20 mm`), **Bottom** `v = 0.0 mm` (`Z = 18.1 mm`, `6.9 mm` bottom rail slot tongue; right `3.0 mm` sits inside the inboard rail slot):

| Port | Label | Center `(u, v)` mm | Cutout & Bolt Geometry | Flush White PETG Inlay (`Z = 0..0.60 mm`) |
| :--- | :--- | :--- | :--- | :--- |
| **`P1`** *(Bottom-Right)* | **`AC IN`** | `(143.0, 46.8)` | **`Ø44.00 mm`** + `2 × Ø4.20 mm` M4 @ `(0, ±27.5)` | **White Circle:** `Ø65.0 mm` ID / `Ø68.6 mm` OD *(`1.8 mm` stroke; clears `Ø63 mm` bezel & bolts)* |
| **`P2`** *(Mid-Right)* | **`AC OUT`** | `(143.0, 128.8)` | **`Ø44.00 mm`** + `2 × Ø4.20 mm` M4 @ `(0, ±27.5)` | **White Circle:** `Ø65.0 mm` ID / `Ø68.6 mm` OD *(`1.8 mm` stroke; clears `Ø63 mm` bezel & bolts)* |
| **`P3`** *(Top-Right)* | **`DC OUT`** | `(143.0, 200.8)` | **`Ø29.50 mm`** *(rear locknut)* | **White Circle:** `Ø43.5 mm` ID / `Ø47.1 mm` OD *(`7.0 mm` radial gap from hole)* |
| **`P4`** *(Bottom-Left)* | **`DC OUT`** | `(65.0, 46.8)` | **`Ø29.50 mm`** *(rear locknut)* | **White Circle:** `Ø43.5 mm` ID / `Ø47.1 mm` OD *(row-aligned with `P1`)* |
| **`P5`** *(Mid-Left)* | **`DC OUT`** | `(65.0, 128.8)` | **`Ø29.50 mm`** *(rear locknut)* | **White Circle:** `Ø43.5 mm` ID / `Ø47.1 mm` OD *(row-aligned with `P2`)* |
| **`P6`** *(Top-Left)* | **`DC OUT`** | `(65.0, 200.8)` | **`Ø29.50 mm`** *(rear locknut)* | **White Circle:** `Ø43.5 mm` ID / `Ø47.1 mm` OD *(row-aligned with `P3`)* |

---

## 3. Removable Exterior Accessory MOLLE Panel — `print_panel_front_outboard_molle.stl`

Bolts directly onto the **outer `+X` T-slots** of the three front 25-series aluminum rails over `print_panel_front_outboard`, trimmed cleanly at **`Y = 210.0 mm`** so both SB50 ports (`Y = 217.7..276.3 mm` white outlines / `225.5..268.5 mm` covers) remain completely accessible even with the MOLLE panel installed:

| Feature | Specification | Notes |
| :--- | :--- | :--- |
| **Overall Envelope** | `208.5 W × 278.7 H × 10.25 D mm` (`Y = 1.5..210.0 mm`) | `6.25 mm` main plate + `4.00 mm` integral rear rail-standoff pads |
| **H2D Print Footprint** | **`278.7 (X) × 208.5 (Y) × 10.25 (Z) mm`** | **1-piece H2D print**, Textured PEI face down on `Z = 0`, **NO supports** |
| **MIL-STD PALS Grid** | **`4 cols × 8 rows = 32` stadium slots** (`30.0 × 13.4 mm`) | True **`38.1 × 25.4 mm` (`1.50" × 1.00"`)** Natick PALS pitch |
| **SB50 Clearance** | **`7.7 mm`** to white border / **`15.5 mm`** to SB50 covers | Stays completely outboard (`Y <= 210.0`) of stacked `AUX BATT` + `DC IN` (`Y = 247.0`) |
| **Frame Mounting** | **`6 × Ø6.8 mm` through-holes** (`1/4"-20` button screws or thumb knobs) | Threads into `6` drop-in T-nuts in Top (`Y = 65, 175`), Bottom (`Y = 65, 175`), and Outboard (`Z = 80, 201.7`) rail outer slots |
