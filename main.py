import os
import sys
import threading
import tkinter as tk

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core import storage, tray
from core.scheduler import check_tasks
from ui.sticker_window import get_resource_path

ICON_PATH = get_resource_path("assets/icon.ico")


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

    tray_thread = threading.Thread(
        target=tray.start_tray, args=(root,), daemon=True
    )
    tray_thread.start()

    root.after(1000, check_tasks, root)
    root.mainloop()


if __name__ == "__main__":
    main()
