"""
MOCK TRADING'den REAL TRADING'e GEÇIŞ REHBERI
=============================================

3 Aşamada Gerçek Para ile Trading Başla
"""

# ============================================================================
# AŞAMA 1: MOCK MODE'DA TEST ET (ŞU ANDA BURDA OLMAN)
# ============================================================================

"""
Mevcut durum:
  ✅ Bot 95 hisse analiz ediyor
  ✅ Her 5 dakikada tarama yapıyor
  ✅ Güçlü sinyal → Otomatik mock trade
  ✅ 5000 TL sanal portföy
  ✅ Risk management yüzde bazlı

Nasıl çalıştır:
  1. PowerShell'de:
     cd "C:\Users\pc\OneDrive\Desktop\BistBot"
     $env:TRADING_MODE = "mock"
     python run_production.py
  
  2. Telegram'da sinyalleri göz et
  3. 7-10 gün veri topla
  4. Win rate > 50% ise → Real'e geç


Ne beklemeliyim:
  - Her 5 dakikada %50+ güven sinyali gelirse → 1 trade
  - Günlük 10-15 sinyal
  - İlk hafta: Stabilite görelim, accuracy test et
  - Mock edebilen trades: 100-150
"""

# ============================================================================
# AŞAMA 2: NEST HESABI AÇMA & API SETUP
# ============================================================================

NEST_SETUP_CHECKLIST = """
☐ ADIM 1: Nest Hesabı Aç
  1. nest.ist → Yeni hesap
  2. E-mail confirm et
  3. Kimlik doğrula (KYC)
  4. Banka hesabını bağla

☐ ADIM 2: Para Yükle
  1. Hesabına gir → Portföy
  2. "Para Yükle" seç
  3. 500 TL yükle (başlangıç)
  4. İzle (2-3 saat)

☐ ADIM 3: Trading İzni Aktif Et
  1. Ayarlar → Trading Yetkileri
  2. "Borsa Trading" aktif et
  3. Kuralları oku, kabul et

☐ ADIM 4: API Key Oluştur
  1. Dashboard → Ayarlar
  2. "API & Geliştirme"
  3. "+ API Key" tıkla
  4. KEY ve SECRET'ı KOPYALA (şimdi!)
  5. Güvenli bir yere kaydet
  
  ⚠️  KEY'i kimseye GÖSTERME!
  ⚠️  Verlerin GİTHUB'a COMMIT ETME!
"""

# ============================================================================
# AŞAMA 3: BOT'U REAL MODE'A ÇEVIR
# ============================================================================

REAL_MODE_ACTIVATION = """
ADIM 1: Environment Variables Set Et
=====================================

PowerShell'de (Nest'ten kopyaladığın KEY/SECRET ile):

$env:TRADING_MODE = "real"
$env:NEST_API_KEY = "your_api_key_here"
$env:NEST_API_SECRET = "your_api_secret_here"

Kontrol et:
$env:TRADING_MODE
$env:NEST_API_KEY


ADIM 2: Bot'u Başlat
====================

cd "C:\Users\pc\OneDrive\Desktop\BistBot"
python run_production.py

Beklenen log output:
  🔴 REAL TRADING ENGINE BAŞLATILDI (Nest API)
  ⚠️  UYARI: Bu gerçek para ile trading yapıyor!
  ✅ Production bot başladı


ADIM 3: Monitor Et
==================

1. Telegram'ı açık tut
2. İlk trade'i bekle (5-15 dakika)
3. Emir Nest Dashboard'da görmeli
4. Position açılırsa: "✅ REAL TRADE: BUY × 10 SISE"


ADIM 4: Sonuçları Analiz Et
============================

1. İlk 10 trade'i gözle:
   - Entry fiyatı makul mi?
   - Position açılıyor mu Nest'te?
   - PnL tracking doğru mu?

2. İlk 24 saat:
   - Win: +50 TL'den fazla → İyi gidiyor
   - Loss: -50 TL ise → Parametreleri tune et
   - Hiç trade: Confidence threshold'u düşür

3. İlk hafta:
   - Win rate > 50% → Scale up
   - Loss devam → Mock'a dön, tune et
"""

# ============================================================================
# RİSK KONTROL MEKANIZMALARI
# ============================================================================

RISK_SAFEGUARDS = """
1. DAILY LOSS LIMIT
   - Günlük max loss: 100 TL (%2 portföy)
   - Ulaşılırsa: Bot kendini durdur
   - Saat 16:00'da reset

2. POSITION SIZE LIMIT
   - Max 1 hisse başına 100 TL
   - Max açık position: 5 (500 TL risk)
   - Fazlası: Sinyal reject edilir

3. R/R RATIO CHECK
   - Minimum 1:1
   - Hedef: 1.5:1 ve üzeri
   - İkisini sağlamayanlar: Otomatik skip

4. CONFIDENCE THRESHOLD
   - >50% güven → Trade aç
   - <30% → Hiç açma
   - Adjust: run_production.py'de

5. MANUAL OVERRIDE
   - Herhangi zaman: Ctrl+C
   - Telegram'dan son signal'ı manuel kapat
   - Nest Dashboard'dan emergency close
"""

# ============================================================================
# NEST DASHBOARD NASIL KULLANILIR
# ============================================================================

NEST_DASHBOARD = """
1. POSITIONS
   - Açık pozisyonlarını göster
   - Her biri için: Entry, SL, TP
   - Unrealized P&L trending

2. ORDERS
   - Geçmiş emirleri göster
   - Filled, Pending, Cancelled
   - Emir ID ile bot'u match et

3. CASH BALANCE
   - Buying power (kullanılabilir para)
   - Margin availability
   - Cash out seçeneği

4. NOTIFICATIONS
   - Emir filled mi?
   - SL/TP hit mi?
   - Bildirim al

NASIL İZLENİR:
- Bot açık kalsın (PowerShell)
- Nest Dashboard açık kalsın başka tabda
- Telegram notification açık
- İlk 24 saat kontinü izle
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

TROUBLESHOOTING = """
❌ "API Credentials bulunamadı" hatası
   → $env:NEST_API_KEY et ve kontrol et
   → PowerShell'i kapatıp tekrar aç

❌ "Order rejected" hatası
   → Nest'te yeterli cash var mı?
   → Trading hours kontrolü (09:30-16:00 weekday)
   → Hisse delisted mi? (Kontrol et)

❌ "Position açıldı ama PnL görmüyorum"
   → Nest'te gerçekten açık mı?
   → Order status kontrol et
   → Telegram mesaj gittin mi?

❌ "Bot çok hızlı trade açıyor"
   → risk_per_trade düşür: %1 yaap
   → confidence_threshold yükselt: 60% yaap
   → Max position limitü koy

❌ "SL/TP trigger olmuyor"
   → Nest platform kendi SL/TP'yi TriGGER ediyor
   → Bot'un SL/TP'si manuel filler
   → Nest Dashboard'dan kontrol et
"""

# ============================================================================
# TELEMETRY VE REPORTING
# ============================================================================

DAILY_REPORT_TEMPLATE = """
📊 DAILY TRADING REPORT
========================

Tarih: 26.03.2026
Mode: REAL / MOCK

📈 TRADES:
  - Toplam: 15
  - Winning: 9 (60%)
  - Losing: 6 (40%)
  - Win Rate: 60% ✅

💰 P&L:
  - Gross P&L: +234 TL
  - Fees: -15 TL (Nest commission)
  - Net: +219 TL

📊 RISK:
  - Daily Loss: -45 TL (safe)
  - Biggest Win: +45 TL
  - Biggest Loss: -30 TL
  - Avg Trade: +14.6 TL

⏰ TIME ANALYSIS:
  - Best hour: 11:00-12:00 (4 trades, +80 TL)
  - Worst hour: 15:30-16:00 (2 trades, -20 TL)

️📱 NOTIFICATIONS:
  - Telegram: ✅ Aktif
  - Trades sent: 15/15
  - Errors: 0

⚙️ NEXT ACTIONS:
  1. 15:30-16:00 saatinde trade sayısı azalt
  2. Confidence threshold'u %55'e yükselt
  3. Risk per trade'ı %2.5'e düşür
"""

# ============================================================================
# GRADUAL SCALING PLAN
# ============================================================================

SCALING_PLAN = """
HAFTA 1: VALIDATION
  Portfolio: 500 TL
  Risk per trade: 1%
  Goal: Win rate > 50% doğrula
  Action: Sadece izle, parametreler stabildir

HAFTA 2-3: CONFIRMATION
  Portfolio: 1000 TL (500 ekle)
  Risk per trade: 1.5%
  Goal: Consistency doğrula
  Action: Micro parametreler tune et

HAFTA 4: SCALE-UP
  Portfolio: 2000 TL (1000 ekle)
  Risk per trade: 2%
  Goal: Real'de başarılı isse → Scale
  Action: Parametreleri optimize et

FARK ETMEK İÇİN:
  - Weekly P&L > -5% → Scale down
  - Weekly P&L > +5% → Scale up
  - Win rate < 45% → Pare dön
  - Win rate > 60% → Devam et
"""

# ============================================================================
# MAIN SECURITY CHECKLIST
# ============================================================================

SECURITY_CHECKLIST = """
✅ API KEY MANAGEMENT
  ☐ API Key'i .py dosyasında yazmadım
  ☐ Environment variable kullandım
  ☐ .gitignore'da secrets isimler var
  ☐ Key'i kişiye göstermedim

✅ DATA SAFETY
  ☐ execution_log.json'da gerçek para yok
  ☐ Logs dosyasında API key yok
  ☐ Backup aldım

✅ TRADING SAFETY
  ☐ Position size test ettim (mock)
  ☐ Risk limit ayarladım
  ☐ SL/TP logic validate ettim
  ☐ Manuel stop komutu biliyorum (Ctrl+C)

✅ OPERATIONAL SAFETY
  ☐ Mock'ta 7 gün test ettim
  ☐ Win rate > 50% doğrulandı
  ☐ İlk deploy'da küçük miktarla başladım
  ☐ 24/7 monitor etmeye hazırım
"""

if __name__ == "__main__":
    print(__doc__)
    print("\n" + "="*70)
    print("SETUP CHECKLIST:")
    print("="*70)
    print(NEST_SETUP_CHECKLIST)
    print("\n" + "="*70)
    print("REAL MODE ACTIVATION:")
    print("="*70)
    print(REAL_MODE_ACTIVATION)

