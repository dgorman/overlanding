# KRAFTLÅDA (`v12s` / `v13`) — IKEA-Style Visual Assembly Guide

> **4Runner Electronics Box (`571.5 × 488.1 × 281.7 mm` / `22.5 × 19.2 × 11.1 in`)**
> Picture-first build booklet. Follow **Steps `0` → `12`** in order using the hardware codes (**`H1`–`H11`**) and printed-part codes (**`P1`–`P10`**) shown in the top-right corner of every sheet.
> *(For detailed engineering notes, wiring gauges, and full reference tables, see [`MANUAL.md`](MANUAL.md) and [`manual/mcmaster-order.md`](manual/mcmaster-order.md).)*

---

## Step `0` — Parts & Hardware Checklist (`H1–H11` & `P1–P10`)

![Step 0: Parts & Hardware Checklist](manual/ikea/page-00-inventory.png)

* [ ] **Count all 46 brass heat-set inserts** (`12× H5`, `16× H6`, `18× H7`) and **24 drop-in rail T-nuts** (`24× H1`).
* [ ] **Print `P10` (`print_tool_tap_guide.stl`) first** so you can tap the cut rails in Step `1`.

---

## Step `1` — Cut & Tap Frame Rails + Cut Panels & Port Holes

![Step 1: Cut & Tap Rails + Cut Panels & Port Holes](manual/ikea/page-01-rails-panels.png)

* [ ] **`(1)` Cut ONE end only** of the 4 Depth Rails (`520.0 mm`) and 4 Height Rails (`230.2 mm`); leave the 4 Width Rails uncut (`436.6 mm`).
* [ ] **`(2)` Slip `P10` Tap Guide over each cut end** and tap `1/4"-20` (`30 mm` deep) with cutting oil.
* [ ] **`(3)` Cut Front Panel (`444 × 237 mm`)** and drill/jigsaw the 10 port openings at the `(X, Z)` coordinates on the sheet.
* [ ] **`(4)` Cut Back Panel (`444 × 237 mm`, with `128 × 86 mm` GX Touch opening)** and **2 Side Panels (`527.5 × 237 mm`)**.

---

## Step `2` — Battery Trays (`P1 ×2`): Press `10×` `M4` Standard Inserts (`H5`)

![Step 2: Battery Tray Heat-Set Inserts](manual/ikea/page-02-tray-inserts.png)

* [ ] **`(1)` Top of `21 mm` Inboard Wall (`2× H5` per tray):** Press straight down flush at `X = 81` and `161 mm` (*no drilling needed*).
* [ ] **`(2)` Outer Column Face of `21 mm` Wall (`3× H5` per tray):** Press horizontally flush at `Z = 17 mm` (`X = 40, 100, 140` on Tray 0; `X = 40, 120, 200` on Tray 1).
* [ ] **`(3)` Leave the 4 countersunk pocket holes empty** (for `H2` rail screws in Step `8`).

---

## Step `3` — Drop Shelves (`P2 ×2`), Posts (`P6 ×2`) & Garmin (`P8`): Inserts & Foam

![Step 3: Drop Shelves, Posts & Garmin Inserts](manual/ikea/page-03-shelf-post-inserts.png)

* [ ] **`(1)` Drop Shelves (`P2 ×2`):** Press **`2× H7` (`M5`)** straight down into the diagonal breaker holes on each shelf top (*no drilling*).
* [ ] **`(2)` Foam Pads (`×2`):** Peel and stick the **`130 × 140 mm` EPDM foam pad** to the flat underside of each drop shelf.
* [ ] **`(3)` Garmin Hanger (`P8`):** Drill 2 pilots to `Ø 5.6 mm` (`7/32"`) → press **`2× H6` (`M4 Short`)** flush.
* [ ] **`(4)` Inverter Posts (`P6 ×2`, `v12s` only):** Drill top end hole to `Ø 5.6 mm` (`7/32"`) → press **`1× H5` (`M4 Std`)** into each post top.

---

## Step `4` — Inverter Plate (`P4 ×6` + `P5 ×8`): Glue, Press `22×` Inserts & Mount Units

![Step 4: Inverter Plate Sub-Assembly](manual/ikea/page-04-plate-subassembly.png)

* [ ] **`(1)` Column Face (`-Y`):** Glue the 6 tiles (`00..21`) + 4 upper splines (`P5`). Drill 14 blue holes to `Ø 5.6 mm` → press **`14× H6` (`M4 Short`)**. Drill 4 red holes to `Ø 6.4 mm` → press **`4× H7` (`M5`)**. Mount **MPPT** (`4× M5×8`), **Cerbo GX** (`4× H9`), and **Orion XS** (`4× H9`).
* [ ] **`(2)` Inverter Face (`+Y`):** Glue 4 lower splines (`P5`). Drill 4 red keyhole pilots to `Ø 6.4 mm` → press **`4× H7` (`M5`)**. Drive **`4× M5×10 + Washers` (`H11`) and leave heads `3 mm` PROUD**!

---

## Step `5` — Bus Shelf (`P3 ×3`) & Garmin Hanger (`P8`) Sub-Assemblies

![Step 5: Bus Shelf & Garmin Sub-Assemblies](manual/ikea/page-05-bus-subassembly.png)

* [ ] **`(1)` Glue Bus Shelf (`521.5 mm`):** Butt `Plate 0` (`214.7 mm`) + **`Plate 1` (`152.0 mm` middle)** + `Plate 2` (`194.7 mm`) and CA-glue the two `20 mm` wall half-laps.
* [ ] **`(2)` Mount Shunt & Bus Bars:** Mark & drill `6× Ø 6.4 mm` (`1/4"`) holes, press **`6× H7` (`M5`)** inserts, and bolt down the **SmartShunt** and **two 5-stud Bus Bars** with **`6× M5×12` (`H11`)**.
* [ ] **`(3)` Mount Garmin Bracket:** Bolt the Garmin bracket to `P8` with **`2× H8` (`M4×10`)** and snap in the Garmin PowerSwitch.

---

## Step `6` — Bolt Frame, Slide In 4 Panels & Load `24×` Drop-In T-Nuts (`H1`)

![Step 6: Frame, Panels & 24 Drop-In T-Nuts](manual/ikea/page-06-frame-tnuts.png)

* [ ] **`(1)` Assemble Frame & 4 Panels:** Slide the 4 panels into the rail centre slots as you bolt the 8 corner cubes (`F1`). Leave lid off.
* [ ] **`(2)` Roll `24× H1` Drop-In T-Nuts into the Inner Rail Slots:** `16×` in the **Bottom Rails** (Blue) + `8×` in the **Top Rails** (Red, `v12s`) at the millimetre marks on the sheet.

---

## Step `7` — Install Inverter Posts (`P6 ×2` + `2× H4`)

![Step 7: Install Inverter Posts](manual/ikea/page-07-posts.png)

* [ ] **`(1)`–`(2)` Stand `Post 0` against the Back Rail and `Post 1` against the Front Rail** at **`Y = 281 mm`** from the outboard rail (slots facing each other).
* [ ] **`(3)` Drive `1× H4` (`1/4"-20 × 7/8"` Button-Head)** through each post's lower sill hole into the width rail T-nut at `Y = 281 mm`.

---

## Step `8` — Bolt Battery Trays (`P1 ×2` + `8× H2`)

![Step 8: Bolt Battery Trays](manual/ikea/page-08-trays.png)

* [ ] **`(1)` Drive `4× H2` (`1/4"-20 × 1/2"` Flat-Head)** through the trays' outer walls into the Bottom Outboard Rail (`X = 70, 172` & `349.5, 451.5 mm`).
* [ ] **`(2)` Drive `4× H2` (`1/4"-20 × 1/2"` Flat-Head)** through the trays' end walls into the Back & Front Width Rails (`Y = 29` & `140 mm`). Confirm all 8 heads sit **FLUSH**.

---

## Step `9` — Drop In Batteries FIRST, Then Bolt Drop Shelves (`P2 ×2`) & Breakers

![Step 9: Batteries, Drop Shelves & Breakers](manual/ikea/page-09-batteries-shelves.png)

* [ ] **`(1)` Lower both SuperPack 60Ah batteries into the trays FIRST.**
* [ ] **`(2)` Tighten Foot Bolts FIRST (`4× H8` / `M4×10`):** `2×` straight down through each shelf foot into the `21 mm` tray wall (`X = 81, 161` & `360.5, 440.5 mm`).
* [ ] **`(3)` Tighten Top Hanger Bolts SECOND (`4× H2` / `1/4"-20 × 1/2"`):** `2×` through each top hanger into the Top Outboard Rail (compresses foam pad `1 mm` onto battery top).
* [ ] **`(4)` Bolt Bussmann 285 Breakers (`4× M5×10 + Washers`, `H11`)** onto the shelf tops.

---

## Step `10` — Drop In Bus Shelf Sub-Assembly (`6× H8` + `4× H2`)

![Step 10: Drop In Bus Shelf](manual/ikea/page-10-bus-shelf.png)

* [ ] **`(1)` Drive `6× H8` (`M4×10`)** horizontally through the Bus Shelf outboard lip into the trays' `21 mm` wall inserts (`3×` per tray).
* [ ] **`(2)` Drive `4× H2` (`1/4"-20 × 1/2"` Flat-Head)** through the Back & Front end walls into the Width Rails (`Y = 198` & `238 mm`).

---

## Step `11` — Slide In Inverter Plate, Lock Post Clips (`P7`) & Mount Garmin (`P8`)

![Step 11: Slide In Plate, Clips & Garmin](manual/ikea/page-11-plate-clips-garmin.png)

* [ ] **`(1)`–`(2)` Slide Inverter Plate down into the Post 0 & Post 1 slots**, then drive **`6× H9` (`M4×8`)** through the Bus Shelf inboard wall into the plate's bottom band.
* [ ] **`(3)` Lock Post Clips (`P7 ×2`, `v12s`):** Drive **`1× H10` (`M4×35`)** down into each post top + **`1× H3` (`1/4"-20 × 7/8"` Flat-Head)** into the Top Width Rail (`Y = 291 mm`).
* [ ] **`(4)` Mount Upper & Lower Garmin Plates (`P8`):** Drive **`4× H2` (`1/4"-20 × 1/2"` Flat-Head)** into the Top & Bottom Inboard Rails (`X = 341.5` & `421.5 mm`).

---

## Step `12` — Hang MultiPlus, Connect `4 AWG` DC Lugs, Mount Ports & Fit Lid

![Step 12: MultiPlus, Heavy DC Wiring, Ports & Lid](manual/ikea/page-12-multiplus-wiring-lid.png)

* [ ] **`(1)` Hang MultiPlus:** Hook the 4 rear keyholes over the 4 proud `M5×10` screws on the plate and snug all 4 screws with a `3 mm` hex key.
* [ ] **`(2)`–`(4)` Connect `4 AWG` DC Lugs:**
  * **Red (`+`):** Battery `+` → Bussmann 285 Breaker → Positive (`+`) Bus Bar.
  * **Black (`−`):** Battery `−` → SmartShunt → Negative (`−`) Bus Bar.
  * **Inverter DC:** Bus Bars → through `70 × 70 mm` front plate window → MultiPlus DC studs.
* [ ] **`(5)` Final Close-Out:** Mount **GX Touch 50** + bezel (`P9`) in back panel, install the **10 Front-Panel Ports** and branch wiring, and secure the **Top Lid Panel**.
