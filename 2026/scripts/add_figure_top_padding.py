"""Add consistent top whitespace to all uitest figure PNGs."""
from pathlib import Path

from PIL import Image

IMGS = Path(__file__).resolve().parents[1] / "imgs"
TOP_PADDING_PX = 40


def add_top_padding(path: Path, px: int = TOP_PADDING_PX) -> None:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    canvas = Image.new("RGB", (w, h + px), (255, 255, 255))
    canvas.paste(img, (0, px))
    canvas.save(path)
    print(f"Padded {path.name}: {w}x{h} -> {canvas.size[0]}x{canvas.size[1]} (+{px}px top)")


if __name__ == "__main__":
    for i in range(1, 12):
        path = IMGS / f"uitest-figure{i}.png"
        if not path.exists():
            raise FileNotFoundError(path)
        add_top_padding(path)
    print("Done.")
