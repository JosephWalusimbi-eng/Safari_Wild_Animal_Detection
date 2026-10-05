"""Probe the extra Zenodo videos and test them for overlap with the annotated Safari frames
(all 9 sessions, i.e. including every val/test frame) using a perceptual difference hash."""
import cv2, numpy as np, csv
from pathlib import Path
X = Path(r"C:\Users\mrjos\Downloads\zenodo_extra")
S = Path(r"C:\Users\mrjos\Downloads\Safari_Dataset")


def dhash(img, n=16):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (n + 1, n), interpolation=cv2.INTER_AREA)
    return (g[:, 1:] > g[:, :-1]).flatten()


ref, names = [], []
for d in sorted(S.iterdir()):
    if not d.is_dir():
        continue
    for f in d.glob("frame_*.png"):
        im = cv2.imread(str(f))
        if im is None:
            continue
        ref.append(dhash(im)); names.append(f"{d.name}/{f.name}")
ref = np.array(ref)
print("reference frames:", len(ref))
rows = []
for v in sorted(X.rglob("*.mp4")):
    cap = cv2.VideoCapture(str(v))
    fps = cap.get(cv2.CAP_PROP_FPS); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dur = n / fps if fps else 0
    best = (999, "")
    step = max(int(fps / 2), 1)  # ~2 frames per second
    k = 0; sampled = 0
    while True:
        ok = cap.grab()
        if not ok:
            break
        if k % step == 0:
            ok, fr = cap.retrieve()
            if ok:
                d = (ref != dhash(fr)).sum(axis=1)
                i = int(d.argmin()); sampled += 1
                if d[i] < best[0]:
                    best = (int(d[i]), names[i])
        k += 1
    print(f"{v.parent.name}/{v.name}: {w}x{h} {fps:.1f}fps {dur:.1f}s ({n} frames); sampled {sampled}; "
          f"closest annotated frame: hamming {best[0]}/256 -> {best[1]}")
    rows.append([v.name, w, h, round(fps, 2), round(dur, 1), best[0], best[1]])
