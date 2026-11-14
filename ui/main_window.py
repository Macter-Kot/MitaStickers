import os
import shutil
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover
    Image = None
    ImageTk = None

from core import storage
from ui.sticker_window import get_resource_path
from ui.manager_window import Tooltip

APP_ICON = get_resource_path("assets/icon.ico")
LOGO = "assets/logo.png"

# --- ПАЛИТРА (в стиле картриджей) ---
FONT = "Segoe UI"
WIN_BG = "#FADDE1"
HEADER_BG = "#F6C6CF"
BORDER = "#E8A3B4"
PANEL_BG = "#FFF8E1"
TEXT = "#3E2723"
MUTED = "#8D6E63"
PRIMARY = "#F4A7B9"
PRIMARY_DARK = "#EC8FA6"
GREEN = "#66BB6A"
GREEN_DARK = "#43A047"
RED = "#EF5350"
RED_DARK = "#C62828"

REPEAT_LABELS = [
    ("Нет", storage.REPEAT_NONE),
    ("Каждый день", storage.REPEAT_DAILY),
    ("Каждую неделю", storage.REPEAT_WEEKLY),
    ("Каждый месяц", storage.REPEAT_MONTHLY),
    ("Каждый год", storage.REPEAT_YEARLY),
    ("Каждые X дней", storage.REPEAT_CUSTOM),
]
LABEL_TO_REPEAT = {label: key for label, key in REPEAT_LABELS}
REPEAT_TO_LABEL = {key: label for label, key in REPEAT_LABELS}

_instance = None


def open_main_window(root, sticker=None, on_saved=None):
    """Открывает окно создания/редактирования.

    sticker=None        -> создание нового стикера (окно переиспользуется);
    sticker=<dict>      -> редактирование, всегда новое окно;
    on_saved=callable   -> вызывается после успешного сохранения.
    """
    global _instance

    if sticker is None and _instance is not None and _instance.winfo_exists():
        _instance.deiconify()
        _instance.lift()
        _instance.focus_force()
        return _instance

    window = MainWindow(root, sticker=sticker, on_saved=on_saved)
    if sticker is None:
        _instance = window
    return window


class MainWindow(tk.Toplevel):
    def __init__(self, root, sticker=None, on_saved=None):
        super().__init__(root)

        self.root = root
        self.sticker = sticker or None
        self.editing = sticker is not None
        self.on_saved = on_saved
        self.selected_image = None
        self._logo_photo = None
        self._drag_x = 0
        self._drag_y = 0

        self.title("MitaStickers — Редактирование" if self.editing else "MitaStickers — Новый стикер")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.configure(bg=BORDER)
        self._apply_icon()

        self.image_var = tk.StringVar()
        self.style_var = tk.StringVar(value="Желтый")
        self.repeat_var = tk.StringVar(value=REPEAT_TO_LABEL[storage.REPEAT_NONE])
        self.repeat_days_var = tk.IntVar(value=2)

        self._prefill()
        self._build()
        self._center()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda event: self.destroy())
        self.bind("<Map>", self._on_map)
        self.focus_force()

    def _apply_icon(self):
        try:
            if os.path.exists(APP_ICON):
                self.iconbitmap(APP_ICON)
        except tk.TclError:
            pass

    def _prefill(self):
        if self.editing:
            self.style_var.set(self.sticker.get("style", "Желтый"))
            image = self.sticker.get("image")
            self.image_var.set(os.path.basename(image) if image else "Картинка не выбрана")
            repeat = self.sticker.get("repeat", storage.REPEAT_NONE)
            self.repeat_var.set(REPEAT_TO_LABEL.get(repeat, REPEAT_TO_LABEL[storage.REPEAT_NONE]))
            self.repeat_days_var.set(int(self.sticker.get("repeat_days", 2) or 2))
        else:
            self.image_var.set("Картинка не выбрана")

    # ---------- сборка интерфейса ----------
    def _build(self):
        container = tk.Frame(self, bg=WIN_BG)
        container.pack(fill="both", expand=True, padx=1, pady=1)

        self._build_header(container)
        self._build_body(container)

    def _build_header(self, parent):
        header = tk.Frame(parent, bg=HEADER_BG)
        header.pack(fill="x")

        self._logo_photo = self._load_logo(34)
        if self._logo_photo is not None:
            logo = tk.Label(header, image=self._logo_photo, bg=HEADER_BG)
        else:
            logo = tk.Label(header, text="MitaStickers", bg=HEADER_BG, fg=TEXT, font=(FONT, 12, "bold"))
        logo.pack(side="left", padx=(12, 6), pady=7)

        subtitle = tk.Label(
            header,
            text="Редактирование" if self.editing else "Новый стикер",
            bg=HEADER_BG, fg=MUTED, font=(FONT, 9, "italic"),
        )
        subtitle.pack(side="left", pady=(16, 0))

        close_btn = self._header_button(header, "\u2716", self.destroy, RED, RED_DARK)
        close_btn.pack(side="right", padx=(0, 8), pady=6)
        min_btn = self._header_button(header, "\u2014", self._minimize, PRIMARY, PRIMARY_DARK)
        min_btn.pack(side="right", pady=6)

        for widget in (header, logo, subtitle):
            self._make_draggable(widget)

    def _build_body(self, parent):
        body = tk.Frame(parent, bg=WIN_BG, padx=16, pady=14)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_columnconfigure(2, weight=1)

        # Заголовок + кнопка настроек
        tk.Label(body, text="Текст напоминания:", bg=WIN_BG, fg=TEXT, font=(FONT, 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        self.btn_settings = tk.Button(
            body, text="\u2699", command=self._open_settings, bg=PRIMARY, fg="white",
            activebackground=PRIMARY_DARK, activeforeground="white", relief="flat", bd=0,
            font=(FONT, 11, "bold"), width=3, cursor="hand2",
        )
        self.btn_settings.grid(row=0, column=2, sticky="e")
        self._settings_tooltip = Tooltip(self.btn_settings, "Настройки")

        self.text_widget = tk.Text(
            body, width=44, height=5, wrap="word", font=(FONT, 10),
            bg=PANEL_BG, fg=TEXT, relief="flat", insertbackground=TEXT,
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY,
            padx=6, pady=4,
        )
        self.text_widget.grid(row=1, column=0, columnspan=3, sticky="we", pady=(4, 12))
        if self.editing:
            self.text_widget.insert("1.0", self.sticker.get("text", ""))

        when = datetime.now() + timedelta(minutes=5)
        if self.editing:
            try:
                when = datetime.strptime(self.sticker.get("datetime", ""), storage.DATETIME_FORMAT)
            except (ValueError, TypeError):
                pass

        tk.Label(body, text="Дата:", bg=WIN_BG, fg=TEXT, font=(FONT, 10)).grid(row=2, column=0, sticky="w")
        self.date_entry = self._entry(body, width=16)
        self.date_entry.insert(0, when.strftime("%Y-%m-%d"))
        self.date_entry.grid(row=3, column=0, sticky="w", pady=(2, 0))

        tk.Label(body, text="Время:", bg=WIN_BG, fg=TEXT, font=(FONT, 10)).grid(
            row=2, column=1, sticky="w", padx=(10, 0)
        )
        self.time_entry = self._entry(body, width=10)
        self.time_entry.insert(0, when.strftime("%H:%M"))
        self.time_entry.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=(2, 0))

        tk.Label(body, text="ГГГГ-ММ-ДД и ЧЧ:ММ", bg=WIN_BG, fg=MUTED, font=(FONT, 8)).grid(
            row=3, column=2, sticky="w", padx=(10, 0), pady=(2, 0)
        )

        tk.Label(body, text="Картинка (необязательно):", bg=WIN_BG, fg=TEXT, font=(FONT, 10, "bold")).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(12, 0)
        )
        self._button(body, "Выбрать файл...", self._choose_image, PRIMARY, PRIMARY_DARK).grid(
            row=5, column=0, sticky="w", pady=(6, 0)
        )
        tk.Label(body, textvariable=self.image_var, bg=WIN_BG, fg=MUTED, font=(FONT, 8)).grid(
            row=5, column=1, columnspan=2, sticky="w", padx=(10, 0), pady=(6, 0)
        )

        # --- Стиль ---
        tk.Label(body, text="Стиль стикера:", bg=WIN_BG, fg=TEXT, font=(FONT, 10, "bold")).grid(
            row=6, column=0, sticky="w", pady=(12, 0)
        )
        self.style_menu = self._option_menu(body, self.style_var, ["Желтый", "Розовый", "Фиолетовый"])
        self.style_menu.grid(row=7, column=0, sticky="w", pady=(2, 0))

        # --- Повтор ---
        tk.Label(body, text="Повтор:", bg=WIN_BG, fg=TEXT, font=(FONT, 10, "bold")).grid(
            row=6, column=1, sticky="w", padx=(10, 0), pady=(12, 0)
        )
        self.repeat_menu = self._option_menu(body, self.repeat_var, [label for label, _ in REPEAT_LABELS])
        self.repeat_menu.grid(row=7, column=1, sticky="w", padx=(10, 0), pady=(2, 0))
        self.repeat_var.trace_add("write", lambda *a: self._update_repeat_state())

        self.repeat_days_spin = tk.Spinbox(
            body, from_=2, to=999, width=5, textvariable=self.repeat_days_var, justify="center",
            font=(FONT, 10), bg=PANEL_BG, fg=TEXT, relief="flat", bd=0,
            buttonbackground=PRIMARY, insertbackground=TEXT, disabledbackground="#EFE3E6",
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY,
        )
        self.repeat_days_spin.grid(row=7, column=2, sticky="w", padx=(10, 0), pady=(2, 0))
        self._update_repeat_state()

        buttons = tk.Frame(body, bg=WIN_BG)
        buttons.grid(row=8, column=0, columnspan=3, sticky="we", pady=(16, 0))
        self._button(buttons, "Редактор", self._open_manager, PRIMARY, PRIMARY_DARK).pack(side="left")

        right = tk.Frame(buttons, bg=WIN_BG)
        right.pack(side="right")
        self._button(right, "Отмена", self.destroy, RED, RED_DARK).pack(side="left", padx=(0, 8))
        self._button(
            right, "Сохранить" if self.editing else "Создать", self._save, GREEN, GREEN_DARK
        ).pack(side="left")

    # ---------- фабрики виджетов ----------
    def _header_button(self, parent, text, command, bg, hover):
        button = tk.Button(
            parent, text=text, command=command, bg=HEADER_BG, fg=TEXT, activebackground=hover,
            activeforeground="white", relief="flat", bd=0, font=(FONT, 10, "bold"),
            width=3, cursor="hand2",
        )
        button.bind("<Enter>", lambda e: button.configure(bg=hover, fg="white"))
        button.bind("<Leave>", lambda e: button.configure(bg=HEADER_BG, fg=TEXT))
        return button

    def _button(self, parent, text, command, bg, hover, fg="white"):
        button = tk.Button(
            parent, text=text, command=command, bg=bg, fg=fg, activebackground=hover,
            activeforeground=fg, relief="flat", bd=0, font=(FONT, 10, "bold"),
            padx=14, pady=6, cursor="hand2",
        )
        button.bind("<Enter>", lambda e: button.configure(bg=hover))
        button.bind("<Leave>", lambda e: button.configure(bg=bg))
        return button

    def _entry(self, parent, width=16):
        return tk.Entry(
            parent, width=width, font=(FONT, 10), bg=PANEL_BG, fg=TEXT,
            relief="flat", bd=0, insertbackground=TEXT,
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY,
        )

    def _option_menu(self, parent, variable, values):
        menu = tk.OptionMenu(parent, variable, *values)
        menu.configure(
            bg=PANEL_BG, fg=TEXT, activebackground=PRIMARY, activeforeground="white",
            relief="flat", bd=0, highlightthickness=1, highlightbackground=BORDER,
            font=(FONT, 10), padx=8, pady=4, cursor="hand2", anchor="w", width=15,
        )
        menu["menu"].configure(
            bg=PANEL_BG, fg=TEXT, activebackground=PRIMARY, activeforeground="white",
            font=(FONT, 10), bd=0,
        )
        return menu

    def _load_logo(self, height):
        if Image is None or ImageTk is None:
            return None
        path = get_resource_path(LOGO)
        if not os.path.exists(path):
            return None
        try:
            image = Image.open(path).convert("RGBA")
            width = max(1, round(image.width * height / image.height))
            resample = getattr(Image, "LANCZOS", getattr(Image, "BICUBIC", 3))
            image = image.resize((width, height), resample)
            return ImageTk.PhotoImage(image)
        except (OSError, ValueError):
            return None

    def _center(self):
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 3
        self.geometry("{}x{}+{}+{}".format(width, height, x, y))

    # ---------- перетаскивание / окно ----------
    def _make_draggable(self, widget):
        widget.bind("<ButtonPress-1>", self._start_move)
        widget.bind("<B1-Motion>", self._on_move)

    def _start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_move(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry("+{}+{}".format(x, y))

    def _minimize(self):
        # Временно возвращаем рамку, чтобы окно могло свернуться в панель задач
        try:
            self.overrideredirect(False)
            self.iconify()
        except tk.TclError:
            pass

    def _on_map(self, event=None):
        try:
            if self.state() == "normal" and not self.overrideredirect():
                self.overrideredirect(True)
        except tk.TclError:
            pass

    # ---------- прочее ----------
    def _open_manager(self):
        from ui.manager_window import open_manager_window

        open_manager_window(self.root)

    def _open_settings(self):
        from ui.settings_window import open_settings_window

        open_settings_window(self.root)

    def _update_repeat_state(self):
        is_custom = self.repeat_var.get() == REPEAT_TO_LABEL[storage.REPEAT_CUSTOM]
        self.repeat_days_spin.configure(state="normal" if is_custom else "disabled")

    def _choose_image(self):
        path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("Все файлы", "*.*"),
            ],
        )
        if path:
            self.selected_image = path
            self.image_var.set(os.path.basename(path))

    def _copy_image(self, path):
        ext = os.path.splitext(path)[1]
        name = "img_{}{}".format(datetime.now().strftime("%Y%m%d%H%M%S%f"), ext)
        storage.ensure_dirs()
        destination = os.path.join(storage.IMAGES_DIR, name)
        shutil.copy2(path, destination)
        return destination

    def _save(self):
        text = self.text_widget.get("1.0", "end").strip()
        if not text:
            messagebox.showerror("Ошибка", "Введите текст напоминания.", parent=self)
            return

        raw = "{} {}".format(self.date_entry.get().strip(), self.time_entry.get().strip())
        try:
            when = datetime.strptime(raw, storage.DATETIME_FORMAT)
        except ValueError:
            messagebox.showerror(
                "Ошибка",
                "Неверный формат даты или времени.\nИспользуйте ГГГГ-ММ-ДД и ЧЧ:ММ.",
                parent=self,
            )
            return

        image = self.sticker.get("image") if self.editing else None
        if self.selected_image:
            try:
                image = self._copy_image(self.selected_image)
            except OSError as error:
                messagebox.showerror("Ошибка", "Не удалось скопировать картинку:\n{}".format(error), parent=self)
                return

        repeat = LABEL_TO_REPEAT.get(self.repeat_var.get(), storage.REPEAT_NONE)
        if repeat == storage.REPEAT_CUSTOM:
            raw_days = self.repeat_days_spin.get().strip()
            try:
                repeat_days = int(raw_days)
            except ValueError:
                messagebox.showerror("Ошибка", "Введите целое число от 2 до 999.", parent=self)
                return

            if repeat_days == 1:
                messagebox.showwarning("Внимание", "Выберите — Каждый день.", parent=self)
                return

            if repeat_days < 2 or repeat_days > 999:
                messagebox.showerror("Ошибка", "Введите целое число от 2 до 999.", parent=self)
                return
        else:
            repeat_days = 2

        if self.editing:
            storage.update_sticker(
                self.sticker.get("id"),
                text=text,
                image=image,
                datetime=when.strftime(storage.DATETIME_FORMAT),
                style=self.style_var.get(),
                repeat=repeat,
                repeat_days=repeat_days,
                status=storage.STATUS_PENDING,
            )
        else:
            storage.add_sticker(
                text=text,
                image=image,
                datetime_str=when.strftime(storage.DATETIME_FORMAT),
                status=storage.STATUS_PENDING,
                style=self.style_var.get(),
                repeat=repeat,
                repeat_days=repeat_days,
            )

        if callable(self.on_saved):
            try:
                self.on_saved()
            except Exception:
                pass

        messagebox.showinfo("Готово", "Изменения сохранены." if self.editing else "Напоминание создано.", parent=self)
        self.destroy()

    def destroy(self):
        global _instance
        if _instance is self:
            _instance = None
        super().destroy()
