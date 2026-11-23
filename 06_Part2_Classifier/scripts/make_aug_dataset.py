"""make_aug_dataset.py - Part 2 v2: cls_v1 + phone-domain augmented copies of the TRAIN images.

val / test / uwec_test are copied from cls_v1 unchanged, so v1 and v2 are compared on identical
evaluation images. Only train changes: every original is kept, plus K augmented copies of each.

Recipe (fixed before seeing any v2 result; every step has the SAME probability for every class,
so the augmentation cannot become a class shortcut):
  0. Safari crops are re-cut from the raw video frame with random context padding
     U(0.15, 1.5) x box size, so the animal is sometimes small in the frame, as in phone photos
     (real surrounding scene, not synthetic borders). Other images start from the stored train image.
  1. p=0.7  source-style homogenisation: shorter side down to U(80, 500) px and back up;
            JPEG re-save at quality U(30, 80) (WhatsApp-like); p=0.3 extra Gaussian blur.
            Every class has one dominant source (video crops / images.cv / iNat), which the model
            could otherwise learn instead of the animal.
  2. p=0.3  synthetic chain-link fence overlay (UWEC animals are photographed through fences).
            Disclosure: this idea came from looking at the UWEC photos, i.e. the test domain.
  3. p=0.5  exposure / contrast / saturation jitter.
Ultralytics' own online augmentation (RandAugment, flips, erasing) still runs during training.

    python make_aug_dataset.py --src ..\\cls_v1 --safari <Safari_Dataset> --out ..\\cls_v2 --k 2
"""
import argparse, csv, json, math, random, shutil, sys
from collections import Counter
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

SEED, MAX_SIDE = 0, 512
OVERLAP_MAX = 0.2   # a crop may contain at most 20% of a bigger other-class box (first try: 0.5, too loose)
MIN_SIDE = 24       # skip degenerate (tiny / sliver) crops


def context_crop(frame, box, others, rng):
    """Random context padding, shrunk until the crop does not take in >= half of a DIFFERENT-class
    box that is at least as big as the target (e.g. Part 1 birds are egrets standing on hippos:
    a wide 'bird' crop would otherwise be a hippo picture labelled bird). Found on the v2 contact
    sheet, LOG Entry 8."""
    x, y, w, h = box
    W, H = frame.size
    p = rng.uniform(0.15, 1.5)
    while True:
        c = (max(0, x - p * w), max(0, y - p * h), min(W, x + w + p * w), min(H, y + h + p * h))
        bad = False
        for ox, oy, ow, oh in others:
            if ow * oh < w * h:
                continue
            ix = max(0, min(c[2], ox + ow) - max(c[0], ox)); iy = max(0, min(c[3], oy + oh) - max(c[1], oy))
            if ix * iy >= OVERLAP_MAX * ow * oh:
                bad = True; break
        if not bad:
            return frame.crop(c)
        if p <= 0.15:
            return None          # even the tightest crop is dominated by another animal: skip this copy
        p = max(0.15, p * 0.6)


def homogenise(im, rng):
    s = rng.uniform(80, 500)
    w, h = im.size
    r = s / min(w, h)
    if r < 1:
        im = im.resize((max(1, round(w * r)), max(1, round(h * r))), Image.BILINEAR).resize((w, h), Image.BILINEAR)
    buf = BytesIO(); im.save(buf, "JPEG", quality=rng.randint(30, 80)); buf.seek(0)
    im = Image.open(buf).convert("RGB")
    if rng.random() < 0.3:
        im = im.filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 1.2)))
    return im


def fence(im, rng):
    w, h = im.size
    layer = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sp = rng.uniform(0.04, 0.12) * max(w, h)               # mesh cell size
    lw = max(1, round(rng.uniform(0.004, 0.012) * max(w, h)))
    g = rng.randint(60, 200)
    col = (g, g, g + rng.randint(-10, 10), rng.randint(140, 230))
    L = 2 * max(w, h)
    for ang in (rng.uniform(35, 55), rng.uniform(125, 145)):
        dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        nx, ny = -dy, dx
        k = -L
        while k < L:
            cx, cy = w + nx * k, h + ny * k
            d.line([(cx - dx * L, cy - dy * L), (cx + dx * L, cy + dy * L)], fill=col, width=lw)
            k += sp
    layer = layer.crop((w // 2, h // 2, w // 2 + w, h // 2 + h))
    if rng.random() < 0.6:                                 # fence out of focus
        layer = layer.filter(ImageFilter.GaussianBlur(rng.uniform(0.5, 2.5)))
    out = im.convert("RGBA"); out.alpha_composite(layer)
    return out.convert("RGB")


def jitter(im, rng):
    im = ImageEnhance.Brightness(im).enhance(rng.uniform(0.7, 1.3))
    im = ImageEnhance.Contrast(im).enhance(rng.uniform(0.8, 1.2))
    return ImageEnhance.Color(im).enhance(rng.uniform(0.7, 1.3))


def safari_box(safari, fname, cache):
    # file name: safari_crop_<session>_<frame stem>_<annotation index>.jpg
    stem = fname[len("safari_crop_"):-4]
    rest, k = stem.rsplit("_", 1)
    i = rest.index("_frame_")
    session, frame = rest[:i], rest[i + 1:]
    if session not in cache:
        cache[session] = json.loads((safari / session / "bbox_anno_coco.json").read_text(encoding="utf-8"))
    coco = cache[session]
    ann = coco["annotations"][int(k)]
    img = next(im for im in coco["images"] if im["id"] == ann["image_id"])
    others = [o["bbox"] for o in coco["annotations"]
              if o["image_id"] == ann["image_id"] and o["category_id"] != ann["category_id"]]
    return safari / session / Path(img["file_name"]).name, ann["bbox"], others


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True); ap.add_argument("--safari", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--k", type=int, default=2)
    a = ap.parse_args()
    src, out, safari = Path(a.src), Path(a.out), Path(a.safari)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} is not empty")
    rng = random.Random(SEED)
    for split in ("val", "test", "uwec_test"):
        shutil.copytree(src / split, out / split)
    shutil.copy2(src / "classes.txt", out / "classes.txt")
    used, cache, n = Counter(), {}, Counter()
    for cdir in sorted((src / "train").iterdir()):
        dst = out / "train" / cdir.name; dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(cdir.glob("*.jpg")):
            shutil.copy2(f, dst / f.name); n[cdir.name] += 1
            for j in range(a.k):
                if f.name.startswith("safari_crop_"):
                    p, box, others = safari_box(safari, f.name, cache)
                    with Image.open(p) as fr:
                        im = context_crop(ImageOps.exif_transpose(fr).convert("RGB"), box, others, rng)
                    if im is None or min(im.size) < MIN_SIDE:
                        used["skipped_dominated_or_tiny"] += 1
                        continue
                    used["context_crop"] += 1
                else:
                    im = Image.open(f).convert("RGB")
                im.thumbnail((MAX_SIDE, MAX_SIDE))
                if rng.random() < 0.7: im = homogenise(im, rng); used["homogenise"] += 1
                if rng.random() < 0.3: im = fence(im, rng); used["fence"] += 1
                if rng.random() < 0.5: im = jitter(im, rng); used["jitter"] += 1
                im.save(dst / f"{f.stem}_aug{j}.jpg", quality=92); n[cdir.name] += 1
    print("train images per class:", dict(n))
    print("total train:", sum(n.values()), " steps applied:", dict(used))


if __name__ == "__main__":
    main()
