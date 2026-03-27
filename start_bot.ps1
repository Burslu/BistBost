# BIST Bot - Windows Task Scheduler Starter Script
# Bu script Windows Task Scheduler tarafından başlatılacak
# Otomatik olarak run_production.py'i background'da çalıştırır

$pythonExe = "C:\Users\pc\AppData\Local\Programs\Python\Python312\python.exe"
$botPath = "C:\Users\pc\OneDrive\Desktop\BistBot\run_production.py"
$botDir = "C:\Users\pc\OneDrive\Desktop\BistBot"

# Log dosyası
$logFile = "$botDir\logs\startup_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Bot'u başlat ve çıkışını log'a yaz
try {
    & $pythonExe $botPath >> $logFile 2>&1
} catch {
    Add-Content -Path $logFile -Value "Hata: $_"
}
