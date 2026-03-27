# BIST BOT - ADVANCED MODULES INTEGRATION GUIDE
# ============================================

## 4 Yeni Modulün Kuruluşu:

### 1️⃣ ADVANCED BACKTEST ENGINE
File: `advanced_backtest_engine.py`
Kullanım: Günlük sinyalleri test et, PnL hesapla

```python
from advanced_backtest_engine import AdvancedBacktestEngine

engine = AdvancedBacktestEngine(başlangıç_bakiye=10000.0)

# Her sinyal test et
sonuç = engine.sinyali_test_et(
    sembol="PETKM.IS",
    sinyal_tarihi="2026-03-27",
    sinyal_tipi="GÜÇLÜ AL",
    entry_price=120.50,
    stop_loss=118.00,
    take_profit=128.50,
    güven=0.72
)

# Rapor oluştur
rapor, metrikleri = engine.rapor_oluştur("data/signals/backtest_report.txt")
```

Çıktı: Win Rate, Profit Factor, Sharpe Ratio, Max Drawdown


### 2️⃣ MULTI-TIMEFRAME ANALYZER
File: `multi_timeframe_analyzer.py`
Kullanım: 5m sinyal + 15m/1h trend validasyonu

```python
from multi_timeframe_analyzer import MultiTimeframeAnalyzer

mtf = MultiTimeframeAnalyzer("PETKM.IS")

# Base güveni boost et
base_güven = 55  # ZAYIF AL
final_güven, alignment_score = mtf.güven_boost_hesapla(base_güven, işlem_tipi="AL")

# Alignment 85/100 ise:
# Final Güven = 55% + (55% × 30% × 0.85) = 55% + 14% = 69% ✅
```

Beklenen Sonuç: +10-20% güven boost eğer tüm timeframe'ler aligned ise


### 3️⃣ ENTRY QUALITY DETECTION
File: `entry_quality_detector.py`
Kullanım: Candlestick pattern analizi

```python
from entry_quality_detector import CandlestickPatternDetector

df = yf.download("PETKM.IS", period="30d", interval="5m", progress=False)
detector = CandlestickPatternDetector(df)

entry_quality = detector.hesapla_entry_quality(işlem_tipi="AL")
# 0-100 score, 70+ = çok güçlü entry

print(detector.rapor_oluştur())
# Engulfing, Pin Bar, Breakout pattern tespiti
```

Beklenen Sonuç: Bullish/Bearish pattern score


### 4️⃣ ADVANCED RISK MANAGER
File: `advanced_risk_manager.py`
Kullanım: Dinamik SL/TP ve position sizing

```python
from advanced_risk_manager import AdvancedRiskManager

df = yf.download("PETKM.IS", period="30d", progress=False)
risk_mgr = AdvancedRiskManager(df, portfolio_size=10000.0, risk_per_trade=2.0)

# Dinamik SL/TP
sl, tp, atr = risk_mgr.hesapla_atr_based_sl_tp(
    entry_price=120.50,
    işlem_tipi="AL",
    atr_multiplier_sl=2.0,
    atr_multiplier_tp=3.0
)

# RR Ratio kontrolü
rr, is_valid = risk_mgr.rr_ratio_kontrol(entry_price, sl, tp, min_rr=1.5)

# Position sizing
pos_size = risk_mgr.hesapla_position_size(entry_price, sl)

print(risk_mgr.rapor_oluştur(entry_price, işlem_tipi="AL"))
```

Beklenen Sonuç: 2:1 RR, dinamik lot size


## 🚀 PRODUCTION BOT INTEGRATION (STEP BY STEP)

### Adım 1: run_production.py'ye modülleri import et

```python
from advanced_backtest_engine import AdvancedBacktestEngine
from multi_timeframe_analyzer import MultiTimeframeAnalyzer
from entry_quality_detector import CandlestickPatternDetector
from advanced_risk_manager import AdvancedRiskManager
```

### Adım 2: Sinyal kalitesi arttır

```python
# RealTimeAnalyzer'dan çıkan sinyalde:

# 1. MTF güven boost
mtf = MultiTimeframeAnalyzer(sembol)
metaf_boosted_güven, alignment = mtf.güven_boost_hesapla(
    advanced_güven, işlem_tipi=sinyal.sinyal_seviyesi
)

# 2. Entry quality check
df = yf.download(sembol, period="30d", interval="5m", progress=False)
detector = CandlestickPatternDetector(df)
entry_quality_score = detector.hesapla_entry_quality(sinyal.sinyal_seviyesi)

# 3. Combined güven (Multi-weighted)
final_güven = (
    metaf_boosted_güven * 0.4 +  # MTF alignment
    (entry_quality_score / 100) * 100 * 0.3 +  # Entry pattern
    # Base advanced_güven * 0.3 (zaten var)
) / 3
```

### Adım 3: Dinamik SL/TP

```python
risk_mgr = AdvancedRiskManager(df, portfolio_size=5000, risk_per_trade=2.0)

sl_dynamic, tp_dynamic, atr_used = risk_mgr.hesapla_atr_based_sl_tp(
    entry_price=analyzer.son_kapanış,
    işlem_tipi=sinyal.sinyal_seviyesi,
    atr_multiplier_sl=2.0,
    atr_multiplier_tp=3.0
)

# SL/TP yerine bunu kullan
sinyal.stop_loss = sl_dynamic
sinyal.hedef = tp_dynamic
```

### Adım 4: Position Sizing

```python
pos_size = risk_mgr.hesapla_position_size(
    entry_price=analyzer.son_kapanış,
    stop_loss=sl_dynamic
)

# Signal executor'a gönder (10 yerine pos_size)
executed_trade = self.signal_executor.execute_from_analyzer_signal(
    ...
    quantity=pos_size,  # Dinamik
    ...
)
```

### Adım 5: Daily Backtest Report

```python
# Cron job: Her gün saat 18:00'de
backtest_engine = AdvancedBacktestEngine(başlangıç_bakiye=10000.0)

# Günün tüm sinyallerini test et
for sinyal in günün_sinyalleri:
    sonuç = backtest_engine.sinyali_test_et(...)

rapor, metrikleri = backtest_engine.rapor_oluştur(
    output_path="data/signals/backtest_daily_report.txt"
)

# Telegram'a gönder
telegram_rapor = f"""
📊 Daily Backtest Report
Win Rate: {metrikleri['win_rate']}%
Profit Factor: {metrikleri['profit_factor']:.2f}x
Total PnL: {metrikleri['toplam_pnl']}
"""
```


## 📋 TEST SEQUENCE

```bash
# 1. Her modülü ayrı test et
python advanced_backtest_engine.py
python multi_timeframe_analyzer.py

python entry_quality_detector.py
python advanced_risk_manager.py

# 2. Integration test
# - Bot 1 saat çalış
# - Sinyalleri test et
# - Metrikleri kontrol et

# 3. Live run
# - Production bot'u başlat
# - Health check devam etsin
# - 24 saatte backtest report bak
```


## 🎯 BEKLENEN SONUÇLAR

❌ BEFORE:
- Güven: %50-65 (Zayıf sinyaller)
- Entry Quality: ?
- SL/TP: Sabit ratio
- Position: 10 adet (fixed)
- Win Rate: Bilinmiyor

✅ AFTER:
- Güven: %70-85 (Güçlü sinyaller)
- Entry Quality: 70+/100 (Candlestick pattern validated)
- SL/TP: Dinamik ATR-based (volatility adaptive)
- Position: Risk-based sizing
- Win Rate: Günlük backtest report


## ⚙️ CONFIGURATION (settings.json)

```json
{
  "advanced_features": {
    "multi_timeframe_enabled": true,
    "entry_quality_check": true,
    "dynamic_sl_tp": true,
    "risk_per_trade_pct": 2.0,
    "min_rr_ratio": 1.5,
    "portfolio_size": 5000.0,
    "daily_backtest": true
  }
}
```


## 💡 NEXT STEPS (After Integration)

1. **Machine Learning Entry** ← Classification model (XGBoost)
2. **Options Strategy** ← Put/Call hedging
3. **Real Broker Integration** ← Live trading API
4. **Advanced Portfolio** ← Multi-symbol optimization
