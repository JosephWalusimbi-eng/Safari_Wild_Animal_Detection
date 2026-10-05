"""prepare_dataset_v2.py - format-aware default split.
Splits any session containing pillarboxed (padded portrait) frames into
<name>_land / <name>_port, crops the padding off the portrait frames,
and applies the chronological 70/15/15 split to each part separately.
Reuses helpers from prepare_dataset.py (unchanged)."""
import argparse, shutil
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image
import prepare_dataset as base

# Content strip of padded portrait frames, as fractions of frame width
# (measured from one sample: x = 656..1264 of 1920). Verify visually.
CONTENT_X = (656 / 1920, 1264 / 1920)
MIN_FRAMES_PER_FORMAT = 10
STATS = defaultdict(int)
TALLY = defaultdict(int)


def _sharp(a):
    return np.abs(np.diff(a, axis=1)).mean() + np.abs(np.diff(a, axis=0)).mean()


def is_pillarboxed(path):
    with Image.open(path) as im:
        g = np.asarray(im.convert("L").resize((480, 270)), dtype=np.float32)
    return _sharp(g[:, :134]) < 0.35 * _sharp(g[:, 192:288])


def crop_boxes(boxes, W, x0, x1):
    cw = x1 - x0
    out = []
    for cls, x, y, w, h in boxes:
        l, r = (x - w / 2) * W, (x + w / 2) * W
        cl, cr = max(l, x0), min(r, x1)
        if cr <= cl or (cr - cl) < 0.5 * (r - l):
            STATS["boxes_dropped"] += 1
            continue
        if cl > l or cr < r:
            STATS["boxes_clipped"] += 1
        out.append((cls, ((cl + cr) / 2 - x0) / cw, y, (cr - cl) / cw, h))
    return out


def write_unit(dst, split, unit, ibi, ids, src_dir, crop):
    img_dir, lbl_dir = dst / "images" / split, dst / "labels" / split
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for i in ids:
        rec = ibi[i]
        src = src_dir / rec["file"]
        if not src.exists() or rec["width"] is None:
            continue
        stem = f"{unit}_{Path(rec['file']).stem}"
        dst_img = img_dir / f"{stem}{src.suffix}"
        boxes = rec["boxes"]
        if crop:
            W, H = rec["width"], rec["height"]
            x0, x1 = round(crop[0] * W), round(crop[1] * W)
            with Image.open(src) as im:
                im.crop((x0, 0, x1, H)).save(dst_img)
            boxes = crop_boxes(boxes, W, x0, x1)
        else:
            shutil.copy2(src, dst_img)
        with open(lbl_dir / f"{stem}.txt", "w", encoding="utf-8") as f:
            for cls, x, y, w, h in boxes:
                f.write(f"{cls} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
                TALLY[base.FINAL_CLASSES[cls]] += 1
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    a = ap.parse_args()
    src_root, dst = Path(a.src), Path(a.dst)
    if dst.exists() and any(dst.iterdir()):
        raise SystemExit(f"{dst} is not empty - rename or remove it first.")
    dst.mkdir(parents=True, exist_ok=True)

    for folder in base.ALL_SESSIONS:
        print(f"\nSession: {folder}")
        ibi = base.load_session(src_root, folder)
        src_dir = src_root / folder
        ids = sorted(ibi, key=lambda i: ibi[i]["file"])
        flags = {i: is_pillarboxed(src_dir / ibi[i]["file"])
                 for i in ids if (src_dir / ibi[i]["file"]).exists()}
        n_pil = sum(flags.values())
        n_land = len(flags) - n_pil
        print(f"  frames: {len(flags)}  landscape: {n_land}  pillarboxed: {n_pil}")
        if n_pil >= MIN_FRAMES_PER_FORMAT and n_land >= MIN_FRAMES_PER_FORMAT:
            units = [(f"{folder}_land", [i for i in ids if i in flags and not flags[i]], None),
                     (f"{folder}_port", [i for i in ids if i in flags and flags[i]], CONTENT_X)]
            print("  -> splitting into land/port units, cropping port frames")
        else:
            units = [(folder, ids, None)]
        for unit, uids, crop in units:
            tr, va, te = base.chronological_blocks(uids)
            for split, sids in (("train", tr), ("val", va), ("test", te)):
                n = write_unit(dst, split, unit, ibi, sids, src_dir, crop)
                print(f"  {unit:22s} {split:5s} {n}")

    base.write_data_yaml(dst, "data.yaml")
    print("\nBoxes written per class:")
    for c in base.FINAL_CLASSES:
        print(f"  {c:12s} {TALLY[c]:5d}")
    print(f"  TOTAL {sum(TALLY.values())}  (original 3909; dropped by crop: "
          f"{STATS['boxes_dropped']}, clipped: {STATS['boxes_clipped']})")


if __name__ == "__main__":
    main()
