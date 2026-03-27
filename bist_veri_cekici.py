"""
BIST Veri Çekici — yfinance
============================
Kullanım:
    pip install yfinance pandas
 
    python bist_veri_cekici.py
"""
 
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
 
# ─────────────────────────────────────────
# 1. TAKİP EDİLECEK HİSSELER
# ─────────────────────────────────────────
# BIST formatı: <KOD>.IS
HISSELER = [
    "THYAO.IS",   # Türk Hava Yolları
    "EREGL.IS",   # Ereğli Demir Çelik
    "ASELS.IS",   # Aselsan
    "GARAN.IS",   # Garanti Bankası
    "KCHOL.IS",   # Koç Holding
    "SISE.IS",    # Şişecam
    "BIMAS.IS",   # BİM Mağazaları
    "AKBNK.IS",   # Akbank
    "YKBNK.IS",   # Yapı ve Kredi Bankası
    "TOASO.IS",   # Tofaş Otomobil
]
 
# Global / Makro
GLOBAL = [
    "^BIST100",   # BIST 100 Endeksi
    "^GSPC",      # S&P 500
    "^VIX",       # Korku Endeksi
    "GC=F",       # Altın Vadeli
    "CL=F",       # Ham Petrol (WTI)
    "USDTRY=X",   # USD/TRY
    "EURTRY=X",   # EUR/TRY
]
 
# ─────────────────────────────────────────
# 2. VERİ ÇEKME FONKSİYONLARI
# ─────────────────────────────────────────
 
def hisse_verisi_cek(sembol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Tek hisse için OHLCV verisi çeker.
 
    period  : 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    Not: 1m–90m intervallar yalnızca son 60 gün için çalışır.
    """
    try:
        ticker = yf.Ticker(sembol)
        df = ticker.history(period=period, interval=interval)
 
        if df.empty:
            print(f"  [UYARI] {sembol} için veri bulunamadı.")
            return pd.DataFrame()
 
        # Gereksiz sütunları düşür
        df = df[["Open", "High", "Low", "Close", "Volume"]]
        df.index = df.index.tz_localize(None)  # timezone kaldır
        df.index.name = "Tarih"
        df.columns = ["Açılış", "Yüksek", "Düşük", "Kapanış", "Hacim"]
        df["Sembol"] = sembol
 
        print(f"  [OK] {sembol:15s} — {len(df)} satır | "
              f"{df.index[0].date()} → {df.index[-1].date()}")
        return df
 
    except Exception as e:
        print(f"  [HATA] {sembol}: {e}")
        return pd.DataFrame()
 
 
def coklu_hisse_cek(semboller: list, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Birden fazla hisseyi tek seferde çeker ve birleştirir."""
    print(f"\n{'─'*50}")
    print(f"  {len(semboller)} sembol çekiliyor... (period={period}, interval={interval})")
    print(f"{'─'*50}")
 
    tumdf = []
    for s in semboller:
        df = hisse_verisi_cek(s, period, interval)
        if not df.empty:
            tumdf.append(df)
 
    if not tumdf:
        return pd.DataFrame()
 
    return pd.concat(tumdf)
 
 
def ozet_istatistik(df: pd.DataFrame) -> pd.DataFrame:
    """
    Her hisse için temel özet istatistik üretir:
    son fiyat, değişim %, 52h yüksek/düşük, ort. hacim
    """
    sonuclar = []
 
    for sembol, grp in df.groupby("Sembol"):
        grp = grp.sort_index()
        son_fiyat   = grp["Kapanış"].iloc[-1]
        onceki_gun  = grp["Kapanış"].iloc[-2] if len(grp) > 1 else son_fiyat
        degisim_pct = (son_fiyat - onceki_gun) / onceki_gun * 100
 
        haftalik_df = grp.tail(5)
        aylik_df    = grp.tail(21)
        yillik_df   = grp.tail(252)
 
        sonuclar.append({
            "Sembol":         sembol,
            "Son Fiyat":      round(son_fiyat, 2),
            "Günlük %":       round(degisim_pct, 2),
            "5g Değişim %":   round((grp["Kapanış"].iloc[-1] / haftalik_df["Kapanış"].iloc[0] - 1) * 100, 2),
            "21g Değişim %":  round((grp["Kapanış"].iloc[-1] / aylik_df["Kapanış"].iloc[0] - 1) * 100, 2),
            "252g High":      round(yillik_df["Yüksek"].max(), 2),
            "252g Low":       round(yillik_df["Düşük"].min(), 2),
            "Ort. Hacim (M)": round(grp["Hacim"].mean() / 1_000_000, 1),
        })
 
    return pd.DataFrame(sonuclar).set_index("Sembol")
 
 
def hareketli_ortalama_ekle(df: pd.DataFrame) -> pd.DataFrame:
    """
    Her hisseye MA7, MA21, MA50, MA200 sütunları ekler.
    Teknik analiz motorunun temel girdisi.
    """
    sonuc = []
    for sembol, grp in df.groupby("Sembol"):
        grp = grp.copy().sort_index()
        grp["MA7"]   = grp["Kapanış"].rolling(7).mean().round(2)
        grp["MA21"]  = grp["Kapanış"].rolling(21).mean().round(2)
        grp["MA50"]  = grp["Kapanış"].rolling(50).mean().round(2)
        grp["MA200"] = grp["Kapanış"].rolling(200).mean().round(2)
        # Golden Cross / Death Cross sinyali
        grp["GC_Signal"] = (grp["MA50"] > grp["MA200"]).astype(int)
        sonuc.append(grp)
    return pd.concat(sonuc)
 
 
def csv_kaydet(df: pd.DataFrame, dosya_adi: str):
    """Veriyi CSV olarak kaydeder."""
    klasor = "bist_data"
    os.makedirs(klasor, exist_ok=True)
    yol = os.path.join(klasor, dosya_adi)
    df.to_csv(yol, encoding="utf-8-sig")
    print(f"  [KAYIT] {yol} ({len(df)} satır)")
    return yol
 
 
# ─────────────────────────────────────────
# 3. ANA AKIŞ
# ─────────────────────────────────────────
 
def main():
    print("\n" + "="*50)
    print("  BIST VERİ ÇEKİCİ — yfinance")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
 
    # 3a. Hisse verileri (1 yıllık günlük)
    print("\n[1/4] BIST hisseleri çekiliyor...")
    hisse_df = coklu_hisse_cek(HISSELER, period="1y", interval="1d")
 
    # 3b. Global / Makro veriler
    print("\n[2/4] Global & makro veriler çekiliyor...")
    global_df = coklu_hisse_cek(GLOBAL, period="1y", interval="1d")
 
    # 3c. Hareketli ortalama ekle
    print("\n[3/4] Hareketli ortalamalar hesaplanıyor...")
    hisse_df = hareketli_ortalama_ekle(hisse_df)
 
    # 3d. Özet istatistik
    print("\n[4/4] Özet istatistik üretiliyor...")
    ozet_df = ozet_istatistik(hisse_df)
 
    # Ekrana bas
    print("\n" + "="*50)
    print("  ÖZET İSTATİSTİK")
    print("="*50)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 120)
    print(ozet_df.to_string())
 
    # 3e. CSV kaydet
    print("\n[KAYIT] CSV dosyaları yazılıyor...")
    csv_kaydet(hisse_df, "hisseler_gunluk.csv")
    csv_kaydet(global_df, "global_gunluk.csv")
    csv_kaydet(ozet_df, "ozet_istatistik.csv")
 
    print("\n[TAMAMLANDI]")
    print("  Bir sonraki adım: bu verilere RSI ve MACD ekleyelim.")
    return hisse_df, global_df, ozet_df
 
 
# ─────────────────────────────────────────
# 4. HAFTALIK / AYLIK / YILLIK VERİ
# ─────────────────────────────────────────
 
def coklu_timeframe_cek(sembol: str) -> dict:
    """
    Tek hisse için çoklu zaman dilimi verisi döndürür.
    Trade asistanında farklı MA'ları karşılaştırmak için kullanılır.
    """
    print(f"\n  {sembol} için çoklu timeframe çekiliyor...")
    return {
        "gunluk":  hisse_verisi_cek(sembol, period="1y",  interval="1d"),
        "haftalik": hisse_verisi_cek(sembol, period="5y", interval="1wk"),
        "aylik":   hisse_verisi_cek(sembol, period="10y", interval="1mo"),
    }
 
 
# ─────────────────────────────────────────
# 5. GERÇEKLEŞTİRME
# ─────────────────────────────────────────
 
if __name__ == "__main__":
    hisse_df, global_df, ozet_df = main()
 
    # İsteğe bağlı: tek hisse çoklu timeframe
    # tf = coklu_timeframe_cek("THYAO.IS")
    # print(tf["haftalik"].tail())
 