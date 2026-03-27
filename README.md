# 🤖 BIST Real-Time Trading Bot

Algoritmik ticaret asistanı - **Real-time sinyal üretimi, ağırlıklı analiz, saatlik Telegram özeti**

## 📋 Sistem Özellikleri

✅ **11 Teknik İndikatör**: MA, RSI, MACD, ADX, ATR, Bollinger, Stochastic, CCI, Williams %R, Hacim, Haber Sentiment

✅ **Ağırlıklı Skor Sistemi**: Her indikatörün kat sayıları farklı (MA×2.0, RSI×1.5, MACD×1.5, vs.)

✅ **Real-Time Analiz**: 5 dakikalık barlarla sürekli veri güncelleme

✅ **Telegram Entegrasyonu**: Güçlü sinyaller anında + saatlik özet mesajları

✅ **BacktestValidator**: 1 yıllık geçmiş veri - %93 getiri test sonucu!

## 📊 Proje Yapısı

```
BistBot/
├── realtime_analyzer.py      (👈 MAIN: 11 indikatör + ağırlıklı skor)
├── backtest_validator.py     (Geçmiş 1 yıl test - backtest raporu)
├── run_production.py         (Production bot - 24/7 mode)
├── test_realtime.py          (Hızlı test - 1 hisse)
│
├── config/
│   ├── settings.json         (Konfigürasyon)
│   └── settings.py           (Loader)
│
├── data/
│   ├── raw/                  (OHLCV veri)
│   └── signals/              (Sinyal CSV + backtest raporu)
│
├── logs/                     (Günlük loglar)
├── requirements.txt          (Bağımlılıklar)
└── README.md                 (Bu dosya!)
```

## 🚀 Başlangıç (3 adım)

### 1️⃣ Kurulum
```powershell
cd C:\Users\pc\OneDrive\Desktop\BistBot
pip install -r requirements.txt
```

### 2️⃣ Telegram Setup (OPTIONAL)
- @BotFather ile bot oluştur, token al
- @userinfobot ile chat_id al
- config/settings.json'u güncelle

### 3️⃣ Çalıştır
```powershell
# Test (1 hisse)
py test_realtime.py

# Backtest (1 yıl - görün sistem ne kadar başarılı)
py backtest_validator.py

# Production (5 dakikada bir, saatlik Telegram özeti)
py run_production.py
```

## 📈 İndikatör Ağırlıkları

```
MA Sistemi:      ×2.0  (Trend yönü en kritik)
RSI:             ×1.5  (Momentum)
MACD:            ×1.5  (Momentum confirmation)
ADX:             ×1.3  (Trend gücü)
ATR:             ×1.2  (Volatilite ölçüsü)
Bollinger:       ×1.0  (Aşırı hareket)
Stochastic:      ×1.0  (Oscillator)
Williams %R:     ×1.0  (Momentum 2)
CCI:             ×0.9  (Cyclic indicator)
Hacim:           ×0.8  (Volume confirmation)
Haber Sentiment: ×1.5  (KAP + NLP - henüz placeholder)
```

## 🎯 Sinyal Seviyeleri

```
+0.50 ve üstü    → 🟢 GÜÇLÜ AL      (Strong Buy)
+0.20 ~ +0.50    → 📗 ZAYIF AL      (Weak Buy)
-0.20 ~ +0.20    → ⚪ NÖTR           (Neutral)
-0.50 ~ -0.20    → 📕 ZAYIF SAT     (Weak Sell)
-0.50 ve altı    → 🔴 GÜÇLÜ SAT     (Strong Sell)
```

## ✅ Backtest Sonuçları (1 Yıl)

| Sembol | Getiri | Win Rate | İşlem | Status |
|--------|--------|----------|-------|--------|
| ASELS.IS | **+93.74%** | 100% | 5 | 🚀 |
| SISE.IS | +21.07% | 60% | 9 | ✓ |
| AKBNK.IS | +20.95% | 50% | 8 | ✓ |
| YKBNK.IS | +18.45% | 50% | 8 | ✓ |
| Ortalama | **~10-12%** | ~50% | - | ✓ Pozitif |

## ⚠️ Risk Management

```
Stop-Loss = Giriş - 1.5×ATR
Take-Profit = Giriş + 2.0×ATR
Risk:Reward = 1:1.33 (favorable)
```

## 🛠️ Gelecek Geliştirmeler

- [ ] KAP haber NLP integre et
- [ ] Makro göstergeler ekle (USD/TRY, altın, petrol)
- [ ] Backtester parameter optimizasyonu
- [ ] Web Dashboard
- [ ] Docker deployment

## ⚠️ Yasal Uyarı

**Bu bot EĞİTİM amaçlıdır!** Yatırım TAVSİYESİ DEĞİLDİR. Piyasa riski yüksektir, kaybetmeyi göze alanlar kullanmalı.

Bu durumda mesaj sadece terminale yazdirilir. Gercek gonderim icin:

- telegram.enabled = true
- telegram.dry_run = false
- telegram.bot_token ve telegram.chat_id alanlarini doldur

## Sonraki Fazlar

- Haber/KAP NLP skoru ekleme
- Makro/global skorun karar modeline entegrasyonu
- Backtest ve walk-forward test
- Telegram komutlari ve portfoy takibi
