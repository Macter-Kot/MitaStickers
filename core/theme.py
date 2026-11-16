DEFAULT_THEME = "pink"

THEMES = {
    "pink": {
        # --- Цвета интерфейса ---
        "bg_main": "#FADDE1",       # Фон главного окна создания/редактирования
        "header_bg": "#F6C6CF",     # Фон шапки окна
        "border": "#E8A3B4",        # Обводка полей ввода (Entry, Text)
        "panel_bg": "#FFF8E1",      # Кремовый фон внутренних панелей и полей ввода
        "text": "#3E2723",          # Основной темный текст
        "muted": "#8D6E63",         # Второстепенный текст (подписи, формат даты)
        
        # --- Кнопки ---
        "primary": "#F4A7B9",       # Основной розовый (шестеренка, "Выбрать файл")
        "primary_dark": "#EC8FA6",  # Розовый потемнее (ховер-эффект)
        "green": "#66BB6A",         # Кнопка "Создать" / "Сохранить"
        "green_dark": "#43A047",    # Ховер для зеленой кнопки
        "red": "#EF5350",           # Кнопка "Отмена" / "Удалить"
        "red_dark": "#C62828",      # Ховер для красной кнопки
        "off": "#E0E0E0",           # Неактивные кнопки (фильтры)
        "off_dark": "#CFCFCF",      # Ховер неактивных кнопок
        
        # --- Панели и Карточки (Менеджер и Настройки) ---
        "panel_border": "#F06292",  # Рамка панели/ заголовки
        "card_bg": "#FFFFFF",       # Белый фон карточек с настройками
        "card_border": "#FBC02D",   # Желтая рамка карточек

        # --- Скроллбар ---
        "scrollbar_bg": "#F6C6CF",          # Желоб (trough)
        "scrollbar_thumb": "#F4A7B9",       # Ползунок
        "scrollbar_thumb_active": "#EC8FA6",  # Ползунок при наведении
        "scrollbar_arrow": "#8D6E63",       # Стрелочки

        # --- Крестик закрытия ---
        "close_btn_color": "#9C8489",       # Темный серо-розовый элемент

        # --- Картридж ---
        "cartridge_tint": None      # Оригинальный цвет картинки
    },
    
    "purple": {
        # --- Цвета интерфейса ---
        "bg_main": "#2E2352",       # Темно-фиолетовый фон окна
        "header_bg": "#251C43",     # Еще более темная шапка
        "border": "#483889",        # Обводка полей
        "panel_bg": "#2C2C36",      # Фон панелей
        "text": "#FFFFFF",          # Белый текст
        "muted": "#B39DDB",         # Светло-фиолетовый текст
        
        # --- Кнопки ---
        "primary": "#7B5CB8",       
        "primary_dark": "#5E4596",
        "green": "#4CAF50",         
        "green_dark": "#388E3C",
        "red": "#E36A75",           
        "red_dark": "#C5535D",
        "off": "#3B2D6B",           
        "off_dark": "#2E2352",
        
        # --- Панели и Карточки ---
        "panel_border": "#B39DDB",  # Фиолетовая рамка/ заголовки
        "card_bg": "#3C3C4C",       # Фон карточек
        "card_border": "#5E4596",   

        # --- Скроллбар ---
        "scrollbar_bg": "#251C43",          # Желоб (trough)
        "scrollbar_thumb": "#7B5CB8",       # Ползунок
        "scrollbar_thumb_active": "#5E4596",  # Ползунок при наведении
        "scrollbar_arrow": "#B39DDB",       # Стрелочки

        # --- Крестик закрытия ---
        "close_btn_color": "#1A0F33",       # Тёмно-фиолетовый, как вдавленная гравировка

        # --- Картридж ---
        "cartridge_tint": "#483889" # Цвет тонировки
    }
}

# Код темы -> подпись на русском (переводится через _() в UI)
THEME_LABELS = {
    "pink": "Розовая",
    "purple": "Тёмно-фиолетовая",
}


def get_theme(name=None):
    """Возвращает словарь цветов текущей темы (из settings.json -> "theme")."""
    if name is None:
        name = DEFAULT_THEME
        try:
            from core import settings

            name = settings.get("theme", DEFAULT_THEME) or DEFAULT_THEME
        except Exception:
            pass
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def get_theme_name():
    try:
        from core import settings

        name = settings.get("theme", DEFAULT_THEME) or DEFAULT_THEME
    except Exception:
        name = DEFAULT_THEME
    return name if name in THEMES else DEFAULT_THEME


def set_theme(name, persist=True):
    if name not in THEMES:
        name = DEFAULT_THEME
    if persist:
        try:
            from core import settings

            settings.set_value("theme", name)
        except Exception:
            pass
    return THEMES[name]
