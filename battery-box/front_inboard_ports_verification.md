# Final Production Engineering Specification — Front & Side H2D Panels

Source geometry verified directly from `stl/master/print_panel_front_inboard_ports.stl`, `stl/master/print_panel_front_outboard.stl`, `stl/master/print_panel_side_*.stl`, and `cad/cage.py`.

![print_panel_front_inboard_ports Final Engineering Drawing](./front_inboard_ports_verification.png)

> **Ready to Print (All Textured PEI Side Out):** Every enclosure panel STL in `stl/master/` is pre-oriented with its **exterior Textured PEI face flat on `Z = 0.00 mm`** and `X_bed = 245.50 mm` so it drops straight onto the Bambu H2D build plate between the left/right nozzle exclusion strips without rotating.

---

## 1. H2D Print Schedule — Front & Side Enclosure Panels (`6` Plates Remaining)

*(Back pair `print_panel_back_inboard_gx.stl` and `print_panel_back_outboard.stl` already printed and verified.)*

| # | STL File (`stl/master/`) | Bed Footprint `X × Y × Z` (`mm`) | Half-Lap Flap (`Z` on Bed) | Bambu Studio H2D Support Setting | Notes |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **1** | `print_panel_front_outboard.stl` | `245.5 × 278.0 × 6.25` | `Z = 0.000 .. 3.125 mm` | **NO supports** | Carries `Pack2` SB50 (`29.0 × 53.0 mm` + `4 × Ø4.3 M4 @ 45°`) |
| **2** | `print_panel_front_inboard_ports.stl` | `245.5 × 186.1 × 6.25` | `Z = 3.200 .. 6.100 mm` | **Enable Supports** *(Normal, Snug, On build plate only)* | Carries final verified `P1`–`P6` ports + M4 holes; `-0.15 mm` lap relief |
| **3** | `print_panel_side_outboard_back.stl` | `245.5 × 278.9 × 6.25` | `Z = 0.000 .. 3.125 mm` | **NO supports** | Solid outboard rear half (`537.8 mm` / `21.17"` assembled pair) |
| **4** | `print_panel_side_outboard_front.stl` | `245.5 × 278.9 × 6.25` | `Z = 3.200 .. 6.100 mm` | **Enable Supports** *(Normal, Snug, On build plate only)* | Solid outboard front half; `-0.15 mm` lap relief (`6.10 mm` joint) |
| **5** | `print_panel_side_inboard_back.stl` | `245.5 × 278.9 × 6.25` | `Z = 0.000 .. 3.125 mm` | **NO supports** | Solid inboard rear half (`537.8 mm` / `21.17"` assembled pair) |
| **6** | `print_panel_side_inboard_front.stl` | `245.5 × 278.9 × 6.25` | `Z = 3.200 .. 6.100 mm` | **Enable Supports** *(Normal, Snug, On build plate only)* | Solid inboard front half; `-0.15 mm` lap relief (`6.10 mm` joint) |

---

## 2. Overall Envelope — `print_panel_front_inboard_ports.stl`

Viewed from the **exterior front** looking `-X` (**Left** `u = 0` is the `20.0 mm` half-lap seam; **Right** `u = 186.1 mm` slots into the inboard vertical rail; **Bottom** `v = 0` slots into the bottom width rail):

| Feature | Metric (`mm`) | Imperial (`in`) | Physical / Assembly Note |
| :--- | :---: | :---: | :--- |
| **Overall Blank (`W × H × T`)** | `186.10 × 245.50 × 6.25` | `7.327" × 9.665" × 0.246"` | `6.25 mm` wall thickness (`0.25 mm` clearance in `6.5 mm` rail slots) |
| **Exposed Daylight Window** | `163.10 × 231.70` | `6.421" × 9.122"` | Clear face between `20 mm` lap step and `25 mm` aluminum rails |
| **Rail Slot Tongues** | `3.0` (Right), `6.9` (Top/Bot) | `0.118"` (R), `0.272"` (T/B) | Right rail face at `u = 183.1`; Bot/Top rails at `v = 6.9` & `238.6` |
| **Right Corner Notches** | `2 × R17.20` (`Ø34.40`) | `R0.677"` (`Ø1.354"`) | Clears front inboard corner cube connectors |
| **Left Half-Lap Seam** | `20.00 W`, `Z = 3.20..6.10` | `0.787" W`, `2.90 mm` flap | `+0.075 mm` glue/interface gap + `-0.15 mm` inner relief (`6.10 mm` total seam) |
| **Internal Rear Post Keepout** | `u = 2.0 .. 50.0` | `0.079" .. 1.969"` | `print_post_inverter_1` sits **`9.4 mm` (`0.37"`) behind inner face** full height |

---

## 3. Final PLA-Test-Verified Port & M4 Bolt Cutouts

| ID & Function | Center `(u, v)` (`mm`) | Final Production Cutout | M4 Mounting Bolt Holes (`Ø4.30 mm` Through) | Clearances & Webs |
| :--- | :---: | :---: | :--- | :--- |
| **`P1` — L14-30 Shore Power Inlet** *(Bottom-Right)* | `(143.0, 57.8)` | **`Ø45.00 mm`** (`1.772"`) | **`2 × Ø4.30 mm`** at 12 & 6 o'clock (`5.0 mm` from edge -> `v = 30.3` & `85.3 mm`, **`55.0 mm` C-to-C**) | `17.6 mm` web to Right rail; `84–135 mm` internal rear depth |
| **`P2` — L14-30 Inverter AC Outlet** *(Mid-Right)* | `(143.0, 127.8)` | **`Ø45.00 mm`** (`1.772"`) | **`2 × Ø4.30 mm`** at 12 & 6 o'clock (`5.0 mm` from edge -> `v = 100.3` & `155.3 mm`, **`55.0 mm` C-to-C**) | `70.0 mm` above `P1` (`25.0 mm` cutout web; `10.7 mm` bridge between M4 holes) |
| **`P3` — Upper-Right Round / USB** *(Top-Right)* | `(143.0, 200.8)` | **`Ø29.50 mm`** (`1.161"`) | Rear locknut *(no flange bolts)* | `73.0 mm` above `P2`; `23.05 mm` web to Top rail; `86.9 mm` rear depth |
| **`P4` — Anderson SB50 Alt/Solar** *(Bottom-Left)* | `(75.0, 93.3)` | **`29.00 W × 53.00 H mm`** (`1.142" × 2.087"`)<br>`u = 60.5..89.5`, `v = 66.8..119.8` | **`4 × Ø4.30 mm`** at `5.0 mm` on `45°` from corners (`u = 56.96` & `93.04`, `v = 63.26` & `123.34` -> **`36.07 × 60.07 mm` C-to-C**) | `+5.0 mm` extended at bottom, `-8.0 mm` narrower; `4.81 mm` clear of `u = 50.0` rear post; `135.3 mm` rear depth |
| **`P5` — 12V Aux / Marine Socket** *(Mid-Left)* | `(75.0, 150.8)` | **`Ø29.50 mm`** (`1.161"`) | Rear locknut *(no flange bolts)* | `16.25 mm` solid bridge above `P4` cutout; `50.0 mm` below `P6` |
| **`P6` — Upper-Left Round / USB** *(Top-Left)* | `(75.0, 200.8)` | **`Ø29.50 mm`** (`1.161"`) | Rear locknut *(no flange bolts)* | `20.50 mm` bridge above `P5`; `23.05 mm` web to Top rail |
| *(Companion)* **`sb50_pack` on `print_panel_front_outboard.stl`** | `65.0 mm` outboard of seam, `v = 93.3` | **`29.00 W × 53.00 H mm`** (`1.142" × 2.087"`) | **`4 × Ø4.30 mm`** at `5.0 mm` on `45°` from corners (**`36.07 × 60.07 mm` C-to-C**) | Matches `P4` pod geometry; `65.4 mm` (`2.57"`) clear rear depth to `print_breaker_shelf_1` |
