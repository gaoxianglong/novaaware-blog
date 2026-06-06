"""Generate data charts for AI-Testing UI automation article."""
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from PIL import Image

OUT_DIR = Path(__file__).resolve().parents[1] / "imgs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TOP_PADDING_PX = 40

# Palette aligned with existing article figures
COLORS = {
    "blue": "#4A90D9",
    "indigo": "#5B6BBF",
    "purple": "#7B5EA7",
    "teal": "#2EAF9B",
    "green": "#4CAF7A",
    "orange": "#E8913A",
    "red": "#D9534F",
    "gray": "#6B7280",
    "light": "#E8EDF3",
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#CBD5E1",
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})


def save(fig, name: str):
    path = OUT_DIR / name
    try:
        fig.tight_layout()
    except Exception:
        pass
    buf = BytesIO()
    fig.savefig(buf, dpi=160, bbox_inches="tight", facecolor="white", pad_inches=0.05)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    w, h = img.size
    canvas = Image.new("RGB", (w, h + TOP_PADDING_PX), (255, 255, 255))
    canvas.paste(img, (0, TOP_PADDING_PX))
    canvas.save(path)
    print(f"Wrote {path} ({canvas.size[0]}x{canvas.size[1]}, +{TOP_PADDING_PX}px top)")


def chart_failure_root_causes():
    """Figure 2 — XPath locator failure root-cause taxonomy (internal audit)."""
    labels = [
        "Wrapper div\nadded/removed",
        "Dynamic / hashed\nclass names",
        "i18n or copy\nchange",
        "Positional / index\nshift",
        "Shadow DOM /\niframe boundary",
        "Other (timing,\nA/B, viewport)",
    ]
    values = [38, 22, 14, 12, 9, 5]
    colors = [
        COLORS["red"], COLORS["orange"], COLORS["purple"],
        COLORS["blue"], COLORS["indigo"], COLORS["gray"],
    ]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    y = np.arange(len(labels))
    bars = ax.barh(y, values, color=colors, height=0.62, edgecolor="white", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Share of broken XPath locators (%)")
    ax.set_xlim(0, 45)
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.6, bar.get_y() + bar.get_height() / 2,
                f"{val}%", va="center", fontweight="bold", fontsize=10)
    ax.axvline(38, color=COLORS["red"], linestyle=":", alpha=0.5, linewidth=1.2)
    note = (
        "Source: internal locator audit, Q1 2026. "
        "38% of failures: target still visible; DOM path no longer valid."
    )
    fig.text(0.12, 0.02, note, fontsize=8.5, color=COLORS["gray"])
    fig.subplots_adjust(bottom=0.14)
    save(fig, "uitest-figure2.png")


def chart_triage_time():
    """Figure 4 — Median failure triage time: XPath vs visual-first."""
    methods = ["XPath / DOM\nlocator failure", "Visual-first\nfailure bundle"]
    median_min = [52, 14]
    p90_min = [98, 31]

    x = np.arange(len(methods))
    w = 0.34
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    b1 = ax.bar(x - w / 2, median_min, w, label="Median (P50)", color=COLORS["blue"])
    b2 = ax.bar(x + w / 2, p90_min, w, label="P90", color=COLORS["teal"])
    ax.set_ylabel("Minutes to root-cause classification")
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.set_ylim(0, 115)
    ax.legend(loc="upper right", framealpha=0.95)

    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 2,
                    f"{int(h)} min", ha="center", fontweight="bold", fontsize=10)

    reduction = round((1 - 14 / 52) * 100)
    ax.annotate(
        f"−{reduction}% median triage",
        xy=(1, 14), xytext=(0.45, 72),
        arrowprops=dict(arrowstyle="->", color=COLORS["green"], lw=1.8),
        fontsize=10, color=COLORS["green"], fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="#E8F5EE", ec=COLORS["green"], alpha=0.9),
    )
    fig.text(0.12, 0.02,
             "Half of XPath failures were 'element moved but still visible' — not expressible in selector strings.",
             fontsize=8.5, color=COLORS["gray"])
    fig.subplots_adjust(bottom=0.14)
    save(fig, "uitest-figure4.png")


def chart_effort_distribution():
    """Figure 3 — Where UI automation effort goes (industry + internal)."""
    categories = ["Locator repair\n& maintenance", "New test\ndesign", "Env / data\nsetup", "CI flake\ntriage", "Reporting &\nevidence"]
    industry = [52, 22, 12, 9, 5]
    internal_before = [48, 24, 11, 12, 5]
    internal_after = [18, 38, 11, 8, 25]

    x = np.arange(len(categories))
    w = 0.26
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    ax.bar(x - w, industry, w, label="Industry benchmark (WQR 2024–25)", color=COLORS["gray"], alpha=0.75)
    ax.bar(x, internal_before, w, label="Our team — legacy XPath suite", color=COLORS["red"], alpha=0.85)
    ax.bar(x + w, internal_after, w, label="Our team — visual + NL (pilot wk 12)", color=COLORS["green"], alpha=0.9)
    ax.set_ylabel("Share of automation engineer-hours (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 58)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.95)
    fig.text(
        0.12, 0.02,
        "Industry: World Quality Report 2024–25 (Capgemini/Sogeti/Cognizant), weighted avg. for web UI teams. "
        "Internal: Jira + CI time logs, n=6 engineers.",
        fontsize=8, color=COLORS["gray"],
    )
    fig.subplots_adjust(bottom=0.16)
    save(fig, "uitest-figure3.png")


def chart_pilot_outcomes():
    """Figure 11 — 12-week pilot comparative outcomes."""
    metrics = [
        "Locator repair\n(h / release)",
        "CI flake rate\n(smoke, %)",
        "New case authoring\n(hours)",
        "Framework\nbootstrap (hours)",
    ]
    legacy = [48, 14, 5.0, 48]  # bootstrap: 2-3 days -> use 48h midpoint
    visual = [11, 5, 1.125, 5.5]  # authoring: 45-90 min -> 1.125h avg; bootstrap 5-6h

    x = np.arange(len(metrics))
    w = 0.34
    fig, ax = plt.subplots(figsize=(10, 5.5))
    b1 = ax.bar(x - w / 2, legacy, w, label="Legacy XPath suite", color=COLORS["red"], alpha=0.85)
    b2 = ax.bar(x + w / 2, visual, w, label="Visual + NL Agent suite", color=COLORS["green"], alpha=0.9)
    ax.set_ylabel("Value (hours or % — see axis labels per metric)")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)

    labels_legacy = ["48 h", "14%", "4–6 h", "2–3 d"]
    labels_visual = ["11 h", "5%", "45–90 m", "5–6 h"]
    for bar, lbl in zip(b1, labels_legacy):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2,
                lbl, ha="center", fontsize=9, fontweight="bold", color=COLORS["red"])
    for bar, lbl in zip(b2, labels_visual):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2,
                lbl, ha="center", fontsize=9, fontweight="bold", color="#1B7A4E")

    ax.set_ylim(0, 58)
    ax.legend(loc="upper right")
    fig.text(0.12, 0.02,
             "Pilot scope: 180+ migrated cases, 3 browsers, bi-weekly releases. "
             "Flake rate = smoke jobs failing then passing on immediate retry.",
             fontsize=8.5, color=COLORS["gray"])
    fig.subplots_adjust(bottom=0.14)
    save(fig, "uitest-figure11.png")


def chart_post_refactor_failures():
    """Figure 1 — First sprint post-refactor failure breakdown."""
    labels = ["Locator resolution\n(no functional defect)", "Functional /\nassertion failure", "Env / data /\ninfra", "Flaky timing\n(resolved on retry)"]
    sizes = [47, 28, 15, 10]
    colors = [COLORS["red"], COLORS["orange"], COLORS["blue"], COLORS["gray"]]
    explode = (0.06, 0, 0, 0)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    wedges, texts, autotexts = ax.pie(
        sizes, explode=explode, labels=labels, colors=colors,
        autopct="%1.0f%%", startangle=140, pctdistance=0.72,
        textprops={"fontsize": 9},
        wedgeprops=dict(edgecolor="white", linewidth=1.5),
    )
    for t in autotexts:
        t.set_fontweight("bold")
        t.set_fontsize(11)
    centre = plt.Circle((0, 0), 0.55, fc="white")
    ax.add_artist(centre)
    ax.text(0, 0.06, "540\nruns", ha="center", va="center", fontsize=14, fontweight="bold")
    ax.text(0, -0.18, "254 failed", ha="center", va="center", fontsize=10, color=COLORS["red"])
    fig.text(0.12, 0.02,
             "47% failed before any functional defect was found — locator resolution only. "
             "Repair consumed 6 engineer-days.",
             fontsize=8.5, color=COLORS["gray"])
    fig.subplots_adjust(bottom=0.12)
    save(fig, "uitest-figure1.png")


def chart_recognition_performance():
    """Figure 10 — Visual recognition accuracy & latency by segmentation mode."""
    modes = ["Fixed grid\n(4×3)", "Layout\nheuristics", "Hybrid\n(grid + refine)", "SAM /\nCV hybrid"]
    accuracy = [82, 87, 94, 91]
    latency = [180, 260, 500, 650]

    fig, ax1 = plt.subplots(figsize=(9.5, 5.2))
    x = np.arange(len(modes))
    w = 0.38
    bars = ax1.bar(x - w / 2, accuracy, w, color=COLORS["purple"], label="Region accuracy (%)", alpha=0.9)
    ax1.set_ylabel("Region accuracy (%)", color=COLORS["purple"])
    ax1.set_ylim(75, 100)
    ax1.set_xticks(x)
    ax1.set_xticklabels(modes)
    ax2 = ax1.twinx()
    ax2.plot(x, latency, color=COLORS["orange"], marker="o", linewidth=2.5, markersize=8, label="P50 latency (ms)")
    ax2.set_ylabel("P50 latency (ms)", color=COLORS["orange"])
    ax2.set_ylim(0, 800)
    for bar, val in zip(bars, accuracy):
        ax1.text(bar.get_x() + bar.get_width() / 2, val + 0.8, f"{val}%", ha="center", fontsize=9, fontweight="bold")
    for i, val in enumerate(latency):
        ax2.text(i, val + 28, f"{val} ms", ha="center", fontsize=9, color=COLORS["orange"], fontweight="bold")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="lower right", fontsize=9)
    fig.text(0.12, 0.02,
             "Accuracy = correct tile scope on first attempt. Latency = segment + index on CI worker (8 vCPU, no GPU).",
             fontsize=8.5, color=COLORS["gray"])
    fig.subplots_adjust(bottom=0.14)
    save(fig, "uitest-figure10.png")


if __name__ == "__main__":
    chart_post_refactor_failures()
    chart_failure_root_causes()
    chart_effort_distribution()
    chart_triage_time()
    chart_recognition_performance()
    chart_pilot_outcomes()
    print("Done.")
