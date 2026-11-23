"""evaluate_cls.py - Part 2: evaluate trained classifiers on test and uwec_test.

For every run folder given, predicts every image in <data>/test and <data>/uwec_test and writes
into <out>/:
  predictions.csv     run, split, file, true, pred, conf, top5 (one row per image)
  summary.csv         run, split, n, top1, top5, macro_acc (mean of per-class accuracy)
  per_class.csv       run, split, class, n, correct, acc
  threshold.csv       run, split, threshold, coverage, acc_on_answered  ("unknown" below threshold)
  cm_<run>_<split>.png   confusion matrix (row-normalised, counts printed)

    python evaluate_cls.py --data <cls_v1> --runs <runs>/n_seed0 <runs>/n_seed1 ... --out <results>
"""
import argparse, csv
from collections import defaultdict
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ultralytics import YOLO

EXT = {".jpg", ".jpeg", ".png"}
THRESHOLDS = [0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def images(split_dir):
    for cdir in sorted(p for p in split_dir.iterdir() if p.is_dir()):
        for f in sorted(cdir.iterdir()):
            if f.suffix.lower() in EXT:
                yield cdir.name, f


def plot_cm(cm, names, title, path):
    keep = [i for i in range(len(names)) if cm[i].sum() or cm[:, i].sum()]
    cm = cm[np.ix_(keep, keep)]; nm = [names[i] for i in keep]
    norm = cm / np.maximum(cm.sum(1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(0.45 * len(nm) + 3, 0.45 * len(nm) + 2.5))
    ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    for i in range(len(nm)):
        for j in range(len(nm)):
            if cm[i, j]:
                ax.text(j, i, int(cm[i, j]), ha="center", va="center", fontsize=7,
                        color="white" if norm[i, j] > 0.5 else "black")
    ax.set_xticks(range(len(nm)), nm, rotation=90, fontsize=8)
    ax.set_yticks(range(len(nm)), nm, fontsize=8)
    ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(title, fontsize=10)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--splits", nargs="+", default=["test", "uwec_test"])
    a = ap.parse_args()
    data, out = Path(a.data), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    P, S, PC, T = [], [], [], []
    for run in map(Path, a.runs):
        m = YOLO(str(run / "weights" / "best.pt"))
        names = [m.names[i] for i in range(len(m.names))]
        idx = {n: i for i, n in enumerate(names)}
        for split in a.splits:
            items = list(images(data / split))
            if not items:
                continue
            rows = []
            for k in range(0, len(items), 64):
                chunk = items[k:k + 64]
                res = m.predict([str(f) for _, f in chunk], imgsz=224, verbose=False)
                for (true, f), r in zip(chunk, res):
                    p = r.probs
                    top5 = [names[i] for i in p.top5]
                    rows.append(dict(run=run.name, split=split, file=f"{true}/{f.name}", true=true,
                                     pred=names[p.top1], conf=round(float(p.top1conf), 4),
                                     top5="|".join(top5)))
            P += rows
            n = len(rows)
            top1 = sum(r["true"] == r["pred"] for r in rows) / n
            top5 = sum(r["true"] in r["top5"].split("|") for r in rows) / n
            per = defaultdict(lambda: [0, 0])
            cm = np.zeros((len(names), len(names)), int)
            for r in rows:
                per[r["true"]][0] += 1; per[r["true"]][1] += r["true"] == r["pred"]
                cm[idx[r["true"]], idx[r["pred"]]] += 1
            macro = float(np.mean([c / t for t, c in per.values()]))
            S.append(dict(run=run.name, split=split, n=n, top1=round(top1, 4),
                          top5=round(top5, 4), macro_acc=round(macro, 4)))
            PC += [dict(run=run.name, split=split, cls=c, n=t, correct=k_, acc=round(k_ / t, 4))
                   for c, (t, k_) in sorted(per.items())]
            for th in THRESHOLDS:
                ans = [r for r in rows if r["conf"] >= th]
                T.append(dict(run=run.name, split=split, threshold=th,
                              coverage=round(len(ans) / n, 4),
                              acc_on_answered=round(sum(r["true"] == r["pred"] for r in ans) / len(ans), 4) if ans else ""))
            plot_cm(cm, names, f"{run.name} - {split} (n={n}, top-1 {top1:.2f})",
                    out / f"cm_{run.name}_{split}.png")
            print(f"{run.name:14s} {split:10s} n={n:4d} top1={top1:.3f} top5={top5:.3f} macro={macro:.3f}", flush=True)
    for name, rows in (("predictions", P), ("summary", S), ("per_class", PC), ("threshold", T)):
        with open(out / f"{name}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
