import os

try:
    import pystray
    from PIL import Image
except ImportError:  # pragma: no cover
    pystray = None
    Image = None

from core import storage

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ICON_PATH = os.path.join(BASE_DIR, "assets", "default_icon.ico")

_icon = None
_root = None


def _load_icon():
    if Image is None:
        return None
    if os.path.exists(ICON_PATH):
        try:
            return Image.open(ICON_PATH)
        except OSError:
            pass
    return Image.new("RGB", (64, 64), "#FBC02D")


def _on_create(icon, item):
    if _root is None:
        return
    from ui.main_window import open_main_window

    _root.after_idle(lambda: open_main_window(_root))


def _on_exit(icon, item):
    if _root is not None:
        _root.after_idle(_root.quit)
    icon.stop()


def start_tray(root):
    global _icon, _root
    _root = root

    if pystray is None or Image is None:
        return

    menu = pystray.Menu(
        pystray.MenuItem("Создать стикер", _on_create, default=True),
        pystray.MenuItem("Выход", _on_exit),
    )
    _icon = pystray.Icon("MitaStickers", _load_icon(), "MitaStickers", menu)
    _icon.run()
