"""
╔════════════════════════════════════════════════════════════════════╗
║           🤖 BIST REAL-TIME TRADING BOT - QUICK START              ║
║                    5 Dakikada Başlat!                              ║
╚════════════════════════════════════════════════════════════════════╝
"""

# ───────────────────────────────────────────────────────────────────
# ADIM 1: Test Et (1 dakika)
# ───────────────────────────────────────────────────────────────────

print("""
🎬 ADIM 1: HIZLI TEST

Terminal'de çalıştır:

    py test_realtime.py

Beklenen çıktı:
    ✓ Veri çekildi: 1776 bar
    ✓ Analiz tamamlandı
    ✓ Sembol: THYAO.IS
    ✓ Sinyal: NÖTR/AL/SAT/vs
    ✓ Güven: X% 
    ✓ 11 indikatörün skorları

İşte bitmiş! ✓ Sistem çalışıyor.
""")

# ───────────────────────────────────────────────────────────────────
# ADIM 2: Backtest Çalıştır (2 dakika)
# ───────────────────────────────────────────────────────────────────

print("""
📊 ADIM 2: BACKTEST (Geçmiş Net Kâr)

Terminal'de:

    py backtest_validator.py

Beklenen çıktı:
    ASELS.IS        93.74%        100%       5
    SISE.IS         21.07%       60.0%       9
    AKBNK.IS        20.95%       50.0%       8
    ...
    Ortalama: ~10-12% getiri ✓

Harika! Sistem tarihsel olarak karla çalışıyor.
""")

# ───────────────────────────────────────────────────────────────────
# ADIM 3: Production Başlat (1 dakika)
# ───────────────────────────────────────────────────────────────────

print("""
🚀 ADIM 3: PRODUCTION MODE (24/7)

Terminal'de:

    py run_production.py

Beklenen çıktı:
    ============================================================
    🚀 Production bot başladı - 10 hisse takip ediliyor
       Periyot: 5 dakika
       Telegram: ✓ Aktif
    ============================================================
    
    Analiz başladı: 14:35:00
    🔥 THYAO.IS: ZAYIF AL (68% güven)
    ✓ EREGL.IS: NÖTR (12% güven)
    ✓ GARAN.IS: ZAYIF SAT (45% güven)
    ...
    
    📊 Özet: 3 AL | 2 SAT | 5 NÖTR
    ⏱️  Sonraki analiz: 5 dakika sonra

Bot şimdi 5 dakikada bir veri çekiyor ve analiz ediyor!

📱 Telegram'a da mesaj alıyorsun olmalı. Kontrol et!

💡 Bot'u durdurmak: Ctrl + C

BOTun 24/7 çalışması için DEPLOYMENT_GUIDE.py'ı oku!
""")

# ───────────────────────────────────────────────────────────────────
# BONUS: Konfigürasyon Değişiklikleri
# ───────────────────────────────────────────────────────────────────

print("""
⚙️  KONFIGÜRASYON (config/settings.json)

1. Hangi hisseleri takip etmek istersen?
   "bist": ["THYAO.IS", "EREGL.IS", ...]  ← bu listeyi düzenle

2. Periyodu değiştirmek?
   "fetch_interval_minutes": 5  ← 1, 2, 5, 15, 60 vb.

3. Telegram kapalı mı?
   "enabled": true/false
   "dry_run": false  (false = gerçek gönder, true = test)

4. Indikatör ağırlıklarını değiştirmek?
   "indicator_weights": { 
     "MA_Sistemi": 2.0, 
     ... 
   }

Hepsi değiştirildi? Bot'u yeniden başlat!
""")

# ───────────────────────────────────────────────────────────────────
# ARKADAŞÇA SAHİBİ TİPLERİ
# ───────────────────────────────────────────────────────────────────

print("""
📚 DOSYALAR & AÇIKLAMA

realtime_analyzer.py
  → MAIN MOTOR
  → 11 indikatör hesapla
  → Ağırlıklı skor üret
  
backtest_validator.py
  → Geçmiş 1 yıl test et
  → Win rate, getiri hesapla
  → Strateji doğrulaması
  
run_production.py
  → 5 dakikaya bir çalış
  → Saatlik Telegram özeti
  → 24/7 takip
  
config/settings.json
  → Tüm ayarlar burası
  → Token, chat_id, hisseler, vb.

data/signals/
  → Sinyal CSV'leri
  → Backtest raporları
  
logs/
  → Günlük loglar
  → Debug & monitoring
""")

# ───────────────────────────────────────────────────────────────────
# HATIRLATMALAR
# ───────────────────────────────────────────────────────────────────

print("""
⚠️  ÖNEMLI HATIRLATMALAR

1. ✓ Python 3.12 lazım
2. ✓ pip install -r requirements.txt yap
3. ✓ Telegram token + chat_id ayarla (@BotFather + @userinfobot)
4. ✓ Bot'u /start et (handshake gerekir)
5. ⚠️ YASAL: Bu bot EĞİTİM amaçlıdır, YATIRıM TAVSİYESİ DEĞİLDİR

5 saniye sonra hata alırsan?
  → README.md'deki Troubleshooting bölümünü oku
  → DEPLOYMENT_GUIDE.py'ı oku
  → Code içindeki kommentleri oku
""")

# ───────────────────────────────────────────────────────────────────
# 24/7 DEPLOYMENT (Seçimli)
# ───────────────────────────────────────────────────────────────────

print("""
🌍 24/7 DEPLOYMENT (OPTIONAL)

Bot'u her zaman çalıştırılmasını mı istiyorsun?

A. Windows Task Scheduler (En Kolay)
   → DEPLOYMENT_GUIDE.py'ı oku
   → Computer açılınca otomatik başlar

B. Docker (Profesyonel)
   → Docker kur
   → docker build -t bist-bot .
   → docker run -d --restart always bist-bot

C. Linux VPS (Uzun vadeli)
   → Screen session ile çalıştır
   → Cron job schedule

Hangi seçeneği seçersen seç, DEPLOYMENT_GUIDE.py adım adım anlatıyor!
""")

# ───────────────────────────────────────────────────────────────────
# BİTİS
# ───────────────────────────────────────────────────────────────────

print("""
════════════════════════════════════════════════════════════════════

✅ Başlama Kontrol Listesi:

    □ Python 3.12 kurulu
    □ pip install -r requirements.txt
    □ config/settings.json ayarlandı (token, chat_id)
    □ py test_realtime.py başarısız
    □ py backtest_validator.py başarısız
    □ py run_production.py çalışıyor (terminal'de loglar?)

Hepsi seçili? 🎉 
BIST Trading Bot'u başlat ve Telegram'da mesaj bekle!

💬 Sorular? Kod içindeki comments'i oku!
📖 Daha fazla: README.md, DEPLOYMENT_GUIDE.py

Happy Trading! 📈

════════════════════════════════════════════════════════════════════
""")

if __name__ == "__main__":
    input("\nDevam etmek için Enter'a basınız...")
