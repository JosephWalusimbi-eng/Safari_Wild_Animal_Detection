"""Repeat-factor sampling (LVIS-style) for the TRAIN split only.
f(c) = share of train images that contain class c.   r(c) = max(1, sqrt(t / f(c))).
An image's repeat factor = max r(c) over the classes it contains; it is listed
round(r) times (deterministic), capped at --cap. val/test are hard links, untouched.
Builds wildlife-yolo-rfs next to the original; the original is never modified."""
import argparse, math, os, shutil
from collections import Counter
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--t", type=float, default=0.3)
ap.add_argument("--cap", type=int, default=4)
a = ap.parse_args()
NAMES = ["antelope", "bird", "chimpanzee", "elephant", "gorilla", "hippo", "hog"]
SRC = Path(r"C:\Users\mrjos\Downloads\wildlife-yolo")
DST = Path(r"C:\Users\mrjos\Downloads\wildlife-yolo-rfs")
if DST.exists() and any(DST.iterdir()):
    raise SystemExit(f"{DST} not empty")


def link(s, d):
    d.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(s, d)
    except OSError:
        shutil.copy2(s, d)


for sp in ("train", "val", "test"):
    for kind in ("images", "labels"):
        for f in (SRC / kind / sp).glob("*"):
            link(f, DST / kind / sp / f.name)

imgs = sorted((DST / "images" / "train").glob("*.png"))
cls_of = {}
for f in imgs:
    txt = (DST / "labels" / "train" / (f.stem + ".txt")).read_text().splitlines()
    cls_of[f] = {int(l.split()[0]) for l in txt if l.strip()}
n = len(imgs)
freq = {c: sum(c in s for s in cls_of.values()) / n for c in range(7)}
r_c = {c: max(1.0, math.sqrt(a.t / freq[c])) for c in range(7)}
print(f"train images: {n}   t={a.t}  cap={a.cap}")
print("class        f(c)   r(c)")
for c in range(7):
    print(f"{NAMES[c]:11s} {freq[c]:5.2f}  {r_c[c]:5.2f}")
lines, reps, box_after = [], Counter(), Counter()
for f in imgs:
    r = max([r_c[c] for c in cls_of[f]] or [1.0])
    k = min(a.cap, max(1, int(r + 0.5)))
    reps[k] += 1
    lines += [str(f)] * k
    txt = (DST / "labels" / "train" / (f.stem + ".txt")).read_text().splitlines()
    for l in txt:
        if l.strip():
            box_after[NAMES[int(l.split()[0])]] += k
(DST / "train_rfs.txt").write_text("\n".join(lines) + "\n")
(DST / "data.yaml").write_text(
    f"path: {DST.as_posix()}\ntrain: {(DST / 'train_rfs.txt').as_posix()}\n"
    f"val: images/val\ntest: images/test\nnc: 7\nnames: {NAMES}\n"
)
print("copies per image:", dict(sorted(reps.items())), "-> train list length", len(lines))
print("train boxes seen per epoch after repeating:", dict(box_after))
