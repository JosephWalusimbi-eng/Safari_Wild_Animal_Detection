"""make_figures.py - Part 2: report figures from saved results (no GPU, no images needed).

Reads  <runs>/<run>/results.csv  and  <results>/summary.csv, per_class.csv, threshold.csv
Writes <results>/figures/*.png

    python make_figures.py --runs ..\\runs --results ..\\results\\v1 --best v1_n_seed0
"""
import argparse, csv
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# reference palette (dataviz skill, light mode), fixed order
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
    "axes.titlesize": 11, "axes.titleweight": "bold", "legend.frameon": False,
})


def rd(p):
    with open(p, encoding="utf-8") as fh:
        return [{k.strip(): v for k, v in r.items()} for r in csv.DictReader(fh)]


def curves(runs_dir, names, out):
    fig, ax = plt.subplots(figsize=(7, 4))
    for n, col in zip(names, (BLUE, AQUA, YELLOW, ORANGE)):   # fixed palette order, one slot per run
        rows = rd(runs_dir / n / "results.csv")
        ep = [int(float(r["epoch"])) for r in rows]
        acc = [float(r["metrics/accuracy_top1"]) for r in rows]
        big = "_s_" in n
        ax.plot(ep, acc, color=col, lw=2,
                label=("YOLOv8s-cls" if big else "YOLOv8n-cls") + f" seed {n[-1]} (best {max(acc):.3f})")
    ax.set_xlabel("epoch"); ax.set_ylabel("validation top-1 accuracy"); ax.set_ylim(0, 1)
    ax.set_title("Training: validation accuracy per epoch"); ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout(); fig.savefig(out / "training_curves.png", dpi=150); plt.close(fig)


def test_vs_uwec(summary, out):
    runs = sorted({r["run"] for r in summary})
    get = {(r["run"], r["split"]): float(r["top1"]) for r in summary}
    n = {r["split"]: r["n"] for r in summary}
    fig, ax = plt.subplots(figsize=(7, 4))
    w = 0.38
    for k, (split, col, lab) in enumerate((("test", BLUE, f"web/park test (n={n.get('test')})"),
                                           ("uwec_test", ORANGE, f"UWEC phone photos (n={n.get('uwec_test')})"))):
        xs = [i + (k - 0.5) * (w + 0.02) for i in range(len(runs))]
        vals = [get.get((r, split), 0) for r in runs]
        ax.bar(xs, vals, w, color=col, label=lab)
        for x, v in zip(xs, vals):
            ax.text(x, v + 0.015, f"{v:.2f}", ha="center", fontsize=8, color=INK2)
    ax.set_xticks(range(len(runs)), runs); ax.set_ylim(0, 1.05); ax.set_ylabel("top-1 accuracy")
    ax.set_title("In-distribution test vs real phone photos", pad=28)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=8)
    ax.grid(axis="x", visible=False)
    fig.tight_layout(); fig.savefig(out / "test_vs_uwec.png", dpi=150); plt.close(fig)


def per_class(pc, run, split, out, title):
    rows = sorted([r for r in pc if r["run"] == run and r["split"] == split], key=lambda r: float(r["acc"]))
    if not rows:
        return
    fig, ax = plt.subplots(figsize=(6.5, 0.32 * len(rows) + 1.2))
    ys = range(len(rows))
    ax.barh(ys, [float(r["acc"]) for r in rows], 0.7, color=BLUE)
    for y, r in zip(ys, rows):
        ax.text(float(r["acc"]) + 0.01, y, f"{r['correct']}/{r['n']}", va="center", fontsize=8, color=INK2)
    ax.set_yticks(list(ys), [r["cls"] for r in rows], fontsize=8); ax.set_xlim(0, 1.12)
    ax.set_xlabel("accuracy (correct / images)"); ax.set_title(title); ax.grid(axis="y", visible=False)
    fig.tight_layout(); fig.savefig(out / f"per_class_{split}_{run}.png", dpi=150); plt.close(fig)


def threshold(th, run, out):
    fig, ax = plt.subplots(figsize=(7, 4))
    for split, col in (("test", BLUE), ("uwec_test", ORANGE)):
        rows = [r for r in th if r["run"] == run and r["split"] == split]
        t = [float(r["threshold"]) for r in rows]
        ax.plot(t, [float(r["coverage"]) for r in rows], color=col, lw=2, ls="--",
                label=f"{split}: share answered")
        ax.plot(t, [float(r["acc_on_answered"] or 0) for r in rows], color=col, lw=2, marker="o", ms=4,
                label=f"{split}: accuracy when answered")
    ax.set_xlabel("confidence threshold (below it the app says \"not sure\")"); ax.set_ylim(0, 1.02)
    ax.set_title(f"Choosing the \"not sure\" threshold ({run})"); ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout(); fig.savefig(out / f"threshold_{run}.png", dpi=150); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True); ap.add_argument("--results", required=True)
    ap.add_argument("--best", required=True)
    a = ap.parse_args()
    res = Path(a.results); out = res / "figures"; out.mkdir(parents=True, exist_ok=True)
    summary, pc, th = rd(res / "summary.csv"), rd(res / "per_class.csv"), rd(res / "threshold.csv")
    curves(Path(a.runs), sorted({r["run"] for r in summary}), out)
    test_vs_uwec(summary, out)
    per_class(pc, a.best, "uwec_test", out, f"UWEC phone photos, per class ({a.best})")
    per_class(pc, a.best, "test", out, f"Web/park test set, per class ({a.best})")
    threshold(th, a.best, out)
    print("figures in", out)


if __name__ == "__main__":
    main()
