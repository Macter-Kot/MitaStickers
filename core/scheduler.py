from datetime import datetime, timedelta

from core import storage
from ui.sticker_window import StickerWindow

CHECK_INTERVAL_MS = 30000
OVERDUE_THRESHOLD = timedelta(minutes=1)


def check_tasks(root):
    try:
        now = datetime.now()
        stickers = storage.load_stickers()

        changed = False
        for sticker in stickers:
            if sticker.get("status") != storage.STATUS_PENDING:
                continue

            try:
                due = datetime.strptime(sticker.get("datetime", ""), storage.DATETIME_FORMAT)
            except (ValueError, TypeError):
                continue

            if due > now:
                continue

            is_overdue = (now - due) > OVERDUE_THRESHOLD

            StickerWindow(
                root,
                text=sticker.get("text", ""),
                image_path=sticker.get("image"),
                is_overdue=is_overdue,
                sticker_id=sticker.get("id"),
                style=sticker.get("style", "Желтый"),
                datetime_str=sticker.get("datetime"),
                repeat=sticker.get("repeat", "none"),
            )

            sticker["status"] = storage.STATUS_SHOWN
            changed = True

        if changed:
            storage.save_stickers(stickers)
    except Exception:
        pass
    finally:
        root.after(CHECK_INTERVAL_MS, check_tasks, root)
