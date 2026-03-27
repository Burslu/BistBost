"""
Teknik Analiz Modülü
=====================
RSI · MACD · Bollinger Bantları · Stochastic · ATR · Hacim Analizi
→ Her indikatör için AL / SAT / NÖTR sinyal üretir
→ Tüm sinyalleri birleştiren toplam skor verir
 
Kullanım:
    pip install pandas numpy
 
    from bist_veri_cekici import hisse_verisi_cek
    from teknik_analiz import TeknikAnaliz
 
    df = hisse_verisi_cek("THYAO.IS", period="1y")
    ta = TeknikAnaliz(df)
    sonuc = ta.tam_analiz()
    print(sonuc)
"""
 
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Literal
 
Sinyal = Literal["AL", "SAT", "NÖTR"]
 
# ─────────────────────────────────────────────────────────────────
# YARDIMCI: Sinyal → sayısal ağırlık
# ─────────────────────────────────────────────────────────────────
SINYAL_AGIRLIK = {"AL": 1, "NÖTR": 0, "SAT": -1}
 
 
@dataclass
class IndikatorSonuc:
    ad: str
    deger: float
    sinyal: Sinyal
    aciklama: str
    agirlik: float = 1.0          # sinyalin skordaki ağırlığı
 
    @property
    def skor(self) -> float:
        return SINYAL_AGIRLIK[self.sinyal] * self.agirlik
 
 
# ─────────────────────────────────────────────────────────────────
# ANA SINIF
# ─────────────────────────────────────────────────────────────────
 
class TeknikAnaliz:
    """
    Bir hissenin OHLCV DataFrame'ini alır,
    tüm teknik indikatörleri hesaplar ve sinyal üretir.
 
    df sütun adları: Açılış, Yüksek, Düşük, Kapanış, Hacim
    (bist_veri_cekici.py çıktısıyla birebir uyumlu)
    """
 
    def __init__(self, df: pd.DataFrame):
        if df.empty:
            raise ValueError("Boş DataFrame geldi.")
        self.df = df.copy().sort_index()
        self.kapanis = self.df["Kapanış"]
        self.yuksek  = self.df["Yüksek"]
        self.dusuk   = self.df["Düşük"]
        self.hacim   = self.df["Hacim"]
        self.sembol  = df["Sembol"].iloc[0] if "Sembol" in df.columns else "?"
        self._hesapla()
 
    # ──────────────────────────────────────────
    # 1. RSI  (Relative Strength Index)
    # ──────────────────────────────────────────
 
    def _rsi(self, period: int = 14) -> pd.Series:
        delta = self.kapanis.diff()
        kazan = delta.clip(lower=0)
        kayip = -delta.clip(upper=0)
        avg_k = kazan.ewm(com=period - 1, min_periods=period).mean()
        avg_y = kayip.ewm(com=period - 1, min_periods=period).mean()
        rs    = avg_k / avg_y.replace(0, np.nan)
        return 100 - (100 / (1 + rs))
 
    def rsi_sinyal(self, period: int = 14,
                   asiri_satim: float = 30,
                   asiri_alim: float = 70) -> IndikatorSonuc:
        rsi_ser = self._rsi(period)
        rsi_val = round(float(rsi_ser.iloc[-1]), 2)
 
        if rsi_val < asiri_satim:
            sinyal = "AL"
            acik   = f"RSI {rsi_val} → aşırı satım bölgesi (< {asiri_satim})"
        elif rsi_val > asiri_alim:
            sinyal = "SAT"
            acik   = f"RSI {rsi_val} → aşırı alım bölgesi (> {asiri_alim})"
        else:
            sinyal = "NÖTR"
            acik   = f"RSI {rsi_val} → nötr bölge ({asiri_satim}–{asiri_alim})"
 
        return IndikatorSonuc("RSI", rsi_val, sinyal, acik, agirlik=1.5)
 
    # ──────────────────────────────────────────
    # 2. MACD
    # ──────────────────────────────────────────
 
    def _macd(self, hizli: int = 12, yavas: int = 26, sinyal_p: int = 9):
        ema_h  = self.kapanis.ewm(span=hizli, adjust=False).mean()
        ema_y  = self.kapanis.ewm(span=yavas, adjust=False).mean()
        macd   = ema_h - ema_y
        signal = macd.ewm(span=sinyal_p, adjust=False).mean()
        hist   = macd - signal
        return macd, signal, hist
 
    def macd_sinyal(self) -> IndikatorSonuc:
        macd, signal, hist = self._macd()
        m_val  = round(float(macd.iloc[-1]), 4)
        h_val  = round(float(hist.iloc[-1]), 4)
        h_prev = round(float(hist.iloc[-2]), 4)
 
        # Histogram yönü değişiyor mu? (crossover)
        if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
            sinyal = "AL"
            acik   = f"MACD sinyal çizgisini yukarı kesti (histogram: {h_val:+.4f})"
        elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
            sinyal = "SAT"
            acik   = f"MACD sinyal çizgisini aşağı kesti (histogram: {h_val:+.4f})"
        elif h_val > 0 and h_val > h_prev:
            sinyal = "AL"
            acik   = f"MACD histogramı pozitif ve artıyor ({h_val:+.4f})"
        elif h_val < 0 and h_val < h_prev:
            sinyal = "SAT"
            acik   = f"MACD histogramı negatif ve azalıyor ({h_val:+.4f})"
        else:
            sinyal = "NÖTR"
            acik   = f"MACD belirsiz (histogram: {h_val:+.4f})"
 
        return IndikatorSonuc("MACD", m_val, sinyal, acik, agirlik=1.5)
 
    # ──────────────────────────────────────────
    # 3. Bollinger Bantları
    # ──────────────────────────────────────────
 
    def _bollinger(self, period: int = 20, std_katsayi: float = 2.0):
        orta  = self.kapanis.rolling(period).mean()
        std   = self.kapanis.rolling(period).std()
        ust   = orta + std_katsayi * std
        alt   = orta - std_katsayi * std
        bw    = (ust - alt) / orta   # Bandwidth
        return orta, ust, alt, bw
 
    def bollinger_sinyal(self) -> IndikatorSonuc:
        orta, ust, alt, bw = self._bollinger()
        son_fiyat = float(self.kapanis.iloc[-1])
        u_val     = round(float(ust.iloc[-1]), 2)
        a_val     = round(float(alt.iloc[-1]), 2)
        o_val     = round(float(orta.iloc[-1]), 2)
        bw_val    = round(float(bw.iloc[-1]) * 100, 2)
 
        # %B göstergesi: fiyatın bantlar içindeki konumu (0–1)
        pct_b = (son_fiyat - a_val) / (u_val - a_val) if (u_val - a_val) > 0 else 0.5
 
        if son_fiyat < a_val:
            sinyal = "AL"
            acik   = f"Fiyat ({son_fiyat:.2f}) alt banda ({a_val:.2f}) dokundu — geri tepme beklentisi"
        elif son_fiyat > u_val:
            sinyal = "SAT"
            acik   = f"Fiyat ({son_fiyat:.2f}) üst banda ({u_val:.2f}) değdi — aşırı uzama"
        elif pct_b < 0.2:
            sinyal = "AL"
            acik   = f"Fiyat alt banda yakın (%B={pct_b:.2f}), bant genişliği={bw_val:.1f}%"
        elif pct_b > 0.8:
            sinyal = "SAT"
            acik   = f"Fiyat üst banda yakın (%B={pct_b:.2f}), bant genişliği={bw_val:.1f}%"
        else:
            sinyal = "NÖTR"
            acik   = f"Fiyat orta bölgede (%B={pct_b:.2f}), orta bant={o_val:.2f}"
 
        return IndikatorSonuc("Bollinger", round(pct_b, 3), sinyal, acik, agirlik=1.0)
 
    # ──────────────────────────────────────────
    # 4. Hareketli Ortalama Sistemi
    # ──────────────────────────────────────────
 
    def ma_sinyal(self) -> IndikatorSonuc:
        """
        MA7 > MA21 > MA50 > MA200 → güçlü AL
        Aksi sıralama → SAT
        Crossover'lar en güçlü sinyal
        """
        k = self.kapanis
        ma7   = k.rolling(7).mean()
        ma21  = k.rolling(21).mean()
        ma50  = k.rolling(50).mean()
        ma200 = k.rolling(200).mean()
 
        son_fiyat = float(k.iloc[-1])
        v7   = round(float(ma7.iloc[-1]),   2)
        v21  = round(float(ma21.iloc[-1]),  2)
        v50  = round(float(ma50.iloc[-1]),  2)
        v200 = round(float(ma200.iloc[-1]), 2)
 
        # Golden / Death Cross (MA50 ↔ MA200)
        gc_simdi  = ma50.iloc[-1] > ma200.iloc[-1]
        gc_once   = ma50.iloc[-2] > ma200.iloc[-2]
 
        if gc_simdi and not gc_once:
            sinyal = "AL"
            acik   = f"GOLDEN CROSS! MA50({v50}) MA200({v200})'ü yukarı kesti"
        elif not gc_simdi and gc_once:
            sinyal = "SAT"
            acik   = f"DEATH CROSS! MA50({v50}) MA200({v200})'ü aşağı kesti"
        elif son_fiyat > v7 > v21 > v50:
            sinyal = "AL"
            acik   = f"Fiyat tüm MA'ların üstünde — güçlü yükseliş trendi"
        elif son_fiyat < v7 < v21 < v50:
            sinyal = "SAT"
            acik   = f"Fiyat tüm MA'ların altında — güçlü düşüş trendi"
        elif son_fiyat > v50:
            sinyal = "AL"
            acik   = f"Fiyat MA50({v50}) üstünde, orta vadeli trend yukarı"
        elif son_fiyat < v50:
            sinyal = "SAT"
            acik   = f"Fiyat MA50({v50}) altında, orta vadeli trend aşağı"
        else:
            sinyal = "NÖTR"
            acik   = f"MA sistemi karışık sinyal veriyor"
 
        return IndikatorSonuc("MA Sistemi", son_fiyat, sinyal, acik, agirlik=2.0)
 
    # ──────────────────────────────────────────
    # 5. Stochastic Oscillator
    # ──────────────────────────────────────────
 
    def stochastic_sinyal(self, k_period: int = 14, d_period: int = 3) -> IndikatorSonuc:
        low_min  = self.dusuk.rolling(k_period).min()
        high_max = self.yuksek.rolling(k_period).max()
        k_line   = 100 * (self.kapanis - low_min) / (high_max - low_min).replace(0, np.nan)
        d_line   = k_line.rolling(d_period).mean()
 
        k_val = round(float(k_line.iloc[-1]), 2)
        d_val = round(float(d_line.iloc[-1]), 2)
 
        if k_val < 20 and k_line.iloc[-1] > d_line.iloc[-1]:
            sinyal = "AL"
            acik   = f"Stoch K({k_val}) aşırı satımda ve D({d_val})'yi yukarı kesti"
        elif k_val > 80 and k_line.iloc[-1] < d_line.iloc[-1]:
            sinyal = "SAT"
            acik   = f"Stoch K({k_val}) aşırı alımda ve D({d_val})'yi aşağı kesti"
        elif k_val < 20:
            sinyal = "AL"
            acik   = f"Stoch K({k_val}) aşırı satım bölgesinde"
        elif k_val > 80:
            sinyal = "SAT"
            acik   = f"Stoch K({k_val}) aşırı alım bölgesinde"
        else:
            sinyal = "NÖTR"
            acik   = f"Stochastic nötr (K={k_val}, D={d_val})"
 
        return IndikatorSonuc("Stochastic", k_val, sinyal, acik, agirlik=1.0)
 
    # ──────────────────────────────────────────
    # 6. ATR — Volatilite & Stop-Loss Seviyesi
    # ──────────────────────────────────────────
 
    def atr_hesapla(self, period: int = 14) -> float:
        """ATR stop-loss mesafesi hesaplamak için kullanılır."""
        tr = pd.concat([
            self.yuksek - self.dusuk,
            (self.yuksek - self.kapanis.shift()).abs(),
            (self.dusuk  - self.kapanis.shift()).abs()
        ], axis=1).max(axis=1)
        return round(float(tr.ewm(span=period, adjust=False).mean().iloc[-1]), 2)
 
    # ──────────────────────────────────────────
    # 7. Hacim Analizi
    # ──────────────────────────────────────────
 
    def hacim_sinyal(self, period: int = 20) -> IndikatorSonuc:
        ort_hacim   = self.hacim.rolling(period).mean()
        son_hacim   = float(self.hacim.iloc[-1])
        ort_val     = float(ort_hacim.iloc[-1])
        hacim_orani = son_hacim / ort_val if ort_val > 0 else 1.0
 
        son_fiyat_degisim = float(self.kapanis.iloc[-1]) - float(self.kapanis.iloc[-2])
 
        if hacim_orani > 1.5 and son_fiyat_degisim > 0:
            sinyal = "AL"
            acik   = f"Yüksek hacimli yükseliş (hacim ort.nın {hacim_orani:.1f}x'i)"
        elif hacim_orani > 1.5 and son_fiyat_degisim < 0:
            sinyal = "SAT"
            acik   = f"Yüksek hacimli düşüş (hacim ort.nın {hacim_orani:.1f}x'i)"
        elif hacim_orani < 0.5:
            sinyal = "NÖTR"
            acik   = f"Düşük hacim — hareket güvenilir değil ({hacim_orani:.1f}x)"
        else:
            sinyal = "NÖTR"
            acik   = f"Hacim normal seviyelerde ({hacim_orani:.1f}x ortalama)"
 
        return IndikatorSonuc("Hacim", round(hacim_orani, 2), sinyal, acik, agirlik=0.8)
 
    # ──────────────────────────────────────────
    # TÜM HESAPLAMALAR
    # ──────────────────────────────────────────
 
    def _hesapla(self):
        """Constructor'da çağrılır, tüm indikatörleri önceden hesaplar."""
        self._rsi_sonuc         = self.rsi_sinyal()
        self._macd_sonuc        = self.macd_sinyal()
        self._bollinger_sonuc   = self.bollinger_sinyal()
        self._ma_sonuc          = self.ma_sinyal()
        self._stoch_sonuc       = self.stochastic_sinyal()
        self._hacim_sonuc       = self.hacim_sinyal()
        self._atr               = self.atr_hesapla()
 
    # ──────────────────────────────────────────
    # GENEL SKOR & KARAR
    # ──────────────────────────────────────────
 
    def genel_skor(self) -> tuple[float, Sinyal, str]:
        """
        Tüm indikatörlerin ağırlıklı ortalamasını hesaplar.
        Dönen değer: (skor, sinyal, güç_etiketi)
        Skor aralığı: -1.0 (güçlü SAT) → +1.0 (güçlü AL)
        """
        sonuclar = [
            self._rsi_sonuc,
            self._macd_sonuc,
            self._bollinger_sonuc,
            self._ma_sonuc,
            self._stoch_sonuc,
            self._hacim_sonuc,
        ]
        toplam_agirlik = sum(s.agirlik for s in sonuclar)
        agirlikli_skor = sum(s.skor for s in sonuclar) / toplam_agirlik
 
        # Normalize: -1 → +1
        skor = round(agirlikli_skor, 3)
 
        if skor >= 0.4:
            sinyal, etiket = "AL",   "GÜÇLÜ AL"
        elif skor >= 0.15:
            sinyal, etiket = "AL",   "ZAYIF AL"
        elif skor <= -0.4:
            sinyal, etiket = "SAT",  "GÜÇLÜ SAT"
        elif skor <= -0.15:
            sinyal, etiket = "SAT",  "ZAYIF SAT"
        else:
            sinyal, etiket = "NÖTR", "NÖTR / BEKLE"
 
        return skor, sinyal, etiket
 
    # ──────────────────────────────────────────
    # ÖZET RAPOR
    # ──────────────────────────────────────────
 
    def tam_analiz(self) -> dict:
        """
        Tüm indikatör sonuçlarını ve genel skoru döndürür.
        Trade asistanının karar katmanına bu dict beslenecek.
        """
        skor, sinyal, etiket = self.genel_skor()
        son_fiyat = round(float(self.kapanis.iloc[-1]), 2)
        stop_loss = round(son_fiyat - 1.5 * self._atr, 2)  # 1.5 ATR altı
        hedef     = round(son_fiyat + 2.0 * self._atr, 2)  # 2.0 ATR üstü (risk/ödül 1:1.33)
 
        return {
            "sembol":     self.sembol,
            "son_fiyat":  son_fiyat,
            "tarih":      str(self.df.index[-1].date()),
            "genel_sinyal": etiket,
            "skor":       skor,
            "atr":        self._atr,
            "stop_loss":  stop_loss,
            "hedef_fiyat": hedef,
            "indikatorler": {
                "RSI":        {"deger": self._rsi_sonuc.deger,       "sinyal": self._rsi_sonuc.sinyal,       "aciklama": self._rsi_sonuc.aciklama},
                "MACD":       {"deger": self._macd_sonuc.deger,      "sinyal": self._macd_sonuc.sinyal,      "aciklama": self._macd_sonuc.aciklama},
                "Bollinger":  {"deger": self._bollinger_sonuc.deger, "sinyal": self._bollinger_sonuc.sinyal, "aciklama": self._bollinger_sonuc.aciklama},
                "MA":         {"deger": self._ma_sonuc.deger,        "sinyal": self._ma_sonuc.sinyal,        "aciklama": self._ma_sonuc.aciklama},
                "Stochastic": {"deger": self._stoch_sonuc.deger,     "sinyal": self._stoch_sonuc.sinyal,     "aciklama": self._stoch_sonuc.aciklama},
                "Hacim":      {"deger": self._hacim_sonuc.deger,     "sinyal": self._hacim_sonuc.sinyal,     "aciklama": self._hacim_sonuc.aciklama},
            }
        }
 
    def yazdir(self):
        """Konsola okunabilir özet basar."""
        analiz = self.tam_analiz()
        print(f"\n{'═'*58}")
        print(f"  {analiz['sembol']}  —  {analiz['tarih']}")
        print(f"  Son Fiyat : {analiz['son_fiyat']:>10.2f} TL")
        print(f"  ATR       : {analiz['atr']:>10.2f}  (volatilite ölçüsü)")
        print(f"  Stop-Loss : {analiz['stop_loss']:>10.2f}  (1.5 × ATR altı)")
        print(f"  Hedef     : {analiz['hedef_fiyat']:>10.2f}  (2.0 × ATR üstü)")
        print(f"{'─'*58}")
        print(f"  {'İNDİKATÖR':<14} {'DEĞER':>8}  {'SİNYAL':<8}  AÇIKLAMA")
        print(f"{'─'*58}")
        for ad, bilgi in analiz["indikatorler"].items():
            print(f"  {ad:<14} {bilgi['deger']:>8}  {bilgi['sinyal']:<8}  {bilgi['aciklama']}")
        print(f"{'─'*58}")
        print(f"  GENEL SKOR: {analiz['skor']:>+.3f}   →   {analiz['genel_sinyal']}")
        print(f"{'═'*58}\n")
 
 
# ─────────────────────────────────────────────────────────────────
# ÇOKLU HİSSE TARAMA
# ─────────────────────────────────────────────────────────────────
 
def coklu_hisse_tara(hisse_df: pd.DataFrame) -> pd.DataFrame:
    """
    Birden fazla hisseyi tek seferde tara, skor tablosu döndür.
    Kullanım:
        from bist_veri_cekici import coklu_hisse_cek
        df = coklu_hisse_cek(HISSELER)
        tablo = coklu_hisse_tara(df)
        print(tablo.sort_values("Skor", ascending=False))
    """
    sonuclar = []
    for sembol, grp in hisse_df.groupby("Sembol"):
        try:
            ta      = TeknikAnaliz(grp)
            analiz  = ta.tam_analiz()
            sonuclar.append({
                "Sembol":   sembol,
                "Fiyat":    analiz["son_fiyat"],
                "Sinyal":   analiz["genel_sinyal"],
                "Skor":     analiz["skor"],
                "RSI":      analiz["indikatorler"]["RSI"]["sinyal"],
                "MACD":     analiz["indikatorler"]["MACD"]["sinyal"],
                "Bollinger":analiz["indikatorler"]["Bollinger"]["sinyal"],
                "MA":       analiz["indikatorler"]["MA"]["sinyal"],
                "ATR":      analiz["atr"],
                "Stop":     analiz["stop_loss"],
                "Hedef":    analiz["hedef_fiyat"],
            })
        except Exception as e:
            print(f"  [HATA] {sembol}: {e}")
 
    df = pd.DataFrame(sonuclar).set_index("Sembol")
    return df.sort_values("Skor", ascending=False)
 
 
# ─────────────────────────────────────────────────────────────────
# TEST / DEMO
# ─────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    # bist_veri_cekici.py ile birlikte kullan
    try:
        from bist_veri_cekici import hisse_verisi_cek, coklu_hisse_cek, HISSELER
    except ImportError:
        print("[UYARI] bist_veri_cekici.py bulunamadı.")
        print("  Lütfen her iki dosyayı aynı klasöre koy.\n")
        exit()
 
    # --- Tek hisse analizi ---
    print("\n[1] Tek hisse analizi — THYAO.IS")
    df_thyao = hisse_verisi_cek("THYAO.IS", period="1y")
    if not df_thyao.empty:
        ta = TeknikAnaliz(df_thyao)
        ta.yazdir()
 
    # --- Tüm hisseleri tara ---
    print("[2] Tüm hisseleri tara")
    tum_df = coklu_hisse_cek(HISSELER, period="1y")
    if not tum_df.empty:
        tablo = coklu_hisse_tara(tum_df)
        print("\n  TARAMA SONUÇLARI (skora göre sıralı):\n")
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 130)
        print(tablo.to_string())
 
        # En güçlü AL sinyalleri
        al_listesi = tablo[tablo["Sinyal"].str.contains("AL")]
        if not al_listesi.empty:
            print(f"\n  AL sinyali veren hisseler ({len(al_listesi)} adet):")
            print(al_listesi[["Fiyat","Sinyal","Skor","ATR","Stop","Hedef"]].to_string())
 