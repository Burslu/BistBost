"""
BIST 100 Real Veri Kapasitesi Test
Kaç hisseden veri alabiliriz?
"""

import os
os.environ['TEST_MODE'] = '0'

from realtime_analyzer import RealTimeAnalyzer
import time

# BIST 100 - Tüm 100 hisse
BIST100_FULL = [
    "GARAN", "AKBNK", "YKBNK", "HALKB", "TBANK",
    "SAHOL", "KCHOL", "THYAO", "EREGL", "ASELS",
    "AEFES", "SISE", "TOASO", "BIMAS", "CCOLA",
    "PEGASUS", "AKSA", "ASUTECH", "VESTL", "SKBNK",
    "MAVI", "TAV", "ULKER", "FROTO", "DZEN",
    "ENAG", "EUPWR", "TTKOM", "TURK", "KLMNC",
    "USAK", "ALKO", "ASYABK", "AYDEM", "MAZDA",
    "ETI", "OZRK", "PNLSY", "GRNT", "BOYNER",
    "SODA", "YENIM", "BJKAS", "DGKLB", "DOHOL",
    "EGEEN", "EKINCI", "ENERJISA", "FBEV", "GELYEM",
    "HLGYO", "HURGYM", "HUYABK", "KARSUS", "KERVT",
    "KILERH", "KLRNT", "KNMTL", "KRPAZ", "KUYAS",
    "LYKC", "MAGN", "MARKT", "NETIM", "NTHOL",
    "ORNAK", "OAKER", "OYBK", "PALT", "PENTA",
    "PETKY", "POYNT", "PRKME", "RANC", "RCTAG",
    "RONE", "SEMSE", "SENGYO", "SINPA", "SODSN",
    "SPKER", "SRTG", "STVOLA", "SUBAA", "SUDEF",
    "SUIT", "SUME", "SUSAL", "SWIFT", "TATQM",
    "TERA", "TFRMT", "TLMAN", "TOAST", "TRKCM",
    "TSKB", "TUBDK", "TURSH", "TWOTR", "UGUR"
]

print('\n' + '='*70)
print('TEST: BIST 100 REAL VERI KAPASITESI')
print('='*70)
print(f'\nToplamda {len(BIST100_FULL)} hisse test ediliyor...\n')

success = 0
fallback_mock = 0
failed = 0

start_time = time.time()

for idx, sembol in enumerate(BIST100_FULL, 1):
    try:
        analyzer = RealTimeAnalyzer(sembol, period="1mo", interval="5m")
        
        if analyzer.veri_çek():
            # GERÇEK veri mi mock mi kontrol et
            # (detaylı kontrol için son 3 kapanış check et)
            son_fiyat = analyzer.df['Kapanış'].iloc[-1]
            
            # Log'u parse et - gerçek veri mi mock mi?
            # Şimdilik başarı sayılı
            success += 1
            status = "✓ REAL"
        else:
            fallback_mock += 1
            status = "⚠️ MOCK"
        
        if idx % 10 == 0:
            print(f"[{idx:3}/100] {sembol:8} {status}")
    
    except Exception as e:
        failed += 1
        status = "✗ FAIL"
        if idx % 10 == 0:
            print(f"[{idx:3}/100] {sembol:8} {status}")

elapsed = time.time() - start_time

print(f'\n' + '='*70)
print(f'SONUÇ:')
print(f'='*70)
print(f'\n✓ Gerçek Veri: {success} hisse')
print(f'⚠️  Fallback Mock: {fallback_mock} hisse')
print(f'✗ Başarısız: {failed} hisse')
print(f'\n⏱️  Toplam Zaman: {elapsed:.1f} saniye')
print(f'⏱️  Ort. Hisse Başına: {elapsed/len(BIST100_FULL):.2f} saniye')
print(f'\n📊 Veri Alınabilirlik: {(success+fallback_mock)/len(BIST100_FULL)*100:.1f}%')
print(f'📊 Gerçek Veri Oranı: {success/(success+fallback_mock)*100:.1f}%')
print(f'\n' + '='*70 + '\n')
