import os
import sys

APP_NAME = "MitaStickers"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_command():
    if getattr(sys, "frozen", False):
        return '"{}"'.format(sys.executable)
    script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
    return '"{}" "{}"'.format(sys.executable, script)


def _open_key(access):
    import winreg

    return winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, access)


def add_to_startup():
    try:
        import winreg
    except ImportError:
        return False

    try:
        with _open_key(winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_command())
        return True
    except OSError:
        return False


def remove_from_startup():
    try:
        import winreg
    except ImportError:
        return False

    try:
        with _open_key(winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        return True
    except OSError:
        return False


def is_in_startup():
    try:
        import winreg
    except ImportError:
        return False

    try:
        with _open_key(winreg.KEY_QUERY_VALUE) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except OSError:
        return False
