import json
import os

from core import storage

SETTINGS_FILE = os.path.join(storage.DATA_DIR, "settings.json")

DEFAULTS = {
    "first_run_prompted": False,
    "theme": "pink",
    "language": "ru",
    "autostart": False,
}


def load_settings():
    """Читает настройки из data/settings.json, дополняя значениями по умолчанию."""
    storage.ensure_dirs()
    settings = dict(DEFAULTS)

    if not os.path.exists(SETTINGS_FILE):
        save_settings(settings)
        return settings

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError, ValueError):
        return settings

    if isinstance(data, dict):
        settings.update(data)
    else:
        # Файл был пустым/некорректным — нормализуем его до словаря настроек
        save_settings(settings)
    return settings


def save_settings(settings):
    """Сохраняет настройки, гарантируя наличие всех ключей по умолчанию."""
    storage.ensure_dirs()
    merged = dict(DEFAULTS)
    if isinstance(settings, dict):
        merged.update(settings)

    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(merged, file, ensure_ascii=False, indent=2)
    return merged


def get(key, default=None):
    return load_settings().get(key, DEFAULTS.get(key, default))


def set_value(key, value):
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
    return settings
