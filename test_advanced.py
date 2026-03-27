#!/usr/bin/env python
"""Quick test for advanced_analyzer module"""

try:
    from advanced_analyzer import (
        AdvancedConfidenceScore,
        HaberSentimentAnalyzer,
        RiskAnalyzer,
        PiyasaDurumuAnalyzer,
        AdvancedSignalFormatter
    )
    print("✓ All imports successful")
    
    # Quick test
    conf = AdvancedConfidenceScore(
        base_score=0.35,
        indikatör_sayısı_hemfikir=9,
        risk_faktörü=0.25,
        hacim_teyidi=0.8,
        haber_sentiment=0.2,
        piyasa_trend=1
    )
    
    güven = conf.hesapla()
    print(f"✓ Confidence score: {güven * 100}%")
    
    # Test formatter
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
        haber=0.2,
        piyasa=1
    )
    
    print("✓ Formatter works")
    print("\n=== SAMPLE MESSAGE ===")
    print(mesaj)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
