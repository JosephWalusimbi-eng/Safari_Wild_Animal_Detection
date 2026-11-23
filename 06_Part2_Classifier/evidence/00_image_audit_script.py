import sys, hashlib, re, csv
from pathlib import Path
from collections import defaultdict, Counter
from PIL import Image, ExifTags

roots = [Path(p) for p in sys.argv[1:-1]]
out = Path(sys.argv[-1])
TAG = {v: k for k, v in ExifTags.TAGS.items()}
rows = []
hashes = defaultdict(list)
for root in roots:
    for f in root.rglob("*"):
        if not f.is_file() or f.suffix.lower() in (".json",):
            continue
        rel = f.relative_to(root)
        parts = rel.parts
        # group = species folder; images.cv data collapses to its species
        if "images.cv" in str(rel):
            grp = "/".join(p for p in parts[:parts.index(next(p for p in parts if p.startswith("images.cv")))]) + " [images.cv]"
        else:
            grp = "/".join(parts[:-1])
        h = hashlib.md5(f.read_bytes()).hexdigest()
        hashes[h].append(str(rel))
        make = model = dt = ""
        w = hgt = 0
        try:
            with Image.open(f) as im:
                w, hgt = im.size
                ex = im.getexif()
                make = str(ex.get(TAG["Make"], "")).strip("\x00 ")
                model = str(ex.get(TAG["Model"], "")).strip("\x00 ")
                dt = str(ex.get(TAG["DateTime"], ""))
        except Exception as e:
            make = f"ERR {e.__class__.__name__}"
        rows.append(dict(root=root.name, group=grp, file=f.name, w=w, h=hgt, make=make, model=model, dt=dt, md5=h))

with open(out, "w", newline="", encoding="utf-8") as fh:
    wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
    wr.writeheader(); wr.writerows(rows)

by = defaultdict(list)
for r in rows:
    by[(r["root"], r["group"])].append(r)
print(f"{'group':70s} n  camEXIF  medW x medH  sample-names")
for (rt, g), rs in sorted(by.items()):
    cam = sum(1 for r in rs if r["make"] and not r["make"].startswith("ERR"))
    ws = sorted(r["w"] for r in rs); hs = sorted(r["h"] for r in rs)
    names = ", ".join(r["file"][:28] for r in rs[:2])
    print(f"{rt}:{g[-66:]:68s} {len(rs):4d} {cam:4d}  {ws[len(ws)//2]:5d}x{hs[len(hs)//2]:<5d} {names}")
cams = Counter((r["make"], r["model"]) for r in rows if r["make"] and not r["make"].startswith("ERR"))
print("\nCameras:", cams.most_common(15))
print("Dates:", Counter(r["dt"][:7] for r in rows if r["dt"]).most_common(10))
dups = [v for v in hashes.values() if len(v) > 1]
print(f"\nExact duplicate groups: {len(dups)}  (files involved {sum(len(v) for v in dups)})")
for v in dups[:8]:
    print("  ", v[:3])
print("Total images:", len(rows), " errors:", sum(1 for r in rows if r['make'].startswith('ERR')))
