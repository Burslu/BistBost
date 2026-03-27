#!/usr/bin/env python
"""Send test intraday message"""

import requests

token = "8654047508:AAG02kXiIeZjlbfN_UTlRVtYZ39-fENSxGo"
chat_id = "636619118"
url = f"https://api.telegram.org/bot{token}/sendMessage"

message = """🟢 ZAYIF AL - SISE.IS
════════════════════════════════════════
📊 Fiyat: 46.50 ₺
💪 Güven: 🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜ 72%
⚠️  Risk: 🟩🟩🟨🟨⬜⬜⬜⬜⬜⬜ 35%

🚀 INTRADAY TRADE ANALIZI:
   🟢 Entry Quality: ✅ ÇOK İYİ (82%)
   ⚡ Momentum: ⚡ YÜKSEK (65%)
   📊 Breakout Potansiyeli: 📊 YÜKSELİŞ

📈 Teknik Analiz:
   • Stop Loss: 43.20 ₺
   • Target: 51.30 ₺
   • R:R Ratio: 1:1.45
   • Volatilite (ATR): 2.40 ₺

🔗 Piyasa + Haber Sentimenti:
   📈 Trend: 🚀 UPTREND
   😊 Pozitif
   → İyi kazançlar, yatırımcı güveni artıyor

⏰ 26.03.2026 16:28:50
—
💡 Strateji: INTRADAY (Hızlı giriş-çıkış, günlük işlem)
⚠️ NOT: Eğitim Amaçlıdır. Kendi Risk Yönetiminizi Yapınız!"""

try:
    resp = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
    print(f"✅ Status: {resp.status_code}")
    print(f"✓ Message ID: {resp.json().get('result', {}).get('message_id')}")
    print("\n📝 Message sent successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
