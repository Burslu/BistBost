"""
Telegram Bot - BIST Trade Asistani
==================================
Her gün kapanıştan sonra sinyalleri Telegram'a gönderir.

Kurulum:
1. BotFather'dan token al: https://t.me/BotFather
2. Kendi chat ID'nizi al: https://t.me/userinfobot
3. config/settings.json içinde telegram.bot_token ve telegram.chat_id 'ye yapıştır
4. telegram.enabled = true, telegram.dry_run = false yap
5. python telegram_bot.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Telegram kütüphanesi
try:
    import requests
except ImportError:
    print("[HATA] requests kütüphanesi yüklü değil. Kurulum:")
    print("  py -m pip install requests")
    sys.exit(1)

from gunluk_sinyal_akisi import (
    load_settings,
    ensure_directories,
    build_signal_tables,
    build_telegram_message,
    save_outputs,
)


def send_telegram_bot(message: str, settings: dict) -> bool:
    """
    Telegram Bot API kullanarak mesaj gönderir.
    
    Gerekli ayarlar:
    - telegram.bot_token
    - telegram.chat_id
    - telegram.enabled
    - telegram.dry_run
    """
    telegram_cfg = settings.get("telegram", {})
    enabled = telegram_cfg.get("enabled", False)
    dry_run = telegram_cfg.get("dry_run", True)
    token = telegram_cfg.get("bot_token", "").strip()
    chat_id = telegram_cfg.get("chat_id", "").strip()

    # Dry-run modunda sadece konsolda yazdir
    if dry_run:
        print("\n[TELEGRAM DRY-RUN] Mesaj gönderilmedi. Terminal çıktısı:")
        print("=" * 60)
        print(message)
        print("=" * 60)
        print("\nCanlı gönderiş için:")
        print("  1. config/settings.json'da telegram.dry_run = false yap")
        print("\n")
        return False

    # Canlı gönderiş
    if not enabled:
        print("[UYARI] Telegram aktif değil (telegram.enabled = false).")
        return False

    if not token or not chat_id:
        print("[HATA] Telegram bot_token veya chat_id boş!")
        print("  Lütfen config/settings.json'da Telegram bilgilerini ekle:")
        print("    - telegram.bot_token: BotFather'dan aldığın token")
        print("    - telegram.chat_id: Senin chat ID'n (userinfobot'tan al)")
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",  # HTML format desteği
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("[OK] Telegram mesajı gönderildi.")
            return True
        else:
            print(f"[HATA] Telegram API döndü: {response.status_code}")
            print(f"  Mesaj: {response.text}")
            return False

    except Exception as exc:
        print(f"[HATA] Telegram gönderimi başarısız: {exc}")
        return False


def main():
    """Telegram bot ana döngüsü."""
    settings = load_settings()
    dirs = ensure_directories(settings)

    print("\n" + "=" * 60)
    print("  TELEGRAM BOT - BIST TRADE ASISTANI")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    # Sinyal tabloları oluştur
    hisse_df, tum_df, aksiyon_df = build_signal_tables(settings)

    # Telegram mesajı oluştur
    message = build_telegram_message(aksiyon_df, settings)

    # Gönder
    sent = send_telegram_bot(message, settings)

    # Çıktıları kaydet
    paths = save_outputs(hisse_df, tum_df, aksiyon_df, message, dirs)

    # Özet
    print("\n" + "=" * 60)
    print("  ÖZET")
    print("=" * 60)
    print(f"Toplam sinyal: {len(tum_df)}")
    print(f"Aksiyon sinyali: {len(aksiyon_df)}")
    print(f"Telegram: {'GÖNDERİLDİ' if sent else 'DRY-RUN'}")
    print(f"Sinyal CSV: {paths['all_sig_path'].name}")
    print(f"Log: {paths['log_path'].name}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
