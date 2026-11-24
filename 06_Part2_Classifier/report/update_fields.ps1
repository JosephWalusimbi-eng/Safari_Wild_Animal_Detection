# update_fields.ps1 - opens a report in Word, refreshes contents / list of tables / list of figures,
# saves, and exports a PDF next to it.
#   powershell -File update_fields.ps1                                  (full report)
#   powershell -File update_fields.ps1 UgaWildVision_Part2_Report_Short.docx
param([string]$name = "UgaWildVision_Part2_Report.docx")
$ErrorActionPreference = "Stop"
$docx = Join-Path $PSScriptRoot $name
$pdf  = [System.IO.Path]::ChangeExtension($docx, ".pdf")
$lock = Join-Path $PSScriptRoot ("~$" + $name.Substring(2))
if (Test-Path -LiteralPath $lock) { Remove-Item -LiteralPath $lock -Force }   # stale lock file blocks Word
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($docx, $false, $false, $false)
    foreach ($t in $doc.TablesOfContents) { $t.Update() }
    foreach ($t in $doc.TablesOfFigures) { $t.Update() }
    $doc.Fields.Update() | Out-Null
    foreach ($s in @("TOC 1", "TOC 2", "TOC 3", "Table of Figures")) {
        try { $st = $doc.Styles.Item($s); $st.Font.Name = "Times New Roman"; $st.Font.Size = 12 } catch {}
    }
    foreach ($t in $doc.TablesOfContents) { $t.Update() }
    foreach ($t in $doc.TablesOfFigures) { $t.Update() }
    $doc.Save()
    $doc.ExportAsFixedFormat($pdf, 17)
    "$name : $($doc.ComputeStatistics(2)) pages -> $pdf"
    $doc.Close()
} finally {
    $word.Quit()
}
