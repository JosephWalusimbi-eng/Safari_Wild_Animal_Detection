"""Export the chosen model (S1, seed 0) to ONNX, check accuracy parity, and benchmark latency."""
import time, json, shutil, numpy as np, torch
from pathlib import Path
from ultralytics import YOLO
import onnxruntime as ort

RUN = Path(r"C:\Users\mrjos\Downloads\wildlife-capstone\runs\S1_augment_seed0\weights")
DATA = r"C:\Users\mrjos\Downloads\wildlife-yolo\data.yaml"
pt = RUN / "best.pt"
m = YOLO(str(pt))
onnx_path = Path(m.export(format="onnx", imgsz=640, dynamic=False, simplify=True, opset=17))
print("onnx:", onnx_path, round(onnx_path.stat().st_size / 1e6, 2), "MB; pt:", round(pt.stat().st_size / 1e6, 2), "MB")

# accuracy parity on the VALIDATION split (same images, both formats)
res = {}
for tag, p in (("pt", pt), ("onnx", onnx_path)):
    r = YOLO(str(p), task="detect").val(data=DATA, split="val", imgsz=640, workers=0, batch=1 if tag == "onnx" else 16, verbose=False, plots=False)
    res[tag] = (round(r.box.map50, 4), round(r.box.map, 4))
print("val mAP50 / mAP50-95  pt:", res["pt"], " onnx:", res["onnx"])


def bench(fn, n=200, warm=30):
    for _ in range(warm): fn()
    t = []
    for _ in range(n):
        s = time.perf_counter(); fn(); t.append((time.perf_counter() - s) * 1000)
    t = np.array(t); return round(float(np.median(t)), 2), round(float(np.percentile(t, 95)), 2)


x = np.random.rand(1, 3, 640, 640).astype(np.float32)
out = {}
net = m.model.float().eval()
with torch.no_grad():
    xt = torch.from_numpy(x)
    net_c = net.cpu(); out["torch_cpu_fp32"] = bench(lambda: net_c(xt), n=60, warm=10)
    net_g = net.cuda(); xg = xt.cuda()
    def g():
        net_g(xg); torch.cuda.synchronize()
    out["torch_gpu_fp32"] = bench(g)
    net_g.half(); xh = xg.half()
    def gh():
        net_g(xh); torch.cuda.synchronize()
    out["torch_gpu_fp16"] = bench(gh)
so = ort.SessionOptions()
sess = ort.InferenceSession(str(onnx_path), so, providers=["CPUExecutionProvider"])
name = sess.get_inputs()[0].name
out["onnxruntime_cpu"] = bench(lambda: sess.run(None, {name: x}), n=60, warm=10)
print("providers available:", ort.get_available_providers())
print("latency ms, batch 1, 640x640, model forward only (median, p95):")
for k, v in out.items(): print(f"  {k:18s} {v[0]:7.2f}  {v[1]:7.2f}")
json.dump({"sizes_MB": {"pt": round(pt.stat().st_size / 1e6, 2), "onnx": round(onnx_path.stat().st_size / 1e6, 2)},
           "val_parity": res, "latency_ms_median_p95": out}, open(r"C:\Users\mrjos\export_bench.json", "w"), indent=1)
shutil.copy2(onnx_path, r"C:\Users\mrjos\Downloads\wildlife-capstone\weights\S1_seed0_best.onnx")
