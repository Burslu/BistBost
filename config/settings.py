"""
Configuration Loader - settings.json yükleme
"""

import json
from pathlib import Path

def load_settings():
    """settings.json dosyasını yükle"""
    settings_file = Path(__file__).parent / "settings.json"
    
    with open(settings_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_settings(settings):
    """settings.json dosyasına kaydet"""
    settings_file = Path(__file__).parent / "settings.json"
    
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
