"""
Production Ready - Real-Time BIST Trading Bot
==============================================
5 dakikalık periyotla veri güncelleme + Saatlik Telegram özeti
"""

import os
import sys
import json
import time
import logging
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread, Event
import pandas as pd

# Logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# File'a yazarken console'da sessiz kal (sadece WARNING ve üstü göster)
file_handler = logging.FileHandler(log_dir / f"production_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
if sys.platform == "win32":
    import io
    console_handler.stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
console_handler.setLevel(logging.INFO)  # INFO ve üzeri (INFO, WARNING, ERROR, CRITICAL)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[file_handler, console_handler]
)

# UTF-8 encoding Windows konsolu için
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
logger = logging.getLogger(__name__)

# Import modülleri
try:
    from realtime_analyzer import RealTimeAnalyzer
    from config.settings import load_settings
    from advanced_analyzer import (
        AdvancedConfidenceScore,
        HaberSentimentAnalyzer,
        RiskAnalyzer,
        PiyasaDurumuAnalyzer,
        AdvancedSignalFormatter,
        IntradayTradingAnalyzer
    )
    from trading_engine import MockTradingEngine, TradingRiskConfig
    from signal_executor import SignalExecutor, MockTradeMonitor
    
    # 🆕 ADVANCED MODULES
    from advanced_backtest_engine import AdvancedBacktestEngine
    from multi_timeframe_analyzer import MultiTimeframeAnalyzer
    from entry_quality_detector import CandlestickPatternDetector
    from advanced_risk_manager import AdvancedRiskManager
    from real_trading_engine import RealTradingEngine, TradingEngineFactory
except ImportError as e:
    logger.error(f"Import hatası: {e}")
    sys.exit(1)

class ProductionBot:
    """Production-hazır real-time trading bot"""
    
    def __init__(self):
        self.settings = load_settings()
        self.hisseler = self.settings["symbols"]["bist"]
        self.periyot_dakika = self.settings["strategy"].get("fetch_interval_minutes", 5)
        self.telegramaktif = self.settings["telegram"].get("enabled", False)
        self.telegramtoken = self.settings["telegram"].get("bot_token")
        self.telegramchatid = self.settings["telegram"].get("chat_id")
        
        # 🎯 TRADING ENGINE BAŞLAT (Mode'u kontrol et)
        trading_mode = os.getenv("TRADING_MODE", "mock").lower()  # mock veya real
        
        if trading_mode == "real":
            # Real Nest Trading
            api_key = os.getenv("NEST_API_KEY")
            api_secret = os.getenv("NEST_API_SECRET")
            
            if not api_key or not api_secret:
                logger.error("❌ REAL MODE: API Credentials bulunamadı!")
                logger.error("Şu environment variables'ları set et:")
                logger.error("  $env:NEST_API_KEY = 'your_key'")
                logger.error("  $env:NEST_API_SECRET = 'your_secret'")
                sys.exit(1)
            
            self.trading_engine = TradingEngineFactory.create(
                "real",
                api_key=api_key,
                api_secret=api_secret
            )
            self.signal_executor = SignalExecutor(self.trading_engine, confidence_threshold=60)
            logger.info("🔴 REAL TRADING ENGINE BAŞLATILDI (Nest API)")
            logger.warning("⚠️  UYARI: Bu gerçek para ile trading yapıyor!")
            
        else:
            # Mock Trading (Varsayılan)
            risk_config = TradingRiskConfig(
                portfolio_size=5000.0,  # Sanal portföy
                risk_per_trade=2.0,    # %2 risk
                min_rr_ratio=1.0       # R/R
            )
            self.trading_engine = MockTradingEngine(risk_config)
            self.signal_executor = SignalExecutor(self.trading_engine, confidence_threshold=70)
            self.trade_monitor = MockTradeMonitor(self.signal_executor)
            logger.info("✓ Mock Trading Engine başlatıldı (5000 TL sanal portföy)")
        
        # Piyasa durumu analyzer
        self.bist100_df = None
        self._piyasa_verisini_guncelle()
        
        self.sinyaller_saati = {}  # Saatlik sinyalleri tut
        self.son_ozet_saat = datetime.now().hour
        self.calistir_bayragi = True
        self.sinyaller_df = pd.DataFrame()  # Tarihçe for delta detection
        
        # Health check
        self.son_health_check = datetime.now()
        self.health_check_interval = 15  # 15 dakika
        self.toplam_hisse_tarandı = 0
        self.son_guclu_sinyal = None
        
        # 🆕 ADVANCED MODULES
        self.backtest_engine = AdvancedBacktestEngine(başlangıç_bakiye=5000.0)
        self.günün_sinyalleri = []  # Daily backtest için
        self.advanced_enabled = self.settings.get("advanced_features", {}).get("enabled", True)
        
    def _borsa_acik_mi(self) -> bool:
        """Borsa saatleri kontrolü (Pazartesi-Cuma 10:00-18:00)"""
        now = datetime.now()
        weekday = now.weekday()  # 0=Pazartesi, 6=Pazar
        hour = now.hour
        minute = now.minute
        current_time = hour + minute/60
        
        # Pazartesi(0) - Cuma(4), 10:00-18:00
        if weekday >= 5:  # Cumartesi/Pazar
            return False
        if current_time < 10.0 or current_time > 18.0:
            return False
        return True
        
    def _piyasa_verisini_guncelle(self):
        """XU100 ve piyasa verilerini güncelle"""
        try:
            import yfinance as yf
            self.bist100_df = yf.download("XU100.IS", period="1mo", interval="5m", progress=False)
            if self.bist100_df is not None and len(self.bist100_df) > 0:
                logger.info("✓ Piyasa verisi güncellendi (XU100)")
        except Exception as e:
            logger.warning(f"Piyasa verisi güncellemesi başarısız: {e}")
        
    def sinyal_telegramgönder(self, sinyal, advanced_data=None):
        """Güçlü sinyal Telegram'a gönder (≥70% güven) - INTRADAY OPTIMIZED"""
        if not self.telegramaktif:
            return
        
        # Güven kontrol: Sadece 70%+ sinyalleri gönder
        if sinyal.güven_yüzdesi < 70:
            logger.debug(f"⏭️ {sinyal.sembol}: Güven %{int(sinyal.güven_yüzdesi)} < 70% → Telegram'a gönderilmedi")
            return
        
        # ZAYIF sinyalleri filtrele
        if "ZAYIF" in sinyal.sinyal_seviyesi:
            logger.debug(f"⏭️ {sinyal.sembol}: {sinyal.sinyal_seviyesi} (Zayıf) → Telegram'a gönderilmedi")
            return
        
        # INFO level'de güçlü sinyali logla
        logger.info(f"📱 TELEGRAM SINYAL: {sinyal.sembol} {sinyal.sinyal_seviyesi} | Güven: {int(sinyal.güven_yüzdesi)}% | Fiyat: {sinyal.fiyat}")
        
        # Advanced data yoksa fallback
        if advanced_data is None:
            advanced_data = {
                "risk": 0.5,
                "haber": 0,
                "haber_text": "",
                "piyasa": 0,
                "momentum": 0,
                "entry_quality": 0,
                "breakout": 0
            }
        
        # Advanced formatter kullan
        mesaj = AdvancedSignalFormatter.format_telegram_message(
            sembol=sinyal.sembol,
            fiyat=sinyal.fiyat,
            sinyal=sinyal.sinyal_seviyesi,
            güven=sinyal.güven_yüzdesi / 100.0,
            stop_loss=sinyal.stop_loss,
            hedef=sinyal.hedef,
            atr=sinyal.indikatörler[-1].value if sinyal.indikatörler else 0,  # ATR
            volatilite=advanced_data.get("volatilite", 0.02),
            risk=advanced_data.get("risk", 0.5),
            haber=advanced_data.get("haber", 0),
            piyasa=advanced_data.get("piyasa", 0),
            haber_text=advanced_data.get("haber_text", ""),
            momentum=advanced_data.get("momentum", 0),
            entry_quality=advanced_data.get("entry_quality", 0),
            breakout=advanced_data.get("breakout", 0)
        )
        
        self._telegram_post(mesaj)
    
    def günlük_backtest_raporonu_gönder(self):
        """Günün sinyallerini backtest et ve rapor gönder (18:00'de)"""
        
        if not self.günün_sinyalleri or len(self.günün_sinyalleri) == 0:
            logger.info("📊 Günlük backtest: Sinyal yok")
            return
        
        logger.info(f"📊 Günlük backtest raporu oluşturuluyor ({len(self.günün_sinyalleri)} sinyal)...")
        
        try:
            # Backtest engine oluştur
            backtest_engine = AdvancedBacktestEngine(başlangıç_bakiye=5000.0)
            
            # Her sinyali test et
            for sinyal in self.günün_sinyalleri:
                sonuç = backtest_engine.sinyali_test_et(
                    sembol=sinyal["sembol"],
                    sinyal_tarihi=(sinyal["timestamp"]).strftime("%Y-%m-%d"),
                    sinyal_tipi=sinyal["sinyal"],
                    entry_price=sinyal["entry"],
                    stop_loss=sinyal["sl"],
                    take_profit=sinyal["tp"],
                    güven=sinyal["güven"]
                )
                
                if sonuç:
                    logger.debug(f"  {sinyal['sembol']}: {sonuç['pnl']:.2f} TL ({sonuç['pnl_pct']:.1f}%)")
            
            # Metrikleri hesapla
            metrikleri = backtest_engine.metrikleri_hesapla()
            
            if metrikleri:
                # Rapor oluştur
                rapor_txt, _ = backtest_engine.rapor_oluştur(
                    output_path=f"data/signals/backtest_daily_{datetime.now().strftime('%Y%m%d')}.txt"
                )
                
                # Telegram'a gönder
                telegram_rapor = f"""
📊 DAILY BACKTEST REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Operations: {metrikleri['toplam_işlem']}
✅ Wins: {metrikleri['kazanan_işlem']} ({metrikleri['win_rate']:.1f}%)
❌ Losses: {metrikleri['kaybeden_işlem']}

💰 Profit: {metrikleri['toplam_pnl']:.2f} TL
📊 Profit Factor: {metrikleri['profit_factor']:.2f}x
⚡ Sharpe Ratio: {metrikleri['sharpe_ratio']:.2f}
🔴 Max Drawdown: {metrikleri['max_drawdown']:.2f} TL

🎯 Avg Win: {metrikleri['avg_win']:.2f} TL
🎯 Avg Loss: {metrikleri['avg_loss']:.2f} TL
💹 RR Ratio: {metrikleri['payoff_ratio']:.2f}

⏰ {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
                
                self._telegram_post(telegram_rapor)
                logger.info(f"✅ Günlük backtest raporu gönderildi")
                
                # Store for reference
                self.günün_sinyalleri = []
        
        except Exception as e:
            logger.error(f"Günlük backtest hatası: {e}")
    
    def saatlik_ozet_telegramgönder(self):
        """Saatlik özet (devre dışı - günlük backtest yeterli)"""
        return  # 🔴 DISABLED - buggy with advanced modules
    
    def _telegram_post(self, metin):
        """Telegram'a mesaj gönder (internal)"""
        import requests
        
        try:
            url = f"https://api.telegram.org/bot{self.telegramtoken}/sendMessage"
            response = requests.post(
                url,
                json={"chat_id": self.telegramchatid, "text": metin},
                timeout=5
            )
            if response.status_code == 200:
                logger.info("✓ Telegram mesajı gönderildi")
            else:
                logger.warning(f"✗ Telegram hatası: {response.status_code}")
        except Exception as e:
            logger.error(f"✗ Telegram gönderme hatası: {e}")
    
    def health_check_telegramgönder(self):
        """15 dakikada bir bot alive mesajı gönder"""
        zaman = datetime.now()
        son_check_geçen = (zaman - self.son_health_check).total_seconds() / 60
        
        if son_check_geçen >= self.health_check_interval:
            # Health message oluştur
            health_msg = f"""🤖 BOT ALIVE - Health Check
━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ Zaman: {zaman.strftime('%H:%M:%S')}
📊 Tarandı: {self.toplam_hisse_tarandı} hisse (bu turda)
📈 Son Güçlü Sinyal: {self.son_guclu_sinyal if self.son_guclu_sinyal else 'Henüz yok'}
🟢 Durumu: NORMAL ✅
━━━━━━━━━━━━━━━━━━━━━━━━━
Telegram: ✓ Bağlı
Analiz: ✓ Aktif
Logger: ✓ Kayıt Ediyor"""
            
            self._telegram_post(health_msg)
            logger.info(f"💚 Health Check gönderildi")
            self.son_health_check = zaman
            self.toplam_hisse_tarandı = 0  # Reset counter
    
    def analiz_dongusu(self):
        """Ana analiz döngüsü (5 dakikada bir - Borsa saatleri: Pt-Cu 10:00-18:00)"""
        logger.info(f"🚀 Production bot başladı - {len(self.hisseler)} hisse takip ediliyor")
        logger.info(f"   Periyot: {self.periyot_dakika} dakika")
        logger.info(f"   Borsa Saatleri: Pazartesi-Cuma 10:00-18:00")
        logger.info(f"   Telegram: {'✓ Aktif' if self.telegramaktif else '✗ Kapalı'}")
        logger.info(f"   Advanced Metrics: ✓ Aktif (Risk, Haber, Piyasa Trendi)")
        
        while self.calistir_bayragi:
            try:
                zaman = datetime.now()
                
                # BORSA SAATLERI KONTROLÜ
                if not self._borsa_acik_mi():
                    weekday_name = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][zaman.weekday()]
                    next_open = "10:00 Pazartesi" if zaman.weekday() >= 4 else f"10:00 {weekday_name}"
                    logger.info(f"⏰ Borsa kapalı ({zaman.strftime('%A %H:%M')}). Sonraki açılış: {next_open}")
                    time.sleep(300)  # 5 dakika bekle
                    continue
                
                logger.info(f"\n{'='*60}")
                logger.info(f"Analiz başladı: {zaman.strftime('%H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                # Health Check kontrol et (15 dakikada bir)
                self.health_check_telegramgönder()
                
                sinyaller_bu_tur = []
                
                # Piyasa verisini güncelle
                piyasa_analyzer = PiyasaDurumuAnalyzer(self.bist100_df)
                piyasa_trend = piyasa_analyzer.genel_trend()
                try:
                    piyasa_volatilitesi_val = piyasa_analyzer.piyasa_volatilitesi()
                    piyasa_volatilitesi = float(piyasa_volatilitesi_val) if piyasa_volatilitesi_val is not None else 0.015
                except:
                    piyasa_volatilitesi = 0.015
                
                logger.info(f"📈 Piyasa Trendi: {'🚀 UP' if piyasa_trend > 0 else '📉 DOWN' if piyasa_trend < 0 else '➡️ NÖTR'} | Volatilite: {piyasa_volatilitesi*100:.2f}%")
                
                # Tüm hisseleri analiz et
                for sembol in self.hisseler:
                    try:
                        self.toplam_hisse_tarandı += 1  # Sayac increment et
                        analyzer = RealTimeAnalyzer(sembol, period="1mo", interval="5m")
                        sinyal = analyzer.tamAnaliz()
                        
                        if sinyal:
                            # Advanced metrics hesapla
                            risk_analyzer = RiskAnalyzer(analyzer.df)
                            risk_volatilite = risk_analyzer.volatilite_riski()
                            risk_drawdown = risk_analyzer.drawdown_riski()
                            risk_composite = (risk_volatilite * 0.6 + risk_drawdown * 0.4)
                            
                            # Haber sentiment (NOW returns tuple: score, text)
                            haber_data = HaberSentimentAnalyzer.kaptan_sentiment_al(sembol)
                            if isinstance(haber_data, tuple):
                                haber_sentiment, haber_text = haber_data
                            else:
                                haber_sentiment, haber_text = haber_data, ""
                            
                            # intraday trading metrics
                            intraday_analyzer = IntradayTradingAnalyzer(analyzer.df)
                            momentum = intraday_analyzer.momentum_gucü()
                            entry_quality = intraday_analyzer.entry_quality()
                            breakout = intraday_analyzer.breakout_olasılığı()
                            
                            # Indikatörler kaç tanesinin hemfikir?
                            hemfikir_sayisi = sum([1 for ind in sinyal.indikatörler if np.sign(ind.skor) == np.sign(sinyal.ağırlıklı_skor)])
                            
                            # Hacim teyidi
                            hacim_teyidi = sinyal.indikatörler[-2].skor if len(sinyal.indikatörler) >= 2 else 0.5
                            
                            # Composite confidence
                            conf_score = AdvancedConfidenceScore(
                                base_score=sinyal.ağırlıklı_skor,
                                indikatör_sayısı_hemfikir=hemfikir_sayisi,
                                risk_faktörü=risk_composite,
                                hacim_teyidi=max(0, min(1, hacim_teyidi)),
                                haber_sentiment=haber_sentiment,
                                piyasa_trend=piyasa_trend
                            )
                            advanced_güven = conf_score.hesapla()
                            
                            # Advanced data paketi
                            advanced_data = {
                                "risk": risk_composite,
                                "haber": haber_sentiment,
                                "haber_text": haber_text,
                                "piyasa": piyasa_trend,
                                "volatilite": piyasa_volatilitesi,
                                "hemfikir": hemfikir_sayisi,
                                "advanced_güven": advanced_güven,
                                "momentum": momentum,
                                "entry_quality": entry_quality,
                                "breakout": breakout
                            }
                            
                            sinyaller_bu_tur.append((sinyal, advanced_data))
                            self.sinyaller_saati[sembol] = sinyal
                            
                            # 🆕 ADVANCED MODULES INTEGRATION
                            if self.advanced_enabled:
                                try:
                                    # 1️⃣ MULTI-TIMEFRAME ANALYSIS
                                    mtf = MultiTimeframeAnalyzer(sembol)
                                    mtf_boosted_güven, mtf_alignment = mtf.güven_boost_hesapla(
                                        advanced_güven * 100, 
                                        işlem_tipi=sinyal.sinyal_seviyesi
                                    )
                                    mtf_boosted_güven = mtf_boosted_güven / 100
                                    
                                    # 2️⃣ ENTRY QUALITY DETECTION
                                    detector = CandlestickPatternDetector(analyzer.df)
                                    entry_quality_advanced = detector.hesapla_entry_quality(sinyal.sinyal_seviyesi) / 100
                                    
                                    # 3️⃣ Advanced Risk Manager (SL/TP)
                                    risk_mgr = AdvancedRiskManager(analyzer.df, portfolio_size=5000, risk_per_trade=2.0)
                                    sl_dynamic, tp_dynamic, atr_used = risk_mgr.hesapla_atr_based_sl_tp(
                                        entry_price=analyzer.son_kapanış,
                                        işlem_tipi=sinyal.sinyal_seviyesi,
                                        atr_multiplier_sl=2.0,
                                        atr_multiplier_tp=3.0
                                    )
                                    
                                    # RR Ratio check
                                    rr_ratio, rr_valid = risk_mgr.rr_ratio_kontrol(
                                        analyzer.son_kapanış, 
                                        sl_dynamic, 
                                        tp_dynamic, 
                                        min_rr=1.5
                                    )
                                    
                                    # Position sizing
                                    pos_size = risk_mgr.hesapla_position_size(
                                        analyzer.son_kapanış, 
                                        sl_dynamic
                                    )
                                    
                                    # COMBINED GÜVEN (weighted)
                                    final_güven = (
                                        mtf_boosted_güven * 0.35 +  # MTF alignment
                                        entry_quality_advanced * 0.35 +  # Entry pattern
                                        advanced_güven * 0.30  # Base confidence
                                    )
                                    
                                    # Override old values
                                    advanced_güven = final_güven
                                    entry_quality = entry_quality_advanced * 100
                                    sinyal.stop_loss = sl_dynamic
                                    sinyal.hedef = tp_dynamic
                                    
                                    # Store for daily backtest
                                    self.günün_sinyalleri.append({
                                        "sembol": sembol,
                                        "sinyal": sinyal.sinyal_seviyesi,
                                        "entry": analyzer.son_kapanış,
                                        "sl": sl_dynamic,
                                        "tp": tp_dynamic,
                                        "güven": final_güven,
                                        "pos_size": pos_size,
                                        "rr_ratio": rr_ratio,
                                        "timestamp": datetime.now()
                                    })
                                    
                                    logger.info(f"🔧 ADVANCED: Güven={final_güven*100:.0f}% | MTF={mtf_alignment:.0f} | Entry={entry_quality_advanced*100:.0f} | RR={rr_ratio:.2f}")
                                    
                                except Exception as adv_e:
                                    logger.warning(f"Advanced modules hatası ({sembol}): {adv_e}")
                                    # Fallback: use original values
                            
                            # Log - geliştirilmiş versi + INTRADAY METRICS
                            güven_emoji = "🔥" if advanced_güven > 0.75 else "✔️" if advanced_güven > 0.65 else "◆"
                            risk_emoji = "⚠️" if risk_composite > 0.7 else "✓"
                            entry_emoji = "✅" if entry_quality > 75 else "🟡" if entry_quality > 50 else "🔴"
                            momentum_emoji = "⚡" if momentum > 60 else "✓" if momentum > 30 else "❄️"
                            
                            # 50-65% arası sinyallerde log'a yazdır ama işlem yapma
                            if 0.50 < advanced_güven <= 0.65:
                                logger.info(
                                    f"🟡 {sembol}: {sinyal.sinyal_seviyesi:<10} | "
                                    f"Güven: {int(advanced_güven*100)}% | "
                                    f"Risk: {int(risk_composite*100)}% {risk_emoji} | "
                                    f"Entry: {entry_emoji}{int(entry_quality)}% | "
                                    f"Momentum: {momentum_emoji}{int(momentum)}% | "
                                    f"[IZLENIYOR - İşlem bekleniyor...]"
                                )
                            else:
                                logger.info(
                                    f"{güven_emoji} {sembol}: {sinyal.sinyal_seviyesi:<10} | "
                                    f"Güven: {int(advanced_güven*100)}% | "
                                    f"Risk: {int(risk_composite*100)}% {risk_emoji} | "
                                    f"Entry: {entry_emoji}{int(entry_quality)}% | "
                                    f"Momentum: {momentum_emoji}{int(momentum)}% | "
                                    f"Haber: {'😊' if haber_sentiment > 0.2 else '😔' if haber_sentiment < -0.2 else '😐'}"
                                )
                            
                            # Güçlü sinyal (>65%) ise hemen gönder + trade aç
                            if advanced_güven > 0.65:
                                # Son güçlü sinyali kaydet (health check için)
                                self.son_guclu_sinyal = f"{sembol} ({int(advanced_güven*100)}%)"
                                
                                # 🎯 MOCK TRADE EXECUTE
                                try:
                                    # pos_size tanımlı mı?
                                    pos_size_actual = 10  # default fallback
                                    if 'pos_size' in locals():
                                        pos_size_actual = pos_size
                                    
                                    executed_trade = self.signal_executor.execute_from_analyzer_signal(
                                        symbol=sembol,
                                        sinyal_tipi=sinyal.sinyal_seviyesi,
                                        güven=advanced_güven * 100,
                                        market_price=analyzer.son_kapanış,
                                        entry_quality=entry_quality,
                                        momentum=momentum,
                                        volatilite=piyasa_volatilitesi,
                                        haber_sentiment=haber_sentiment,
                                        haber_text=haber_text,
                                        market_trend=sinyal.sinyal_seviyesi,
                                        quantity=pos_size_actual  # 🆕 Dinamik
                                    )
                                    if executed_trade:
                                        logger.info(f"✅ MOCK TRADE: {sembol} açıldı - Position ID: {executed_trade['position_id']} | Size: {pos_size_actual} adet")
                                except Exception as te:
                                    logger.warning(f"Mock trade error: {te}")
                                
                                # Telegram'a gönder
                                self.sinyal_telegramgönder(sinyal, advanced_data)
                    
                    except Exception as e:
                        logger.error(f"✗ {sembol} analiz hatası: {e}")
                        continue
                
                # İstatistik
                al_sayisi = len([s for s, _ in sinyaller_bu_tur if "AL" in s.sinyal_seviyesi])
                sat_sayisi = len([s for s, _ in sinyaller_bu_tur if "SAT" in s.sinyal_seviyesi])
                notr_sayisi = len([s for s, _ in sinyaller_bu_tur if "NÖTR" in s.sinyal_seviyesi])
                
                logger.info(f"\n📊 Özet: {al_sayisi} AL | {sat_sayisi} SAT | {notr_sayisi} NÖTR")
                
                # Saatlik özet (devre dışı - günlük backtest yeterli)
                # if zaman.hour != self.son_ozet_saat:
                #     logger.info("⏰ Saatlik özet gönderiliyor...")
                #     self.saatlik_ozet_telegramgönder()
                #     self.son_ozet_saat = zaman.hour
                
                # Bekle
                logger.info(f"⏱️  Sonraki analiz: {self.periyot_dakika} dakika sonra ({(zaman + timedelta(minutes=self.periyot_dakika)).strftime('%H:%M')})")
                time.sleep(self.periyot_dakika * 60)
            
            except KeyboardInterrupt:
                logger.info("\n⛔ Bot durduruldu (Ctrl+C)")
                self.calistir_bayragi = False
                break
            except Exception as e:
                logger.error(f"⚠️  Döngü hatası: {e}", exc_info=True)
                logger.info(f"Yeniden başlatılıyor...")
                time.sleep(10)
    
    def kapat(self):
        """Bot'u düzgün kapat"""
        logger.info("Bot kapatılıyor...")
        self.calistir_bayragi = False


def main():
    """Main entry point"""
    
    # Dizinleri oluştur
    Path("logs").mkdir(exist_ok=True)
    Path("data/signals").mkdir(parents=True, exist_ok=True)
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("🤖 BIST REAL-TIME TRADING BOT")
    logger.info("=" * 60)
    
    bot = ProductionBot()
    
    try:
        bot.analiz_dongusu()
    except KeyboardInterrupt:
        logger.info("\nKlavye kesintisi algılandı")
        bot.kapat()
    except Exception as e:
        logger.error(f"Kritik hata: {e}")
        bot.kapat()
    finally:
        logger.info("Bot tamamen kapatıldı")


if __name__ == "__main__":
    main()
