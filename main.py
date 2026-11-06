import os
import sys
import threading
import tkinter as tk

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core import storage, tray
from core.scheduler import check_tasks

ICON_PATH = os.path.join(BASE_DIR, "assets", "default_icon.ico")


def main():
    storage.load_stickers()

    root = tk.Tk()
    root.title("MitaStickers")
    root.withdraw()

    try:
        if os.path.exists(ICON_PATH):
            root.iconbitmap(ICON_PATH)
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
