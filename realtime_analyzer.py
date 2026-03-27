"""
Real-Time BIST Trading Bot - Geliştirilmiş Analiz Motoru
========================================================
- Veri güncelleme: Her 5 dakikada bir
- Indikatör ağırlıklandırması: Kat sayılar ile
- 10+ teknik indikatör + haber sentiment
- Ağırlıklı skor sistemi (normalize)
- Saatlik Telegram özeti (top 5 sinyal)
"""

import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from threading import Thread
import requests

try:
    import yfinance as yf
except ImportError:
    print("pip install yfinance pandas numpy requests")
    exit(1)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/realtime_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────
# İNDİKATÖR AĞIRLIKLARI (Kat Sayılar)
# ─────────────────────────────────────────────────────

INDIKATÖR_AĞIRLIKLARI = {
    "MA_Sistemi":      2.0,    # Trend yönü en kritik
    "RSI":             1.5,    # Momentum
    "MACD":            1.5,    # Trend momentum
    "ADX":             1.3,    # Trend gücü
    "ATR":             1.2,    # Volatilite
    "Bollinger":       1.0,    # Aşırı hareket
    "Stochastic":      1.0,    # K/D çizgileri
    "CCI":             0.9,    # Cyclic indicator
    "Hacim":           0.8,    # Hacim analizi
    "Williams_R":      1.0,    # Momentum 2
    "Haber_Sentiment": 1.5,    # KAP + haber NLP
}

TOPLAM_AGIRLIK = sum(INDIKATÖR_AĞIRLIKLARI.values())

# Skor thresholdları
SKOR_THRESHOLDS = {
    "GÜÇLÜ_AL":    0.50,      # +0.50 ve üstü
    "ZAYIF_AL":    0.20,      # +0.20 ile +0.50
    "NÖTR":        0.20 - (-0.20),  # -0.20 ile +0.20
    "ZAYIF_SAT":  -0.20,      # -0.50 ile -0.20
    "GÜÇLÜ_SAT":  -0.50,      # -0.50 ve altı
}

# ─────────────────────────────────────────────────────
# SİNYAL SINIFLARI
# ─────────────────────────────────────────────────────

class IndikatorSignal:
    """Tek indikatörün sonucu"""
    def __init__(self, ad, deger, sinyal, aciklama, agirlik):
        self.ad = ad
        self.deger = round(deger, 4)
        self.sinyal = sinyal  # "AL", "SAT", "NÖTR"
        self.aciklama = aciklama
        self.agirlik = agirlik
        
    @property
    def skor(self):
        """Ağırlıklandırılmış skor (-1 ile +1 arası)"""
        sinyal_map = {"AL": 1, "NÖTR": 0, "SAT": -1}
        return sinyal_map.get(self.sinyal, 0) * self.agirlik


class TradingSignal:
    """Hisse için final sinyal"""
    def __init__(self, sembol, indikatörler, zaman):
        self.sembol = sembol
        self.indikatörler = indikatörler  # IndikatorSignal listesi
        self.zaman = zaman
        self.fiyat = None
        self.stop_loss = None
        self.hedef = None
        
    @property
    def ağırlıklı_skor(self):
        """Tüm indikatörlerin ağırlıklı ortalaması"""
        toplam = sum(ind.skor for ind in self.indikatörler)
        return round(toplam / TOPLAM_AGIRLIK, 3)
    
    @property
    def sinyal_seviyesi(self):
        """Final sinyal"""
        skor = self.ağırlıklı_skor
        if skor >= SKOR_THRESHOLDS["GÜÇLÜ_AL"]:
            return "GÜÇLÜ AL"
        elif skor >= SKOR_THRESHOLDS["ZAYIF_AL"]:
            return "ZAYIF AL"
        elif skor <= -SKOR_THRESHOLDS["GÜÇLÜ_AL"]:
            return "GÜÇLÜ SAT"
        elif skor <= -SKOR_THRESHOLDS["ZAYIF_AL"]:
            return "ZAYIF SAT"
        else:
            return "NÖTR"
    
    @property
    def güven_yüzdesi(self):
        """Sinyal güven seviyesi (%)"""
        return round(abs(self.ağırlıklı_skor) * 100, 1)


# ─────────────────────────────────────────────────────
# İNDİKATÖR HESAPLAMA MOTORU
# ─────────────────────────────────────────────────────

class RealTimeAnalyzer:
    """Real-time BIST analiz motoru"""
    
    def __init__(self, sembol, period="1mo", interval="5m"):
        self.sembol = sembol
        self.period = period
        self.interval = interval
        self.df = None
        self.son_sinyaller = {}  # {sembol: TradingSignal}
        
    def veri_çek(self):
        """Son 1 ay veriyi 5 dakikalık barlarla çek"""
        try:
            ticker = yf.Ticker(self.sembol)
            self.df = ticker.history(period=self.period, interval=self.interval)
            
            if self.df.empty:
                logger.warning(f"{self.sembol} veri bulunamadı")
                return False
            
            # Sütun adlarını Türkçeleştir
            self.df.columns = ["Açılış", "Yüksek", "Düşük", "Kapanış", "Hacim", "Div", "Hisse Bölünme"]
            self.df = self.df.drop(columns=["Div", "Hisse Bölünme"], errors="ignore")
            return True
        except Exception as e:
            logger.error(f"{self.sembol} veri çekme hatası: {e}")
            return False
    
    # ─── MA Sistemi ───
    def ma_sinyal(self):
        """MA7, MA21, MA50, MA200 analizi"""
        if len(self.df) < 200:
            return IndikatorSignal("MA_Sistemi", 0, "NÖTR", "Yetersiz veri", INDIKATÖR_AĞIRLIKLARI["MA_Sistemi"])
        
        k = self.df["Kapanış"]
        ma7 = k.rolling(7).mean()
        ma21 = k.rolling(21).mean()
        ma50 = k.rolling(50).mean()
        ma200 = k.rolling(200).mean()
        
        son_fiyat = float(k.iloc[-1])
        v7, v21, v50, v200 = float(ma7.iloc[-1]), float(ma21.iloc[-1]), float(ma50.iloc[-1]), float(ma200.iloc[-1])
        
        # Golden Cross
        gc_simdi = ma50.iloc[-1] > ma200.iloc[-1]
        gc_once = ma50.iloc[-2] > ma200.iloc[-2]
        
        if gc_simdi and not gc_once:
            return IndikatorSignal("MA_Sistemi", son_fiyat, "AL", "GOLDEN CROSS!", INDIKATÖR_AĞIRLIKLARI["MA_Sistemi"])
        elif not gc_simdi and gc_once:
            return IndikatorSignal("MA_Sistemi", son_fiyat, "SAT", "DEATH CROSS!", INDIKATÖR_AĞIRLIKLARI["MA_Sistemi"])
        elif son_fiyat > v7 > v21 > v50:
            return IndikatorSignal("MA_Sistemi", son_fiyat, "AL", "Fiyat tüm MA'ların üstünde", INDIKATÖR_AĞIRLIKLARI["MA_Sistemi"])
        elif son_fiyat < v7 < v21 < v50:
            return IndikatorSignal("MA_Sistemi", son_fiyat, "SAT", "Fiyat tüm MA'ların altında", INDIKATÖR_AĞIRLIKLARI["MA_Sistemi"])
        elif son_fiyat > v50:
            return IndikatorSignal("MA_Sistemi", son_fiyat, "AL", "Fiyat MA50 üstünde", INDIKATÖR_AĞIRLIKLARI["MA_Sistemi"])
        elif son_fiyat < v50:
            return IndikatorSignal("MA_Sistemi", son_fiyat, "SAT", "Fiyat MA50 altında", INDIKATÖR_AĞIRLIKLARI["MA_Sistemi"])
        else:
            return IndikatorSignal("MA_Sistemi", son_fiyat, "NÖTR", "MA sistemi karışık", INDIKATÖR_AĞIRLIKLARI["MA_Sistemi"])
    
    # ─── RSI ───
    def rsi_sinyal(self, period=14, aşırı_satım=30, aşırı_alım=70):
        """RSI hesapla ve sinyal üret"""
        delta = self.df["Kapanış"].diff()
        kazan = delta.clip(lower=0)
        kayip = -delta.clip(upper=0)
        avg_k = kazan.ewm(com=period-1, min_periods=period).mean()
        avg_y = kayip.ewm(com=period-1, min_periods=period).mean()
        rs = avg_k / avg_y.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        rsi_val = float(rsi.iloc[-1])
        
        if rsi_val < aşırı_satım:
            return IndikatorSignal("RSI", rsi_val, "AL", f"Aşırı satım ({rsi_val:.1f})", INDIKATÖR_AĞIRLIKLARI["RSI"])
        elif rsi_val > aşırı_alım:
            return IndikatorSignal("RSI", rsi_val, "SAT", f"Aşırı alım ({rsi_val:.1f})", INDIKATÖR_AĞIRLIKLARI["RSI"])
        else:
            return IndikatorSignal("RSI", rsi_val, "NÖTR", f"RSI nötr ({rsi_val:.1f})", INDIKATÖR_AĞIRLIKLARI["RSI"])
    
    # ─── MACD ───
    def macd_sinyal(self, hızlı=12, yavas=26, signal=9):
        """MACD analizi"""
        ema_h = self.df["Kapanış"].ewm(span=hızlı).mean()
        ema_y = self.df["Kapanış"].ewm(span=yavas).mean()
        macd = ema_h - ema_y
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        m_val = float(macd.iloc[-1])
        hist_val = float(histogram.iloc[-1])
        
        if macd.iloc[-1] > signal_line.iloc[-1] and macd.iloc[-2] <= signal_line.iloc[-2]:
            return IndikatorSignal("MACD", hist_val, "AL", "MACD Signal Crossover", INDIKATÖR_AĞIRLIKLARI["MACD"])
        elif macd.iloc[-1] < signal_line.iloc[-1] and macd.iloc[-2] >= signal_line.iloc[-2]:
            return IndikatorSignal("MACD", hist_val, "SAT", "MACD Death Crossover", INDIKATÖR_AĞIRLIKLARI["MACD"])
        elif hist_val > 0:
            return IndikatorSignal("MACD", hist_val, "AL", "Histogram pozitif", INDIKATÖR_AĞIRLIKLARI["MACD"])
        elif hist_val < 0:
            return IndikatorSignal("MACD", hist_val, "SAT", "Histogram negatif", INDIKATÖR_AĞIRLIKLARI["MACD"])
        else:
            return IndikatorSignal("MACD", hist_val, "NÖTR", "MACD nötr", INDIKATÖR_AĞIRLIKLARI["MACD"])
    
    # ─── ADX (Trend Gücü) ───
    def adx_sinyal(self, period=14):
        """ADX trend gücü analizi"""
        h = self.df["Yüksek"]
        l = self.df["Düşük"]
        c = self.df["Kapanış"]
        
        plus_dm = h.diff()
        minus_dm = -l.diff()
        plus_dm = plus_dm.clip(lower=0)
        minus_dm = minus_dm.clip(lower=0)
        
        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        adx_val = float(adx.iloc[-1])
        
        if adx_val > 40:
            sinyal = "AL" if plus_di.iloc[-1] > minus_di.iloc[-1] else "SAT"
            return IndikatorSignal("ADX", adx_val, sinyal, f"Güçlü trend ({adx_val:.1f})", INDIKATÖR_AĞIRLIKLARI["ADX"])
        elif adx_val > 20:
            sinyal = "AL" if plus_di.iloc[-1] > minus_di.iloc[-1] else "SAT"
            return IndikatorSignal("ADX", adx_val, sinyal, f"Orta trend ({adx_val:.1f})", INDIKATÖR_AĞIRLIKLARI["ADX"])
        else:
            return IndikatorSignal("ADX", adx_val, "NÖTR", f"Trend zayıf ({adx_val:.1f})", INDIKATÖR_AĞIRLIKLARI["ADX"])
    
    # ─── ATR (Volatilite) ───
    def atr_sinyal(self, period=14):
        """ATR volatilite analizi"""
        h = self.df["Yüksek"]
        l = self.df["Düşük"]
        c = self.df["Kapanış"]
        
        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        atr_val = float(atr.iloc[-1])
        
        atr_pct = (atr_val / float(c.iloc[-1])) * 100
        
        if atr_pct > 2.0:
            return IndikatorSignal("ATR", atr_val, "SAT", f"Yüksek volatilite ({atr_pct:.2f}%)", INDIKATÖR_AĞIRLIKLARI["ATR"])
        elif atr_pct < 0.5:
            return IndikatorSignal("ATR", atr_val, "AL", f"Düşük volatilite ({atr_pct:.2f}%)", INDIKATÖR_AĞIRLIKLARI["ATR"])
        else:
            return IndikatorSignal("ATR", atr_val, "NÖTR", f"Normal volatilite ({atr_pct:.2f}%)", INDIKATÖR_AĞIRLIKLARI["ATR"])
    
    # ─── Bollinger Bantları ───
    def bollinger_sinyal(self, period=20, std_mult=2.0):
        """Bollinger Bands"""
        orta = self.df["Kapanış"].rolling(period).mean()
        std = self.df["Kapanış"].rolling(period).std()
        ust = orta + std_mult * std
        alt = orta - std_mult * std
        
        son_fiyat = float(self.df["Kapanış"].iloc[-1])
        pct_b = (son_fiyat - float(alt.iloc[-1])) / (float(ust.iloc[-1]) - float(alt.iloc[-1]))
        
        if pct_b < 0.2:
            return IndikatorSignal("Bollinger", pct_b, "AL", "Alt banta yakın", INDIKATÖR_AĞIRLIKLARI["Bollinger"])
        elif pct_b > 0.8:
            return IndikatorSignal("Bollinger", pct_b, "SAT", "Üst banta yakın", INDIKATÖR_AĞIRLIKLARI["Bollinger"])
        else:
            return IndikatorSignal("Bollinger", pct_b, "NÖTR", "Bant içinde", INDIKATÖR_AĞIRLIKLARI["Bollinger"])
    
    # ─── Stochastic ───
    def stochastic_sinyal(self, k_period=14, d_period=3):
        """Stochastic Oscillator"""
        low_min = self.df["Düşük"].rolling(k_period).min()
        high_max = self.df["Yüksek"].rolling(k_period).max()
        k_line = 100 * (self.df["Kapanış"] - low_min) / (high_max - low_min)
        d_line = k_line.rolling(d_period).mean()
        
        k_val = float(k_line.iloc[-1])
        
        if k_val < 20:
            return IndikatorSignal("Stochastic", k_val, "AL", "Aşırı satım", INDIKATÖR_AĞIRLIKLARI["Stochastic"])
        elif k_val > 80:
            return IndikatorSignal("Stochastic", k_val, "SAT", "Aşırı alım", INDIKATÖR_AĞIRLIKLARI["Stochastic"])
        else:
            return IndikatorSignal("Stochastic", k_val, "NÖTR", "Nötr bölge", INDIKATÖR_AĞIRLIKLARI["Stochastic"])
    
    # ─── CCI (Commodity Channel Index) ───
    def cci_sinyal(self, period=20):
        """CCI analizi"""
        tp = (self.df["Yüksek"] + self.df["Düşük"] + self.df["Kapanış"]) / 3
        sma = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        cci = (tp - sma) / (0.015 * mad)
        
        cci_val = float(cci.iloc[-1])
        
        if cci_val > 100:
            return IndikatorSignal("CCI", cci_val, "SAT", "Aşırı alım", INDIKATÖR_AĞIRLIKLARI["CCI"])
        elif cci_val < -100:
            return IndikatorSignal("CCI", cci_val, "AL", "Aşırı satım", INDIKATÖR_AĞIRLIKLARI["CCI"])
        else:
            return IndikatorSignal("CCI", cci_val, "NÖTR", "Nötr", INDIKATÖR_AĞIRLIKLARI["CCI"])
    
    # ─── Hacim Analizi ───
    def hacim_sinyal(self, period=20):
        """Hacim analizi"""
        ort_hacim = self.df["Hacim"].rolling(period).mean()
        son_hacim = float(self.df["Hacim"].iloc[-1])
        ort_val = float(ort_hacim.iloc[-1])
        orani = son_hacim / ort_val if ort_val > 0 else 1.0
        
        sonFiyat_degisim = float(self.df["Kapanış"].iloc[-1]) - float(self.df["Kapanış"].iloc[-2])
        
        if orani > 1.5 and sonFiyat_degisim > 0:
            return IndikatorSignal("Hacim", orani, "AL", "Yüksek hacimli yükseliş", INDIKATÖR_AĞIRLIKLARI["Hacim"])
        elif orani > 1.5 and sonFiyat_degisim < 0:
            return IndikatorSignal("Hacim", orani, "SAT", "Yüksek hacimli düşüş", INDIKATÖR_AĞIRLIKLARI["Hacim"])
        else:
            return IndikatorSignal("Hacim", orani, "NÖTR", "Normal hacim", INDIKATÖR_AĞIRLIKLARI["Hacim"])
    
    # ─── Williams %R ───
    def williams_r_sinyal(self, period=14):
        """Williams %R momentum"""
        high_max = self.df["Yüksek"].rolling(period).max()
        low_min = self.df["Düşük"].rolling(period).min()
        wr = -100 * (high_max - self.df["Kapanış"]) / (high_max - low_min)
        
        wr_val = float(wr.iloc[-1])
        
        if wr_val < -80:
            return IndikatorSignal("Williams_R", wr_val, "AL", "Aşırı satım", INDIKATÖR_AĞIRLIKLARI["Williams_R"])
        elif wr_val > -20:
            return IndikatorSignal("Williams_R", wr_val, "SAT", "Aşırı alım", INDIKATÖR_AĞIRLIKLARI["Williams_R"])
        else:
            return IndikatorSignal("Williams_R", wr_val, "NÖTR", "Nötr", INDIKATÖR_AĞIRLIKLARI["Williams_R"])
    
    # ─── Haber Sentiment (Placeholder) ───
    def haber_sentiment_sinyal(self):
        """KAP haber analizi (placeholder - sonra NLP eklenecek)"""
        # TODO: KAP API + NLP sentiment analizi
        return IndikatorSignal("Haber_Sentiment", 0, "NÖTR", "Haber verisi bekleniyor", INDIKATÖR_AĞIRLIKLARI["Haber_Sentiment"])
    
    # ─── TAM ANALİZ ───
    def tamAnaliz(self):
        """Tüm indikatörleri hesapla ve final sinyal üret"""
        if not self.veri_çek():
            return None
        
        indikatörler = [
            self.ma_sinyal(),
            self.rsi_sinyal(),
            self.macd_sinyal(),
            self.adx_sinyal(),
            self.atr_sinyal(),
            self.bollinger_sinyal(),
            self.stochastic_sinyal(),
            self.cci_sinyal(),
            self.hacim_sinyal(),
            self.williams_r_sinyal(),
            self.haber_sentiment_sinyal(),
        ]
        
        signal = TradingSignal(self.sembol, indikatörler, datetime.now())
        signal.fiyat = float(self.df["Kapanış"].iloc[-1])
        
        # ATR hesapla
        h = self.df["Yüksek"]
        l = self.df["Düşük"]
        c = self.df["Kapanış"]
        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        atr_val = float(atr.iloc[-1])
        
        signal.stop_loss = round(signal.fiyat - 1.5 * atr_val, 2)
        signal.hedef = round(signal.fiyat + 2.0 * atr_val, 2)
        
        return signal


# ─────────────────────────────────────────────────────
# REAL-TIME MONITOR
# ─────────────────────────────────────────────────────

class RealTimeMonitor:
    """Real-time veri takibi ve sinyal bildirimi"""
    
    def __init__(self, hisseler, periyot_dakika=5, telegram_token=None, telegram_chatid=None):
        self.hisseler = hisseler
        self.periyot_saniye = periyot_dakika * 60
        self.telegram_token = telegram_token
        self.telegram_chatid = telegram_chatid
        self.sinyaller_saati = {}  # Saatlik sinyalleri sakla
        self.son_ozet_saat = datetime.now().hour
        
    def sinyal_gönder_telegram(self, sinyal):
        """Yeni sinyal Telegram'a gönder"""
        if not self.telegram_token or not self.telegram_chatid:
            return
        
        mesaj = f"""
🔔 YENİ SİNYAL - {sinyal.sembol}
══════════════════════════════
📊 Fiyat: {sinyal.fiyat:.2f} TL
📈 Sinyal: {sinyal.sinyal_seviyesi}
🎯 Güven: {sinyal.güven_yüzdesi}%
🔴 Stop: {sinyal.stop_loss:.2f}
🟢 Hedef: {sinyal.hedef:.2f}
⏰ Saat: {sinyal.zaman.strftime('%H:%M:%S')}
"""
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            requests.post(url, json={
                "chat_id": self.telegram_chatid,
                "text": mesaj
            }, timeout=5)
        except:
            pass
    
    def saatlik_ozet_gönder(self):
        """Saatlik özet (top 5 sinyal)"""
        if not self.telegram_token or not self.telegram_chatid:
            return
        
        if not self.sinyaller_saati:
            return
        
        # En yüksek güven sinyallerini al
        sorted_sinyaller = sorted(
            self.sinyaller_saati.values(),
            key=lambda x: x.güven_yüzdesi,
            reverse=True
        )[:5]
        
        mesaj = "📊 SAATLİK ÖZETİ\n" + "=" * 40 + "\n"
        for i, sig in enumerate(sorted_sinyaller, 1):
            mesaj += f"{i}) {sig.sembol} | {sig.sinyal_seviyesi} | {sig.güven_yüzdesi}% | {sig.fiyat:.2f}₺\n"
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            requests.post(url, json={
                "chat_id": self.telegram_chatid,
                "text": mesaj
            }, timeout=5)
        except:
            pass
        
        self.sinyaller_saati = {}
    
    def izle(self):
        """Main loop"""
        logger.info("Real-time monitor başladı")
        
        while True:
            try:
                zaman = datetime.now()
                logger.info(f"Analiz döngüsü: {zaman}")
                
                for sembol in self.hisseler:
                    analyzer = RealTimeAnalyzer(sembol)
                    sinyal = analyzer.tamAnaliz()
                    
                    if sinyal:
                        logger.info(f"{sembol}: {sinyal.sinyal_seviyesi} | Güven: {sinyal.güven_yüzdesi}%")
                        
                        # Saatlik özete ekle
                        self.sinyaller_saati[sembol] = sinyal
                        
                        # Güçlü sinyalleri hemen gönder
                        if sinyal.güven_yüzdesi > 70:
                            self.sinyal_gönder_telegram(sinyal)
                
                # Saatte bir özet gönder
                if zaman.hour != self.son_ozet_saat:
                    self.saatlik_ozet_gönder()
                    self.son_ozet_saat = zaman.hour
                
                # Periyot kadar bekle
                logger.info(f"{self.periyot_saniye} saniye bekleniyor...")
                time.sleep(self.periyot_saniye)
                
            except KeyboardInterrupt:
                logger.info("Monitor durduruldu")
                break
            except Exception as e:
                logger.error(f"Monitor hatası: {e}")
                time.sleep(self.periyot_saniye)


# ─────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────

if __name__ == "__main__":
    from config.settings import load_settings
    
    settings = load_settings()
    hisseler = settings["symbols"]["bist"]
    
    telegram_cfg = settings.get("telegram", {})
    token = telegram_cfg.get("bot_token", "")
    chat_id = telegram_cfg.get("chat_id", "")
    
    monitor = RealTimeMonitor(
        hisseler=hisseler if hisseler else ["THYAO.IS", "EREGL.IS", "GARAN.IS"],
        periyot_dakika=5,
        telegram_token=token if telegram_cfg.get("enabled") else None,
        telegram_chatid=chat_id if telegram_cfg.get("enabled") else None
    )
    
    monitor.izle()
