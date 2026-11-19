# Структура проекта MitaStickers

MitaStickers/
│
├── main.py                 # Главный файл запуска
├── requirements.txt        # Список библиотек (Pillow, pystray, python-dateutil)
├── README.md               # Описание проекта
│
├── data/                   # Папка для хранения данных (создается автоматически)
│   ├── stickers.json       # Файл с напоминалками
│   └── settings.json       # Настройки приложения
│
├── assets/                 # Графические ресурсы
│   ├── icon.ico            # Иконка окна/панели задач
│   ├── default_icon.ico    # Иконка системного трея
│   ├── logo.png            # Логотип в шапке окна
│   ├── cartridge.png       # Рамка (картридж) для окон
│   └── default_placeholder.png  # Заглушка для картинок
│
├── locales/                # Файлы локализации
│   ├── ru.json             # Русский язык
│   └── en.json             # Английский язык
│
├── core/                   # Логика приложения
│   ├── storage.py          # Чтение/запись JSON, сохранение картинок
│   ├── settings.py         # Работа с настройками
│   ├── i18n.py             # Система переводов (RU/EN)
│   ├── theme.py            # Темы оформления (pink / purple)
│   ├── date_utils.py       # Форматы даты и времени
│   ├── scheduler.py        # Проверка просроченных напоминаний
│   ├── autostart.py        # Добавление в автозагрузку Windows
│   └── tray.py             # Иконка в системном трее
│
└── ui/                     # Пользовательский интерфейс (Tkinter)
    ├── main_window.py      # Окно создания/редактирования
    ├── manager_window.py   # Редактор (картридж)
    ├── settings_window.py  # Окно настроек (картридж)
    └── sticker_window.py   # Всплывающее окно-стикер