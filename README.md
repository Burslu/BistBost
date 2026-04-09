# BIST Algorithmic Trading Bot

324 BIST hissesini 12 teknik indikatörle analiz eden, sürekli çalışan sinyal botu.

## Özellikler

- **324 BIST hissesi** (BIST 100 + ek hisseler)
- **12 ağırlıklı teknik indikatör** (MA, MACD, ADX, Momentum, RSI, Hacim, OBV, Bollinger, Stochastic, CCI, Williams %R, ATR)
- **Trend bağlam sistemi** — güçlü trendlerde osilatör gürültüsünü bastırır
- **Pozisyon takibi** — aynı hisseye spam AL sinyali göndermez, güven artarsa tekrar bildirir
- **Sürekli çalışma modu** — borsa saatlerinde 10dk analiz, 60dk Telegram raporu
- **Mock trading** — 10.000 TL sanal bakiye ile R/R bazlı al-sat simülasyonu
- **Telegram entegrasyonu** — HTML raporlar, otomatik mesaj bölme

## Proje Yapısı

```
BistBot/
├── bist100_signal_bot.py     # Ana bot (tek dosya, tüm işlevler)
├── config/
│   └── settings.json         # Telegram token + chat_id
├── data/
│   ├── raw/                  # OHLCV önbellek
│   └── signals/              # Pozisyon takibi + mock trade log
├── logs/                     # Çalışma logları
├── requirements.txt
├── Procfile
└── .github/workflows/        # GitHub Actions (opsiyonel)
```

## Kurulum

```powershell
cd C:\Users\pc\OneDrive\Desktop\BistBot
pip install -r requirements.txt
```

Telegram için `config/settings.json`:
```json
{
  "telegram": {
    "bot_token": "BOT_TOKEN",
    "chat_id": "CHAT_ID"
  }
}
```

## Kullanım

```powershell
# Sürekli mod (varsayılan: 10dk analiz, 60dk rapor, borsa saatleri)
py bist100_signal_bot.py

# Tek seferlik analiz
py bist100_signal_bot.py --tek

# Özel aralıklar
py bist100_signal_bot.py --aralik 5 --rapor-aralik 30

# 7/24 çalış (borsa dışı saatlerde de)
py bist100_signal_bot.py --7-24

# Mock trading ile (10K TL sanal bakiye)
py bist100_signal_bot.py --mock
```

## İndikatör Ağırlıkları (v2)

| İndikatör | Ağırlık | Rol |
|-----------|---------|-----|
| MA Sistemi | 2.5 | Trend yönü |
| MACD | 1.8 | Momentum confirm |
| ADX | 1.5 | Trend gücü |
| Momentum | 1.5 | Fiyat ivmesi |
| RSI | 1.2 | Aşırı alım/satım |
| Hacim | 1.2 | Volume confirm |
| OBV | 1.0 | Akıllı para |
| Bollinger | 0.8 | Band yürüyüşü |
| Stochastic | 0.7 | Osilatör |
| CCI | 0.5 | Döngüsel |
| Williams %R | 0.5 | Momentum 2 |
| ATR | 0.0 | Bilgi amaçlı |

## Sinyal Seviyeleri

```
≥ +0.40  →  GUCLU_AL
≥ +0.10  →  ZAYIF_AL
> -0.10  →  NOTR
> -0.40  →  ZAYIF_SAT
≤ -0.40  →  GUCLU_SAT
```

## Yasal Uyarı

Bu bot eğitim amaçlıdır. Yatırım tavsiyesi değildir.
- Telegram komutlari ve portfoy takibi
