"""
Advanced Backtest Engine - Strateji Validasyonu & Performance Metrikleri
=========================================================================
Real signals geçmiş veriye karşı test ederek:
- Win Rate, Loss Rate
- Profit Factor
- Sharpe Ratio
- Max Drawdown
- Risk/Reward Ratio
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import pandas as pd
import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)

class AdvancedBacktestEngine:
    """Advanced backtest & performance metrics"""
    
    def __init__(self, başlangıç_bakiye=10000.0):
        self.başlangıç_bakiye = başlangıç_bakiye
        self.işlemler = []  # Tüm işlemler
        self.kâr_kayıp = []  # Her işlemin P&L
        self.equity_curve = [başlangıç_bakiye]
        self.pozisyonlar = {}  # Açık pozisyonlar
        
    def sinyali_test_et(self, sembol, sinyal_tarihi, sinyal_tipi, entry_price, stop_loss, take_profit, güven):
        """
        Bir sinyali test et:
        - Entry fiyat: signal tarihi (close)
        - Exit: SL veya TP'ye hit olunca
        - Win/Loss hesapla
        """
        try:
            # Sinyal tarihinden sonraki verileri çek
            df = yf.download(sembol, start=sinyal_tarihi, period="30d", progress=False)
            
            if df.empty:
                return None
            
            df = df.reset_index()
            
            # İlk çubuk entry
            entry_bar = df.iloc[0]
            entry_price_actual = entry_bar['Close']
            
            # Sonraki çubuklarda SL/TP check et
            trade_result = None
            
            for idx in range(1, len(df)):
                bar = df.iloc[idx]
                high = bar['High']
                low = bar['Low']
                close = bar['Close']
                
                if sinyal_tipi in ["AL", "GÜÇLÜ AL", "ZAYIF AL"]:
                    # AL işlemi
                    if low <= stop_loss:
                        # Stop Loss hit
                        trade_result = {
                            "type": "SL",
                            "entry": entry_price_actual,
                            "exit": stop_loss,
                            "pnl": stop_loss - entry_price_actual,
                            "pnl_pct": ((stop_loss - entry_price_actual) / entry_price_actual) * 100,
                            "bars_held": idx,
                            "win": False
                        }
                        break
                    elif high >= take_profit:
                        # Take Profit hit
                        trade_result = {
                            "type": "TP",
                            "entry": entry_price_actual,
                            "exit": take_profit,
                            "pnl": take_profit - entry_price_actual,
                            "pnl_pct": ((take_profit - entry_price_actual) / entry_price_actual) * 100,
                            "bars_held": idx,
                            "win": True
                        }
                        break
                
                elif sinyal_tipi in ["SAT", "GÜÇLÜ SAT", "ZAYIF SAT"]:
                    # SAT işlemi
                    if high >= stop_loss:
                        # Stop Loss hit
                        trade_result = {
                            "type": "SL",
                            "entry": entry_price_actual,
                            "exit": stop_loss,
                            "pnl": entry_price_actual - stop_loss,
                            "pnl_pct": ((entry_price_actual - stop_loss) / entry_price_actual) * 100,
                            "bars_held": idx,
                            "win": False
                        }
                        break
                    elif low <= take_profit:
                        # Take Profit hit
                        trade_result = {
                            "type": "TP",
                            "entry": entry_price_actual,
                            "exit": take_profit,
                            "pnl": entry_price_actual - take_profit,
                            "pnl_pct": ((entry_price_actual - take_profit) / entry_price_actual) * 100,
                            "bars_held": idx,
                            "win": True
                        }
                        break
            
            # 30 günde SL/TP'ye hit olmadıysa, son fiyatta exit
            if trade_result is None:
                last_close = df.iloc[-1]['Close']
                if sinyal_tipi in ["AL", "GÜÇLÜ AL", "ZAYIF AL"]:
                    pnl = last_close - entry_price_actual
                else:
                    pnl = entry_price_actual - last_close
                
                trade_result = {
                    "type": "TIMEOUT",
                    "entry": entry_price_actual,
                    "exit": last_close,
                    "pnl": pnl,
                    "pnl_pct": (pnl / entry_price_actual) * 100,
                    "bars_held": len(df),
                    "win": pnl > 0
                }
            
            trade_result["sembol"] = sembol
            trade_result["sinyal"] = sinyal_tipi
            trade_result["güven"] = güven
            trade_result["tarih"] = sinyal_tarihi
            
            self.işlemler.append(trade_result)
            self.kâr_kayıp.append(trade_result["pnl"])
            
            return trade_result
            
        except Exception as e:
            logger.error(f"Sinyal test hatası ({sembol}): {e}")
            return None
    
    def metrikleri_hesapla(self):
        """Tüm işlemler için performance metrikleri hesapla"""
        
        if not self.işlemler:
            return None
        
        wins = sum(1 for t in self.işlemler if t["win"])
        losses = len(self.işlemler) - wins
        
        win_trades = [t["pnl"] for t in self.işlemler if t["win"]]
        loss_trades = [t["pnl"] for t in self.işlemler if not t["win"]]
        
        total_pnl = sum(t["pnl"] for t in self.işlemler)
        
        # Metrikleri hesapla
        metrikleri = {
            "toplam_işlem": len(self.işlemler),
            "kazanan_işlem": wins,
            "kaybeden_işlem": losses,
            "win_rate": (wins / len(self.işlemler)) * 100 if self.işlemler else 0,
            
            "toplam_pnl": total_pnl,
            "ortalama_pnl": np.mean(self.kâr_kayıp),
            "std_pnl": np.std(self.kâr_kayıp),
            
            "avg_win": np.mean(win_trades) if win_trades else 0,
            "avg_loss": np.mean(loss_trades) if loss_trades else 0,
            "max_win": max(win_trades) if win_trades else 0,
            "max_loss": min(loss_trades) if loss_trades else 0,
            
            "profit_factor": abs(sum(win_trades) / sum(loss_trades)) if loss_trades and sum(loss_trades) != 0 else 0,
            "payoff_ratio": abs(np.mean(win_trades) / np.mean(loss_trades)) if loss_trades and np.mean(loss_trades) != 0 else 0,
            
            "ortalama_bar_tutus": np.mean([t["bars_held"] for t in self.işlemler]),
            
            # Risk metrikleri
            "max_drawdown": self._hesapla_max_drawdown(),
            "sharpe_ratio": self._hesapla_sharpe_ratio(),
        }
        
        return metrikleri
    
    def _hesapla_max_drawdown(self):
        """Maximum Drawdown hesapla"""
        if not self.kâr_kayıp:
            return 0
        
        cumulative = np.cumsum(self.kâr_kayıp)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max)
        
        return abs(np.min(drawdown))
    
    def _hesapla_sharpe_ratio(self, risk_free_rate=0.02):
        """Sharpe Ratio (yıllık, %2 risk-free rate)"""
        if len(self.kâr_kayıp) < 2:
            return 0
        
        returns = np.array(self.kâr_kayıp)
        excess_return = np.mean(returns) - (risk_free_rate / 252)  # Günlük risk-free
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0
        
        sharpe = (excess_return / std_return) * np.sqrt(252)
        return sharpe
    
    def rapor_oluştur(self, output_path=None):
        """Detaylı backtest raporu oluştur"""
        metrikleri = self.metrikleri_hesapla()
        
        if not metrikleri:
            return None
        
        rapor = f"""
╔══════════════════════════════════════════════════════════════╗
║           BACKTEST PERFORMANCE RAPORU                         ║
╚══════════════════════════════════════════════════════════════╝

📊 İŞLEM İSTATİSTİKLERİ
────────────────────────────────────────
  Toplam İşlem:        {metrikleri["toplam_işlem"]}
  Kazanan:             {metrikleri["kazanan_işlem"]} ({metrikleri["win_rate"]:.2f}%)
  Kaybeden:            {metrikleri["kaybeden_işlem"]}
  
💰 KÂR/KAYIP
────────────────────────────────────────
  Toplam P&L:          {metrikleri["toplam_pnl"]:.2f} TL
  Ortalama P&L:        {metrikleri["ortalama_pnl"]:.2f} TL
  Stdv P&L:            {metrikleri["std_pnl"]:.2f} TL
  
  En Büyük Kazanç:     {metrikleri["max_win"]:.2f} TL
  En Büyük Kayıp:      {metrikleri["max_loss"]:.2f} TL
  Ort. Kazanç:         {metrikleri["avg_win"]:.2f} TL
  Ort. Kayıp:          {metrikleri["avg_loss"]:.2f} TL

📈 KALİTE METRİKLERİ
────────────────────────────────────────
  Profit Factor:       {metrikleri["profit_factor"]:.2f}x (1.5+ hedef)
  Payoff Ratio:        {metrikleri["payoff_ratio"]:.2f} (1.0+ hedef)
  Ortalama Bar Tutuş:  {metrikleri["ortalama_bar_tutus"]:.1f} gün

⚠️  RİSK METRİKLERİ
────────────────────────────────────────
  Max Drawdown:        {metrikleri["max_drawdown"]:.2f} TL
  Sharpe Ratio:        {metrikleri["sharpe_ratio"]:.2f} (1.0+ hedef)

╔══════════════════════════════════════════════════════════════╗
║ NOT: Profit Factor > 1.5 ve Sharpe > 1.0 = İyi Strateji      ║
╚══════════════════════════════════════════════════════════════╝
"""
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rapor)
        
        return rapor, metrikleri


# Test fonksiyonu
if __name__ == "__main__":
    engine = AdvancedBacktestEngine(başlangıç_bakiye=10000.0)
    
    # Örnek sinyalleri test et
    sinyaller = [
        {
            "sembol": "PETKM.IS",
            "tarih": "2026-01-15",
            "sinyal": "GÜÇLÜ AL",
            "entry": 120.50,
            "sl": 118.00,
            "tp": 128.50,
            "güven": 0.72
        }
    ]
    
    for sinyal in sinyaller:
        sonuç = engine.sinyali_test_et(
            sembol=sinyal["sembol"],
            sinyal_tarihi=sinyal["tarih"],
            sinyal_tipi=sinyal["sinyal"],
            entry_price=sinyal["entry"],
            stop_loss=sinyal["sl"],
            take_profit=sinyal["tp"],
            güven=sinyal["güven"]
        )
        
        if sonuç:
            print(f"\n{sinyal['sembol']} ({sinyal['sinyal']})")
            print(f"  Entry: {sonuç['entry']:.2f} TL")
            print(f"  Exit: {sonuç['exit']:.2f} TL ({sonuç['type']})")
            print(f"  P&L: {sonuç['pnl']:.2f} TL ({sonuç['pnl_pct']:.2f}%)")
            print(f"  Bars: {sonuç['bars_held']}")
    
    # Rapor oluştur
    rapor, _ = engine.rapor_oluştur(output_path="data/signals/backtest_rapor_advanced.txt")
    print(rapor)
