# run_part2_v1.ps1 - Part 2 v1 training + evaluation on the GPU machine (setgpu, account mrjos).
# Trains YOLOv8n-cls with 3 seeds (variance, as in Part 1) and YOLOv8s-cls with seed 0
# (does a bigger model help?), then evaluates all four on test and uwec_test.
$ErrorActionPreference = "Continue"
$P2 = "C:\Users\mrjos\Downloads\wildlife-capstone\part2"
Set-Location $P2
& C:\Users\mrjos\Downloads\wildlife-capstone\venv\Scripts\Activate.ps1
New-Item -ItemType Directory -Force logs, runs, results | Out-Null
$runs = @()
foreach ($job in @(@("yolov8n-cls.pt","n",0), @("yolov8n-cls.pt","n",1), @("yolov8n-cls.pt","n",2), @("yolov8s-cls.pt","s",0))) {
  $name = "v1_$($job[1])_seed$($job[2])"
  "START $name $(Get-Date -Format s)" | Out-File -Append logs\progress.txt
  python scripts\train_cls.py --data "$P2\cls_v1" --model $job[0] --seed $job[2] --project "$P2\runs" --name $name *> "logs\$name.log"
  "END   $name exit=$LASTEXITCODE $(Get-Date -Format s)" | Out-File -Append logs\progress.txt
  $runs += "$P2\runs\$name"
}
python scripts\evaluate_cls.py --data "$P2\cls_v1" --runs $runs --out "$P2\results\v1" *> logs\eval_v1.log
"EVAL exit=$LASTEXITCODE $(Get-Date -Format s)" | Out-File -Append logs\progress.txt
"ALL DONE" | Out-File -Append logs\progress.txt
