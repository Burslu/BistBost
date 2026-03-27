"""
DEPLOYMENT GUIDE - BIST Real-Time Trading Bot
==============================================
24/7 Otomatik Çalıştırma Seçenekleri
"""

# ═══════════════════════════════════════════════════════════════
# OPTION 1: VS Code Terminal (Basit, Hızlı)
# ═══════════════════════════════════════════════════════════════

"""
1. VS Code'u aç
2. Terminal > New Terminal (Ctrl + `)
3. Şu komutu çalıştır:

    py run_production.py

4. Terminal açık bırak, bot 24/7 çalışacak
5. Kapatmak için: Ctrl + C

Avantajlar:
  ✓ Başlamak basit (1 komut)
  ✓ Logları canlı görebilirsin
  ✓ Herhangi kurulum gerekmez

Dezavantajlar:
  ✗ VS Code kapatılırsa bot da durur
  ✗ Computer sleep moduna girerse durur
"""

# ═══════════════════════════════════════════════════════════════
# OPTION 2: PowerShell Background Job (Windows)
# ═══════════════════════════════════════════════════════════════

"""
PowerShell'de çalıştır:

    Start-Job -ScriptBlock { 
        cd 'C:\Users\pc\OneDrive\Desktop\BistBot'; 
        py run_production.py 
    }

Bot'u görmek:
    Get-Job | Format-Table Id, Name, State

Bot'u durdurmak:
    Stop-Job -Id <JOB_ID>

Avantajlar:
  ✓ VS Code kapatılsa bile çalışıyor
  ✓ PowerShell arka planda çalışır
  ✓ Kolay başlat/durdur

Dezavantajlar:
  ✗ Computer sleep modunda durur
  ✗ Restart'tan sonra otomatik başlamaz
"""

# ═══════════════════════════════════════════════════════════════
# OPTION 3: Task Scheduler (Windows Otomatik)
# ═══════════════════════════════════════════════════════════════

"""
Windows Task Scheduler'da Yeni Görev Oluştur:

1. "Task Scheduler" aç (Başlat menüsünde ara)
2. "Create Basic Task" tıkla
3. İsim: "BIST Trading Bot"
4. Trigger: "At system startup" seç
5. Action:
   - Action: "Start a program"
   - Program: C:\Users\pc\AppData\Local\Programs\Python\Python312\python.exe
   - Arguments: C:\Users\pc\OneDrive\Desktop\BistBot\run_production.py
   - Start in: C:\Users\pc\OneDrive\Desktop\BistBot
6. Conditions: 
   - ✓ "Wake the computer..."
   - ✓ "Run with highest privileges"
7. Settings:
   - ✓ "Allow task to be run on demand"
   - ✓ "Run task as soon as possible if scheduled time missed"

Sonuç: Computer açılınca bot otomatik başlar, 24/7 çalışır!

Avantajlar:
  ✓ Computer açılınca otomatik başlar
  ✓ Gerçek 24/7 deployment
  ✓ Hassasiyet arttırılabilir

Dezavantajlar:
  ✗ Setup biraz karışık
  ✗ Logları canlı takip etmek zor
"""

# ═══════════════════════════════════════════════════════════════
# OPTION 4: Docker Container (Profesyonel)
# ═══════════════════════════════════════════════════════════════

"""
Dockerfile:

    FROM python:3.12-slim
    
    WORKDIR /app
    COPY . /app/
    RUN pip install -r requirements.txt
    
    ENV PYTHONUNBUFFERED=1
    ENV PYTHONIOENCODING=utf-8
    
    CMD ["python", "run_production.py"]

Docker komutları:

    # Build
    docker build -t bist-bot .
    
    # Run (24/7)
    docker run -d --name bist-bot --restart always bist-bot
    
    # Logları görmek
    docker logs -f bist-bot
    
    # Durdurmak
    docker stop bist-bot

Avantajlar:
  ✓ Tamamen izolasyon (sistem hassasiyeti yok)
  ✓ Kolay deployment
  ✓ Production standart
  ✓ Remote deployment kolay

Dezavantajlar:
  ✗ Docker kurulması gerekir
  ✗ Setup daha kompleks
"""

# ═══════════════════════════════════════════════════════════════
# TAVSIYA: Start Simple, Scale Later
# ═══════════════════════════════════════════════════════════════

"""
İlk başlarda: OPTION 1 (VS Code Terminal)
  ✓ Hızlı test edin
  ✓ Telegram mesajlarını doğrulayın
  ✓ Görev çizelgesini ayarlayın

Sonra: OPTION 3 (Task Scheduler)
  ✓ 24/7 production mode
  ✓ Computer açılınca otomatik

Profesyonel: OPTION 4 (Docker)
  ✓ Cloud deployment (AWS, VPS)
  ✓ Multiple instances
"""

# ═══════════════════════════════════════════════════════════════
# MONITORING & LOGGING
# ═══════════════════════════════════════════════════════════════

"""
Loglar şu yerde depolanır:

    logs/production_YYYYMMDD.log

Her başlangıçta yeni dosya oluşturulur:
    logs/production_20260326.log
    logs/production_20260327.log
    ...

Log ayarları (run_production.py içinde):
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler('logs/production_YYYYMMDD.log'),
            logging.StreamHandler()  # Console'a da yazır
        ]
    )

Log örnekleri:

    2026-03-26 14:35:00 - INFO - 🚀 Production bot başladı - 10 hisse
    2026-03-26 14:35:00 - INFO - Analiz başladı: 14:35:00
    2026-03-26 14:35:05 - INFO - 🔥 SISE.IS: ZAYIF AL (78% güven)
    2026-03-26 14:35:05 - INFO - ✓ Telegram mesajı gönderildi
    2026-03-26 14:40:00 - INFO - 📊 Özet: 3 AL | 2 SAT | 5 NÖTR
"""

# ═══════════════════════════════════════════════════════════════
# TROUBLESHOOTING
# ═══════════════════════════════════════════════════════════════

"""
Bot başlamıyor?
  → Python path doğru mu? (python --version)
  → requirements.txt kurulu mu? (pip list | grep yfinance)
  → Directory doğru mu? (cd BistBot)

Telegram mesajı gitmiyor?
  → config/settings.json'da "enabled": true?
  → Bot token ve chat_id doğru?
  → @BotFather'dan yeni token al, tekrar dene

Veri çekme hatası?
  → Internet bağlantısı var mı?
  → yfinance API erişil

iyor mu? (test: py -c "import yfinance; print(yfinance.__version__)")
  → VPN kullanıyor musun? (yfinance Turkey'de çalışabilir ama VPN ile daha stabil)

Memory leak / Yavaşlama?
  → Bot'u yeniden başlat (Ctrl+C, sonra tekrar çalıştır)
  → Weekly restart scheduler'a ekle (cron job, Task Scheduler)

Performance?
  → 5 dakikalık barlar kullanıyoruz (yfinance limit: 2000 günlük history)
  → Daha hızlı işlem için: 1 dakikalık barlar (veri yoksa önermedim)
"""

# ═══════════════════════════════════════════════════════════════
# CHECKLIST - DEPLOYMENT ÖNCESI
# ═══════════════════════════════════════════════════════════════

"""
□ Python 3.12 kurulu?
□ requirements.txt kurulu? (pip install -r requirements.txt)
□ config/settings.json var? (Telegram token + chat_id)
□ Telegram bot token doğru? (@BotFather)
□ Chat ID doğru? (@userinfobot)
□ Bot'u /start ettim (@BotFather bot'u)
□ test_production_bot.py başarıyla çalıştı?
□ backtest_validator.py sonuçları iyi?
□ logs/ directory oluşturuldu?
□ data/signals/ directory oluşturuldu?

Deployment öncesi son test:
    py run_production.py
    
    (1-2 saat çalıştır, Telegram'da mesaj aldın mı?)

Hepsi tamam? ✓ Deployment için hazırız!
"""

print(__doc__)
