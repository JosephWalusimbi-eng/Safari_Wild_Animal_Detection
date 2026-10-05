"""How do error counts depend on the confidence threshold? S1 seed 0, test split, IoU>=0.5 matching."""
from pathlib import Path
import cv2
from ultralytics import YOLO
R = Path(r"C:\Users\mrjos\Downloads\wildlife-yolo"); N = ["antelope","bird","chimpanzee","elephant","gorilla","hippo","hog"]
m = YOLO(r"C:\Users\mrjos\Downloads\wildlife-capstone\runs\S1_augment_seed0\weights\best.pt")


def iou(a, b):
    iw = min(a[2], b[2]) - max(a[0], b[0]); ih = min(a[3], b[3]) - max(a[1], b[1])
    if iw <= 0 or ih <= 0: return 0.0
    i = iw * ih; return i / ((a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i)


data = []
for f in sorted((R / "images" / "test").glob("*.png")):
    im = cv2.imread(str(f)); h, w = im.shape[:2]
    gts = []
    for l in (R / "labels" / "test" / (f.stem + ".txt")).read_text().splitlines():
        if l.strip():
            c, x, y, bw, bh = l.split(); x, y, bw, bh = map(float, (x, y, bw, bh)); gts.append((int(c), [(x-bw/2)*w, (y-bh/2)*h, (x+bw/2)*w, (y+bh/2)*h]))
    r = m.predict(im, imgsz=640, conf=0.001, iou=0.7, verbose=False, max_det=300)[0]
    data.append((gts, [(int(c), float(p), b) for c, p, b in zip(r.boxes.cls, r.boxes.conf, r.boxes.xyxy.tolist())]))
print("conf  | found-correct  found-wrong-class  missed  | total GT 662")
for conf in (0.001, 0.05, 0.1, 0.25, 0.4, 0.5):
    ok = wrong = miss = 0
    for gts, preds in data:
        pp = [p for p in preds if p[1] >= conf]
        for gc, gb in gts:
            best, bj = 0, -1
            for j, (pc, p, pb) in enumerate(pp):
                v = iou(gb, pb)
                if v > best: best, bj = v, j
            if best >= 0.5:
                if pp[bj][0] == gc: ok += 1
                else: wrong += 1
            else: miss += 1
    print(f"{conf:5.3f} | {ok:5d}  {wrong:5d}  {miss:5d}")
