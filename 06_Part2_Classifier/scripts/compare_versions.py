"""compare_versions.py - v1 vs v2 (same model, seeds, settings; only training images differ).

Reads results\\<v>\\predictions.csv and runs\\<run>\\results.csv. Writes results\\compare_v1_v2.md and prints it.
Reports: mean +/- std over the 3 small-model seeds (test, UWEC, UWEC regular classes, UWEC low-data
classes); UWEC per class; paired per-image changes (right->wrong, wrong->right) summed over seeds;
best validation top-1 and epochs (the 3x-steps-per-epoch confound).

    python compare_versions.py --root ..
"""
import argparse, csv, statistics as st
from collections import defaultdict
from pathlib import Path

LOW = {"lion", "buffalo", "cheetah", "kudu", "hyena"}
ap = argparse.ArgumentParser(); ap.add_argument("--root", required=True); a = ap.parse_args()
root = Path(a.root)


def preds(v):
    d = defaultdict(dict)                      # run -> (split,file) -> (true,pred)
    with open(root / "results" / v / "predictions.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            d[r["run"]][(r["split"], r["file"])] = (r["true"], r["pred"])
    return d


def acc(rows):
    return sum(t == p for t, p in rows) / len(rows) if rows else float("nan")


def ms(xs):
    return f"{st.mean(xs):.3f} ± {st.pstdev(xs):.3f}" if len(xs) > 1 else f"{xs[0]:.3f}"


P = {"v1": preds("v1"), "v2": preds("v2")}
runs = {v: [f"{v}_n_seed{s}" for s in (0, 1, 2)] for v in P}
out = ["# v1 vs v2 (small model, 3 seeds each)\n",
       "Mean ± population std over seeds. UWEC = 47 team phone photos (never trained on).\n",
       "| Metric | v1 | v2 |", "|---|---|---|"]


def metric(name, sel):
    out.append(f"| {name} | " + " | ".join(
        ms([acc([tp for (sp, f), tp in P[v][r].items() if sel(sp, tp[0])]) for r in runs[v]]) for v in ("v1", "v2")) + " |")


metric("test top-1 (n=559)", lambda sp, t: sp == "test")
metric("UWEC top-1, all (n=47)", lambda sp, t: sp == "uwec_test")
metric("UWEC top-1, regular classes (n=24: bird 8, chimp 7, tiger 3, zebra 5, croc 1)", lambda sp, t: sp == "uwec_test" and t not in LOW)
metric("UWEC top-1, low-data classes (n=23: lion 9, buffalo 9, cheetah 5)", lambda sp, t: sp == "uwec_test" and t in LOW)

out += ["", "## UWEC correct per class, per seed (v1 | v2)", "", "| class | n | v1 seeds 0/1/2 | v2 seeds 0/1/2 |", "|---|---|---|---|"]
classes = sorted({t for (sp, f), (t, p) in P["v1"][runs["v1"][0]].items() if sp == "uwec_test"})
for c in classes:
    row = []
    for v in ("v1", "v2"):
        row.append("/".join(str(sum(t == p for (sp, f), (t, p) in P[v][r].items() if sp == "uwec_test" and t == c)) for r in runs[v]))
    n = sum(1 for (sp, f), (t, p) in P["v1"][runs["v1"][0]].items() if sp == "uwec_test" and t == c)
    out.append(f"| {c} | {n} | {row[0]} | {row[1]} |")

out += ["", "## Paired UWEC changes, seed s of v1 vs seed s of v2 (summed over 3 seeds, 141 image-seeds)", ""]
w2r = r2w = 0
for s in (0, 1, 2):
    for k, (t, p1) in P["v1"][f"v1_n_seed{s}"].items():
        if k[0] != "uwec_test":
            continue
        p2 = P["v2"][f"v2_n_seed{s}"][k][1]
        w2r += (p1 != t) and (p2 == t); r2w += (p1 == t) and (p2 != t)
out.append(f"wrong->right: {w2r}   right->wrong: {r2w}   (net {w2r - r2w:+d})")

out += ["", "## Validation (selection metric) and training length", "", "| run | best val top-1 | epoch of best | epochs run |", "|---|---|---|---|"]
for v in ("v1", "v2"):
    for r in runs[v]:
        rows = list(csv.DictReader(open(root / "runs" / r / "results.csv", encoding="utf-8")))
        rows = [{k.strip(): x for k, x in q.items()} for q in rows]
        b = max(rows, key=lambda q: float(q["metrics/accuracy_top1"]))
        out.append(f"| {r} | {float(b['metrics/accuracy_top1']):.3f} | {b['epoch']} | {len(rows)} |")
txt = "\n".join(out)
(root / "results" / "compare_v1_v2.md").write_text(txt + "\n", encoding="utf-8")
print(txt)
