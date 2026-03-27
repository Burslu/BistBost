"""
Signal Executor - Bot Sinyallerini Trading'e Çevir
==================================================
Bot → Signal → Trading Engine → Mock Position
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class SignalExecutor:
    """
    Bot'tan gelen sinyali analiz edip
    Trading engine'e gönder
    """
    
    def __init__(self, trading_engine, confidence_threshold: float = 50):
        self.engine = trading_engine
        self.confidence_threshold = confidence_threshold
        self.executed_signals: List[Dict] = []
        
    def execute_from_analyzer_signal(
        self,
        symbol: str,
        sinyal_tipi: str,  # "AL" / "SAT" / "NÖTR"
        güven: float,  # 0-100
        market_price: float,
        entry_quality: float,  # 0-100
        momentum: float,  # 0-100
        volatilite: float,  # % ATR
        haber_sentiment: float,  # -1 to +1
        haber_text: str = "",
        market_trend: str = "NÖTR",
        quantity: int = 10  # 🆕 Dinamik position size
    ) -> Optional[Dict]:
        """
        RealTimeAnalyzer'dan gelen sinyali işle
        
        Sinyal Tipi:
        - "GÜÇLÜ AL": entry_quality > 70 + güven > 60
        - "AL": entry_quality > 40 + güven > 50
        - "SAT": reverse
        - Else: "NÖTR"
        """
        
        # 1. Sinyal tipini belirle
        if sinyal_tipi == "NÖTR" or güven < self.confidence_threshold:
            logger.debug(f"❌ {symbol}: Sinyal yetersiz (güven: {güven}%)")
            return None
        
        # 2. Stop Loss & Take Profit hesabı
        # Volatilite bazlı SL/TP
        atr_multiplier = volatilite / 100.0
        
        if sinyal_tipi in ["GÜÇLÜ AL", "AL"]:
            # Alış için
            stop_loss = market_price * (1 - atr_multiplier)
            take_profit = market_price * (1 + atr_multiplier * 1.5)  # 1.5x untuk higher TP
            trade_type = "AL"
            
        elif sinyal_tipi in ["GÜÇLÜ SAT", "SAT", "ZAYIF SAT"]:
            # Satış için
            stop_loss = market_price * (1 + atr_multiplier)
            take_profit = market_price * (1 - atr_multiplier * 1.5)
            trade_type = "SAT"
            
        else:
            return None
        
        # 3. Trading Engine'de position aç
        from trading_engine import TradeSignal
        
        # Engine tipini kontrol et
        is_real_engine = hasattr(self.engine, 'client')  # RealTradingEngine'in client attribute'ı var
        
        if is_real_engine:
            # REAL TRADING (Nest API)
            position = self.engine.place_market_order(
                symbol=symbol,
                order_type=trade_type,
                quantity=quantity,  # 🆕 Dinamik position size
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if position:
                exec_record = {
                    "position_id": position.nest_order_id,
                    "symbol": symbol,
                    "type": trade_type,
                    "entry_price": market_price,
                    "entry_quality": entry_quality,
                    "confidence": güven,
                    "momentum": momentum,
                    "volatilite": volatilite,
                    "haber_sentiment": haber_sentiment,
                    "haber_text": haber_text,
                    "stop_loss": position.stop_loss,
                    "take_profit": position.take_profit,
                    "quantity": position.quantity,
                    "timestamp": datetime.now().isoformat(),
                    "mode": "REAL"
                }
        else:
            # MOCK TRADING
            signal = TradeSignal(
                symbol=symbol,
                signal_type=trade_type,
                entry_price=market_price,
                confidence=güven,
                market_trend=market_trend,
                timestamp=datetime.now().isoformat()
            )
            
            position = self.engine.process_signal(
                signal=signal,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if position:
                exec_record = {
                    "position_id": position.id,
                    "symbol": symbol,
                    "type": trade_type,
                    "entry_price": market_price,
                    "entry_quality": entry_quality,
                    "confidence": güven,
                    "momentum": momentum,
                    "volatilite": volatilite,
                    "haber_sentiment": haber_sentiment,
                    "haber_text": haber_text,
                    "stop_loss": position.stop_loss,
                    "take_profit": position.take_profit,
                    "quantity": position.quantity,
                    "timestamp": datetime.now().isoformat(),
                    "mode": "MOCK"
                }
            else:
                return None
        
        self.executed_signals.append(exec_record)
        
        logger.info(
            f"🚀 TRADE EXECUTED: {symbol} {trade_type} "
            f"× {position.quantity:.2f} @ {market_price} "
            f"(Güven: {güven}%, EQ: {entry_quality}%)"
        )
        
        return exec_record
    
    def get_open_positions_summary(self) -> Dict:
        """Açık pozisyonları göster"""
        
        portfolio = self.engine.get_status()
        open_positions = [p for p in self.engine.risk_manager.positions if p.status == "AÇIK"]
        
        summary = {
            "portfolio_status": portfolio,
            "open_positions": [
                {
                    "id": p.id,
                    "symbol": p.symbol,
                    "type": p.signal_type,
                    "entry": p.entry_price,
                    "quantity": p.quantity,
                    "sl": p.stop_loss,
                    "tp": p.take_profit,
                    "risk_tl": p.risk_amount
                }
                for p in open_positions
            ]
        }
        
        return summary
    
    def save_execution_log(self, filepath: str = "execution_log.json"):
        """Execution log'u kaydet"""
        
        data = {
            "executed_signals": self.executed_signals,
            "portfolio": self.engine.get_status(),
            "timestamp": datetime.now().isoformat()
        }
        
        Path(filepath).write_text(json.dumps(data, indent=2, ensure_ascii=False))
        logger.info(f"Execution log kaydedildi: {filepath}")


class MockTradeMonitor:
    """
    Açık pozisyonları monitorla
    Fake price updates ile position kapat
    """
    
    def __init__(self, signal_executor: SignalExecutor):
        self.executor = signal_executor
        
    def simulate_price_update(self, symbol: str, new_price: float):
        """
        Simüle ederek yeni fiyat ile kontrol et
        SL/TP hit oldu mu?
        """
        
        engine = self.executor.engine
        open_positions = [p for p in engine.risk_manager.positions 
                         if p.status == "AÇIK" and p.symbol == symbol]
        
        for position in open_positions:
            exit_triggered = False
            exit_reason = None
            
            if position.signal_type == "AL":
                # Alış pozisyonu
                if new_price <= position.stop_loss:
                    exit_triggered = True
                    exit_reason = f"SL HIT ({position.stop_loss})"
                elif new_price >= position.take_profit:
                    exit_triggered = True
                    exit_reason = f"TP HIT ({position.take_profit})"
                    
            else:  # SAT
                # Satış pozisyonu
                if new_price >= position.stop_loss:
                    exit_triggered = True
                    exit_reason = f"SL HIT ({position.stop_loss})"
                elif new_price <= position.take_profit:
                    exit_triggered = True
                    exit_reason = f"TP HIT ({position.take_profit})"
            
            if exit_triggered:
                logger.info(f"📊 {exit_reason} → Position kapatılıyor")
                engine.risk_manager.close_position(
                    position.id,
                    new_price,
                    datetime.now().isoformat()
                )


# TEST
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    from trading_engine import MockTradingEngine, TradingRiskConfig
    
    # Mock engine başlat
    config = TradingRiskConfig(portfolio_size=5000, risk_per_trade=2)
    engine = MockTradingEngine(config)
    executor = SignalExecutor(engine)
    monitor = MockTradeMonitor(executor)
    
    print("=" * 60)
    print("TEST: Bot Signal → Mock Trade Execution")
    print("=" * 60)
    
    # Simule et: Bot sinyali geldi
    print("\n📡 Bot SINYALI: THYAO.IS")
    sig1 = executor.execute_from_analyzer_signal(
        symbol="THYAO.IS",
        sinyal_tipi="AL",
        güven=75,
        market_price=120.50,
        entry_quality=82,
        momentum=65,
        volatilite=2.5,
        haber_sentiment=0.3,
        haber_text="İyi kazançlar, yatırımcı güveni artıyor",
        market_trend="TREND"
    )
    
    if sig1:
        print(f"\n{json.dumps(sig1, indent=2, ensure_ascii=False)}")
        
        # Monitor: Fiyat hareketi simüle et
        print("\n📈 Simülasyon: Fiyat 121.20 oldu")
        monitor.simulate_price_update("THYAO.IS", 121.20)
        
        print("\n📈 Simülasyon: Fiyat 123.00 oldu (TP çarptı)")
        monitor.simulate_price_update("THYAO.IS", 123.00)
    
    # Özet
    print("\n" + "=" * 60)
    print("PORTFÖY ÖZETI")
    print("=" * 60)
    status = executor.get_open_positions_summary()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    executor.save_execution_log()
