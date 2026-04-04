# Windows Task Scheduler Setup - Pazartesi 10:00
# Admin haklarıyla çalıştırın

$BotPath = "$env:USERPROFILE\OneDrive\Desktop\BistBot"
$PythonExe = "$BotPath\.venv\Scripts\python.exe"
$BotScript = "$BotPath\production_bot_morgan_stanley.py"
$TaskName = "BIST_Bot_Pazartesi_10h"

Write-Host "Setup başladı..." -ForegroundColor Yellow

# Eski task sil
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Eski task silindi" -ForegroundColor Green
}
catch {
    Write-Host "Eski task bulunamadı" -ForegroundColor Cyan
}

# Pazartesi 10:00 trigger
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "10:00am"

# Python script action
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $BotScript -WorkingDirectory $BotPath

# Settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Principal
$Principal = New-ScheduledTaskPrincipal -UserID "NT AUTHORITY\SYSTEM" -RunLevel Highest

# Task oluştur
$Task = New-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal

# Kaydet
Register-ScheduledTask -InputObject $Task -TaskName $TaskName -TaskPath "\BistBot\" -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host "BASARILI!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "PAZARTESI 10:00 - BOT OTOMATIK BASLAYACAK" -ForegroundColor Green
Write-Host ""
Write-Host "Detaylar:" -ForegroundColor Cyan
Write-Host "  Task: $TaskName"
Write-Host "  Zaman: Pazartesi 10:00 (Haftalik)"
Write-Host "  Script: $BotScript"
Write-Host "  Mod: CANLIDA"
Write-Host "  Telegram: Saatlik rapor"
Write-Host ""
