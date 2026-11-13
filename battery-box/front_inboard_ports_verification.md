# Dual-Nozzle Front Enclosure Panels & Removable Accessory MOLLE Panel — Production Spec

Source geometry verified directly from `stl/master/print_panel_front_outboard_multicolor.3mf`, `stl/master/print_panel_front_outboard.stl`, `stl/master/print_panel_front_outboard_inlay_white.stl`, `stl/master/print_panel_front_inboard_ports_multicolor.3mf`, `stl/master/print_panel_front_inboard_ports.stl`, `stl/master/print_panel_front_inboard_ports_inlay_white.stl`, `stl/master/print_panel_front_outboard_molle.stl`, and `cad/cage.py`.

![Dual-Nozzle Front Enclosure Panels & Accessory MOLLE Engineering Drawing](./front_inboard_ports_verification.png)

---

## 1. Dual-Nozzle Bambu H2D Setup (`print_panel_front_outboard_multicolor.3mf` & `print_panel_front_inboard_ports_multicolor.3mf`)

Both front tiles print **exterior face down on `Z = 0.00 mm` (Textured PEI plate)** so the `0.60 mm` (`3 × 0.20 mm` layers) White PETG outlines and labels cure dead-flush inside the Black PETG panel face with zero raised snagging edges and only **3 nozzle swaps total** (Layers `1–3`, ~15 seconds on the H2D; Layers `4–31` print 100% single-nozzle Black PETG):

- **`print_panel_front_outboard_multicolor.3mf` (`245.5 × 278.0 × 6.25 mm` on bed — `"AUX BATT"`):**
  - `panel_black` = **Black PETG** nozzle (`1`), `inlay_white` = **White PETG** nozzle (`2`).
  - **Plate Settings → First layer filament sequence:** `Customize` → **`White (2) → Black (1)`**.
  - **Wall generator:** `Arachne`.
  - **Enable support:** **`UNCHECKED` (NO supports needed!)** — `print_panel_front_outboard` carries the `Z = 0.000..3.125 mm` base half-lap flap resting directly on the Textured PEI plate.
- **`print_panel_front_inboard_ports_multicolor.3mf` (`245.5 × 186.1 × 6.25 mm` on bed — 6-Port Strip):**
  - Same nozzle mapping, `First layer filament sequence: White (2) → Black (1)`, and `Arachne` wall generator, plus **Normal / Snug / On build plate only** supports under its `Z = 3.20..6.10 mm` (`-0.15 mm` relieved) rear half-lap flap.
- *(Alternative)* Drag the paired `.stl` + `*_inlay_white.stl` files together onto the Bambu Studio plate and click **Yes** (*"Load these files as a single object with multiple parts?"*).

---

## 2. Final Port Coordinates, White Outlines & Top Labels

### A. Outboard Front Tile — `print_panel_front_outboard` (`278.0 W × 245.5 H × 6.25 T mm`)
Origin: **Left** `u = 0.0 mm` (`3.0 mm` outboard rail slot tongue), **Bottom** `v = 0.0 mm` (`6.9 mm` bottom rail slot tongue; right `20.0 mm` `u = 258.0..278.0 mm` is the `Z = 0..3.125 mm` front half-lap flap):

| Port | Top Label | Center `(u, v)` (`mm`) | Cutout & M4 Mounting Holes *(100% Identical to `P4`)* | White PETG `0.60 mm` Flush Outline (`1.8 mm` Stroke) |
| :--- | :---: | :---: | :--- | :--- |
| **`sb50_pack`** | **`AUX BATT`** | `(193.0, 93.3)` | **`29.0 W × 53.0 H mm`** + `4 × Ø4.30 mm` M4 @ `45°` (`5.0 mm` from corners = `36.07 × 60.07 mm` C-C) | **White Rounded Box:** `45.0 × 69.0 mm` ID (`R7.5`) / `48.6 × 72.6 mm` OD (`R9.3`) |

### B. Inboard Front Tile — `print_panel_front_inboard_ports` (`186.1 W × 245.5 H × 6.25 T mm`)
Origin: **Left** `u = 0.0 mm` (`20.0 mm` rear half-lap seam), **Bottom** `v = 0.0 mm` (`6.9 mm` bottom rail slot tongue; exposed vertical rail daylight = `v = 6.9 .. 238.6 mm`):

| Port | Top Label | Center `(u, v)` (`mm`) | Cutout & M4 Mounting Holes | White PETG `0.60 mm` Flush Outline (`1.8 mm` Stroke) |
| :--- | :---: | :---: | :--- | :--- |
| **`P1`** *(Bottom-Right)* | **`AC IN`** | `(143.0, 46.8)` | **`Ø45.00 mm`** + `2 × Ø4.30 mm` M4 at 12 & 6 o'clock (`v = 19.3` & `74.3`, `55.0 mm` C-C) | **White Circle:** `Ø65.0 mm` ID / `Ø68.6 mm` OD *(clears `5 mm` bezel + M4 heads)* |
| **`P2`** *(Mid-Right)* | **`AC OUT`** | `(143.0, 128.8)` | **`Ø45.00 mm`** + `2 × Ø4.30 mm` M4 at 12 & 6 o'clock (`v = 101.3` & `156.3`, `55.0 mm` C-C) | **White Circle:** `Ø65.0 mm` ID / `Ø68.6 mm` OD |
| **`P3`** *(Top-Right)* | **`DC OUT`** | `(143.0, 200.8)` | **`Ø29.50 mm`** *(rear locknut)* | **White Circle:** `Ø43.5 mm` ID / `Ø47.1 mm` OD *(`7.0 mm` radial gap from hole)* |
| **`P4`** *(Bottom-Left)* | **`DC IN`** | `(75.0, 65.8)` | **`29.0 W × 53.0 H mm`** + `4 × Ø4.30 mm` M4 @ `45°` (`36.07 × 60.07 mm` C-C) | **White Rounded Box:** `45.0 × 69.0 mm` ID (`R7.5`) / `48.6 × 72.6 mm` OD (`R9.3`) |
| **`P5`** *(Mid-Left)* | **`DC OUT`** | `(75.0, 139.8)` | **`Ø29.50 mm`** *(rear locknut)* | **White Circle:** `Ø43.5 mm` ID / `Ø47.1 mm` OD *(`7.0 mm` radial gap from hole)* |
| **`P6`** *(Top-Left)* | **`SOLAR IN`** | `(75.0, 200.8)` | **`Ø29.50 mm`** *(rear locknut)* | **White Circle:** `Ø43.5 mm` ID / `Ø47.1 mm` OD *(`7.0 mm` radial gap from hole)* |

---

## 3. Removable Exterior Accessory MOLLE Panel — `print_panel_front_outboard_molle.stl`

Bolts directly onto the **outer `+X` T-slots** of the three front 25-series aluminum rails over `print_panel_front_outboard` whenever the `Pack2` (`AUX BATT`) SB50 umbilical is not plugged in:

| Feature | Specification | Notes |
| :--- | :--- | :--- |
| **Overall Envelope** | `290.0 W × 278.7 H × 10.25 D mm` (`11.42" × 10.97" × 0.404"`) | `6.25 mm` main plate + `4.00 mm` integral rear rail-standoff pads |
| **H2D Print Footprint** | **`278.7 (X) × 290.0 (Y) × 10.25 (Z) mm`** | **1-piece H2D print**, Textured PEI face down on `Z = 0`, **NO supports** |
| **MIL-STD PALS Grid** | **`6 cols × 8 rows = 48` stadium slots** (`30.0 × 13.4 mm`) | True **`38.1 × 25.4 mm` (`1.50" × 1.00"`)** Natick PALS webbing & `1/4"`/`M6` bolt pitch |
| **Behind-Slot Strap Gap** | **`13.38 mm` (`0.53"`)** to `print_panel_front_outboard.stl` | `9.375 mm` rail slot recess + `4.0 mm` standoff pads (`8.4 mm` clear over SB50 bezel!) |
| **Frame Mounting** | **`6 × Ø6.8 mm` through-holes** (`1/4"-20` button screws or thumb knobs) | Threads into `6` drop-in T-nuts in Top (`Z = 269.2`), Bottom (`Z = 12.5`), and Outboard (`Y = 12.5`) rail outer slots |
