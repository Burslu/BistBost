@echo off
REM ============================================
REM BIST Bot Auto-Start Script
REM Windows Startup'ta otomatik başlaz
REM ============================================

title BIST Trading Bot - Production
color 0A

echo.
echo ========================================
echo  BIST BOT - PRODUCTION MODE
echo  Başlama zamanı: %date% %time%
echo ========================================
echo.

REM Python path
set PYTHON_PATH=C:\Users\pc\AppData\Local\Programs\Python\Python312\python.exe

REM Bot path
set BOT_PATH=C:\Users\pc\OneDrive\Desktop\BistBot\run_production.py

REM Log path
set LOG_PATH=C:\Users\pc\OneDrive\Desktop\BistBot\logs\bot_startup.log

REM Timestamp for log
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a-%%b)

echo %mydate% %mytime% - Bot başlatılıyor... >> %LOG_PATH%

REM Start bot
%PYTHON_PATH% %BOT_PATH% >> %LOG_PATH% 2>&1

if errorlevel 1 (
    echo %mydate% %mytime% - HATA! Bot başlatılamadı >> %LOG_PATH%
    pause
) else (
    echo %mydate% %mytime% - Bot başarıyla başlatıldı >> %LOG_PATH%
)
