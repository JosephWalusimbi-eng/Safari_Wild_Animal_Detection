"""train_cls.py - Part 2: train a YOLOv8 classification model on cls_v1.

    python train_cls.py --data <cls_v1> --model yolov8n-cls.pt --seed 0 --project <runs> --name n_seed0

Settings are fixed here (not on the command line) so every run is comparable and recorded.
Ultralytics writes args.yaml, results.csv, results.png and weights/best.pt into the run folder.
"""
import argparse
from ultralytics import YOLO

SETTINGS = dict(
    imgsz=224,        # phone-friendly; source images are stored at <=512 px
    epochs=60,
    patience=15,      # early stop on val top-1
    batch=64,         # moderate: the GPU is shared
    workers=0,        # Ultralytics loaders hang on this machine (Part 1 finding)
    optimizer="AdamW",
    lr0=0.001,
    cos_lr=True,
    pretrained=True,  # ImageNet-pretrained backbone
    erasing=0.4,      # Ultralytics classify default augmentation (RandAugment + erasing)
    deterministic=True,
    plots=True,
    exist_ok=False,
)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--model", default="yolov8n-cls.pt")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--project", required=True)
    ap.add_argument("--name", required=True)
    a = ap.parse_args()
    YOLO(a.model).train(data=a.data, seed=a.seed, project=a.project, name=a.name, **SETTINGS)
