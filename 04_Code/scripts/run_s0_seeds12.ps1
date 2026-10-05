Set-Location C:\Users\mrjos\Downloads\wildlife-capstone
.\venv\Scripts\Activate.ps1
foreach ($s in 1,2) {
  yolo detect train `
    data=C:\Users\mrjos\Downloads\wildlife-yolo\data.yaml `
    model=yolov8n.pt epochs=100 imgsz=640 patience=20 batch=16 `
    project=C:\Users\mrjos\Downloads\wildlife-capstone\runs `
    name=S0_baseline_seed$s seed=$s `
    mosaic=0.0 hsv_h=0.0 hsv_s=0.0 hsv_v=0.0 `
    translate=0.0 scale=0.0 fliplr=0.0 flipud=0.0 `
    mixup=0.0 copy_paste=0.0 degrees=0.0 shear=0.0 perspective=0.0 *> logs\S0_baseline_seed$s.log
}
