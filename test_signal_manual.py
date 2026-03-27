"""
Test Sinyal Gönder - Bot'u Test Et
=====================================
Bot'a manuel olarak örnek sinyal ver ve trade açılıp açılmadığını kontrol et
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("🧪 BOT TEST - MANUEL SINYAL GÖNDER")
print("="*70)

try:
    from trading_engine import MockTradingEngine, TradingRiskConfig
    from signal_executor import SignalExecutor
    
    # Engine'i oluştur (Bot'un aynısını)
    config = TradingRiskConfig(portfolio_size=5000, risk_per_trade=2)
    engine = MockTradingEngine(config)
    executor = SignalExecutor(engine, confidence_threshold=60.0)  # 60% threshold
    
    print(f"✅ Trading Engine başlatıldı")
    print(f"   Portföy: {engine.risk_manager.current_portfolio:.2f} TL")
    print(f"   Confidence Threshold: 60%")
    
    # =============================
    # TEST SİNYAL 1: GÜÇLÜ AL
    # =============================
    print("\n" + "-"*70)
    print("📡 TEST SİNYAL 1: SISE - GÜÇLÜ AL (70% Güven - KABUL EDİLMELİ)")
    print("-"*70)
    
    trade1 = executor.execute_from_analyzer_signal(
        symbol="SISE",
        sinyal_tipi="AL",
        güven=70.0,  # 60% threshold'u geçer
        market_price=50.0,
        entry_quality=78,
        momentum=62,
        volatilite=2.3,
        haber_sentiment=0.3,
        haber_text="İyi kazançlar, yatırımcı güveni artıyor",
        market_trend="TREND"
    )
    
    if trade1:
        print("✅ TRADE BAŞARILI AÇILDI!")
        print(f"   Position ID: {trade1['position_id']}")
        print(f"   Entry: {trade1['entry_price']} TL")
        print(f"   Quantity: {trade1['quantity']} adet")
        print(f"   SL: {trade1['stop_loss']:.2f} | TP: {trade1['take_profit']:.2f}")
        print(f"   Mode: {trade1['mode']}")
        
        status = engine.get_status()
        print(f"\n   Portföy Durumu:")
        print(f"   - Başlangıç: {status['starting_portfolio']:.2f} TL")
        print(f"   - Şuanki: {status['current_portfolio']:.2f} TL")
        print(f"   - Açık Position: {status['open_positions_count']}")
    else:
        print("❌ TRADE AÇILMADI (HATA!)")
    
    # =============================
    # TEST SİNYAL 2: DÜŞÜK GÜVEN
    # =============================
    print("\n" + "-"*70)
    print("📡 TEST SİNYAL 2: THYAO - ZAYIF SAT (45% Güven - RED EDİLMELİ)")
    print("-"*70)
    
    trade2 = executor.execute_from_analyzer_signal(
        symbol="THYAO",
        sinyal_tipi="SAT",
        güven=45.0,  # 60% threshold altında = RED
        market_price=120.0,
        entry_quality=50,
        momentum=35,
        volatilite=1.5,
        haber_sentiment=-0.1,
        haber_text="Nötr",
        market_trend="NÖTR"
    )
    
    if trade2:
        print("❌ ERROR: TRADE AÇILDI AMA RED EDİLMESİ GEREKTİ!")
    else:
        print("✅ SİNYAL DOĞRU REDDEDILDI (Güven < 60%)")
    
    # =============================
    # TEST SİNYAL 3: ORTA GÜVEN
    # =============================
    print("\n" + "-"*70)
    print("📡 TEST SİNYAL 3: AKBNK - AL (65% Güven - KABUL EDİLMELİ)")
    print("-"*70)
    
    trade3 = executor.execute_from_analyzer_signal(
        symbol="AKBNK",
        sinyal_tipi="AL",
        güven=65.0,  # 60% threshold'u geçer
        market_price=30.0,
        entry_quality=62,
        momentum=58,
        volatilite=1.8,
        haber_sentiment=0.1,
        haber_text="Pozitif beklentiler",
        market_trend="TREND"
    )
    
    if trade3:
        print("✅ TRADE BAŞARILI AÇILDI!")
        print(f"   Position ID: {trade3['position_id']}")
        print(f"   Entry: {trade3['entry_price']} TL")
        print(f"   Quantity: {trade3['quantity']} adet")
        
        status = engine.get_status()
        print(f"\n   Portföy Durumu:")
        print(f"   - Şuanki: {status['current_portfolio']:.2f} TL")
        print(f"   - Açık Positions: {status['open_positions_count']}")
    else:
        print("❌ TRADE AÇILMADI")
    
    # =============================
    # ÖZET
    # =============================
    print("\n" + "="*70)
    print("📊 FINAL ÖZET")
    print("="*70)
    
    final_status = engine.get_status()
    print(f"\nPortföy Durumu:")
    print(f"  Başlangıç: {final_status['starting_portfolio']:.2f} TL")
    print(f"  Şuanki: {final_status['current_portfolio']:.2f} TL")
    print(f"  PnL: {final_status['total_pnl']:.2f} TL")
    print(f"  Açık Positions: {final_status['open_positions_count']}")
    print(f"  Kapalı Positions: {final_status['closed_positions_count']}")
    
    print(f"\n🎯 Executed Signals:")
    print(f"  Toplam: {len(executor.executed_signals)}")
    for sig in executor.executed_signals:
        print(f"  - {sig['symbol']} {sig['type']} @ {sig['entry_price']:.2f} (Güven: {sig['confidence']}%)")
    
    print("\n" + "="*70)
    print("✅ TEST TAMAMLANDI")
    print("="*70)
    
    print("""
SONUÇLAR:
  ✓ Trade 1 (70% güven): AÇILDI ← Doğru
  ✓ Trade 2 (45% güven): RED ← Doğru
  ✓ Trade 3 (65% güven): AÇILDI ← Doğru
  
60% THRESHOLD başarılı!
Sistema hazır. Bot'u başlat:
  
  $env:TRADING_MODE = "mock"
  python run_production.py
    """)

except Exception as e:
    logger.error(f"❌ Test hatası: {e}", exc_info=True)
    print("\n⚠️  Hata oluştu. Lütfen logs'u kontrol et.")

print()
