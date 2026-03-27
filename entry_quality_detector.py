"""
Advanced Entry Quality Detection - Candlestick Patterns
=======================================================
Bullish/Bearish pattern tanısı:
- Engulfing
- Pin Bar (Hammer/Hanging Man)
- Doji
- Breakout + Retest
- Support/Resistance level validation
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class CandlestickPatternDetector:
    """Candlestick pattern recognition"""
    
    def __init__(self, df):
        """
        df: OHLCV DataFrame (Open, High, Low, Close, Volume required)
        """
        self.df = df.copy()
        self.patterns = {
            "engulfing": 0,
            "pin_bar": 0,
            "doji": 0,
            "breakout": 0,
            "demand_zone": 0,
            "supply_zone": 0,
        }
    
    def _normalize_açılış_kapat(self, idx):
        """Açılış-kapanış normalleştirilmiş farkı"""
        o = self.df.iloc[idx]["Open"]
        c = self.df.iloc[idx]["Close"]
        return abs(c - o)
    
    def _body_boyutu(self, idx):
        """Çubuğun body boyutu (fark)"""
        o = self.df.iloc[idx]["Open"]
        c = self.df.iloc[idx]["Close"]
        return abs(c - o)
    
    def _shadow_boyutu(self, idx):
        """Çubuğun shadow boyutu (wick)"""
        h = self.df.iloc[idx]["High"]
        l = self.df.iloc[idx]["Low"]
        o = self.df.iloc[idx]["Open"]
        c = self.df.iloc[idx]["Close"]
        
        top_shadow = h - max(o, c)
        bottom_shadow = min(o, c) - l
        
        return top_shadow, bottom_shadow
    
    def engulfing_pattern(self, bullish=True):
        """
        Engulfing Pattern:
        Bullish: Kırmızı çubuk + Yeşil çubuk (body olarak tam kapsıyor)
        """
        if len(self.df) < 2:
            return 0
        
        idx = -1
        prev_idx = -2
        
        prev_o = self.df.iloc[prev_idx]["Open"]
        prev_c = self.df.iloc[prev_idx]["Close"]
        curr_o = self.df.iloc[idx]["Open"]
        curr_c = self.df.iloc[idx]["Close"]
        
        if bullish:
            # Önceki çubuk bearish (red)
            if prev_c >= prev_o:
                return 0
            
            # Şu anki çubuk bullish (green) ve öncekini kapsıyor
            if curr_c > prev_o and curr_o < prev_c:
                score = 40  # Base score
                
                # Kapsama gücü
                coverage = min((curr_c - curr_o) / (prev_o - prev_c), 2.0) * 100
                score += min(coverage, 30)
                
                return min(score, 100)
        else:
            # Bearish engulfing
            if prev_c <= prev_o:
                return 0
            
            if curr_c < prev_o and curr_o > prev_c:
                score = 40
                coverage = min((curr_o - curr_c) / (prev_c - prev_o), 2.0) * 100
                score += min(coverage, 30)
                
                return min(score, 100)
        
        return 0
    
    def pin_bar_pattern(self, bullish=True):
        """
        Pin Bar (Hammer/Hanging Man):
        - Küçük body
        - Çok uzun alt wick (bullish) veya üst wick (bearish)
        """
        if len(self.df) < 1:
            return 0
        
        idx = -1
        body = self._body_boyutu(idx)
        top_shadow, bottom_shadow = self._shadow_boyutu(idx)
        
        h = self.df.iloc[idx]["High"]
        l = self.df.iloc[idx]["Low"]
        candle_range = h - l
        
        # Body %20'den az olmalı (bar'ın body'si küçük)
        body_ratio = body / candle_range if candle_range > 0 else 0
        
        if bullish:
            # Hammer: Alt wick uzun, üst wick kısa
            if bottom_shadow > (top_shadow * 2) and body_ratio < 0.3:
                wick_strength = min((bottom_shadow / candle_range) * 100, 50)
                return min(35 + wick_strength, 100)
        else:
            # Hanging man: Üst wick uzun
            if top_shadow > (bottom_shadow * 2) and body_ratio < 0.3:
                wick_strength = min((top_shadow / candle_range) * 100, 50)
                return min(35 + wick_strength, 100)
        
        return 0
    
    def doji_pattern(self):
        """
        Doji: Açılış = Kapanış (veya çok yakın)
        Belirsizlik gösterimi
        """
        if len(self.df) < 1:
            return 0
        
        idx = -1
        o = self.df.iloc[idx]["Open"]
        c = self.df.iloc[idx]["Close"]
        
        body = abs(c - o)
        h = self.df.iloc[idx]["High"]
        l = self.df.iloc[idx]["Low"]
        candle_range = h - l
        
        body_ratio = body / candle_range if candle_range > 0 else 0
        
        # Body %5'ten az
        if body_ratio < 0.05:
            # Doji, ama trendi kırma öncesi ise değersiz
            return 15  # Zayıf sinyal
        
        return 0
    
    def support_resistance_test(self, sembol_verisi):
        """
        Support/Resistance level test:
        Son 50 bar içinde level tanı, şu anki fiyat test ederse score artır
        """
        if len(self.df) < 50:
            return 0
        
        close_prices = self.df["Close"].values
        
        # Son 50 bar
        prices_50 = close_prices[-50:]
        
        # Support ve resistance level
        support = np.min(prices_50)
        resistance = np.max(prices_50)
        current = close_prices[-1]
        
        # Test score
        score = 0
        
        # Support test
        if current > support and current < support * 1.02:
            score += 30  # Support bounce
        
        # Resistance test
        if current < resistance and current > resistance * 0.98:
            score += 30  # Resistance pushup
        
        return min(score, 70)
    
    def breakout_retest_pattern(self):
        """
        Breakout + Retest:
        1. Breakout oldu (resistance/support geçildi)
        2. Retest oldu (geri test)
        """
        if len(self.df) < 20:
            return 0
        
        close_prices = self.df["Close"].values[-20:]
        
        # Peaks ve valleys bul
        peaks = []
        valleys = []
        
        for i in range(1, len(close_prices) - 1):
            if close_prices[i] > close_prices[i-1] and close_prices[i] > close_prices[i+1]:
                peaks.append((i, close_prices[i]))
            if close_prices[i] < close_prices[i-1] and close_prices[i] < close_prices[i+1]:
                valleys.append((i, close_prices[i]))
        
        if not peaks or not valleys:
            return 0
        
        # Son peak/valley level
        recent_resistance = max([p[1] for p in peaks[-3:]])
        recent_support = min([v[1] for v in valleys[-3:]])
        
        current = close_prices[-1]
        
        # Breakout + Retest detect
        score = 0
        
        # Bullish: retest support
        if current > recent_resistance:
            # Breakout, şimdi retest bak
            if any(close_prices[i] < recent_resistance for i in range(len(close_prices) - 5, -1, -1)):
                score = 45
        
        # Bearish: retest resistance
        if current < recent_support:
            if any(close_prices[i] > recent_support for i in range(len(close_prices) - 5, -1, -1)):
                score = 45
        
        return score
    
    def hesapla_entry_quality(self, işlem_tipi="AL"):
        """
        Entry quality score (0-100) hesapla
        """
        
        if işlem_tipi in ["AL", "GÜÇLÜ AL"]:
            # Bullish pattern'ları ara
            engulfing = self.engulfing_pattern(bullish=True)
            pin_bar = self.pin_bar_pattern(bullish=True)
            breakout = self.breakout_retest_pattern()
            support_test = self.support_resistance_test(None)
            
            # Weighted average
            scores = [
                (engulfing, 0.25),
                (pin_bar, 0.20),
                (breakout, 0.25),
                (support_test, 0.30),
            ]
        else:
            # Bearish pattern'ları ara
            engulfing = self.engulfing_pattern(bullish=False)
            pin_bar = self.pin_bar_pattern(bullish=False)
            breakout = self.breakout_retest_pattern()
            support_test = self.support_resistance_test(None)
            
            scores = [
                (engulfing, 0.25),
                (pin_bar, 0.20),
                (breakout, 0.25),
                (support_test, 0.30),
            ]
        
        # Weighted score
        entry_quality = sum(s * w for s, w in scores)
        entry_quality = max(0, min(entry_quality, 100))
        
        return entry_quality
    
    def rapor_oluştur(self):
        """Pattern analiz raporu"""
        
        if len(self.df) < 2:
            return "Yeterli veri yok"
        
        bullish_engulfing = self.engulfing_pattern(bullish=True)
        bearish_engulfing = self.engulfing_pattern(bullish=False)
        pin_bar_bull = self.pin_bar_pattern(bullish=True)
        pin_bar_bear = self.pin_bar_pattern(bullish=False)
        doji = self.doji_pattern()
        breakout = self.breakout_retest_pattern()
        
        rapor = f"""
╔═══════════════════════════════════════════════════════════╗
║        CANDLESTICK PATTERN DETECTION REPORT
╚═══════════════════════════════════════════════════════════╝

🔍 BULLISH PATTERNS
─────────────────────────────────────────────
  Engulfing (Bullish): {bullish_engulfing:.0f}/100
  Pin Bar (Hammer):    {pin_bar_bull:.0f}/100
  Breakout (Bullish):  {breakout:.0f}/100

🔴 BEARISH PATTERNS
─────────────────────────────────────────────
  Engulfing (Bearish): {bearish_engulfing:.0f}/100
  Pin Bar (Hanging):   {pin_bar_bear:.0f}/100
  Breakout (Bearish):  {breakout:.0f}/100

⚪ NEUTRALİTY
─────────────────────────────────────────────
  Doji Pattern:        {doji:.0f}/100

📊 ENTRY QUALITY SCORES
─────────────────────────────────────────────
  AL Entry Quality:    {self.hesapla_entry_quality('AL'):.0f}/100
  SAT Entry Quality:   {self.hesapla_entry_quality('SAT'):.0f}/100

💡 İNTERPRETASYON
  • 70+: Çok Güçlü Entry (Hemen gir)
  • 50-70: Orta Güçlü (Beklemeye değer)
  • 30-50: Zayıf (Bekleme tercih)
  • <30: Çok Zayıf (Girmeme)
"""
        
        return rapor


# Test
if __name__ == "__main__":
    import yfinance as yf
    
    df = yf.download("PETKM.IS", period="30d", interval="5m", progress=False)
    
    detector = CandlestickPatternDetector(df)
    
    print(detector.rapor_oluştur())
    
    print(f"\nAL Entry Quality: {detector.hesapla_entry_quality('AL'):.1f}%")
    print(f"SAT Entry Quality: {detector.hesapla_entry_quality('SAT'):.1f}%")
