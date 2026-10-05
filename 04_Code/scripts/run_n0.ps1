Set-Location C:\Users\mrjos\Downloads\wildlife-capstone
.\venv\Scripts\Activate.ps1
foreach ($s in 0,1,2) {
  $name = "N0_naive_seed$s"
  yolo detect train data=C:\Users\mrjos\Downloads\wildlife-capstone\configs\data_naive.yaml model=yolov8n.pt epochs=100 imgsz=640 patience=20 batch=16 project=C:\Users\mrjos\Downloads\wildlife-capstone\runs name=$name seed=$s mosaic=0.0 hsv_h=0.0 hsv_s=0.0 hsv_v=0.0 translate=0.0 scale=0.0 fliplr=0.0 flipud=0.0 mixup=0.0 copy_paste=0.0 degrees=0.0 shear=0.0 perspective=0.0 *> "logs\$name.log"
}
"ALL DONE" | Out-File logs\N0_done.txt
