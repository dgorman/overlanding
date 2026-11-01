# 4Runner Electronics Box: Design History & Build Log

This document archives the chronological build log and earlier design iterations (`v2` through `v13`, plus the `v4` cube and `v6` bookshelf series) that led to the final **`v12s` + `pack2`** build.

For the active build, see [`README.md`](README.md) and the step-by-step [`MANUAL.md`](MANUAL.md).

---

## Build Log (Newest First)

| Date | Notes |
|---|---|
| 2026-11-01 | **Bus shelf: everything to the tray side** (user: the `−` bar sat right under the plate's cable window, where the inverter, Orion and Garmin leads come through and would rest on a bus bar). The `+` bar, SmartShunt and `−` bar now sit in one row along the tray side on a single stud line `23 mm` from the shelf's tray edge (bars `1 mm` off the lip, ears 16 in; shunt `4.5 mm` off it); the inboard band under the window is empty. Found on the way: the SmartShunt's two mounting slots are on its **stud line, 12.5 mm from the stud edge** of the 46 mm housing (STEP), not centred as modelled, which is why the printed shunt sat `15.5 mm` off the lip and the user asked for it `11 mm` closer; the model also had it base-up with the studs inboard (fixed: `HOLES["shunt_x"]`, `STEP_FLIP`). Reprint Plate 1; drill Plates 0 / 2 (`Ø 6.4`, same x, `23 mm` from the tray edge) or reprint. Bench 4 and Step 7 redrawn. |
| 2026-10-31 | **IceBox stack straps** (user: a `4 mm` bracket like the Goose Gear corner gusset, tying the box's 8020 to the IceBox's). The box stands rail on rail on the IceBox and both frames are the same MaxLite `25 mm` rail with bare outer faces, so the tie is a straight `60 × 46 × 4` strap across the seam on each bottom depth rail's outer face: two `1/4-20 × 1/2 in` button heads into drop-in T-nuts in the box rail's outer slot, two into the IceBox rail's under it; the upper pair are `2.4 mm` slots for the cube-on-cube seam gap. Four straps (`print_stack_strap_*`, one bed `plate_stack_straps.stl`, plus a DXF for aluminium), `70 mm` in from the cubes so they clear the IceBox's own gussets. Manual Step 11; 8 more T-nuts (outer slots), 8 button heads, 8 washers. |
| 2026-10-31 | **Garmin hanger runs to the bottom rail** (user: somewhere to tie the wiring): a second plate (`print_garmin_hanger_lower`) on the bottom inboard rail's inner slot, 1 mm under the upper one, both with cable-tie slots. 24 T-nuts now. |
| 2026-10-30 | **GX Touch 50** flush display in the back panel's inboard end (user), 30 mm behind it to the MultiPlus for the body and a right-angle plug; printed trim bezel (`print_touch_bezel`) over the perforations. Opening size to be taken from Victron's flush-kit template. |
| 2026-10-30 | **As built: 22.5 in deep, metric frame** (user: 2.5 in shorter after the test fit). Model set to the real frame (25 mm rails, 25.75 cubes, height rails 230.2, box 571.5 × 488.1 × 281.7); depth rails to be cut to 520.0. Bus shelf end plates unchanged (already printed), middle plate 132; Garmin moved onto a printed hanger plate from the top inboard rail, the user's idea (no room in front of the MultiPlus's cable end); tray corners notched for the proud cubes; panel tongues stop at the cubes; screw lengths per joint (order 3). Full audit with a slot ledger in [`manual/audit-2026-10-30.md`](manual/audit-2026-10-30.md). |
| 2026-10-30 | **The donor IceBox has no bottom front width rail** (user: the fridge opening). The parts list had assumed all 12 rails. One 436.6 mm rail must be added: a Goose Gear Extrusion Frame Modification Kit x.31 bar was ordered 2026-10-30 (same finish, pre-tapped; McMaster 47065T101 by the foot is the backup). 5 T-nuts and the front panel's bottom tongue live on it. |
| 2026-10-25 | **Trays snug and strapless** (user): pocket clearance 0.5 mm per side instead of 1 (1 mm per side would be zero and the battery would not drop in), and the strap groove and end-wall slots are gone since the drop shelf is the hold-down. Trays 242 long, no bridges at all now. |
| 2026-10-25 | **Trays and bus shelf bolt straight to the width rails; brackets gone; countersinks fixed** (user: why not bolt the trays to the rail directly, and why does the shelf stop short of the rail?). Each tray now butts its width rail and takes two countersunk 1/4-20 through its end wall; the bus shelf runs rail face to rail face with two 1/4-20 through each end wall; the four L brackets, their pads and inserts are gone (20 T-nuts, 20 flat heads, 12 long M4 inserts). While doing it: the 'countersinks' on the tray walls, brackets and shelf wall had been 13 mm counterbores placed 0.5 mm off the wall, in the air, so those holes were plain and the flat heads would have stood 4 mm proud against the batteries (the already-printed PLA trays have this: countersink them by hand or reprint). Now real 82° cones, and `--clash` probes every one at its face (16/16). Manual steps renumbered 1–10, placement and T-nut positions regenerated. |
| 2026-10-25 | **Tile cuts on one face per row.** The lower tiles had their lap rabbet on the front and their spline pockets on the back, so printed on either face they carried 18 mm bridges at the pockets (the Gemini review flagged it). Now every row's rabbets and pockets are on one face, alternating by row, with two splines per row per joint (8, on their own plate) placed clear of the laps. All six tiles: zero unsupported area. |
| 2026-10-25 | **Plate was missing the six bottom-band pilots** for the bus shelf wall's M4 bolts (the shelf wall had its holes, the manual said to set the inserts, but the plate's pilot list never collected them; found by a Gemini review of the exported code). Fixed, and `--clash` now pushes a pin through every plate pilot and reports any blocked one (24/24 open). |
| 2026-10-25 | **Drop shelf, second fit (user, after the reprint):** holes line up with the 285. (1) Still 2 mm of daylight over the battery: `shelf_drop=2` lowers the plate to 1 mm over the body top (the pad space); the pad in the model is now 1 mm. (2) The two plate holes were printed 8.0 mm for M6 inserts that were never ordered: now 6.4 mm for the M5 94180A361 inserts and M5 × 12 + washer that are in the McMaster order. (3) The 18 mm end gussets became full-length ribs (18 at the hanger, 5 at the lip): on its 130 mm edge the top pair of gussets was 162 mm² hanging in air and strung. Overhang scan 534 → 195 mm² (all that is left is the roofs of horizontal holes). |
| 2026-10-24 | **Breaker drop shelf fitted to the parts in hand.** (1) The printed shelf stood about 3/8 in off the battery: the SuperPack's 213 mm is to the top of its terminals, and its flat body top is at 208 (measured on the Victron STEP, 5 mm studs), so the plate drops 5 mm and its pad now sits on the body with no gap (`batt_body_h`, `shelf_pad` parameters). (2) The breakers are the **150 A 285150F-121-S** (same 285 body); the shelf's two holes were on the mirrored diagonal and did not fit, now lower-left to upper-right as in the series drawing. Reprint both shelves. |
| 2026-10-24 | **Plate layout (user):** the Garmin PowerSwitch moves to the plate's **inverter face**, turned 90°, above the cable window (x 480–555, z 145–270): 59 mm in front of the MultiPlus's cable end, 18 mm behind the socket bodies, so only its feed passes through the window and its outputs run straight to the ports instead of a bundle through the window. The MPPT, Cerbo and Orion become **one row** along the top of the column face (tops at 266; the Orion 11 lower so its lugs clear the tile lap), leaving the band over the shelf's bus bars and shunt open for lugs. The plate code now asserts every unit insert clears the tiles' lap band and that every unit has a hole pattern. Screw lengths in the bolting table set so nothing is proud on the far face (no nuts anywhere on the plate). |
| 2026-10-24 | **Plate pilots were blind from the column side** (user: no holes visible on the back of the plate): the pilot cut started 1 mm inside the plate and left a 1 mm skin on the column face under every unit. Now cut through (a 4 mm pin passes all 18 pilots in the model). Breaker stand-in rebuilt as the Bussmann 285 from the series drawing (flange, corner wells over the holes, stud insulators on the opposite diagonal, button, reset lever out of the outboard side); a pin through each drop-shelf hole passes the breaker's hole too. |
| 2026-10-23 | Bus shelf plate 1's lap ledge printed as strings: the floor half-lap's pocket was a 3 mm ceiling open at the plate edge, so the slicer bridged it 105 mm between the lip and the wall. The U-channel plates cannot print upside down (their walls would be in the air), so the **laps moved from the floor into the walls**: the floors butt, and the lip and the inboard wall each carry a 20 mm half-lap whose tongue is the outer half of the wall, standing on the bed from floor to wall top. No bridge, no overhang, no support on any plate. Plates 0, 1 and 2 all change (reprint 0 and 1). The code asserts the trays' lip bolts stay clear of the laps. |
| 2026-10-20 | Printed rail-end tap guide (`cad/tools.py` → `print_tool_tap_guide.stl`) replaces the bought guide block; manual and tool list say the Milwaukee tap set is usable with chip clearing. |
| 2026-10-20 | Drop shelf lowered onto a 3 mm foam pad on the battery: it is now the battery hold-down (user's idea); straps optional. |
| 2026-10-20 | Lap bolts dropped from v12s (their nuts landed under the shunt, bus bars and plate units): the shelf plates each bolt to the trays and the plate, the tiles are held by the units screwed across the laps and the splines. M4 × 16 and locknuts off the BOM. |
| 2026-10-20 | Fasteners: everything in a 6 mm part moves to M5 with a washer (inverter keyholes, breakers, shunt) because M6 inserts are longer than the plate; short M4 inserts for the plate's own units. First McMaster order placed. |
| 2026-10-20 | Manual: simple dimensioned drawing for step 3 (`cad/simple_steps.py`): plan with the two post positions in big numbers and a side view with the bolt height. |
| 2026-10-20 | Manual: **placement drawing and tables** from `cad/placement.py`: every part's position from the back-rail and outboard-rail faces, and the 18 drop-in T-nut positions along each rail. |
| 2026-10-20 | Manual: McMaster-Carr order list (inserts, screws, locknuts, T-nuts, tapping tools) with verified part numbers where confirmed. |
| 2026-10-20 | Assembly order corrected: batteries go in **before** the breaker drop shelves (a shelf covers the battery's middle; user caught it). Manual and diagrams renumbered. |
| 2026-10-20 | **Build manual** (`MANUAL.md`): rendered step diagrams from `cad/manual.py`, print list with STL links, hardware and tool lists, port hole positions, wiring table. |
| 2026-10-20 | Drop shelf made buildable: the leg's wall bolts now go down through a 15 mm **foot** on the wall top (they had been drawn through the leg itself), the leg carries on 24 mm above the plate as a lip, gussets moved above the plate (the battery is 6 mm under it), hanger countersinks on the inner face. Print-and-build section written. |
| 2026-10-20 | **Breakers are Eaton Bussmann 285060F-121-S** (60 A, 48 V, IP67, M6 studs, 81.3 × 48.1 × 31.5 + 6.4 button): low enough to sit on a **drop shelf over each battery**, hung from the top outboard rail and standing on the tray wall, 13 mm under the lid. Breakers leave the plate face. |
| 2026-10-20 | The donor IceBox turned out to be the **25 in model**: v12s is now 635 deep with its depth rails **uncut**; only the four height rails are cut and tapped. Interior unchanged, clash-clean. |
| 2026-10-18 | **README restructured around the v12s build**: the build, its zones, electrical, IceBox-sourced parts, rail cutting, fasteners, assembly order, printing notes and pack2 at the top; every earlier version collapsed under Reference designs. |
| 2026-10-18 | `v12s_pack` view: v12s on the IceBox with pack2 on the floor 80 mm in front of its port face (umbilical side toward the box), to see the two together. |
| 2026-10-18 | **pack2:** stacked 2 × 2 SuperPack add-on pack for v12s (325 × 314 × 572, all printed, bus + breaker on a top shelf, SB175 in its back panel); v12s front panel gets the SB175 umbilical inlet in front of the bus column. |
| 2026-10-18 | Tapping tools BOM added to the rail-cutting guide (spiral-point 1/4-20 HSS tap, T-handle, guide block, fluid). |
| 2026-10-18 | **v12s is the build.** MultiPlus-II order cancelled; height rails cut to 231.2 (282 − two 25.4 cubes). Depth rails were to be cut to 569.2 until the donor turned out to be the 25 in box, which needs no depth cut. |
| 2026-10-17 | **Rail cutting and tapping guide** added (cut lengths per variant, cut-order so the height rails are practice, tap without drilling, dry-fit) with the warning that cutting the depth rails for v12s rules out the MultiPlus-II. |
| 2026-10-17 | v12s: **front panel from a side-panel offcut.** The IceBox's side panels are solid; cut to 237 each leaves a 762 × 277 offcut, and the front needs 443 × 237, so the ports go straight through solid sheet. No printed front, no bezel; the slotted rear offcut is spare. |
| 2026-10-17 | (superseded the same day) v12s: front panel from the slotted offcut (the IceBox rear panel is 514 tall inside its rails; the box's back takes its bottom 237, the front its next 237, with 40 to spare). The ports cannot go through slots, so the offcut gets a 139 × 210 opening and a **one-piece printed port bezel** (153 × 227 × 6, 5 M4 countersunk from outside into inserts) carries them behind it. The two-tile printed front panel is gone from v12s. |
| 2026-10-17 | Plate mounting: pilot holes for every column-face unit's inserts in the v12s tiles (upright MPPT pattern transposed, 7148 pattern added); fastener table in the README. |
| 2026-10-17 | v12s only: back panel drawn with the IceBox's slot pattern; trays lose the unused inner-end pads and the optional floor holes (left over from the 2 × 2 layout); viewer gains a **sub-assembly legend** (frame, each tray, bus shelf, inverter plate, posts, ports) alongside the material legend. |
| 2026-10-17 | Breakers moved high onto the plate's column face (reachable from above), shunt down to the shelf, cable window lowered to bus level; corner cubes, side panels, perforated back panel and lid taken from the second IceBox; front panel printed in two lapped tiles. |
| 2026-10-17 | **Assembly order written up** (bench sub-assemblies, then posts → brackets → trays → shelf → plate → inverter → batteries). Shelf plates joined on half-laps; post clips widened with the rail bolt off the plate line; drop-in T-nuts specified. |
| 2026-10-17 | Inverter shims removed (it hangs on the plate); tray-to-shelf joint reworked: M4 inserts in the trays' inboard walls, bolts through the shelf lip from the column side; v12s drawn stacked on the IceBox. |
| 2026-10-17 | **v12s:** the 12/1200 + two 60Ah box cut to 620 deep (24.4 in), charge gear stacked on the plate; v13 shown to be depth-bound at 762 by the 200Ah pair and the II. |
| 2026-10-14 | MultiPlus-II 12/3000 ordered: v12 now carries it with the two SuperPack 60Ah (60 A bank limit, charger set to 60 A); the 12/1200 build kept as `v12_1200`. Upgrade to v13 = batteries and trays only. |
| 2026-10-13 | v12 interior replaced by v13's (two SuperPack 60Ah at the ends of the outboard zone, 12/1200 on the long plate): upgrade = swap trays and inverter. 60 A phase-1 limit noted. |
| 2026-10-13 | **v12 moved into v13's form factor** (282 tall, ports on the inboard half, posts 254 + 28 mm clips) so a v12 build upgrades to v13 by reprinting the trays, bus shelf and inverter plate. Upgrade path written up in the v12 section. |
| 2026-10-13 | v13: floor tied in (shelf to the front rail, tray L brackets to both width rails, Garmin onto the plate instead of a loose floor pad); cable window in the plate's front tile. |
| 2026-10-13 | **v13:** MultiPlus-II 3 kVA + two Lithium Smart 200Ah in the IceBox footprint at 11.1 in (user's 1500 W load; height was the only dimension allowed to grow). Inverter on its long side along the inboard side, batteries end to end outboard, bus column between. Victron mounting orientation to confirm. |
| 2026-10-12 | **v12 made the primary candidate.** Printing notes (materials, orientation, inserts, lifting load path) added to its section. |
| 2026-10-12 | v12: Garmin moved to the front panel beside the external ports it feeds; the Orion joins the MPPT on the inboard wall and the Cerbo goes there too (fits with 41 mm spare). The inverter plate's top corners are notched around the post clips. |
| 2026-10-12 | v12 inverter plate raised to 250 mm so the MultiPlus's top tabs bolt to it: the plate stands 21 mm above the 229 mm posts in the rail-free middle, with its top corners notched around the post clips. Cerbo laid flat on a pedestal, Orion turned lugs-to-mount. |
| 2026-10-12 | v12 lowered from 279 to **254 mm (10 in)**: the top rails only run along the edges, so the MultiPlus and batteries in the middle are limited by the lid, not the rails. Ports re-stacked in three columns and the MPPT mount shortened to stay under the rails. |
| 2026-10-12 | v12 rail ties reworked: the IceBox's panels live in the rails' slots, so L tabs on the rail tops cannot work; every tie is now a horizontal bolt into the rails' inner slots, and the panels sit in the slots inside the bar envelope. |
| 2026-10-12 | **v12:** v5's IceBox-footprint frame at half height (762 × 487 × 279), not card based: one-layer 2 × 2 batteries, bus shelf in the column, MultiPlus on its long side on a fixed plate, Orion + ports inside the front panel, MPPT upright + Garmin inside the side panel. |
| 2026-10-07 | Fastener rule written down: no loose nuts inside the assembled box; the deck ties' M4s go into inserts in the deck, the column floor's lip screws into inserts; nuts only on bench sub-assemblies (MultiPlus bolts, card laps, panel ports). |
| 2026-10-07 | v11 deck fasteners audited: the front column post's ledge now overhangs the post so its hole lands inside the extension plate (it was 3 mm outside); the script asserts every deck hole is at least 4 mm inside its plate and the report counts them. |
| 2026-10-07 | v11 ports moved to the front face: the width lets the front card sit against the inboard rail, leaving a 78 mm strip beside it for every port in one column, so the box no longer depends on which side the IceBox is on. Front column-post ledge shortened to clear the front card's SB50 pigtails. |
| 2026-10-07 | v11 widened to 386 (4.0 in pedal room): MultiPlus 47 mm off the batteries, its SB175 back on the card's rear face mating up (card 444, no notch). Deck-to-post connection made real: ledges are now part of the column posts (gusseted, M4 insert) and two cleats under the stack-half joint hold the extension's inner edge. |
| 2026-10-06 | v11 deck: the stack half now runs post to post on the same back and front lines as the extension, as two splined plates, so it sits on the whole of the back legs' boss tabs. |
| 2026-10-06 | v11 column floor: a continuous full-width 6 mm floor from the tray wall to the inverter card's posts, two halves butted at the middle, each bolted at both ends (replaces a lap-joined pair, then a pair of short brackets). A deck change made by mistake from the same screenshot was reverted. |
| 2026-10-06 | v11 stack plate extended forward to the extension's line over the front legs (back-leg tabs lengthened so it still prints). |
| 2026-10-06 | v11: deck windows removed (they would pin the leads); lug room raised 14 → 30 mm for 4 AWG lugs, deck to 500, legs in three segments; pack inlet follows. |
| 2026-10-06 | v11 deck extended over the inverter column (plate on the column posts' ledges, 32 mm notch along the card for the SB175 and leads); breaker moved onto it. Inverter card now lifts after the plate is unbolted. |
| 2026-10-06 | v11 inverter mounted **flush** on a 264 mm 2 × 2-tile column card (posts' slots 7 mm so the body clears their lips), bracket modelled above it, SB175 moved above the bracket. |
| 2026-10-06 | v11 stretched to the 17.25 in limit: 437.8 deep, +4 behind the front card's SB50s, +3 in front of the MPPT. |
| 2026-10-06 | v11: round ports in one column at the IceBox end of the wall zone (panel stiffness); inverter card moved to 35 mm off the batteries; the inverter's SB175 comes back **lying above the MultiPlus on the card face, mating forward**, with the column card raised to 480. |
| 2026-10-06 | **v11:** v10 with the cards swapped. MultiPlus lengthwise in the 163 mm column (147 needed), charge gear on the front card: **431 deep (17.0 in)**. Ports on the pedal-side wall beside the front card, single column. |
| 2026-10-06 | v10 ports: after two wrong turns (inboard side behind the column card: too tight; front strip: too narrow for L14-30s) they sit on the **pedal-side wall beside the inverter, backs toward it**. Frame widened 12 mm to 365 so the SB175 fits sideways; inverter card on 48 / 0 posts. L14-30s restored. Pedal room now **123 mm (4.8 in)** inside the IceBox face (the 5 in brief; v9 at 353 gives 5.3 in). Pedal-room dimension added to the overlay. |
| 2026-10-06 | Breaker is the **Blue Sea 7148** (187-series surface mount 150 A), 87.4 × 59 × 45.6 mm from the datasheet, not the 67 × 43 × 66 guess. Decks re-laid for it: bus bars along the depth between smaller 100 × 55 hand windows, breakers along the depth at the deck edges, SmartShunt across, Garmin on edge on a printed angle (v9). `cad/step/BlueSea-7148.step` is wired in: drop the file from bluesea.com there and the script uses it instead of the studded stand-in. |
| 2026-10-05 | **v10:** two batteries in one stack, charge card lengthwise in the freed column along the inboard wall (rear-face SB50s, rail-footed half-lapped posts), ports above the MultiPlus: **454 deep (17.9 in)**. Tradeoff documented: 120 Ah and the inverter limited to ~700 W continuous by the two SuperPacks' 60 A. Add-on pack modelled in the v10 scene, then made **all printed** (325 × 314 × 312: 30 mm half-lapped corner posts on the tray pads, 6 mm panel tiles, 4-tile lid) with one Blue Sea 187 150 A breaker and no bus bars; the bar-frame version stays behind `--pack=bars`. Blue Sea 187 (67 × 43 × 66) is now the breaker everywhere. |
| 2026-10-05 | Deck connector row removed: pigtails lugged at the bus bars, SB175 on the inverter card is the only inverter-side plug; Garmin moved onto the deck with a PP45 at its front edge; inverter card closed up to 20 mm from the deck; charge-card pigtails routed in the 18 mm outboard chase. **568 deep (22.4 in).** |
| 2026-10-05 | MPPT moved to the top of the charge card and the panel connectors (sockets, L14-30 in/out, SB50 inlets, now modelled) gathered in the bottom band behind the card's empty zone, so the front grace drops from 45 to 10 mm: **618 deep (24.3 in)**. Garmin to the inverter card's rear face with its own SB50 feed + PP45. v10 full-length-deck study built, reviewed and removed. |
| 2026-10-05 | Cards reworked for printing: guide posts stood 18 mm in from the rails, so each card is 249 wide and prints as **two** 249 × 234 tiles with a 24 mm half-lap (glued + 3 × M4) instead of four spline-joined tiles. Every tile prints flat with its rabbet up, no supports. Inverter card is exactly the MultiPlus width; Garmin PowerSwitch turned 90° beside the Orion; SB50 row re-pitched to 47 mm. |
| 2026-10-05 | Card backs made flush: splines recessed into 3 mm pockets, MultiPlus backing plates replaced by fender washers (the "bumps" on the card backs). Back bracket pads moved off the strap slot. |
| 2026-10-05 | Rack connections reworked after "how do the supports connect?": leg feet (which collided with the rails and each other, and bolted to the plate) replaced by foot tabs screwed to tray corner pads; tenon joints replaced by a half-lap that the shelf screw pins (the old shelf screw landed in the tenon pocket); deck holes moved into leg boss tabs (they were 1 mm from the deck edge); deck tied to the corner bars; crosswise strap slots (blocked by the touching trays) turned lengthwise with the buckle in front. `cage.py v9 --clash` reports solid overlaps between parts. |
| 2026-10-05 | Trays get L tabs onto the bottom rails (side tabs integral, back brackets printed) so the box lifts as one unit with the batteries in; guide-post feet fixed to sit on the rails instead of 6 mm above them (the floor panel stops at the rail). Dimensions corrected to 661 × 353 after the 6 mm tray walls. |
| 2026-10-05 | Garmin outputs get a PP45 block on the charge card's front face; rack beefed up (6 mm tray walls, 30 mm lips, M6 to the plate, shelves screwed to the legs, cam straps); full assembly procedure written. |
| 2026-10-05 | v9 cards cut down 50 mm (444 tall) so the upward-facing connector stacks leave 60 mm of cable room under the lid. |
| 2026-10-05 | Card connectors moved to the top of each card's rear face (wire-bend room below); the charge card's inlet SB50s join the rear row. |
| 2026-10-05 | Each card gets its own fixed Andersons on its rear face, mating face up (pigtails lift off before the card); deck extended 40 mm forward with its halves pointing at the cards; 657 mm deep. |
| 2026-10-05 | Real Anderson SB175/SB50 housings (Anderson STEP files) on the deck, mating axis across the box so the flying halves unplug sideways from above. Rack legs split in two with an M4 boss for the deck; deck in two halves; shelves trimmed: every v9 part now fits the P1S bed. Printing and assembly table added. |
| 2026-10-05 | v9 depth opened up for wiring: 70 mm deck-to-inverter-card, 45 mm card-to-ports; 636 mm (25 in) deep. Inverter run is 4 AWG as built. |
| 2026-10-05 | **v9:** fixed bus deck on the battery rack with Anderson receptacles; two cards that unplug and lift out alone; 539 deep. Cable sizes from the Victron manuals: 2 AWG + 150 A for the 12/1200, 6 AWG for the Orion, 10 AWG for the MPPT. |
| 2026-10-05 | All cards printed as solid 6 mm tiles (same as under the inverter) so units can be shifted and re-drilled; cables route under the cards, not through them. |
| 2026-10-05 | MultiPlus hole pattern corrected to the 374.6 mm body (the 406 figure includes the bracket); card solid under the inverter footprint for micro-adjustment. |
| 2026-10-04 | Mounting detail: bosses + heat-set inserts at every unit's hole pattern on the printed cards, M6 through-bolts with backing plates for the MultiPlus; fastener list in the report. |
| 2026-10-04 | **v8:** cards turned across the box (three: inverter, charge, distribution). 598 deep, 6.5 in shorter than the IceBox; v7 kept. |
| 2026-10-04 | v7: port wall brought in to the gear (642 deep, 4.7 in shorter), height kept at 559; cards are printed 2 × 2 ribbed tiles; 12/1200 upright alone on its card, Orion + Cerbo on the distribution card. |
| 2026-10-04 | **v7:** 200Ah Smarts and MultiPlus-II shelved. Four SuperPack 60Ah in two touching stacks at the IceBox end, kit-bar cross-members, both cards lengthwise in front with the 12/1200 upright. 345 mm wide (5.6 in narrower). |
| 2026-10-04 | Cage right-justified against the IceBox (`align="right"`); noted that a single-card layout would reach 384 mm. |
| 2026-10-04 | Frame narrowed to 440 mm (sized from the Y stack, for bike pedals beside the box). `bookshelf60` checks the owner's SuperPack 60Ah in the 200Ah trays: fits with spacers. Dimension lines added to the viewer. |
| 2026-10-04 | Inverter back to the owner's MultiPlus 12/1200/50 (Victron STEP added); v6 column widens to 240 mm; 2 × 2 of 200Ah is now the main v6, two end to end is `bookshelf2`. MPPT STEP flipped terminals-down. |
| 2026-10-04 | Battery column now stands on the Goose Gear plate (floor cut away under it): +31 mm of height, 43 mm over the top lugs in the 2 × 2. Viewer fetches are cache-busted per publish. Victron STEP geometry replaces the grey boxes where Victron publishes a file. |
| 2026-10-04 | Asked about 4 × 200Ah: added the `bookshelf4` 2 × 2 variant with a six-leg printed rack; it fits with 15 mm end gaps and 11 mm over the top lugs, recommendation stays at 2 × 200Ah. Column widened to 192 mm for Victron's 20 mm vents by moving the Cerbo to the inverter card. |
| 2026-10-04 | Owner's IceBox 1.3 is the 30" (762 mm) model, not 25": v5 and v6 re-sized. v6 battery column becomes two Lithium Smart 200Ah end to end (400 Ah), no stack. `--column` / `--arrange` options added to compare batteries. |
| 2026-10-04 | **v6 draft:** cards turned 90° to run front to back along the inboard wall so a MultiPlus-II 12/3000 fits on its side; one column of two Lithium Smart 100Ah outboard with frame-mounted supports. `python cage.py bookshelf`. |
| 2026-10-04 | Named the parts: distribution card, inverter/charger card, battery bay. Battery supports noted as needing to be frame-mounted, not card-adjacent; left for the battery decision. |
| 2026-10-04 | MPPT and Cerbo on the dist card with the Garmin; upper card keeps only the Orion. v5 battery stacks justified to the side walls with a 145 mm channel. Checked the MultiPlus-II 12/3000 and 12/4k: neither fits (578 / 631 mm long) and four SuperPack 60Ah can only supply 120 A continuous, so the 12/800 stays. SuperPack weight corrected to 7.5 kg. |
| 2026-10-04 | **v5:** second variant in the same script: a stock IceBox 1.3 frame (635 × 487 × 559) with two upright battery stacks and the dist card at the front panel. Viewer gets a version switch. v4 tagged `cage-v4-cube`. |
| 2026-10-04 | **v4:** four batteries (three upright + one on its long side on a printed shelf), dist card moved to the front layer facing the sockets with the Garmin on it, lower card notched for battery cables, two spare bars as floor joists. |
| 2026-10-04 | **v3:** cube from 12 uncut bars (487.4 mm each way, 71 mm under the IceBox). Batteries end to end in depth instead of stacked; Garmin joins the upper card turned 90°. Lift clearances drop to 658 / 741 mm. |
| 2026-10-04 | Card guides were floating: replaced with printed posts bolted into the top and bottom rail T-slots. Panels moved to the outside of the bars (Goose Gear style), which also gains 12 mm of inside width and 6 mm of height. |
| 2026-10-04 | Ordered 4 more mod kits (8 total, 16 bars). Frame is now all kit aluminium with a cut plan; no printed rail. |
| 2026-10-04 | **v2:** re-laid out as a half-depth twin of the IceBox (317.5 × 487.4 × 558.8). Batteries stacked, MultiPlus on its side on a lower card, MPPT/Orion/Garmin on an upper card, distribution on a third card beside the batteries. v1 long-box layout kept in git history (`cad/cage.py` before this commit). |
| 2026-10-04 | Owner confirmed the list: 2 × SuperPack 60Ah, MultiPlus 12/800/35, MPPT 100/30 with Anderson solar ingress, Cerbo, Orion XS 12/12-50, SmartShunt, Garmin PowerSwitch, battery breakers, 6 AWG. Dropped the unidentified parts. Added the IceBox 1.3 to the model and switched the frame to kit bars + printed rails. |
| 2026-10-04 | Project started. Identified components from photos, pulled datasheet dims, built parametric CadQuery model with drop-in card, printed-part STLs, renders and web viewer. Four Goose Gear mod kits on order. |

---

## Reference Designs (Historical Iterations)

Nothing in the sections below is being built; these notes preserve the architectural trade-offs explored between `v4` (`cube`) and `v13` (`MultiPlus-II`). All variants remain runnable via `python cage.py <variant>`.

### v12 & v13: Full-Depth 30" IceBox Footprint (`762 × 487 × 282 mm`)

**v12 (reference, superseded by v12s): 11.1 in tall IceBox footprint, MultiPlus-II with two SuperPack 60Ah, batteries upgradeable to v13** (`python cage.py v12`, viewer "v12")

v5's idea (a second IceBox 1.3 frame, same width and depth as the 30" IceBox) cut down to **762 × 487 × 282 mm, 11.1 in tall**, 10.9 in below the IceBox deck. The parts in it only need 254 (the MultiPlus on its long side, 249 mm plus its plate; the top rails do not limit it because they only run along the edges), but the box is cut at **v13's height** so that the same frame, panels, lid, posts, clips and port strip carry a MultiPlus-II and two Smart 200Ah later. The inverter ends 31 mm under the lid, the batteries with their lugs 46. Nothing needs to lift out, so there are no cards, no deck, no legs and no shelves: lid off and every unit is in reach.

**v13: v12 one inch taller for a 1500 W AC load, MultiPlus-II 3 kVA** (`python cage.py v13`, viewer "v13")

Asked 2026-10-13: run a 1500 W AC appliance, keep the IceBox footprint, height may grow from 10 to 11 in, use the MultiPlus-II. Two things had to change, not one: four SuperPack 60Ah give 120 A continuous and a 1500 W load pulls about 130 A, so the battery changes too. **762 × 487 × 282 mm, 11.1 in**.

| Zone | What is there |
|---|---|
| Inboard side, full depth | the **MultiPlus-II 12/3000/120-50** (578 × 277 × 148, 19 kg) on its **long side**: 578 along the depth, 148 into the box, 277 tall on two 2 mm shims, back on a printed plate (3 × 2 tiles, 256 tall from z 21) that runs the depth in two v12 posts turned 90° against the width rails; cable end faces forward |
| Outboard side, full depth | two **Lithium Smart 12.8V/200Ah** (321 × 152 × 237, 20 kg each) end to end in trays with 6 mm floors and 1.5 mm pocket clearance; each tray prints as two halves on a 20 mm half-lap (bench bolts) |
| Column between, 110 wide | the bus shelf in three half-lapped plates **running to the front rail**: the two bus bars in the row under the MPPT and the SmartShunt in the row under the Cerbo |
| Plate's column face | MPPT upright, Cerbo, Orion and the Garmin low; the **two Blue Sea 7148 breakers high at the front** (z 175–234, 48 mm under the lid); a **67 × 78 cable window** low in the plate's front tile (x 645–712, z 40–118) |
| Front zone, 113 deep | the inverter's cable end and the port strip on the **inboard** half of the **printed** front panel |

---

### v9, v10, & v11: Unpluggable Card & Bus-Deck Series

**v9: v8 plus a fixed bus deck, so every card unplugs and lifts out alone** (`python cage.py v9`)

The problem with v8: the battery leads run under card 3, through card 2, up to the bus bars on card 1, so no card comes out without its neighbours. v9 moves everything that is wired to more than one card off the cards:

- **Bus deck.** A printed 6 mm plate bolted to the tops of the battery rack legs, at 468 mm, 91 mm under the lid. It carries both bus bars, the two battery breakers, the SmartShunt, and the mating halves of every card's connector along its front edge: an **SB175** for the inverter and three **SB50s** for the MPPT, the Orion and the Garmin/Cerbo feed. A hand window in the plate reaches the battery lugs below it.
- **Two cards, one plug each side.** The inverter card carries the MultiPlus 12/1200 and a single SB175 receptacle at the top of its rear face. The charge card carries the MPPT (at the top), the Orion and the Cerbo on its front face and five SB50 receptacles at the top of its rear face (MPPT, Orion, Cerbo, solar in, alternator in).
- **Dimensions:** **568 × 353 × 559 mm (22.4 in deep), 7.6 in shorter and 5.3 in narrower than the IceBox**, same height. ~58 kg.

```
frame bottom rails ──T-nuts──▶ tray L tabs ──▶ trays ──M4 insert──▶ leg foot tabs ──▶ lower legs
                                 │                                         │ half-lap + shelf M4
                                 ▼                                         ▼
                      lower batteries (strap)                  shelves ──▶ upper batteries (strap)
                                                                           │
                                                   upper legs ──M4──▶ bus deck ──M4──▶ deck ties ──T-nut──▶ frame corner bars
```

**v10: two batteries, 454 mm deep (17.9 in)** (`python cage.py v10`, viewer "v10")

Drop to two SuperPacks in **one stack** and the depth falls to **454 × 353 × 559 mm**, 12.1 in shorter than the IceBox and 4.5 in shorter than v9, at the same width and height, with the charge card turned lengthwise along the inboard wall in the freed column and the two displaced SuperPacks moved into an all-printed external add-on pack (`325 × 314 × 312 mm`).

**v11: v10 swapped, 438 mm deep (17.24 in)** (`python cage.py v11`, viewer "v11")

Swaps the cards from v10: the MultiPlus bolts flush onto the lengthwise column card beside the battery stack (264 mm card, 101 mm deep in a 163 mm column), while the MPPT, Orion, Cerbo, Garmin, and SmartShunt move to the front card (`437.8 × 386 × 559 mm`, meeting the 17.25 in Goose Gear plate access-port depth limit with 4.0 in of bike-pedal clearance).

---

### v7 & v8: Narrow 4-Battery Card Cages (`345 mm` Wide)

- **v7 (`python cage.py v7`)**: **642 deep (25.3 in) × 345 wide (13.6 in) × 559 tall**. Two touching stacks of two SuperPack 60Ah at the IceBox end, kit-bar cross-members, and two lengthwise cards in front (inverter card with MultiPlus 12/1200 upright; distribution card with breakers, bus bars, MPPT, Garmin, shunt, Orion, and Cerbo).
- **v8 (`python cage.py v8`)**: **598 deep × 345 wide × 559 tall**. Same battery bay as v7, with three cards turned across the box (inverter, charge, distribution) so the inverter only costs its 100 mm thickness in depth.

---

### v6 (`bookshelf`, `bookshelf2`, `bookshelf60`): Side-Mount Cards (`440 × 762 × 559 mm`)

Started as the way to fit a MultiPlus-II; both cards run front-to-back along the inboard wall (`694 × 494 mm`), sliding down between posts on the back and front width rails, with a 240 mm wide battery column outboard carrying either four Lithium Smart 12.8V/200Ah in a 2×2 rack (`bookshelf`), two 200Ah end-to-end (`bookshelf2`), or four SuperPack 60Ah in the 200Ah trays with spacers (`bookshelf60`).

---

### v4 (`cube`) & v5 (`icebox`): Early Card-Cage Layouts

| | v4 cube (`cage.py cube`) | v5 second IceBox (`cage.py icebox`) |
|---|---|---|
| Frame | 12 uncut kit bars, 487 × 487 × 487 mm | Stock 30" IceBox 1.3 frame, fridge slide removed: 762 × 487 × 559 mm |
| Inside | 437 × 437 × 431 | 711 × 437 × 502 |
| Batteries (4) | 3 upright + 1 on its long side on a shelf | 2 upright stacks of 2, one at each side wall, 145 mm channel between |
| Cards | lower (MultiPlus), upper (Orion, 171 tall), dist (423 tall, with MPPT + Cerbo + Garmin) tight behind the MultiPlus | same three; upper 242 tall; dist 494 tall pushed forward to the sockets |
| Mass | ~49 kg | ~63 kg |

![Cube against the IceBox](renders/cube/with-icebox.png)
![Cube, front iso](renders/cube/iso-front.png)
![IceBox variant against the IceBox](renders/icebox/with-icebox.png)
![IceBox variant, cards lifted](renders/icebox/cards-lifted.png)
