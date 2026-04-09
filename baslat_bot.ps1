# BistBot Otomatik Baslat
# Windows Task Scheduler tarafindan calistirilir
# Borsa acilisi oncesi botu surekli modda baslatir

$BotDir = "C:\Users\pc\OneDrive\Desktop\BistBot"
$PythonExe = "py"
$BotScript = "bist100_signal_bot.py"
$LogFile = "$BotDir\logs\bot_startup.log"
$LockFile = "$BotDir\bot.lock"

# Log klasoru yoksa olustur
if (-not (Test-Path "$BotDir\logs")) {
    New-Item -ItemType Directory -Path "$BotDir\logs" -Force | Out-Null
}

# Zaten calisiyor mu kontrol et (CIM ile command line kontrol)
$existing = Get-CimInstance Win32_Process -Filter "Name LIKE 'python%' OR Name LIKE 'py%'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*bist100_signal_bot*" }

if ($existing) {
    $pids = ($existing | ForEach-Object { $_.ProcessId }) -join ", "
    $msg = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Bot zaten calisiyor (PID: $pids). Yeni instance baslatilmadi."
    Add-Content -Path $LogFile -Value $msg
    exit 0
}

# Eski lock dosyasi varsa temizle (process yoksa stale lock)
if (Test-Path $LockFile) {
    Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
    $msg = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Eski lock dosyasi temizlendi"
    Add-Content -Path $LogFile -Value $msg
}

# Botu baslat
Set-Location $BotDir
$msg = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Bot baslatiliyor..."
Add-Content -Path $LogFile -Value $msg

# Surekli modda baslat (arka planda)
Start-Process -FilePath $PythonExe -ArgumentList "$BotScript --mock" -WorkingDirectory $BotDir -WindowStyle Hidden -RedirectStandardOutput "$BotDir\logs\bot_output.log" -RedirectStandardError "$BotDir\logs\bot_error.log"

$msg = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Bot baslatildi (surekli mod + mock trading)"
Add-Content -Path $LogFile -Value $msg
