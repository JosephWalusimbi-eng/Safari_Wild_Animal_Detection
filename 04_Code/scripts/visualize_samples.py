"""
visualize_samples.py

Sanity check for prepare_dataset.py's output. Draws the converted YOLO
bounding boxes back onto a handful of sample images per session and saves
them as PNGs, so you can visually confirm:
  1. The COCO -> YOLO coordinate conversion is correct (boxes actually sit
     on the animals, not offset or mis-scaled).
  2. What each class really looks like - in particular, settling the
     'antelope' identification question from the proposal.

Runs on CPU. Safe to run in a second terminal while GPU training is going
in another window - it does not touch the GPU.

Usage:
    python visualize_samples.py --dataset C:\\Users\\mrjos\\Downloads\\wildlife-yolo --out C:\\Users\\mrjos\\Downloads\\visual_check --per-session 2
"""

import argparse
import random
import yaml
from pathlib import Path
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont

# Known session-name prefixes used by prepare_dataset.py when writing
# output filenames ("{folder_name}_{original_stem}{ext}")
ALL_SESSIONS = [
    "antelope", "chimpanzees", "elephant",
    "gorillas", "gorillas2", "gorillas3",
    "hippo", "hippo2", "hog",
]

BOX_COLOR = (255, 60, 60)
TEXT_BG = (255, 60, 60)


def load_class_names(dataset_root: Path):
    with open(dataset_root / "data.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    names = data["names"]
    # 'names' may be a list or a dict depending on how PyYAML parsed it
    if isinstance(names, dict):
        return [names[i] for i in range(len(names))]
    return names


def session_of(filename: str):
    """Recover which session a converted file came from, based on its
    '{session}_{original_stem}' naming prefix. Checks longest names first
    so 'gorillas2' isn't mistaken for 'gorillas'."""
    for session in sorted(ALL_SESSIONS, key=len, reverse=True):
        if filename.startswith(session + "_"):
            return session
    return "UNKNOWN"


def draw_boxes(img_path: Path, label_path: Path, class_names: list, out_path: Path):
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()

    n_boxes = 0
    if label_path.exists():
        with open(label_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                cls_id, xc, yc, bw, bh = parts
                cls_id = int(cls_id)
                xc, yc, bw, bh = float(xc), float(yc), float(bw), float(bh)

                # YOLO normalized -> pixel corners
                x1 = (xc - bw / 2) * w
                y1 = (yc - bh / 2) * h
                x2 = (xc + bw / 2) * w
                y2 = (yc + bh / 2) * h

                label = class_names[cls_id] if cls_id < len(class_names) else f"id{cls_id}"
                draw.rectangle([x1, y1, x2, y2], outline=BOX_COLOR, width=4)
                text_y = max(0, y1 - 28)
                draw.rectangle([x1, text_y, x1 + 10 + len(label) * 13, text_y + 26], fill=TEXT_BG)
                draw.text((x1 + 5, text_y + 2), label, fill=(255, 255, 255), font=font)
                n_boxes += 1

    img.save(out_path)
    return n_boxes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="Path to the YOLO dataset folder (output of prepare_dataset.py)")
    ap.add_argument("--out", required=True, help="Where to save annotated sample images")
    ap.add_argument("--split", default="train", choices=["train", "val", "test"])
    ap.add_argument("--per-session", type=int, default=2, help="How many sample images to draw per session")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    random.seed(args.seed)
    dataset_root = Path(args.dataset)
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    class_names = load_class_names(dataset_root)
    print(f"Classes: {class_names}")

    img_dir = dataset_root / "images" / args.split
    lbl_dir = dataset_root / "labels" / args.split

    all_images = sorted(img_dir.glob("*.png")) + sorted(img_dir.glob("*.jpg"))
    by_session = defaultdict(list)
    for p in all_images:
        by_session[session_of(p.name)].append(p)

    print(f"\nFound images for {len(by_session)} sessions in {args.split} split:")
    for session, files in sorted(by_session.items()):
        print(f"  {session:15s} {len(files)} images")

    print(f"\nSampling {args.per_session} image(s) per session -> {out_root}\n")

    total_written = 0
    for session, files in sorted(by_session.items()):
        if session == "UNKNOWN":
            print(f"  [WARN] {len(files)} images did not match any known session prefix - skipping")
            continue
        sample = random.sample(files, min(args.per_session, len(files)))
        for img_path in sample:
            label_path = lbl_dir / f"{img_path.stem}.txt"
            out_path = out_root / f"{img_path.stem}_annotated.png"
            n_boxes = draw_boxes(img_path, label_path, class_names, out_path)
            print(f"  [{session}] {img_path.name} -> {n_boxes} box(es) drawn -> {out_path.name}")
            total_written += 1

    print(f"\nDone. {total_written} annotated images written to {out_root}")
    print("Open that folder and check: do the boxes sit tightly on the animals,")
    print("and does the label match what's actually in the frame? Pay special")
    print("attention to the 'antelope' samples.")


if __name__ == "__main__":
    main()
