import json
from datetime import datetime
from pathlib import Path
from urllib import parse, request

import pandas as pd

from bist_veri_cekici import coklu_hisse_cek, hareketli_ortalama_ekle
from teknik_analiz import TeknikAnaliz


BASE_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = BASE_DIR / "config" / "settings.json"


def load_settings(path: Path = SETTINGS_PATH) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_directories(settings: dict) -> dict:
    raw_dir = BASE_DIR / settings["paths"]["raw_dir"]
    signals_dir = BASE_DIR / settings["paths"]["signals_dir"]
    log_dir = BASE_DIR / settings["paths"]["log_dir"]

    for d in [raw_dir, signals_dir, log_dir]:
        d.mkdir(parents=True, exist_ok=True)

    return {
        "raw_dir": raw_dir,
        "signals_dir": signals_dir,
        "log_dir": log_dir,
    }


def build_signal_tables(settings: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    period = settings["market_data"]["period"]
    interval = settings["market_data"]["interval"]

    bist_symbols = settings["symbols"]["bist"]
    hisse_df = coklu_hisse_cek(bist_symbols, period=period, interval=interval)
    if hisse_df.empty:
        raise RuntimeError("BIST verisi cekilemedi. Sembol listesini ve internet baglantisini kontrol et.")

    hisse_df = hareketli_ortalama_ekle(hisse_df)

    tum_sinyaller = []
    for sembol, grp in hisse_df.groupby("Sembol"):
        try:
            analiz = TeknikAnaliz(grp).tam_analiz()
            tum_sinyaller.append(
                {
                    "sembol": analiz["sembol"],
                    "tarih": analiz["tarih"],
                    "fiyat": analiz["son_fiyat"],
                    "genel_sinyal": analiz["genel_sinyal"],
                    "skor": analiz["skor"],
                    "atr": analiz["atr"],
                    "stop_loss": analiz["stop_loss"],
                    "hedef_fiyat": analiz["hedef_fiyat"],
                }
            )
        except Exception as exc:
            tum_sinyaller.append(
                {
                    "sembol": sembol,
                    "tarih": "-",
                    "fiyat": None,
                    "genel_sinyal": "HATA",
                    "skor": 0.0,
                    "atr": None,
                    "stop_loss": None,
                    "hedef_fiyat": None,
                    "hata": str(exc),
                }
            )

    tum_df = pd.DataFrame(tum_sinyaller).sort_values("skor", ascending=False)

    min_score = float(settings["strategy"]["min_abs_score_for_signal"])
    max_signals = int(settings["strategy"]["max_signals"])

    aksiyon_df = tum_df[tum_df["skor"].abs() >= min_score].head(max_signals).copy()
    return hisse_df, tum_df, aksiyon_df


def build_telegram_message(aksiyon_df: pd.DataFrame, settings: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode = "DRY-RUN" if settings["telegram"].get("dry_run", True) else "LIVE"

    lines = [
        f"BIST Trade Asistani | {mode}",
        f"Tarih: {now}",
        "",
    ]

    if aksiyon_df.empty:
        lines.append("Bugun esik degerini asan sinyal yok. BEKLE.")
    else:
        lines.append("Oncelikli sinyaller:")
        max_items = int(settings["telegram"]["max_signals_in_message"])

        for i, (_, row) in enumerate(aksiyon_df.head(max_items).iterrows(), start=1):
            lines.append(
                f"{i}) {row['sembol']} | {row['genel_sinyal']} | skor: {row['skor']:+.3f} | "
                f"fiyat: {row['fiyat']:.2f} | stop: {row['stop_loss']:.2f} | hedef: {row['hedef_fiyat']:.2f}"
            )

    lines.extend([
        "",
        "Not: Bu cikti yatirim tavsiyesi degildir.",
    ])

    return "\n".join(lines)


def send_telegram_message(message: str, settings: dict) -> bool:
    telegram_cfg = settings["telegram"]
    enabled = telegram_cfg.get("enabled", False)
    dry_run = telegram_cfg.get("dry_run", True)
    token = telegram_cfg.get("bot_token", "").strip()
    chat_id = telegram_cfg.get("chat_id", "").strip()

    if dry_run or not enabled:
        print("\n[TELEGRAM DRY-RUN] Mesaj gonderilmedi. Uretilecek metin:\n")
        print(message)
        return False

    if not token or not chat_id:
        print("[UYARI] Telegram aktif ama bot_token/chat_id eksik. Mesaj gonderilmedi.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = parse.urlencode({"chat_id": chat_id, "text": message}).encode("utf-8")

    try:
        req = request.Request(url, data=payload, method="POST")
        with request.urlopen(req, timeout=10) as resp:
            ok = resp.status == 200
        print("[OK] Telegram mesaji gonderildi." if ok else "[HATA] Telegram API basarisiz dondu.")
        return ok
    except Exception as exc:
        print(f"[HATA] Telegram gonderimi basarisiz: {exc}")
        return False


def save_outputs(hisse_df: pd.DataFrame, tum_df: pd.DataFrame, aksiyon_df: pd.DataFrame, message: str, dirs: dict) -> dict:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    raw_path = dirs["raw_dir"] / f"hisseler_{stamp}.csv"
    all_sig_path = dirs["signals_dir"] / f"tum_sinyaller_{stamp}.csv"
    act_sig_path = dirs["signals_dir"] / f"aksiyon_sinyalleri_{stamp}.csv"
    log_path = dirs["log_dir"] / f"run_{stamp}.json"

    hisse_df.to_csv(raw_path, encoding="utf-8-sig")
    tum_df.to_csv(all_sig_path, index=False, encoding="utf-8-sig")
    aksiyon_df.to_csv(act_sig_path, index=False, encoding="utf-8-sig")

    log_data = {
        "timestamp": stamp,
        "raw_data_file": str(raw_path),
        "all_signals_file": str(all_sig_path),
        "actionable_signals_file": str(act_sig_path),
        "telegram_preview": message,
        "actionable_count": int(len(aksiyon_df)),
    }

    with log_path.open("w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    return {
        "raw_path": raw_path,
        "all_sig_path": all_sig_path,
        "act_sig_path": act_sig_path,
        "log_path": log_path,
    }


def main() -> None:
    settings = load_settings()
    dirs = ensure_directories(settings)

    global_period = settings["market_data"]["period"]
    global_interval = settings["market_data"]["interval"]
    global_symbols = settings["symbols"]["global"]

    # Makro veriler su an karar modeline dahil edilmiyor; ileriki fazlar icin saklaniyor.
    global_df = coklu_hisse_cek(global_symbols, period=global_period, interval=global_interval)

    hisse_df, tum_df, aksiyon_df = build_signal_tables(settings)
    message = build_telegram_message(aksiyon_df, settings)
    sent = send_telegram_message(message, settings)
    paths = save_outputs(hisse_df, tum_df, aksiyon_df, message, dirs)

    if not global_df.empty:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        global_path = dirs["raw_dir"] / f"global_{stamp}.csv"
        global_df.to_csv(global_path, encoding="utf-8-sig")
        print(f"[KAYIT] Global veri kaydedildi: {global_path}")

    print("\n===== GUNLUK CALISMA OZETI =====")
    print(f"Toplam sembol: {len(tum_df)}")
    print(f"Aksiyon sinyali: {len(aksiyon_df)}")
    print(f"Telegram gonderildi: {'EVET' if sent else 'HAYIR'}")
    print(f"Tum sinyaller: {paths['all_sig_path']}")
    print(f"Aksiyon sinyalleri: {paths['act_sig_path']}")
    print(f"Run log: {paths['log_path']}")


if __name__ == "__main__":
    main()
