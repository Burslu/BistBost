"""
BIST 100 Sinyal Botu - Tam Otomatik AL/SAT Sinyali + Telegram Rapor
=====================================================================
- BIST 100 hisselerini yfinance üzerinden çeker (fallback: collectapi)
- 11 ağırlıklı teknik indikatörle analiz eder
- Hisse bazlı detaylı AL/SAT sinyalleri üretir
- Telegram'a otomatik rapor gönderir
- Tek dosya, bağımsız çalışır

Kullanım:
    pip install yfinance pandas numpy requests
    
    # .env veya ortam değişkenleri:
    set TELEGRAM_BOT_TOKEN=123456:ABC-DEF
    set TELEGRAM_CHAT_ID=123456789
    
    python bist100_signal_bot.py
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
import numpy as np
import requests

try:
    import yfinance as yf
except ImportError:
    print("[HATA] yfinance kurulu degil: pip install yfinance")
    sys.exit(1)

# ─── Windows UTF-8 fix ───
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ─── Logging ───
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"signal_bot_{datetime.now():%Y%m%d}.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("BistBot")

# ═══════════════════════════════════════════════════════
# BIST TÜM HİSSELER (yfinance'te doğrulanmış 324 hisse)
# ═══════════════════════════════════════════════════════

BIST_TUMU = [
    "ADEL","AEFES","AGROT","AHGAZ","AKBNK","AKCNS","AKENR","AKFGY","AKSA","AKSEN",
    "AKSUE","ALARK","ALFAS","ALGYO","ALKIM","ANSGR","ARASE","ARCLK","ARDYZ","ARSAN",
    "ASELS","ASTOR","ASUZU","AYCES","AYGAZ","BAGFS","BANVT","BARMA","BASGZ","BERA",
    "BFREN","BIMAS","BIOEN","BNTAS","BOBET","BRISA","BRSAN","BRYAT","BTCIM","BUCIM",
    "CANTE","CASA","CATES","CCOLA","CEMAS","CEMTS","CIMSA","CMENT","CONSE","CRDFA",
    "CUSAN","CWENE","DAGI","DENGE","DERHL","DESA","DGATE","DITAS","DMRGD","DNISI",
    "DOAS","DOHOL","DURDO","DYOBY","DZGYO","ECILC","ECZYT","EDATA","EGEEN","EKGYO",
    "EKSUN","EMKEL","ENERY","ENJSA","ENKAI","ENTRA","EPLAS","EREGL","ERSU","ESCAR",
    "EUPWR","EUREN","EYGYO","FENER","FLAP","FONET","FORMT","FORTE","FRIGO","FROTO",
    "GARAN","GEDIK","GEDZA","GENTS","GEREL","GESAN","GIPTA","GLBMD","GLCVY","GLYHO",
    "GMTAS","GOKNR","GOLTS","GOODY","GOZDE","GRSEL","GSDHO","GSRAY","GUBRF","GWIND",
    "GZNMI","HALKB","HATEK","HDFGS","HEDEF","HEKTS","HLGYO","HRKET","HTTBT","HUBVC",
    "HUNER","IHEVA","IHGZT","IHLAS","IHLGM","IHYAY","IMASM","INDES","INGRM","INTEM",
    "INVEO","ISATR","ISCTR","ISFIN","ISGYO","ISMEN","IZENR","IZFAS","JANTS","KAPLM",
    "KARTN","KATMR","KAYSE","KCHOL","KERVN","KFEIN","KGYO","KIMMR","KLGYO","KLMSN",
    "KLRHO","KLSER","KLSYN","KMPUR","KNFRT","KONTR","KONYA","KORDS","KOTON","KRDMD",
    "KRONT","KRSTL","KTLEV","KUTPO","KUYAS","KZBGY","KZGYO","LIDER","LILAK","LKMNH",
    "LMKDC","LOGO","LUKSK","MAGEN","MAKIM","MAKTK","MANAS","MARBL","MARTI","MAVI",
    "MEDTR","MEGAP","MERCN","MERIT","MERKO","MGROS","MIATK","MNDRS","MNDTR","MOBTL",
    "MPARK","MRGYO","MSGYO","MTRKS","MTRYO","MZHLD","NATEN","NETAS","NTGAZ","NTHOL",
    "NUGYO","NUHCM","OBAMS","ODAS","ONCSM","ORCAY","ORGE","OSMEN","OSTIM","OTKAR",
    "OYAKC","OYLUM","OZKGY","OZRDN","PAMEL","PAPIL","PARSN","PCILT","PEKGY","PENGD",
    "PENTA","PETKM","PETUN","PGSUS","PINSU","PKENT","PLTUR","POLHO","POLTK","PRDGS",
    "PRKAB","PRKME","PRZMA","PSDTC","QUAGR","RALYH","RAYSG","REEDR","RNPOL","RODRG",
    "ROYAL","RTALB","RUBNS","RYGYO","SAHOL","SANEL","SARKY","SASA","SAYAS","SDTTR",
    "SEGYO","SEKFK","SELEC","SELVA","SILVR","SISE","SKBNK","SMART","SMRTG","SNGYO",
    "SNICA","SOKE","SOKM","SONME","SRVGY","SUMAS","SUWEN","TABGD","TATGD","TAVHL",
    "TBORG","TCELL","TDGYO","TEKTU","TERA","TEZOL","TGSAS","THYAO","TKFEN","TLMAN",
    "TMPOL","TMSN","TNZTP","TOASO","TRCAS","TRGYO","TRILC","TSKB","TTKOM","TTRAK",
    "TUCLK","TUKAS","TUPRS","TUREX","TURGG","TURSG","UFUK","ULKER","ULUSE","ULUUN",
    "UNLU","USAK","VAKBN","VAKFN","VAKKO","VANGD","VBTYZ","VERTU","VERUS","VESBE",
    "VESTL","VKFYO","VKGYO","YAPRK","YATAS","YBTAS","YEOTK","YGGYO","YKBNK","YKSLN",
    "YUNSA","YYLGD","ZEDUR","ZOREN",
]

# ═══════════════════════════════════════════════════════
# İNDİKATÖR AĞIRLIKLARI
# ═══════════════════════════════════════════════════════

AGIRLIKLAR = {
    "MA_Sistemi":  2.5,   # Trend yonu (en onemli)
    "MACD":        1.8,   # Trend teyidi
    "ADX":         1.5,   # Trend gucu
    "Momentum":    1.5,   # Fiyat ivmesi (YENİ)
    "RSI":         1.2,   # Asiri alim/satim
    "Hacim":       1.2,   # Hacim teyidi (artirildi)
    "OBV":         1.0,   # Hacim trendi (artirildi)
    "Bollinger":   0.8,   # Bant pozisyonu (azaltildi)
    "Stochastic":  0.7,   # Osilator (azaltildi)
    "CCI":         0.5,   # Osilator (azaltildi)
    "Williams_R":  0.5,   # Osilator (azaltildi, Stoch ile cakisiyor)
    "ATR":         0.0,   # Sadece bilgi amacli, skorlama disi
}

TOPLAM_AGIRLIK = sum(v for v in AGIRLIKLAR.values() if v > 0)  # ATR haric

# Sinyal eşikleri (düşürüldü — eski değerler çok yüksekti)
ESIK_GUCLU_AL  =  0.30   # eskisi 0.40
ESIK_ZAYIF_AL  =  0.10   # eskisi 0.15
ESIK_ZAYIF_SAT = -0.10   # eskisi -0.15
ESIK_GUCLU_SAT = -0.30   # eskisi -0.40

# ─── Sürekli Çalışma Ayarları ───
ANALIZ_ARALIK_DK   = 10    # Kaç dakikada bir analiz yap
RAPOR_ARALIK_DK    = 60    # Kaç dakikada bir Telegram rapor gönder
BORSA_ACILIS       = (10, 0)   # 10:00
BORSA_KAPANIS      = (18, 10)  # 18:10 (kapanış seansı dahil)

# ─── Pozisyon Takip Ayarları ───
# Zaten AL sinyali olan hisse için tekrar AL gönderme eşiği
TEKRAR_AL_MIN_GUVEN_ARTISI = 15.0   # Mevcut güvenden en az %15 artış olmalı
TEKRAR_AL_MIN_GUVEN        = 60.0   # Veya mutlak güven %60+ olmalı

# ═══════════════════════════════════════════════════════
# VERİ SINIFI
# ═══════════════════════════════════════════════════════

@dataclass
class IndikatorSonuc:
    ad: str
    deger: float
    sinyal: str        # "AL" | "SAT" | "NOTR"
    aciklama: str
    agirlik: float

    @property
    def skor(self) -> float:
        return {"AL": 1, "NOTR": 0, "SAT": -1}.get(self.sinyal, 0) * self.agirlik


@dataclass
class HisseAnaliz:
    sembol: str
    fiyat: float
    tarih: str
    skor: float
    sinyal: str        # GUCLU_AL, ZAYIF_AL, NOTR, ZAYIF_SAT, GUCLU_SAT
    guven: float       # 0-100%
    stop_loss: float
    hedef: float
    atr: float
    indikatörler: list  # IndikatorSonuc listesi
    veri_kaynagi: str   # "yfinance" | "collectapi"


# ═══════════════════════════════════════════════════════
# VERİ ÇEKİCİ
# ═══════════════════════════════════════════════════════

class VeriCekici:
    """BIST hisse verilerini yfinance'den çeker, bulamazsa alternatif dener."""

    @staticmethod
    def yfinance_cek(sembol: str, period: str = "6mo", interval: str = "1d") -> Optional[pd.DataFrame]:
        """Yahoo Finance'den OHLCV veri çeker."""
        ticker = f"{sembol}.IS"
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False, timeout=10)
            if df is None or df.empty or len(df) < 30:
                return None
            
            # MultiIndex column fix (yfinance 0.2.32+)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            df = df.rename(columns={
                "Open": "Acilis", "High": "Yuksek", "Low": "Dusuk",
                "Close": "Kapanis", "Volume": "Hacim"
            })
            
            # Gerekli kolonlar
            for col in ["Acilis", "Yuksek", "Dusuk", "Kapanis", "Hacim"]:
                if col not in df.columns:
                    return None
            
            df = df[["Acilis", "Yuksek", "Dusuk", "Kapanis", "Hacim"]].dropna()
            if len(df) < 30:
                return None
            
            return df
        except Exception as e:
            log.debug(f"{sembol} yfinance hata: {e}")
            return None

    @staticmethod
    def collectapi_cek(sembol: str) -> Optional[pd.DataFrame]:
        """
        CollectAPI (Türkiye borsası) ile günlük veri çeker.
        Ücretsiz katmanda günlük 100 istek hakkı var.
        API key gerektirir: COLLECTAPI_KEY ortam değişkeni
        """
        api_key = os.getenv("COLLECTAPI_KEY", "")
        if not api_key:
            return None

        try:
            url = f"https://api.collectapi.com/economy/hpiStock?stock={sembol}"
            headers = {
                "content-type": "application/json",
                "authorization": f"apikey {api_key}"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None

            data = resp.json()
            if not data.get("success"):
                return None

            result = data.get("result", {})
            # CollectAPI tek günlük veri döner, geçmiş verisi sınırlı
            # Sadece son fiyat bilgisi alınabilir
            return None  # Geçmiş veri yetersiz, yfinance tercih et
        except Exception:
            return None

    @staticmethod
    def veri_getir(sembol: str, period: str = "6mo") -> tuple[Optional[pd.DataFrame], str]:
        """
        Smart fallback: yfinance -> collectapi -> None
        Returns (DataFrame, kaynak_adi)
        """
        # 1. yfinance
        df = VeriCekici.yfinance_cek(sembol, period=period)
        if df is not None:
            return df, "yfinance"

        # 2. Alternatif ticker dene (.E suffix)
        try:
            ticker_alt = f"{sembol}.E"
            df_alt = yf.download(ticker_alt, period=period, interval="1d", progress=False, timeout=10)
            if df_alt is not None and not df_alt.empty and len(df_alt) >= 30:
                if isinstance(df_alt.columns, pd.MultiIndex):
                    df_alt.columns = df_alt.columns.get_level_values(0)
                df_alt = df_alt.rename(columns={
                    "Open": "Acilis", "High": "Yuksek", "Low": "Dusuk",
                    "Close": "Kapanis", "Volume": "Hacim"
                })
                df_alt = df_alt[["Acilis", "Yuksek", "Dusuk", "Kapanis", "Hacim"]].dropna()
                if len(df_alt) >= 30:
                    return df_alt, "yfinance_alt"
        except Exception:
            pass

        # 3. collectapi (API key varsa)
        df_c = VeriCekici.collectapi_cek(sembol)
        if df_c is not None:
            return df_c, "collectapi"

        return None, "yok"


# ═══════════════════════════════════════════════════════
# TEKNİK ANALİZ MOTORU
# ═══════════════════════════════════════════════════════

class TeknikAnalizMotoru:
    """11 indikatörlü ağırlıklı teknik analiz motoru."""

    def __init__(self, df: pd.DataFrame, sembol: str):
        self.df = df.copy().sort_index()
        self.sembol = sembol
        self.k = self.df["Kapanis"]
        self.h = self.df["Yuksek"]
        self.l = self.df["Dusuk"]
        self.v = self.df["Hacim"]

    # ─── 1. MA Sistemi ───
    def ma_sinyal(self) -> IndikatorSonuc:
        k = self.k
        ma7  = k.rolling(7).mean()
        ma21 = k.rolling(21).mean()
        ma50 = k.rolling(50).mean()

        if len(k) < 50:
            return IndikatorSonuc("MA_Sistemi", 0, "NOTR", "Yetersiz veri (<50 bar)", AGIRLIKLAR["MA_Sistemi"])

        son = float(k.iloc[-1])
        v7, v21, v50 = float(ma7.iloc[-1]), float(ma21.iloc[-1]), float(ma50.iloc[-1])

        # MA200 opsiyonel
        if len(k) >= 200:
            ma200 = k.rolling(200).mean()
            v200 = float(ma200.iloc[-1])
            gc_simdi = ma50.iloc[-1] > ma200.iloc[-1]
            gc_once  = ma50.iloc[-2] > ma200.iloc[-2]
            if gc_simdi and not gc_once:
                return IndikatorSonuc("MA_Sistemi", son, "AL", f"GOLDEN CROSS MA50({v50:.2f})>MA200({v200:.2f})", AGIRLIKLAR["MA_Sistemi"])
            elif not gc_simdi and gc_once:
                return IndikatorSonuc("MA_Sistemi", son, "SAT", f"DEATH CROSS MA50({v50:.2f})<MA200({v200:.2f})", AGIRLIKLAR["MA_Sistemi"])

        if son > v7 > v21 > v50:
            return IndikatorSonuc("MA_Sistemi", son, "AL", f"Fiyat tum MA'larin ustunde (guclu trend)", AGIRLIKLAR["MA_Sistemi"])
        elif son < v7 < v21 < v50:
            return IndikatorSonuc("MA_Sistemi", son, "SAT", f"Fiyat tum MA'larin altinda (dusus trendi)", AGIRLIKLAR["MA_Sistemi"])
        elif son > v50:
            return IndikatorSonuc("MA_Sistemi", son, "AL", f"Fiyat MA50({v50:.2f}) ustunde", AGIRLIKLAR["MA_Sistemi"])
        elif son < v50:
            return IndikatorSonuc("MA_Sistemi", son, "SAT", f"Fiyat MA50({v50:.2f}) altinda", AGIRLIKLAR["MA_Sistemi"])
        else:
            return IndikatorSonuc("MA_Sistemi", son, "NOTR", "MA sistemi karisik", AGIRLIKLAR["MA_Sistemi"])

    # ─── 2. RSI ───
    def rsi_sinyal(self, period=14) -> IndikatorSonuc:
        delta = self.k.diff()
        kazan = delta.clip(lower=0)
        kayip = -delta.clip(upper=0)
        avg_k = kazan.ewm(com=period-1, min_periods=period).mean()
        avg_y = kayip.ewm(com=period-1, min_periods=period).mean()
        rs = avg_k / avg_y.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        val = round(float(rsi.iloc[-1]), 2)
        if val < 25:
            return IndikatorSonuc("RSI", val, "AL", f"RSI={val} asiri satim (<25)", AGIRLIKLAR["RSI"])
        elif val > 75:
            return IndikatorSonuc("RSI", val, "SAT", f"RSI={val} asiri alim (>75)", AGIRLIKLAR["RSI"])
        return IndikatorSonuc("RSI", val, "NOTR", f"RSI={val} notr (25-75)", AGIRLIKLAR["RSI"])

    # ─── 3. MACD ───
    def macd_sinyal(self) -> IndikatorSonuc:
        ema12 = self.k.ewm(span=12, adjust=False).mean()
        ema26 = self.k.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal

        h_val = round(float(hist.iloc[-1]), 4)
        h_prev = round(float(hist.iloc[-2]), 4)

        if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
            return IndikatorSonuc("MACD", h_val, "AL", "MACD yukari kesti (bullish crossover)", AGIRLIKLAR["MACD"])
        elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
            return IndikatorSonuc("MACD", h_val, "SAT", "MACD asagi kesti (bearish crossover)", AGIRLIKLAR["MACD"])
        elif h_val > 0 and h_val > h_prev:
            return IndikatorSonuc("MACD", h_val, "AL", f"Histogram pozitif ve artiyor ({h_val:+.4f})", AGIRLIKLAR["MACD"])
        elif h_val < 0 and h_val < h_prev:
            return IndikatorSonuc("MACD", h_val, "SAT", f"Histogram negatif ve azaliyor ({h_val:+.4f})", AGIRLIKLAR["MACD"])
        return IndikatorSonuc("MACD", h_val, "NOTR", f"MACD belirsiz (hist={h_val:+.4f})", AGIRLIKLAR["MACD"])

    # ─── 4. ADX ───
    def adx_sinyal(self, period=14) -> IndikatorSonuc:
        if len(self.df) < period * 3:
            return IndikatorSonuc("ADX", 0, "NOTR", "Yetersiz veri", AGIRLIKLAR["ADX"])

        plus_dm = self.h.diff().clip(lower=0)
        minus_dm = (-self.l.diff()).clip(lower=0)
        tr = pd.concat([self.h - self.l, (self.h - self.k.shift()).abs(), (self.l - self.k.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()

        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.rolling(period).mean()

        val = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 0
        if val > 25:
            sinyal = "AL" if float(plus_di.iloc[-1]) > float(minus_di.iloc[-1]) else "SAT"
            return IndikatorSonuc("ADX", round(val, 1), sinyal, f"Guclu trend ADX={val:.1f}", AGIRLIKLAR["ADX"])
        return IndikatorSonuc("ADX", round(val, 1), "NOTR", f"Zayif trend ADX={val:.1f}", AGIRLIKLAR["ADX"])

    # ─── 5. ATR ───
    def atr_hesapla(self, period=14) -> float:
        tr = pd.concat([self.h - self.l, (self.h - self.k.shift()).abs(), (self.l - self.k.shift()).abs()], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean()
        return round(float(atr.iloc[-1]), 4)

    def atr_sinyal(self) -> IndikatorSonuc:
        """ATR artık sadece bilgi amaçlı — yüksek volatilite yanlış SAT sinyali üretiyordu."""
        atr_val = self.atr_hesapla()
        son_fiyat = float(self.k.iloc[-1])
        atr_pct = (atr_val / son_fiyat) * 100 if son_fiyat > 0 else 0

        if atr_pct > 5.0:
            aciklama = f"Yuksek volatilite %{atr_pct:.2f} (bilgi)"
        elif atr_pct > 3.0:
            aciklama = f"Normal volatilite %{atr_pct:.2f}"
        elif atr_pct < 1.5:
            aciklama = f"Dusuk volatilite %{atr_pct:.2f} (sikisma)"
        else:
            aciklama = f"Volatilite %{atr_pct:.2f}"
        return IndikatorSonuc("ATR", round(atr_pct, 2), "NOTR", aciklama, AGIRLIKLAR["ATR"])

    # ─── 6. Bollinger Bands ───
    def bollinger_sinyal(self, period=20) -> IndikatorSonuc:
        orta = self.k.rolling(period).mean()
        std = self.k.rolling(period).std()
        ust = orta + 2.0 * std
        alt = orta - 2.0 * std

        son = float(self.k.iloc[-1])
        u, a = float(ust.iloc[-1]), float(alt.iloc[-1])
        pct_b = (son - a) / (u - a) if (u - a) > 0 else 0.5

        # Band walk tespiti: son 5 gün %B > 0.8 ise trend yürüyüşü
        if len(self.k) >= 5:
            recent_b = []
            for i in range(-5, 0):
                s_i = float(self.k.iloc[i])
                u_i = float(ust.iloc[i])
                a_i = float(alt.iloc[i])
                b_i = (s_i - a_i) / (u_i - a_i) if (u_i - a_i) > 0 else 0.5
                recent_b.append(b_i)
            avg_b = sum(recent_b) / len(recent_b)
            if avg_b > 0.75 and pct_b > 0.8:
                return IndikatorSonuc("Bollinger", round(pct_b, 3), "AL",
                    f"Band walk — ust bant boyunca trend %B={pct_b:.2f}", AGIRLIKLAR["Bollinger"])

        if pct_b < 0.05:
            return IndikatorSonuc("Bollinger", round(pct_b, 3), "AL", f"Fiyat alt bandin altinda (geri tepme)", AGIRLIKLAR["Bollinger"])
        elif pct_b < 0.2:
            return IndikatorSonuc("Bollinger", round(pct_b, 3), "AL", f"Fiyat alt banda yakin %B={pct_b:.2f}", AGIRLIKLAR["Bollinger"])
        elif pct_b > 1.05:
            return IndikatorSonuc("Bollinger", round(pct_b, 3), "NOTR", f"Fiyat ust bandin ustunde (momentum) %B={pct_b:.2f}", AGIRLIKLAR["Bollinger"])
        elif pct_b > 0.8:
            return IndikatorSonuc("Bollinger", round(pct_b, 3), "NOTR", f"Fiyat ust bant bolgesi %B={pct_b:.2f}", AGIRLIKLAR["Bollinger"])
        return IndikatorSonuc("Bollinger", round(pct_b, 3), "NOTR", f"%B={pct_b:.2f} bant ortasi", AGIRLIKLAR["Bollinger"])

    # ─── 7. Stochastic ───
    def stochastic_sinyal(self, k_period=14, d_period=3) -> IndikatorSonuc:
        low_min = self.l.rolling(k_period).min()
        high_max = self.h.rolling(k_period).max()
        denom = (high_max - low_min).replace(0, np.nan)
        k_line = 100 * (self.k - low_min) / denom
        d_line = k_line.rolling(d_period).mean()

        kv = float(k_line.iloc[-1]) if not pd.isna(k_line.iloc[-1]) else 50
        dv = float(d_line.iloc[-1]) if not pd.isna(d_line.iloc[-1]) else 50

        if kv < 25 and kv > dv:
            return IndikatorSonuc("Stochastic", round(kv, 1), "AL", f"K={kv:.0f} asiri satimda, D'yi yukari kesti", AGIRLIKLAR["Stochastic"])
        elif kv < 25:
            return IndikatorSonuc("Stochastic", round(kv, 1), "AL", f"K={kv:.0f} asiri satim bolgesi", AGIRLIKLAR["Stochastic"])
        elif kv > 75 and kv < dv:
            return IndikatorSonuc("Stochastic", round(kv, 1), "SAT", f"K={kv:.0f} asiri alimda, D'yi asagi kesti", AGIRLIKLAR["Stochastic"])
        elif kv > 90:
            return IndikatorSonuc("Stochastic", round(kv, 1), "SAT", f"K={kv:.0f} ekstrem alim bolgesi", AGIRLIKLAR["Stochastic"])
        elif kv > 75:
            return IndikatorSonuc("Stochastic", round(kv, 1), "NOTR", f"Stoch K={kv:.0f} ust bolgede", AGIRLIKLAR["Stochastic"])
        return IndikatorSonuc("Stochastic", round(kv, 1), "NOTR", f"Stoch K={kv:.0f} notr", AGIRLIKLAR["Stochastic"])

    # ─── 8. CCI ───
    def cci_sinyal(self, period=20) -> IndikatorSonuc:
        tp = (self.h + self.l + self.k) / 3
        sma = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
        cci = (tp - sma) / (0.015 * mad)

        val = float(cci.iloc[-1]) if not pd.isna(cci.iloc[-1]) else 0
        if val < -150:
            return IndikatorSonuc("CCI", round(val, 1), "AL", f"CCI={val:.0f} asiri satim", AGIRLIKLAR["CCI"])
        elif val > 200:
            return IndikatorSonuc("CCI", round(val, 1), "SAT", f"CCI={val:.0f} ekstrem alim", AGIRLIKLAR["CCI"])
        elif val > 100:
            return IndikatorSonuc("CCI", round(val, 1), "NOTR", f"CCI={val:.0f} yukari momentum", AGIRLIKLAR["CCI"])
        elif val < -100:
            return IndikatorSonuc("CCI", round(val, 1), "NOTR", f"CCI={val:.0f} asagi momentum", AGIRLIKLAR["CCI"])
        return IndikatorSonuc("CCI", round(val, 1), "NOTR", f"CCI={val:.0f} notr", AGIRLIKLAR["CCI"])

    # ─── 9. Williams %R ───
    def williams_r_sinyal(self, period=14) -> IndikatorSonuc:
        hmax = self.h.rolling(period).max()
        lmin = self.l.rolling(period).min()
        denom = (hmax - lmin).replace(0, np.nan)
        wr = -100 * (hmax - self.k) / denom

        val = float(wr.iloc[-1]) if not pd.isna(wr.iloc[-1]) else -50
        if val < -85:
            return IndikatorSonuc("Williams_R", round(val, 1), "AL", f"W%R={val:.0f} asiri satim", AGIRLIKLAR["Williams_R"])
        elif val > -5:
            return IndikatorSonuc("Williams_R", round(val, 1), "SAT", f"W%R={val:.0f} ekstrem alim", AGIRLIKLAR["Williams_R"])
        elif val > -15:
            return IndikatorSonuc("Williams_R", round(val, 1), "NOTR", f"W%R={val:.0f} ust bolge", AGIRLIKLAR["Williams_R"])
        return IndikatorSonuc("Williams_R", round(val, 1), "NOTR", f"W%R={val:.0f} notr", AGIRLIKLAR["Williams_R"])

    # ─── 10. Hacim Analizi ───
    def hacim_sinyal(self, period=20) -> IndikatorSonuc:
        ort = self.v.rolling(period).mean()
        son_hacim = float(self.v.iloc[-1])
        ort_val = float(ort.iloc[-1]) if not pd.isna(ort.iloc[-1]) else 1
        oran = son_hacim / ort_val if ort_val > 0 else 1.0
        fiyat_degisim = float(self.k.iloc[-1]) - float(self.k.iloc[-2])

        if oran > 1.5 and fiyat_degisim > 0:
            return IndikatorSonuc("Hacim", round(oran, 2), "AL", f"Yuksek hacimli yukselme ({oran:.1f}x ort.)", AGIRLIKLAR["Hacim"])
        elif oran > 1.5 and fiyat_degisim < 0:
            return IndikatorSonuc("Hacim", round(oran, 2), "SAT", f"Yuksek hacimli dusus ({oran:.1f}x ort.)", AGIRLIKLAR["Hacim"])
        return IndikatorSonuc("Hacim", round(oran, 2), "NOTR", f"Hacim normal ({oran:.1f}x ort.)", AGIRLIKLAR["Hacim"])

    # ─── 11. OBV (On Balance Volume) ───
    def obv_sinyal(self) -> IndikatorSonuc:
        direction = np.sign(self.k.diff())
        obv = (self.v * direction).cumsum()
        obv_ma = obv.rolling(20).mean()

        if len(obv) < 21:
            return IndikatorSonuc("OBV", 0, "NOTR", "Yetersiz veri", AGIRLIKLAR["OBV"])

        obv_val = float(obv.iloc[-1])
        obv_ma_val = float(obv_ma.iloc[-1])

        if obv_val > obv_ma_val * 1.1:
            return IndikatorSonuc("OBV", round(obv_val, 0), "AL", "OBV trendi yukari (alim baskisi)", AGIRLIKLAR["OBV"])
        elif obv_val < obv_ma_val * 0.9:
            return IndikatorSonuc("OBV", round(obv_val, 0), "SAT", "OBV trendi asagi (satim baskisi)", AGIRLIKLAR["OBV"])
        return IndikatorSonuc("OBV", round(obv_val, 0), "NOTR", "OBV notr", AGIRLIKLAR["OBV"])

    # ─── 12. Momentum (YENİ) ───
    def momentum_sinyal(self) -> IndikatorSonuc:
        """Fiyat ivmesi: 5 ve 20 günlük getiri + hacim teyidi."""
        if len(self.k) < 21:
            return IndikatorSonuc("Momentum", 0, "NOTR", "Yetersiz veri", AGIRLIKLAR["Momentum"])

        son = float(self.k.iloc[-1])
        fiyat_5g = float(self.k.iloc[-6]) if len(self.k) >= 6 else son
        fiyat_20g = float(self.k.iloc[-21]) if len(self.k) >= 21 else son

        getiri_5g = ((son - fiyat_5g) / fiyat_5g * 100) if fiyat_5g > 0 else 0
        getiri_20g = ((son - fiyat_20g) / fiyat_20g * 100) if fiyat_20g > 0 else 0

        # Hacim teyidi: son 5 gün ortalama hacim vs 20 gün
        hacim_5g = float(self.v.iloc[-5:].mean()) if len(self.v) >= 5 else 0
        hacim_20g = float(self.v.iloc[-20:].mean()) if len(self.v) >= 20 else 1
        hacim_oran = hacim_5g / hacim_20g if hacim_20g > 0 else 1.0

        # Güçlü momentum: pozitif getiri + artan hacim
        if getiri_5g > 5.0 and hacim_oran > 1.2:
            return IndikatorSonuc("Momentum", round(getiri_5g, 2), "AL",
                f"Guclu ivme +{getiri_5g:.1f}% (5g) hacim {hacim_oran:.1f}x", AGIRLIKLAR["Momentum"])
        elif getiri_5g > 3.0:
            return IndikatorSonuc("Momentum", round(getiri_5g, 2), "AL",
                f"Pozitif ivme +{getiri_5g:.1f}% (5g) 20g:{getiri_20g:+.1f}%", AGIRLIKLAR["Momentum"])
        elif getiri_5g < -5.0 and hacim_oran > 1.2:
            return IndikatorSonuc("Momentum", round(getiri_5g, 2), "SAT",
                f"Guclu dusus {getiri_5g:.1f}% (5g) hacim {hacim_oran:.1f}x", AGIRLIKLAR["Momentum"])
        elif getiri_5g < -3.0:
            return IndikatorSonuc("Momentum", round(getiri_5g, 2), "SAT",
                f"Negatif ivme {getiri_5g:.1f}% (5g) 20g:{getiri_20g:+.1f}%", AGIRLIKLAR["Momentum"])
        return IndikatorSonuc("Momentum", round(getiri_5g, 2), "NOTR",
            f"Ivme {getiri_5g:+.1f}% (5g) 20g:{getiri_20g:+.1f}%", AGIRLIKLAR["Momentum"])

    # ─── TAM ANALİZ ───
    def analiz_et(self) -> HisseAnaliz:
        indikatörler = [
            self.ma_sinyal(),
            self.rsi_sinyal(),
            self.macd_sinyal(),
            self.adx_sinyal(),
            self.atr_sinyal(),
            self.bollinger_sinyal(),
            self.stochastic_sinyal(),
            self.cci_sinyal(),
            self.williams_r_sinyal(),
            self.hacim_sinyal(),
            self.obv_sinyal(),
            self.momentum_sinyal(),
        ]

        # ─── Trend Kontekst Tespiti ───
        # MA ve MACD aynı yönde ise "confirmed trend" moduna gir
        ma_sonuc = indikatörler[0]   # MA_Sistemi
        macd_sonuc = indikatörler[2]  # MACD
        adx_sonuc = indikatörler[3]   # ADX

        trend_up = (ma_sonuc.sinyal == "AL" and macd_sonuc.sinyal == "AL")
        trend_down = (ma_sonuc.sinyal == "SAT" and macd_sonuc.sinyal == "SAT")

        # ─── Kontekst Düzeltmesi ───
        # Osilatörlerin trend içinde yanlış sinyal vermesini engelle
        osilator_adlari = {"Stochastic", "CCI", "Williams_R"}
        if trend_up:
            for i, ind in enumerate(indikatörler):
                if ind.ad in osilator_adlari and ind.sinyal == "SAT":
                    # Güçlü trend içinde osilatör SAT → NOTR'a düşür
                    indikatörler[i] = IndikatorSonuc(
                        ind.ad, ind.deger, "NOTR",
                        f"{ind.aciklama} (trend icinde notr)",
                        ind.agirlik
                    )
        elif trend_down:
            for i, ind in enumerate(indikatörler):
                if ind.ad in osilator_adlari and ind.sinyal == "AL":
                    indikatörler[i] = IndikatorSonuc(
                        ind.ad, ind.deger, "NOTR",
                        f"{ind.aciklama} (dusus trendinde notr)",
                        ind.agirlik
                    )

        toplam_skor = sum(i.skor for i in indikatörler)
        skor = round(toplam_skor / TOPLAM_AGIRLIK, 3)

        if skor >= ESIK_GUCLU_AL:
            sinyal = "GUCLU_AL"
        elif skor >= ESIK_ZAYIF_AL:
            sinyal = "ZAYIF_AL"
        elif skor <= ESIK_GUCLU_SAT:
            sinyal = "GUCLU_SAT"
        elif skor <= ESIK_ZAYIF_SAT:
            sinyal = "ZAYIF_SAT"
        else:
            sinyal = "NOTR"

        son_fiyat = round(float(self.k.iloc[-1]), 2)
        atr = self.atr_hesapla()
        stop_loss = round(son_fiyat - 1.5 * atr, 2)
        hedef = round(son_fiyat + 2.0 * atr, 2)
        guven = round(abs(skor) * 100, 1)

        return HisseAnaliz(
            sembol=self.sembol,
            fiyat=son_fiyat,
            tarih=str(self.df.index[-1].date()) if hasattr(self.df.index[-1], 'date') else str(self.df.index[-1])[:10],
            skor=skor,
            sinyal=sinyal,
            guven=guven,
            stop_loss=stop_loss,
            hedef=hedef,
            atr=atr,
            indikatörler=indikatörler,
            veri_kaynagi="",
        )


# ═══════════════════════════════════════════════════════
# TELEGRAM GÖNDERİCİ
# ═══════════════════════════════════════════════════════

class TelegramGonderici:
    """Telegram Bot API ile mesaj gönderici. Uzun mesajları otomatik böler."""

    MAX_MSG_LEN = 4000  # Telegram limiti 4096, güvenlik payı

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"

    def gonder(self, metin: str) -> bool:
        """Mesajı Telegram'a gönderir. Uzunsa otomatik böler."""
        parcalar = self._bol(metin)
        basarili = True
        for parca in parcalar:
            if not self._tek_gonder(parca):
                basarili = False
            time.sleep(0.5)  # Rate limit
        return basarili

    def _tek_gonder(self, metin: str) -> bool:
        try:
            resp = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": metin,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                return True
            else:
                log.warning(f"Telegram API {resp.status_code}: {resp.text[:200]}")
                # HTML parse hatası varsa plain text olarak dene
                if "can't parse entities" in resp.text.lower():
                    resp2 = requests.post(
                        f"{self.base_url}/sendMessage",
                        json={"chat_id": self.chat_id, "text": metin},
                        timeout=15,
                    )
                    return resp2.status_code == 200
                return False
        except Exception as e:
            log.error(f"Telegram gonderme hatasi: {e}")
            return False

    def _bol(self, metin: str) -> list[str]:
        """Mesajı Telegram limitine göre böler."""
        if len(metin) <= self.MAX_MSG_LEN:
            return [metin]

        parcalar = []
        satırlar = metin.split('\n')
        mevcut = ""

        for satir in satırlar:
            if len(mevcut) + len(satir) + 1 > self.MAX_MSG_LEN:
                if mevcut:
                    parcalar.append(mevcut)
                mevcut = satir
            else:
                mevcut = mevcut + "\n" + satir if mevcut else satir

        if mevcut:
            parcalar.append(mevcut)

        return parcalar


# ═══════════════════════════════════════════════════════
# RAPOR OLUŞTURUCU
# ═══════════════════════════════════════════════════════

class RaporOlusturucu:
    """Analiz sonuçlarından Telegram raporu oluşturur."""

    SINYAL_EMOJI = {
        "GUCLU_AL":  "🟢",
        "ZAYIF_AL":  "📗",
        "NOTR":      "⏸️",
        "ZAYIF_SAT": "📕",
        "GUCLU_SAT": "🔴",
    }

    SINYAL_LABEL = {
        "GUCLU_AL":  "GUCLU AL",
        "ZAYIF_AL":  "ZAYIF AL",
        "NOTR":      "NOTR",
        "ZAYIF_SAT": "ZAYIF SAT",
        "GUCLU_SAT": "GUCLU SAT",
    }

    @staticmethod
    def _kisa_neden(s: 'HisseAnaliz') -> str:
        """Hissenin en belirleyici 2 indikatörünü kısa döndürür."""
        al_ind  = [i for i in s.indikatörler if i.sinyal == "AL"]
        sat_ind = [i for i in s.indikatörler if i.sinyal == "SAT"]
        notr_ind = [i for i in s.indikatörler if i.sinyal == "NOTR"]

        if s.sinyal in ("GUCLU_AL", "ZAYIF_AL"):
            top = sorted(al_ind, key=lambda x: x.agirlik, reverse=True)[:2]
            return ", ".join(i.ad for i in top) if top else "karisik sinyaller"
        elif s.sinyal in ("GUCLU_SAT", "ZAYIF_SAT"):
            top = sorted(sat_ind, key=lambda x: x.agirlik, reverse=True)[:2]
            return ", ".join(i.ad for i in top) if top else "karisik sinyaller"
        else:  # NOTR
            return f"{len(al_ind)} AL / {len(notr_ind)} notr / {len(sat_ind)} SAT → denge"

    @staticmethod
    def ozet_rapor(sonuclar: list['HisseAnaliz'], basarisiz: list[str]) -> str:
        """Genel özet rapor — detaylı analiz sadece güven ≥%50 AL sinyallerine."""
        now = datetime.now()

        # >= %50 güven ile AL sinyali verenler → detaylı raporlanacak
        detay_al = [s for s in sonuclar
                    if s.sinyal in ("GUCLU_AL", "ZAYIF_AL") and s.guven >= 50]
        detay_al.sort(key=lambda x: x.skor, reverse=True)

        # Geri kalanlar kısa listelenir
        zayif_al  = [s for s in sonuclar
                     if s.sinyal in ("GUCLU_AL", "ZAYIF_AL") and s.guven < 50]
        notr      = [s for s in sonuclar if s.sinyal == "NOTR"]
        zayif_sat = [s for s in sonuclar if s.sinyal == "ZAYIF_SAT"]
        guclu_sat = [s for s in sonuclar if s.sinyal == "GUCLU_SAT"]

        rapor = f"""🚀 <b>BIST FULL ANALİZ RAPORU</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ {now:%H:%M:%S} | 📅 {now:%d.%m.%Y}
📊 Analiz: {len(sonuclar)}/{len(sonuclar)+len(basarisiz)} hisse
📡 Veri: Yahoo Finance (son islem gunu kapanis)
🧠 Motor: v2 (12 indikator + trend kontekst)

🟢 <b>AL (guven 50%+):</b> {len(detay_al)} hisse - detayli rapor
📗 <b>ZAYIF AL (50% alti):</b> {len(zayif_al)} hisse
⏸️ <b>NOTR:</b> {len(notr)} hisse (indikatorler dengede)
📕 <b>ZAYIF SAT:</b> {len(zayif_sat)} hisse
🔴 <b>GUCLU SAT:</b> {len(guclu_sat)} hisse
━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

        # ── Detaylı AL sinyalleri (kısa önizleme) ──
        if detay_al:
            rapor += "\n\n🟢 <b>AL SİNYALLERİ (detay asagida):</b>"
            for s in detay_al:
                kar_pct = ((s.hedef - s.fiyat) / s.fiyat * 100) if s.fiyat > 0 else 0
                rapor += f"\n  • <b>{s.sembol}</b> {s.fiyat:.2f}₺ | %{s.guven:.0f} guven | Hedef: {s.hedef:.2f}₺ (+{kar_pct:.1f}%)"

        # ── Zayıf AL (kısa liste) ──
        if zayif_al:
            rapor += f"\n\n📗 <b>ZAYIF AL ({len(zayif_al)}):</b>"
            for s in sorted(zayif_al, key=lambda x: x.skor, reverse=True):
                neden = RaporOlusturucu._kisa_neden(s)
                rapor += f"\n  • {s.sembol} {s.fiyat:.2f}₺ %{s.guven:.0f} ({neden})"

        # ── NOTR (kısa liste + açıklama) ──
        if notr:
            rapor += f"\n\n⏸️ <b>NOTR ({len(notr)}) — indikatorler dengede:</b>"
            for s in sorted(notr, key=lambda x: x.skor, reverse=True):
                neden = RaporOlusturucu._kisa_neden(s)
                rapor += f"\n  • {s.sembol} {s.fiyat:.2f}₺ ({neden})"

        # ── Zayıf SAT (kısa liste) ──
        if zayif_sat:
            rapor += f"\n\n📕 <b>ZAYIF SAT ({len(zayif_sat)}):</b>"
            for s in sorted(zayif_sat, key=lambda x: x.skor):
                neden = RaporOlusturucu._kisa_neden(s)
                rapor += f"\n  • {s.sembol} {s.fiyat:.2f}₺ %{s.guven:.0f} ({neden})"

        # ── Güçlü SAT (kısa liste) ──
        if guclu_sat:
            rapor += f"\n\n🔴 <b>GUCLU SAT ({len(guclu_sat)}):</b>"
            for s in sorted(guclu_sat, key=lambda x: x.skor):
                neden = RaporOlusturucu._kisa_neden(s)
                rapor += f"\n  • {s.sembol} {s.fiyat:.2f}₺ %{s.guven:.0f} ({neden})"

        if basarisiz:
            rapor += f"\n\n⚠️ Veri cekilemeyen: {len(basarisiz)} hisse"

        if detay_al:
            rapor += f"\n\n🤖 <i>BistBot | {len(detay_al)} detayli rapor asagida...</i>"
        else:
            rapor += f"\n\n🤖 <i>BistBot | 50%+ guvenle AL sinyali bulunamadi.</i>"
        return rapor

    @staticmethod
    def hisse_detay_rapor(s: HisseAnaliz) -> str:
        """Tek hisse için detaylı rapor."""
        emoji = RaporOlusturucu.SINYAL_EMOJI.get(s.sinyal, "❓")
        label = RaporOlusturucu.SINYAL_LABEL.get(s.sinyal, s.sinyal)

        kar_pct = ((s.hedef - s.fiyat) / s.fiyat * 100) if s.fiyat > 0 else 0
        risk_pct = ((s.fiyat - s.stop_loss) / s.fiyat * 100) if s.fiyat > 0 else 0
        rr_ratio = kar_pct / risk_pct if risk_pct > 0 else 0

        rapor = f"""{emoji} <b>{s.sembol}</b> | {label}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
💹 Fiyat: <b>{s.fiyat:.2f}₺</b>
📈 Hedef: {s.hedef:.2f}₺ (+{kar_pct:.1f}%)
🛑 Stop: {s.stop_loss:.2f}₺ (-{risk_pct:.1f}%)
⚖️ Odül/Risk: {rr_ratio:.2f}:1
🎯 Skor: {s.skor:+.3f} | Guven: %{s.guven:.0f}
📅 Tarih: {s.tarih} | Kaynak: {s.veri_kaynagi}
"""

        # İndikatör detayları
        al_list = [i for i in s.indikatörler if i.sinyal == "AL"]
        sat_list = [i for i in s.indikatörler if i.sinyal == "SAT"]

        if al_list:
            rapor += "\n📊 <b>AL Sinyalleri:</b>"
            for i in al_list:
                rapor += f"\n  ✅ {i.ad}: {i.aciklama}"

        if sat_list:
            rapor += "\n\n📊 <b>SAT Sinyalleri:</b>"
            for i in sat_list:
                rapor += f"\n  ❌ {i.ad}: {i.aciklama}"

        return rapor


# ═══════════════════════════════════════════════════════
# MOCK TRADING ENGINE (Sanal Al-Sat Simülasyonu)
# ═══════════════════════════════════════════════════════

MOCK_BASLANGIC_BAKIYE = 10_000.0  # 10.000 TL
MOCK_RISK_ORANI       = 0.02      # İşlem başına %2 risk
MOCK_MIN_RR           = 1.5       # Minimum Risk/Reward oranı
MOCK_MAX_POZISYON     = 5         # Aynı anda max açık pozisyon
MOCK_KOMISYON_ORANI   = 0.002     # %0.2 komisyon (alış+satış)

@dataclass
class MockIslem:
    sembol: str
    yon: str               # "AL"
    giris_fiyat: float
    lot: float             # Kaç adet
    maliyet: float         # Toplam giriş maliyeti (komisyon dahil)
    stop_loss: float
    hedef: float
    rr_orani: float        # Risk/Reward
    giris_guven: float
    giris_skor: float
    giris_zamani: str
    durum: str = "ACIK"    # ACIK, HEDEF, STOP, SINYAL_CIKIS
    cikis_fiyat: float = 0.0
    cikis_zamani: str = ""
    kar_zarar: float = 0.0
    kar_zarar_pct: float = 0.0

class MockTrader:
    """10K TL sanal bakiye ile R/R bazlı al-sat simülasyonu."""

    DOSYA = Path("data/signals/mock_portfolio.json")

    def __init__(self):
        self.bakiye = MOCK_BASLANGIC_BAKIYE
        self.acik_islemler: list[MockIslem] = []
        self.kapali_islemler: list[MockIslem] = []
        self._yukle()

    def _yukle(self):
        try:
            if self.DOSYA.exists():
                with open(self.DOSYA, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.bakiye = data.get("bakiye", MOCK_BASLANGIC_BAKIYE)
                for t in data.get("acik_islemler", []):
                    self.acik_islemler.append(MockIslem(**t))
                for t in data.get("kapali_islemler", []):
                    self.kapali_islemler.append(MockIslem(**t))
        except Exception as e:
            log.debug(f"Mock portfolio yuklenemedi: {e}")

    def _kaydet(self):
        self.DOSYA.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "guncelleme": datetime.now().isoformat(),
            "bakiye": round(self.bakiye, 2),
            "baslangic_bakiye": MOCK_BASLANGIC_BAKIYE,
            "toplam_deger": round(self.toplam_deger(), 2),
            "acik_pozisyon_sayisi": len(self.acik_islemler),
            "kapali_islem_sayisi": len(self.kapali_islemler),
            "acik_islemler": [
                {k: v for k, v in t.__dict__.items()} for t in self.acik_islemler
            ],
            "kapali_islemler": [
                {k: v for k, v in t.__dict__.items()} for t in self.kapali_islemler[-50:]  # Son 50
            ],
        }
        with open(self.DOSYA, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def toplam_deger(self) -> float:
        """Bakiye + açık pozisyonların maliyet değeri."""
        acik_maliyet = sum(t.maliyet for t in self.acik_islemler)
        return self.bakiye + acik_maliyet

    def _zaten_acik(self, sembol: str) -> bool:
        return any(t.sembol == sembol for t in self.acik_islemler)

    def islem_degerlendir(self, sonuclar: list['HisseAnaliz']):
        """Her turda: 1) Mevcut pozisyonları kontrol et  2) Yeni AL yap."""

        # ─── 1) Açık pozisyonları kontrol et (stop/hedef/sinyal çıkış) ───
        acik_kalan = []
        for islem in self.acik_islemler:
            # Bu sembolün güncel analizini bul
            guncel = next((s for s in sonuclar if s.sembol == islem.sembol), None)
            if guncel is None:
                acik_kalan.append(islem)
                continue

            fiyat = guncel.fiyat
            cikis = False

            if fiyat <= islem.stop_loss:
                # STOP-LOSS tetiklendi
                islem.durum = "STOP"
                islem.cikis_fiyat = islem.stop_loss
                cikis = True
            elif fiyat >= islem.hedef:
                # HEDEF fiyat ulaşıldı
                islem.durum = "HEDEF"
                islem.cikis_fiyat = islem.hedef
                cikis = True
            elif guncel.sinyal in ("GUCLU_SAT", "ZAYIF_SAT"):
                # SAT sinyali geldi
                islem.durum = "SINYAL_CIKIS"
                islem.cikis_fiyat = fiyat
                cikis = True

            if cikis:
                satis_tutari = islem.lot * islem.cikis_fiyat
                komisyon = satis_tutari * MOCK_KOMISYON_ORANI
                net_satis = satis_tutari - komisyon
                islem.kar_zarar = round(net_satis - islem.maliyet, 2)
                islem.kar_zarar_pct = round((islem.kar_zarar / islem.maliyet) * 100, 2)
                islem.cikis_zamani = datetime.now().strftime("%Y-%m-%d %H:%M")
                self.bakiye += net_satis
                self.kapali_islemler.append(islem)
                log.info(f"💰 MOCK {islem.durum}: {islem.sembol} "
                         f"giris:{islem.giris_fiyat:.2f} cikis:{islem.cikis_fiyat:.2f} "
                         f"K/Z:{islem.kar_zarar:+.2f}₺ ({islem.kar_zarar_pct:+.1f}%)")
            else:
                acik_kalan.append(islem)

        self.acik_islemler = acik_kalan

        # ─── 2) Yeni AL sinyallerini değerlendir ───
        if len(self.acik_islemler) >= MOCK_MAX_POZISYON:
            self._kaydet()
            return

        # GUCLU_AL sinyallerini skora göre sırala
        adaylar = [
            s for s in sonuclar
            if s.sinyal == "GUCLU_AL"
            and not self._zaten_acik(s.sembol)
            and s.atr > 0
            and s.stop_loss > 0
            and s.hedef > s.fiyat
        ]
        adaylar.sort(key=lambda x: x.skor, reverse=True)

        for s in adaylar:
            if len(self.acik_islemler) >= MOCK_MAX_POZISYON:
                break

            # R/R hesabı
            risk = s.fiyat - s.stop_loss
            reward = s.hedef - s.fiyat
            if risk <= 0:
                continue
            rr = reward / risk

            if rr < MOCK_MIN_RR:
                continue  # R/R yetersiz

            # Pozisyon boyutu: bakiyenin %2'si risk
            risk_tutari = self.bakiye * MOCK_RISK_ORANI
            lot = risk_tutari / risk
            maliyet = lot * s.fiyat
            komisyon = maliyet * MOCK_KOMISYON_ORANI
            toplam_maliyet = maliyet + komisyon

            # Bakiye kontrolü
            if toplam_maliyet > self.bakiye * 0.95:
                continue  # Bakiye yetersiz (%5 marj bırak)

            # AL
            self.bakiye -= toplam_maliyet
            islem = MockIslem(
                sembol=s.sembol,
                yon="AL",
                giris_fiyat=s.fiyat,
                lot=round(lot, 2),
                maliyet=round(toplam_maliyet, 2),
                stop_loss=s.stop_loss,
                hedef=s.hedef,
                rr_orani=round(rr, 2),
                giris_guven=s.guven,
                giris_skor=s.skor,
                giris_zamani=datetime.now().strftime("%Y-%m-%d %H:%M"),
            )
            self.acik_islemler.append(islem)
            log.info(f"🛒 MOCK AL: {s.sembol} @ {s.fiyat:.2f}₺ "
                     f"lot:{lot:.1f} maliyet:{toplam_maliyet:.0f}₺ "
                     f"SL:{s.stop_loss:.2f} TP:{s.hedef:.2f} R/R:{rr:.1f}")

        self._kaydet()

    def rapor(self) -> str:
        """Mock trading özet raporu."""
        toplam = self.toplam_deger()
        kz = toplam - MOCK_BASLANGIC_BAKIYE
        kz_pct = (kz / MOCK_BASLANGIC_BAKIYE) * 100

        satirlar = [
            f"\n💼 <b>MOCK PORTFOLIO</b>",
            f"  Baslangic: {MOCK_BASLANGIC_BAKIYE:,.0f}₺",
            f"  Bakiye:    {self.bakiye:,.0f}₺",
            f"  Toplam:    {toplam:,.0f}₺ ({kz:+,.0f}₺ | {kz_pct:+.1f}%)",
            f"  Acik:      {len(self.acik_islemler)} pozisyon",
        ]

        if self.acik_islemler:
            satirlar.append(f"\n  📊 <b>Acik Pozisyonlar:</b>")
            for t in self.acik_islemler:
                satirlar.append(
                    f"    • {t.sembol} @ {t.giris_fiyat:.2f}₺ "
                    f"SL:{t.stop_loss:.2f} TP:{t.hedef:.2f} R/R:{t.rr_orani}"
                )

        # Son kapanan işlemler
        son_kapanan = self.kapali_islemler[-5:]
        if son_kapanan:
            kazanc = sum(1 for t in self.kapali_islemler if t.kar_zarar > 0)
            kayip = sum(1 for t in self.kapali_islemler if t.kar_zarar <= 0)
            toplam_islem = len(self.kapali_islemler)
            win_rate = (kazanc / toplam_islem * 100) if toplam_islem > 0 else 0

            satirlar.append(f"\n  📈 <b>Islem Gecmisi:</b> {toplam_islem} islem | "
                          f"Win:{kazanc} Loss:{kayip} ({win_rate:.0f}%)")
            for t in reversed(son_kapanan):
                emoji = "✅" if t.kar_zarar > 0 else "❌"
                satirlar.append(
                    f"    {emoji} {t.sembol} {t.durum} "
                    f"{t.giris_fiyat:.2f}→{t.cikis_fiyat:.2f} "
                    f"K/Z:{t.kar_zarar:+.0f}₺ ({t.kar_zarar_pct:+.1f}%)"
                )

        return "\n".join(satirlar)


# ═══════════════════════════════════════════════════════
# POZİSYON TAKİPÇİ (Duplicate Signal Prevention)
# ═══════════════════════════════════════════════════════

@dataclass
class AcikPozisyon:
    sembol: str
    sinyal: str          # İlk sinyal türü (GUCLU_AL, ZAYIF_AL)
    giris_fiyat: float
    giris_guven: float   # İlk giriş güveni
    son_guven: float     # Son analiz güveni
    son_skor: float
    bildirim_guven: float  # Son bildirimdeki güven (tekrar AL karşılaştırması)
    giris_zamani: str
    bildirim_sayisi: int = 1  # Kaç kez AL bildirimi gönderildi

class PozisyonTakipci:
    """Açık AL sinyallerini takip eder, gereksiz tekrar bildirimleri engeller."""

    DOSYA = Path("data/signals/acik_pozisyonlar.json")

    def __init__(self):
        self.pozisyonlar: dict[str, AcikPozisyon] = {}
        self._yukle()

    def _yukle(self):
        """Disk'ten açık pozisyonları yükle."""
        try:
            if self.DOSYA.exists():
                with open(self.DOSYA, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for p in data.get("pozisyonlar", []):
                    self.pozisyonlar[p["sembol"]] = AcikPozisyon(**p)
        except Exception as e:
            log.debug(f"Pozisyon dosyasi yuklenemedi: {e}")

    def _kaydet(self):
        """Pozisyonları diske kaydet."""
        self.DOSYA.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "guncelleme": datetime.now().isoformat(),
            "pozisyonlar": [
                {
                    "sembol": p.sembol, "sinyal": p.sinyal,
                    "giris_fiyat": p.giris_fiyat, "giris_guven": p.giris_guven,
                    "son_guven": p.son_guven, "son_skor": p.son_skor,
                    "bildirim_guven": p.bildirim_guven,
                    "giris_zamani": p.giris_zamani, "bildirim_sayisi": p.bildirim_sayisi,
                }
                for p in self.pozisyonlar.values()
            ]
        }
        with open(self.DOSYA, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def filtrele(self, sonuclar: list['HisseAnaliz']) -> tuple[list['HisseAnaliz'], list['HisseAnaliz'], list['HisseAnaliz']]:
        """
        Sonuçları 3 gruba ayır:
          yeni_al   : İlk kez AL sinyali veren (bildirilecek)
          tekrar_al : Zaten açık pozisyonu olan VE güven yükselmiş (bildirilecek)
          filtreli  : Zaten açık, güven artmamış (sessiz geçilecek)

        Ayrıca SAT sinyali gelen açık pozisyonları kapatır.
        """
        yeni_al = []
        tekrar_al = []
        filtreli = []

        for s in sonuclar:
            sembol = s.sembol
            mevcut = self.pozisyonlar.get(sembol)

            if s.sinyal in ("GUCLU_AL", "ZAYIF_AL"):
                if mevcut is None:
                    # ─ YENİ AL: İlk kez sinyal ─
                    yeni_al.append(s)
                    self.pozisyonlar[sembol] = AcikPozisyon(
                        sembol=sembol, sinyal=s.sinyal,
                        giris_fiyat=s.fiyat, giris_guven=s.guven,
                        son_guven=s.guven, son_skor=s.skor,
                        bildirim_guven=s.guven,
                        giris_zamani=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    )
                else:
                    # ─ MEVCUT POZİSYON: Tekrar AL kontrolü ─
                    # Güven artışını son BİLDİRİM'e göre hesapla
                    guven_artisi = s.guven - mevcut.bildirim_guven
                    mevcut.son_guven = s.guven
                    mevcut.son_skor = s.skor

                    # Tekrar AL koşulları:
                    # 1) Güven son bildirimden beri ≥15 puan arttıysa
                    # 2) Güven ≥70 VE son bildirimden beri arttıysa
                    if (guven_artisi >= TEKRAR_AL_MIN_GUVEN_ARTISI or
                            (s.guven >= TEKRAR_AL_MIN_GUVEN and guven_artisi > 0)):
                        mevcut.bildirim_sayisi += 1
                        mevcut.bildirim_guven = s.guven  # Bildirim güvenini güncelle
                        tekrar_al.append(s)
                    else:
                        filtreli.append(s)

            elif s.sinyal in ("ZAYIF_SAT", "GUCLU_SAT"):
                if mevcut is not None:
                    # ─ SAT sinyali: Pozisyonu kapat ─
                    del self.pozisyonlar[sembol]

            else:
                # NOTR: Pozisyon varsa güncelle ama bildirim yok
                if mevcut is not None:
                    mevcut.son_guven = s.guven
                    mevcut.son_skor = s.skor

        self._kaydet()
        return yeni_al, tekrar_al, filtreli

    def ozet(self) -> str:
        """Açık pozisyon özeti."""
        if not self.pozisyonlar:
            return ""
        satırlar = [f"\n📂 <b>Acik Pozisyonlar ({len(self.pozisyonlar)}):</b>"]
        for p in sorted(self.pozisyonlar.values(), key=lambda x: x.son_skor, reverse=True):
            satırlar.append(
                f"  • {p.sembol} giris:{p.giris_fiyat:.2f}₺ "
                f"guven:%{p.son_guven:.0f} (x{p.bildirim_sayisi})"
            )
        return "\n".join(satırlar)


# ═══════════════════════════════════════════════════════
# ANA BOT
# ═══════════════════════════════════════════════════════

class Bist100SignalBot:
    """BIST Full otomatik sinyal botu — sürekli çalışma + pozisyon takibi."""

    def __init__(self):
        # Telegram config: önce env var, sonra settings.json
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        # Env boşsa settings.json'dan dene
        if not self.telegram_token or not self.telegram_chat_id:
            self._load_from_settings()

        self.telegram = None
        if self.telegram_token and self.telegram_chat_id:
            self.telegram = TelegramGonderici(self.telegram_token, self.telegram_chat_id)
            log.info("Telegram aktif ✓")
        else:
            log.warning("Telegram devre disi (token/chat_id eksik)")

        self.sonuclar: list[HisseAnaliz] = []
        self.basarisiz: list[str] = []
        self.pozisyon_takip = PozisyonTakipci()
        self.mock_trader: Optional[MockTrader] = None

    def mock_aktif_et(self):
        """Mock trading modunu aktif et."""
        self.mock_trader = MockTrader()
        log.info(f"💼 Mock trading aktif | Bakiye: {self.mock_trader.bakiye:,.0f}₺ | "
                 f"Acik: {len(self.mock_trader.acik_islemler)} pozisyon")

    def _load_from_settings(self):
        """settings.json'dan Telegram bilgilerini yükle."""
        try:
            settings_path = Path(__file__).parent / "config" / "settings.json"
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                tg = settings.get("telegram", {})
                if not self.telegram_token:
                    self.telegram_token = tg.get("bot_token", "")
                if not self.telegram_chat_id:
                    self.telegram_chat_id = tg.get("chat_id", "")
        except Exception:
            pass

    def analiz_hepsini(self, hisseler: list[str] = None, period: str = "6mo"):
        """Tüm hisseleri analiz et."""
        if hisseler is None:
            hisseler = BIST_TUMU

        self.sonuclar = []
        self.basarisiz = []
        toplam = len(hisseler)

        log.info(f"\n{'='*60}")
        log.info(f"🔍 {toplam} BIST hissesi analiz ediliyor...")
        log.info(f"{'='*60}")

        for idx, sembol in enumerate(hisseler, 1):
            pct = idx / toplam * 100
            bar_len = 30
            filled = int(bar_len * idx / toplam)
            bar = '█' * filled + '░' * (bar_len - filled)
            print(f"\r  [{bar}] {idx}/{toplam} ({pct:.0f}%) {sembol:8s}", end='', flush=True)

            try:
                df, kaynak = VeriCekici.veri_getir(sembol, period=period)
                if df is None:
                    self.basarisiz.append(sembol)
                    continue

                motor = TeknikAnalizMotoru(df, sembol)
                analiz = motor.analiz_et()
                analiz.veri_kaynagi = kaynak
                self.sonuclar.append(analiz)

            except Exception as e:
                log.debug(f"{sembol} analiz hatasi: {e}")
                self.basarisiz.append(sembol)

            time.sleep(0.2)  # Yahoo rate limit

        print()  # Yeni satır
        log.info(f"\n✅ Analiz tamamlandi: {len(self.sonuclar)} basarili, {len(self.basarisiz)} basarisiz")

    def rapor_olustur_ve_gonder(self, min_guven: float = 50.0, saat_basi_rapor: bool = True):
        """Rapor oluştur ve Telegram'a gönder.
        
        saat_basi_rapor=True  → Tam özet rapor + detaylar (saat başı)
        saat_basi_rapor=False → Sadece yeni/güçlenen AL sinyalleri (ara tarama)
        """
        if not self.sonuclar:
            log.warning("Analiz sonucu yok, once analiz_hepsini() calistirin.")
            return

        # ─── Pozisyon filtresi uygula ───
        yeni_al, tekrar_al, filtreli = self.pozisyon_takip.filtrele(self.sonuclar)

        if saat_basi_rapor:
            # ═══ SAAT BAŞI: Tam rapor ═══
            ozet = RaporOlusturucu.ozet_rapor(self.sonuclar, self.basarisiz)

            # Açık pozisyon bilgisi ekle
            poz_ozet = self.pozisyon_takip.ozet()
            if poz_ozet:
                ozet += "\n" + poz_ozet

            # Filtreli bilgi
            if filtreli:
                ozet += f"\n\n🔇 <i>{len(filtreli)} hisse zaten takipte (tekrar bildirilmedi)</i>"

            print(f"\n{ozet}\n")
            if self.telegram:
                log.info("📤 Saat basi rapor Telegram'a gonderiliyor...")
                self.telegram.gonder(ozet)

            # Detaylı rapor: yeni + tekrar AL sinyalleri (güven >= min_guven)
            detay_hisseler = [
                s for s in (yeni_al + tekrar_al)
                if s.guven >= min_guven
            ]
            detay_hisseler.sort(key=lambda x: x.skor, reverse=True)

            for s in detay_hisseler:
                is_tekrar = s in tekrar_al
                detay = RaporOlusturucu.hisse_detay_rapor(s)
                if is_tekrar:
                    poz = self.pozisyon_takip.pozisyonlar.get(s.sembol)
                    detay = f"🔄 <b>GUCLENEN SINYAL (x{poz.bildirim_sayisi})</b>\n" + detay
                print(f"\n{detay}")
                if self.telegram:
                    self.telegram.gonder(detay)
                    time.sleep(1)

            if detay_hisseler:
                log.info(f"📱 {len(detay_hisseler)} hisse detayli rapor gonderildi "
                         f"({len(yeni_al)} yeni, {len(tekrar_al)} guclenen)")
            else:
                log.info("ℹ️ Detayli rapor gonderilecek yeni sinyal yok.")

        else:
            # ═══ ARA TARAMA: Sadece yeni keşifler bildirilir ═══
            bildirilecek = [s for s in yeni_al if s.guven >= min_guven]
            bildirilecek += [s for s in tekrar_al if s.guven >= min_guven]

            if not bildirilecek:
                log.info(f"🔍 Ara tarama: {len(self.sonuclar)} hisse | "
                         f"yeni AL: {len(yeni_al)} | guclenen: {len(tekrar_al)} | "
                         f"filtreli: {len(filtreli)} — bildirim yok")
                return

            log.info(f"🆕 Ara tarama: {len(bildirilecek)} yeni/guclenen sinyal bulundu!")

            for s in sorted(bildirilecek, key=lambda x: x.skor, reverse=True):
                is_tekrar = s in tekrar_al
                detay = RaporOlusturucu.hisse_detay_rapor(s)
                if is_tekrar:
                    poz = self.pozisyon_takip.pozisyonlar.get(s.sembol)
                    detay = f"🔄 <b>GUCLENEN SINYAL (x{poz.bildirim_sayisi})</b>\n" + detay
                else:
                    detay = f"🆕 <b>YENI AL SINYALI</b>\n" + detay
                print(f"\n{detay}")
                if self.telegram:
                    self.telegram.gonder(detay)
                    time.sleep(1)

    def konsol_ozet(self):
        """Konsol'da kısa özet."""
        if not self.sonuclar:
            return

        guclu_al  = [s for s in self.sonuclar if s.sinyal == "GUCLU_AL"]
        zayif_al  = [s for s in self.sonuclar if s.sinyal == "ZAYIF_AL"]
        notr      = [s for s in self.sonuclar if s.sinyal == "NOTR"]
        zayif_sat = [s for s in self.sonuclar if s.sinyal == "ZAYIF_SAT"]
        guclu_sat = [s for s in self.sonuclar if s.sinyal == "GUCLU_SAT"]

        print(f"\n{'═'*60}")
        print(f"  BIST FULL SİNYAL ÖZETİ - {datetime.now():%d.%m.%Y %H:%M}")
        print(f"{'═'*60}")
        print(f"  🟢 GUCLU AL:  {len(guclu_al):3d} hisse")
        print(f"  📗 ZAYIF AL:  {len(zayif_al):3d} hisse")
        print(f"  ⏸️  NOTR:      {len(notr):3d} hisse")
        print(f"  📕 ZAYIF SAT: {len(zayif_sat):3d} hisse")
        print(f"  🔴 GUCLU SAT: {len(guclu_sat):3d} hisse")
        print(f"  ⚠️  Basarisiz: {len(self.basarisiz):3d} hisse")
        print(f"{'═'*60}")

        if guclu_al:
            print(f"\n  🟢 EN İYİ AL FIRSATLARI:")
            for s in sorted(guclu_al, key=lambda x: x.skor, reverse=True)[:10]:
                print(f"     {s.sembol:8s} {s.fiyat:>8.2f}₺  Skor:{s.skor:+.3f}  Hedef:{s.hedef:.2f}₺  SL:{s.stop_loss:.2f}₺")

        if guclu_sat:
            print(f"\n  🔴 EN GUCLU SAT SİNYALLERİ:")
            for s in sorted(guclu_sat, key=lambda x: x.skor)[:10]:
                print(f"     {s.sembol:8s} {s.fiyat:>8.2f}₺  Skor:{s.skor:+.3f}")

        print()

    def sonuclari_kaydet(self, dosya: str = "data/signals/son_analiz.json"):
        """Analiz sonuçlarını JSON olarak kaydet."""
        Path(dosya).parent.mkdir(parents=True, exist_ok=True)

        data = {
            "tarih": datetime.now().isoformat(),
            "toplam_analiz": len(self.sonuclar),
            "basarisiz": self.basarisiz,
            "sonuclar": [
                {
                    "sembol": s.sembol,
                    "fiyat": s.fiyat,
                    "tarih": s.tarih,
                    "skor": s.skor,
                    "sinyal": s.sinyal,
                    "guven": s.guven,
                    "stop_loss": s.stop_loss,
                    "hedef": s.hedef,
                    "atr": s.atr,
                    "kaynak": s.veri_kaynagi,
                    "indikatorler": [
                        {"ad": i.ad, "deger": i.deger, "sinyal": i.sinyal, "aciklama": i.aciklama}
                        for i in s.indikatörler
                    ],
                }
                for s in self.sonuclar
            ]
        }

        with open(dosya, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        log.info(f"💾 Sonuclar kaydedildi: {dosya}")


# ═══════════════════════════════════════════════════════
# ÇALIŞTIR
# ═══════════════════════════════════════════════════════

def borsa_acik_mi() -> bool:
    """Borsa saatleri içinde mi? (Hafta içi 10:00-18:10)"""
    now = datetime.now()
    if now.weekday() >= 5:  # Cumartesi / Pazar
        return False
    saat = (now.hour, now.minute)
    return BORSA_ACILIS <= saat <= BORSA_KAPANIS


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║   🤖 BIST FULL SİNYAL BOTU v2                          ║
║   12 İndikatör + Trend Kontekst | Telegram Rapor        ║
║   Sürekli Çalışma: ~10dk analiz | ~60dk rapor           ║
╚══════════════════════════════════════════════════════════╝
""")

    import argparse
    parser = argparse.ArgumentParser(description="BIST Sinyal Botu")
    parser.add_argument("--tek", action="store_true", help="Tek seferlik çalıştır (eski mod)")
    parser.add_argument("--aralik", type=int, default=ANALIZ_ARALIK_DK, help=f"Analiz aralığı dakika (varsayılan: {ANALIZ_ARALIK_DK})")
    parser.add_argument("--rapor-aralik", type=int, default=RAPOR_ARALIK_DK, help=f"Rapor aralığı dakika (varsayılan: {RAPOR_ARALIK_DK})")
    parser.add_argument("--7-24", dest="yedi_yirmi_dort", action="store_true", help="Borsa saatleri dışında da çalış")
    parser.add_argument("--mock", action="store_true", help="Mock trading aktif (10K TL sanal bakiye)")
    args = parser.parse_args()

    bot = Bist100SignalBot()

    if args.mock:
        bot.mock_aktif_et()

    if args.tek:
        # ─── TEK SEFERLİK MOD (eski davranış) ───
        log.info("📌 Tek seferlik mod")
        bot.analiz_hepsini(period="6mo")
        if bot.mock_trader:
            bot.mock_trader.islem_degerlendir(bot.sonuclar)
        bot.konsol_ozet()
        bot.sonuclari_kaydet()
        bot.rapor_olustur_ve_gonder(min_guven=50.0, saat_basi_rapor=True)
        if bot.mock_trader:
            mock_rapor = bot.mock_trader.rapor()
            print(mock_rapor)
            if bot.telegram:
                bot.telegram.gonder(mock_rapor)
        print("\n✅ Tamamlandi!")
        return

    # ─── SÜREKLİ ÇALIŞMA MODU ───
    analiz_aralik = args.aralik
    rapor_aralik = args.rapor_aralik
    log.info(f"🔄 Surekli mod: her {analiz_aralik}dk analiz | her {rapor_aralik}dk rapor")
    log.info(f"📂 Acik pozisyon takibi: {len(bot.pozisyon_takip.pozisyonlar)} mevcut pozisyon")
    if bot.mock_trader:
        log.info(f"💼 Mock trading aktif | Bakiye: {bot.mock_trader.bakiye:,.0f}₺")

    if bot.telegram:
        baslangic_msg = (
            f"🤖 <b>BistBot v2 Basladi</b>\n"
            f"🔄 Analiz: her {analiz_aralik}dk\n"
            f"📊 Rapor: her {rapor_aralik}dk\n"
            f"📂 Acik pozisyon: {len(bot.pozisyon_takip.pozisyonlar)}\n"
        )
        if bot.mock_trader:
            baslangic_msg += f"💼 Mock trading: {bot.mock_trader.bakiye:,.0f}₺\n"
        baslangic_msg += f"⏰ {datetime.now():%H:%M:%S}"
        bot.telegram.gonder(baslangic_msg)

    son_rapor_zamani = None
    tur_sayisi = 0

    try:
        while True:
            now = datetime.now()

            # Borsa kapalıysa bekle
            if not args.yedi_yirmi_dort and not borsa_acik_mi():
                # Gece / hafta sonu
                if now.hour == 9 and now.minute == 55:
                    log.info("⏰ Borsa 5dk icinde aciliyor, hazirlaniliyor...")
                else:
                    next_check = 60  # Her dakika kontrol et
                    if now.weekday() >= 5:
                        log.info(f"📅 Hafta sonu — bir sonraki kontrol {next_check}sn sonra")
                    else:
                        log.info(f"🕐 Borsa kapali ({now:%H:%M}) — bekleniyor...")
                    time.sleep(next_check)
                    continue

            tur_sayisi += 1
            log.info(f"\n{'─'*50}")
            log.info(f"🔄 Tur #{tur_sayisi} | {now:%H:%M:%S}")
            log.info(f"{'─'*50}")

            # Analiz
            bot.analiz_hepsini(period="6mo")
            bot.sonuclari_kaydet()

            # Saat başı rapor mu, ara tarama mı?
            saat_basi = False
            if son_rapor_zamani is None:
                saat_basi = True  # İlk çalıştırma
            elif (now - son_rapor_zamani).total_seconds() >= rapor_aralik * 60:
                saat_basi = True

            # Mock trading
            if bot.mock_trader and bot.sonuclar:
                bot.mock_trader.islem_degerlendir(bot.sonuclar)

            bot.rapor_olustur_ve_gonder(min_guven=50.0, saat_basi_rapor=saat_basi)

            # Mock rapor (saat başı)
            if saat_basi and bot.mock_trader:
                mock_rapor = bot.mock_trader.rapor()
                print(mock_rapor)
                if bot.telegram:
                    bot.telegram.gonder(mock_rapor)

            if saat_basi:
                son_rapor_zamani = now
                bot.konsol_ozet()

            # Sonraki tura kadar bekle
            bekleme = analiz_aralik * 60
            log.info(f"⏳ Sonraki analiz {analiz_aralik}dk sonra ({(now + timedelta(minutes=analiz_aralik)):%H:%M:%S})")
            time.sleep(bekleme)

    except KeyboardInterrupt:
        log.info("\n🛑 Bot durduruldu (Ctrl+C)")
        if bot.telegram:
            bot.telegram.gonder(f"🛑 BistBot durduruldu | {datetime.now():%H:%M:%S}")
        print("\n✅ Bot kapatildi.")


if __name__ == "__main__":
    main()
