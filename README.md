# MitaStickers 0.1

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
│   ├── init.py
│   ├── storage.py          # Чтение и запись JSON-файла
│   ├── scheduler.py        # Проверяет просрочку (overdue)
│   ├── autostart.py        # Прописывает программу в автозагрузку
│   └── tray.py             # Иконка в системном трее (pystray)
│
└── ui/                     # Интерфейс (окна, кнопки, стикеры)
├── init.py
├── main_window.py      # Окно для создания новой напоминалки
└── sticker_window.py   # Всплывающее окно-стикер (без рамок)