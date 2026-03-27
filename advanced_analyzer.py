"""
Advanced BIST Trading Bot Analyzer
===================================
- 11 Teknik İndikatör (EXISTING)
- + Haber Sentiment (KAP trending)
- + Risk/Volatilite Faktörü
- + Güven Seviyesi (Multi-factor confidence)
- + Piyasa Durumu Analizi
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import yfinance as yf
import requests

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# ADVANCED CONFIDENCE SCORING
# ═══════════════════════════════════════════════════════════════

class AdvancedConfidenceScore:
    """Geliştirilmiş güven skoru hesaplayıcı"""
    
    def __init__(self, base_score, indikatör_sayısı_hemfikir, risk_faktörü, 
                 hacim_teyidi, haber_sentiment, piyasa_trend):
        self.base_score = base_score  # -1 ile 1
        self.indikatör_sayısı_hemfikir = indikatör_sayısı_hemfikir  # 0-11
        self.risk_faktörü = risk_faktörü  # 0-1 (düşük=iyi, yüksek=riskli)
        self.hacim_teyidi = hacim_teyidi  # 0-1 (hacim ne kadar destekliyor)
        self.haber_sentiment = haber_sentiment  # -1 ile 1
        self.piyasa_trend = piyasa_trend  # -1, 0, 1
    
    def hesapla(self):
        """Composite confidence score"""
        # Base score ağırlığı
        skor = abs(self.base_score)
        
        # İndikatör hemfikirliği (11'den kaçı hemfikir?)
        hemfikirlik_puan = self.indikatör_sayısı_hemfikir / 11.0
        skor *= (0.5 + hemfikirlik_puan * 0.5)  # 50-100% boost
        
        # Risk faktörü (yüksek volatilite = lower confidence)
        risk_puan = 1.0 - self.risk_faktörü
        skor *= (0.7 + risk_puan * 0.3)  # 70-100% multiplier
        
        # Hacim teyidi (hacim destek = more confident)
        skor *= (0.65 + self.hacim_teyidi * 0.35)  # 65-100%
        
        # Haber sentiment (trend'le uyumlu mu?)
        if abs(self.haber_sentiment) > 0:
            if np.sign(self.base_score) == np.sign(self.haber_sentiment):
                skor *= 1.1  # +10% boost 
        
        # Piyasa trend (market trend support)
        if self.piyasa_trend != 0:
            if np.sign(self.base_score) == np.sign(self.piyasa_trend):
                skor *= 1.15  # +15% boost
        
        return round(min(skor, 1.0), 3)  # Cap at 100%


# ═══════════════════════════════════════════════════════════════
# HABER SENTIMENT ANALYZER (Placeholder - KAP API)
# ═══════════════════════════════════════════════════════════════

class HaberSentimentAnalyzer:
    """KAP haber sentiment analizi"""
    
    @staticmethod
    def kaptan_sentiment_al(sembol, son_n_saat=24):
        """
        KAP'tan son haberler al ve açıklama yap
        Todo: Real KAP API integrate et
        
        Returns:
            (score, açıklama) tuple
            score: -1 ile +1 (negatif-pozitif)
            açıklama: Neden bu sentiment?
        """
        # Placeholder - gerçek implementasyonda KAP API kullanacak
        sentiments = {
            "SISE.IS": (0.3, "İyi kazançlar, yatırımcı güveni artıyor"),
            "GARAN.IS": (-0.2, "Genel piyasa baskısı, finansal sektör zayıf"),
            "THYAO.IS": (0.1, "Turizm sektöründe hafif pozitif trendler"),
            "ASELS.IS": (0.4, "Güçlü talep ve expansion planları"),
            "EREGL.IS": (-0.15, "Petrol fiyatları baskılı, enerji sektörü zorluk çekiyor"),
            "KCHOL.IS": (0.25, "Kütahya Seramik yeni ürün serileri başarılı"),
            "AKBNK.IS": (0.05, "Banka sektörü dengeli, kredi talebinde toparlanma"),
            "YKBNK.IS": (-0.1, "Faiz baskısı altında, yatırımcı çekimserliği"),
        }
        
        if sembol in sentiments:
            return sentiments[sembol]
        
        # Default: nötr
        return (0, "Nötr market durumu, yeterli haber verisi yok")


# ═══════════════════════════════════════════════════════════════
# INTRADAY TRADING ANALYZER (YENİ!)
# ═══════════════════════════════════════════════════════════════

class IntradayTradingAnalyzer:
    """Intraday (gün içi) trading için özel analiz"""
    
    def __init__(self, df):
        self.df = df
        if "Kapanış" in df.columns:
            self.close_col = "Kapanış"
        elif "Close" in df.columns:
            self.close_col = "Close"
        else:
            self.close_col = df.columns[-1]
            
        if "Yüksek" in df.columns:
            self.high_col = "Yüksek"
        elif "High" in df.columns:
            self.high_col = "High"
        
        if "Düşük" in df.columns:
            self.low_col = "Düşük"
        elif "Low" in df.columns:
            self.low_col = "Low"
    
    def momentum_gucü(self):
        """
        Intraday momentum kuvveti 0-100
        Yüksek = hızlı giriş-çıkış fırsatı
        """
        c = self.df[self.close_col]
        returns = c.pct_change()
        
        # Son 5 bar'ın absolute momentum'u
        recent_momentum = returns.tail(5).abs().mean()
        
        # Yüzdeye çevir
        momentum_score = min(recent_momentum * 1000, 100)
        return round(momentum_score, 1)
    
    def volatilite_intraday(self):
        """Volatilite ratio (0-1) - intraday swing için optimal band"""
        h = self.df[self.high_col]
        l = self.df[self.low_col]
        c = self.df[self.close_col]
        
        # Average True Range ratio
        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        
        # Volatilite %
        volatilite_pct = (float(atr.iloc[-1]) / float(c.iloc[-1])) * 100
        
        return round(volatilite_pct, 2)
    
    def breakout_olasılığı(self):
        """
        Support/Resistance breakout olasılığı
        Yüksek = Quick entry fırsatı
        """
        c = self.df[self.close_col]
        h = self.df[self.high_col]
        l = self.df[self.low_col]
        
        # Son 20 bar high/low
        high_20 = h.tail(20).max()
        low_20 = l.tail(20).min()
        
        son_fiyat = float(c.iloc[-1])
        
        # Direnç'e/Destek'e olan mesafe
        mesafe_direnç = abs(son_fiyat - high_20)
        mesafe_destek = abs(son_fiyat - low_20)
        aralık = high_20 - low_20
        
        # 0-1 score: 0.5'e yakın = ortada, 0 veya 1'e yakın = breakout hazır
        if aralık > 0:
            breakout_score = min(mesafe_direnç / aralık, 1.0)
            if mesafe_destek < mesafe_direnç:
                breakout_score = 1.0 - breakout_score
        else:
            breakout_score = 0.5
        
        return round(breakout_score, 2)
    
    def entry_quality(self):
        """
        Intraday entry kalitesi: 0-100
        - Volatilite optimal range'de?
        - Momentum yüksek?
        - Breakout olasılığı var?
        """
        momentum = self.momentum_gucü()  # 0-100
        volatilite_val = self.volatilite_intraday()  # %
        breakout = self.breakout_olasılığı()  # 0-1
        
        # Volatilite optimal = 0.5-2.0%
        vol_score = 100 - abs(volatilite_val - 1.0) * 50
        vol_score = max(0, min(vol_score, 100))
        
        # Composite entry quality
        entry_quality = (
            momentum * 0.4 +          # Momentum çok önemli (intraday)
            vol_score * 0.35 +        # Volatilite
            breakout * 100 * 0.25     # Breakout potansiyeli
        )
        
        return round(entry_quality, 1)


# ═══════════════════════════════════════════════════════════════
# RİSK & VOLATILITE ANALYZER
# ═══════════════════════════════════════════════════════════════

class RiskAnalyzer:
    """Risk ve volatilite analizi"""
    
    def __init__(self, df):
        self.df = df
        # Column names'i normalize et (yfinance vs Türkçe)
        if "Kapanış" in df.columns:
            self.close_col = "Kapanış"
        elif "Close" in df.columns:
            self.close_col = "Close"
        else:
            self.close_col = df.columns[-1]  # fallback
    
    def volatilite_riski(self):
        """Volatilite risk skoru (0-1, yüksek=riskli)"""
        kapanış = self.df[self.close_col]
        returns = kapanış.pct_change()
        volatilite = returns.std()
        
        # Eğer volatilite %3'den fazlaysa riskli
        risk_skor = min(volatilite / 0.03, 1.0)
        return round(risk_skor, 3)
    
    def beta_hesapla(self, pazar_df=None):
        """Beta katsayısı (market volatilitesine karşı)"""
        # TODO: XU100 vs hisse karşılaştırması
        return 0.5  # Placeholder
    
    def drawdown_riski(self):
        """Son 20 barında maximum drawdown"""
        kapanış = self.df[self.close_col].tail(20)
        running_max = kapanış.expanding().max()
        drawdown = (kapanış - running_max) / running_max
        max_drawdown = drawdown.min()
        
        return round(abs(max_drawdown), 3)


# ═══════════════════════════════════════════════════════════════
# PIYASA DURUMU ANALYZER
# ═══════════════════════════════════════════════════════════════

class PiyasaDurumuAnalyzer:
    """Genel piyasa trendi ve durumu"""
    
    def __init__(self, bist100_df):
        self.bist100_df = bist100_df  # XU100.IS data
        # Column names'i normalize et
        if bist100_df is not None and len(bist100_df) > 0:
            if "Kapanış" in bist100_df.columns:
                self.close_col = "Kapanış"
            elif "Close" in bist100_df.columns:
                self.close_col = "Close"
            else:
                self.close_col = bist100_df.columns[-1]
        else:
            self.close_col = None
    
    def genel_trend(self):
        """Genel piyasa trendi (-1, 0, 1)"""
        if self.bist100_df is None or len(self.bist100_df) < 5 or self.close_col is None:
            return 0
        
        try:
            kapanış = self.bist100_df[self.close_col]
            ort_5bar = kapanış.rolling(5).mean()
            
            son_fiyat = float(kapanış.iloc[-1])
            son_ort = float(ort_5bar.iloc[-1])
            
            if son_fiyat > son_ort:
                return 1  # UPTREND
            elif son_fiyat < son_ort:
                return -1  # DOWNTREND
            else:
                return 0  # NÖTR
        except:
            return 0
    
    def piyasa_volatilitesi(self):
        """Genel piyasa volatilitesi"""
        if self.bist100_df is None or self.close_col is None:
            return 0.015
        
        try:
            returns = self.bist100_df[self.close_col].pct_change()
            vol = returns.std()
            return float(round(vol, 4))
        except:
            return 0.015
    
    def fear_greed_index(self):
        """VIX benzeri fear/greed (placeholder)"""
        # TODO: ^VIX ve diğer global indicators'dan hesapla
        return 50  # 0-100, 50=neutral


# ═══════════════════════════════════════════════════════════════
# ADVANCED SINYAL FORMATTER
# ═══════════════════════════════════════════════════════════════

class AdvancedSignalFormatter:
    """Geliştirilmiş sinyal formatı"""
    
    @staticmethod
    def format_telegram_message(sembol, fiyat, sinyal, güven, stop_loss, 
                                hedef, atr, volatilite, risk, haber, piyasa,
                                haber_text="", momentum=0, entry_quality=0, breakout=0):
        """Profesyonel Telegram mesajı - INTRADAY TRADING FOCUS"""
        
        # Sinyal emoji
        if "AL" in sinyal:
            emoji = "🟢" if "GÜÇLÜ" in sinyal else "📗"
        elif "SAT" in sinyal:
            emoji = "🔴" if "GÜÇLÜ" in sinyal else "📕"
        else:
            emoji = "⚪"
        
        # Güven meter
        confidence_meter = AdvancedSignalFormatter._confidence_meter(güven)
        
        # Risk meter
        risk_meter = AdvancedSignalFormatter._risk_meter(risk)
        
        # Piyasa durumu emoji
        piyasa_emoji = "📈" if piyasa > 0 else "📉" if piyasa < 0 else "➡️"
        
        # Haber sentiment detaylı
        if haber > 0.2:
            haber_emoji = "😊 Pozitif"
        elif haber < -0.2:
            haber_emoji = "😔 Negatif"
        else:
            haber_emoji = "😐 Nötr"
        
        # İntraday özel göstergeler
        momentum_status = "⚡ YÜKSEK" if momentum > 60 else "✓ NORMAL" if momentum > 30 else "❄️ DÜŞÜK"
        entry_status = "✅ ÇOK İYİ" if entry_quality > 75 else "✓ İYİ" if entry_quality > 50 else "⚠️  ZAYIF"
        breakout_status = "📊 YÜKSELİŞ" if breakout > 0.7 else "📈 OKE" if breakout > 0.3 else "📉 DÜŞÜŞ"
        
        # Entry kalitesine göre emoji
        entry_emoji = "🟢" if entry_quality > 75 else "🟡" if entry_quality > 50 else "🔴"
        
        # Mesaj
        mesaj = f"""
{emoji} {sinyal} - {sembol}
════════════════════════════════════════
📊 Fiyat: {fiyat:.2f} ₺
💪 Güven: {confidence_meter} {int(güven*100)}%
⚠️  Risk: {risk_meter} {int(risk*100)}%

🚀 INTRADAY TRADE ANALIZI:
   {entry_emoji} Entry Quality: {entry_status} ({int(entry_quality)}%)
   ⚡ Momentum: {momentum_status} ({int(momentum)}%)
   📊 Breakout Potansiyeli: {breakout_status}
   
📈 Teknik Analiz:
   • Stop Loss: {stop_loss:.2f} ₺
   • Target: {hedef:.2f} ₺
   • R:R Ratio: 1:{round((hedef-fiyat)/(fiyat-stop_loss), 2)}
   • Volatilite (ATR): {atr:.2f} ₺

🔗 Piyasa + Haber Sentimenti:
   {piyasa_emoji} Trend: {"🚀 UPTREND" if piyasa > 0 else "📉 DOWNTREND" if piyasa < 0 else "➡️ NÖTR"}
   {haber_emoji}"""
        
        if haber_text:
            mesaj += f"\n   → {haber_text}"
        
        mesaj += f"""

⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
—
💡 Strateji: INTRADAY (Hızlı giriş-çıkış, günlük işlem)
⚠️ NOT: Eğitim Amaçlıdır. Kendi Risk Yönetiminizi Yapınız!
"""
        return mesaj
    
    @staticmethod
    def _confidence_meter(confidence):
        """Grafik güven göstergesi"""
        level = int(confidence * 10)
        filled = "🟩" * level
        empty = "⬜" * (10 - level)
        return filled + empty
    
    @staticmethod
    def _risk_meter(risk):
        """Risk göstergesi (düşük iyi, yüksek kötü)"""
        level = int(risk * 10)
        colors = ["🟩", "🟩", "🟨", "🟨", "🟨", "🟧", "🟧", "🟥", "🟥", "🟥"]
        meter = "".join([colors[i] if i <= level else "⬜" for i in range(10)])
        return meter
    
    @staticmethod
    def format_ozet_message(sinyaller):
        """Saatlik özet mesajı (top 5)"""
        mesaj = f"📊 BIST SINYALI ÖZETI - {datetime.now().strftime('%H:%M')}\n"
        mesaj += "════════════════════════════════════\n\n"
        
        for i, sig in enumerate(sinyaller[:5], 1):
            sinyal_emoji = "🟢" if "AL" in sig["sinyal"] else "🔴" if "SAT" in sig["sinyal"] else "⚪"
            mesaj += f"{i}) {sinyal_emoji} {sig['sembol']}\n"
            mesaj += f"   Sinyal: {sig['sinyal']}\n"
            mesaj += f"   Fiyat: {sig['fiyat']:.2f} ₺\n"
            mesaj += f"   Güven: {int(sig['güven']*100)}% | Risk: {int(sig['risk']*100)}%\n"
            mesaj += f"   Stop: {sig['stop']:.2f} | Hedef: {sig['hedef']:.2f}\n\n"
        
        mesaj += "════════════════════════════════════\n"
        mesaj += f"Toplam Sinyal: {len(sinyaller)} | "
        mesaj += f"AL: {len([s for s in sinyaller if 'AL' in s['sinyal']])} | "
        mesaj += f"SAT: {len([s for s in sinyaller if 'SAT' in s['sinyal']])}\n\n"
        mesaj += "⚠️ Not: Eğitim Amaçlıdır. Risk Yönetimi Yapınız!"
        
        return mesaj


# ═══════════════════════════════════════════════════════════════
# ENHANCED CSV FORMATTER
# ═══════════════════════════════════════════════════════════════

def export_advanced_signals(sinyaller, output_dir="data/signals"):
    """Geliştirilmiş CSV export - flexible format destekler"""
    data = []
    
    for sig in sinyaller:
        # Fallback keys ile güvenli erişim
        data.append({
            "Tarih": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "Sembol": sig.get("sembol", "N/A"),
            "Fiyat": sig.get("fiyat", 0),
            "Sinyal": sig.get("sinyal", "NÖTR"),
            "Ağırlıklı_Skor": sig.get("skor", sig.get("güven", 0)),  # Fallback: güven
            "Güven_%": int(sig.get("güven", 0) * 100),
            "Risk_%": int(sig.get("risk", 0) * 100),
            "ATR": sig.get("atr", 0),
            "Stop_Loss": sig.get("stop", sig.get("stop_loss", 0)),  # Fallback
            "Hedef": sig.get("hedef", 0),
            "Haber_Sentiment": sig.get("haber", 0),
            "Piyasa_Trendi": sig.get("piyasa", "NÖTR"),
        })
    
    df = pd.DataFrame(data)
    
    # CSV kaydet
    csv_path = Path(output_dir) / f"advanced_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    return csv_path, df


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test confidence score
    conf = AdvancedConfidenceScore(
        base_score=0.35,
        indikatör_sayısı_hemfikir=9,  # 11'den 9'u hemfikir
        risk_faktörü=0.25,  # Orta risk
        hacim_teyidi=0.8,  # Hacim yüksek
        haber_sentiment=0.2,  # Hafif pozitif haber
        piyasa_trend=1  # Uptrend
    )
    
    güven = conf.hesapla()
    print(f"Composite Confidence: {güven * 100}%")
    
    # Test formatter
    mesaj = AdvancedSignalFormatter.format_telegram_message(
        sembol="SISE.IS",
        fiyat=46.50,
        sinyal="ZAYIF AL",
        güven=0.72,
        stop_loss=43.20,
        hedef=51.30,
        atr=2.4,
        volatilite=0.018,
        risk=0.35,
        haber=0.2,
        piyasa=1
    )
    print(mesaj)
