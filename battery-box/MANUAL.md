# 4Runner Electronics Box: Build Manual (v12s)

Step-by-step assembly of the v12s box: the frame of a 25 in Goose Gear IceBox 1.3 cut down to 282 mm tall, holding a MultiPlus 12/1200-class inverter and two Victron SuperPack 60Ah, with the charge gear on a printed plate and one Bussmann 285 breaker over each battery. Every diagram is rendered from the CAD model (`cad/cage.py`, variant `v12s`), so what you see is what the STLs produce. Parts placed in a step are shown in colour; parts already in place are grey. The front of the box, with the ports, is on the right in every picture.

Outer size: **635 × 487 × 282 mm (25.0 × 19.2 × 11.1 in)**. Loaded weight about 42 kg: frame 15, batteries 15, inverter 8, prints and gear 4.

**Before you start, read these two rules.** They are why every fastener in this manual is reachable.

- The IceBox panels sit in the rails' centre slots, so a rail's top and bottom slots are taken. Every tie to the frame is a horizontal 1/4-20 into a rail's **inner-face slot** through a **drop-in T-nut**, which can be added after the frame is closed.
- There is no loose nut inside the assembled box. Printed parts carry heat-set inserts; the only nuts are the T-nuts in the rails and the lap-joint nuts on parts that are bolted together on the bench first.

---

## 1. What you need

### 1.1 From the second IceBox 1.3 (25 in model)

| Part | Use | Cut |
|---|---|---|
| 8 corner cubes | the box's corners | none |
| 4 width rails, 436.6 mm | front and back, top and bottom | none |
| 4 depth rails, 584.2 mm | sides, top and bottom | none |
| 4 height rails, 508 mm | corners | **cut to 231.2 mm**, one end, re-tap 1/4-20 |
| 2 side panels | the box's sides | cut to 237 mm tall |
| perforated rear panel | the box's back (against the main IceBox) | cut to 237 mm tall, slots and all |
| one side-panel offcut (635 × 277) | the box's **front panel** | cut to 443 × 237, then the port holes |
| top panel | the lid | none |

Measure an uncut width rail before cutting anything: it should read 436.6 mm. If it does not, the cubes are not 25.4 mm and every number below shifts by the same amount; re-run the model with the real cube size.

### 1.2 Printed parts

All files are in [`stl/v12s/`](stl/v12s/). Click a link, then **Download** on GitHub's file page, and open the file in Bambu Studio (File → Import). Or clone the repo and import the folder. Material for everything: **PETG or ASA**, never PLA (the box sits in a closed truck). 0.2 mm layers, brim on every part.

| Part | Qty | File(s) | Orientation on the bed | Walls / infill | Notes |
|---|---|---|---|---|---|
| Battery tray | 2 | [tray_0](stl/v12s/print_tray_battery_0.stl), [tray_1](stl/v12s/print_tray_battery_1.stl) | flat, floor down | 5 / 40 % (100 % floor is cheap insurance) | 255 × 167 × 36. They differ only in which end carries the bracket pads: tray 0 at the back, tray 1 at the front |
| Tray rail bracket | 4 | [00](stl/v12s/print_tray_rail_bracket_00.stl), [01](stl/v12s/print_tray_rail_bracket_01.stl), [10](stl/v12s/print_tray_rail_bracket_10.stl), [11](stl/v12s/print_tray_rail_bracket_11.stl) | as modelled, vertical leg down | 5 / 50 % | 0x fit tray 0 at the back rail, 1x fit tray 1 at the front rail |
| Breaker drop shelf | 2 | [shelf_0](stl/v12s/print_breaker_shelf_0.stl), [shelf_1](stl/v12s/print_breaker_shelf_1.stl) | **on its side**, the 130 mm edge vertical: every wall then prints upright, no supports | 4 / 40 % | 130 × 168 × 243, ~400 g each. Never flat: the leg would be 189 mm of overhang |
| Bus shelf plate | 3 | [0](stl/v12s/print_bus_shelf_0.stl), [1](stl/v12s/print_bus_shelf_1.stl), [2](stl/v12s/print_bus_shelf_2.stl) | flat | 4 / 30 % | 177 × 110 × 34. Plate 2 has the front wall and bolts into the front rail |
| Inverter plate tile | 6 | [00](stl/v12s/print_plate_inverter_tile_00.stl), [01](stl/v12s/print_plate_inverter_tile_01.stl), [10](stl/v12s/print_plate_inverter_tile_10.stl), [11](stl/v12s/print_plate_inverter_tile_11.stl), [20](stl/v12s/print_plate_inverter_tile_20.stl), [21](stl/v12s/print_plate_inverter_tile_21.stl) | flat on the face | 4 / 30 % | 179 × 140 × 6. First digit = column from the back, second = row from the bottom. Pilot holes for every unit are in them |
| Plate spline | 6 | [v1_85](stl/v12s/print_plate_inverter_spline_v1_85.stl), [v1_149](stl/v12s/print_plate_inverter_spline_v1_149.stl), [v1_213](stl/v12s/print_plate_inverter_spline_v1_213.stl), [v2_85](stl/v12s/print_plate_inverter_spline_v2_85.stl), [v2_149](stl/v12s/print_plate_inverter_spline_v2_149.stl), [v2_213](stl/v12s/print_plate_inverter_spline_v2_213.stl) | flat | 3 / 100 % | 60 × 18 × 3, all identical: print six of one |
| Inverter post | 2 | [post_0](stl/v12s/print_post_inverter_0.stl), [post_1](stl/v12s/print_post_inverter_1.stl) | **on a side** | 5 / 50 % | 254 × 24 × 18. Mirror pair: 0 at the back rail, 1 at the front |
| Post clip | 2 | [clip_0](stl/v12s/print_post_clip_0.stl), [clip_1](stl/v12s/print_post_clip_1.stl) | as modelled | 5 / 50 % | 40 × 24 × 28, mirror pair |

About 2.5 kg of filament, 35 hours. Pictures of each part are in [section 4](#4-the-printed-parts).

### 1.3 Hardware

| Item | Qty (buy) | Where it goes |
|---|---|---|
| Drop-in (roll-in) 1/4-20 T-nuts for 1 in 10-series slot | 18 (20) | every tie into a rail's inner slot |
| 1/4-20 × 3/4 in flat-head (countersunk) screws, stainless | 18 (20) | with the T-nuts: trays 4, brackets 4, post sills 2, clips 2, bus shelf front wall 2, drop-shelf hangers 4 |
| M4 heat-set inserts (5.6 mm pilot) | 32 (40) | tray pads 4, tray inboard walls 6, tray wall tops 4, plate bottom band 6, post tops 2, Cerbo 4, Orion 4, Garmin 2 |
| M4 × 10 button-head screws | 32 (40) | into those inserts |
| M4 × 16 screws + nylock nuts | 13 (15) | lap joints, bench only: bus shelf laps 4, plate laps 9 |
| M5 heat-set inserts (6.4 mm pilot) + M5 × 12 screws | 8 (10) | MPPT 4, bus bars 4 |
| M6 heat-set inserts (8.0 mm pilot) | 10 (12) | inverter keyholes 4, breakers 4, shunt 2 |
| M6 × 16 pan-head screws | 10 | inverter keyholes (left 2 mm proud), breakers, shunt |
| CA glue | | the six splines, which locate only |
| 1 in cam straps, 1.5 m | 2 | one per battery through the tray's floor groove |

Plus the electrical parts on the component list in `components.md`: MultiPlus, two SuperPack 60Ah, two Bussmann 285060F breakers, two 5-stud bus bars, SmartShunt, MPPT 100/30, Cerbo GX, Orion XS, Garmin PowerSwitch, two L14-30 panel inlets, two SB50 and one SB175 panel inlets, three 12 V and two USB sockets, and the cable in section 3.

### 1.4 Tools

Hex keys 2.5, 3, 4 and 5 mm plus 5/32 in for the 1/4-20 flat-heads; a soldering iron with insert tips; caliper and a small square; a non-ferrous mitre blade or bandsaw, a disc sander or mill file; the 1/4-20 tapping set from the README's rail-cutting guide (HSS spiral-point tap, T-handle, guide block, fluid); a 6 mm and a 60 mm hole saw and a step drill for the front panel ports; crimper and heat gun for the lugs.

---

## 2. Bench work

Everything in this section happens before the box is assembled, where nuts, clamps and the soldering iron are easy to use.

### 2.1 Cut and tap the height rails

Follow the README's [cutting and tapping guide](README.md#rail-cutting). Four cuts, 508 → 231.2 mm, one end of each rail only; tap the cut end 1/4-20, 30 mm deep. The four 276.8 mm offcuts are your tapping practice. Dry-fit the bare frame and check the diagonals.

### 2.2 Cut the panels

The two side panels and the perforated rear panel cut to 237 mm tall. The front panel comes from one side-panel offcut: 443 × 237. Its port holes, measured from the panel's **inboard** edge (the edge toward the main IceBox) and its bottom edge, hole centres:

| Port | From inboard edge | From bottom | Hole |
|---|---|---|---|
| L14-30 shore inlet | 39 | 50 | 60 mm |
| L14-30 inverter outlet | 39 | 120 | 60 mm |
| 12 V socket | 39 | 175 | 29 mm |
| SB50 solar inlet | 92 | 40 | 48 × 37 rectangle |
| SB50 alternator inlet | 92 | 96 | 48 × 37 rectangle |
| USB socket | 92 | 140 | 22 mm |
| USB socket | 92 | 173 | 22 mm |
| 12 V socket | 124 | 135 | 29 mm |
| 12 V socket | 124 | 175 | 29 mm |
| SB175 inlet for pack2 | 247 | 88 | 26 × 56 rectangle |

These are the model's positions, measured from the panel's inboard edge (box y 462) and its bottom tongue edge (box z 22); the two outer-column sockets clear the inverter-plate post behind them by 2.5 mm, so drill those two exactly.

### 2.3 Inserts

Set every insert with the iron before anything is assembled; the table in 1.3 says where. Pilot holes are printed; the plate tiles print all pilots at 4.6 mm, so drill those to 5.6 (M4), 6.4 (M5) or 8.0 (M6) first.

### 2.4 Bus shelf sub-assembly

Join the three plates on their 20 mm floor half-laps with two M4 × 16 and nuts per lap, plate 0 at the back, plate 2 with the front wall at the front. Mount the two bus bars on their M5 inserts in the row nearest the inverter plate and the SmartShunt on its M6 inserts in the row nearest the trays, and make up the bus-bar-to-shunt link. The result is one 530 mm piece that drops into the box in step 7.

### 2.5 Inverter plate sub-assembly

Lay the six tiles out: columns 0, 1, 2 from the back, rows 0 (bottom) and 1 (top). Each column's two tiles join on a horizontal half-lap with three M4 × 16 and nuts; the columns join on vertical joints with the splines glued into their pockets on the inverter side. Set the inserts: six M4 in the bottom band for the bus shelf wall, and on the **column face** M5 × 4 for the MPPT, M4 × 4 for the Cerbo, M4 × 4 for the Orion, M4 × 2 for the Garmin; on the **inverter face** M6 × 4 for the keyholes, with M6 × 16 pan heads driven in and left 2 mm proud. Mount the MPPT (upright, terminals down), Cerbo, Orion (terminals down) and Garmin on the column face and dress their short leads. The inverter does not go on yet.

### 2.6 Breaker shelves

Set the two M6 inserts in each shelf plate. The breakers go on in step 6, in the box.

---

## 3. Assembly, step by step

Work from the top with the lid off. Every fastener is reached with a hex key from above or along the open column. The batteries go in at step 6, before the drop shelves cover them.

### Step 1: the frame

![Step 1](manual/img/01-frame.png)

Bolt the cubes and rails together with the IceBox's own corner-cube screws, but **before closing each face, slide its panel into the rails' centre slots** (step 2 is part of this step in practice). Drop 18 T-nuts into the inner-face slots as you go, or add them afterwards with the drop-in type: 2 in the top outboard depth rail for each drop shelf (4), 2 in the bottom outboard depth rail per tray (4), 2 in each width rail for the brackets, 2 in each bottom width rail for the post sills, 2 in each top width rail for the clips, 2 in the bottom front width rail for the bus shelf wall. Square the frame by its diagonals before the last cube screws are tightened.

### Step 2: the panels

![Step 2](manual/img/02-panels.png)

Perforated panel at the back, side panels each side, the solid front panel with its port holes at the front, each 3 mm into the rail slots top and bottom and into the cube bars at the sides. The lid stays off.

### Step 3: the posts

![Step 3](manual/img/03-posts.png)
![Step 3 from above](manual/img/03-posts-top.png)

Stand post 0 against the back width rail and post 1 against the front width rail, on the inboard side, slots facing each other. One countersunk 1/4-20 through each post's sill into the bottom rail's T-nut, head on the post's inner face.

### Step 4: the tray brackets

![Step 4](manual/img/04-brackets.png)
![Step 4 from above](manual/img/04-brackets-top.png)

Four L brackets bolt to the width rails **before** the trays go in, because each one's rail bolt faces where the tray will be. Brackets 00 and 01 at the back rail for tray 0, 10 and 11 at the front rail for tray 1; countersunk 1/4-20 into the inner slot, horizontal leg standing 36 mm up, ready for the tray pads. The front brackets stand beside their pad, not over it, because the front pads end 3 mm off the rail.

### Step 5: the trays

![Step 5](manual/img/05-trays.png)
![Step 5 from above](manual/img/05-trays-top.png)

Empty trays. Drop tray 0 into the outboard zone with room to spare, slide it to the back so its pads go under the bracket legs, then two M4 × 10 down through the legs into the pad inserts. Now the two countersunk 1/4-20s through the tray's outer wall into the outboard rail's T-nuts, from inside the empty pocket. Tray 1 the same at the front. Each tray is now tied to a width rail and the outboard rail.

### Step 6: the batteries

![Step 6](manual/img/06-batteries.png)

The batteries go in **before** the drop shelves: once a shelf is on, nothing 229 mm long can pass under its plate. Each SuperPack into its tray from above, strap through the floor groove and over the top with the buckle at the battery's end (the shelf plate will sit 6 mm above the battery, so keep the strap flat across the middle). No lugs yet: the leads go on in step 10.

### Step 7: breaker drop shelves

![Step 7](manual/img/07-shelves.png)
![Step 7 from above](manual/img/07-shelves-top.png)

For each battery: lower the empty shelf over it, hanger against the top outboard rail's inner face, foot on the tray's inboard wall beyond the battery; the plate clears the battery top by 6 mm and the hanger key path at 269 mm clears the lugs' height. Start all four screws by hand: two M4 × 10 down through the foot into the wall-top inserts, two countersunk 1/4-20 through the hanger into the rail's T-nuts. Tighten the foot screws first, then the hanger screws with the key coming along the open box over the empty plate. Then the Bussmann 285 down onto the plate's M6 inserts, studs toward the column.

### Step 8: the bus shelf

![Step 8](manual/img/08-bus.png)
![Step 8 from above](manual/img/08-bus-top.png)

Lower the sub-assembly into the column, lip against the trays' inboard walls. Three M4 × 10 per tray through the lip into the tray wall inserts, driven from the column side (heads in the column). Two countersunk 1/4-20 through the front wall into the front rail's T-nuts, from inside the column.

### Step 9: the inverter plate and clips

![Step 9](manual/img/09-plate.png)
![Step 9 from above](manual/img/09-plate-top.png)

Lower the plate with its units into the two post slots, column face toward the batteries. Its units clear everything on the shelf. The bottom band lands against the bus shelf's inboard wall: six M4 × 10 through that wall into the plate's inserts, from the column side, under the MPPT. Then the two clips: one M4 × 10 down into each post top, one countersunk 1/4-20 into the top width rail's T-nut; the clip's rail bolt sits 10 mm off the plate line so the key passes the plate's edge.

### Step 10: the inverter and the DC leads

![Step 10](manual/img/10-inverter.png)

Hang the MultiPlus on its four keyholes over the proud M6 heads, cable end toward the front, and snug the heads. Now the lugs: each battery's positive straight up to its breaker's battery-side stud, 4 AWG from the breaker's other stud over the shelf lip to the positive bus bar; negatives to the shunt's battery side; the MultiPlus DC leads through the plate's low window to the bus bars; AC in and out to the L14-30s beside it. Fit the breaker stud covers.

### Step 11: ports, pigtails and the lid

![Step 11](manual/img/11-ports-lid.png)

Port bodies into the front panel from inside, SB50 pigtails to the MPPT and Orion, Garmin outputs through the plate window to the sockets, the SB175 to the bus bars. The IceBox top panel goes on as the lid; with 17 mm between the lid and the truck roof, use flush pulls, not standing handles.

### Wiring

| Run | Cable | Protection |
|---|---|---|
| Battery + → its Bussmann 285 → + bus bar | 4 AWG, short | the 60 A breaker |
| Battery − → shunt → − bus bar | 4 AWG | |
| Bus bars → MultiPlus | 4 AWG, under 1 m | the breakers, 60 A each side |
| Bus → Orion output | 6 AWG | 60 A |
| Alternator → Orion input (SB50) | 6 AWG | 60 A at the start battery |
| Bus → MPPT battery side | 10 AWG | 40 A |
| Solar → MPPT (SB50) | 10 AWG | per string |
| Bus → Garmin PowerSwitch | 10 AWG | 60 A |
| Garmin outputs → sockets | 10 AWG per circuit | Garmin per-channel |
| Bus → Cerbo | 16 AWG | 3 A |
| pack2 umbilical (SB175) | 2 AWG | breaker in the pack |
| Shore in / inverter out | 12 AWG | the MultiPlus AC breaker |

---

## 4. The printed parts

| | |
|---|---|
| ![tray](manual/img/part-print_tray_battery_0.png) | ![bracket back](manual/img/part-print_tray_rail_bracket_00.png) |
| ![bracket front](manual/img/part-print_tray_rail_bracket_10.png) | ![drop shelf](manual/img/part-print_breaker_shelf_0.png) |
| ![post](manual/img/part-print_post_inverter_0.png) | ![clip](manual/img/part-print_post_clip_0.png) |
| ![bus shelf 0](manual/img/part-print_bus_shelf_0.png) | ![bus shelf 2](manual/img/part-print_bus_shelf_2.png) |
| ![tile 00](manual/img/part-print_plate_inverter_tile_00.png) | ![tile 21](manual/img/part-print_plate_inverter_tile_21.png) |
| ![spline](manual/img/part-print_plate_inverter_spline_v1_85.png) | |

---

## 5. The add-on pack (pack2)

Four more SuperPacks in a stacked all-printed cage on an SB175 umbilical. Its files are in [`stl/pack2/`](stl/pack2/) and its description and assembly order are in the README under pack2. Build the box first; the pack is a separate project with its own parts list.

---

Regenerate the diagrams after any model change with `cd cad && .venv/bin/python manual.py v12s`.
