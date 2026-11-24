# update_fields.ps1 - opens the report in Word, refreshes the contents, lists and captions, saves, exports PDF.
$ErrorActionPreference = "Stop"
$docx = Join-Path $PSScriptRoot "UgaWildVision_Part2_Report.docx"
$pdf  = Join-Path $PSScriptRoot "UgaWildVision_Part2_Report.pdf"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($docx, $false, $false, $false)
    $doc.Fields.Update() | Out-Null
    foreach ($t in $doc.TablesOfContents) { $t.Update() }
    foreach ($t in $doc.TablesOfFigures) { $t.Update() }
    # Word builds TOC entries in its own TOC/Table of Figures styles; force Times New Roman 12 there too.
    foreach ($name in @("TOC 1", "TOC 2", "TOC 3", "Table of Figures")) {
        try { $s = $doc.Styles.Item($name); $s.Font.Name = "Times New Roman"; $s.Font.Size = 12 } catch {}
    }
    foreach ($t in $doc.TablesOfContents) { $t.Update() }
    foreach ($t in $doc.TablesOfFigures) { $t.Update() }
    $doc.Save()
    $doc.ExportAsFixedFormat($pdf, 17)
    "TOCs: $($doc.TablesOfContents.Count)  TOFs: $($doc.TablesOfFigures.Count)  pages: $($doc.ComputeStatistics(2))"
    $doc.Close()
} finally {
    $word.Quit()
}
