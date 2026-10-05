"""predict.py - run the wildlife detector on photos, folders of photos, or videos.

Finds seven classes: antelope, bird, chimpanzee, elephant, gorilla, hippo, hog.
For each input it writes an annotated copy (boxes + names + confidence), one CSV of every
detection, and prints a per-class summary. See HOWTOUSE.txt for plain-English instructions.

Examples:
    python predict.py photo.jpg
    python predict.py C:\\frames_folder --conf 0.4
    python predict.py clip.mp4 --every 5
    python predict.py clip.mp4 --model model/S1_seed0_best.onnx
"""
import argparse
import csv
import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_CANDIDATES = [HERE / "model" / "S1_seed0_best.pt", HERE.parent / "model" / "S1_seed0_best.pt"]
DEFAULT_MODEL = next((c for c in _CANDIDATES if c.exists()), _CANDIDATES[0])
CLASSES = ["antelope", "bird", "chimpanzee", "elephant", "gorilla", "hippo", "hog"]
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv", ".m4v"}
COLOURS = [(60, 180, 75), (255, 225, 25), (0, 130, 200), (245, 130, 48),
           (145, 30, 180), (70, 240, 240), (240, 50, 230)]


def parse_args():
    ap = argparse.ArgumentParser(description="Detect wildlife in photos or videos.")
    ap.add_argument("source", help="an image, a folder of images, or a video file")
    ap.add_argument("--model", default=str(DEFAULT_MODEL), help="model file (.pt or .onnx)")
    ap.add_argument("--conf", type=float, default=0.25,
                    help="minimum confidence to keep a detection, 0 to 1 (default 0.25)")
    ap.add_argument("--imgsz", type=int, default=640, help="model input size (default 640, as trained)")
    ap.add_argument("--every", type=int, default=1,
                    help="for videos: analyse every Nth frame (default 1 = all frames)")
    ap.add_argument("--out", default="predictions", help="output folder (default ./predictions)")
    ap.add_argument("--no-save-media", action="store_true", help="write only the CSV, not annotated images/video")
    ap.add_argument("--device", default=None,
                    help="'cpu', or a GPU number such as 0 (default: GPU if available; ONNX models always use the CPU)")
    return ap.parse_args()


def draw(cv2, frame, boxes):
    """Draw boxes on a copy of the frame. boxes = list of (class_id, conf, x1, y1, x2, y2)."""
    out = frame.copy()
    thick = max(2, out.shape[1] // 500)
    scale = max(0.5, out.shape[1] / 1600)
    for cid, conf, x1, y1, x2, y2 in boxes:
        col = COLOURS[cid % len(COLOURS)]
        cv2.rectangle(out, (int(x1), int(y1)), (int(x2), int(y2)), col, thick)
        label = f"{CLASSES[cid]} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)
        top = max(int(y1) - th - 6, 0)
        cv2.rectangle(out, (int(x1), top), (int(x1) + tw + 6, top + th + 6), col, -1)
        cv2.putText(out, label, (int(x1) + 3, top + th + 1), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thick)
    return out


def detect(model, frame, conf, imgsz, device):
    r = model.predict(frame, conf=conf, imgsz=imgsz, device=device, verbose=False)[0]
    return [(int(c), float(p), *map(float, b)) for c, p, b in
            zip(r.boxes.cls, r.boxes.conf, r.boxes.xyxy.tolist())]


def main():
    a = parse_args()
    # Never let Ultralytics pip-install packages on its own (with a GPU present it tries to
    # install onnxruntime-gpu for ONNX models, which can hang and alters the environment).
    os.environ.setdefault("YOLO_AUTOINSTALL", "false")
    try:
        import cv2
        from ultralytics import YOLO
    except ImportError as e:
        sys.exit(f"Missing package ({e.name}). Install with:  pip install ultralytics opencv-python onnxruntime")

    src, model_path, out = Path(a.source), Path(a.model), Path(a.out)
    if not src.exists():
        sys.exit(f"Cannot find the input: {src}")
    if not model_path.exists():
        sys.exit(f"Cannot find the model file: {model_path}  (use --model to point to it)")
    out.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(model_path), task="detect")
    # ONNX runs on the CPU here (needs only the plain onnxruntime package).
    device = "cpu" if model_path.suffix.lower() == ".onnx" else a.device

    rows, totals = [], Counter()

    def log(name, frame_no, dets):
        for cid, conf, x1, y1, x2, y2 in dets:
            rows.append([name, frame_no, CLASSES[cid], round(conf, 3), round(x1), round(y1), round(x2), round(y2)])
            totals[CLASSES[cid]] += 1

    if src.is_dir() or src.suffix.lower() in IMAGE_EXT:
        files = sorted(p for p in (src.iterdir() if src.is_dir() else [src]) if p.suffix.lower() in IMAGE_EXT)
        if not files:
            sys.exit("No images found in that folder.")
        for f in files:
            img = cv2.imread(str(f))
            if img is None:
                print(f"  skipped (cannot read): {f.name}")
                continue
            dets = detect(model, img, a.conf, a.imgsz, device)
            log(f.name, "", dets)
            if not a.no_save_media:
                cv2.imwrite(str(out / f"{f.stem}_detected.jpg"), draw(cv2, img, dets))
            print(f"  {f.name}: {len(dets)} animal(s)")
        units = f"{len(files)} image(s)"
    elif src.suffix.lower() in VIDEO_EXT:
        cap = cv2.VideoCapture(str(src))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = None
        if not a.no_save_media:
            writer = cv2.VideoWriter(str(out / f"{src.stem}_detected.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                                     fps / max(a.every, 1), (w, h))
        k = analysed = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if k % max(a.every, 1) == 0:
                dets = detect(model, frame, a.conf, a.imgsz, device)
                log(src.name, k, dets)
                analysed += 1
                if writer:
                    writer.write(draw(cv2, frame, dets))
            k += 1
        cap.release()
        if writer:
            writer.release()
        units = f"{analysed} video frame(s) (of {k})"
    else:
        sys.exit(f"Unsupported file type: {src.suffix}. Use an image or video ({', '.join(sorted(IMAGE_EXT | VIDEO_EXT))}).")

    csv_path = out / "detections.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "frame", "class", "confidence", "x1", "y1", "x2", "y2"])
        w.writerows(rows)

    print(f"\nAnalysed {units} with {model_path.name} at confidence >= {a.conf}.")
    print("Detections per class:", dict(totals) if totals else "none")
    print(f"Results written to: {out.resolve()}  (detections.csv" + ("" if a.no_save_media else " + annotated files") + ")")
    print("Reminder: this model is least reliable for birds and for footage from places/cameras it has not seen.")


if __name__ == "__main__":
    main()
