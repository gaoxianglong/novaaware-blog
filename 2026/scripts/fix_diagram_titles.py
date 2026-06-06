"""Remove embedded titles from hand-made diagram figures 5-9."""
from pathlib import Path

from PIL import Image

IMGS = Path(__file__).resolve().parents[1] / "imgs"

# Top crop per figure: removes matplotlib/patch overlay and baked-in title text.
CROP_TOP = {5: 110, 6: 100, 7: 106, 8: 142, 9: 106}


def remove_title(fig_num: int):
    path = IMGS / f"uitest-figure{fig_num}.png"
    img = Image.open(path).convert("RGB")
    w, h = img.size
    crop = CROP_TOP[fig_num]
    cropped = img.crop((0, crop, w, h))
    cropped.save(path)
    print(f"Removed title from {path.name}: {w}x{h} -> {cropped.size[0]}x{cropped.size[1]} (crop {crop}px)")


if __name__ == "__main__":
    for fig_num in CROP_TOP:
        remove_title(fig_num)
    print("Done.")
