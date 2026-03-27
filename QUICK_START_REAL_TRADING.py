"""
🤖 BIST BOT - MOCK → REAL TRADING QUICK START
==============================================
"""

# ============================================================================
# ŞUANKI DURUM
# ============================================================================

CURRENT_STATUS = """
✅ BOT ÇALIŞIYOR (Job 31 - MOCK MODE)
  - 95 BIST hissesi analiz ediliyor
  - Her 5 dakikada tarama yapılıyor
  - Mock portföy: 5000 TL
  - Telegram: Aktif (güçlü sinyaller gönderiliyor)
  - Risk management: Her trade %2 risk

YAPILAN:
  ✅ 11 teknik gösterge + ağırlık sistemi
  ✅ Intraday metrikleri (Entry Quality, Momentum, Breakout)
  ✅ Haber sentiment analizi (açıklamalar ile)
  ✅ Position sizing hesabı
  ✅ R/R ratio validasyonu
  ✅ Mock trading engine
  ✅ Nest API integration altyapısı
  ✅ Mode switching (mock ↔ real)

BEKLENEN:
  - 5 dakika içinde >50% güven sinyali gelirse → Position açılacak
  - Telegram'da mesaj gelecek
  - Sanal para eksi/artı olacak
"""

print(CURRENT_STATUS)

# ============================================================================
# 3 Lİ GEÇIŞ PLANI
# ============================================================================

PLAN = """
╔════════════════════════════════════════════════════════════════╗
║ GEÇIŞ PLANI: MOCK → REAL TRADING                             ║
╚════════════════════════════════════════════════════════════════╝

┌─ AŞAMA 1: MOCK MODE TESTE (ŞU ANDA BURADA) ──────────────────┐
│                                                                │
│ Durum: Bot çalışıyor, sanal portföy 5000 TL                  │
│ Hedef: Win rate > 50%, consistency doğrula                   │
│ Süre: 7-10 gün                                               │
│ Kontrol:                                                      │
│   ✓ İlk 100 trade'i gözle                                   │
│   ✓ Win/Loss oranı hesapla                                  │
│   ✓ False positives kontrol et                              │
│   ✓ Sabah/öğlen/akşam fark etkisini gözle                   │
│ Başarı Kriteri:                                              │
│   - Win rate > 50%                                           │
│   - Consecutive losses < 3                                   │
│   - P&L consistency                                          │
│                                                                │
└────────────────────────────────────────────────────────────────┘

┌─ AŞAMA 2: NEST ACCOUNT SETUP ─────────────────────────────────┐
│                                                                │
│ Mock'ta başarılı isen:                                        │
│   1. Nest.ist → Yeni hesap aç                               │
│   2. Kimlik doğrula (KYC)                                    │
│   3. 500 TL para yükle                                       │
│   4. Dashboard → Settings → API                             │
│   5. API Key + Secret oluştur & KOPYALA                    │
│                                                                │
│ ⚠️  UYARILAR:                                                │
│   - Key'i kimseye gösterme                                   │
│   - GitHub'a commit etme                                     │
│   - Güvenli bir yerde kaydet                                │
│                                                                │
└────────────────────────────────────────────────────────────────┘

┌─ AŞAMA 3: REAL MODE BAŞLAT ───────────────────────────────────┐
│                                                                │
│ PowerShell'de:                                                │
│                                                                │
│ $env:TRADING_MODE = "real"                                   │
│ $env:NEST_API_KEY = "your_key"                              │
│ $env:NEST_API_SECRET = "your_secret"                        │
│                                                                │
│ cd "C:\Users\pc\OneDrive\Desktop\BistBot"                   │
│ python run_production.py                                     │
│                                                                │
│ Beklenen log:                                                 │
│   🔴 REAL TRADING ENGINE BAŞLATILDI (Nest API)             │
│   ⚠️  UYARI: Bu gerçek para ile trading yapıyor!            │
│                                                                │
│ 24 saat monitoring:                                           │
│   ✓ Telegram'ı açık tut                                      │
│   ✓ Trades açılıyor mu kontrol et                           │
│   ✓ PnL tracking doğru mu                                   │
│   ✓ Hiçbir sorunda Ctrl+C ile durdur                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘

╔════════════════════════════════════════════════════════════════╗
║ TIMING ÖNERILERI                                              ║
╚════════════════════════════════════════════════════════════════╝

Pazartesi 10:00      : Mock mode'yı başlat
Pazartesi-Cuma       : 7 gün observe et
Sonraki Pazartesi    : Nest setup & real mode başlat
Sonraki 24 saat      : Intense monitoring
Sonraki hafta        : Normal ops, daily reports
"""

print(PLAN)

# ============================================================================
# DOSYA REFERENSLERI
# ============================================================================

FILES = """
📁 KEY FILES / REHBER DOSYALARI

├─ NEST_INTEGRATION_GUIDE.py
│  └─ Nest API client kodu
│  └─ Başlama adımları
│  └─ API endpoint'leri
│
├─ real_trading_engine.py
│  └─ Gerçek trading engine
│  └─ Mock/Real switching factory
│  └─ Position management
│
├─ REAL_TRADING_GUIDE.py
│  └─ Detaylı geçiş rehberi
│  └─ Risk kontrol mekanizmaları
│  └─ Troubleshooting
│  └─ Daily report template
│
├─ run_production.py
│  └─ Main bot orchestrator
│  └─ Mode switching mantığı
│  └─ Signal executor entegrasyonu
│
├─ trading_engine.py
│  └─ Mock trading engine
│  └─ Position sizing
│  └─ Risk management
│
└─ signal_executor.py
   └─ Bot sinyali → Trade dönüştürücü
   └─ Mock/Real engine uyumlu
"""

print(FILES)

# ============================================================================
# KOMUTLAR
# ============================================================================

COMMANDS = """
🎮 KULLANFUL KOMUTLAR

1. MOCK MODE (Şuanki)
   ─────────────────
   $env:TRADING_MODE = "mock"
   python run_production.py

2. REAL MODE (Nest'e bağlı)
   ──────────────────────
   $env:TRADING_MODE = "real"
   $env:NEST_API_KEY = "key"
   $env:NEST_API_SECRET = "secret"
   python run_production.py

3. BOT'U DURDURMAK
   ──────────────
   Ctrl+C (PowerShell'de)

4. BOT DURUMUNU GÖRMEK
   ──────────────────
   Get-Job
   Receive-Job -Id <ID> -Keep

5. PORTFÖY DASHBOARD
   ────────────────
   python dashboard.py

6. TRADING LOGU
   ───────────
   Get-Content execution_log.json
"""

print(COMMANDS)

# ============================================================================
# SAATLIK CHECKLIST
# ============================================================================

HOURLY_CHECK = """
⏰ SAATLIK KONTROL LİSTESİ (Real mode'da)

[ ] Telegram açık mı? (Notifications aktif)
[ ] Bot çalışıyor mı? (PowerShell window)
[ ] Trades Nest'te açılıyor mu?
[ ] PnL doğru hesaplanıyor mu?
[ ] Loss limit aşıldı mı? (Daily -100 TL)
[ ] Hiç kritik hata var mı?

EĞERİSTE SORUN OLUŞURSA:
  1. Ctrl+C ile bot'u durdur
  2. Nest Dashboard'da pozisyonları kontrol et
  3. Manual kapatman gerekirse Nest'ten kapat
  4. Logs/production_*.log dosyasını oku
  5. Hata tekrarlanıyor mu? → run_production.py debug mode
"""

print(HOURLY_CHECK)

# ============================================================================
# İLK 24 SAAT AYAR
# ============================================================================

FIRST_24_HOURS = """
🚀 İLK 24 SAAT AYAR REHBERI

SAATİL 0: SETUP
  ✓ Real mode env vars set et
  ✓ Bot başlat
  ✓ Nest Dashboard açık tut

SAATİL 1-2: STABILIZASYON
  ✓ İlk işlem görün
  ✓ Nest'te position açık mı?
  ✓ Telegram mesaj geliyor mu?
  ✓ Risk yönetimi çalışıyor mu?

SAATİL 2-6: GÖZLEMLEME
  ✓ Minimum 5-10 trade'i gözle
  ✓ Win/Loss sayısını not et
  ✓ Entry fiyatları makul mı?
  ✓ Position sizing doğru mu?

SAATİL 6-12: GÜNE YAKLAŞ
  ✓ Consolidation süresi
  ✓ Parametreler stabil mi?
  ✓ İlk 100 trade'in win rate'ını hesapla

SAATİL 12-24: SABAH AÇILIŞ ÖNCESİ
  ✓ Gece analiz: Parametreler tune edildi mi?
  ✓ Sabah açılışı monitör etme (hızlı volatilite)
  ✓ Günlük loss limit kontrol

BAŞARILI GÖSTERGELER:
  - Win rate >= 50%
  - P&L >= +50 TL
  - No system errors
  - Trades executing smoothly
"""

print(FIRST_24_HOURS)

print("\n" + "="*70)
print("📞 SORULARSAN:")
print("="*70)
print("1. Nest API docu: https://api.nest.ist/documentation")
print("2. Bot logs: logs/production_<date>.log")
print("3. Execution log: execution_log.json")
print("4. Telegram: Hattı açık tut mesajları gelmesi için")
print("\nHazır mısın? 🚀")
