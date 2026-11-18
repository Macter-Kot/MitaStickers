import calendar
import json
import os
import sys
from datetime import datetime, timedelta

try:
    from dateutil.relativedelta import relativedelta
except ImportError:  # pragma: no cover
    relativedelta = None

APP_NAME = "MitaStickers"

# Собранный PyInstaller EXE распаковывает ресурсы во временную папку sys._MEIPASS
FROZEN = bool(getattr(sys, "frozen", False))

# Корень исходников/проекта (в EXE это временная папка _MEIPASS)
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Папка только для чтения с ресурсами (assets, locales).
# В EXE — _MEIPASS, в режиме разработки — корень проекта.
RESOURCE_DIR = getattr(sys, "_MEIPASS", None) or PROJECT_DIR

# BASE_DIR оставлен для совместимости: это корень ресурсов/проекта.
BASE_DIR = PROJECT_DIR

# Папка пользовательских данных (для записи):
#   EXE        -> %LOCALAPPDATA%\MitaStickers
#   разработка -> <корень проекта>
if FROZEN:
    USER_DIR = os.path.join(
        os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), APP_NAME
    )
    DATA_DIR = USER_DIR
else:
    USER_DIR = PROJECT_DIR
    DATA_DIR = os.path.join(PROJECT_DIR, "data")

IMAGES_DIR = os.path.join(DATA_DIR, "images")
DATA_FILE = os.path.join(DATA_DIR, "stickers.json")

DATETIME_FORMAT = "%Y-%m-%d %H:%M"

STATUS_PENDING = "pending"
STATUS_SHOWN = "shown"
STATUS_COMPLETED = "completed"

REPEAT_NONE = "none"
REPEAT_DAILY = "daily"
REPEAT_WEEKLY = "weekly"
REPEAT_MONTHLY = "monthly"
REPEAT_YEARLY = "yearly"
REPEAT_CUSTOM = "custom"

REPEAT_VALUES = (
    REPEAT_NONE,
    REPEAT_DAILY,
    REPEAT_WEEKLY,
    REPEAT_MONTHLY,
    REPEAT_YEARLY,
    REPEAT_CUSTOM,
)


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)


def load_stickers():
    ensure_dirs()
    if not os.path.exists(DATA_FILE):
        save_stickers([])
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError, ValueError):
        return []

    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("stickers"), list):
        return [item for item in data["stickers"] if isinstance(item, dict)]
    return []


def save_stickers(stickers):
    ensure_dirs()
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(stickers, file, ensure_ascii=False, indent=2)


def next_id(stickers=None):
    if stickers is None:
        stickers = load_stickers()
    return max((int(item.get("id", 0)) for item in stickers), default=0) + 1


def add_sticker(text, image=None, datetime_str="", status=STATUS_PENDING, style="Желтый",
                repeat=REPEAT_NONE, repeat_days=0):
    stickers = load_stickers()
    sticker = {
        "id": next_id(stickers),
        "text": text,
        "image": image,
        "datetime": datetime_str,
        "status": status,
        "style": style,
        "repeat": repeat,
        "repeat_days": int(repeat_days or 0),
    }
    stickers.append(sticker)
    save_stickers(stickers)
    return sticker


def update_sticker(sticker_id, **fields):
    stickers = load_stickers()
    for sticker in stickers:
        if sticker.get("id") == sticker_id:
            sticker.update(fields)
            break
    save_stickers(stickers)
    return stickers


def get_sticker(sticker_id):
    for sticker in load_stickers():
        if sticker.get("id") == sticker_id:
            return sticker
    return None


def delete_sticker(sticker_id):
    stickers = load_stickers()

    # Сначала находим стикер и удаляем его картинку (если она есть)
    for sticker in stickers:
        if sticker.get("id") == sticker_id:
            img_path = sticker.get("image")
            if img_path and os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except OSError:
                    pass
            break  # Нашли и удалили картинку

    remaining = [item for item in stickers if item.get("id") != sticker_id]
    save_stickers(remaining)
    return remaining


def _add_months(moment, months):
    """Добавляет месяцы с корректировкой конца месяца (запасной вариант без dateutil)."""
    total = moment.month - 1 + months
    year = moment.year + total // 12
    month = total % 12 + 1
    day = min(moment.day, calendar.monthrange(year, month)[1])
    return moment.replace(year=year, month=month, day=day)


def advance_datetime(moment, repeat, repeat_days=0):
    """Возвращает следующую дату по типу повтора (или None, если повтор выключен)."""
    if repeat == REPEAT_DAILY:
        return moment + timedelta(days=1)
    if repeat == REPEAT_WEEKLY:
        return moment + timedelta(weeks=1)
    if repeat == REPEAT_MONTHLY:
        if relativedelta is not None:
            return moment + relativedelta(months=1)
        return _add_months(moment, 1)
    if repeat == REPEAT_YEARLY:
        if relativedelta is not None:
            return moment + relativedelta(years=1)
        return _add_months(moment, 12)
    if repeat == REPEAT_CUSTOM:
        days = max(1, int(repeat_days or 1))
        return moment + timedelta(days=days)
    return None


def complete_sticker(sticker_id):
    """Отмечает стикер выполненным.

    Для разового (repeat == "none") просто ставит статус "completed".
    Для повторяющегося оставляет "pending" и переносит дату на следующий интервал
    (при необходимости «догоняя» до ближайшего будущего момента).
    """
    stickers = load_stickers()
    for sticker in stickers:
        if sticker.get("id") != sticker_id:
            continue

        repeat = sticker.get("repeat", REPEAT_NONE)
        next_moment = None

        if repeat and repeat != REPEAT_NONE:
            try:
                base = datetime.strptime(sticker.get("datetime", ""), DATETIME_FORMAT)
            except (ValueError, TypeError):
                base = None

            if base is not None:
                next_moment = advance_datetime(base, repeat, sticker.get("repeat_days", 0))
                now = datetime.now()
                guard = 0
                while next_moment is not None and next_moment <= now and guard < 10000:
                    next_moment = advance_datetime(next_moment, repeat, sticker.get("repeat_days", 0))
                    guard += 1

        if next_moment is not None:
            sticker["datetime"] = next_moment.strftime(DATETIME_FORMAT)
            sticker["status"] = STATUS_PENDING
        else:
            sticker["status"] = STATUS_COMPLETED
        break

    save_stickers(stickers)
    return stickers
