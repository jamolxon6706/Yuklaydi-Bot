# Start the arq worker (run this in a second terminal)
Write-Host "Starting arq worker..." -ForegroundColor Green
.\.venv\Scripts\python.exe -m arq bot.worker.tasks.WorkerSettings
