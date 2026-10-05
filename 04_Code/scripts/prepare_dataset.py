"""
prepare_dataset.py

Converts the raw Safari_Dataset (9 per-session COCO-annotated folders) into
a YOLO-format dataset with:
  1. Species-level label recovery: 'monkey' boxes are remapped to 'gorilla'
     or 'chimpanzee' based on which session folder they came from.
  2. 'vulture' and 'hyena' categories dropped (declared in the schema but
     never annotated - 0 boxes across the whole dataset).
  3. Two split manifests:
       - default   : chronological block split (70/15/15) applied
                     independently within every session folder. This is
                     the Tier-2, leakage-safe split used for the baseline
                     and the S0-S5 ablation ladder.
       - leave_session_out : for the two classes with multiple independent
                     sessions (hippo, gorilla), hold out one whole session
                     entirely for testing. Used only for Experiment A
                     (cross-session generalization).

Usage:
    python prepare_dataset.py --src D:\\Safari_Wild_Animal_Detection\\Safari_Dataset --dst D:\\wildlife-yolo

Run this ONCE after scp'ing the raw dataset over. It does not modify the
source folder; it writes a new, YOLO-ready folder at --dst.
"""

import argparse
import json
import shutil
from pathlib import Path
from collections import defaultdict

from PIL import Image

# ---------------------------------------------------------------------------
# Fixed knowledge about this dataset, confirmed by direct inspection
# (see capstone proposal, Section 4). Do not change without re-verifying
# against the actual annotation files.
# ---------------------------------------------------------------------------

# Raw category id -> raw name, as declared in every session's COCO json
RAW_CATEGORIES = {
    0: "vulture",   # declared, 0 boxes anywhere - dropped
    1: "hyena",     # declared, 0 boxes anywhere - dropped
    2: "hippo",
    3: "bird",
    4: "antelope",  # working assumption: Uganda kob - verify visually before final report
    5: "hog",
    6: "monkey",    # ambiguous - remapped below using folder identity
    7: "elephant",
}

DROPPED_RAW_IDS = {0, 1}

# Folders whose 'monkey' boxes are actually one specific primate species.
# Confirmed single-species sessions (folder name + manual spot-check).
MONKEY_REMAP_BY_FOLDER = {
    "gorillas": "gorilla",
    "gorillas2": "gorilla",
    "gorillas3": "gorilla",
    "chimpanzees": "chimpanzee",
}

# Final YOLO class list (alphabetical, fixed order - this defines class ids
# used everywhere downstream, so do not reorder after training starts)
FINAL_CLASSES = ["antelope", "bird", "chimpanzee", "elephant", "gorilla", "hippo", "hog"]
CLASS_TO_ID = {name: i for i, name in enumerate(FINAL_CLASSES)}

# All 9 session folders expected on disk
ALL_SESSIONS = [
    "antelope", "chimpanzees", "elephant",
    "gorillas", "gorillas2", "gorillas3",
    "hippo", "hippo2", "hog",
]

# Multi-session classes used for the leave-session-out (Experiment A) split
LEAVE_SESSION_OUT_GROUPS = {
    "hippo": {"train": ["hippo2"], "test": ["hippo"]},
    "gorilla": {"train": ["gorillas", "gorillas2"], "test": ["gorillas3"]},
}

SPLIT_RATIOS = (0.70, 0.15, 0.15)  # train, val, test - chronological blocks


def resolve_final_class(raw_cat_id: int, folder_name: str):
    """Map a raw COCO category id, in the context of its source folder,
    to a final class name. Returns None if the box should be dropped."""
    if raw_cat_id in DROPPED_RAW_IDS:
        return None
    raw_name = RAW_CATEGORIES.get(raw_cat_id)
    if raw_name is None:
        return None
    if raw_name == "monkey":
        mapped = MONKEY_REMAP_BY_FOLDER.get(folder_name)
        if mapped is None:
            # 'monkey' box in a folder we don't have a confirmed mapping
            # for - skip rather than guess, and flag it loudly.
            print(f"  [WARN] 'monkey' box in unmapped folder '{folder_name}' - skipped")
            return None
        return mapped
    return raw_name


def coco_bbox_to_yolo(bbox, img_w, img_h):
    """COCO bbox is [x_min, y_min, width, height] in pixels.
    YOLO format is [x_center, y_center, width, height], normalized 0-1."""
    x_min, y_min, w, h = bbox
    x_center = (x_min + w / 2) / img_w
    y_center = (y_min + h / 2) / img_h
    w_norm = w / img_w
    h_norm = h / img_h
    return x_center, y_center, w_norm, h_norm


def load_session(src_root: Path, folder_name: str):
    """Load one session folder's annotation file and return per-image
    records: {image_filename: {"width":.., "height":.., "boxes":[(cls_id, x,y,w,h), ...]}}"""
    folder = src_root / folder_name
    json_path = folder / "bbox_anno_coco.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Missing annotation file: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        coco = json.load(f)

    # image_id -> record. Use basename of file_name, never the embedded
    # path, since the JSON's internal paths do not reliably match the
    # extracted folder layout on disk (e.g. 'Safari/antelope1/...' inside
    # the antelope/ folder).
    images_by_id = {}
    for img in coco["images"]:
        basename = Path(img["file_name"]).name
        images_by_id[img["id"]] = {
            "file": basename,
            "width": None,
            "height": None,
            "boxes": [],
        }

    # This dataset's COCO files do not include width/height on image
    # entries (non-standard), so read actual pixel dimensions from each
    # PNG file on disk instead.
    missing_files = 0
    for img_id, rec in images_by_id.items():
        img_path = folder / rec["file"]
        if not img_path.exists():
            missing_files += 1
            continue
        with Image.open(img_path) as im:
            rec["width"], rec["height"] = im.size

    if missing_files:
        print(f"  [WARN] {missing_files} image files listed in {folder_name}'s JSON were not found on disk")

    skipped_unknown_image = 0
    skipped_no_dims = 0
    for ann in coco["annotations"]:
        img_rec = images_by_id.get(ann["image_id"])
        if img_rec is None:
            skipped_unknown_image += 1
            continue
        if img_rec["width"] is None:
            skipped_no_dims += 1
            continue
        final_class = resolve_final_class(ann["category_id"], folder_name)
        if final_class is None:
            continue
        cls_id = CLASS_TO_ID[final_class]
        yolo_box = coco_bbox_to_yolo(ann["bbox"], img_rec["width"], img_rec["height"])
        img_rec["boxes"].append((cls_id, *yolo_box))

    if skipped_unknown_image:
        print(f"  [WARN] {skipped_unknown_image} annotations in {folder_name} referenced an unknown image id")
    if skipped_no_dims:
        print(f"  [WARN] {skipped_no_dims} annotations in {folder_name} skipped - image file missing, no dimensions")

    return images_by_id  # dict keyed by coco image id


def chronological_blocks(image_ids_sorted, ratios=SPLIT_RATIOS):
    """Split a chronologically-ordered list of image ids into
    train/val/test blocks (no shuffling - preserves temporal separation
    between splits to reduce near-duplicate-frame leakage)."""
    n = len(image_ids_sorted)
    n_train = int(n * ratios[0])
    n_val = int(n * ratios[1])
    train = image_ids_sorted[:n_train]
    val = image_ids_sorted[n_train:n_train + n_val]
    test = image_ids_sorted[n_train + n_val:]
    return train, val, test


def write_yolo_files(dst_root: Path, split: str, folder_name: str, images_by_id: dict, ids: list, src_images_dir: Path):
    img_out_dir = dst_root / "images" / split
    lbl_out_dir = dst_root / "labels" / split
    img_out_dir.mkdir(parents=True, exist_ok=True)
    lbl_out_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for img_id in ids:
        rec = images_by_id[img_id]
        src_img_path = src_images_dir / rec["file"]
        if not src_img_path.exists():
            print(f"  [WARN] image file missing on disk, skipped: {src_img_path}")
            continue

        # Prefix with folder name to guarantee unique filenames across
        # sessions (e.g. 'hippo_frame_0000_t000-27.png')
        out_stem = f"{folder_name}_{Path(rec['file']).stem}"
        dst_img_path = img_out_dir / f"{out_stem}{Path(rec['file']).suffix}"
        dst_lbl_path = lbl_out_dir / f"{out_stem}.txt"

        shutil.copy2(src_img_path, dst_img_path)
        with open(dst_lbl_path, "w", encoding="utf-8") as f:
            for cls_id, x, y, w, h in rec["boxes"]:
                f.write(f"{cls_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
        written += 1

    return written


def write_data_yaml(dst_root: Path, filename: str):
    yaml_path = dst_root / filename
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(f"path: {dst_root.as_posix()}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write("test: images/test\n")
        f.write(f"nc: {len(FINAL_CLASSES)}\n")
        f.write(f"names: {FINAL_CLASSES}\n")
    print(f"Wrote {yaml_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Path to Safari_Dataset folder (contains antelope/, gorillas/, etc.)")
    ap.add_argument("--dst", required=True, help="Output path for the YOLO-formatted dataset (default split)")
    ap.add_argument("--dst-lso", default=None, help="Optional separate output path for the leave-session-out split (Experiment A)")
    args = ap.parse_args()

    src_root = Path(args.src)
    dst_root = Path(args.dst)

    if dst_root.exists():
        print(f"[WARN] {dst_root} already exists - files may be overwritten/merged.")
    dst_root.mkdir(parents=True, exist_ok=True)

    class_box_counts = defaultdict(int)
    class_image_counts = defaultdict(int)

    print("=" * 70)
    print("PASS 1: default split (chronological block, per session)")
    print("=" * 70)

    for folder_name in ALL_SESSIONS:
        print(f"\nProcessing session: {folder_name}")
        images_by_id = load_session(src_root, folder_name)
        # Sort by filename (frames are named with zero-padded indices, so
        # lexicographic order == chronological order)
        sorted_ids = sorted(images_by_id.keys(), key=lambda i: images_by_id[i]["file"])

        train_ids, val_ids, test_ids = chronological_blocks(sorted_ids)
        src_images_dir = src_root / folder_name

        for split_name, ids in (("train", train_ids), ("val", val_ids), ("test", test_ids)):
            n_written = write_yolo_files(dst_root, split_name, folder_name, images_by_id, ids, src_images_dir)
            print(f"  {split_name}: {n_written} images")

        for img_id, rec in images_by_id.items():
            class_image_counts["__total__"] += 1
            for cls_id, *_ in rec["boxes"]:
                class_box_counts[FINAL_CLASSES[cls_id]] += 1

    write_data_yaml(dst_root, "data.yaml")

    print("\n" + "=" * 70)
    print("Per-class box counts after remap (should match proposal Section 4):")
    print("=" * 70)
    total = 0
    for name in FINAL_CLASSES:
        c = class_box_counts.get(name, 0)
        total += c
        print(f"  {name:12s} {c:5d}")
    print(f"  {'TOTAL':12s} {total:5d}   (expected: 3909)")

    # ---------------------------------------------------------------
    # PASS 2: leave-session-out split, only if requested
    # ---------------------------------------------------------------
    if args.dst_lso:
        dst_lso_root = Path(args.dst_lso)
        dst_lso_root.mkdir(parents=True, exist_ok=True)
        print("\n" + "=" * 70)
        print("PASS 2: leave-session-out split (Experiment A - hippo, gorilla)")
        print("=" * 70)

        for group_name, cfg in LEAVE_SESSION_OUT_GROUPS.items():
            print(f"\nGroup: {group_name}  train_sessions={cfg['train']}  test_session={cfg['test']}")
            for folder_name in cfg["train"]:
                images_by_id = load_session(src_root, folder_name)
                ids = list(images_by_id.keys())
                src_images_dir = src_root / folder_name
                n = write_yolo_files(dst_lso_root, "train", folder_name, images_by_id, ids, src_images_dir)
                print(f"  [train] {folder_name}: {n} images")
            for folder_name in cfg["test"]:
                images_by_id = load_session(src_root, folder_name)
                ids = list(images_by_id.keys())
                src_images_dir = src_root / folder_name
                n = write_yolo_files(dst_lso_root, "test", folder_name, images_by_id, ids, src_images_dir)
                print(f"  [test]  {folder_name}: {n} images")

        # val split for LSO: carve a small val set out of the train sessions
        # (reuse the default split's val images for those same sessions)
        print("\n[NOTE] For a val set under the leave-session-out split, reuse")
        print("       images/val from the default split for sessions in each")
        print("       group's 'train' list (already written in Pass 1).")

        write_data_yaml(dst_lso_root, "data.yaml")

    print("\nDone.")


if __name__ == "__main__":
    main()
