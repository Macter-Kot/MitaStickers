import json
import os

from core import settings, storage

# Код языка -> его название на самом языке (для окна настроек)
LANGUAGES = {
    "ru": "Русский",
    "en": "English",
}

_current_language = None
_translations = {}
_loaded = False


def _locales_dir():
    return os.path.join(storage.RESOURCE_DIR, "locales")


def _load_catalog(lang):
    path = os.path.join(_locales_dir(), "{}.json".format(lang))
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError):
        return {}
    if isinstance(data, dict):
        return {str(key): str(value) for key, value in data.items()}
    return {}


def _ensure_loaded():
    global _current_language, _translations, _loaded
    if _loaded:
        return
    lang = "ru"
    try:
        lang = settings.get("language", "ru") or "ru"
    except Exception:
        pass
    if lang not in LANGUAGES:
        lang = "ru"
    _current_language = lang
    _translations = _load_catalog(lang)
    _loaded = True


def _(text):
    """Возвращает перевод строки для текущего языка.

    Ключом служит оригинальная русская строка. Если перевода нет — возвращается сам ключ.
    """
    if not text:
        return text
    _ensure_loaded()
    return _translations.get(text, text)


def get_language():
    _ensure_loaded()
    return _current_language


def set_language(lang, persist=True):
    """Меняет язык (и при persist=True сохраняет его в settings.json)."""
    global _current_language, _translations, _loaded
    if lang not in LANGUAGES:
        lang = "ru"
    _current_language = lang
    _translations = _load_catalog(lang)
    _loaded = True
    if persist:
        try:
            settings.set_value("language", lang)
        except Exception:
            pass
    return lang


def language_label(lang):
    return LANGUAGES.get(lang, lang)


def available_languages():
    return dict(LANGUAGES)
