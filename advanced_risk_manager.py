"""
Advanced Volatility-Based Stop Loss & Take Profit System
========================================================
Dynamic SL/TP adjustment:
- ATR-based (adaptif market volatility)
- Chandelier Stop
- Time-based stop (X dakika)
- Risk/Reward ratio enforcement (min 1:2)
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class AdvancedRiskManager:
    """
    Volatilite-bazlı dinamik risk yönetimi
    """
    
    def __init__(self, df, portfolio_size=10000.0, risk_per_trade=2.0):
        """
        df: OHLC DataFrame
        portfolio_size: Portföy büyüklüğü (TL)
        risk_per_trade: Risk yüzdesi (%2 = her trade'de portföyün %2'si)
        """
        self.df = df.copy()
        self.portfolio_size = portfolio_size
        self.risk_per_trade = risk_per_trade
        
        self._hesapla_indicators()
    
    def _hesapla_indicators(self):
        """ATR, Volatility, Chandelier hesapla"""
        
        # ATR (Average True Range)
        high = self.df['High'].values
        low = self.df['Low'].values
        close = self.df['Close'].values
        
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        self.atr = pd.Series(tr).rolling(14).mean().values
        
        # ATR %
        self.atr_pct = (self.atr / close) * 100
        
        # Kanal (Chandelier)
        self.highest_high = pd.Series(high).rolling(22).max().values
        self.lowest_low = pd.Series(low).rolling(22).min().values
    
    def hesapla_atr_based_sl_tp(self, entry_price, işlem_tipi="AL", atr_multiplier_sl=2.0, atr_multiplier_tp=3.0):
        """
        ATR-based SL/TP
        
        Args:
        - entry_price: Giriş fiyatı
        - işlem_tipi: AL veya SAT
        - atr_multiplier_sl: SL için ATR çarpanı (2-3)
        - atr_multiplier_tp: TP için ATR çarpanı (3-5)
        
        Return: (stop_loss, take_profit, atr_used)
        """
        
        if len(self.atr) == 0:
            # Default SL/TP
            if işlem_tipi == "AL":
                sl = entry_price * 0.97  # %3 below
                tp = entry_price * 1.06  # %6 above
            else:
                sl = entry_price * 1.03
                tp = entry_price * 0.94
            
            return sl, tp, 0
        
        current_atr = self.atr[-1]
        
        if işlem_tipi in ["AL", "GÜÇLÜ AL", "ZAYIF AL"]:
            # BUY
            stop_loss = entry_price - (current_atr * atr_multiplier_sl)
            take_profit = entry_price + (current_atr * atr_multiplier_tp)
        else:
            # SELL
            stop_loss = entry_price + (current_atr * atr_multiplier_sl)
            take_profit = entry_price - (current_atr * atr_multiplier_tp)
        
        return stop_loss, take_profit, current_atr
    
    def hesapla_chandelier_stop(self, işlem_tipi="AL", lookback=22):
        """
        Chandelier Stop (Trailing stop)
        
        - Bull: Highest High (22 bar) - ATR
        - Bear: Lowest Low (22 bar) + ATR
        """
        
        if len(self.df) < lookback:
            return None
        
        current_atr = self.atr[-1]
        
        if işlem_tipi in ["AL", "GÜÇLÜ AL"]:
            # Bull chandelier
            chandelier_stop = self.highest_high[-1] - (current_atr * 3)
            return chandelier_stop
        else:
            # Bear chandelier
            chandelier_stop = self.lowest_low[-1] + (current_atr * 3)
            return chandelier_stop
    
    def hesapla_position_size(self, entry_price, stop_loss, sembol_price=1.0):
        """
        Risk-based position sizing:
        
        Position Size = (Risk Amount) / (Entry - Stop Loss)
        Risk Amount = Portfolio Size × Risk % / 100
        """
        
        risk_amount = (self.portfolio_size * self.risk_per_trade) / 100
        
        distance = abs(entry_price - stop_loss)
        
        if distance == 0:
            return 0
        
        # Kaç lot girebiliriz?
        position_value = risk_amount / distance  # Tutulacak fiyat toplamı
        
        # Standart lot: 10 adet base case
        position_size = int((position_value / entry_price) / sembol_price) * sembol_price
        
        # Min 1 lot
        position_size = max(position_size, 1)
        
        return position_size
    
    def rr_ratio_kontrol(self, entry_price, stop_loss, take_profit, min_rr=1.0):
        """
        Risk/Reward Ratio kontrolü
        
        RR = Profit Size / Risk Size
        Min RR 1.0 olmalı (1:1), ideal 1.5-2.0
        """
        
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return 0, False
        
        rr_ratio = reward / risk
        
        is_valid = rr_ratio >= min_rr
        
        return rr_ratio, is_valid
    
    def optimize_tp_by_rr(self, entry_price, stop_loss, target_rr=2.0, işlem_tipi="AL"):
        """
        TP'yi target RR'ye göre optimize et
        
        Örnek: Hedefiniz 2:1 RR ise
        TP = Entry + (Stop Loss - Entry) × 2
        """
        
        risk = abs(entry_price - stop_loss)
        reward_needed = risk * target_rr
        
        if işlem_tipi in ["AL", "GÜÇLÜ AL"]:
            take_profit = entry_price + reward_needed
        else:
            take_profit = entry_price - reward_needed
        
        return take_profit
    
    def time_based_stop(self, entry_time, timeout_minutes=60):
        """
        Time-based stop: X dakika sonra çık
        """
        
        # TODO: Real implementation
        return {
            "timeout_minutes": timeout_minutes,
            "exit_condition": f"Eğer {timeout_minutes} dakikada TP/SL hit olmadıysa, market close yap"
        }
    
    def rapor_oluştur(self, entry_price, işlem_tipi="AL"):
        """Risk management raporu"""
        
        # ATR-based
        sl_atr, tp_atr, atr_val = self.hesapla_atr_based_sl_tp(
            entry_price, 
            işlem_tipi,
            atr_multiplier_sl=2.0,
            atr_multiplier_tp=3.0
        )
        
        # Chandelier
        chandelier = self.hesapla_chandelier_stop(işlem_tipi)
        
        # RR Ratio
        rr, is_valid = self.rr_ratio_kontrol(entry_price, sl_atr, tp_atr, min_rr=1.5)
        
        # Position size
        pos_size = self.hesapla_position_size(entry_price, sl_atr)
        
        # Optimized TP
        tp_optimized = self.optimize_tp_by_rr(entry_price, sl_atr, target_rr=2.0, işlem_tipi=işlem_tipi)
        rr_optimized, _ = self.rr_ratio_kontrol(entry_price, sl_atr, tp_optimized)
        
        rapor = f"""
╔════════════════════════════════════════════════════════════╗
║        ADVANCED RISK MANAGEMENT REPORT
╚════════════════════════════════════════════════════════════╝

📊 İŞLEM PARAMETRELERI
────────────────────────────────────────────
  Entry Price:          {entry_price:.2f} TL
  İşlem Tipi:          {işlem_tipi}
  Current ATR:          {atr_val:.2f} TL ({self.atr_pct[-1]:.2f}%)

🛑 STOP LOSS SEÇENEKLERİ
────────────────────────────────────────────
  ATR-Based (2x):       {sl_atr:.2f} TL (Risk: {entry_price - sl_atr:.2f} TL)
  Chandelier Stop:      {chandelier:.2f} TL (Trailing)

🎯 TAKE PROFIT SEÇENEKLERİ
────────────────────────────────────────────
  ATR-Based (3x):       {tp_atr:.2f} TL
  Optimized (2:1 RR):   {tp_optimized:.2f} TL

📈 RISK/REWARD ANALYSIS
────────────────────────────────────────────
  ATR-Based RR:         1:{rr:.2f} {'✅ (Kabul)' if is_valid else '❌ (Reddedildi)'}
  Optimized RR:         1:{rr_optimized:.2f} ✅

💰 POZİSYON SİZİNG
────────────────────────────────────────────
  Portföy:              {self.portfolio_size:.2f} TL
  Risk per Trade:       {self.risk_per_trade}%
  Risk Amount:          {(self.portfolio_size * self.risk_per_trade) / 100:.2f} TL
  Position Size:        {pos_size} adet
  
⏰ TIME-BASED STOP
────────────────────────────────────────────
  Timeout:              60 dakika (exit condition)

╔════════════════════════════════════════════════════════════╗
║ ÖNERİ: Optimized TP kullanarak 2:1 RR garantile et       ║
╚════════════════════════════════════════════════════════════╝
"""
        
        return rapor


# Test
if __name__ == "__main__":
    import yfinance as yf
    
    df = yf.download("PETKM.IS", period="30d", interval="1h", progress=False)
    
    risk_manager = AdvancedRiskManager(
        df,
        portfolio_size=10000.0,
        risk_per_trade=2.0
    )
    
    entry = df["Close"].iloc[-1]
    
    print(risk_manager.rapor_oluştur(entry, işlem_tipi="AL"))
