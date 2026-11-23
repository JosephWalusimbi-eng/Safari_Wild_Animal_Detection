"""export_cls.py - Part 2: export the chosen classifier to ONNX for the PWA and verify it.

1. Exports <run>/weights/best.pt to ONNX (224x224, static shape, fp32).
2. Writes labels.json (class index -> name) next to it.
3. Verifies on every uwec_test (+ test) image that the ONNX model, fed by a plain-numpy copy
   of the preprocessing the PWA will do in JavaScript, gives the same top-1 as the PyTorch
   model through Ultralytics. Reports agreement and max probability difference.
4. Times ONNX inference on CPU (single image).

PWA preprocessing (must match exactly; see PREPROCESS below):
   EXIF-rotate -> RGB -> resize so the SHORTER side = 224 (bilinear) -> centre-crop 224x224
   -> float32 / 255 (no mean/std) -> NCHW. Output is already softmax probabilities.

    python export_cls.py --run <runs>/v1_n_seed0 --data <cls_v1> --out <export_dir>
"""
import argparse, json, shutil, time
from pathlib import Path
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageOps
from ultralytics import YOLO

S = 224


def PREPROCESS(path):
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
    # Same geometry as torchvision Resize(224) + CenterCrop(224), which Ultralytics uses:
    # long side = int(224 * long / short) (truncated), crop offset = int(round((dim - 224) / 2)).
    w, h = im.size
    if w <= h:
        nw, nh = S, int(S * h / w)
    else:
        nw, nh = int(S * w / h), S
    im = im.resize((nw, nh), Image.BILINEAR)
    l, t = int(round((nw - S) / 2.0)), int(round((nh - S) / 2.0))
    a = np.asarray(im.crop((l, t, l + S, t + S)), dtype=np.float32) / 255.0
    return a.transpose(2, 0, 1)[None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    run, out = Path(a.run), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    m = YOLO(str(run / "weights" / "best.pt"))
    onnx_path = Path(m.export(format="onnx", imgsz=S, dynamic=False, simplify=True, opset=17))
    shutil.copy2(onnx_path, out / "model.onnx")
    names = [m.names[i] for i in range(len(m.names))]
    (out / "labels.json").write_text(json.dumps(names, indent=1), encoding="utf-8")

    sess = ort.InferenceSession(str(out / "model.onnx"), providers=["CPUExecutionProvider"])
    inp = sess.get_inputs()[0].name
    files = sorted(Path(a.data).glob("uwec_test/*/*.jpg")) + sorted(Path(a.data).glob("test/*/*.jpg"))
    agree, maxdiff, lines = 0, 0.0, []
    for f in files:
        p_onnx = sess.run(None, {inp: PREPROCESS(f)})[0][0]
        r = m.predict(str(f), imgsz=S, verbose=False)[0].probs
        p_pt = r.data.cpu().numpy()
        agree += int(np.argmax(p_onnx) == r.top1)
        maxdiff = max(maxdiff, float(np.abs(p_onnx - p_pt).max()))
    x = PREPROCESS(files[0]); sess.run(None, {inp: x})
    t0 = time.perf_counter()
    for _ in range(50):
        sess.run(None, {inp: x})
    ms = (time.perf_counter() - t0) / 50 * 1000
    rep = dict(run=run.name, onnx_mb=round((out / "model.onnx").stat().st_size / 1e6, 2),
               images_checked=len(files), top1_agreement=round(agree / len(files), 4),
               max_prob_diff=round(maxdiff, 4), cpu_ms_per_image=round(ms, 2), classes=len(names))
    (out / "export_check.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(rep)


if __name__ == "__main__":
    main()
