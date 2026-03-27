# ============================================
# BIST Bot Auto-Start PowerShell Script
# PC başlangıcında bot'u sürekli çalıştır
# ============================================

$ErrorActionPreference = "SilentlyContinue"

# Paths
$pythonPath = "C:\Users\pc\AppData\Local\Programs\Python\Python312\python.exe"
$botPath = "C:\Users\pc\OneDrive\Desktop\BistBot\run_production.py"
$logDir = "C:\Users\pc\OneDrive\Desktop\BistBot\logs"
$logFile = "$logDir\bot_startup.log"

# Create log directory if not exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Log function
function Log {
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logFile -Value "[$timestamp] $message"
}

# Check if Python exists
if (-not (Test-Path $pythonPath)) {
    Log "❌ Python bulunamadı: $pythonPath"
    exit 1
}

# Check if bot script exists
if (-not (Test-Path $botPath)) {
    Log "❌ Bot script bulunamadı: $botPath"
    exit 1
}

# Start bot in infinite loop (auto-restart on crash)
Log "🚀 Bot başlatılıyor (sonsuz mod - auto-restart)..."

$restartCount = 0
while ($true) {
    try {
        $restartCount++
        Log "---"
        Log "Başlangıç #$restartCount - $(Get-Date -Format 'HH:mm:ss')"
        
        # Start bot (blocking)
        & $pythonPath $botPath
        
        Log "⚠️  Bot durduruldu veya crashed oldu"
        Log "5 saniye sonra yeniden başlatılacak..."
        
        Start-Sleep -Seconds 5
        
    } catch {
        Log "❌ Hata: $_"
        Log "5 saniye sonra yeniden başlatılacak..."
        Start-Sleep -Seconds 5
    }
}
