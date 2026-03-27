"""
Multi-Timeframe Analyzer - 5m, 15m, 1H trend validation
========================================================
Küçük timeframe sinyalini büyük timeframe trend ile doğrula:
- 5m: Entry trigger
- 15m: Trend filtesi
- 1H: Market context
Eğer hepsi aligned ise sinyal güveni %40 artacak
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MultiTimeframeAnalyzer:
    """Multi-timeframe trend analysis"""
    
    def __init__(self, sembol, lookback_periods=50):
        self.sembol = sembol
        self.lookback_periods = lookback_periods
        self.df_5m = None
        self.df_15m = None
        self.df_1h = None
        self.df_4h = None
        
    def verileri_çek(self):
        """Tüm timeframe'leri çek"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # 5 minutelık (son 10 gün)
            self.df_5m = yf.download(
                self.sembol, 
                start=end_date - timedelta(days=10),
                interval="5m",
                progress=False
            )
            
            # 15 minutellik
            self.df_15m = yf.download(
                self.sembol,
                start=end_date - timedelta(days=20),
                interval="15m",
                progress=False
            )
            
            # 1 saatlik
            self.df_1h = yf.download(
                self.sembol,
                start=start_date,
                interval="1h",
                progress=False
            )
            
            # 4 saatlik (market context)
            self.df_4h = yf.download(
                self.sembol,
                start=start_date - timedelta(days=90),
                interval="1h",
                progress=False
            )
            
            # 4h aggregate (4 adet 1h = 1 adet 4h)
            if self.df_4h is not None and len(self.df_4h) >= 4:
                try:
                    # Handle MultiIndex columns if present
                    if isinstance(self.df_4h.columns, pd.MultiIndex):
                        self.df_4h.columns = self.df_4h.columns.droplevel(1)
                    
                    # Resample to 4-hour candles
                    agg_dict = {}
                    if 'Open' in self.df_4h.columns:
                        agg_dict['Open'] = 'first'
                    if 'High' in self.df_4h.columns:
                        agg_dict['High'] = 'max'
                    if 'Low' in self.df_4h.columns:
                        agg_dict['Low'] = 'min'
                    if 'Close' in self.df_4h.columns:
                        agg_dict['Close'] = 'last'
                    if 'Volume' in self.df_4h.columns:
                        agg_dict['Volume'] = 'sum'
                    
                    if agg_dict:
                        self.df_4h = self.df_4h.resample('4h').agg(agg_dict)
                        self.df_4h.columns = list(agg_dict.keys())  # Ensure column names are set
                except Exception as resample_error:
                    logger.warning(f"4h resample hatası: {resample_error}, raw verileri kullanılacak")
            
            return True
            
        except Exception as e:
            logger.error(f"Multi-timeframe veri çekme hatası ({self.sembol}): {e}")
            return False
    
    def _hesapla_trend(self, df, period=20):
        """
        Trend hesapla:
        +1: UPTREND
        0: NÖTR
        -1: DOWNTREND
        """
        if df is None or len(df) < period:
            return 0
        
        try:
            # Ensure Close column exists
            if 'Close' not in df.columns:
                logger.warning("Close column not found in df")
                return 0
                
            close = df['Close'].values.ravel()  # Ensure 1D array
            sma_short = pd.Series(close).rolling(period).mean().iloc[-1]
            sma_long = pd.Series(close).rolling(period*2).mean().iloc[-1]
            
            current_price = close[-1]
            
            if current_price > sma_short > sma_long:
                return 1  # UPTREND
            elif current_price < sma_short < sma_long:
                return -1  # DOWNTREND
            else:
                return 0  # NÖTR
        except Exception as e:
            logger.warning(f"Trend hesaplama hatası: {e}")
            return 0
    
    def _hesapla_momentum(self, df):
        """Momentum hesapla (RSI-based)"""
        if df is None or len(df) < 14:
            return 0
        
        try:
            if 'Close' not in df.columns:
                return 0
                
            close = df['Close'].values.ravel()  # Ensure 1D array
            
            # RSI hesapla
            delta = np.diff(close)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            
            avg_gain = np.mean(gain[-14:])
            avg_loss = np.mean(loss[-14:])
            
            if avg_loss == 0:
                return 50
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        except Exception as e:
            logger.warning(f"Momentum hesaplama hatası: {e}")
            return 0
    
    def _hesapla_oynaklık(self, df):
        """Volatilite hesapla (ATR %)"""
        if df is None or len(df) < 14:
            return 0
        
        try:
            required_cols = ['High', 'Low', 'Close']
            if not all(col in df.columns for col in required_cols):
                return 0
                
            high = df['High'].values.ravel()[-14:]  # Ensure 1D array
            low = df['Low'].values.ravel()[-14:]
            close = df['Close'].values.ravel()[-14:]
            
            tr1 = high - low
            tr2 = np.abs(high - np.roll(close, 1))
            tr3 = np.abs(low - np.roll(close, 1))
            
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            atr = np.mean(tr)
            
            volatilite_pct = (atr / close[-1]) * 100
            
            return volatilite_pct
        except Exception as e:
            logger.warning(f"Oynaklık hesaplama hatası: {e}")
            return 0
    
    def analiz_yap(self, işlem_tipi="AL"):
        """
        Multi-timeframe analiz yap:
        İşlem tipi: AL veya SAT
        
        Return: alignment_score (0-100), trend_dict
        """
        
        if not self.verileri_çek():
            return 0, {}
        
        # Her timeframe için trend hesapla
        trend_5m = self._hesapla_trend(self.df_5m, period=5)
        trend_15m = self._hesapla_trend(self.df_15m, period=10)
        trend_1h = self._hesapla_trend(self.df_1h, period=14)
        trend_4h = self._hesapla_trend(self.df_4h, period=20)
        
        # Momentum
        momentum_5m = self._hesapla_momentum(self.df_5m)
        momentum_1h = self._hesapla_momentum(self.df_1h)
        
        # Oynaklık
        vol_1h = self._hesapla_oynaklık(self.df_1h)
        vol_4h = self._hesapla_oynaklık(self.df_4h)
        
        # Alignment check
        alignment_score = 0
        alignment_details = {
            "5m_trend": trend_5m,
            "15m_trend": trend_15m,
            "1h_trend": trend_1h,
            "4h_trend": trend_4h,
            "5m_momentum": momentum_5m,
            "1h_momentum": momentum_1h,
            "1h_volatility": vol_1h,
            "4h_volatility": vol_4h,
        }
        
        if işlem_tipi in ["AL", "GÜÇLÜ AL", "ZAYIF AL"]:
            # AL işlemi: tüm trend UP alignment
            
            # 5m trend önemli (entry trigger)
            if trend_5m == 1:
                alignment_score += 20
            elif trend_5m == 0:
                alignment_score += 10
            
            # 15m trend (lokum filtesi)
            if trend_15m == 1:
                alignment_score += 15
            elif trend_15m == 0:
                alignment_score += 8
            
            # 1h trend (medium-term)
            if trend_1h == 1:
                alignment_score += 25
            elif trend_1h == 0:
                alignment_score += 12
            
            # 4h trend (context - en önemli)
            if trend_4h == 1:
                alignment_score += 25
            elif trend_4h == 0:
                alignment_score += 10
            elif trend_4h == -1:
                alignment_score -= 10  # Dönüş cezası
            
            # Momentum doğrulaması
            if momentum_5m > 60:
                alignment_score += 5
            if momentum_1h > 50:
                alignment_score += 5
        
        elif işlem_tipi in ["SAT", "GÜÇLÜ SAT", "ZAYIF SAT"]:
            # SAT işlemi: tüm trend DOWN alignment
            
            if trend_5m == -1:
                alignment_score += 20
            elif trend_5m == 0:
                alignment_score += 10
            
            if trend_15m == -1:
                alignment_score += 15
            elif trend_15m == 0:
                alignment_score += 8
            
            if trend_1h == -1:
                alignment_score += 25
            elif trend_1h == 0:
                alignment_score += 12
            
            if trend_4h == -1:
                alignment_score += 25
            elif trend_4h == 0:
                alignment_score += 10
            elif trend_4h == 1:
                alignment_score -= 10
            
            if momentum_5m < 40:
                alignment_score += 5
            if momentum_1h < 50:
                alignment_score += 5
        
        # Cap at 100
        alignment_score = min(alignment_score, 100)
        alignment_score = max(alignment_score, 0)
        
        return alignment_score, alignment_details
    
    def güven_boost_hesapla(self, base_güven, işlem_tipi="AL"):
        """
        Base güvenin Multi-timeframe alignment ile güven boost et
        
        Example:
        - Base: 55% (ZAYIF AL)
        - Alignment: 85/100
        - Final: 55% + (85% guidance) = Better confidence
        """
        
        alignment_score, _ = self.analiz_yap(işlem_tipi)
        
        # Base güvenin %30'u kadar boost edilebilir max
        max_boost = base_güven * 0.30
        
        # Alignment score'a göre boost
        boost = (alignment_score / 100.0) * max_boost
        
        final_güven = min(base_güven + boost, 100.0)
        
        return final_güven, alignment_score
    
    def rapor_oluştur(self):
        """MTF analiz raporu"""
        alignment_score, details = self.analiz_yap()
        
        rapor = f"""
╔════════════════════════════════════════════════════════════╗
║     MULTI-TIMEFRAME TREND ANALYSIS - {self.sembol}
╚════════════════════════════════════════════════════════════╝

📊 TREND ALIGNMENT SCORE: {alignment_score}/100

🔍 TİMEFRAME TRENDS
─────────────────────────────────────────────
  5m  Trend: {'🟢 UPTREND' if details['5m_trend'] == 1 else '🔴 DOWNTREND' if details['5m_trend'] == -1 else '⚪ NÖTR'}
  15m Trend: {'🟢 UPTREND' if details['15m_trend'] == 1 else '🔴 DOWNTREND' if details['15m_trend'] == -1 else '⚪ NÖTR'}
  1H  Trend: {'🟢 UPTREND' if details['1h_trend'] == 1 else '🔴 DOWNTREND' if details['1h_trend'] == -1 else '⚪ NÖTR'}
  4H  Trend: {'🟢 UPTREND' if details['4h_trend'] == 1 else '🔴 DOWNTREND' if details['4h_trend'] == -1 else '⚪ NÖTR'}

⚡ MOMENTUM
─────────────────────────────────────────────
  5m  RSI: {details['5m_momentum']:.1f}
  1H  RSI: {details['1h_momentum']:.1f}

🌊 VOLATILITY (ATR %)
─────────────────────────────────────────────
  1H  Vol: {details['1h_volatility']:.2f}%
  4H  Vol: {details['4h_volatility']:.2f}%

📈 DEĞERLENDİRME
─────────────────────────────────────────────
  • 85+: Güçlü Alignment (Sinyal Güveni +40%)
  • 60-85: Orta Alignment (Sinyal Güveni +25%)
  • 40-60: Zayıf Alignment (Sinyal Güveni +10%)
  • <40: Alignment Yok (Sinyal Red)
"""
        
        return rapor


# Test
if __name__ == "__main__":
    analyzer = MultiTimeframeAnalyzer("PETKM.IS")
    
    # AL işlemi için analiz
    base_güven = 55
    final_güven, alignment = analyzer.güven_boost_hesapla(base_güven, işlem_tipi="AL")
    
    print(analyzer.rapor_oluştur())
    print(f"\nBase Güven: {base_güven}%")
    print(f"MTF Alignment: {alignment}/100")
    print(f"Final Güven: {final_güven:.1f}%")
    print(f"Boost: +{final_güven - base_güven:.1f}%")
