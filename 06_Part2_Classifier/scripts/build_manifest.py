"""build_manifest.py - Part 2 (smartphone species classifier).

Walks the Entebbe photo folders and writes manifest.csv: one row per image with
the folder it came from, a proposed class, its likely source, a leakage group,
and keep/drop. Nothing is moved or edited; the manifest is the single place
where labels are corrected.

    python build_manifest.py --raw ..\\raw --out ..\\manifest.csv

Source is inferred from file evidence (names, sizes, metadata), NOT species:
  own_phone  - team photos at UWEC (shared via WhatsApp: ~960 px, no EXIF, or full-size
               phone originals). These form the real-world test set.
  images_cv  - images.cv export (has meta.json, 256x256, pre-split).
  inat_style - Genus_species_<id>_<n>.jpg / obs_<id>_<n>.jpg / <id>_<n>.jpg at ~500 px.
  web        - browser downloads (images (n).jpg, download.webp, etc.).
"""
import argparse, csv, hashlib, re
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, ImageOps, ExifTags

TAG = {v: k for k, v in ExifTags.TAGS.items()}
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ""}

# leaf folder -> proposed class (None = no class of its own; goes to 'other' pool)
FOLDER_CLASS = {
    "cheetahs": "cheetah", "foxes": "fox", "hyenas": "hyena", "jackals": "jackal",
    "leopards": "leopard", "lions": "lion", "tigers": "tiger", "weasels": "weasel",
    "wild_dogs": "wild_dog", "wolves": "wolf", "bats": "bat",
    "antelopes": "gazelle",            # these are gazelles, NOT Uganda kob
    "buffaloes": "buffalo", "elands": "eland", "elephants": "elephant",
    "gazelles": "gazelle", "giraffes": "giraffe", "impalas": "impala", "kudus": "kudu",
    "rhinos": "rhino", "waterbucks": "waterbuck", "wildebeest": "wildebeest",
    "zebras": "zebra", "kangaroos": "kangaroo", "koalas": "koala", "wombats": "wombat",
    "aardvarks": "aardvark", "hippopotamuses": "hippo", "pangolins": "pangolin",
    "shrews": "shrew", "warthogs": "warthog",
    "baboons": "monkey",               # folder holds Cercopithecus monkeys, not baboons
    "monkeys": "monkey", "bush_babies": "bush_baby", "chimpanzees": "chimpanzee",
    "gorillas": "gorilla", "lemurs": "lemur",
    "beavers": "beaver", "capybaras": "capybara", "mice": "rodent_small",
    "rats": "rodent_small", "porcupines": "porcupine", "rabbits": "rabbit",
    "squirrels": "squirrel",
    "ostriches": "bird", "owl": "bird", "parrots": "bird",
    "crocodiles": "crocodile",
    "cobras": "snake", "pythons": "snake", "vipers": "snake",
    "tortoises": "tortoise",
    "bees": None,
}
# whole subtrees mapped by an ancestor folder name
ANCESTOR_CLASS = {"frogs and toads": "frog", "5_fish": "fish"}

# individual corrections found by eye on the contact sheets (folder/file -> class or "DROP")
OVERRIDES = {
    "buffaloes/27.jpeg": "zebra", "buffaloes/28.jpeg": "zebra", "buffaloes/29.jpeg": "zebra",
    "buffaloes/30.jpeg": "zebra", "buffaloes/31.jpeg": "zebra",
    "buffaloes/images (4).jpg": "DROP:american bison, not African buffalo",
    "buffaloes/images.jpg": "DROP:domestic/water buffalo, not African buffalo",
}
FLAGS = {"cheetahs/images (3).jpg": "shutterstock watermark - never redistribute"}

INAT = re.compile(r"^(?:obs_)?(?:[A-Z][a-z]+_[a-z]+(?:_[a-z]+)*_)?(\d{5,})_\d+\.jpe?g$")
WEB = re.compile(r"^(images( ?\(?\d*\)?)?|download.*|[A-Za-z0-9]{20,}.*)(\.\w+)?$")
PHONE_DIMS = {960, 867, 1156, 1280}


def source_of(rel, f, w, h, make):
    if any(p.startswith("images.cv") for p in rel.parts):
        return "images_cv"
    if "uwec" in f.name.lower() or make.lower() == "samsung":
        return "own_phone"
    if INAT.match(f.name):
        return "inat_style"
    if f.suffix.lower() != ".webp" and (w in PHONE_DIMS or h in PHONE_DIMS) \
            and not WEB.match(f.name):
        return "own_phone"
    return "web"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = Path(a.raw)
    rows, seen = [], {}
    for f in sorted(raw.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in IMG_EXT or f.name == "meta.json":
            continue
        rel = f.relative_to(raw)
        parts = [p for p in rel.parts[:-1] if not p.startswith("images.cv")
                 and p not in ("data", "train", "val", "test")
                 and not p.startswith("animal ") and p not in ("leopard", "tiger")]
        leaf = next((p for p in reversed(parts) if p in FOLDER_CLASS), None)
        anc = next((ANCESTOR_CLASS[p] for p in parts if p in ANCESTOR_CLASS), None)
        cls = anc or (FOLDER_CLASS.get(leaf) if leaf else None)
        key = f"{leaf}/{f.name}"
        try:
            with Image.open(f) as im:
                ex = im.getexif()
                orient = ex.get(TAG["Orientation"], 1)
                w, h = ImageOps.exif_transpose(im).size
                make = str(ex.get(TAG["Make"], "")).strip("\x00 ")
        except Exception as e:
            rows.append(dict(path=str(rel), folder=leaf, cls="", source="", group="",
                             w=0, h=0, exif_rot=0, md5="", action="DROP", note=f"unreadable {e}"))
            continue
        md5 = hashlib.md5(f.read_bytes()).hexdigest()
        src = source_of(rel, f, w, h, make)
        m = INAT.match(f.name)
        group = (f"own:{leaf}" if src == "own_phone" else
                 f"inat:{m.group(1)}" if m and src == "inat_style" else f"file:{rel}")
        action, note = "KEEP", FLAGS.get(key, "")
        if key in OVERRIDES:
            o = OVERRIDES[key]
            if o.startswith("DROP"):
                action, note = "DROP", o[5:]
            else:
                note = f"relabelled {cls}->{o}"; cls = o
        if cls is None:
            action, note = "OTHER", "no class of its own"
        if md5 in seen:
            action, note = "DROP", f"exact duplicate of {seen[md5]}"
        else:
            seen[md5] = str(rel)
        rows.append(dict(path=str(rel), folder=leaf, cls=cls or "", source=src, group=group,
                         w=w, h=h, exif_rot=int(orient not in (1, None)), md5=md5,
                         action=action, note=note))

    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wr.writeheader(); wr.writerows(rows)

    keep = [r for r in rows if r["action"] == "KEEP"]
    tab = defaultdict(Counter)
    for r in keep:
        tab[r["cls"]][r["source"]] += 1
    srcs = ["own_phone", "inat_style", "web", "images_cv"]
    print(f"{'class':14s}" + "".join(f"{s:>11s}" for s in srcs) + f"{'total':>8s}")
    for c in sorted(tab, key=lambda c: -sum(tab[c].values())):
        print(f"{c:14s}" + "".join(f"{tab[c][s]:11d}" for s in srcs) + f"{sum(tab[c].values()):8d}")
    print(Counter(r["action"] for r in rows), " rotated-by-EXIF:", sum(r["exif_rot"] for r in rows))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
