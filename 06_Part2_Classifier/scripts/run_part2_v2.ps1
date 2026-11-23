# run_part2_v2.ps1 - Part 2 v2: same model, seeds and SETTINGS as v1 (train_cls.py unchanged);
# the ONLY change is the training images (cls_v2 = cls_v1 train + 2 phone-domain augmented copies
# each). val/test/uwec_test are identical to v1. Model selection is by val; UWEC is reported once.
$ErrorActionPreference = "Continue"
$P2 = "C:\Users\mrjos\Downloads\wildlife-capstone\part2"
Set-Location $P2
& C:\Users\mrjos\Downloads\wildlife-capstone\venv\Scripts\Activate.ps1
$runs = @()
foreach ($s in 0, 1, 2) {
  $name = "v2_n_seed$s"
  "START $name $(Get-Date -Format s)" | Out-File -Append logs\progress_v2.txt
  python scripts\train_cls.py --data "$P2\cls_v2" --model yolov8n-cls.pt --seed $s --project "$P2\runs" --name $name *> "logs\$name.log"
  "END   $name exit=$LASTEXITCODE $(Get-Date -Format s)" | Out-File -Append logs\progress_v2.txt
  $runs += "$P2\runs\$name"
}
python scripts\evaluate_cls.py --data "$P2\cls_v2" --runs $runs --out "$P2\results\v2" *> logs\eval_v2.log
"EVAL exit=$LASTEXITCODE $(Get-Date -Format s)" | Out-File -Append logs\progress_v2.txt
"ALL DONE" | Out-File -Append logs\progress_v2.txt
