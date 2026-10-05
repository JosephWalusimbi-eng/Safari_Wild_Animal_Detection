Set-Location C:\Users\mrjos\Downloads\wildlife-capstone
.\venv\Scripts\Activate.ps1
foreach ($s in 0,1,2) {
  python scripts\train_hr.py --name S1_1280_seed$s --data C:\Users\mrjos\Downloads\wildlife-yolo\data.yaml --seed $s --imgsz 1280 --batch 8 *> "logs\S1_1280_seed$s.log"
}
"ALL DONE" | Out-File logs\HR_done.txt
