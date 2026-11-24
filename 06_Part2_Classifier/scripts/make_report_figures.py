"""make_report_figures.py - extra figures for the Part 2 report (charts and diagrams only, no photos).

    python make_report_figures.py --root .. --index <cls_v1\\index.csv> --out ..\\report\\figures

Reads only saved CSVs (manifest.csv, results\\v1, results\\v2, cls_v1\\index.csv, runs\\*\\results.csv).
"""
import argparse, csv, collections, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED, GRID = "#222222", "#555555", "#dddddd"
plt.rcParams.update({
    "font.family": "Times New Roman", "font.size": 11, "axes.edgecolor": "#888888",
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "figure.dpi": 100,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
})


def rd(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(fig, out, name):
    fig.tight_layout()
    fig.savefig(out / name, dpi=200, facecolor="white")
    plt.close(fig)
    print("wrote", name)


def box(ax, x, y, w, h, text):
    """Plain block: white fill, thin black border, square corners, black text."""
    ax.add_patch(plt.Rectangle((x, y), w, h, fc="white", ec="black", lw=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11, color="black")


def arrow(ax, x1, y1, x2, y2, label=None):
    """Straight black arrow; optional small label beside it."""
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color="black", lw=1.0))
    if label:
        ax.text((x1 + x2) / 2 + 0.08, (y1 + y2) / 2, label, fontsize=10, va="center")


def _canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off"); ax.grid(False)
    return fig, ax


def diagram_pipeline(out):
    """Proposed approach as a top-to-bottom flow (plain boxes and arrows)."""
    fig, ax = _canvas(8, 6.3)
    W, H, X, top, step = 5.6, 0.55, 0.9, 5.6, 0.86
    texts = ["Data sources: Part 1 park video frames + UWEC dataset",
             "Audit: record the source and correct label of every image",
             "Build dataset: 26 classes, split by session or photo group",
             "Train YOLOv8 classifiers (3 random seeds)",
             "Select the model on validation; evaluate on test sets",
             "Export the model (ONNX) to the phone app",
             "Offline field guide app for visitors"]
    ys = [top - k * step for k in range(len(texts))]
    for t, y in zip(texts, ys):
        box(ax, X, y, W, H, t)
    for y1, y2 in zip(ys[:-1], ys[1:]):
        arrow(ax, X + W / 2, y1, X + W / 2, y2 + H)
    # the team's own UWEC phone photos skip training and are used only for the real-world test
    bx, bw = 6.75, 1.2
    box(ax, bx, ys[2] - 0.15, bw, H + 0.3, "47 UWEC\nphone photos\n(test only)")
    ax.texts[-1].set_fontsize(9)
    ym = ys[4] + H / 2
    ax.plot([bx + bw / 2, bx + bw / 2], [ys[2] - 0.15, ym], color="black", lw=1.0)
    arrow(ax, bx + bw / 2, ym, X + W, ym)
    save(fig, out, "fig_pipeline.png")


def diagram_pwa(out):
    """How the app answers one photo (plain boxes and arrows)."""
    fig, ax = _canvas(8, 5.6)
    W, H, X = 5.0, 0.55, 1.5
    texts = ["Visitor takes or chooses a photo", "Rotate, resize and crop to 224 x 224",
             "Classifier runs on the phone", "Confidence of the best answer at least 0.7?"]
    ys = [4.9 - k * 0.86 for k in range(len(texts))]
    for t, y in zip(texts, ys):
        box(ax, X, y, W, H, t)
    for y1, y2 in zip(ys[:-1], ys[1:]):
        arrow(ax, X + W / 2, y1, X + W / 2, y2 + H)
    yb = ys[-1] - 1.25
    box(ax, 0.3, yb, 3.4, 0.75, "Show the animal: name in\nchosen language, facts, safety")
    box(ax, 4.3, yb, 3.4, 0.75, "Say \"not sure\" and ask for\na closer, clearer photo")
    arrow(ax, X + 1.0, ys[-1], 2.0, yb + 0.75, "yes")
    arrow(ax, X + W - 1.0, ys[-1], 6.0, yb + 0.75, "no")
    box(ax, 0.3, yb - 1.05, 3.4, H, "Visitor can record a sighting")
    arrow(ax, 2.0, yb, 2.0, yb - 1.05 + H)
    save(fig, out, "fig_pwa.png")


def fig_sources(root, index, out):
    man = rd(root / "manifest.csv")
    src = collections.Counter(r["source"] for r in man)
    names = {"images_cv": "images.cv", "inat_style": "iNaturalist-style", "web": "Web downloads",
             "own_phone": "Team phone photos (UWEC)"}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.9), gridspec_kw={"width_ratios": [1, 1.25]})
    keys = ["images_cv", "inat_style", "web", "own_phone"]
    vals = [src[k] for k in keys]
    a1.barh([names[k] for k in keys][::-1], vals[::-1], color=BLUE, height=0.6)
    for i, v in enumerate(vals[::-1]):
        a1.text(v + 40, i, f"{v:,}", va="center", fontsize=10, color=INK)
    a1.set_xlabel("images"); a1.set_xlim(0, max(vals) * 1.18)
    a1.set_title("(a) Sources of the 5,187 UWEC dataset images", fontsize=11)
    a1.grid(axis="y", visible=False)
    idx = rd(index)
    c = collections.Counter((r["split"], r["origin"]) for r in idx)
    splits = ["train", "val", "test", "uwec_test"]
    origins = [("safari_crop", "Part 1 crops", BLUE), ("images_cv", "images.cv", ORANGE),
               ("inat_style", "iNaturalist-style", AQUA), ("web", "Web", YELLOW),
               ("own_phone", "Team phone (UWEC)", "#6250d6")]
    left = [0] * 4
    for o, lab, col in origins:
        v = [c[(s, o)] for s in splits]
        a2.barh(splits[::-1], v[::-1], left=left[::-1], color=col, label=lab, height=0.6,
                edgecolor="white", linewidth=1)
        left = [l + x for l, x in zip(left, v)]
    for i, t in enumerate(left[::-1]):
        a2.text(t + 40, i, f"{t:,}", va="center", fontsize=10)
    a2.set_xlabel("images"); a2.set_xlim(0, max(left) * 1.15)
    a2.set_title("(b) Built dataset cls_v1 by split and origin", fontsize=11)
    a2.legend(fontsize=9, loc="lower right"); a2.grid(axis="y", visible=False)
    save(fig, out, "fig_sources.png")


def fig_split_counts(root, out):
    rows = []
    for line in (root / "cls_v1_build_log.txt").read_text().splitlines()[1:]:
        p = line.split()
        if len(p) >= 5 and p[0] not in ("totals", "class") and p[1].isdigit():
            rows.append((p[0], *map(int, p[1:5])))
    rows.sort(key=lambda r: r[1] + r[2] + r[3])
    fig, ax = plt.subplots(figsize=(8.5, 7.2))
    names = [r[0] for r in rows]
    left = [0] * len(rows)
    for j, (lab, col) in enumerate([("train", BLUE), ("val", AQUA), ("test", YELLOW), ("uwec_test", ORANGE)]):
        v = [r[j + 1] for r in rows]
        ax.barh(names, v, left=left, color=col, label=lab, height=0.7, edgecolor="white", linewidth=0.8)
        left = [l + x for l, x in zip(left, v)]
    for i, t in enumerate(left):
        ax.text(t + 5, i, str(t), va="center", fontsize=9)
    ax.set_xlabel("images"); ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", fontsize=10)
    ax.set_title("Images per class and split (cls_v1)", fontsize=12)
    save(fig, out, "fig_split_counts.png")


def fig_metrics_per_run(root, out):
    s = rd(root / "results/v1/summary.csv")
    runs = ["v1_n_seed0", "v1_n_seed1", "v1_n_seed2", "v1_s_seed0"]
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.9), sharey=True)
    for ax, split, title in [(axs[0], "test", "(a) In-distribution test (n = 559)"),
                             (axs[1], "uwec_test", "(b) UWEC phone photos (n = 47)")]:
        for k, (m, lab, col) in enumerate([("top1", "top-1", BLUE), ("top5", "top-5", AQUA),
                                           ("macro_acc", "macro (mean per class)", ORANGE)]):
            v = [float(next(r[m] for r in s if r["run"] == run and r["split"] == split)) for run in runs]
            xs = [i + (k - 1) * 0.26 for i in range(len(runs))]
            ax.bar(xs, v, width=0.24, color=col, label=lab)
            for x, y in zip(xs, v):
                ax.text(x, y + 0.015, f"{y:.2f}", ha="center", fontsize=8)
        ax.set_xticks(range(len(runs))); ax.set_xticklabels(runs, fontsize=9)
        ax.set_ylim(0, 1.1); ax.set_title(title, fontsize=11); ax.grid(axis="x", visible=False)
    axs[0].set_ylabel("accuracy"); axs[1].legend(fontsize=9, loc="upper right")
    save(fig, out, "fig_metrics_per_run.png")


def fig_confidence(root, out):
    p = [r for r in rd(root / "results/v1/predictions.csv") if r["run"] == "v1_n_seed2"]
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.7))
    bins = [i / 20 for i in range(21)]
    for ax, split, title in [(axs[0], "test", "(a) Test set (n = 559)"), (axs[1], "uwec_test", "(b) UWEC phone photos (n = 47)")]:
        ok = [float(r["conf"]) for r in p if r["split"] == split and r["true"] == r["pred"]]
        bad = [float(r["conf"]) for r in p if r["split"] == split and r["true"] != r["pred"]]
        ax.hist([ok, bad], bins=bins, color=[BLUE, ORANGE], label=[f"correct (n={len(ok)})", f"wrong (n={len(bad)})"],
                edgecolor="white", linewidth=0.6)
        ax.axvline(0.7, color="#333333", ls="--", lw=1); ax.text(0.68, ax.get_ylim()[1] * 0.92, "threshold 0.7", ha="right", fontsize=9)
        ax.set_xlabel("top-1 confidence"); ax.set_title(title, fontsize=11); ax.legend(fontsize=9, loc="upper left")
        ax.grid(axis="x", visible=False)
    axs[0].set_ylabel("images")
    save(fig, out, "fig_confidence.png")


def fig_v1_v2(root, out):
    s1, s2 = rd(root / "results/v1/summary.csv"), rd(root / "results/v2/summary.csv")
    pc1, pc2 = rd(root / "results/v1/per_class.csv"), rd(root / "results/v2/per_class.csv")
    reg, low = {"bird", "chimpanzee", "tiger", "zebra", "crocodile"}, {"lion", "buffalo", "cheetah"}

    def sub(pc, run, classes):
        r = [x for x in pc if x["run"] == run and x["split"] == "uwec_test" and x["cls"] in classes]
        return sum(int(x["correct"]) for x in r) / sum(int(x["n"]) for x in r)

    metrics = []
    for ver, s, pc in [("v1", s1, pc1), ("v2", s2, pc2)]:
        runs = [f"{ver}_n_seed{i}" for i in range(3)]
        t = [float(next(r["top1"] for r in s if r["run"] == x and r["split"] == "test")) for x in runs]
        u = [float(next(r["top1"] for r in s if r["run"] == x and r["split"] == "uwec_test")) for x in runs]
        g = [sub(pc, x, reg) for x in runs]
        l = [sub(pc, x, low) for x in runs]
        metrics.append([t, u, g, l])
    labs = ["Test top-1\n(n=559)", "UWEC top-1, all\n(n=47)", "UWEC, regular\nclasses (n=24)", "UWEC, low-data\nclasses (n=23)"]
    fig, ax = plt.subplots(figsize=(9, 4))
    for k, (ver, col) in enumerate([("v1 (original training images)", BLUE), ("v2 (+ phone-style augmentation)", ORANGE)]):
        m = [st.mean(v) for v in metrics[k]]; sd = [st.pstdev(v) for v in metrics[k]]
        xs = [i + (k - 0.5) * 0.36 for i in range(4)]
        ax.bar(xs, m, width=0.34, yerr=sd, capsize=4, color=col, label=ver, error_kw=dict(ecolor="#333333", lw=1))
        for x, y, e in zip(xs, m, sd):
            ax.text(x, y + e + 0.02, f"{y:.3f}", ha="center", fontsize=9)
    ax.set_xticks(range(4)); ax.set_xticklabels(labs); ax.set_ylim(0, 1.08)
    ax.set_ylabel("accuracy (mean of 3 seeds)"); ax.legend(fontsize=9, loc="upper right"); ax.grid(axis="x", visible=False)
    save(fig, out, "fig_v1_v2_summary.png")


def fig_val_curves_v2(root, out):
    fig, ax = plt.subplots(figsize=(9, 3.8))
    for ver, col in [("v1", BLUE), ("v2", ORANGE)]:
        for i, ls in zip(range(3), ["-", "--", ":"]):
            r = rd(root / f"runs/{ver}_n_seed{i}/results.csv")
            r = [{k.strip(): v for k, v in x.items()} for x in r]
            ax.plot([int(x["epoch"]) for x in r], [float(x["metrics/accuracy_top1"]) for x in r],
                    color=col, ls=ls, lw=1.5, label=f"{ver} seed {i}")
    ax.set_xlabel("epoch"); ax.set_ylabel("validation top-1"); ax.set_ylim(0.6, 0.95)
    ax.legend(ncol=2, fontsize=9, loc="lower right")
    save(fig, out, "fig_val_curves_v1_v2.png")


def fig_loss(root, out):
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
    for run, col in [("v1_n_seed0", BLUE), ("v1_n_seed1", AQUA), ("v1_n_seed2", YELLOW), ("v1_s_seed0", ORANGE)]:
        r = [{k.strip(): v for k, v in x.items()} for x in rd(root / f"runs/{run}/results.csv")]
        e = [int(x["epoch"]) for x in r]
        axs[0].plot(e, [float(x["train/loss"]) for x in r], color=col, lw=1.4, label=run)
        axs[1].plot(e, [float(x["val/loss"]) for x in r], color=col, lw=1.4, label=run)
    axs[0].set_title("(a) Training loss", fontsize=11); axs[1].set_title("(b) Validation loss", fontsize=11)
    for a in axs:
        a.set_xlabel("epoch")
    axs[0].set_ylabel("cross-entropy loss"); axs[1].legend(fontsize=9)
    save(fig, out, "fig_loss_curves.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True); ap.add_argument("--index", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    root, out = Path(a.root), Path(a.out); out.mkdir(parents=True, exist_ok=True)
    diagram_pipeline(out); diagram_pwa(out)
    fig_sources(root, Path(a.index), out); fig_split_counts(root, out)
    fig_metrics_per_run(root, out); fig_confidence(root, out); fig_v1_v2(root, out)
    fig_val_curves_v2(root, out); fig_loss(root, out)
