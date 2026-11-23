# build_v2_on_gpu.ps1 - builds cls_v2 on the GPU machine (uploading 423 MB over the slow relay link
# timed out; see LOG Entry 8). Same script and seed as the local build; compare the logs afterwards.
$P2 = "C:\Users\mrjos\Downloads\wildlife-capstone\part2"
Set-Location $P2
if (Test-Path cls_v2) { "cls_v2 already exists - not rebuilding" | Out-File logs\build_v2.log; exit 1 }
& C:\Users\mrjos\Downloads\wildlife-capstone\venv\Scripts\python scripts\make_aug_dataset.py --src cls_v1 --safari C:\Users\mrjos\Downloads\Safari_Dataset --out cls_v2 --k 2 *> logs\build_v2.log
"BUILD exit=$LASTEXITCODE $(Get-Date -Format s)" | Out-File -Append logs\build_v2.log
