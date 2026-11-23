"""build_cls_dataset.py - Part 2: build an image-classification dataset (ImageFolder layout)
from (1) the Part 1 Safari boxes, cut out as crops, and (2) the Entebbe photos (manifest.csv).

Output (Ultralytics classify format):
    <out>/train/<class>/*.jpg   <out>/val/<class>/*.jpg   <out>/test/<class>/*.jpg
    <out>/uwec_test/<class>/*.jpg    team's own UWEC phone photos - NEVER trained on
    <out>/index.csv                  one row per written image (origin, split, group)

Split rules (leakage-safe, same spirit as Part 1):
  * Safari crops keep the exact Part 1 split of their frame (read from dataset_labels).
  * Entebbe web/iNat/images.cv photos: split by GROUP (an iNat observation's photos stay
    together) with a deterministic hash, 80/10/10.
  * own_phone photos -> uwec_test only.
  * Near-duplicates (dHash distance <= DUP_BITS) of a train image are removed from val/test.
  * Classes are capped per split so one big source cannot dominate.

    python build_cls_dataset.py --manifest ..\\manifest.csv --raw ..\\raw
        --safari D:\\...\\Safari_Dataset --labels D:\\...\\dataset_labels\\wildlife-yolo\\labels
        --out ..\\cls_v1
"""
import argparse, csv, hashlib, json, random, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps

# ---- class list (v1). Anything else that is kept goes to 'other'. ------------------
CLASSES = ["uganda_kob", "bird", "chimpanzee", "elephant", "gorilla", "hippo", "warthog",
           "tiger", "leopard", "fox", "frog", "snake", "fish", "zebra", "monkey",
           "crocodile", "tortoise", "giraffe", "rhino", "squirrel",
           # LOW-DATA classes (user decision 2026-11-22): fewer than 20 photos each, most of
           # them UWEC phone shots that are held out for testing. Expect poor accuracy until
           # more photos are collected. See DATA_NOTES.md.
           "lion", "buffalo", "cheetah", "kudu", "hyena",
           "other"]
LOW_DATA = {"lion", "buffalo", "cheetah", "kudu", "hyena"}
SAFARI_TO_CLS = {"antelope": "uganda_kob", "hog": "warthog"}   # others keep their name
CAP = {"train": 400, "val": 60, "test": 60}                    # per class, per split
MAX_SIDE = 512            # stored size; training runs at 224
CROP_PAD = 0.15           # context added around each Safari box
MIN_CROP = 32             # px, shorter side of the box; smaller boxes are skipped
DUP_BITS = 4
SEED = 0

# ---- Part 1 constants, copied so this script has no import dependency ---------------
RAW_CATEGORIES = {2: "hippo", 3: "bird", 4: "antelope", 5: "hog", 6: "monkey", 7: "elephant"}
MONKEY_REMAP = {"gorillas": "gorilla", "gorillas2": "gorilla", "gorillas3": "gorilla",
                "chimpanzees": "chimpanzee"}
SESSIONS = ["antelope", "chimpanzees", "elephant", "gorillas", "gorillas2", "gorillas3",
            "hippo", "hippo2", "hog"]


def save(im, path):
    im = im.convert("RGB")
    im.thumbnail((MAX_SIDE, MAX_SIDE))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, quality=92)


def dhash(path):
    with Image.open(path) as im:
        g = np.asarray(im.convert("L").resize((9, 8)), dtype=np.int16)
    return np.packbits((g[:, 1:] > g[:, :-1]).ravel())


def part1_split_map(labels_root):
    """(session, frame_stem) -> split, from Part 1's final label files."""
    m = {}
    for split in ("train", "val", "test"):
        for f in (labels_root / split).glob("*.txt"):
            stem = f.stem
            i = stem.index("_frame_")
            unit, frame = stem[:i], stem[i + 1:]
            session = unit.removesuffix("_land").removesuffix("_port")
            m[(session, frame)] = split
    return m


def safari_items(safari_root, labels_root):
    smap = part1_split_map(labels_root)
    missing = 0
    for session in SESSIONS:
        coco = json.loads((safari_root / session / "bbox_anno_coco.json").read_text(encoding="utf-8"))
        files = {im["id"]: Path(im["file_name"]).name for im in coco["images"]}
        for k, ann in enumerate(coco["annotations"]):
            raw = RAW_CATEGORIES.get(ann["category_id"])
            if raw is None:
                continue
            name = MONKEY_REMAP.get(session) if raw == "monkey" else raw
            if name is None:
                continue
            fname = files[ann["image_id"]]
            split = smap.get((session, Path(fname).stem))
            if split is None:
                missing += 1
                continue
            yield dict(cls=SAFARI_TO_CLS.get(name, name), split=split, origin="safari_crop",
                       group=f"safari:{session}", src=safari_root / session / fname,
                       box=ann["bbox"], key=f"{session}_{Path(fname).stem}_{k}")
    if missing:
        print(f"[note] {missing} Safari boxes had no Part 1 split (frame not in final dataset) - skipped")


def group_split(group):
    h = int(hashlib.md5(f"{SEED}:{group}".encode()).hexdigest(), 16) % 100
    return "train" if h < 80 else "val" if h < 90 else "test"


def entebbe_items(manifest, raw_root):
    with open(manifest, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["action"] == "DROP":
                continue
            cls = r["cls"] if r["cls"] in CLASSES and r["action"] == "KEEP" else "other"
            split = "uwec_test" if r["source"] == "own_phone" else group_split(r["group"])
            yield dict(cls=cls, split=split, origin=r["source"], group=r["group"],
                       src=raw_root / r["path"], box=None,
                       key=hashlib.md5(r["path"].encode()).hexdigest()[:12])


def main():
    ap = argparse.ArgumentParser()
    for a in ("manifest", "raw", "safari", "labels", "out"):
        ap.add_argument(f"--{a}", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} is not empty - remove it or choose another --out")
    rng = random.Random(SEED)

    items = list(safari_items(Path(a.safari), Path(a.labels)))
    items += list(entebbe_items(Path(a.manifest), Path(a.raw)))

    # cap per (split, class); uwec_test is never capped
    by = defaultdict(list)
    for it in items:
        by[(it["split"], it["cls"])].append(it)
    chosen = []
    for (split, cls), lst in by.items():
        rng.shuffle(lst)
        chosen += lst if split == "uwec_test" else lst[:CAP[split]]

    rows, skipped = [], Counter()
    for it in chosen:
        dst = out / it["split"] / it["cls"] / f"{it['origin']}_{it['key']}.jpg"
        try:
            with Image.open(it["src"]) as im:
                im = ImageOps.exif_transpose(im)
                if it["box"]:
                    x, y, w, h = it["box"]
                    if min(w, h) < MIN_CROP:
                        skipped["tiny_box"] += 1
                        continue
                    px, py = w * CROP_PAD, h * CROP_PAD
                    im = im.crop((max(0, x - px), max(0, y - py),
                                  min(im.width, x + w + px), min(im.height, y + h + py)))
                save(im, dst)
        except Exception as e:
            skipped[f"error {type(e).__name__}"] += 1
            continue
        rows.append(dict(split=it["split"], cls=it["cls"], origin=it["origin"],
                         group=it["group"], file=str(dst.relative_to(out)), src=str(it["src"])))

    # near-duplicate removal: val/test/uwec_test images too close to any train image
    train_h = np.stack([dhash(out / r["file"]) for r in rows if r["split"] == "train"])
    train_bits = np.unpackbits(train_h, axis=1)
    kept = []
    for r in rows:
        if r["split"] != "train":
            b = np.unpackbits(dhash(out / r["file"]))
            if (np.count_nonzero(train_bits != b, axis=1) <= DUP_BITS).any():
                (out / r["file"]).unlink()
                skipped[f"near_dup_in_{r['split']}"] += 1
                continue
        kept.append(r)

    with open(out / "index.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(kept[0])); wr.writeheader(); wr.writerows(kept)
    (out / "classes.txt").write_text("\n".join(CLASSES) + "\n", encoding="utf-8")
    for split in ("train", "val", "test", "uwec_test"):   # every class folder in every split
        for c in CLASSES:
            (out / split / c).mkdir(parents=True, exist_ok=True)

    t = defaultdict(Counter)
    for r in kept:
        t[r["cls"]][r["split"]] += 1
    sp = ["train", "val", "test", "uwec_test"]
    print(f"{'class':12s}" + "".join(f"{s:>10s}" for s in sp))
    for c in CLASSES:
        print(f"{c:12s}" + "".join(f"{t[c][s]:10d}" for s in sp) + ("   LOW-DATA" if c in LOW_DATA else ""))
    print("totals     " + "".join(f"{sum(t[c][s] for c in CLASSES):10d}" for s in sp))
    print("skipped:", dict(skipped))


if __name__ == "__main__":
    main()
