import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core import autostart, settings, storage, tray
from core.scheduler import check_tasks
from ui.sticker_window import get_resource_path

ICON_PATH = get_resource_path("assets/icon.ico")


def ask_autostart_on_first_run(root):
    """Один раз предлагает добавить приложение в автозагрузку Windows."""
    current = settings.load_settings()
    if current.get("first_run_prompted"):
        return

    try:
        already = autostart.is_in_startup()
    except Exception:
        already = False

    if not already:
        try:
            answer = messagebox.askyesno(
                "MitaStickers",
                "Добавить MitaStickers в автозагрузку Windows, чтобы напоминания "
                "работали после перезагрузки компьютера?",
                parent=root,
            )
        except Exception:
            answer = False
        if answer:
            try:
                autostart.add_to_startup()
            except Exception:
                pass

    current["first_run_prompted"] = True
    current["autostart"] = bool(autostart.is_in_startup())
    settings.save_settings(current)


def main():
    storage.load_stickers()

    root = tk.Tk()
    root.title("MitaStickers")
    root.withdraw()

    try:
        if os.path.exists(ICON_PATH):
            # default=... задаёт иконку по умолчанию для всех окон (иконка на панели задач)
            root.iconbitmap(default=ICON_PATH)
    except tk.TclError:
        pass

    ask_autostart_on_first_run(root)

    tray_thread = threading.Thread(
        target=tray.start_tray, args=(root,), daemon=True
    )
    tray_thread.start()

    root.after(1000, check_tasks, root)
    root.mainloop()


if __name__ == "__main__":
    main()
