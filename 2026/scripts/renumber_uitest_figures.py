"""Renumber uitest figure PNGs to match article appearance order (1-11)."""
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont

IMGS = Path(__file__).resolve().parents[1] / "imgs"

# Current file -> appearance order (1-based)
APPEARANCE_ORDER = {
    "uitest-figure10.png": 1,   # post-refactor chart
    "uitest-figure6.png": 2,    # root-cause chart
    "uitest-figure8.png": 3,    # effort chart
    "uitest-figure7.png": 4,    # triage chart
    "uitest-figure1.png": 5,    # xpath vs visual diagram
    "uitest-figure2.png": 6,    # pipeline diagram
    "uitest-figure3.png": 7,    # NL script diagram
    "uitest-figure4.png": 8,    # agent loop diagram
    "uitest-figure5.png": 9,    # architecture diagram
    "uitest-figure11.png": 10,  # segmentation chart
    "uitest-figure9.png": 11,   # pilot chart
}

# Diagram titles baked into hand-made figures (old number -> new number + title suffix)
DIAGRAM_TITLES = {
    5: "Figure 5 — Traditional XPath vs. Visual Segmentation Locators",
    6: "Figure 6 — Page Segmentation and Visual Element Recognition Pipeline",
    7: "Figure 7 — Natural Language to Executable UI Test Script",
    8: "Figure 8 — AI-Agent Closed-Loop Framework Build Workflow (Ring View)",
    9: "Figure 9 — Target UI Automation Framework Architecture",
}


def renumber_files():
    tmp = {}
    for old_name, order in APPEARANCE_ORDER.items():
        src = IMGS / old_name
        if not src.exists():
            raise FileNotFoundError(src)
        tmp_path = IMGS / f"_renum_tmp_{order:02d}.png"
        shutil.copy2(src, tmp_path)
        tmp[order] = tmp_path
        print(f"Staged {old_name} -> {tmp_path.name}")

    for order, tmp_path in tmp.items():
        dest = IMGS / f"uitest-figure{order}.png"
        tmp_path.replace(dest)
        print(f"Renamed -> {dest.name}")


def patch_diagram_title(img_path: Path, new_title: str, banner_h: int = 98):
    """Replace baked-in diagram title with a single matplotlib-style heading."""
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, _ = img.size
    draw.rectangle([(0, 0), (w, banner_h)], fill=(255, 255, 255))
    for size in range(24, 14, -1):
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", size)
        except OSError:
            font = ImageFont.load_default()
            break
        bbox = font.getbbox(new_title)
        if bbox[2] - bbox[0] <= int(w * 0.92):
            break
    bbox = font.getbbox(new_title)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - text_w) // 2 - bbox[0]
    y = (banner_h - text_h) // 2 - bbox[1]
    draw.text((x, y), new_title, fill=(30, 41, 59), font=font)
    img.save(img_path)
    print(f"Patched title on {img_path.name}")


if __name__ == "__main__":
    renumber_files()
    for fig_num, title in DIAGRAM_TITLES.items():
        patch_diagram_title(IMGS / f"uitest-figure{fig_num}.png", title)
    print("Figure renumbering complete.")
