"""
🎯 PRODUCTION BOT - GERÇEk BIST VERİ + MOCK BAKİYE
═══════════════════════════════════════════════════════════════════
Pazartesi 10:00 - Her saat:
1. Gerçek BIST 100 hisseleri analiz et
2. Gerçek sinyalleri hesapla (TEST_MODE=0)
3. Telegram'a gönder
4. Mock 10000 TL ile AL-SAT yap
5. 1 hafta takip et
"""

import os
os.environ['TEST_MODE'] = '0'  # CANLIDA - Gerçek veri + fallback

import sys
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import requests

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"bot_prod_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

try:
    from realtime_analyzer import RealTimeAnalyzer
    from config.settings import load_settings
except ImportError as e:
    logger.error(f"Import hatası: {e}")
    sys.exit(1)

# BIST 100 - Top aktif hisseler (en çok trading hacmi)
BIST100_AKTIF = [
    "GARAN", "AKBNK", "YKBNK", "HALKB", "TBANK",
    "SAHOL", "KCHOL", "THYAO", "EREGL", "ASELS",
    "AEFES", "SISE", "TOASO", "BIMAS", "CCOLA",
    "PEGASUS", "AKSA", "VESTL", "SKBNK", "MAVI"
]

class ProductionBotProd:
    """Production Bot - Gerçek BIST Verisi (+ fallback mock)"""
    
    def __init__(self):
        self.settings = load_settings()
        self.hisseler = BIST100_AKTIF  # İlk 20 aktif hisse (yfinance destekli)
        
        self.telegram_enabled = self.settings["telegram"].get("enabled", False)
        self.telegram_token = self.settings["telegram"].get("bot_token")
        self.telegram_chat_id = self.settings["telegram"].get("chat_id")
        
        self.son_rapor_saati = datetime.now().hour - 1
        
        logger.info("🤖 PRODUCTION BOT BAŞLATILDI")
        logger.info(f"   Hisseler: {len(self.hisseler)} (Aktif BIST 100)")
        logger.info(f"   Telegram: {'✓' if self.telegram_enabled else '✗'}")
        logger.info(f"   Veri Modu: GERÇEK (yfinance) + Fallback (mock)")
    
    def _telegram_post(self, metin):
        if not self.telegram_enabled:
            return False
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            response = requests.post(
                url,
                json={"chat_id": self.telegram_chat_id, "text": metin},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def hourly_rapor(self):
        """Saatlik rapor - Gerçek hisseler + Mock bakiye
        (Borsa kontrol main döngüde yapılıyor)"""
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 BIST 100 SAATLİK RAPOR")
        logger.info(f"{'='*70}")
        
        guclu_al = []
        zayif_al = []
        zayif_sat = []
        notr = []
        
        veri_kaynagi = {'gercek': 0, 'mock': 0}
        
        # Hisseleri analiz et
        for idx, sembol in enumerate(self.hisseler, 1):
            try:
                logger.debug(f"[{idx:2}/{len(self.hisseler)}] {sembol} analiz ediliyor...")
                
                analyzer = RealTimeAnalyzer(sembol, period="1mo", interval="5m")
                
                # Veri çek
                if not analyzer.veri_çek():
                    logger.warning(f"   ✗ {sembol}: Veri çekme başarısız")
                    continue
                
                # Veri kaynağı kontrol et
                if analyzer.df is not None:
                    veri_kaynagi['gercek'] += 1  # Basit kontrol
                
                # Analiz yap
                sinyal = analyzer.tamAnaliz()
                
                if not sinyal:
                    logger.debug(f"   ? {sembol}: Sinyal yok")
                    continue
                
                fiyat = analyzer.df['Kapanış'].iloc[-1]
                güven = sinyal.güven_yüzdesi
                tip = sinyal.sinyal_seviyesi
                
                # Kategorize et
                if tip == "AL":
                    if güven >= 47:
                        guclu_al.append({
                            'sembol': sembol,
                            'güven': güven,
                            'fiyat': fiyat,
                            'tp': fiyat * 1.15,
                            'sl': fiyat * 0.95,
                            'trend': 'Short-term',
                            'işlem_türü': 'Swing AL',
                            'volatilite': 'Değişken',
                            'sebep': f'Teknik sinyal ({güven:.0f}%)'
                        })
                    else:
                        zayif_al.append({'sembol': sembol, 'güven': güven})
                
                elif tip == "SAT":
                    if güven >= 40:
                        zayif_sat.append({'sembol': sembol, 'güven': güven})
                
                elif tip == "NÖTR":
                    notr.append({'sembol': sembol, 'güven': güven})
                
                logger.debug(f"   ✓ {sembol}: {tip:6} ({güven:.0f}%)")
            
            except Exception as e:
                logger.error(f"   ✗ {sembol}: {str(e)[:40]}")
                continue
        
        # Rapor oluştur
        rapor = f"""📊 BIST 100 SAATLİK RAPOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ {datetime.now().strftime('%H:%M:%S')} | 📅 {datetime.now().strftime('%d.%m.%Y')}
💰 Mock Bakiye: 10.000₺

🎯 GÜÇLÜ AL ({len(guclu_al)} sinyal - 47%+)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        # GÜÇLÜ AL sinyalleri
        if guclu_al:
            for idx, sig in enumerate(sorted(guclu_al, key=lambda x: x['güven'], reverse=True), 1):
                kar_pct = ((sig['tp'] - sig['fiyat']) / sig['fiyat']) * 100
                risk_pct = ((sig['fiyat'] - sig['sl']) / sig['fiyat']) * 100
                oran = (sig['tp'] - sig['fiyat']) / (sig['fiyat'] - sig['sl'])
                
                rapor += f"\n\n#{idx}. {sig['sembol']} | {int(sig['güven'])}%"
                rapor += f"\n💹 Giriş: {sig['fiyat']:.2f}₺ | 📈 TP: {sig['tp']:.2f}₺ (+{kar_pct:.1f}%)"
                rapor += f"\n🛑 SL: {sig['sl']:.2f}₺ (-{risk_pct:.1f}%) | R/R: {oran:.2f}:1"
                rapor += f"\n📊 {sig['sebep']}"
        else:
            rapor += "\n\n(Şu an GÜÇLÜ AL sinyali yok)"
        
        # DİĞER FİRSATLAR
        rapor += f"\n\n📋 DİĞER FİRSATLAR"
        rapor += "\n" + "─" * 50
        
        if zayif_al:
            rapor += f"\n📈 Zayıf AL ({len(zayif_al)}): " + ", ".join([f"{s['sembol']}" for s in zayif_al[:5]])
        
        if zayif_sat:
            rapor += f"\n📉 Zayıf SAT ({len(zayif_sat)}): " + ", ".join([f"{s['sembol']}" for s in zayif_sat[:5]])
        
        if notr:
            rapor += f"\n⏸️  NÖTR ({len(notr)}): " + ", ".join([f"{s['sembol']}" for s in notr[:5]])
        
        rapor += f"\n\n{'═'*50}\n✓ Analiz: {datetime.now().strftime('%H:%M')}"
        rapor += f"\n📲 AL sinyallerini takip et!"
        
        # Gönder
        self._telegram_post(rapor)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✓ Rapor Gönderildi")
        logger.info(f"   🎯 GÜÇLÜ AL: {len(guclu_al)}")
        logger.info(f"   📈 Zayıf AL: {len(zayif_al)}")
        logger.info(f"   📉 Zayıf SAT: {len(zayif_sat)}")
        logger.info(f"   ⏸️  NÖTR: {len(notr)}")
        logger.info(f"\n{rapor[:400]}...\n")
        logger.info(f"{'='*70}\n")


if __name__ == "__main__":
    bot = ProductionBotProd()
    
    logger.info(f"\n{'='*70}")
    logger.info(f"🚀 BIST BOT BAŞLADI - HAFTA BOYUNCA ÇALIŞACAK")
    logger.info(f"📅 Pazartesi-Cuma | ⏰ 10:00-18:00")
    logger.info(f"{'='*70}\n")
    
    last_hour = -1
    while True:
        try:
            now = datetime.now()
            hour = now.hour
            minute = now.minute
            weekday = now.weekday()  # 0=Pazartesi, 4=Cuma, 5+=Weekend
            
            # Borsa açık saatleri: Pazartesi(0)-Cuma(4), 10:00-18:00
            if weekday < 5 and 10 <= hour < 18:
                # Her saat başında (10:00, 11:00, ..., 17:00) rapor gönder
                if hour != last_hour and minute < 2:  # İlk 2 dakikada rapor yap
                    logger.info(f"\n⏰ {hour}:00 - Saatlik rapor hazırlanıyor...")
                    bot.hourly_rapor()
                    last_hour = hour
            else:
                # Borsa dışı saatler - status mesajı
                status = ""
                if hour < 10 and weekday < 5:
                    status = f"🌙 Sabah {hour:02d}:00 - Bot uyuyor (Haftaiçi 10:00'da başlayacak)"
                elif hour >= 18 and weekday < 5:
                    status = f"🚪 Akşam {hour:02d}:00 - Borsa kapandı (Yarın 10:00'da tekrar)"
                elif weekday >= 5:
                    status = f"🏁 Weekend - Bot duraklı (Pazartesi 10:00'da başlayacak)"
                
                if status and hour != last_hour:
                    logger.info(status)
                    last_hour = hour
            
            # Her dakika kontrol et
            time.sleep(60)
        
        except KeyboardInterrupt:
            logger.info(f"\n{'='*70}")
            logger.info(f"⛔ BOT DURDURULDU - Kullanıcı tarafından kapatıldı")
            logger.info(f"{'='*70}\n")
            break
        
        except Exception as e:
            logger.error(f"❌ Hata: {str(e)}")
            time.sleep(60)
