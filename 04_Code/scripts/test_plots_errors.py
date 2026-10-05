"""(1) Test-set confusion matrix + PR/F1 curves for S0 and S1 (seed 0).
(2) Error analysis for S1 seed 0 on the TEST split: match predictions to ground truth (IoU>=0.5), count
    true positives, missed animals (FN), wrong-class matches, and spurious boxes (FP), per class, at conf 0.25;
    save a montage of example errors."""
import csv, random
from pathlib import Path
import numpy as np, cv2
from ultralytics import YOLO

RUNS = Path(r"C:\Users\mrjos\Downloads\wildlife-capstone\runs")
DATA = r"C:\Users\mrjos\Downloads\wildlife-yolo\data.yaml"
ROOT = Path(r"C:\Users\mrjos\Downloads\wildlife-yolo")
NAMES = ["antelope", "bird", "chimpanzee", "elephant", "gorilla", "hippo", "hog"]
OUT = Path(r"C:\Users\mrjos\Downloads\wildlife-capstone\runs\eval_plots"); OUT.mkdir(exist_ok=True)

for run in ("S0_baseline_seed0", "S1_augment_seed0"):
    m = YOLO(str(RUNS / run / "weights" / "best.pt"))
    m.val(data=DATA, split="test", imgsz=640, workers=0, batch=16, plots=True, verbose=False, project=str(OUT), name=run + "_test", exist_ok=True)
    print("plots", run, flush=True)

m = YOLO(str(RUNS / "S1_augment_seed0" / "weights" / "best.pt"))
imgs = sorted((ROOT / "images" / "test").glob("*.png"))


def iou(a, b):
    iw = min(a[2], b[2]) - max(a[0], b[0]); ih = min(a[3], b[3]) - max(a[1], b[1])
    if iw <= 0 or ih <= 0: return 0.0
    i = iw * ih; return i / ((a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i)


stats = {n: dict(gt=0, tp=0, wrong_class=0, missed=0, fp=0) for n in NAMES}
examples = {"missed": [], "wrong_class": [], "fp": []}
for f in imgs:
    im = cv2.imread(str(f)); h, w = im.shape[:2]
    gts = []
    for l in (ROOT / "labels" / "test" / (f.stem + ".txt")).read_text().splitlines():
        if l.strip():
            c, x, y, bw, bh = l.split(); c = int(c); x, y, bw, bh = map(float, (x, y, bw, bh))
            gts.append((c, [(x-bw/2)*w, (y-bh/2)*h, (x+bw/2)*w, (y+bh/2)*h]))
    r = m.predict(im, imgsz=640, conf=0.25, verbose=False)[0]
    preds = [(int(c), float(p), b) for c, p, b in zip(r.boxes.cls, r.boxes.conf, r.boxes.xyxy.tolist())]
    used = set(); img_err = []
    for gc, gb in gts:
        stats[NAMES[gc]]["gt"] += 1
        best, bj = 0, -1
        for j, (pc, pp, pb) in enumerate(preds):
            if j in used: continue
            v = iou(gb, pb)
            if v > best: best, bj = v, j
        if best >= 0.5:
            used.add(bj)
            if preds[bj][0] == gc: stats[NAMES[gc]]["tp"] += 1
            else:
                stats[NAMES[gc]]["wrong_class"] += 1; img_err.append(("wrong_class", gc, gb, preds[bj]))
        else:
            stats[NAMES[gc]]["missed"] += 1; img_err.append(("missed", gc, gb, None))
    for j, (pc, pp, pb) in enumerate(preds):
        if j not in used:
            stats[NAMES[pc]]["fp"] += 1; img_err.append(("fp", pc, None, (pc, pp, pb)))
    for kind, gc, gb, pr in img_err: examples[kind].append((f, gc, gb, pr))

with open(r"C:\Users\mrjos\error_counts.csv", "w", newline="") as fh:
    w_ = csv.writer(fh); w_.writerow(["class", "gt_boxes", "found_correct", "found_wrong_class", "missed", "false_positive_boxes"])
    for n in NAMES:
        s = stats[n]; w_.writerow([n, s["gt"], s["tp"], s["wrong_class"], s["missed"], s["fp"]])
        print(f"{n:11s} gt {s['gt']:4d}  correct {s['tp']:4d}  wrong-class {s['wrong_class']:3d}  missed {s['missed']:4d}  FP {s['fp']:4d}")

random.seed(0); tiles = []
for kind in ("missed", "wrong_class", "fp"):
    pool = examples[kind]; classes = sorted({e[1] for e in pool})
    pick = []
    for c in classes: pick += [e for e in pool if e[1] == c][:1]
    random.shuffle(pick)
    for f, gc, gb, pr in pick[:4]:
        im = cv2.imread(str(f)); h, w = im.shape[:2]
        if gb: cv2.rectangle(im, tuple(map(int, gb[:2])), tuple(map(int, gb[2:])), (0, 200, 0), max(3, w // 300))
        if pr: cv2.rectangle(im, tuple(map(int, pr[2][:2])), tuple(map(int, pr[2][2:])), (0, 0, 255), max(3, w // 300))
        lab = f"{kind}: truth {NAMES[gc]}" + (f", pred {NAMES[pr[0]]} {pr[1]:.2f}" if pr and kind != 'fp' else (f", pred {NAMES[pr[0]]} {pr[1]:.2f}" if pr else ""))
        im = cv2.resize(im, (640, int(640 * h / w))); cv2.putText(im, lab, (6, 24), 0, 0.6, (255, 255, 255), 3); cv2.putText(im, lab, (6, 24), 0, 0.6, (0, 0, 0), 1)
        tiles.append(cv2.copyMakeBorder(im, 0, max(0, 360 - im.shape[0]), 0, 0, cv2.BORDER_CONSTANT)[:360])
rows = [np.hstack(tiles[i:i+3]) for i in range(0, len(tiles) - len(tiles) % 3, 3)]
cv2.imwrite(r"C:\Users\mrjos\error_examples.jpg", np.vstack(rows)); print("montage tiles", len(tiles))
