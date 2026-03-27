"""
Production Bot Test - 2 dakika çalış
Ctrl+C ile kapat
"""

import sys
sys.path.insert(0, '.')

from run_production import ProductionBot
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

bot = ProductionBot()

# Periyotu test için 1 dakikaya düşür
bot.periyot_dakika = 1

print(f"""
╔════════════════════════════════════════╗
║   PRODUCTION BOT TEST (2 dakika)      ║
╚════════════════════════════════════════╝

📊 Takip edilecek hisseler: {len(bot.hisseler)}
⏱️  Periyot: {bot.periyot_dakika} dakika
📱 Telegram: {'✓ Aktif' if bot.telegramaktif else '✗ Kapalı'}

Başlangıç: 2 işlem yapılacak (2 dakika)
Çıkış: Ctrl+C tuşlab verin
""")

input("Başlamak için Enter'a basınız...")

try:
    # Max 2 döngü için
    for döngü in range(2):
        print(f"\n--- DÖNGÜ {döngü+1}/2 ---")
        
        # Kısaltılmış analiz (sadece ilk 3 hisse)
        for sembol in bot.hisseler[:3]:
            from realtime_analyzer import RealTimeAnalyzer
            
            try:
                analyzer = RealTimeAnalyzer(sembol, period="1mo", interval="5m")
                sinyal = analyzer.tamAnaliz()
                
                if sinyal:
                    print(f"  {sinyal.sembol}: {sinyal.sinyal_seviyesi} ({sinyal.güven_yüzdesi}%)")
            except Exception as e:
                print(f"  {sembol}: Hata - {str(e)[:30]}")
        
        if döngü < 1:  # Son döngü değilse beklе
            print(f"\n⏳ {bot.periyot_dakika} dakika bekleniyor...")
            time.sleep(bot.periyot_dakika * 60)

except KeyboardInterrupt:
    print("\n\n⛔ Test durduruldu (Ctrl+C)")

print("\n✅ Test tamamlandı!")
