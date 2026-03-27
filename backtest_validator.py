"""
Backtest Validator - Geçmiş veri üzerinde strateji test et
===========================================================
Tarihsel OHLCV verisi ile simülasyon yap, kazanç/kayıp hesapla
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)

class BacktestValidator:
    """Strateji backtest motoru"""
    
    def __init__(self, sembol, baslangic_bakiye=10000, komisyon=0.001):
        self.sembol = sembol
        self.baslangic_bakiye = baslangic_bakiye
        self.komisyon = komisyon  # 0.1%
        self.df = None
        
    def veri_çek_gunluk(self):
        """1 yıllık günlük veri çek (backtest için)"""
        try:
            ticker = yf.Ticker(self.sembol)
            self.df = ticker.history(period="1y", interval="1d")
            
            if self.df.empty:
                logger.warning(f"{self.sembol} veri bulunamadı")
                return False
            
            self.df.columns = ["Açılış", "Yüksek", "Düşük", "Kapanış", "Hacim", "Div", "Hisse Bölünme"]
            self.df = self.df.drop(columns=["Div", "Hisse Bölünme"], errors="ignore")
            self.df = self.df.reset_index()
            self.df = self.df.rename(columns={"Date": "Tarih"})
            return True
        except Exception as e:
            logger.error(f"{self.sembol} veri çekme hatası: {e}")
            return False
    
    def ma_sinyali(self):
        """MA sistemi sinyali (-1, 0, 1)"""
        k = self.df["Kapanış"]
        ma50 = k.rolling(50).mean()
        ma200 = k.rolling(200).mean()
        
        sinyaller = pd.Series(0, index=self.df.index, dtype=int)
        sinyaller[k > ma50] = 1
        sinyaller[(k < ma50) & (ma50 > ma200)] = 0
        sinyaller[k < ma50] = -1
        
        return sinyaller
    
    def rsi_sinyali(self, period=14, aşırı_satım=30, aşırı_alım=70):
        """RSI sinyali"""
        delta = self.df["Kapanış"].diff()
        kazan = delta.clip(lower=0)
        kayip = -delta.clip(upper=0)
        avg_k = kazan.ewm(com=period-1, min_periods=period).mean()
        avg_y = kayip.ewm(com=period-1, min_periods=period).mean()
        rs = avg_k / avg_y.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        sinyaller = pd.Series(0, index=self.df.index, dtype=int)
        sinyaller[rsi < aşırı_satım] = 1
        sinyaller[rsi > aşırı_alım] = -1
        
        return sinyaller
    
    def macd_sinyali(self, hızlı=12, yavas=26, signal=9):
        """MACD sinyali"""
        ema_h = self.df["Kapanış"].ewm(span=hızlı).mean()
        ema_y = self.df["Kapanış"].ewm(span=yavas).mean()
        macd = ema_h - ema_y
        signal_line = macd.ewm(span=signal).mean()
        
        sinyaller = pd.Series(0, index=self.df.index, dtype=int)
        sinyaller[macd > signal_line] = 1
        sinyaller[macd < signal_line] = -1
        
        return sinyaller
    
    def taraf_oyu(self):
        """Üçlü sinyalin oyu: MA, RSI, MACD"""
        sig_ma = self.ma_sinyali()
        sig_rsi = self.rsi_sinyali()
        sig_macd = self.macd_sinyali()
        
        # Toplam oy (3 indikatörden kaç tahlile )
        toplam = sig_ma + sig_rsi + sig_macd
        
        # Oy kuralı: 
        # - 2+ AL tarafı → AL
        # - 2+ SAT tarafı → SAT
        # - 1 AL, 1 SAT → NÖTR
        
        sinyaller = pd.Series("NÖTR", index=self.df.index, dtype=object)
        sinyaller[toplam >= 2] = "AL"
        sinyaller[toplam <= -2] = "SAT"
        
        return sinyaller
    
    def simülasyon(self, min_güven=2):
        """
        Backtest simülasyonu çalıştır
        min_güven: Kaç indikatör hemfikir olmalı (2 veya 3)
        """
        
        self.df["Sinyal"] = self.taraf_oyu()
        
        bakiye = self.baslangic_bakiye
        hisse_sayisi = 0
        giriş_fiyati = 0
        işlem_sayisi = 0
        kâr_kayıplar = []
        
        işlemler = []
        
        for i in range(len(self.df)):
            tarih = self.df.loc[i, "Tarih"]
            fiyat = float(self.df.loc[i, "Kapanış"])
            sinyal = self.df.loc[i, "Sinyal"]
            
            # AL sinyali
            if sinyal == "AL" and hisse_sayisi == 0 and bakiye > 0:
                hisse_sayisi = int(bakiye / fiyat * 0.95)  # 5% nakit yedek tut
                bakiye -= hisse_sayisi * fiyat * (1 + self.komisyon)
                giriş_fiyati = fiyat
                işlem_sayisi += 1
                işlemler.append({
                    "tarih": tarih,
                    "yönü": "AL",
                    "fiyat": fiyat,
                    "miktar": hisse_sayisi
                })
            
            # SAT sinyali
            elif sinyal == "SAT" and hisse_sayisi > 0:
                çıkış_fiyati = fiyat
                kâr_kayıp = hisse_sayisi * (çıkış_fiyati - giriş_fiyati) - (hisse_sayisi * çıkış_fiyati * self.komisyon)
                bakiye += hisse_sayisi * çıkış_fiyati * (1 - self.komisyon)
                kâr_kayıplar.append(kâr_kayıp)
                işlem_sayisi += 1
                işlemler.append({
                    "tarih": tarih,
                    "yönü": "SAT",
                    "fiyat": fiyat,
                    "miktar": hisse_sayisi,
                    "kâr_kayıp": kâr_kayıp
                })
                hisse_sayisi = 0
            
            # Zarar durdurma (stop loss %10)
            elif hisse_sayisi > 0 and fiyat < giriş_fiyati * 0.90:
                çıkış_fiyati = fiyat
                kâr_kayıp = hisse_sayisi * (çıkış_fiyati - giriş_fiyati) - (hisse_sayisi * çıkış_fiyati * self.komisyon)
                bakiye += hisse_sayisi * çıkış_fiyati * (1 - self.komisyon)
                kâr_kayıplar.append(kâr_kayıp)
                işlem_sayisi += 1
                işlemler.append({
                    "tarih": tarih,
                    "yönü": "STOP-LOSS",
                    "fiyat": fiyat,
                    "miktar": hisse_sayisi,
                    "kâr_kayıp": kâr_kayıp
                })
                hisse_sayisi = 0
        
        # Pozisyon açık bırakılmışsa kapat
        son_fiyat = float(self.df.iloc[-1]["Kapanış"])
        if hisse_sayisi > 0:
            kâr_kayıp = hisse_sayisi * (son_fiyat - giriş_fiyati)
            bakiye += hisse_sayisi * son_fiyat * (1 - self.komisyon)
            kâr_kayıplar.append(kâr_kayıp)
        
        # Metrikler
        toplam_kâr_kayıp = sum(kâr_kayıplar) if kâr_kayıplar else 0
        final_bakiye = bakiye
        getiri = ((final_bakiye - self.baslangic_bakiye) / self.baslangic_bakiye) * 100
        
        kazan_işlem = len([kk for kk in kâr_kayıplar if kk > 0])
        kaybeden_işlem = len([kk for kk in kâr_kayıplar if kk < 0])
        
        if kaybeden_işlem > 0:
            win_rate = (kazan_işlem / (kazan_işlem + kaybeden_işlem)) * 100
        else:
            win_rate = 100 if kazan_işlem > 0 else 0
        
        avg_kâr = np.mean([kk for kk in kâr_kayıplar if kk > 0]) if kazan_işlem > 0 else 0
        avg_kayıp = np.mean([kk for kk in kâr_kayıplar if kk < 0]) if kaybeden_işlem > 0 else 0
        
        # Sonuçlar
        sonuc = {
            "sembol": self.sembol,
            "dönem": "1 Yıl",
            "başlangıç_bakiye": self.baslangic_bakiye,
            "final_bakiye": round(final_bakiye, 2),
            "toplam_kâr_kayıp": round(toplam_kâr_kayıp, 2),
            "getiri_yüzdesi": round(getiri, 2),
            "işlem_sayısı": işlem_sayisi,
            "kazanan_işlem": kazan_işlem,
            "kaybeden_işlem": kaybeden_işlem,
            "win_rate": round(win_rate, 2),
            "ortalama_kâr": round(avg_kâr, 2),
            "ortalama_kayıp": round(avg_kayıp, 2),
            "profit_factor": round(abs(avg_kâr / avg_kayıp), 2) if avg_kayıp != 0 else 0,
        }
        
        return sonuc, işlemler


# ─────────────────────────────────────────────────────
# MAIN - TÜM BIST STOKLARINı TEST ET
# ─────────────────────────────────────────────────────

if __name__ == "__main__":
    from config.settings import load_settings
    
    logging.basicConfig(level=logging.INFO)
    
    settings = load_settings()
    hisseler = settings["symbols"]["bist"]
    
    print("\n" + "=" * 70)
    print("BACKTEST: BIST Hisseleri (1 Yıllık Tarihsel Veri)")
    print("=" * 70 + "\n")
    
    sonuçlar = []
    
    for sembol in hisseler:
        print(f"🔍 Backtest: {sembol}...")
        
        validator = BacktestValidator(sembol)
        if validator.veri_çek_gunluk():
            sonuc, işlemler = validator.simülasyon()
            sonuçlar.append(sonuc)
            
            print(f"  ✓ {sonuc['işlem_sayısı']} işlem")
            print(f"  ✓ Getiri: {sonuc['getiri_yüzdesi']}%")
            print(f"  ✓ Win Rate: {sonuc['win_rate']}%\n")
        else:
            print(f"  ✗ Veri çekme başarısız\n")
    
    # Özet rapor
    print("\n" + "=" * 70)
    print("BACKTEST SONUÇLARI (Sıralı - En Yüksek Getiri)")
    print("=" * 70 + "\n")
    
    sorted_sonuçlar = sorted(sonuçlar, key=lambda x: x['getiri_yüzdesi'], reverse=True)
    
    print(f"{'Sembol':<12} {'Getiri%':<12} {'Win Rate':<12} {'İşlem':<8} {'Profit Factor':<15}")
    print("-" * 70)
    
    for s in sorted_sonuçlar:
        print(f"{s['sembol']:<12} {s['getiri_yüzdesi']:>10}% {s['win_rate']:>10}% {s['işlem_sayısı']:>7} {s['profit_factor']:>14}")
    
    # JSON olarak kaydet
    rapor = {
        "tarih": datetime.now().isoformat(),
        "toplam_hisse": len(sonuçlar),
        "ortalama_getiri": round(np.mean([s['getiri_yüzdesi'] for s in sonuçlar]), 2),
        "en_yüksek_getiri": max([s['getiri_yüzdesi'] for s in sonuçlar]),
        "en_düşük_getiri": min([s['getiri_yüzdesi'] for s in sonuçlar]),
        "detaylar": sorted_sonuçlar
    }
    
    rapor_path = Path("data/signals") / f"backtest_rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    rapor_path.parent.mkdir(exist_ok=True)
    
    with open(rapor_path, 'w', encoding='utf-8') as f:
        json.dump(rapor, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Backtest raporu kaydedildi: {rapor_path}")
    print("=" * 70 + "\n")
