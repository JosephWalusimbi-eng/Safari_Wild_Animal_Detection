"""make_compare_figure.py - v1 vs v2 on the UWEC phone photos, per class (mean over 3 seeds).

    python make_compare_figure.py --root ..
Writes results\\compare_v1_v2.png
"""
import argparse, csv
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE, ORANGE = "#2a78d6", "#eb6834"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
                     "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.grid": True, "grid.color": GRID, "axes.spines.top": False,
                     "axes.spines.right": False, "legend.frameon": False, "font.size": 10})
ap = argparse.ArgumentParser(); ap.add_argument("--root", required=True); a = ap.parse_args()
root = Path(a.root)
acc = {v: defaultdict(list) for v in ("v1", "v2")}      # class -> per-seed correct fraction
tot = defaultdict(int)
for v in acc:
    per = defaultdict(lambda: defaultdict(lambda: [0, 0]))   # run -> class -> [n, correct]
    for r in csv.DictReader(open(root / "results" / v / "predictions.csv", encoding="utf-8")):
        if r["split"] != "uwec_test" or not r["run"].startswith(f"{v}_n_"):
            continue
        per[r["run"]][r["true"]][0] += 1; per[r["run"]][r["true"]][1] += r["true"] == r["pred"]
    for run, d in per.items():
        for c, (n, k) in d.items():
            acc[v][c].append(k / n); tot[c] = n
classes = sorted(tot, key=lambda c: -tot[c])
fig, ax = plt.subplots(figsize=(7.5, 4))
w = 0.38
for k, (v, col, lab) in enumerate((("v1", BLUE, "v1 (original training images)"), ("v2", ORANGE, "v2 (+ phone-style augmentation)"))):
    xs = [i + (k - 0.5) * (w + 0.02) for i in range(len(classes))]
    vals = [sum(acc[v][c]) / len(acc[v][c]) for c in classes]
    ax.bar(xs, vals, w, color=col, label=lab)
    for x, val in zip(xs, vals):
        ax.text(x, val + 0.015, f"{val:.2f}", ha="center", fontsize=7, color=INK2)
ax.set_xticks(range(len(classes)), [f"{c}\n(n={tot[c]})" for c in classes], fontsize=8)
ax.set_ylim(0, 1.1); ax.set_ylabel("share of UWEC photos correct\n(mean of 3 seeds)")
ax.set_title("Phone-photo accuracy per animal: augmentation did not help", pad=26)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=8); ax.grid(axis="x", visible=False)
fig.tight_layout(); fig.savefig(root / "results" / "compare_v1_v2.png", dpi=150)
print("wrote", root / "results" / "compare_v1_v2.png")
