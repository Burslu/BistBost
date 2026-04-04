# Task Scheduler - Final Bot

$BotPath = "$env:USERPROFILE\OneDrive\Desktop\BistBot"
$PythonExe = "$BotPath\.venv\Scripts\python.exe"
$BotScript = "$BotPath\production_bot_final.py"
$TaskName = "BIST_Bot_Pazartesi_10h"

Write-Host "Task Scheduler Updating..." -ForegroundColor Yellow

# Remove old task
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Monday 10:00 trigger
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "10:00am"

# Python script action
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $BotScript -WorkingDirectory $BotPath

# Settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Principal
$Principal = New-ScheduledTaskPrincipal -UserID "NT AUTHORITY\SYSTEM" -RunLevel Highest

# Task
$Task = New-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal

# Register
Register-ScheduledTask -InputObject $Task -TaskName $TaskName -TaskPath "\BistBot\" -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "SUCCESS - Monday 10 AM Bot Start" -ForegroundColor Green
Write-Host ""
Write-Host "Details:"
Write-Host "  Script: production_bot_final.py"
Write-Host "  Schedule: Every Monday 10 AM"
Write-Host "  Mode: Real BIST Data + Fallback Mock"
Write-Host ""
