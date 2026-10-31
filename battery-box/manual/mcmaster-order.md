# McMaster-Carr order for the v12s box

Two ways to use this. Click each link and press **Add to Order** with the quantity shown, or copy the part-number block at the bottom into McMaster's **Order Pad** (the cart page has a "type or paste part numbers" box; one `part,quantity` per line). Quantities are the packs to buy, not the pieces needed; spares are built in.

Items marked **verify** are the right catalogue line but the exact length or type must be confirmed on the page before adding (McMaster's numbers change with length; a 1 in screw where 3/4 in is specified bottoms out in the rail slot).

## Inserts

| Qty | Part | Link | What it is |
|---|---|---|---|
| 1 pack of 50 | 94180A353 | https://www.mcmaster.com/94180A353/ | M4 brass heat-set insert, 5.25 mm hole. 12 needed (no bracket pads since 2026-10-25) |
| 1 pack of 25 | 94180A361 | https://www.mcmaster.com/94180A361/ | M5 brass heat-set insert, 6.7 mm long. 8 needed |
| 1 pack of 100 | 94180A351 | https://www.mcmaster.com/94180A351/ | M4 brass heat-set insert, **short**, for the 6 mm inverter plate. 16 needed (the 7.9 mm 94180A353 go in the thick parts) |

## Screws and nuts

| Qty | Part | Link | What it is |
|---|---|---|---|
| 1 pack of 100 | 92095A190 | https://www.mcmaster.com/92095A190/ | M4 × 10 button head, 18-8. 28 needed |
| (ordered) | 93625A150 | https://www.mcmaster.com/93625A150/ | M4 locknuts: no longer used (the lap bolts were dropped), keep as spares |
| 1 pack of 50 | 92095A210 | https://www.mcmaster.com/92095A210/ | M5 × 12 button head, 18-8. 18 needed: MPPT, bus bars, inverter keyholes, breakers, shunt |
| 1 pack of 100 | 93475A240 | https://www.mcmaster.com/93475A240/ | M5 flat washer, 18-8, 5.3 ID × 10 OD: under the inverter keyhole, breaker and shunt screws. 10 needed |
| 1 pack of 50 | 92210A540 | https://www.mcmaster.com/92210A540/ | 1/4"-20 × 3/4 in flat-head 82° hex-drive, 18-8. **Superseded by order 3**: too long for a countersunk head in a 6 mm wall (bottoms out in the rail). Spares. 92210A542 is the 1 in: too long |

## T-nuts

| Qty | Part | Link | What it is |
|---|---|---|---|
| 5 packs of 4 | 6000N501 | https://www.mcmaster.com/6000N501/ | 1/4"-20 drop-in spring-loaded ball nut for 1 in (10-series) rail. 24 needed since the Garmin hanger plates (2026-10-31), 20 bought: order one more pack. End-feed nuts (47065T142) will not do: the rails are capped by cubes |

## Rail (not from McMaster: a Goose Gear Extrusion Frame Modification Kit x.31 was ordered 2026-10-30 for the bottom front width rail, same finish, pre-tapped)

| Qty | Part | Link | What it is |
|---|---|---|---|
| (not needed) | 47065T101 | https://www.mcmaster.com/47065T101/ | 1 in × 1 in four-slot T-slotted framing rail (10-series profile, same as the IceBox): cut to 436.6 mm and tap both ends 1/4-20. Skip it if a Goose Gear mod-kit bar is left: that is this rail, already tapped |

## Tapping

| Qty | Part | Link | What it is |
|---|---|---|---|
| (not needed) | | | tap and handle: the Milwaukee SAE tap-and-die set bought at Home Depot covers them; the guide is printed (`stl/v12s/print_tool_tap_guide.stl`) |
| 1 | **verify** | https://www.mcmaster.com/products/tapping-fluid/ | Tap Magic Aluminum, 4 oz |
| 1 | **verify** | https://www.mcmaster.com/products/drill-bits/size~7/ | #7 jobber drill, only if a rail bore measures under 5.0 mm |

## Also

| Qty | Part | Link | What it is |
|---|---|---|---|
| 1 | 74765A63 | https://www.mcmaster.com/74765A63/ | Loctite 401, 0.1 oz: enough for the six splines and the laps |

## Order Pad block (the verified lines)

```
94180A353,1
94180A361,1
92095A190,1
93625A150,1
92095A210,1
92095A226,1
```

Ordered 2026-10-20 (order 1): 94180A353, 94180A361, 92095A190, 93625A150, 92095A210, 92095A226. The M6 screws and the M4 locknuts are spares now.

## Order 3 (placed 2026-10-30): the screw lengths the joints actually need

The 3/4 in flat heads bottom out in the rail: a countersunk head in a 6 mm wall leaves 13 mm sticking out and a drop-in nut has room for 7. Rule: screw length = plastic under the head + 6 to 7 mm.

```
92210A537,1    1/4"-20 x 1/2 flat head 82 deg, 18-8: trays, shelf end walls, drop-shelf hangers (16)
92210A541,1    1/4"-20 x 7/8 flat head: post clips (2)
92949A541,1    1/4"-20 x 7/8 button head: post sills (2)
92095A189,1    M4 x 8 button head: shelf wall to plate band (6), Cerbo (4), Orion (4)
92095A199,1    M4 x 35 button head: clip down into the post top (2)
92095A208,1    M5 x 10 button head: MultiPlus keyholes (4), breakers (4)
92095A207,1    M5 x 8 button head: MPPT keyholes (4)
```

The 3/4 in flat heads (92210A540) are spares. The M4 x 10s stay for the shelf lip (6), the drop-shelf foot (4) and the Garmin (2); the M5 x 12s for the bus bars (4) and shunt (2). The T-nuts: the frame is metric 25-series with a 6.5 mm slot, the same opening as the 10-series, so the 6000N501 drop-ins fit.

## Order 2 (placed 2026-10-20)

```
94180A351,1    short M4 inserts, 4.7 mm, pack of 100
93475A240,1    M5 washers, pack of 100
92210A540,1    1/4"-20 x 3/4 flat-head 82 deg, 18-8, pack of 50
74765A63,1     Loctite 401 instant adhesive, 0.1 oz
6000N501,5     drop-in spring-loaded nut for 1 in rail, 1/4"-20, packs of 4 (20 nuts)
```

That completes the McMaster list. The Diablo D1084L blade is ordered from Home Depot (2026-10-20). Still to get elsewhere: cutting fluid (WD-40 is fine), two 1/8 in adhesive-backed closed-cell foam pads 130 x 140 for the drop shelves, a #7 drill only if a rail bore measures under 5.0 mm.
