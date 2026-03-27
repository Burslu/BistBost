"""
Mock Trading Dashboard - Portföy ve Açık Pozisyonları Göster
============================================================
"""

import json
from pathlib import Path
from datetime import datetime


def dashboard():
    """Mevcut portföy durumunu göster"""
    
    # Trading log dosyalarını bul
    log_file = Path("execution_log.json")
    if not log_file.exists():
        print("❌ Henüz işlem yok (execution_log.json bulunamadı)")
        return
    
    try:
        data = json.loads(log_file.read_text(encoding='utf-8'))
        
        portfolio = data.get("portfolio", {})
        executed = data.get("executed_signals", [])
        
        print("\n" + "="*70)
        print("📊 MOCK TRADING DASHBOARD")
        print("="*70)
        
        print(f"\n💰 PORTFÖY:")
        print(f"   Başlangıç: {portfolio.get('starting_portfolio', 0):.2f} TL")
        print(f"   Şuanki: {portfolio.get('current_portfolio', 0):.2f} TL")
        print(f"   Toplam PnL: {portfolio.get('total_pnl', 0):.2f} TL ({portfolio.get('pnl_percent', 0):.2f}%)")
        
        print(f"\n📈 POZİSYONLAR:")
        print(f"   Açık: {portfolio.get('open_positions_count', 0)}")
        print(f"   Kapalı: {portfolio.get('closed_positions_count', 0)}")
        print(f"   Açık Risk: {portfolio.get('open_risk_tl', 0):.2f} TL ({portfolio.get('open_risk_percent', 0):.2f}%)")
        
        if executed:
            print(f"\n📋 EXECUTE EDILEN SİNYALLER:")
            for sig in executed[-10:]:  # Son 10
                pnl_str = f"+{sig.get('pnl', 0):.2f} TL" if sig.get('pnl', 0) > 0 else f"{sig.get('pnl', 0):.2f} TL"
                status = "✅" if sig.get('pnl', 0) > 0 else "❌" if sig.get('pnl', 0) < 0 else "⚪"
                print(f"   {status} {sig['symbol']} {sig['type']} @ {sig['entry_price']:.2f} "
                      f"| EQ: {sig['entry_quality']:.0f}% | Cont: {sig['confidence']:.0f}%")
        
        print("\n" + "="*70)
        print(f"⏰ Güncelleme: {data.get('timestamp', 'Bilinmiyor')}")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Hata: {e}")


if __name__ == "__main__":
    dashboard()
