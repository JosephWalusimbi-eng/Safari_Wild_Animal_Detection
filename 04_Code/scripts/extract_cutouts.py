"""Cut every TRAIN-split animal out of its frame using SAM, prompted with its box.
Writes RGBA crops to cutouts/<class>/ plus cutouts/index.csv. Val/test never read."""
import csv, collections
from pathlib import Path
import numpy as np
from PIL import Image
from ultralytics import SAM
R = Path(r"C:\Users\mrjos\Downloads\wildlife-yolo")
OUT = Path(r"C:\Users\mrjos\Downloads\wildlife-capstone\cutouts")
NAMES = ["antelope","bird","chimpanzee","elephant","gorilla","hippo","hog"]
FILL_MIN, FILL_MAX, NEIGH_MAX, MIN_SIDE = 0.25, 0.97, 0.30, 12
sam = SAM("sam_b.pt")
for n in NAMES: (OUT/n).mkdir(parents=True, exist_ok=True)
rows, stat = [], collections.Counter()
imgs = sorted((R/"images"/"train").glob("*.png"))
for k, f in enumerate(imgs):
    im = Image.open(f).convert("RGB"); W, H = im.size
    boxes = []
    for l in (R/"labels"/"train"/(f.stem+".txt")).read_text().splitlines():
        if not l.strip(): continue
        c,x,y,w,h = l.split(); c=int(c); x,y,w,h = map(float,(x,y,w,h))
        boxes.append((c, np.array([(x-w/2)*W,(y-h/2)*H,(x+w/2)*W,(y+h/2)*H])))
    if not boxes: continue
    res = sam(str(f), bboxes=[b.tolist() for _,b in boxes], verbose=False)[0]
    masks = res.masks.data.cpu().numpy().astype(bool)
    arr = np.asarray(im)
    for i,(c,b) in enumerate(boxes):
        x0,y0,x1,y1 = [int(round(v)) for v in b]; x0=max(x0,0);y0=max(y0,0);x1=min(x1,W);y1=min(y1,H)
        stat[(NAMES[c],"total")] += 1
        if x1-x0 < MIN_SIDE or y1-y0 < MIN_SIDE: stat[(NAMES[c],"too_small")] += 1; continue
        area = (x1-x0)*(y1-y0)
        contaminated = False
        for j,(_,b2) in enumerate(boxes):
            if j==i: continue
            iw = min(x1,b2[2])-max(x0,b2[0]); ih = min(y1,b2[3])-max(y0,b2[1])
            if iw>0 and ih>0 and iw*ih/area > NEIGH_MAX: contaminated = True
        if contaminated: stat[(NAMES[c],"overlaps_neighbour")] += 1; continue
        m = masks[i][y0:y1, x0:x1]
        fill = m.sum()/area
        if not (FILL_MIN <= fill <= FILL_MAX): stat[(NAMES[c],"bad_fill")] += 1; continue
        rgba = np.dstack([arr[y0:y1,x0:x1], (m*255).astype(np.uint8)])
        name = f"{f.stem}_{i}.png"
        Image.fromarray(rgba, "RGBA").save(OUT/NAMES[c]/name)
        rows.append([NAMES[c], name, f.stem, x1-x0, y1-y0, W, H, round(float(fill),3)])
        stat[(NAMES[c],"kept")] += 1
    if k % 100 == 0: print(k, "/", len(imgs), flush=True)
with open(OUT/"index.csv","w",newline="") as fh:
    w = csv.writer(fh); w.writerow(["class","file","source","w","h","srcW","srcH","fill"]); w.writerows(rows)
print("\nclass        total  kept  too_small overlaps bad_fill")
for n in NAMES:
    print(f"{n:11s} {stat[(n,'total')]:6d} {stat[(n,'kept')]:5d} {stat[(n,'too_small')]:9d} {stat[(n,'overlaps_neighbour')]:8d} {stat[(n,'bad_fill')]:8d}")
