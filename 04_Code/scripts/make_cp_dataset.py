"""Build wildlife-yolo-cp = wildlife-yolo + N synthetic TRAIN images.
Synthetic image = a random original TRAIN frame with 1-3 SAM cutouts (antelope,
bird, elephant; cut out of TRAIN frames only) pasted in. val/test are hard-linked
unchanged. Original dataset is never modified."""
import csv, os, random, shutil, argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=400); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args(); random.seed(a.seed); np.random.seed(a.seed)
SRC = Path(r"C:\Users\mrjos\Downloads\wildlife-yolo"); DST = Path(r"C:\Users\mrjos\Downloads\wildlife-yolo-cp")
CUT = Path(r"C:\Users\mrjos\Downloads\wildlife-capstone\cutouts")
NAMES = ["antelope","bird","chimpanzee","elephant","gorilla","hippo","hog"]
PASTE = {"elephant":0.4, "bird":0.3, "antelope":0.3}       # class sampling weights
BIRD_FILL_MAX = 0.80                                          # drops big non-bird masks
if DST.exists() and any(DST.iterdir()): raise SystemExit(f"{DST} not empty")
def link(s, d):
    d.parent.mkdir(parents=True, exist_ok=True)
    try: os.link(s, d)
    except OSError: shutil.copy2(s, d)
for sp in ("train","val","test"):
    for kind in ("images","labels"):
        for f in (SRC/kind/sp).glob("*"): link(f, DST/kind/sp/f.name)
idx = list(csv.DictReader(open(CUT/"index.csv")))
lib = {c: [r for r in idx if r["class"]==c and (c!="bird" or float(r["fill"])<=BIRD_FILL_MAX)] for c in PASTE}
print({c: len(v) for c,v in lib.items()}, "cutouts available")
train_imgs = sorted((SRC/"images"/"train").glob("*.png"))
manifest = []
def overlap_frac(b, others):
    m = 0
    for o in others:
        iw = min(b[2],o[2])-max(b[0],o[0]); ih = min(b[3],o[3])-max(b[1],o[1])
        if iw>0 and ih>0: m = max(m, iw*ih/((b[2]-b[0])*(b[3]-b[1])))
    return m
made = 0; attempts = 0
while made < a.n and attempts < a.n*5:
    attempts += 1
    tf = random.choice(train_imgs)
    bg = Image.open(tf).convert("RGB"); W,H = bg.size
    lbl = [l.split() for l in (SRC/"labels"/"train"/(tf.stem+".txt")).read_text().splitlines() if l.strip()]
    occupied = []
    for c,x,y,w,h in lbl:
        x,y,w,h = map(float,(x,y,w,h)); occupied.append([(x-w/2)*W,(y-h/2)*H,(x+w/2)*W,(y+h/2)*H])
    new = []
    for _ in range(random.choice([1,2,3])):
        cls = random.choices(list(PASTE), weights=list(PASTE.values()))[0]
        r = random.choice(lib[cls])
        cut = Image.open(CUT/cls/r["file"]).convert("RGBA")
        s = (W/float(r["srcW"])) * random.uniform(0.5,1.5)
        nw, nh = max(int(cut.width*s),1), max(int(cut.height*s),1)
        if nw > 0.35*W or nh > 0.35*H: s *= min(0.35*W/nw, 0.35*H/nh); nw,nh = max(int(cut.width*s),1), max(int(cut.height*s),1)
        if nw < 10 or nh < 10 or nw >= W or nh >= H: continue
        cut = cut.resize((nw,nh), Image.LANCZOS)
        if random.random() < 0.5: cut = cut.transpose(Image.FLIP_LEFT_RIGHT)
        al = cut.getchannel("A").filter(ImageFilter.GaussianBlur(0.8)); cut.putalpha(al)
        for _try in range(25):
            x0 = random.randint(0, W-nw); y0 = random.randint(0, H-nh); box = [x0,y0,x0+nw,y0+nh]
            if overlap_frac(box, occupied) <= 0.05: break
        else: continue
        bg.paste(cut, (x0,y0), cut); occupied.append(box); new.append((NAMES.index(cls), box, r["file"]))
    if not new: continue
    name = f"cp_{made:04d}_{tf.stem}"
    bg.save(DST/"images"/"train"/f"{name}.png")
    with open(DST/"labels"/"train"/f"{name}.txt","w") as f:
        for l in lbl: f.write(" ".join(l)+"\n")
        for c,b,_ in new: f.write(f"{c} {(b[0]+b[2])/2/W:.6f} {(b[1]+b[3])/2/H:.6f} {(b[2]-b[0])/W:.6f} {(b[3]-b[1])/H:.6f}\n")
    for c,b,src in new: manifest.append([name, tf.stem, NAMES[c], src])
    made += 1
with open(DST/"cp_manifest.csv","w",newline="") as fh:
    w = csv.writer(fh); w.writerow(["synthetic","background","pasted_class","cutout"]); w.writerows(manifest)
(DST/"data.yaml").write_text(f"path: {DST.as_posix()}\ntrain: images/train\nval: images/val\ntest: images/test\nnc: 7\nnames: {NAMES}\n")
from collections import Counter
print("synthetic images:", made, "pasted per class:", dict(Counter(m[2] for m in manifest)))
