"""
Terminal Test - Bot'u Test Et
============================
Yapay sinyal oluşturarak trading engine'i test et
"""

import sys
sys.path.insert(0, '/content/c/Users/pc/OneDrive/Desktop/BistBot')

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("🧪 BOT TESTING - YAPAY SINYAL İLE TEST")
print("="*70)

# ============================================================================
# TEST 1: EXECUTION LOG KONTROL
# ============================================================================

print("\n\n1️⃣  EXECUTION LOG'U KONTROL ET")
print("-" * 70)

try:
    from pathlib import Path
    import json
    
    log_file = Path("execution_log.json")
    if log_file.exists():
        data = json.loads(log_file.read_text(encoding='utf-8'))
        portfolio = data.get("portfolio", {})
        signals = data.get("executed_signals", [])
        
        print(f"✓ Başlangıç Portföy: {portfolio.get('starting_portfolio', 0):.2f} TL")
        print(f"✓ Şuanki: {portfolio.get('current_portfolio', 0):.2f} TL")
        print(f"✓ Toplam PnL: {portfolio.get('total_pnl', 0):.2f} TL")
        print(f"✓ Açık Positions: {portfolio.get('open_positions_count', 0)}")
        print(f"✓ Kapalı Positions: {portfolio.get('closed_positions_count', 0)}")
        
        if signals:
            print(f"\n✓ Son {min(3, len(signals))} Signal:")
            for sig in signals[-3:]:
                print(f"  - {sig['symbol']} {sig['type']} @ {sig['entry_price']}")
    else:
        print("❌ execution_log.json bulunamadı (henüz trade yok)")
except Exception as e:
    print(f"❌ Hata: {e}")

# ============================================================================
# TEST 2: YAPAY SINYAL İLE TEST
# ============================================================================

print("\n\n2️⃣  YAPAY SINYAL İLE TEST")
print("-" * 70)

try:
    from trading_engine import MockTradingEngine, TradingRiskConfig
    from signal_executor import SignalExecutor
    from datetime import datetime
    
    # Engine oluştur
    config = TradingRiskConfig(portfolio_size=5000, risk_per_trade=2)
    engine = MockTradingEngine(config)
    executor = SignalExecutor(engine)
    
    print(f"✓ Test Engine başlatıldı: {engine.risk_manager.current_portfolio} TL")
    
    # TEST SIGNAL 1: Güçlü AL sinyali
    print("\n📡 TEST SIGNAL 1: SISE AL (75% güven, EQ: 82%)")
    trade1 = executor.execute_from_analyzer_signal(
        symbol="SISE",
        sinyal_tipi="AL",
        güven=75,
        market_price=50.0,
        entry_quality=82,
        momentum=65,
        volatilite=2.5,
        haber_sentiment=0.3,
        haber_text="İyi kazançlar, yatırımcı güveni artıyor",
        market_trend="TREND"
    )
    
    if trade1:
        print(f"✅ TRADE 1 AÇILDI:")
        print(f"   Position ID: {trade1['position_id']}")
        print(f"   Entry: {trade1['entry_price']}")
        print(f"   Qty: {trade1['quantity']}")
        print(f"   Risk: {trade1['risk_amount']} TL")
        porta = engine.get_status()
        print(f"   Portföy: {porta['current_portfolio']:.2f} TL")
    else:
        print("❌ TRADE AÇILMADI (R/R oranı yeterli yok?)")
    
    # TEST SIGNAL 2: Orta AL sinyali
    print("\n📡 TEST SIGNAL 2: THYAO AL (62% güven, EQ: 65%)")
    trade2 = executor.execute_from_analyzer_signal(
        symbol="THYAO",
        sinyal_tipi="AL",
        güven=62,
        market_price=120.0,
        entry_quality=65,
        momentum=45,
        volatilite=1.8,
        haber_sentiment=0.0,
        haber_text="Nötr",
        market_trend="NÖTR"
    )
    
    if trade2:
        print(f"✅ TRADE 2 AÇILDI:")
        print(f"   Position ID: {trade2['position_id']}")
        print(f"   Entry: {trade2['entry_price']}")
        print(f"   Qty: {trade2['quantity']}")
        porta = engine.get_status()
        print(f"   Portföy: {porta['current_portfolio']:.2f} TL")
    else:
        print("❌ TRADE AÇILMADI (R/R oranı yeterli yok?)")
    
    # TEST SIGNAL 3: Zayıf SAT sinyali (REJECT EDİLMELİ)
    print("\n📡 TEST SIGNAL 3: AKBNK SAT (35% güven - REJECTION TEST)")
    trade3 = executor.execute_from_analyzer_signal(
        symbol="AKBNK",
        sinyal_tipi="SAT",
        güven=35,  # < 50% → REJECT
        market_price=30.0,
        entry_quality=40,
        momentum=20,
        volatilite=3.0,
        haber_sentiment=-0.2,
        haber_text="Negatif haber var",
        market_trend="ZAYIF"
    )
    
    if trade3:
        print(f"❌ ERROR: TRADE 3 AÇILDI AMA AÇILMAMALI (Güven < 50%)")
    else:
        print(f"✅ TRADE 3 REJECTİONI BAŞARILI (Güven < 50% - Doğru davranış)")
    
    # PORTFÖY ÖZETI
    print("\n\n📊 PORTFÖY ÖZETI (Test Sonrası)")
    print("-" * 70)
    final_status = engine.get_status()
    print(f"Başlangıç: {final_status['starting_portfolio']:.2f} TL")
    print(f"Şuanki: {final_status['current_portfolio']:.2f} TL")
    print(f"PnL: {final_status['total_pnl']:.2f} TL ({final_status['pnl_percent']:.2f}%)")
    print(f"Açık Positions: {final_status['open_positions_count']}")
    print(f"Kapalı Positions: {final_status['closed_positions_count']}")
    
except Exception as e:
    logger.error(f"❌ Test hatası: {e}", exc_info=True)

# ============================================================================
# TEST 3: CONFIDENCE THRESHOLD AYARI
# ============================================================================

print("\n\n3️⃣  CONFIDENCE THRESHOLD AYAR ÖNERİSİ")
print("-" * 70)

print("""
Bot şu anda >50% güven gerektiriyor. Piyasa sakin olduğu zaman hiçbir 
sinyal açılmaz. Seçenekler:

A) THRESHOLD DÜŞÜR (Daha fazla sinyal)
   - Mevcut: 50%
   - Yeni: 40% (daha fazla, daha riskli)
   - run_production.py'de değiştir:
     self.signal_executor = SignalExecutor(self.trading_engine, 
                                           confidence_threshold=40)

B) PARAMETER TUNE (Daha iyi sinyalleri zorla)
   - Entry quality minimum: 60% yaap
   - R/R ratio: 1.5:1 minimum
   - Momentum: 50%+ zorunlu
   
C) BEKLEMEk (Piyasa harekete başlasın)
   - Sabah açılışında daha fazla volatilite
   - Öğlen 12:00-13:00 arası hareketi
   - Akşam yaklaşımında momentum

Bence: C'yi seç, sabah açılışını bekle (09:30-10:30)
       Değilse A'yi seç (40% threshold)
""")

print("\n" + "="*70)
print("✅ TEST TAMAMLANDI")
print("="*70)
