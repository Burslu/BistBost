"""
Test amaçlı realtime analyzer - 2 döngü, 1 symbol
"""

import sys
sys.path.insert(0, '.')

from realtime_analyzer import RealTimeAnalyzer
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Test et: THYAO.IS
print("=" * 60)
print("TEST: THYAO.IS analizi (5 dakikalık veriler)")
print("=" * 60)

analyzer = RealTimeAnalyzer("THYAO.IS", period="1mo", interval="5m")

# Veri çek
if analyzer.veri_çek():
    print(f"✓ Veri çekildi: {len(analyzer.df)} bar")
    print(f"  Son 3 bar:\n{analyzer.df[['Açılış', 'Kapanış', 'Hacim']].tail(3)}\n")
    
    # Tam analiz
    sinyal = analyzer.tamAnaliz()
    
    if sinyal:
        print(f"\n✓ Analiz tamamlandı:")
        print(f"  Sembol: {sinyal.sembol}")
        print(f"  Fiyat: {sinyal.fiyat:.2f} TL")
        print(f"  Sinyal: {sinyal.sinyal_seviyesi}")
        print(f"  Ağırlıklı Skor: {sinyal.ağırlıklı_skor}")
        print(f"  Güven: {sinyal.güven_yüzdesi}%")
        print(f"  Stop-Loss: {sinyal.stop_loss:.2f}")
        print(f"  Hedef: {sinyal.hedef:.2f}")
        print(f"\n  İndikatör Detayları:")
        for ind in sinyal.indikatörler:
            print(f"    • {ind.ad}: {ind.sinyal} (deger: {ind.deger:.4f}, ağırlık: {ind.agirlik}, skor: {ind.skor:.4f})")
    else:
        print("✗ Analiz başarısız")
else:
    print("✗ Veri çekme başarısız")

print("\n" + "=" * 60)
print("TEST BİTTİ")
print("=" * 60)
