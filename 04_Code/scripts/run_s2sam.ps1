Set-Location C:\Users\mrjos\Downloads\wildlife-capstone
.\venv\Scripts\Activate.ps1
$aug = @('mosaic=1.0','hsv_h=0.015','hsv_s=0.7','hsv_v=0.4','translate=0.1','scale=0.5','fliplr=0.5','flipud=0.0','mixup=0.1','copy_paste=0.0','degrees=0.0','shear=0.0','perspective=0.0')
foreach ($s in 0,1,2) {
  $name = "S2sam_seed$s"
  yolo detect train data=C:\Users\mrjos\Downloads\wildlife-yolo-cp\data.yaml model=yolov8n.pt epochs=100 imgsz=640 patience=20 batch=16 project=C:\Users\mrjos\Downloads\wildlife-capstone\runs name=$name seed=$s @aug *> "logs\$name.log"
}
"ALL DONE" | Out-File logs\S2sam_done.txt
