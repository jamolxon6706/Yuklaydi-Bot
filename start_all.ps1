# Restart all bot processes: stop old ones, start new ones
# Run this script to apply code/config changes

$venv = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$proj = $PSScriptRoot

Write-Host "=== Stopping old processes ===" -ForegroundColor Yellow
Get-WmiObject Win32_Process -Filter "Name='python.exe'" | Where-Object {
    $_.CommandLine -like "*bot.main*" -or
    $_.CommandLine -like "*bot.worker.tasks*"
} | ForEach-Object {
    Write-Host "  Stopping PID $($_.ProcessId): $($_.CommandLine.Substring(0, [Math]::Min(80, $_.CommandLine.Length)))"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2

Write-Host "=== Starting bot + 3 workers ===" -ForegroundColor Green
$cd = "cd '$proj';"

# Main bot
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$cd & '$venv' -m bot.main 2>&1 | Tee-Object -FilePath logs\bot.log -Append" -WindowStyle Normal

Start-Sleep -Seconds 1

# Download worker
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$cd & '$venv' -m arq bot.worker.tasks.WorkerSettings 2>&1 | Tee-Object -FilePath logs\worker.log -Append" -WindowStyle Minimized

# Recognition worker
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$cd & '$venv' -m arq bot.worker.tasks.RecognitionWorkerSettings 2>&1 | Tee-Object -FilePath logs\worker_recog.log -Append" -WindowStyle Minimized

# Music worker
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$cd & '$venv' -m arq bot.worker.tasks.MusicWorkerSettings 2>&1 | Tee-Object -FilePath logs\worker_music.log -Append" -WindowStyle Minimized

Write-Host "All processes started. Logs: logs\bot.log, logs\worker*.log" -ForegroundColor Cyan
Write-Host "Local API: http://localhost:8081 (docker: vidbot-localapi)" -ForegroundColor Cyan
