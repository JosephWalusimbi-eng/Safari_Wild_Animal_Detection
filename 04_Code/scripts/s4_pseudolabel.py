"""S4: pseudo-label frames from the 4 NEW Zenodo videos and add them to a copy of the TRAIN split.
Leak-checked videos only (see report Entry 15). val/test are hard links to the originals.

Rules (stated in the report):
  * each video has one known species -> only detections of that species are used;
  * a frame is kept only if it has >=1 detection of that species with conf >= THR,
    no detection of that species in the ambiguous band [LOW, THR), and no detection of
    any other class with conf >= LOW (a conflict means the model is unsure what it sees).
Usage: python s4_pseudolabel.py --weights <best.pt> --thr 0.6 --src-data wildlife-yolo --out wildlife-yolo-ps"""
import argparse, os, shutil, csv
from pathlib import Path
import cv2
from ultralytics import YOLO

ap = argparse.ArgumentParser()
ap.add_argument("--weights", required=True)
ap.add_argument("--thr", type=float, default=0.6)
ap.add_argument("--low", type=float, default=0.3)
ap.add_argument("--src-data", default="wildlife-yolo")
ap.add_argument("--out", default="wildlife-yolo-ps")
a = ap.parse_args()
NAMES = ["antelope", "bird", "chimpanzee", "elephant", "gorilla", "hippo", "hog"]
X = Path(r"C:\Users\mrjos\Downloads\zenodo_extra")
BASE = Path(r"C:\Users\mrjos\Downloads")
SRC, DST = BASE / a.src_data, BASE / a.out
VIDEOS = {  # file -> (tag, species)
    "Elephant/Elephant/Elephant_ANP.mp4": ("elephantANP", "elephant"),
    "Elephant/Elephant/Elephants. CTPHmp4. CTPHmp4. CTPHmp4.mp4": ("elephantCTPH", "elephant"),
    "Hippopotamus/Hippopotamus/Hippopotamus.mp4": ("hippoLQ", "hippo"),
    "Warthog/Warthog/Warthog.mp4": ("warthog", "hog"),
}
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

model = YOLO(a.weights)
stats, rows = [], []
for rel, (tag, species) in VIDEOS.items():
    cap = cv2.VideoCapture(str(X / rel))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    step = max(int(round(fps / 2)), 1)
    sid = NAMES.index(species)
    k = sampled = kept = boxes = amb = conflict = nodet = 0
    while True:
        if not cap.grab():
            break
        if k % step == 0:
            ok, fr = cap.retrieve()
            if ok:
                sampled += 1
                r = model.predict(fr, imgsz=640, conf=a.low, verbose=False)[0]
                cls = r.boxes.cls.int().tolist(); cf = r.boxes.conf.tolist(); xywhn = r.boxes.xywhn.tolist()
                good = [(c, p, b) for c, p, b in zip(cls, cf, xywhn) if c == sid and p >= a.thr]
                band = [1 for c, p in zip(cls, cf) if c == sid and p < a.thr]
                other = [1 for c, p in zip(cls, cf) if c != sid]
                if not good:
                    nodet += 1
                elif band:
                    amb += 1
                elif other:
                    conflict += 1
                else:
                    name = f"ps_{tag}_{k:05d}"
                    cv2.imwrite(str(DST / "images" / "train" / f"{name}.png"), fr)
                    with open(DST / "labels" / "train" / f"{name}.txt", "w") as f:
                        for c, p, b in good:
                            f.write(f"{c} {b[0]:.6f} {b[1]:.6f} {b[2]:.6f} {b[3]:.6f}\n")
                    kept += 1; boxes += len(good)
                    rows.append([name, tag, species, len(good), round(min(p for _, p, _ in good), 3)])
        k += 1
    stats.append((tag, species, sampled, kept, boxes, nodet, amb, conflict))
with open(DST / "ps_manifest.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["image", "video", "species", "boxes", "min_conf"]); w.writerows(rows)
(DST / "data.yaml").write_text(f"path: {DST.as_posix()}\ntrain: images/train\nval: images/val\ntest: images/test\nnc: 7\nnames: {NAMES}\n")
print(f"weights={a.weights}  thr={a.thr}  low={a.low}")
print("video          species  sampled  kept  boxes  no_conf_det  ambiguous  conflict")
for s in stats:
    print(f"{s[0]:14s} {s[1]:8s} {s[2]:7d} {s[3]:5d} {s[4]:6d} {s[5]:12d} {s[6]:10d} {s[7]:9d}")
print("TOTAL kept frames:", sum(s[3] for s in stats), " boxes:", sum(s[4] for s in stats))
