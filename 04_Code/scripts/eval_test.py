"""Evaluate trained models on a dataset's TEST split, per class. Writes CSV.
Usage: python eval_test.py --data <data.yaml> --out <csv> run1 run2 ...   (run = folder name under runs/)"""
import argparse, csv
from pathlib import Path
from ultralytics import YOLO
ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); ap.add_argument("--split", default="test"); ap.add_argument("--imgsz", type=int, default=640)
ap.add_argument("runs", nargs="+"); a = ap.parse_args()
RUNS = Path(r"C:\Users\mrjos\Downloads\wildlife-capstone\runs")
NAMES = ["antelope", "bird", "chimpanzee", "elephant", "gorilla", "hippo", "hog"]
rows = []
for r in a.runs:
    m = YOLO(str(RUNS / r / "weights" / "best.pt"))
    res = m.val(data=a.data, split=a.split, imgsz=a.imgsz, verbose=False, plots=False, workers=0, batch=16)
    b = res.box
    rows.append([r, "all", round(b.mp, 4), round(b.mr, 4), round(b.map50, 4), round(b.map, 4)])
    for j, ci in enumerate(b.ap_class_index):
        rows.append([r, NAMES[int(ci)], round(float(b.p[j]), 4), round(float(b.r[j]), 4), round(float(b.ap50[j]), 4), round(float(b.ap[j]), 4)])
    print(r, "done", flush=True)
with open(a.out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["run", "class", "precision", "recall", "mAP50", "mAP50-95"]); w.writerows(rows)
