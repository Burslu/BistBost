#!/usr/bin/env python
"""Test advanced message format"""

import requests

token = "8654047508:AAG02kXiIeZjlbfN_UTlRVtYZ39-fENSxGo"
chat_id = "636619118"
url = f"https://api.telegram.org/bot{token}/sendMessage"

message = """🟢 ZAYIF AL - THYAO.IS
════════════════════════════════════════
📊 Fiyat: 293.00 ₺
💪 Güven: 🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜ 60%
⚠️  Risk: 🟩🟨🟨⬜⬜⬜⬜⬜⬜⬜ 20%

📈 Teknik Analiz:
   • Stop Loss: 291.50 ₺
   • Target: 296.00 ₺
   • R:R Ratio: 1:1.67
   • Volatilite (ATR): 1.8 ₺

🔗 Piyasa Durumu:
   📈 Genel Trend: 🚀 UP
   📰 Haber: 😊 Pozitif

⏰ Advanced Metrics: AKTIF ✓
—
⚠️ Not: Eğitim Amaçlıdır!"""

try:
    resp = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
    print(f"✅ Message sent! Status: {resp.status_code}")
    if resp.status_code == 200:
        result = resp.json()
        print(f"✓ message_id: {result.get('result', {}).get('message_id')}")
        print(f"✓ Chat ID: {chat_id}")
        print("\n📝 Message format verified!")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"❌ Error: {e}")
