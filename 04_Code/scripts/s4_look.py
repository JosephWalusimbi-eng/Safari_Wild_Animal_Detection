import cv2, numpy as np
from pathlib import Path
from ultralytics import YOLO
X = Path(r"C:\Users\mrjos\Downloads\zenodo_extra")
V = {"elephantANP": "Elephant/Elephant/Elephant_ANP.mp4",
     "elephantCTPH": "Elephant/Elephant/Elephants. CTPHmp4. CTPHmp4. CTPHmp4.mp4",
     "hippoLQ": "Hippopotamus/Hippopotamus/Hippopotamus.mp4",
     "warthog": "Warthog/Warthog/Warthog.mp4"}
NAMES = ["antelope", "bird", "chimpanzee", "elephant", "gorilla", "hippo", "hog"]
m = YOLO(r"runs\S1_augment_seed0\weights\best.pt")
tiles = []
for tag, rel in V.items():
    cap = cv2.VideoCapture(str(X / rel)); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    allconf = []; cls_hist = {}
    picks = []
    for k in range(0, n, max(int(cap.get(cv2.CAP_PROP_FPS) / 2), 1)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok, fr = cap.read()
        if not ok: continue
        r = m.predict(fr, imgsz=640, conf=0.1, verbose=False)[0]
        c = r.boxes.conf.tolist(); allconf.append(max(c) if c else 0)
        for ci in r.boxes.cls.int().tolist(): cls_hist[NAMES[ci]] = cls_hist.get(NAMES[ci], 0) + 1
        picks.append((k, fr, r))
    a = np.array(allconf)
    print(f"{tag}: frames {len(a)}; max-conf per frame: median {np.median(a):.2f}, share>=0.6 {np.mean(a>=0.6):.0%}, "
          f"share>=0.3 {np.mean(a>=0.3):.0%}; classes predicted at conf>=0.1: {cls_hist}")
    for k, fr, r in [picks[len(picks) // 4], picks[len(picks) // 2], picks[3 * len(picks) // 4]]:
        im = r.plot(); h, w = im.shape[:2]; s = 360 / h
        tiles.append(cv2.resize(im, (int(w * s), 360)))
    # pad each row to same width
rows = []
for i in range(0, len(tiles), 3):
    row = tiles[i:i + 3]; rows.append(np.hstack(row))
W = max(r.shape[1] for r in rows)
rows = [cv2.copyMakeBorder(r, 0, 0, 0, W - r.shape[1], cv2.BORDER_CONSTANT) for r in rows]
cv2.imwrite(r"C:\Users\mrjos\s4_look.jpg", np.vstack(rows))
