"""
Real Trading Engine - Nest Integration
=======================================
Mock Trading'den Gerçek Trading'e Geçiş
"""

import logging
from typing import Optional, Dict
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RealTradePosition:
    """Nest'te açılan gerçek pozisyon"""
    symbol: str
    order_type: str  # BUY / SELL
    quantity: float
    entry_price: float
    nest_order_id: str
    entry_time: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: str = "PENDING"  # PENDING, EXECUTED, FILLED, CANCELLED, ERROR


class RealTradingEngine:
    """Nest API üzerinden gerçek trading"""
    
    def __init__(self, nest_client):
        """
        Args:
            nest_client: NestTradingClient instance
        """
        self.client = nest_client
        self.positions: Dict[str, RealTradePosition] = {}
        self.trade_log = []
        
    def place_market_order(
        self,
        symbol: str,
        order_type: str,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Optional[RealTradePosition]:
        """
        Market emirini ver
        
        Args:
            symbol: Hisse (ör: "SISE")
            order_type: "BUY" veya "SELL"
            quantity: Adet
            stop_loss: Otomatik SL (ayrı emir ile yapılabilir)
            take_profit: Otomatik TP (ayrı emir ile yapılabilir)
        """
        
        try:
            # Nest'e MARKET emirini gönder
            response = self.client.place_order(
                symbol=symbol,
                order_type=order_type,
                quantity=quantity,
                order_kind="MARKET"
            )
            
            if "error" in response:
                logger.error(f"❌ Order failed: {response['error']}")
                return None
            
            order_id = response.get("order_id")
            
            # Position oluştur ve track et
            position = RealTradePosition(
                symbol=symbol,
                order_type=order_type,
                quantity=quantity,
                entry_price=response.get("filled_price", 0),  # Doldurulduktan sonra
                nest_order_id=order_id,
                entry_time=datetime.now().isoformat(),
                stop_loss=stop_loss,
                take_profit=take_profit,
                status="EXECUTED"
            )
            
            self.positions[order_id] = position
            
            # Log
            self.trade_log.append({
                "type": "OPEN",
                "symbol": symbol,
                "order_type": order_type,
                "quantity": quantity,
                "order_id": order_id,
                "timestamp": datetime.now().isoformat(),
                "status": "SUCCESS"
            })
            
            logger.info(
                f"✅ REAL TRADE: {order_type} × {quantity} {symbol} "
                f"| Order ID: {order_id}"
            )
            
            return position
        
        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return None
    
    def place_limit_order(
        self,
        symbol: str,
        order_type: str,
        quantity: float,
        limit_price: float
    ) -> Optional[RealTradePosition]:
        """
        Limit emirini ver (fiyat limitli)
        
        İyi fiyattan almak için: BUY limit price < market price
        """
        
        try:
            response = self.client.place_order(
                symbol=symbol,
                order_type=order_type,
                quantity=quantity,
                order_kind="LIMIT",
                price=limit_price
            )
            
            if "error" in response:
                logger.error(f"❌ Limit order failed: {response['error']}")
                return None
            
            order_id = response.get("order_id")
            
            position = RealTradePosition(
                symbol=symbol,
                order_type=order_type,
                quantity=quantity,
                entry_price=limit_price,
                nest_order_id=order_id,
                entry_time=datetime.now().isoformat(),
                status="PENDING"
            )
            
            self.positions[order_id] = position
            
            logger.info(
                f"⏳ LIMIT ORDER: {order_type} × {quantity} {symbol} @ {limit_price} "
                f"| Bekleniyor..."
            )
            
            return position
        
        except Exception as e:
            logger.error(f"❌ Error placing limit order: {e}")
            return None
    
    def close_position(self, order_id: str) -> Optional[Dict]:
        """
        Position'ı kapat (ters emir ver)
        
        Örnek:
        - Açtık: BUY 10 SISE
        - Kapatmak için: SELL 10 SISE
        """
        
        position = self.positions.get(order_id)
        if not position:
            logger.warning(f"Position {order_id} bulunamadı")
            return None
        
        # Ters emir tipi
        reverse_type = "SELL" if position.order_type == "BUY" else "BUY"
        
        try:
            close_response = self.client.place_order(
                symbol=position.symbol,
                order_type=reverse_type,
                quantity=position.quantity,
                order_kind="MARKET"
            )
            
            if "error" in close_response:
                logger.error(f"❌ Close order failed: {close_response['error']}")
                return None
            
            exit_price = close_response.get("filled_price", 0)
            
            # PnL hesabı
            if position.order_type == "BUY":
                pnl = (exit_price - position.entry_price) * position.quantity
            else:  # SELL
                pnl = (position.entry_price - exit_price) * position.quantity
            
            # Log
            self.trade_log.append({
                "type": "CLOSE",
                "symbol": position.symbol,
                "open_order_id": order_id,
                "close_order_id": close_response.get("order_id"),
                "entry_price": position.entry_price,
                "exit_price": exit_price,
                "quantity": position.quantity,
                "pnl": round(pnl, 2),
                "timestamp": datetime.now().isoformat(),
                "status": "SUCCESS"
            })
            
            status_emoji = "✅" if pnl > 0 else "❌" if pnl < 0 else "⚪"
            logger.info(
                f"{status_emoji} POSITION KAPALANDI: {position.symbol} "
                f"| Entry: {position.entry_price:.2f} → Exit: {exit_price:.2f} "
                f"| PnL: {pnl:.2f} TL"
            )
            
            return {
                "order_id": order_id,
                "symbol": position.symbol,
                "entry_price": position.entry_price,
                "exit_price": exit_price,
                "quantity": position.quantity,
                "pnl": pnl
            }
        
        except Exception as e:
            logger.error(f"❌ Error closing position: {e}")
            return None
    
    def get_portfolio_snapshot(self) -> Dict:
        """Portföy durumunu gel"""
        
        # Nest'ten güncel pozisyonları al
        try:
            nest_positions = self.client.get_positions()
            nest_balance = self.client.get_balance()
        except Exception as e:
            logger.warning(f"Nest data fetch error: {e}")
            nest_positions = []
            nest_balance = {}
        
        return {
            "cash_balance": nest_balance.get("cash", 0),
            "positions": [
                {
                    "symbol": p.get("symbol"),
                    "quantity": p.get("quantity"),
                    "avg_price": p.get("avg_price"),
                    "current_price": p.get("current_price"),
                    "unrealized_pnl": p.get("unrealized_pnl")
                }
                for p in nest_positions
            ],
            "timestamp": datetime.now().isoformat(),
            "trade_log_recent": self.trade_log[-5:] if self.trade_log else []
        }


# ============================================================================
# MOCK vs REAL SWITCHING
# ============================================================================

class TradingEngineFactory:
    """Mock ve Real engine'i seçer"""
    
    @staticmethod
    def create(mode: str = "mock", **kwargs):
        """
        Args:
            mode: "mock" veya "real"
            kwargs: Engine'e geçilecek parametreler
        """
        
        if mode.lower() == "mock":
            from trading_engine import MockTradingEngine, TradingRiskConfig
            config = kwargs.get("config", TradingRiskConfig())
            return MockTradingEngine(config)
        
        elif mode.lower() == "real":
            from NEST_INTEGRATION_GUIDE import NestTradingClient
            
            api_key = kwargs.get("api_key")
            api_secret = kwargs.get("api_secret")
            
            if not api_key or not api_secret:
                raise ValueError("Real mode için api_key ve api_secret gerekli")
            
            client = NestTradingClient(api_key, api_secret)
            return RealTradingEngine(client)
        
        else:
            raise ValueError(f"Unknown mode: {mode}")


# ============================================================================
# ÖRNEK: Mock'tan Real'e Geçiş
# ============================================================================

if __name__ == "__main__":
    import os
    
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*70)
    print("TEST: Mock vs Real Trading Engine")
    print("="*70)
    
    # MODE 1: MOCK (Test)
    print("\n\n📝 MODE 1: MOCK TRADING")
    print("-" * 70)
    
    mock_engine = TradingEngineFactory.create("mock")
    print("✅ Mock engine başlatıldı (5000 TL sanal portföy)")
    print(f"Status: {mock_engine.get_status()}")
    
    # MODE 2: REAL (Nest'e bağlı)
    print("\n\n💰 MODE 2: REAL TRADING (Nest)")
    print("-" * 70)
    print("""
    Real mode'u test etmek için:
    
    1. API Credentials'ı Nest'ten al
    2. Environment variables set et:
       
       PowerShell:
       $env:NEST_API_KEY = "your_key"
       $env:NEST_API_SECRET = "your_secret"
    
    3. Real engine'i başlat:
       
       real_engine = TradingEngineFactory.create(
           "real",
           api_key=os.getenv("NEST_API_KEY"),
           api_secret=os.getenv("NEST_API_SECRET")
       )
    
    4. İlk order'u ver:
       
       position = real_engine.place_market_order(
           symbol="SISE",
           order_type="BUY",
           quantity=10
       )
    """)
    
    print("\n" + "="*70)

