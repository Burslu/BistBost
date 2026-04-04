"""
🎯 MOCK PORTFOLIO TRADER - 10000 TL Backtest
═══════════════════════════════════════════════════════════════════
GÜÇLÜ AL sinyallerinden otomatik AL-SAT yapıp profitability track et
"""

import os
os.environ['TEST_MODE'] = '1'  # Mock veri

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from realtime_analyzer import RealTimeAnalyzer
    from config.settings import load_settings
except ImportError as e:
    print(f"Import hatası: {e}")
    sys.exit(1)


class MockPortfolioTrader:
    """10000 TL mock portföy - AL/SAT simülasyonu"""
    
    def __init__(self, initial_balance=10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance  # Nakit
        self.positions = {}  # {'GARAN': {'miktar': 100, 'giriş': 28.45, 'al_zamani': datetime}}
        self.trade_log = []  # Kapandı işlemler
        self.açık_işlemler = []  # Açık pozisyonlar
        
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0
        
        print(f"\n{'='*70}")
        print(f"🎯 MOCK PORTFÖY TRADER BAŞLATILDI")
        print(f"{'='*70}")
        print(f"💰 Başlangıç Bakiyesi: {initial_balance:,.0f} ₺")
        print(f"{'='*70}\n")
    
    def al(self, sembol, giriş, tp, sl, güven):
        """GÜÇLÜ AL sinyalinden pozisyon aç"""
        
        # Kaç adet alabilir? (Başlangıç %10 risk ile)
        risk_amount = self.balance * 0.10  # %10 risk
        risk_pct = ((giriş - sl) / giriş) * 100
        
        if risk_pct <= 0:
            return False
        
        # Risk tutarından miktar hesapla
        miktar = int(risk_amount / ((giriş - sl) / giriş * giriş))
        
        if miktar <= 0 or self.balance < (giriş * miktar):
            print(f"  ⚠️  {sembol}: Yeterli bakiye yok (Gerekli: {giriş * miktar:,.0f} ₺)")
            return False
        
        # Pozisyon aç
        harcama = giriş * miktar
        self.balance -= harcama
        self.positions[sembol] = {
            'miktar': miktar,
            'giriş': giriş,
            'tp': tp,
            'sl': sl,
            'al_zamani': datetime.now(),
            'güven': güven
        }
        
        kar_target = (tp - giriş) / giriş * 100
        
        self.açık_işlemler.append({
            'sembol': sembol,
            'tip': 'AL',
            'miktar': miktar,
            'giriş': giriş,
            'tp': tp,
            'sl': sl,
            'zamani': datetime.now(),
            'status': 'AÇIK',
            'kar_hedefi_%': kar_target
        })
        
        print(f"✓ AL: {sembol} | {miktar} adet @ {giriş:.2f}₺ ({güven:.0f}%)")
        print(f"   Giriş: {harcama:,.0f}₺ | TP: {tp:.2f}₺ (+{kar_target:.1f}%) | SL: {sl:.2f}₺")
        print(f"   Kalan Bakiye: {self.balance:,.0f}₺\n")
        
        return True
    
    def tp_hit(self, sembol):
        """Hedef fiyatı vur - Kar"""
        if sembol not in self.positions:
            return False
        
        pos = self.positions.pop(sembol)
        miktar = pos['miktar']
        tp = pos['tp']
        giriş = pos['giriş']
        
        # Kar hesapla
        yatırılan = giriş * miktar
        elde_edilen = tp * miktar
        kar = elde_edilen - yatırılan
        kar_pct = (kar / yatırılan) * 100
        
        self.balance += elde_edilen
        self.total_trades += 1
        self.winning_trades += 1
        self.total_profit += kar
        
        al_zamani = pos['al_zamani']
        
        # Log'a kaydet
        self.trade_log.append({
            'sembol': sembol,
            'tip': 'AL→TP',
            'miktar': miktar,
            'giriş': giriş,
            'çıkış': tp,
            'kar': kar,
            'kar_%': kar_pct,
            'zarar': 0,
            'zarar_%': 0,
            'al_zamani': al_zamani,
            'status': 'BAŞARILI'
        })
        
        print(f"🎉 TP HİT: {sembol}")
        print(f"   Kar: +{kar:,.0f}₺ ({kar_pct:+.1f}%)")
        print(f"   Toplam Bakiye: {self.balance:,.0f}₺\n")
        
        return True
    
    def sl_hit(self, sembol):
        """Stop loss'a vur - Zarar"""
        if sembol not in self.positions:
            return False
        
        pos = self.positions.pop(sembol)
        miktar = pos['miktar']
        sl = pos['sl']
        giriş = pos['giriş']
        
        # Zarar hesapla
        yatırılan = giriş * miktar
        elde_edilen = sl * miktar
        zarar = elde_edilen - yatırılan
        zarar_pct = (zarar / yatırılan) * 100
        
        self.balance += elde_edilen
        self.total_trades += 1
        self.losing_trades += 1
        self.total_profit += zarar
        
        al_zamani = pos['al_zamani']
        
        # Log'a kaydet
        self.trade_log.append({
            'sembol': sembol,
            'tip': 'AL→SL',
            'miktar': miktar,
            'giriş': giriş,
            'çıkış': sl,
            'kar': 0,
            'kar_%': 0,
            'zarar': zarar,
            'zarar_%': zarar_pct,
            'al_zamani': al_zamani,
            'status': 'STOP HİT'
        })
        
        print(f"❌ STOP HİT: {sembol}")
        print(f"   Zarar: {zarar:,.0f}₺ ({zarar_pct:.1f}%)")
        print(f"   Toplam Bakiye: {self.balance:,.0f}₺\n")
        
        return True
    
    def rapor(self):
        """Gün sonu rapor"""
        print(f"\n{'='*70}")
        print(f"📊 TRADING RAPORU")
        print(f"{'='*70}\n")
        
        starting_bal = self.initial_balance
        current_bal = self.balance
        total_pnl = current_bal - starting_bal
        pnl_pct = (total_pnl / starting_bal) * 100
        
        print(f"💰 BAKIYE")
        print(f"   Başlangıç: {starting_bal:,.0f}₺")
        print(f"   Şimdiki: {current_bal:,.0f}₺")
        print(f"   Net P&L: {total_pnl:+,.0f}₺ ({pnl_pct:+.2f}%)")
        print()
        
        if self.total_trades > 0:
            win_rate = (self.winning_trades / self.total_trades) * 100
            avg_win = sum([t['kar'] for t in self.trade_log if 'kar' in t]) / self.winning_trades if self.winning_trades > 0 else 0
            avg_loss = sum([abs(t['zarar']) for t in self.trade_log if 'zarar' in t]) / self.losing_trades if self.losing_trades > 0 else 0
            
            print(f"📈 İŞLEM İSTATİSTİKLERİ")
            print(f"   Toplam İşlem: {self.total_trades}")
            print(f"   Kazanç: {self.winning_trades} ({win_rate:.1f}%)")
            print(f"   Kayıp: {self.losing_trades}")
            print(f"   Ort. Kazanç/İşlem: {avg_win:+,.0f}₺")
            print(f"   Ort. Kayıp/İşlem: {avg_loss:+,.0f}₺")
            print()
        
        print(f"📋 İŞLEM DETAYLARı")
        if self.trade_log:
            df = pd.DataFrame(self.trade_log)
            cols_to_show = [col for col in ['sembol', 'tip', 'giriş', 'çıkış', 'kar', 'zarar', 'status'] if col in df.columns]
            print(df[cols_to_show].to_string(index=False))
        else:
            print("Henüz trade yok")
        
        print(f"\n{'='*70}\n")
        
        return {
            'starting_balance': starting_bal,
            'current_balance': current_bal,
            'total_pnl': total_pnl,
            'pnl_pct': pnl_pct,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        }


def test_mock_trader():
    """ADIM 2 Test"""
    
    trader = MockPortfolioTrader(initial_balance=10000)
    
    # TEST 1: GARAN AL
    print("\n🟢 TEST 1: GARAN AL Sinyali")
    print("─" * 70)
    trader.al(
        sembol='GARAN',
        giriş=28.45,
        tp=32.30,
        sl=25.20,
        güven=85
    )
    
    # TEST 2: AKBNK AL
    print("🟢 TEST 2: AKBNK AL Sinyali")
    print("─" * 70)
    trader.al(
        sembol='AKBNK',
        giriş=12.65,
        tp=14.50,
        sl=11.20,
        güven=78
    )
    
    # TEST 3: EREGL AL
    print("🟢 TEST 3: EREGL AL Sinyali")
    print("─" * 70)
    trader.al(
        sembol='EREGL',
        giriş=36.80,
        tp=42.10,
        sl=33.50,
        güven=72
    )
    
    # TEST 4: TP HİT
    print("🟢 TEST 4: GARAN TP HİT")
    print("─" * 70)
    trader.tp_hit('GARAN')
    
    # TEST 5: TP HİT
    print("🟢 TEST 5: AKBNK TP HİT")
    print("─" * 70)
    trader.tp_hit('AKBNK')
    
    # TEST 6: SL HİT
    print("🟢 TEST 6: EREGL SL HİT")
    print("─" * 70)
    trader.sl_hit('EREGL')
    
    # RAPOR
    rapor = trader.rapor()
    
    return rapor


if __name__ == "__main__":
    test_mock_trader()
