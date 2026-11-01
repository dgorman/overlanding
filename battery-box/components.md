# Component Dimensions, Mounting & 3D STEP Models

**Build Status:** Active build is **`v12s`** (see [`README.md`](README.md) and [`MANUAL.md`](MANUAL.md)):
- **Frame & Panels:** Cut down from a donor **25 in Goose Gear IceBox 1.3** (`571.5 × 488.1 × 281.7 mm` as built; `25.0 mm` metric 25-series rails, `25.75 mm` corner cubes) plus one bar from a Goose Gear Extrusion Frame Modification Kit x.31 for the front-bottom width rail. *(The owner's main fridge IceBox in the truck is the **30 in deep** `762 mm` model.)*
- **Inverter:** Owner's **MultiPlus 12/800/35-16 120V** (modelled in [`cad/cage.py`](cad/cage.py) to the larger **12/1200** housing envelope so either fits).
- **Batteries:** Two **Victron SuperPack 12.8V/60Ah** inside `v12s`, plus four more in **`pack2`** on an Anderson SB175 umbilical (`360 Ah` / `180 A` continuous total).

Axis convention: Victron states **h × w × d**. Mounting-hole figures come from manufacturer dimension drawings.

---

## 1. Active `v12s` & `pack2` Components

### Victron Energy

| Item | Model / PN | Overall (mm) | Weight | Mounting Holes | Orientation & Clearance | Source |
|---|---|---|---|---|---|---|
| **MultiPlus 12/800/35-16 120V** *(owner-confirmed; CAD draws the 12/1200 envelope)* | `PMP121800100` | **360 × 240 × 100** *(12/500 = 311 × 182 × 100, 4.4 kg; **12/1200 = 406 × 250 × 100**, 8.2 kg; body 374.6 tall without top bracket)* | 6.4 kg | 2 top + 2 bottom keyholes, centres **220.6 × 243.8**, upper pair 62.8 below top of 374.6 body | Mounted on its long side along the inboard plate, cable end forward; ≥10 cm vent clearance | [Manual](https://www.victronenergy.com/upload/documents/MultiPlus_12V_500-1200VA_120Vac/155314-MultiPlus_500-1200VA_120Vac-pdf-en.pdf) |
| **Lithium SuperPack 12.8V/60Ah** (×2 in `v12s`, ×4 in `pack2`) | `BAT512060705` | **229 × 138 × 213** (L × W × H; flat body top is **208**, M6 terminal posts add 5 mm) | 7.5 kg | Case only; held in `v12s` by tray walls + foam-padded breaker drop shelf | Upright or on long side; internal BMS; M6 terminals; **30 A cont. / 80 A 10 s discharge, 30 A charge, unlimited parallel** | [Datasheet](https://www.victronenergy.com/upload/documents/Datasheet-12,8V-&-25,6-Lithium-SuperPack-EN.pdf) |
| **SmartSolar MPPT 100/30** | `SCC110030210` | **h 130 × w 186 × d 70** | 1.3 kg | 4 keyholes (Ø8 head / 5 mm slot); centres **176 × 71.5**; 4.8 mm in from sides, 25 mm below top | Vertical, terminals down (mounted rotated 90° upright on column face of plate) | [Drawing](https://www.victronenergy.com/upload/documents/BS-SS-MPPT-100-30.pdf) |
| **Orion XS 12/12-50A** | `ORI121217040` | **h 137.3 × w 123.1 × d 40** | 0.33 kg | 4× Ø4.3; centres **109.3 × 113.0** | **Vertical, power terminals down**, ≥10 cm clearance, heatsink to 90 °C, IP65 | [Drawing](https://www.victronenergy.com/upload/documents/DimensionDrawing-ORI121217040-Orion-XS-12-12-50A-DC-DC-battery-charger.pdf) · [Install](https://www.victronenergy.com/media/pg/Orion_XS_12-12-50A_DC-DC_battery_charger/en/installation.html) |
| **Cerbo GX** | `BPP900450110` (MK2) | **h 78 × w 154 × d 48** (154 across ears; body ~143) | ~0.5 kg | 4× Ø4 in corner ears; centres **143 × 58** | Any (column face of inverter plate) | [Drawing](https://www.victronenergy.com/upload/documents/Cerbo-GX.PDF) · [Specs](https://www.victronenergy.com/media/pg/Cerbo_GX/en/technical-specifications.html) |
| **GX Touch 50** (flush mount) | `BPP900455150` | **136 × 94 × 12** (face); cable plug behind | ~0.2 kg | Flush cutout per Victron template (modelled **128 × 86**), framed by `print_touch_bezel.stl` (`150 × 108 × 3`) | Let into inboard end of perforated back panel (`30 mm` clearance to MultiPlus behind it) | [Datasheet](https://www.victronenergy.com/upload/documents/Datasheet-Cerbo-GX-GX-Touch-50-EN.pdf) |
| **SmartShunt 500A/50mV** | `SHU050150050` | **120 long × 52.5 wide base × 34 tall body** (54 with studs) | ~0.32 kg | 2× Ø6 base holes at **101 mm** centres; M10 studs at 55 mm | Mounted on bus shelf floor (`2 × M5` inserts); IP21, keep dry | [Drawing](https://www.victronenergy.com/upload/documents/DimensionDrawing-SmartShunt-500A50mV.pdf) |

### Distribution, Switching & Protection (Non-Victron)

| Item | Model / PN | Overall (mm) | Weight | Mounting Holes | Notes | Source |
|---|---|---|---|---|---|---|
| **Eaton Bussmann 285-Series Breaker** (×2, one per SuperPack on drop shelf) | `285150F-121-S` (150 A in hand; `285060F` 60 A uses identical housing) | **81.28 × 48.13 × 31.5** (+ 6.35 push-to-trip button) | ~0.23 kg | 2 × Ø6.60 mm holes on a **56.64 × 26.67 mm** diagonal (`M5` inserts + washers in drop shelf) | 48 VDC, manual reset / push-to-trip, IP67, M6 studs (5.6 N·m max), any orientation | [Waytek](https://www.waytekwire.com/product/eaton-s-bussmann-series-285060f-121-s-hi-amp) · [Datasheet](https://www.swe-check.com.au/catalog/a64.pdf) |
| **Garmin PowerSwitch** | `010-02466-00` | **125 W × 75 D × 32 H** | ~0.28 kg | Supplied bracket, 2 screws (`M4` short inserts in `print_garmin_hanger.stl`) | 6 channels (30 A per channel, 50 A total max), IPX7, ≤85 °C; hangs on inboard rail | [Garmin](https://www8.garmin.com/manuals/webhelp/GUID-B958A516-72E8-47CA-8793-6337D398EC08/EN-US/GUID-E9A53DAE-B84A-4E4F-9488-5536604B1779.html) |
| **Covered 5-Stud Bus Bars** (×2, `+` red and `−` black) | Generic 12 V / 250 A class, **5 × M8 studs**, clear snap cover (the Blue Sea `2300` 10-gang #8-32 bar listed here before is a 150 A screw-terminal bar and cannot take 4 AWG lugs) | **~155 × 32 × 38** incl. cover (modelled `155 × 35 × 32`) | ~0.2 kg | 2 end ears on **132 mm centres** (owner-measured 2026-10-31), `M5 × 12` into `M5` inserts in bus shelf floor | On the bus shelf floor along the plate-side wall; lugs exit toward the batteries (85 mm from stud centre to tray wall); the plate side has 24 mm, so no lug may point that way | Owner's part (Amazon class); `−` bar must be the same footprint |
| **Garmin port ground bus** | Blue Sea `2701` DualBus 100 A (2 × 5 `#8-32`, buses bridged by the 10 AWG jumper) | **76.5 × 46.5** base, ~25 tall with screws (modelled `77 × 25 × 47` standing on edge) | ~0.1 kg | 2 × `#10`/`M5` mounting screws, **drilled from the part** (no pre-printed pilots) | Inner face of `print_garmin_hanger_lower.stl`, centred, `z 46..93` between the tie-slot rows; every front-port negative lands beside the Garmin that feeds it. Optional cover `2709` | [Blue Sea 2701](https://www.bluesea.com/products/2701) |
| **Anderson SB175 & SB50 Panel Inlets** | `SB175` (×1 pack2 umbilical), `SB50` (×2 solar/alt) | SB175: **55.6 × 79.4 × 25.5** (mated 133.4)<br>SB50: **36.5 × 48 × 16** (mated 81.3) | — | Panel cutouts in solid front panel (`26 × 56` and `48 × 37`) | Official Anderson STEP models cached in `cad/step/` | Drawings `114131S1` & `111923s1` on `andersonpower.com` |

### Goose Gear Frame & Panels

| Item | As-Built Measurements & Specs | Source |
|---|---|---|
| **IceBox 1.3, 25" Deep Module** (donor for `v12s` frame, cubes, and panels) | Original external: **635 × 488.1 × 558.8 mm** (`19-3/16" W × 22" H × 25" D`). Cut down to **`571.5 × 488.1 × 281.7 mm`** (`22.5 × 19.2 × 11.1 in`). Width rails: `436.6 mm` (uncut). Height rails: `508.0 → 230.2 mm`. Depth rails: `584.2 → 520.0 mm`. Panels: `6.0 mm` black phenolic-faced okoume marine plywood captured in rail centre slots (`3.75 mm` tongue depth). | [Goose Gear](https://www.goose-gear.com/products/icebox-1-3-25-deep-module) |
| **Extrusion Frame Modification Kit x.31** | PN `4918-GGR-SH`, $139 (ordered 2026-10-30). Supplies the **missing bottom front width rail (`436.6 mm`)** in matching anodized MaxLite extrusion, factory end-tapped. | [Goose Gear](https://www.goose-gear.com/products/extrusion-frame-modification-kit-x-31-for-campkitchen-icebox) |
| **IceBox stack straps** (printed, `×4`, or cut from `4 mm` aluminium) | `60 × 46 × 4 mm` flat strap across the box-to-IceBox seam on each bottom depth rail's outer face (two per side, `70 mm` in from the corner cubes): `2 × Ø 6.8` holes on the IceBox top rail's slot line, `2 × 6.8 × 9.2` vertical slots on the box bottom rail's, rows `25.75 mm` apart. `1/4-20 × 1/2 in` button heads + washers into drop-in T-nuts in the rails' **outer** slots. Files `stl/v12s/print_stack_strap_*.stl`, `plate_stack_straps.stl`, `print_stack_strap.dxf` | [MANUAL Step 11](MANUAL.md#step-11-strap-the-box-to-the-icebox) |
| **MaxLite™ Extrusion & Corner Cubes** | Measured **metric 25-series (`25.0 × 25.0 mm`)** 6063-T6 extrusion with **`6.5 mm` slot opening** (accepts 10-series / 25-series `1/4-20` drop-in T-nuts `6000N501`). Corner cubes measure **`25.75 mm`** (standing `0.375–0.75 mm` proud of rail faces). | [Audit (`manual/audit-2026-10-30.md`)](manual/audit-2026-10-30.md) |

---

## 2. 3D STEP Models (`cad/step/`)

All Victron STEP files come from `https://www.victronenergy.com/upload/documents/`. [`cad/cage.py`](cad/cage.py) filters each STEP file down to its outer housing solids (e.g. stripping the Cerbo's 686 internal PCB parts) and caches fast-loading BREP files in `cad/step/cache/`. The raw STEP files (~147 MB) are gitignored and can be re-downloaded from the filenames below:

| Component | STEP Filename in `cad/step/` |
|---|---|
| MultiPlus 12/800 / 12/1200 (shared housing family) | `MultiPlus-12-24-48V-800VA-120V-230V-(step).STEP` |
| Lithium SuperPack 12.8V/60Ah (M6) | `DimensionDrawing-BAT512060705-Lithium-SuperPack-12,8V60Ah-(M6)-3D.STEP` |
| SmartSolar MPPT 100/30 | `BS-SS-MPPT-100-30-(stp).STEP` |
| Orion XS 12/12-50A | `DimensionDrawing-ORI121217040-Orion-XS-12-12-50A-DC-DC-battery-charger-3D.STEP` |
| Cerbo GX | `DimensionDrawing_CerboGX-3D.STEP` |
| SmartShunt 500A/50mV | `DimensionDrawing-SmartShunt-500A50mV-3D.STEP` |
| Eaton Bussmann 285 Breaker (optional; parametric stand-in built into `cage.py`) | `Bussmann-285.step` |
| Anderson SB175 & SB50 housings | `ap-web_product-assets_default_step-files_SB-175-Std-02-08-STEP`, `ap-web_product-assets_default_step-files_SB-50-Std-02-08-STEP` |
| *Legacy / Reference variants (`v6`, `v12`, `v13`):* | `MultiPlus-II-12V-3000VA-120V-(UL).STEP`, `LiFePO4-battery-12,8V160Ah-a-&-12,8V200Ah-a-Smart-(stp).STEP`, `LiFePO4_12.8V100Ah_Smart.STEP`, `DimensionDrawing-VE.bus-BMS-V2.STP` |

---

## 3. Evaluated Alternatives & Cancelled Parts (Reference Only)

<details>
<summary>Parts researched during earlier iterations but not used in v12s (click to expand)</summary>

| Item | Model / PN | Dimensions (mm) | Weight | Notes |
|---|---|---|---|---|
| **MultiPlus-II 12/3000/120-50 120V** | Cancelled 2026-10-18 | 578 × 277 × 148 | 19 kg | Too long for the 571.5 mm (`22.5 in`) `v12s` box; explored in `v12` / `v13` (`762 mm` box) |
| **MultiPlus-II 12/4k/160-50 120V** | Reference | 631 × 277 × 164 | 22 kg | Does not fit 635 mm or 571.5 mm box |
| **Victron Lynx Distributor** | `LYN060102000` | 288 × 169 × 78 | 2.2 kg | Alternative M8 bus bar + mega-fuse holder |
| **Blue Sea 2127 MaxiBus 250A** | `2127` | 149 × 38 × 48.5 | 0.36 kg | 4× 5/16" studs; cover `2719` |
| **Blue Sea 187-Series Breaker** | `7148` (150 A) | 87.4 × 59 × 45.6 | 0.26 kg | Used in `v9`–`v13` and `pack2`; replaced in `v12s` by the lower-profile Eaton Bussmann 285 (`31.5 mm` body height) |
| **Blue Sea 285-Series Breaker** | `7180–7189` | 81 × 48 × 31.5 | 0.23 kg | 1/4"-28 studs (Eaton Bussmann `285150F-121-S` is the M6-stud OEM version) |
| **T-Tocas Surface Breaker** | 30–150 A | ~74 × 48 × 43 | — | 1/4" studs, 2× Ø6.6 mounting holes |

</details>
