"""External sanity check on 4 NEW videos (one known species each, leak-checked, Entry 15).
Per frame, take the highest-confidence detection (conf>=0.25): is it the video's species?
Also: share of frames with ANY detection of the right species at conf>=0.25, and with ANY wrong-species
detection at conf>=0.5. This tests species recognition on unseen footage. It does NOT test box accuracy."""
import csv, cv2, numpy as np
from pathlib import Path
from ultralytics import YOLO
X = Path(r"C:\Users\mrjos\Downloads\zenodo_extra")
RUNS = Path(r"C:\Users\mrjos\Downloads\wildlife-capstone\runs")
V = {"elephantANP": ("Elephant/Elephant/Elephant_ANP.mp4", 3),
     "elephantCTPH": ("Elephant/Elephant/Elephants. CTPHmp4. CTPHmp4. CTPHmp4.mp4", 3),
     "hippoLQ": ("Hippopotamus/Hippopotamus/Hippopotamus.mp4", 5),
     "warthog": ("Warthog/Warthog/Warthog.mp4", 6)}
frames = {}
for tag, (rel, sid) in V.items():
    cap = cv2.VideoCapture(str(X / rel)); step = max(int(round((cap.get(cv2.CAP_PROP_FPS) or 25) / 2)), 1)
    fr, k = [], 0
    while cap.grab():
        if k % step == 0:
            ok, f = cap.retrieve()
            if ok: fr.append(f)
        k += 1
    frames[tag] = fr
cfgs = {"S0": "S0_baseline_seed{}", "S1": "S1_augment_seed{}", "S2sam": "S2sam_seed{}", "S3rfs": "S3rfs_seed{}", "S3w": "S3w_seed{}"}
rows = []
for cfg, pat in cfgs.items():
    for s in (0, 1, 2):
        m = YOLO(str(RUNS / pat.format(s) / "weights" / "best.pt"))
        for tag, (rel, sid) in V.items():
            top = anyc = wrong = 0; n = len(frames[tag])
            for f in frames[tag]:
                r = m.predict(f, imgsz=640, conf=0.25, verbose=False)[0]
                cl = r.boxes.cls.int().tolist(); cf = r.boxes.conf.tolist()
                if cl:
                    if cl[int(np.argmax(cf))] == sid: top += 1
                    if sid in cl: anyc += 1
                    if any(c != sid and p >= 0.5 for c, p in zip(cl, cf)): wrong += 1
            rows.append([cfg, s, tag, n, round(top / n, 3), round(anyc / n, 3), round(wrong / n, 3)])
        print(cfg, s, "done", flush=True)
with open(r"C:\Users\mrjos\external_check.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["config", "seed", "video", "frames", "top1_correct", "any_correct", "wrong_conf50"]); w.writerows(rows)
