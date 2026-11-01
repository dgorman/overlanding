# McMaster-Carr Fastener & Hardware Order (`v12s`)

This list covers every heat-set insert, machine screw, washer, T-nut, and adhesive used in [`MANUAL.md`](../MANUAL.md).

Two ways to order:
1. Click each link below and press **Add to Order** with the pack quantity shown, or
2. Copy the **Complete Order Pad Block** below into McMaster's **Order Pad** (on the cart page, click *"type or paste part numbers"* — one `part_number,pack_qty` per line).

---

## 1. Active `v12s` Bill of Materials

### Heat-Set Brass Inserts

| Packs to Buy | McMaster PN | Link | Needed | Where It Goes |
|---|---|---|---|---|
| 1 pack of 50 | `94180A353` | https://www.mcmaster.com/94180A353/ | **12** | **M4 × 0.7 standard (`7.9 mm` long)** for thick printed parts: tray inboard wall faces (`6`), tray wall tops (`4`), inverter post tops (`2`) |
| 1 pack of 100 | `94180A351` | https://www.mcmaster.com/94180A351/ | **16** | **M4 × 0.7 short (`4.7 mm` long)** for `6 mm` plates: inverter plate bottom band (`6`), Cerbo GX (`4`), Orion XS (`4`), Garmin upper hanger plate (`2`) |
| 1 pack of 25 | `94180A361` | https://www.mcmaster.com/94180A361/ | **18** | **M5 × 0.8 (`6.7 mm` long)**: MultiPlus keyholes (`4`), MPPT keyholes (`4`), Bussmann 285 breakers (`4`), bus bars (`4`), SmartShunt (`2`) |

### Screws & Washers (18-8 Stainless Steel)

**Why these lengths:**
- **Rail slot rule:** `screw length = plastic thickness under the head + 6 to 7 mm`. A `3/4 in` flat head in a `6 mm` countersunk wall leaves `13 mm` sticking out and bottoms out in a drop-in T-nut (`~7 mm` thread room), so all `6 mm` walls use **`1/2 in` flat heads**.
- **6 mm inverter plate rule:** Units sit on both faces of the `6 mm` plate with only `2–3 mm` of back clearance, so every screw is sized not to protrude through the opposite face.

| Packs to Buy | McMaster PN | Link | Needed | Where It Goes |
|---|---|---|---|---|
| 1 pack of 50 | `92210A537` | https://www.mcmaster.com/92210A537/ | **20** | **1/4"-20 × 1/2 in flat-head (82° countersunk)**: tray outer & end walls (`8`), bus shelf end walls (`4`), drop-shelf hangers (`4`), Garmin upper & lower hanger plates (`4`) |
| 1 pack of 25 | `92210A541` | https://www.mcmaster.com/92210A541/ | **2** | **1/4"-20 × 7/8 in flat-head (82° countersunk)**: post clips (`2`) into top width rails |
| 1 pack of 25 | `92949A541` | https://www.mcmaster.com/92949A541/ | **2** | **1/4"-20 × 7/8 in button-head**: post sills (`2`, plain hole) into bottom width rails |
| 1 pack of 25 | `92949A537` | https://www.mcmaster.com/92949A537/ | **8** | **1/4"-20 × 1/2 in button-head**: IceBox stack straps (`8`, `4 mm` plate + washer) into outer-slot T-nuts |
| 1 pack of 100 | `92141A029` *(verify)* | https://www.mcmaster.com/92141A029/ | **8** | **1/4 in flat washer, 18-8**: under the stack-strap button heads (`8`) |
| 1 pack of 100 | `92095A190` | https://www.mcmaster.com/92095A190/ | **12** | **M4 × 10 button-head**: bus shelf lip to trays (`6`), drop-shelf feet to tray wall tops (`4`), Garmin bracket to upper hanger (`2`) |
| 1 pack of 100 | `92095A189` | https://www.mcmaster.com/92095A189/ | **14** | **M4 × 8 button-head**: bus shelf inboard wall to inverter plate bottom band (`6`), Cerbo GX (`4`), Orion XS (`4`) |
| 1 pack of 25 | `92095A199` | https://www.mcmaster.com/92095A199/ | **2** | **M4 × 35 button-head**: down through each post clip into the post top insert (`2`) |
| 1 pack of 50 | `92095A208` | https://www.mcmaster.com/92095A208/ | **8** | **M5 × 10 button-head**: MultiPlus keyholes (`4`, with washer, left `3 mm` proud), Bussmann 285 breakers (`4`, with washer) |
| 1 pack of 50 | `92095A207` | https://www.mcmaster.com/92095A207/ | **4** | **M5 × 8 button-head**: MPPT 100/30 keyholes (`4`, left `3 mm` proud) |
| 1 pack of 50 | `92095A210` | https://www.mcmaster.com/92095A210/ | **6** | **M5 × 12 button-head**: bus bars (`4`) and SmartShunt (`2`, with washer) into bus shelf floor |
| 1 pack of 100 | `93475A240` | https://www.mcmaster.com/93475A240/ | **10** | **M5 flat washer (`5.3 mm` ID × `10 mm` OD)**: MultiPlus keyholes (`4`), Bussmann 285 breakers (`4`), SmartShunt (`2`) |

### Drop-In T-Nuts & Adhesive

| Packs to Buy | McMaster PN | Link | Needed | Where It Goes |
|---|---|---|---|---|
| 8 packs of 4 (32 nuts) | `6000N501` | https://www.mcmaster.com/6000N501/ | **32** (`24` inner-slot ties + `8` for the IceBox stack straps in the outer slots) | **1/4"-20 drop-in spring-loaded ball T-nut** for 1 in (10-series) / metric 25-series (`6.5 mm` slot) rail. *(End-feed nuts like `47065T142` cannot be added once corner cubes cap the rails; 80/20 equivalent is `#3382`.)* |
| 1 bottle | `74765A63` | https://www.mcmaster.com/74765A63/ | **1** | **Loctite 401 instant adhesive (`0.1 oz`)**: for the 8 inverter-plate splines and tacking the half-laps |

---

## 2. Complete Order Pad Block (Clean Build)

Paste into McMaster's Order Pad to order the entire active BOM at once:

```text
94180A353,1
94180A351,1
94180A361,1
92210A537,1
92210A541,1
92949A541,1
92095A190,1
92095A189,1
92095A199,1
92095A208,1
92095A207,1
92095A210,1
93475A240,1
92949A537,1
92141A029,1
6000N501,8
74765A63,1
```

### Non-McMaster Items
- **Added bottom front width rail (`436.6 mm`):** Goose Gear **Extrusion Frame Modification Kit x.31** (ordered 2026-10-30; same profile and anodize, pre-tapped). *(McMaster backup was `47065T101`, not needed.)*
- **Saw blade:** Diablo `D1084L` 10 in 80-tooth non-ferrous/plastics blade (ordered from Home Depot 2026-10-20).
- **Tapping tools:** Milwaukee SAE tap-and-die set (`1/4-20` plug tap + handle, bought at Home Depot 2026-10-20), used with the printed tap guide ([`stl/v12s/print_tool_tap_guide.stl`](../stl/v12s/print_tool_tap_guide.stl)) and cutting oil (Tap Magic Aluminum or WD-40).
- **Drop-shelf hold-down pads (`×2`):** `130 × 140 mm` adhesive-backed closed-cell EPDM foam (`1/16 in` firm or `1/8 in` soft).

---

## 3. Owner's Purchase History & Spares Log

<details>
<summary>Orders 1–3 already placed (click to expand)</summary>

### Still to Order
- **`6000N501,3`** (3 more packs of 4 drop-in T-nuts): 5 packs (`20` nuts) were bought in Order 2; the two Garmin hanger plates (`2026-10-31`) brought the total from `20` to `24`, and the four IceBox stack straps (`2026-10-31`, outer slots) to **`32`**.
- **`92949A537,1`** (`1/4"-20 × 1/2 in` button heads, pack of 25) and **`92141A029,1`** (`1/4 in` 18-8 flat washers, pack of 100, PN to verify): the IceBox stack straps (`8` each).

### Order 1 (Placed 2026-10-20)
```text
94180A353,1    M4 standard heat-set inserts, 7.9 mm, pack of 50 (active: 12 used)
94180A361,1    M5 heat-set inserts, 6.7 mm, pack of 25 (active: 18 used)
92095A190,1    M4 x 10 button head, 18-8, pack of 100 (active: 12 used)
92095A210,1    M5 x 12 button head, 18-8, pack of 50 (active: 6 used)
93625A150,1    M4 locknuts, pack of 100 (SPARE: lap bolts were dropped)
92095A226,1    M6 x 12 button head, pack of 25 (SPARE: nothing in v12s takes M6 inserts)
```

### Order 2 (Placed 2026-10-20)
```text
94180A351,1    M4 short heat-set inserts, 4.7 mm, pack of 100 (active: 16 used)
93475A240,1    M5 flat washers, 5.3 ID x 10 OD, pack of 100 (active: 10 used)
74765A63,1     Loctite 401 instant adhesive, 0.1 oz (active)
6000N501,5     1/4"-20 drop-in T-nuts, 5 packs of 4 = 20 nuts (active: need 3 more packs for 32: 24 inner-slot ties + 8 IceBox stack straps)
92210A540,1    1/4"-20 x 3/4 flat-head 82 deg, pack of 50 (SPARE: too long for 6 mm walls, bottoms out in rail; replaced by Order 3)
```

### Order 3 (Placed 2026-10-30: Per-Joint Screw Lengths)
```text
92210A537,1    1/4"-20 x 1/2 flat head 82 deg, 18-8, pack of 50: trays, shelf end walls, drop-shelf hangers, Garmin hangers (20 used)
92210A541,1    1/4"-20 x 7/8 flat head, pack of 25: post clips (2 used)
92949A541,1    1/4"-20 x 7/8 button head, pack of 25: post sills (2 used)
92095A189,1    M4 x 8 button head, pack of 100: shelf wall to plate band (6), Cerbo (4), Orion (4) (14 used)
92095A199,1    M4 x 35 button head, pack of 25: clip down into post top (2 used)
92095A208,1    M5 x 10 button head, pack of 50: MultiPlus keyholes (4), breakers (4) (8 used)
92095A207,1    M5 x 8 button head, pack of 50: MPPT keyholes (4 used)
```

</details>
