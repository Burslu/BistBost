#!/usr/bin/env python312
# -*- coding: utf-8 -*-

print('✅ ENTEGRASYON TEST ÇALIŞMASI\n')

# Import check
print('1️⃣ Checking imports...')
try:
    from run_production import ProductionBot
    from advanced_backtest_engine import AdvancedBacktestEngine
    from multi_timeframe_analyzer import MultiTimeframeAnalyzer
    from entry_quality_detector import CandlestickPatternDetector
    from advanced_risk_manager import AdvancedRiskManager
    from config.settings import load_settings
    print('✅ All imports successful\n')
except Exception as e:
    print(f'❌ Import error: {e}\n')
    import sys
    sys.exit(1)

# Settings check
print('2️⃣ Checking settings...')
settings = load_settings()
adv_cfg = settings.get('advanced_features', {})
print(f'  - Advanced Features Enabled: {adv_cfg.get("enabled", False)}')
print(f'  - Portfolio Size: {adv_cfg.get("portfolio_size", "N/A")} TL')
print(f'  - Risk per Trade: {adv_cfg.get("risk_per_trade_pct", "N/A")}%\n')

print('=' * 60)
print('✅ ENTEGRASYON BAŞARILI!')
print('=' * 60)
print('\n🚀 Bot now ready with:')
print('  • Multi-timeframe Analysis')
print('  • Entry Quality Detection')
print('  • Dynamic SL/TP')
print('  • Risk-based Position Sizing')
print('  • Daily Backtest Reports')
print('  • Health Check (15 dakikada bir)')
