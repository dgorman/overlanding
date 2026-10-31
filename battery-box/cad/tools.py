"""Printed shop tools for the build, written straight to stl/<variant>/ (not part of the assembly).
Run: .venv/bin/python tools.py v12s"""
import os, sys
import cadquery as cq
import cage

OUT = cage.STL
os.makedirs(OUT, exist_ok=True)

# Tap guide cap for the rail ends: a 46 x 46 x 32 block with a 25.3 mm square pocket 14 deep that fits snugly over the 25 mm rail end (the frame is metric 25-series),
# and a 6.5 mm bore through its centre in line with the rail's centre hole, so the 1/4-20 tap starts square and centred.
# Print standing on its pocket face (pocket up), 100 % infill, PETG.  Slide it on the squared rail end, oil the tap, tap through it.
cap = cq.Workplane("XY").box(46, 46, 32, centered=(True, True, False))
cap = cap.cut(cq.Workplane("XY").box(25.3, 25.3, 14, centered=(True, True, False)))                       # pocket over the rail end
cap = cap.cut(cq.Workplane("XY").circle(3.25).extrude(40).translate((0, 0, -1)))                           # tap bore, 6.5 mm
cap = cap.cut(cq.Workplane("XY").circle(6.0).extrude(6).translate((0, 0, 32 - 5)))                          # countersink to catch chips
cap = cap.edges("|Z").fillet(4)
path = os.path.join(OUT, "print_tool_tap_guide.stl")
cq.exporters.export(cap, path)
import plates; plates.reorient_file(path)   # pocket up, at the origin
print("wrote", path)

# Replacement 3-way corner cube (25.75 x 25.75 x 25.75 mm, matching the calipered Goose Gear IceBox 1.3 corner connector):
# The 3 rail-mating faces (+X, +Y, +Z) have a 4.75 mm solid web with a 6.8 mm (1/4-20) clearance hole at the centre (12.875 mm);
# the 3 outer faces (-X, -Y, -Z) have a 13.0 mm counterbore 21.0 mm deep so the three 1/4-20 button-head or socket-head screws
# seat against the inner webs without colliding at the cube's centre. Achiral: one print fits any of the 8 box corners.
C = 25.75
web = 4.75
cb_depth = C - web
mid = C / 2
cube = cq.Workplane("XY").box(C, C, C, centered=False).edges().fillet(1.5)
# 6.8 mm (r=3.4) through-holes on all 3 axes + 13.0 mm (r=6.5) counterbores from the 3 outer faces (x=0, y=0, z=0)
cube = cube.cut(cq.Workplane("XY").center(mid, mid).circle(3.4).extrude(C + 2).translate((0, 0, -1)))
cube = cube.cut(cq.Workplane("XY").center(mid, mid).circle(6.5).extrude(cb_depth + 1).translate((0, 0, -1)))
cube = cube.cut(cq.Workplane("YZ").center(mid, mid).circle(3.4).extrude(C + 2).translate((-1, 0, 0)))
cube = cube.cut(cq.Workplane("YZ").center(mid, mid).circle(6.5).extrude(cb_depth + 1).translate((-1, 0, 0)))
cube = cube.cut(cq.Workplane("XZ").center(mid, mid).circle(3.4).extrude(-(C + 2)).translate((0, -1, 0)))
cube = cube.cut(cq.Workplane("XZ").center(mid, mid).circle(6.5).extrude(-(cb_depth + 1)).translate((0, -1, 0)))
cube_path = os.path.join(OUT, "print_tool_corner_cube.stl")
cq.exporters.export(cube, cube_path)
plates.reorient_file(cube_path)
print("wrote", cube_path)
