Get-Content C:\Users\mrjos\Downloads\wildlife-capstone\logs\S0_baseline_seed0.log -Tail 4
Get-CimInstance Win32_Process | Where-Object { $_.Name -in 'yolo.exe','python.exe','powershell.exe' -and $_.CommandLine -match 'yolo|run_s0' } | ForEach-Object { "{0} parent={1} {2}" -f $_.ProcessId,$_.ParentProcessId,$_.CommandLine.Substring(0,[Math]::Min(100,$_.CommandLine.Length)) }
