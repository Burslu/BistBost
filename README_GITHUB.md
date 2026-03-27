# BIST Algorithmic Trading Bot 🤖

Türkiye Borsa (BIST) üzerinde otomatik sinyal gönderen ve backtest yapan Python bot'u.

## Features ✨

- ✅ 95 BIST hissesinin real-time analizi
- ✅ Telegram üzerinden sinyal bildirimleri
- ✅ Multi-timeframe analizi (5m, 15m, 1h, 4h)
- ✅ Candlestick pattern tanıması
- ✅ Risk yönetimi (ATR-based SL/TP)
- ✅ Günlük backtest raporları
- ✅ %70+ güven filtresi

## Local Çalıştırma

```bash
# Clone
git clone https://github.com/USERNAME/BistBot.git
cd BistBot

# Install
pip install -r requirements.txt

# Setup env
cp .env.example .env
# .env dosyasını edit et (TELEGRAM_BOT_TOKEN vs)

# Run
python run_production.py
```

## Cloud Deployment (Railway.app)

### 1. Railway.app Signup
- https://railway.app → GitHub ile login

### 2. GitHub'a Push
```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

### 3. Railway.app Portal
- New Project → GitHub repository seç
- Variables ekle:
  - `TELEGRAM_BOT_TOKEN` = Senin Telegram token'ı
  - `TELEGRAM_CHAT_ID` = Senin Telegram chat ID'si
- Deploy başladı ✅

### 4. Bot Sonsuza Kadar Çalışıyor 🎉
- Railway 24/7 çalıştırır
- PC'ni kapatabilirsin
- Bot bulutta çalışmaya devam eder

## Configuration

### settings.json
- Hisse listesi
- Telegram credential'ları
- Analiz parametreleri
- Risk yönetimi ayarları

### logs/
- production_YYYYMMDD.log
- Bot'un tüm işlemleri kaydediliyor

## Troubleshooting

**Telegram mesajı gelmiyor?**
- settings.json'da token doğru mu?
- Chat ID doğru mu?
- `dry_run` false mı?

**Bot crash'leniyor?**
- Log dosyasına bak
- venv'yi temizle, yeniden install et

**Hisse verisi gelmiyor?**
- yfinance'ın internet bağlantısı var mı?
- Yahoo Finance'ın BIST verileri var mı?

## Stats 📊

- 🕐 Analiz periyodu: 5 dakika
- 💬 Health check: 15 dakika
- 📈 Hisse sayısı: 95
- 🎯 Min. güven: %70
- 💼 Portfolio: 5000₺ (sanal)

## License

MIT

---

**Soruları var mı?** GitHub issues'tan yaz! 🚀
