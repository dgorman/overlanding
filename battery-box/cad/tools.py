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
