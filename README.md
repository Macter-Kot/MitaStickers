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
├── requirements.txt        # Список библиотек (Pillow)
├── README.md               # Краткое описание проекта
│
├── data/                   # Папка для хранения данных
│   └── stickers.json       # Файл, где лежат напоминалки
│
├── assets/                 # Ассеты
│   └── default_icon.ico    # Иконки программы
│
├── core/                   # Логика
│   ├── __init__.py
│   ├── storage.py          # Чтение и запись JSON-файла
│   ├── scheduler.py        # Проверяет просрочку (overdue)
│   ├── autostart.py        # Прописывает программу в автозагрузку
│   └── tray.py             # Иконка в системном трее (pystray)
│
└── ui/                     # Интерфейс (окна, кнопки, стикеры)
    ├── __init__.py
    ├── main_window.py      # Окно для создания/редактирования напоминалки
    ├── manager_window.py   # Редактор напоминаний (картридж-менеджер)
    └── sticker_window.py   # Всплывающее окно-стикер (без рамок)