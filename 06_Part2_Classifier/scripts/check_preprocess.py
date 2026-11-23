"""check_preprocess.py - evidence for the PWA preprocessing spec (LOG Entry 6).

For every test + uwec_test image, compares 4 things for one run:
  (1) Ultralytics predict()            vs  torchvision Resize+CenterCrop on a cv2-decoded image
  (2) ONNX model                        vs  PyTorch model on the same tensor
  (3) export_cls.PREPROCESS (numpy/PIL) vs  torchvision, pixel by pixel
  (4) the resulting probabilities and top-1 flips
All four must be ~0 for the PWA (which copies PREPROCESS in app.js) to be faithful.

    python check_preprocess.py --run ..\\runs\\v1_n_seed2 --onnx ..\\export\\model.onnx --data ..\\cls_v1
"""
import argparse, sys
from pathlib import Path
import numpy as np, torch, cv2
from PIL import Image
import torchvision.transforms as T
import onnxruntime as ort
sys.path.insert(0, str(Path(__file__).parent))
from export_cls import PREPROCESS
from ultralytics import YOLO

ap = argparse.ArgumentParser()
ap.add_argument("--run", required=True); ap.add_argument("--onnx", required=True); ap.add_argument("--data", required=True)
a = ap.parse_args()
m = YOLO(str(Path(a.run) / "weights" / "best.pt"))
net = m.model.float().eval()
sess = ort.InferenceSession(a.onnx)
tv = T.Compose([T.Resize(224), T.CenterCrop(224), T.ToTensor()])
files = sorted(Path(a.data).glob("uwec_test/*/*.jpg")) + sorted(Path(a.data).glob("test/*/*.jpg"))
s = []
for f in files:
    r = m.predict(str(f), imgsz=224, verbose=False)[0].probs.data.cpu().numpy()
    x = PREPROCESS(f)
    b = tv(Image.fromarray(cv2.cvtColor(cv2.imread(str(f)), cv2.COLOR_BGR2RGB)))[None].numpy()
    with torch.no_grad():
        pa, pb = net(torch.from_numpy(x)), net(torch.from_numpy(b))
    pa = (pa[0] if isinstance(pa, (list, tuple)) else pa).numpy()[0]
    pb = (pb[0] if isinstance(pb, (list, tuple)) else pb).numpy()[0]
    ob = sess.run(None, {sess.get_inputs()[0].name: b})[0][0]
    s.append((np.abs(pb - r).max(), np.abs(ob - pb).max(), np.abs(x - b).max(), np.abs(pa - pb).max(),
              int(pa.argmax() != pb.argmax())))
s = np.array(s)
print(f"images: {len(s)}")
print(f"(1) predict vs torchvision-on-cv2, max prob diff : {s[:, 0].max():.2e}")
print(f"(2) onnx vs pytorch (same tensor), max prob diff : {s[:, 1].max():.2e}")
print(f"(3) PREPROCESS vs torchvision, max pixel diff   : {s[:, 2].max():.4f}")
print(f"(4) PREPROCESS vs torchvision, max prob diff    : {s[:, 3].max():.4f}, top-1 flips {int(s[:, 4].sum())}")
