"""
Trading Engine - Mock Trading + Risk Management
==============================================
Sanal portföy ile AL/SAT işlemleri
Risk yönetimi: Position Sizing, R/R Hesabı
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class TradingRiskConfig:
    """Risk yönetimi konfigürasyonu"""
    portfolio_size: float = 1000.0  # Başlangıç portföy (TL)
    risk_per_trade: float = 2.0  # Her trade'de riske atılan % (default 2%)
    min_rr_ratio: float = 1.0  # Minimum R/R oranı (1:1 en düşük)
    max_position_size: float = 5.0  # Maksimum pozisyon (TL) - limit
    

@dataclass
class TradeSignal:
    """Bot'tan gelen sinyal"""
    symbol: str
    signal_type: str  # "AL" veya "SAT"
    entry_price: float
    confidence: float  # 0-100%
    market_trend: str  # "TREND", "NÖTR", "ZAYIF"
    timestamp: str
    

@dataclass
class Position:
    """Açık pozisyon"""
    id: int
    symbol: str
    signal_type: str  # AL veya SAT
    entry_price: float
    entry_time: str
    quantity: float
    risk_amount: float  # Riske atılan TL
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: str = "AÇIK"  # AÇIK, KÂPALI
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    pnl: float = 0.0
    

class RiskManager:
    """Risk yönetimi ve position sizing"""
    
    def __init__(self, config: TradingRiskConfig = None):
        self.config = config or TradingRiskConfig()
        self.current_portfolio = self.config.portfolio_size
        self.positions: List[Position] = []
        self.position_counter = 0
        
    def calculate_position_size(
        self, 
        entry_price: float,
        stop_loss: float,
        target_price: float,
        current_portfolio: float
    ) -> Dict:
        """
        Position sizing hesabı
        
        Risk: |entry - stop| × quantity = max risk (portföy % kadarı)
        Target: target - entry
        R/R: target / risk
        """
        
        # Risk miktarı (TL cinsinden)
        risk_tl = (current_portfolio * self.config.risk_per_trade) / 100
        
        # Stop loss mesafesi
        sl_distance = abs(entry_price - stop_loss)
        
        if sl_distance == 0:
            return {"error": "Stop Loss, Entry ile aynı olamaz"}
        
        # Lotlama hesabı (her lotta kaç adet al)
        quantity = risk_tl / sl_distance
        
        # Maksimum pozisyon kontrolü
        position_value = entry_price * quantity
        if position_value > self.config.max_position_size * 100:
            quantity = (self.config.max_position_size * 100) / entry_price
        
        # Target mesafesi (kazanç)
        target_distance = abs(target_price - entry_price)
        
        # R/R oranı
        rr_ratio = target_distance / sl_distance if sl_distance > 0 else 0
        
        # Kazanç potansiyeli (TL)
        profit_potential = target_distance * quantity
        
        # R/R kontrolü
        accept_trade = rr_ratio >= self.config.min_rr_ratio
        
        return {
            "quantity": round(quantity, 2),
            "position_value": round(position_value, 2),
            "risk_tl": round(risk_tl, 2),
            "sl_distance": round(sl_distance, 4),
            "target_distance": round(target_distance, 4),
            "rr_ratio": round(rr_ratio, 2),
            "profit_potential": round(profit_potential, 2),
            "accept_trade": accept_trade,
            "reason": "✅ R/R iyi" if accept_trade else f"❌ R/R düşük ({rr_ratio:.2f}:1)"
        }
    
    def create_position(
        self,
        signal: TradeSignal,
        stop_loss: float,
        take_profit: float
    ) -> Optional[Position]:
        """
        Position açma (position sizing ile)
        """
        
        # Risk hesabı
        risk_calc = self.calculate_position_size(
            entry_price=signal.entry_price,
            stop_loss=stop_loss,
            target_price=take_profit,
            current_portfolio=self.current_portfolio
        )
        
        if "error" in risk_calc:
            logger.warning(f"Position açılamadı: {risk_calc['error']}")
            return None
        
        if not risk_calc["accept_trade"]:
            logger.info(f"Trade reddedildi ({signal.symbol}): {risk_calc['reason']}")
            return None
        
        # Position oluştur
        self.position_counter += 1
        position = Position(
            id=self.position_counter,
            symbol=signal.symbol,
            signal_type=signal.signal_type,
            entry_price=signal.entry_price,
            entry_time=signal.timestamp,
            quantity=risk_calc["quantity"],
            risk_amount=risk_calc["risk_tl"],
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions.append(position)
        
        logger.info(
            f"✅ Position açıldı: {signal.symbol} "
            f"| {signal.signal_type} × {risk_calc['quantity']:.2f} "
            f"| Entry: {signal.entry_price} | SL: {stop_loss} | TP: {take_profit} "
            f"| R/R: {risk_calc['rr_ratio']:.2f}:1"
        )
        
        return position
    
    def close_position(
        self,
        position_id: int,
        exit_price: float,
        exit_time: str
    ) -> Optional[Position]:
        """
        Position kapatma ve PnL hesabı
        """
        
        position = next((p for p in self.positions if p.id == position_id), None)
        
        if not position:
            logger.warning(f"Position {position_id} bulunamadı")
            return None
        
        if position.status == "KÂPALI":
            logger.warning(f"Position {position_id} zaten kapalı")
            return None
        
        # PnL hesabı
        if position.signal_type == "AL":
            pnl = (exit_price - position.entry_price) * position.quantity
        else:  # SAT
            pnl = (position.entry_price - exit_price) * position.quantity
        
        # Pozisyonu güncelle
        position.exit_price = exit_price
        position.exit_time = exit_time
        position.pnl = round(pnl, 2)
        position.status = "KÂPALI"
        
        # Portföy güncelle
        self.current_portfolio += pnl
        
        status_emoji = "✅" if pnl > 0 else "❌" if pnl < 0 else "⚪"
        logger.info(
            f"{status_emoji} Position kapalı: {position.symbol} "
            f"| Exit: {exit_price} | PnL: {pnl:.2f} TL | "
            f"Portföy: {self.current_portfolio:.2f} TL"
        )
        
        return position
    
    def get_portfolio_status(self) -> Dict:
        """Portföy durumunu getir"""
        
        open_positions = [p for p in self.positions if p.status == "AÇIK"]
        closed_positions = [p for p in self.positions if p.status == "KÂPALI"]
        
        total_pnl = sum(p.pnl for p in closed_positions)
        open_risk = sum(p.risk_amount for p in open_positions)
        
        return {
            "starting_portfolio": self.config.portfolio_size,
            "current_portfolio": round(self.current_portfolio, 2),
            "total_pnl": round(total_pnl, 2),
            "pnl_percent": round((total_pnl / self.config.portfolio_size) * 100, 2),
            "open_positions_count": len(open_positions),
            "closed_positions_count": len(closed_positions),
            "open_risk_tl": round(open_risk, 2),
            "open_risk_percent": round((open_risk / self.current_portfolio) * 100, 2),
        }
    
    def save_to_file(self, filepath: str = "mock_trades.json"):
        """Tüm işlemleri dosyaya kaydet"""
        
        data = {
            "config": asdict(self.config),
            "portfolio_status": self.get_portfolio_status(),
            "positions": [asdict(p) for p in self.positions]
        }
        
        Path(filepath).write_text(json.dumps(data, indent=2, ensure_ascii=False))
        logger.info(f"Mock trades kaydedildi: {filepath}")


class MockTradingEngine:
    """Mock Trading Motoru"""
    
    def __init__(self, risk_config: TradingRiskConfig = None):
        self.risk_manager = RiskManager(risk_config)
        self.logger = logger
        
    def process_signal(
        self,
        signal: TradeSignal,
        stop_loss: float,
        take_profit: float
    ) -> Optional[Position]:
        """
        Sinyali işle ve position aç
        """
        
        # Enter şartları kontrol et
        if signal.confidence < 50:
            self.logger.info(f"❌ Sinyal yetersiz güven: {signal.confidence}%")
            return None
        
        # Position açmaya çalış
        position = self.risk_manager.create_position(signal, stop_loss, take_profit)
        
        return position
    
    def get_status(self) -> Dict:
        """Bot durumu"""
        return self.risk_manager.get_portfolio_status()


# TEST
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Risk konfigürasyonu
    config = TradingRiskConfig(
        portfolio_size=1000.0,
        risk_per_trade=2.0,  # Her trade'de %2 risk
        min_rr_ratio=1.0
    )
    
    engine = MockTradingEngine(config)
    
    # Test sinyal 1
    signal1 = TradeSignal(
        symbol="SISE.IS",
        signal_type="AL",
        entry_price=50.0,
        confidence=75,
        market_trend="TREND",
        timestamp=datetime.now().isoformat()
    )
    
    # SL: 49 TL (risk 1 TL/adet)
    # TP: 52 TL (kazanç 2 TL/adet) - R/R = 1:2
    pos1 = engine.process_signal(signal1, stop_loss=49.0, take_profit=52.0)
    
    if pos1:
        print(f"\n✅ Position açıldı:")
        print(f"   Portföy: {engine.get_status()['current_portfolio']} TL")
        
        # Pozisyonu kapattığımızı düşün
        # Exit fiyatı: 51.5 TL (kazanç)
        result = engine.risk_manager.close_position(pos1.id, 51.5, datetime.now().isoformat())
        
        print(f"\n✅ Position kapalı:")
        print(f"   PnL: {result.pnl} TL")
        print(f"   Portföy: {engine.get_status()['current_portfolio']} TL")
    
    print(f"\n📊 PORTFÖY DURUMU:")
    status = engine.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Dosyaya kaydet
    engine.risk_manager.save_to_file()
