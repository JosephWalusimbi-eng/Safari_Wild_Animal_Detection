import sys
from pathlib import Path
from PIL import Image, ImageDraw
# usage: sheet.py out.jpg cols file1 file2 ...
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
T = 220
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * T, rows * (T + 14)), "white")
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB"); im.thumbnail((T, T))
    x, y = (i % cols) * T, (i // cols) * (T + 14)
    sheet.paste(im, (x, y))
    d.text((x + 2, y + T), Path(f).parent.name[:12] + "/" + Path(f).name[:18], fill="black")
sheet.save(out, quality=85)
