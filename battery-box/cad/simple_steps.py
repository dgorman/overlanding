"""Simple dimensioned drawings for the manual's steps: plan view with the rails, the parts of that step in orange,
and a few big numbers.  Run: .venv/bin/python simple_steps.py v12s"""
import os, re, sys, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
import cage

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "manual", "img")
asm = cage.build()
bb = {ch.name: ch.obj.val().BoundingBox() for ch in asm.children}
B, D, W, H = cage.B, cage.out_D, cage.out_W, cage.out_H
X0, Y0 = cage.x_in0, cage.y_in0
ORANGE, GREY, BLUE = "#e4601f", "#c9cdd3", "#1a4fb3"


def arrow(ax, p0, p1, text, offset=(0, 0), fs=14, color="#111"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="<|-|>", mutation_scale=16, lw=1.6, color=color))
    ax.text((p0[0] + p1[0]) / 2 + offset[0], (p0[1] + p1[1]) / 2 + offset[1], text, ha="center", va="center", fontsize=fs,
            weight="bold", color=color, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none"))


def plan(ax, new_re, old_res=()):
    ax.set_aspect("equal"); ax.axis("off")
    for (x, y, w, h) in ((0, 0, D, B), (0, W - B, D, B), (0, 0, B, W), (D - B, 0, B, W)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GREY, ec="#666", lw=1))
    for nm, b in bb.items():
        if nm.startswith("icebox_"):
            continue
        if re.match(new_re, nm):
            ax.add_patch(Rectangle((b.xmin, b.ymin), b.xlen, b.ylen, fc=ORANGE, ec="#7a2d08", lw=1.2))
        elif any(re.match(r, nm) for r in old_res):
            ax.add_patch(Rectangle((b.xmin, b.ymin), b.xlen, b.ylen, fc="#e9e9e9", ec="#aaa", lw=0.8))
    ax.text(-10, W / 2, "BACK\n(touches the\nbig IceBox)", rotation=90, ha="right", va="center", fontsize=12, color="#333")
    ax.text(D + 10, W / 2, "FRONT\n(plugs)", rotation=270, ha="left", va="center", fontsize=12, color="#333")
    ax.text(D / 2, -14, "OUTBOARD side: batteries", ha="center", va="top", fontsize=12, color="#333")
    ax.text(D / 2, W + 14, "INBOARD side: inverter", ha="center", va="bottom", fontsize=12, color="#333")
    ax.set_xlim(-70, D + 70); ax.set_ylim(-60, W + 60)


def step3():
    p0, p1 = bb["print_post_inverter_0"], bb["print_post_inverter_1"]
    fig = plt.figure(figsize=(14, 9), dpi=120)
    ax = fig.add_axes([0.03, 0.30, 0.94, 0.66])
    plan(ax, r"^print_post_inverter_")
    yc = (p0.ymin + p0.ymax) / 2
    arrow(ax, (D * 0.50, Y0), (D * 0.50, yc), f"{yc - Y0:.0f} mm\nfrom the outboard rail\nto the middle of the post", offset=(0, 0))
    arrow(ax, (D * 0.80, yc), (D * 0.80, W - B), f"{(W - B) - yc:.0f} mm\nto the inboard rail", offset=(0, 0))
    ax.annotate("post 0: pushed hard\nagainst the BACK rail", xy=(p0.xmax, p0.ymin), xytext=(p0.xmax + 30, Y0 + 30), fontsize=12,
                arrowprops=dict(arrowstyle="->", lw=1.4), bbox=dict(boxstyle="round", fc="#fff2e8", ec=ORANGE))
    ax.annotate("post 1: pushed hard\nagainst the FRONT rail", xy=(p1.xmin, p1.ymin), xytext=(p1.xmin - 215, Y0 + 30), fontsize=12,
                arrowprops=dict(arrowstyle="->", lw=1.4), bbox=dict(boxstyle="round", fc="#fff2e8", ec=ORANGE))
    ax.text(D * 0.30, p0.ymax + 60, "the slot in each post\nfaces the other post", ha="center", fontsize=12, style="italic", color="#444")
    ax.set_title("Step 3: where the two posts go (looking down into the box, lid off)", fontsize=16, weight="bold", loc="left")
    # side view: one post against its rail, the sill bolt height
    ax2 = fig.add_axes([0.04, 0.02, 0.92, 0.26]); ax2.set_aspect("equal"); ax2.axis("off")
    ax2.add_patch(Rectangle((0, 0), 60, B, fc=GREY, ec="#666"))                       # bottom rail, seen end on
    ax2.add_patch(Rectangle((0, H - B), 60, B, fc=GREY, ec="#666"))                   # top rail
    ax2.add_patch(Rectangle((60, 0), 18, 254, fc=ORANGE, ec="#7a2d08"))               # the post, 18 deep, 254 tall
    ax2.plot([64, 30], [B / 2, B / 2], color=BLUE, lw=4)                              # the sill bolt into the rail's inner slot
    ax2.text(-6, B / 2, "the one bolt, into the\nrail's inner slot", ha="right", va="center", fontsize=11, color=BLUE, weight="bold")
    arrow(ax2, (150, 0), (150, B / 2), "", fs=11, color=BLUE); ax2.text(162, B / 2 + 4, f"{B / 2:.0f} mm up from the floor", fontsize=12, color=BLUE, weight="bold", va="center")
    arrow(ax2, (300, 0), (300, 254), "", fs=11); ax2.text(312, 127, "post is 254 mm tall", fontsize=12, weight="bold", va="center")
    ax2.text(-220, H + 12, "side view: the post stands on the floor, flat against the rail.\nIts top gets its clip later, in step 9.", fontsize=12, va="bottom")
    ax2.set_xlim(-230, 560); ax2.set_ylim(-12, 330)
    path = os.path.join(OUT, "03-posts-simple.png"); fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


if __name__ == "__main__":
    step3()
