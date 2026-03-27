#!/usr/bin/env python
"""Test intraday trading metrics"""

import sys
sys.path.insert(0, '/content')

try:
    from advanced_analyzer import (
        IntradayTradingAnalyzer,
        HaberSentimentAnalyzer,
        AdvancedSignalFormatter
    )
    import pandas as pd
    import numpy as np
    
    print("✓ All imports successful")
    
    # Test haber sentiment (now with text)
    haber_data = HaberSentimentAnalyzer.kaptan_sentiment_al("SISE.IS")
    print(f"\n✓ Haber Sentiment Test:")
    print(f"  Score: {haber_data[0]}")
    print(f"  Text: {haber_data[1]}")
    
    # Create sample data
    dates = pd.date_range('2026-03-01', periods=60, freq='5min')
    data = {
        'Kapanış': 100 + np.random.randn(60).cumsum(),
        'Yüksek': 103 + np.random.randn(60).cumsum(),
        'Düşük': 97 + np.random.randn(60).cumsum(),
        'Hacim': np.random.randint(1000, 10000, 60)
    }
    df = pd.DataFrame(data, index=dates)
    
    # Test intraday analyzer
    intraday = IntradayTradingAnalyzer(df)
    
    momentum = intraday.momentum_gucü()
    volatilite = intraday.volatilite_intraday()
    breakout = intraday.breakout_olasılığı()
    entry_quality = intraday.entry_quality()
    
    print(f"\n✓ Intraday Metrics:")
    print(f"  Momentum: {momentum}%")
    print(f"  Volatilite: {volatilite}%")
    print(f"  Breakout Potential: {breakout}")
    print(f"  Entry Quality: {entry_quality}%")
    
    # Test message formatter
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
        haber=0.3,
        piyasa=1,
        haber_text="İyi kazançlar, yatırımcı güveni artıyor",
        momentum=65,
        entry_quality=82,
        breakout=0.75
    )
    
    print(f"\n✓ Formatter works - Message preview:")
    print(mesaj[:300] + "...")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
