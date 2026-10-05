Set-Location C:\Users\mrjos\Downloads\wildlife-capstone
.\venv\Scripts\Activate.ps1
foreach ($s in 0,1,2) {
  python scripts\train_s3.py --name S4ps_seed$s --data C:\Users\mrjos\Downloads\wildlife-yolo-ps2\data.yaml --seed $s *> "logs\S4ps_seed$s.log"
}
"ALL DONE" | Out-File logs\S4_done.txt
