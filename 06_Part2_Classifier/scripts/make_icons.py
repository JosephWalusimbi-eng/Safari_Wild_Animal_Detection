"""make_icons.py - draw the PWA icons (a simple paw print on brand green). No external assets.

    python make_icons.py --out ..\\pwa\\icons
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw

GREEN, CREAM = (31, 77, 43), (246, 245, 240)


def paw(size, pad_frac):
    im = Image.new("RGB", (size, size), GREEN)
    d = ImageDraw.Draw(im)
    s = size * (1 - 2 * pad_frac); o = size * pad_frac
    def ell(cx, cy, rx, ry):
        d.ellipse([o + (cx - rx) * s, o + (cy - ry) * s, o + (cx + rx) * s, o + (cy + ry) * s], fill=CREAM)
    ell(0.50, 0.66, 0.22, 0.18)                                   # pad
    for cx, cy in ((0.24, 0.42), (0.40, 0.27), (0.60, 0.27), (0.76, 0.42)):
        ell(cx, cy, 0.085, 0.11)                                  # toes
    return im


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    paw(192, 0.12).save(out / "icon-192.png")
    paw(512, 0.12).save(out / "icon-512.png")
    paw(512, 0.22).save(out / "maskable-512.png")   # maskable: keep art inside the safe zone
    print("icons written to", out)
