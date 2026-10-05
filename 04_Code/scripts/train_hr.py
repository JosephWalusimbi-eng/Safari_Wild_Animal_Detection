"""Train YOLOv8n with the S1 augmentation set, optionally with class-weighted
classification loss (inverse-sqrt frequency of TRAIN boxes, mean weight = 1).
Usage: python train_s3.py --name S3w_seed0 --data <data.yaml> --seed 0 [--class-weights]"""
import argparse
from pathlib import Path
import torch
from ultralytics import YOLO

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--data", required=True)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--class-weights", action="store_true"); ap.add_argument("--imgsz", type=int, default=640); ap.add_argument("--batch", type=int, default=16)
a = ap.parse_args()

NAMES = ["antelope", "bird", "chimpanzee", "elephant", "gorilla", "hippo", "hog"]
TRAIN_BOXES = [137, 244, 871, 91, 167, 845, 263]  # original wildlife-yolo train split


def weights():
    raw = torch.tensor([1.0 / n ** 0.5 for n in TRAIN_BOXES])
    return raw / raw.mean()


def main():
    model = YOLO("yolov8n.pt")
    if a.class_weights:
        w = weights()
        print("class weights:", {n: round(float(x), 2) for n, x in zip(NAMES, w)}, flush=True)

        def on_start(trainer):
            trainer.model.class_weights = w  # read by v8DetectionLoss when it is created

        model.add_callback("on_train_start", on_start)
    model.train(
        data=a.data, epochs=100, imgsz=a.imgsz, patience=20, batch=a.batch, seed=a.seed,
        project=r"C:\Users\mrjos\Downloads\wildlife-capstone\runs", name=a.name,
        mosaic=1.0, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4, translate=0.1, scale=0.5,
        fliplr=0.5, flipud=0.0, mixup=0.1, copy_paste=0.0, degrees=0.0, shear=0.0, perspective=0.0,
    )


if __name__ == "__main__":
    main()
