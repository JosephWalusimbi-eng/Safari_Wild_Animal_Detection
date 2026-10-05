"""Experiment A dataset, corrected: leave-session-out WITH a clean validation split.
Train sessions: gorillas, gorillas2, hippo2   -> first 85% of each session (time order) = train, last 15% = val
Held-out test sessions: gorillas3, hippo      -> all frames, never used for training or model selection.
(The earlier wildlife-yolo-lso has no val folder, and suggested reusing the default split's val frames,
which are already inside its train set - that would leak.)  Built from wildlife-yolo-lso by hard links."""
import os, shutil
from pathlib import Path
SRC = Path(r"C:\Users\mrjos\Downloads\wildlife-yolo-lso"); DST = Path(r"C:\Users\mrjos\Downloads\wildlife-yolo-lso2")
NAMES = ["antelope", "bird", "chimpanzee", "elephant", "gorilla", "hippo", "hog"]
if DST.exists() and any(DST.iterdir()):
    raise SystemExit("not empty")


def link(s, d):
    d.parent.mkdir(parents=True, exist_ok=True)
    try: os.link(s, d)
    except OSError: shutil.copy2(s, d)


for sess in ("gorillas", "gorillas2", "hippo2"):
    fs = sorted((SRC / "images" / "train").glob(f"{sess}_frame_*.png"))
    k = int(len(fs) * 0.85)
    for i, f in enumerate(fs):
        sp = "train" if i < k else "val"
        link(f, DST / "images" / sp / f.name); link(SRC / "labels" / "train" / (f.stem + ".txt"), DST / "labels" / sp / (f.stem + ".txt"))
    print(f"{sess}: train {k}, val {len(fs) - k}")
for f in (SRC / "images" / "test").glob("*.png"):
    link(f, DST / "images" / "test" / f.name); link(SRC / "labels" / "test" / (f.stem + ".txt"), DST / "labels" / "test" / (f.stem + ".txt"))
(DST / "data.yaml").write_text(f"path: {DST.as_posix()}\ntrain: images/train\nval: images/val\ntest: images/test\nnc: 7\nnames: {NAMES}\n")
import collections
for sp in ("train", "val", "test"):
    c = collections.Counter()
    for l in (DST / "labels" / sp).glob("*.txt"):
        for line in l.read_text().splitlines():
            if line.strip(): c[NAMES[int(line.split()[0])]] += 1
    n = len(list((DST / "images" / sp).glob("*.png")))
    print(sp, n, "images", dict(c))
