Set-Location C:\Users\mrjos\Downloads\wildlife-capstone
.\venv\Scripts\Activate.ps1
foreach ($s in 0,1,2) {
  python scripts\train_s3.py --name ExpA_lso_seed$s --data C:\Users\mrjos\Downloads\wildlife-yolo-lso2\data.yaml --seed $s *> "logs\ExpA_lso_seed$s.log"
}
"ALL DONE" | Out-File logs\ExpA_done.txt
