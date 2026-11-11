import json
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
DATA_FILE = os.path.join(DATA_DIR, "stickers.json")

DATETIME_FORMAT = "%Y-%m-%d %H:%M"

STATUS_PENDING = "pending"
STATUS_SHOWN = "shown"
STATUS_COMPLETED = "completed"


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


def add_sticker(text, image=None, datetime_str="", status=STATUS_PENDING, style="Желтый"):
    stickers = load_stickers()
    sticker = {
        "id": next_id(stickers),
        "text": text,
        "image": image,
        "datetime": datetime_str,
        "status": status,
        "style": style,
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
