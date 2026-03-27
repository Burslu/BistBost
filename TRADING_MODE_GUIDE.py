"""
Trading Mode Configuration
=========================
Mock ve Real Trading'i kontrol et
"""

TRADING_CONFIG = {
    # ========================================
    # TRADING MODE: mock yada real
    # ========================================
    "mode": "mock",  # ← BURADAN DEĞİŞTİR
    
    # Mock mode settings
    "mock": {
        "portfolio_size": 5000.0,      # Sanal portföy (TL)
        "risk_per_trade": 2.0,         # Her trade'de risk %
        "min_rr_ratio": 1.0            # Minimum R/R oranı (1:1)
    },
    
    # Real mode settings (Nest)
    "real": {
        "use_sandbox": False,          # True = test, False = production
        # API Keys: environment variables'dan oku!
        # Kodda yazmayın! GÜVENLİK için env var kullan
        # set NEST_API_KEY=your_key
        # set NEST_API_SECRET=your_secret
    },
    
    # Telegram bilgileri (her mode'da kullanılır)
    "telegram": {
        "enabled": True,
        "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
        "chat_id": "YOUR_CHAT_ID"
    }
}

# ====================================================================
# NASIL KULLANILIR?
# ====================================================================

"""
ADIM 1: MOCK MODE'DA TEST ET
=============================
1. config/trading_mode.json kullan
2. "mode": "mock"
3. Bot sanal portföy ile çalışır
4. Hiçbir gerçek para risk etmez


ADIM 2: REAL MODE'A GEÇIŞ
==========================
1. Nest hesabı aç (https://www.nest.ist)
2. Küçük miktarda para yükle (başlangıçta 500-1000 TL)
3. API Key al (Dashboard → Ayarlar)
4. PowerShell'de:
   
   $env:NEST_API_KEY = "your_key_here"
   $env:NEST_API_SECRET = "your_secret_here"
   
5. run_production.py'de:
   
   config["mode"] = "real"
   
6. Bot gerçek trading yapmaya başlayacak


GÜVENLIK UYARILARI
==================
❌ YAPMA:
- API Key'ini koda yazma
- Secret'ı version control'e commit etme
- Başlangıçta büyük miktarla test etme

✅ YAP:
- Environment variables kullan
- Small position size ile başla (10-20 TL)
- Mock mode'da iyi sonuç aldıktan sonra real'e geç
- Günlük loss limit belirle


ADIM ADIM REAL TRADING BAŞLANGIÇI
==================================

Saat 1: Nest Hesabı Açıp Para Yükle
    └─ nest.ist → Yeni hesap
    └─ 500 TL yükle
    └─ KYC (kimlik doğrula)

Saat 2: API Credentials Al
    └─ Dashboard → Ayarlar
    └─ API geliştirme
    └─ Key + Secret oluştur
    └─ Save!

Saat 3: Bot'u Konfigure Et
    └─ PowerShell'de env set et
    └─ trading_mode.json: "mode": "real"
    └─ First trade size az olsun (10 TL = 1-2 adet)

Saat 4-24: Monitor
    └─ Telegram'da her trade'i gör
    └─ İlk 24 saat loss ise, sebeb analiz et
    └─ Win rate > 50% ise scale up
"""

