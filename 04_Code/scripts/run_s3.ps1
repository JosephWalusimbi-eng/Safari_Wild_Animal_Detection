Set-Location C:\Users\mrjos\Downloads\wildlife-capstone
.\venv\Scripts\Activate.ps1
foreach ($s in 0,1,2) {
  python scripts\train_s3.py --name S3rfs_seed$s --data C:\Users\mrjos\Downloads\wildlife-yolo-rfs\data.yaml --seed $s *> "logs\S3rfs_seed$s.log"
}
foreach ($s in 0,1,2) {
  python scripts\train_s3.py --name S3w_seed$s --data C:\Users\mrjos\Downloads\wildlife-yolo\data.yaml --seed $s --class-weights *> "logs\S3w_seed$s.log"
}
"ALL DONE" | Out-File logs\S3_done.txt
