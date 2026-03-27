# 📂 BIST Bot - Dosya İndeksi

## 🚀 Başlamak İçin (Bu Sırada Aç!)

| Dosya | Amaç |
|-------|------|
| **QUICK_START.py** | 👈 **BURADAN BAŞLA!** 5 dakikada setup |
| **README.md** | Sistem özellikleri, indikatörler, risk management |
| **DEPLOYMENT_GUIDE.py** | 24/7 çalıştırma seçenekleri (VS Code, Task Scheduler, Docker) |

---

## 🤖 Core Python Modülleri

### **realtime_analyzer.py** (MAIN ENGINE)
- **Amacı**: 11 teknik indikatör hesapla, ağırlıklı skor üret
- **Çalıştırma**: `py test_realtime.py`
- **Çıktı**: TradingSignal objesi (sembol, fiyat, sinyal, güven%)
- **Satırlar**: ~800 code
- **Sınıflar**:
  - `IndikatorSignal`: Tek indikatörün sonucu
  - `TradingSignal`: Final sinyal (11 indikatörün ağırlıklı toplamı)
  - `RealTimeAnalyzer`: Veri çek + analiz yap
- **Indikatörler** (11 adet):
  1. MA Sistemi (×2.0) - Golden/Death Cross
  2. RSI (×1.5) - Aşırı satım/alım
  3. MACD (×1.5) - Momentum
  4. ADX (×1.3) - Trend gücü
  5. ATR (×1.2) - Volatilite
  6. Bollinger Bands (×1.0) - Aşırı hareket
  7. Stochastic (×1.0) - Oscillator
  8. CCI (×0.9) - Cyclic
  9. Williams %R (×1.0) - Momentum 2
  10. Hacim (×0.8) - Volume
  11. Haber Sentiment (×1.5) - NLP (placeholder)

### **backtest_validator.py** (TARIHSEL TEST)
- **Amacı**: Geçmiş 1 yıl veri ile strateji test et
- **Çalıştırma**: `py backtest_validator.py`
- **Çıktı**: Win rate, getiri %, profit factor
- **Sonuç**: ASELS.IS +93.74%, ortalama +10-12%
- **Satırlar**: ~350 code
- **Sınıf**: `BacktestValidator`
- **Metodları**:
  - `veri_çek_gunluk()` - 1 yıllık daily bar
  - `taraf_oyu()` - MA, RSI, MACD oyları
  - `simülasyon()` - Trade simulation, risk management
- **Output**: 
  - CSV: `data/signals/ozet_*.csv`
  - JSON: `data/signals/backtest_rapor_*.json`

### **run_production.py** (24/7 BOT)
- **Amacı**: 5 dakikaya bir analiz et, saatlik özet gönder
- **Çalıştırma**: `py run_production.py`
- **Periyot**: 5 dakika (config'de değiştirilebilir)
- **Telegram**: Güçlü sinyalleri hemen (>75% güven) + saatlik özet
- **Satırlar**: ~400 code
- **Sınıf**: `ProductionBot`
- **Metodları**:
  - `analiz_dongusu()` - Main loop, 5 dakikada bir çalış
  - `sinyal_telegramgönder()` - Güçlü sinyal gönder
  - `saatlik_ozet_telegramgönder()` - Top 5 sinyal gönder + CSV kaydet
- **Output**:
  - Log: `logs/production_YYYYMMDD.log`
  - CSV: `data/signals/ozet_*.csv` (saatlik)

---

## 🧪 Test Dosyaları

### **test_realtime.py**
- Hızlı test: 1 hisse (THYAO.IS), 5 dakikalık barlar
- Çıktı: Fiyat, sinyal, güven%, 11 indikatör detayı
- Zaman: ~5 saniye
- Kullanım: `py test_realtime.py`

### **test_production_bot.py**
- Production bot test: 2 döngü, 1 dakika periyot
- Çıktı: Terminal logları
- Zaman: ~2 dakika
- Kullanım: `py test_production_bot.py`

---

## ⚙️ Konfigürasyon

### **config/settings.json**
```json
{
  "symbols": {
    "bist": [10 hisse],
    "global": [7 makro gösterge]
  },
  "market_data": {
    "period": "1mo",           // 1 aylık veri
    "interval": "5m"           // 5 dakikalık barlar
  },
  "strategy": {
    "fetch_interval_minutes": 5,
    "indicator_weights": {...},
    "score_thresholds": {...}
  },
  "telegram": {
    "enabled": true/false,
    "bot_token": "YOUR_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "paths": {
    "raw_dir": "data/raw",
    "signals_dir": "data/signals",
    "log_dir": "logs"
  }
}
```

### **config/settings.py**
- Python dosyası
- `load_settings()` - JSON yükle
- `save_settings()` - JSON kaydet

---

## 📊 Veri Klasörleri

### **data/raw/**
Yfinance'den çekilen ham OHLCV verisi
- `global_YYYYMMDD_HHMMSS.csv` - Makro göstergeler (XU100, ^GSPC, vb.)
- `hisseler_YYYYMMDD_HHMMSS.csv` - BIST hisseleri (THYAO, EREGL, vb.)

### **data/signals/**
Sinyal çıktıları ve backtest raporları
- `tum_sinyaller_*.csv` - Tüm analiz edilen hisseler
- `aksiyon_sinyalleri_*.csv` - Actionable sinyaller (|skor| ≥ 0.2)
- `ozet_*.csv` - Saatlik özet (production bot)
- `backtest_rapor_*.json` - 1 yıllık backtest sonuçları

---

## 📝 Log Klasörü

### **logs/**
- `production_YYYYMMDD.log` - Production bot logları
- `realtime_bot.log` - Realtime analyzer logları
- `run_YYYYMMDD_HHMMSS.json` - Run metadata (timestamp, işlem sayısı, vb.)

---

## 📚 Eski Dosyalar (V1 - Hala Çalışıyor)

| Dosya | Not |
|-------|-----|
| `bist_veri_cekici.py` | V1: Günlük veri fetcher (yfinance wrapper) |
| `teknik_analiz.py` | V1: 6 indikatör (deprecated, `realtime_analyzer.py` kullanılıyor) |
| `gunluk_sinyal_akisi.py` | V1: Günlük orchestrator (REPLACED by `run_production.py`) |
| `telegram_bot.py` | V1: Telegram wrapper (INTEGRATED to `run_production.py`) |
| `run_daily.ps1` | V1: Daily scheduler (REPLACED by Task Scheduler) |
| `Bist veri cekici.py` | V1: Original (RENAMED to `bist_veri_cekici.py`) |
| `Teknik analiz.py` | V1: Original (RENAMED to `teknik_analiz.py`) |

---

## 📋 Diğer Dosyalar

### **requirements.txt**
Python bağımlılıkları
```
yfinance==1.2.0
pandas==3.0.1
numpy==2.4.3
requests==2.33.0
```

### **QUICK_START.py**
- 5 dakikada başlama rehberi
- 3 adım: Test → Backtest → Production
- Çalıştırma: `py QUICK_START.py`

### **DEPLOYMENT_GUIDE.py**
- 24/7 çalıştırma seçenekleri
- 4 option: VS Code, PowerShell, Task Scheduler, Docker
- Troubleshooting & checklist
- Çalıştırma: `py DEPLOYMENT_GUIDE.py`

### **README.md**
Sistem özellikleri, indikatörler, risk management, kurulum

### **INDEX.md** (BU DOSYA)
Tüm dosyaların açıklaması ve ilişkileri

---

## 🔄 Workflow

### Senaryo 1: İlk Çalıştırma
```
1. QUICK_START.py oku
2. py test_realtime.py → Test
3. py backtest_validator.py → Doğru
4. Telegram ayarla (token + chat_id)
5. py run_production.py → Başlat
```

### Senaryo 2: Strateji Test
```
1. config/settings.json'da indicators ağırlıklarını değiştir
2. py backtest_validator.py → Yeni sonuç
3. İyi mi? Evet → Production'a git
4. Hayır? Tekrar değiştir → Adım 2
```

### Senaryo 3: 24/7 Deployment
```
1. DEPLOYMENT_GUIDE.py oku
2. Option 1-4 arasında seç
3. Setup yap
4. Bot öz-check (logs'u kontrol et)
5. 24/7 monitor (Telegram'da mesaj varmı?)
```

---

## 🎯 Sinyal Akışı

```
YFinance (OHLC veri)
    ↓
realtime_analyzer.py (11 indikatör hesapla)
    ↓
Ağırlıklı Skor (-1 ile +1)
    ↓
Sinyal Seviyesi (GÜÇLÜ AL / AL / NÖTR / SAT / GÜÇLÜ SAT)
    ↓
backtest_validator.py (test) veya run_production.py (live)
    ↓
CSV + Telegram + JSON Log çıktı
```

---

## 📊 Dosya Boyutları

| Dosya | Satırlar | Boyut |
|-------|----------|-------|
| realtime_analyzer.py | ~800 | 30 KB |
| backtest_validator.py | ~350 | 12 KB |
| run_production.py | ~400 | 15 KB |
| config/settings.json | ~60 | 2 KB |
| README.md | ~200 | 8 KB |
| **TOTAL** | **~2000** | **~70 KB** |

---

## ✅ Kontrol Listesi

Başlamadan önce kontrol et:

- [ ] Python 3.12 kurulu?
- [ ] `pip install -r requirements.txt`?
- [ ] `config/settings.json` ayarlandı (Telegram)?
- [ ] `py test_realtime.py` başarılı?
- [ ] `py backtest_validator.py` sonuçları iyi?
- [ ] `logs/` ve `data/signals/` klasörleri var?

Hepsi OK? ✓ **QUICK_START.py'ı çalıştır!**

---

## 🆘 Yardım

| Soru | Cevap |
|------|-------|
| Nereden başlayım? | QUICK_START.py |
| Nasıl çalıştırırım? | `py run_production.py` |
| 24/7 nasıl? | DEPLOYMENT_GUIDE.py |
| Telegram almıyorum? | config/settings.json'daki token/chat_id doğru mu? |
| Getiri nasıl? | `py backtest_validator.py` → ortalama %10-12 |
| Indikatör nedir? | README.md'nin "Indikatör Açıklamaları" bölümü |

---

**Tarih**: 2026-03-26 | **Sürüm**: 2.0 | **Status**: Production Ready ✅
