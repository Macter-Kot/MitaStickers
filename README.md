# MitaStickers 0.1

<p align="center">
  <img src="assets/preview.png" alt="MitaStickers Cartridge" width="600"/>
</p>

<p align="center">
  🌐 <b>Русский</b>
</p>

## MitaStickers - Программа для показа стикеров напоминалок о различных событиях.

### Автор
- **[mactep_kot_](https://github.com/Macter-Kot)**
---

### Структура проекта

MitaStickers/
│
├── main.py                 # Главный файл
├── requirements.txt        # Список библиотек (Pillow, pystray, python-dateutil)
├── README.md               # Краткое описание проекта
│
├── data/                   # Папка для хранения данных
│   ├── stickers.json       # Файл, где лежат напоминалки
│   └── settings.json       # Настройки приложения
│
├── assets/                 # Ассеты
│   ├── icon.ico            # Иконка окна/панели задач
│   ├── default_icon.ico    # Иконка системного трея
│   ├── logo.png            # Логотип в шапке окна создания
│   ├── cartridge.png       # Картридж для окон менеджера/настроек
│   └── default_placeholder.png  # Заглушка картинок в стикерах
│
├── locales/                # Словари переводов
│   ├── ru.json
│   └── en.json
│
├── core/                   # Логика
│   ├── __init__.py
│   ├── storage.py          # Чтение и запись JSON-файла напоминалок
│   ├── settings.py         # Чтение и запись настроек
│   ├── i18n.py             # Локализация (переводы, смена языка)
│   ├── theme.py            # Темы оформления (pink / purple)
│   ├── date_utils.py       # Форматы даты и времени (ISO в хранилище)
│   ├── scheduler.py        # Проверяет просрочку (overdue)
│   ├── autostart.py        # Прописывает программу в автозагрузку
│   └── tray.py             # Иконка в системном трее (pystray)
│
└── ui/                     # Интерфейс (окна, кнопки, стикеры)
    ├── __init__.py
    ├── main_window.py      # Окно для создания/редактирования напоминалки
    ├── manager_window.py   # Редактор напоминаний (картридж-менеджер)
    ├── settings_window.py  # Окно настроек (картридж)
    └── sticker_window.py   # Всплывающее окно-стикер (без рамок)