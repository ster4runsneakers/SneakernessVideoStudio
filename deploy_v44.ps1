$src = "C:\Users\Giannis Mini Pc\agent-tools\sneakerness_work\video-studio-v43"
$dst = "F:\SNEAKERNESS.EU\SneakernessVideoStudio-UI-v43-FLAT"
$files = @(
  "grok_prompts.py",
  "captions.py",
  "app.py",
  "UI_VERSION.txt",
  "CHANGELOG_v44.md"
)
foreach ($f in $files) {
  $from = Join-Path $src $f
  $to = Join-Path $dst $f
  if (-not (Test-Path $from)) { Write-Error "Missing $from"; continue }
  Copy-Item -LiteralPath $from -Destination $to -Force
  Write-Host "OK $f -> $to"
}
Write-Host "--- UI_VERSION ---"
Get-Content -LiteralPath (Join-Path $dst "UI_VERSION.txt")
Get-ChildItem -LiteralPath $dst | Where-Object { $files -contains $_.Name } | Format-Table Name, Length, LastWriteTime -AutoSize
