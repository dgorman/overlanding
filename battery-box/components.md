# Component dimensions and mounting (research, 2026-10-04)

Axis convention: Victron states **h × w × d**. Mounting-hole figures are read from Victron dimension drawings. "Not found" means it is not published, not that it is zero.

## Victron

| Item | Model / PN | Overall (mm) | Weight | Mounting holes | Orientation | Source |
|---|---|---|---|---|---|---|
| Cerbo GX | BPP900450110 (current "MK2"); MK3 also exists | h 78 × w 154 × d 48 (154 across the ears; body ~143) | ~0.5 kg | 4× Ø4 in corner ears; centres **143 × 58** | Any | [Drawing](https://www.victronenergy.com/upload/documents/Cerbo-GX.PDF) · [Specs](https://www.victronenergy.com/media/pg/Cerbo_GX/en/technical-specifications.html) |
| Orion XS 12/12-50A | ORI121217040 | h 137.3 × w 123.1 × d 40 | 0.33 kg | 4× Ø4.3; centres **109.3 × 113.0** | **Vertical, power terminals down**, ≥10 cm clearance, heatsink to 90 °C, IP65 | [Drawing](https://www.victronenergy.com/upload/documents/DimensionDrawing-ORI121217040-Orion-XS-12-12-50A-DC-DC-battery-charger.pdf) · [Install](https://www.victronenergy.com/media/pg/Orion_XS_12-12-50A_DC-DC_battery_charger/en/installation.html) |
| SmartSolar MPPT 100/30 | SCC110030210 | h 130 × w 186 × d 70 | 1.3 kg | 4 keyholes (Ø8 head / 5 mm slot); centres **176 × 71.5**; 4.8 mm in from sides, 25 mm below top | Vertical, terminals down | [Drawing](https://www.victronenergy.com/upload/documents/BS-SS-MPPT-100-30.pdf) |
| SmartShunt 500A/50mV | SHU050150050 | 120 long × 52.5 wide base × 34 tall body (54 with studs) | ~0.32 kg | 2× Ø6 base holes at **101 mm** centres; M10 studs at 55 mm | Any; IP21, keep dry | [Drawing](https://www.victronenergy.com/upload/documents/DimensionDrawing-SmartShunt-500A50mV.pdf) |
| **MultiPlus 12/800/35-16 120V** (owner-confirmed) | PMP121800100 | **360 × 240 × 100**; siblings 12/500 = 311 × 182 × 100 (4.4 kg), 12/1200 = 406 × 250 × 100 (8.2 kg) | 6.4 kg | 2 top + 2 bottom keyholes, centres **220.6 × 243.8**, upper pair 62.8 from top | Keyhole layout implies vertical, cables down; ≥10 cm clearance all round | [Manual](https://www.victronenergy.com/upload/documents/MultiPlus_12V_500-1200VA_120Vac/155314-MultiPlus_500-1200VA_120Vac-pdf-en.pdf) |
| Lithium SuperPack 12.8V/60Ah | BAT512060705 | 229 × 138 × 213 (L × W × H) | 7.5 kg | Case only, strap down | Upright or on its long side; internal BMS; M6; **30 A cont. / 80 A 10 s discharge, 30 A charge, parallel unlimited** | [Datasheet](https://www.victronenergy.com/upload/documents/Datasheet-12,8V-&-25,6-Lithium-SuperPack-EN.pdf) |
| Lynx Distributor (alternative bus) | LYN060102000 | 288 × 169 × 78 | 2.2 kg | rear slots 178 × 81 | Any | [Drawing](https://www.victronenergy.com/upload/documents/Lynx-Distributor.pdf) |

**Inverter:** owner confirmed MultiPlus 12/800 (800 W). The photographed LED cluster "inverter / charger / alarm" is shared across the 12/500–12/1200 family; dims above are from the family manual, table on p.22.

**Why the batteries are SuperPacks:** Victron's current Lithium Battery Smart range has no 12.8V/60Ah (50, 100, 160, 180, 200, 330 only). The SuperPack line has a 12.8V/60Ah.

## Non-Victron

| Item | Model | Overall | Weight | Mounting | Notes | Source |
|---|---|---|---|---|---|---|
| Garmin PowerSwitch | 010-02466-00 | 125 W × 75 D × 32 H mm | ~0.28 kg | supplied mount, 2 screws (spacing not published) | IPX7, ≤85 °C | [Garmin](https://www8.garmin.com/manuals/webhelp/GUID-B958A516-72E8-47CA-8793-6337D398EC08/EN-US/GUID-E9A53DAE-B84A-4E4F-9488-5536604B1779.html) |
| Blue Sea 2300 Common 150A BusBar, 10-gang w/ cover | 2300 | 155 × 32 × 28 mm | 0.18 kg | not found | 2× 1/4"-20 studs + 10× #8-32 | [Blue Sea](https://www.bluesea.com/products/2300/Common_150A_BusBar_-_10_Gang_with_Cover) |
| Blue Sea 2127 MaxiBus 250A | 2127 | 149 × 38 × 48.5 mm | 0.36 kg | 2× #10 screws | 4× 5/16" studs; cover 2719 | [Powerwerx](https://powerwerx.com/blue-sea-2127-maxibus-250a-busbar) |
| Blue Sea 285-series surface breaker | 7180–7189 | 81 × 48 × 31.5 mm | 0.23 kg | 2× 1/4" screws | IP67, 1/4"-28 studs | [ISC](https://inverterservicecenter.com/285-series-surface-mount-circuit-breaker-30-amp-blue-sea-7181) |
| T-Tocas surface breaker 30–150 A | — | ~74 × 48 × 43 mm | — | 2× Ø6.6 | IP67, 1/4" studs | [Amazon](https://www.amazon.com/Tocas-150A-Circuit-Breaker-Battery/dp/B01F76VJ3I) |

## Goose Gear

| Item | What the page says | Source |
|---|---|---|
| IceBox 1.3, 25" deep module (the owner's is the **30" deep** version: 762 mm) | "Fridge slide storage unit": enclosure with full-extension fridge tray (15" W × 20" H × 26" D) and gear storage on top. **External 19-3/16" W × 22" H × 25" D**, ~42 lb, $1,345, MaxLite 6063-T6 frame. Slotted back panel: no name, no slot pitch published. | [Page](https://www.goose-gear.com/products/icebox-1-3-25-deep-module) |
| Extrusion Frame Modification Kit x.31 | PN 4918-GGR-SH, $139. "Includes both Extrusion Bars and hardware needed." Bar count, lengths and hardware **not stated**. Purpose: add a Seat Delete Module height; fits CampKitchen 2.3 and IceBox 1.3. 8-week build to order. | [Page](https://www.goose-gear.com/products/extrusion-frame-modification-kit-x-31-for-campkitchen-icebox) |
| MaxLite extrusion | No published cross-section, slot width or 80/20 compatibility. 6063-T6, "26 % lighter". Goose Gear Anchors use roll-in T-nuts for 1/4-20 or M6, consistent with a 10-series-class slot (inference). **Measure a slot.** | [MaxLite](https://www.goose-gear.com/blogs/newsroom/goose-gear-introduces-revolutionary-maxlite-technology-in-explore-series) · [Anchors](https://www.goose-gear.com/products/goose-gear-anchor-kits) |

## Larger inverters (Victron spec page; neither fits a 437 mm card, and four SuperPack 60Ah supply only 120 A)

| Item | Size (mm) | Weight |
|---|---|---|
| MultiPlus-II 12/3000/120-50 120V | 578 × 277 × 148 (h × w × d), 3000 VA / 2400 W, 5500 W peak, 120 A charger | 19 kg |
| MultiPlus-II 12/4k/160-50 120V | 631 × 277 × 164, 160 A charger | 22 kg |

## Victron 3D files (used in the model, `cad/step/`)

All from `https://www.victronenergy.com/upload/documents/`. The model keeps only each file's housing-sized solids (the Cerbo file alone has 686 internal parts) and caches them as BREP in `cad/step/cache/`. The 147 MB of raw STEP is gitignored; re-download with the URLs below.

| Product | File on victronenergy.com |
|---|---|
| MultiPlus-II 12/3000/120-50 120V (UL) | `MultiPlus-II-12V-3000VA-120V-(UL).STEP` |
| Lithium Smart 12.8V 160Ah / 200Ah (shared case) | `LiFePO4-battery-12,8V160Ah-a-&-12,8V200Ah-a-Smart-(stp).STEP` |
| Lithium Smart 12.8V 100Ah | `LiFePO4_12.8V100Ah_Smart.STEP` |
| SmartSolar MPPT 100/30 | `BS-SS-MPPT-100-30-(stp).STEP` |
| Orion XS 12/12-50A | `DimensionDrawing-ORI121217040-Orion-XS-12-12-50A-DC-DC-battery-charger-3D.STEP` |
| Cerbo GX | `DimensionDrawing_CerboGX-3D.STEP` |
| SmartShunt 500A/50mV | `DimensionDrawing-SmartShunt-500A50mV-3D.STEP` |
| MultiPlus 12/800 (12/24/48V, 120/230V shared housing) | `MultiPlus-12-24-48V-800VA-120V-230V-(step).STEP` |
| Lithium SuperPack 12.8V/60Ah (M6) | `DimensionDrawing-BAT512060705-Lithium-SuperPack-12,8V60Ah-(M6)-3D.STEP` |
| VE.Bus BMS V2 (122 × 106 × 23 mm) | `DimensionDrawing-VE.bus-BMS-V2.STP` |
