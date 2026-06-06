"""Figure 8 — Plain hand-drawn style Agent closed loop ring."""
from io import BytesIO
from math import cos, radians, sin
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Wedge
from PIL import Image

OUT = Path(__file__).resolve().parents[1] / "imgs" / "uitest-figure8.png"
TARGET_WIDTH = 1920
TOP_PADDING_PX = 40
DPI = 160

C = {
    "paper": "#FFFDF7",
    "ink": "#334155",
    "soft_ink": "#94A3B8",
    "text": "#1E293B",
    "muted": "#64748B",
    "line": "#94A3B8",
    "human": "#0F766E",
    "human_star": "#DC2626",
    "note_bg": "#FFFBEB",
    "note_edge": "#EAB308",
    "center": "#263445",
}

# (num, title, deliverable, prompt cue, fill, edge, human checkpoint?)
STEPS = [
    ("1", "Rules", "./rules/", "non-negotiables", "#E8F1FF", "#3B82F6", False),
    ("2", "Scaffold", "pytest + Playwright", "minimal layout", "#ECEEFF", "#6366F1", True),
    ("3", "Segment", "uiauto/segment/", "viewport to tiles", "#F3ECFF", "#8B5CF6", True),
    ("4", "Recognize", "uiauto/recognize/", "OCR + bbox", "#E0F7F3", "#14B8A6", False),
    ("5", "VisualDriver", "uiauto/visual/", "stable facade", "#E3F7EC", "#10B981", False),
    ("6", "NL Compiler", "compiler/", "NL to pytest", "#E8F8E2", "#22C55E", True),
    ("7", "First Green", "pytest loop", "fix safely", "#FFF0D5", "#F97316", True),
    ("8", "CI + Skill", "Actions + SKILL.md", "reuse", "#FFE9E9", "#EF4444", True),
]

def rounded_box(ax, xy, w, h, fc, ec, lw=1.4, r=0.018, z=3, alpha=1.0):
    p = FancyBboxPatch(
        xy, w, h,
        boxstyle=f"round,pad=0.01,rounding_size={r}",
        linewidth=lw, edgecolor=ec, facecolor=fc, alpha=alpha,
        transform=ax.transAxes, zorder=z,
    )
    ax.add_patch(p)
    return p


def ring_xy(radius, angle_deg):
    angle = radians(angle_deg)
    return radius * cos(angle), radius * sin(angle)


def main():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    })

    fig_w = TARGET_WIDTH / DPI
    fig_h = fig_w * 0.55
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=DPI)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fig.patch.set_facecolor(C["paper"])
    ax.set_facecolor(C["paper"])

    ax.text(0.50, 1.055, "Eight-step Agent closed loop", ha="center", va="center",
            fontsize=15.5, fontweight="bold", color=C["text"], transform=ax.transAxes)
    ax.text(0.50, 1.018, "plain ring view: Agent builds, Human reviews", ha="center", va="center",
            fontsize=9.8, color=C["muted"], transform=ax.transAxes)

    # Square inset keeps the ring circular regardless of figure aspect ratio.
    ring_ax = fig.add_axes([0.130, 0.180, 0.74, 0.74])
    ring_ax.set_xlim(-1.22, 1.22)
    ring_ax.set_ylim(-1.22, 1.22)
    ring_ax.set_aspect("equal")
    ring_ax.axis("off")
    ring_ax.set_facecolor(C["paper"])

    gap = 8.0
    span = 360 / len(STEPS) - gap
    start = 112.5
    outer_r = 1.00
    inner_r = 0.56
    label_r = 0.78
    arrow_r = 1.13

    for i, (num, title, deliverable, cue, fc, ec, human) in enumerate(STEPS):
        theta2 = start - i * (span + gap)
        theta1 = theta2 - span
        mid = (theta1 + theta2) / 2

        # Double outline and small angle offset give a light hand-drawn feel.
        ring_ax.add_patch(Wedge((0, 0), outer_r, theta1, theta2,
                                width=outer_r - inner_r, facecolor=fc,
                                edgecolor=ec, linewidth=1.35, zorder=3))
        ring_ax.add_patch(Wedge((0.012, -0.010), outer_r * 0.998, theta1 + 0.8, theta2 - 0.6,
                                width=outer_r - inner_r, facecolor="none",
                                edgecolor=ec, linewidth=0.65, alpha=0.45, zorder=4))

        tx, ty = ring_xy(label_r, mid)
        ring_ax.text(tx, ty + 0.035, f"{num}. {title}", ha="center", va="center",
                     fontsize=8.2, fontweight="bold", color=C["text"], zorder=5)
        ring_ax.text(tx, ty - 0.052, cue, ha="center", va="center",
                     fontsize=6.6, color=C["muted"], zorder=5)

        if human:
            hx, hy = ring_xy(1.07, mid)
            ring_ax.text(hx, hy, "*", ha="center", va="center", fontsize=15,
                         fontweight="bold", color=C["human_star"], zorder=6)

    # Four simple directional arrows at NW / NE / SE / SW.
    for arrow_mid in (135, 45, -45, -135):
        a1 = arrow_mid + 7
        a2 = arrow_mid - 7
        x1, y1 = ring_xy(arrow_r, a1)
        x2, y2 = ring_xy(arrow_r, a2)
        ring_ax.add_patch(FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle="-|>", mutation_scale=13,
            linewidth=1.2, color=C["soft_ink"],
            connectionstyle="arc3,rad=-0.25", zorder=2,
        ))

    ring_ax.add_patch(Circle((0, 0), 0.43, facecolor="#FFFFFF",
                             edgecolor=C["ink"], linewidth=1.35, zorder=5))
    ring_ax.add_patch(Circle((0.012, -0.012), 0.425, facecolor="none",
                             edgecolor=C["ink"], linewidth=0.65, alpha=0.45, zorder=6))
    ring_ax.text(0, 0.075, "Human\nReview", ha="center", va="center",
                 fontsize=13.0, fontweight="bold", color=C["text"], zorder=7)
    ring_ax.text(0, -0.125, "approve diff\nand constraints",
                 ha="center", va="center", fontsize=8.0, color=C["muted"],
                 linespacing=1.2, zorder=7)

    # Footer summary
    rounded_box(ax, (0.190, 0.065), 0.62, 0.068, C["note_bg"], C["note_edge"], lw=1.1, z=2)
    ax.text(0.50, 0.107,
            "* = human checkpoint: review diff, assertions, environment, or CI policy",
            ha="center", va="center", fontsize=8.5, fontweight="bold",
            color=C["text"], transform=ax.transAxes, zorder=3)
    ax.text(0.50, 0.084,
            "Inputs: FRAMEWORK_SPEC.md + ./rules/ + golden path NL case",
            ha="center", va="center", fontsize=7.8, color=C["muted"],
            transform=ax.transAxes, zorder=3)

    buf = BytesIO()
    fig.savefig(buf, dpi=DPI, facecolor=C["paper"], pad_inches=0.08)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    scale = TARGET_WIDTH / img.width
    new_h = int(img.height * scale)
    img = img.resize((TARGET_WIDTH, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (TARGET_WIDTH, new_h + TOP_PADDING_PX), (255, 253, 247))
    canvas.paste(img, (0, TOP_PADDING_PX))
    canvas.save(OUT)
    print(f"Wrote {OUT} ({canvas.size[0]}x{canvas.size[1]})")


if __name__ == "__main__":
    main()
