"""
NEST API Integration Guide
=========================
Gerçek Trading için Nest (Halkbank) Entegrasyonu

ADIM 1: Nest Hesabı Açma
ADIM 2: API Credentials Alma
ADIM 3: Python Client Oluşturma
"""

# ============================================================================
# ADIM 1: NEST HESABI AÇMA
# ============================================================================

"""
1. Nest.ist websitesine git: https://www.nest.ist/
2. Yeni hesap aç (Kimlik doğrula)
3. Para yükle (Minimum genellikle 100 TL)
4. Trading izni aktif et
"""

# ============================================================================
# ADIM 2: API CREDENTIALS ALMA
# ============================================================================

"""
Nest Dashboard'dan:
1. Ayarlar → API/Uygulama Geliştirme
2. Yeni API Key oluştur
3. Secret Key'i kaydet (GÜVENLİ!)
4. Webhook URL ekle (isteğe bağlı)

İhtiyacın olacak:
- API_KEY
- API_SECRET
- ACCOUNT_ID (genellikle email)
"""

# ============================================================================
# ADIM 3: NEST PYTHON CLIENT
# ============================================================================

import requests
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class NestTradingClient:
    """Nest API Client - Gerçek Trading"""
    
    BASE_URL = "https://api.nest.ist"  # Production
    # BASE_URL = "https://sandbox.nest.ist"  # Sandbox test
    
    def __init__(self, api_key: str, api_secret: str, account_id: str = None):
        """
        Initialize Nest client
        
        Args:
            api_key: Nest API Key
            api_secret: Nest API Secret
            account_id: Opsiyonel (genellikle otomatik)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.account_id = account_id
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
        
    def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """
        API'ye request gönder
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url, json=data)
            else:
                return {"error": f"Unknown method: {method}"}
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error: {e}")
            return {"error": str(e)}
    
    def get_account_info(self) -> Dict:
        """Hesap bilgisi al"""
        return self._request("GET", "/account/info")
    
    def get_balance(self) -> Dict:
        """Bakiye bilgisi (para ve hisse)"""
        return self._request("GET", "/account/balance")
    
    def get_positions(self) -> List[Dict]:
        """Açık pozisyonları al"""
        result = self._request("GET", "/positions")
        return result.get("positions", []) if isinstance(result, dict) else []
    
    def get_orders(self, limit: int = 100) -> List[Dict]:
        """Geçmiş ve açık emirleri al"""
        return self._request("GET", f"/orders?limit={limit}")
    
    def place_order(
        self,
        symbol: str,
        order_type: str,  # "BUY" or "SELL"
        quantity: float,
        order_kind: str = "MARKET",  # "MARKET", "LIMIT", "STOP"
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict:
        """
        Emir ver (AL/SAT)
        
        Args:
            symbol: Hisse sembolü (ör: "SISE" veya "SISE.IS")
            order_type: "BUY" veya "SELL"
            quantity: Adet
            order_kind: "MARKET" (anında), "LIMIT" (fiyat belirt), "STOP" (koşulla)
            price: Limit emirinde birim fiyatı
            stop_price: Stop emirinde tetikleyici fiyat
        """
        
        # Symbol format standardize et
        if not symbol.endswith(".IS"):
            symbol = f"{symbol}.IS"
        
        payload = {
            "symbol": symbol,
            "order_type": order_type,
            "quantity": quantity,
            "order_kind": order_kind,
            "timestamp": datetime.now().isoformat()
        }
        
        if order_kind == "LIMIT" and price:
            payload["price"] = price
        if order_kind == "STOP" and stop_price:
            payload["stop_price"] = stop_price
        
        response = self._request("POST", "/orders/create", payload)
        
        if "error" not in response:
            logger.info(
                f"✅ Emir verildi: {order_type} × {quantity} {symbol} "
                f"| Emir ID: {response.get('order_id')}"
            )
        else:
            logger.error(f"❌ Emir hatası: {response['error']}")
        
        return response
    
    def cancel_order(self, order_id: str) -> Dict:
        """Emiryi iptal et"""
        return self._request("DELETE", f"/orders/{order_id}", {})
    
    def get_order_status(self, order_id: str) -> Dict:
        """Emir durumunu kontrol et"""
        return self._request("GET", f"/orders/{order_id}/status")


# ============================================================================
# ÖRNEK KULLANIM
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # ⚠️ KRİTİK: GÜVENLİK
    # API Key'i hiç koda yazmayın!
    # Bunun yerine environment variables kullan:
    
    import os
    
    api_key = os.getenv("NEST_API_KEY", "YOUR_API_KEY_HERE")
    api_secret = os.getenv("NEST_API_SECRET", "YOUR_API_SECRET_HERE")
    
    if "YOUR_API_KEY" in api_key:
        print("\n⚠️  API Credentials bulunamadı!")
        print("\nNasıl yapılır:")
        print("1. Nest Dashboard'dan API Key al")
        print("2. Environment variable ekle:")
        print("   Windows PowerShell:")
        print("   $env:NEST_API_KEY = 'your_key'")
        print("   $env:NEST_API_SECRET = 'your_secret'")
        print("\n3. Sonra bot'u başlat")
        exit(1)
    
    # Client oluştur
    client = NestTradingClient(api_key, api_secret)
    
    # Test: Hesap bilgisi al
    print("\n" + "="*60)
    print("TEST: Nest API Bağlantı")
    print("="*60)
    
    account = client.get_account_info()
    print(f"\nHesap: {account.get('account_name', 'Bilinmiyor')}")
    
    balance = client.get_balance()
    print(f"Bakiye: {balance.get('cash', 0):.2f} TL")
    
    # Açık pozisyonlar
    positions = client.get_positions()
    print(f"\nAçık Pozisyonlar: {len(positions)}")
    for pos in positions[:5]:
        print(f"  {pos.get('symbol')}: {pos.get('quantity')} adet @ {pos.get('avg_price'):.2f}")
    
    print("\n" + "="*60)

