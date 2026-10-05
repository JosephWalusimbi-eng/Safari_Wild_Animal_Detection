import numpy as np
from pathlib import Path
from ultralytics import YOLO
N = ["antelope","bird","chimpanzee","elephant","gorilla","hippo","hog","background"]
m = YOLO(r"C:\Users\mrjos\Downloads\wildlife-capstone\runs\S1_augment_seed0\weights\best.pt")
out = Path(r"C:\Users\mrjos\Downloads\wildlife-capstone\runs\eval_plots")
np.set_printoptions(linewidth=200)
for conf in (0.001, 0.25):
    r = m.val(data=r"C:\Users\mrjos\Downloads\wildlife-yolo\data.yaml", split="test", imgsz=640, workers=0, batch=16, conf=conf, plots=True,
              verbose=False, project=str(out), name=f"S1s0_test_conf{conf}", exist_ok=True)
    cm = r.confusion_matrix.matrix.astype(int)  # [predicted, true]
    print(f"\n=== library matrix at conf={conf}  (rows = predicted, columns = true; last = background) ===")
    print("          " + " ".join(f"{n[:6]:>6s}" for n in N))
    for i, row in enumerate(cm): print(f"{N[i][:9]:9s} " + " ".join(f"{v:6d}" for v in row))
    off = cm[:7, :7].sum() - np.trace(cm[:7, :7])
    print("true animals (column sums, classes only):", cm[:, :7].sum(), "| correct:", np.trace(cm[:7, :7]), "| wrong-class:", off, "| missed (pred=background):", cm[7, :7].sum(), "| false alarms (true=background):", cm[:7, 7].sum())
