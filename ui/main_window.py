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

from core import date_utils, storage
from core.i18n import _
from core.theme import get_theme
from ui.sticker_window import get_resource_path
from ui.manager_window import Tooltip

APP_ICON = get_resource_path("assets/icon.ico")
LOGO = "assets/logo.png"

FONT = "Segoe UI"

# Канонические значения стилей (они же хранятся в JSON) и их исходные подписи
STYLE_VALUES = ["Желтый", "Розовый", "Фиолетовый"]

# Пары (канонический код повтора, исходная русская подпись)
REPEAT_SPEC = [
    (storage.REPEAT_NONE, "Нет"),
    (storage.REPEAT_DAILY, "Каждый день"),
    (storage.REPEAT_WEEKLY, "Каждую неделю"),
    (storage.REPEAT_MONTHLY, "Каждый месяц"),
    (storage.REPEAT_YEARLY, "Каждый год"),
    (storage.REPEAT_CUSTOM, "Каждые X дней"),
]

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

        # Делаем прозрачным - для отрисовки
        self.attributes("-alpha", 0.0)

        self.root = root
        self.theme = get_theme()
        self.sticker = sticker or None
        self.editing = sticker is not None
        self.on_saved = on_saved
        self.selected_image = None
        self._logo_photo = None
        self._drag_x = 0
        self._drag_y = 0

        self.title("MitaStickers — " + (_("Редактирование") if self.editing else _("Новый стикер")))
        self.resizable(False, False)
        # self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.configure(bg=self.theme["border"])
        self._apply_icon()

        self.image_var = tk.StringVar()
        self.style_var = tk.StringVar()
        self.repeat_var = tk.StringVar()
        self.repeat_days_var = tk.IntVar(value=2)

        self._build_mappings()
        self._build()

        # Вызываем центрирование с задержкой 50 мс
        self.after(50, self._center)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda event: self.destroy())
        self.bind("<Map>", self._on_map)
        self.focus_force()

    def _build_mappings(self):
        # Стили: подпись <-> канонический ключ
        self._style_labels = [_("Желтый"), _("Розовый"), _("Фиолетовый")]
        self._style_value_by_label = dict(zip(self._style_labels, STYLE_VALUES))
        self._style_label_by_value = dict(zip(STYLE_VALUES, self._style_labels))

        # Повторы: подпись <-> канонический код
        self._repeat_labels = []
        self._repeat_value_by_label = {}
        self._repeat_label_by_value = {}
        for value, source in REPEAT_SPEC:
            label = _(source)
            self._repeat_labels.append(label)
            self._repeat_value_by_label[label] = value
            self._repeat_label_by_value[value] = label
        self._repeat_custom_label = self._repeat_label_by_value[storage.REPEAT_CUSTOM]

        # Начальные значения
        if self.editing:
            initial_style = self.sticker.get("style", STYLE_VALUES[0])
            initial_repeat = self.sticker.get("repeat", storage.REPEAT_NONE)
            self.repeat_days_var.set(int(self.sticker.get("repeat_days", 2) or 2))
            image = self.sticker.get("image")
            self.image_var.set(os.path.basename(image) if image else _("Картинка не выбрана"))
        else:
            initial_style = STYLE_VALUES[0]
            initial_repeat = storage.REPEAT_NONE
            self.image_var.set(_("Картинка не выбрана"))

        self.style_var.set(self._style_label_by_value.get(initial_style, self._style_labels[0]))
        self.repeat_var.set(
            self._repeat_label_by_value.get(initial_repeat, self._repeat_label_by_value[storage.REPEAT_NONE])
        )

    def _apply_icon(self):
        try:
            if os.path.exists(APP_ICON):
                self.iconbitmap(APP_ICON)
        except tk.TclError:
            pass

    # ---------- сборка интерфейса ----------
    def _build(self):
        container = tk.Frame(self, bg=self.theme["bg_main"])
        container.pack(fill="both", expand=True, padx=1, pady=1)

        self._build_header(container)
        self._build_body(container)

    def _build_header(self, parent):
        t = self.theme
        header = tk.Frame(parent, bg=t["header_bg"])
        header.pack(fill="x")

        self._logo_photo = self._load_logo(34)
        if self._logo_photo is not None:
            logo = tk.Label(header, image=self._logo_photo, bg=t["header_bg"])
        else:
            logo = tk.Label(header, text="MitaStickers", bg=t["header_bg"], fg=t["text"], font=(FONT, 12, "bold"))
        logo.pack(side="left", padx=(12, 6), pady=7)

        subtitle = tk.Label(
            header,
            text=_("Редактирование") if self.editing else _("Новый стикер"),
            bg=t["header_bg"], fg=t["muted"], font=(FONT, 9, "italic"),
        )
        subtitle.pack(side="left", pady=(16, 0))

        close_btn = self._header_button(header, "\u2716", self.destroy, t["red_dark"])
        close_btn.pack(side="right", padx=(0, 8), pady=6)
        min_btn = self._header_button(header, "\u2014", self._minimize, t["primary_dark"])
        min_btn.pack(side="right", pady=6)

        for widget in (header, logo, subtitle):
            self._make_draggable(widget)

    def _build_body(self, parent):
        t = self.theme
        body = tk.Frame(parent, bg=t["bg_main"], padx=16, pady=14)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_columnconfigure(2, weight=1)

        tk.Label(body, text=_("Текст напоминания:"), bg=t["bg_main"], fg=t["text"], font=(FONT, 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        self.btn_settings = tk.Button(
            body, text="\u2699", command=self._open_settings, bg=t["primary"], fg="white",
            activebackground=t["primary_dark"], activeforeground="white", relief="flat", bd=0,
            font=(FONT, 11, "bold"), width=3, cursor="hand2",
        )
        self.btn_settings.grid(row=0, column=2, sticky="e")
        self._settings_tooltip = Tooltip(self.btn_settings, _("Настройки"))

        self.text_widget = tk.Text(
            body, width=44, height=5, wrap="word", font=(FONT, 10),
            bg=t["panel_bg"], fg=t["text"], relief="flat", insertbackground=t["text"],
            highlightthickness=1, highlightbackground=t["border"], highlightcolor=t["primary"],
            padx=6, pady=4,
        )
        self.text_widget.grid(row=1, column=0, columnspan=3, sticky="we", pady=(4, 12))
        if self.editing:
            self.text_widget.insert("1.0", self.sticker.get("text", ""))

        when = datetime.now() + timedelta(minutes=5)
        if self.editing:
            parsed = date_utils.parse_iso(self.sticker.get("datetime", ""))
            if parsed is not None:
                when = parsed

        tk.Label(body, text=_("Дата:"), bg=t["bg_main"], fg=t["text"], font=(FONT, 10)).grid(row=2, column=0, sticky="w")
        self.date_entry = self._entry(body, width=16)
        self.date_entry.insert(0, date_utils.format_date(when))
        self.date_entry.grid(row=3, column=0, sticky="w", pady=(2, 0))

        tk.Label(body, text=_("Время:"), bg=t["bg_main"], fg=t["text"], font=(FONT, 10)).grid(
            row=2, column=1, sticky="w", padx=(10, 0)
        )
        self.time_entry = self._entry(body, width=12)
        self.time_entry.insert(0, date_utils.format_time(when))
        self.time_entry.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=(2, 0))

        tk.Label(body, text=date_utils.input_hint(), bg=t["bg_main"], fg=t["muted"], font=(FONT, 8)).grid(
            row=3, column=2, sticky="w", padx=(10, 0), pady=(2, 0)
        )

        tk.Label(body, text=_("Картинка (необязательно):"), bg=t["bg_main"], fg=t["text"], font=(FONT, 10, "bold")).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(12, 0)
        )
        self._button(body, _("Выбрать файл..."), self._choose_image, t["primary"], t["primary_dark"]).grid(
            row=5, column=0, sticky="w", pady=(6, 0)
        )
        tk.Label(body, textvariable=self.image_var, bg=t["bg_main"], fg=t["muted"], font=(FONT, 8)).grid(
            row=5, column=1, columnspan=2, sticky="w", padx=(10, 0), pady=(6, 0)
        )

        # --- Стиль ---
        tk.Label(body, text=_("Стиль стикера:"), bg=t["bg_main"], fg=t["text"], font=(FONT, 10, "bold")).grid(
            row=6, column=0, sticky="w", pady=(12, 0)
        )
        self.style_menu = self._option_menu(body, self.style_var, self._style_labels, width=15)
        self.style_menu.grid(row=7, column=0, sticky="w", pady=(2, 0))

        # --- Повтор ---
        tk.Label(body, text=_("Повтор:"), bg=t["bg_main"], fg=t["text"], font=(FONT, 10, "bold")).grid(
            row=6, column=1, sticky="w", padx=(10, 0), pady=(12, 0)
        )
        self.repeat_menu = self._option_menu(body, self.repeat_var, self._repeat_labels, width=18)
        self.repeat_menu.grid(row=7, column=1, sticky="w", padx=(10, 0), pady=(2, 0))
        self.repeat_var.trace_add("write", lambda *a: self._update_repeat_state())

        self.repeat_days_spin = tk.Spinbox(
            body, from_=2, to=999, width=5, textvariable=self.repeat_days_var, justify="center",
            font=(FONT, 10), bg=t["panel_bg"], fg=t["text"], relief="flat", bd=0,
            buttonbackground=t["primary"], insertbackground=t["text"], disabledbackground=t["off"],
            highlightthickness=1, highlightbackground=t["border"], highlightcolor=t["primary"],
        )
        self.repeat_days_spin.grid(row=7, column=2, sticky="w", padx=(10, 0), pady=(2, 0))
        self._update_repeat_state()

        buttons = tk.Frame(body, bg=t["bg_main"])
        buttons.grid(row=8, column=0, columnspan=3, sticky="we", pady=(16, 0))
        self._button(buttons, _("Редактор"), self._open_manager, t["primary"], t["primary_dark"]).pack(side="left")

        right = tk.Frame(buttons, bg=t["bg_main"])
        right.pack(side="right")
        self._button(right, _("Отмена"), self.destroy, t["red"], t["red_dark"]).pack(side="left", padx=(0, 8))
        self._button(
            right, _("Сохранить") if self.editing else _("Создать"), self._save, t["green"], t["green_dark"]
        ).pack(side="left")

    # ---------- фабрики виджетов ----------
    def _header_button(self, parent, text, command, hover):
        t = self.theme
        button = tk.Button(
            parent, text=text, command=command, bg=t["header_bg"], fg=t["text"], activebackground=hover,
            activeforeground="white", relief="flat", bd=0, font=(FONT, 10, "bold"),
            width=3, cursor="hand2",
        )
        button.bind("<Enter>", lambda e: button.configure(bg=hover, fg="white"))
        button.bind("<Leave>", lambda e: button.configure(bg=t["header_bg"], fg=t["text"]))
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
        t = self.theme
        return tk.Entry(
            parent, width=width, font=(FONT, 10), bg=t["panel_bg"], fg=t["text"],
            relief="flat", bd=0, insertbackground=t["text"],
            highlightthickness=1, highlightbackground=t["border"], highlightcolor=t["primary"],
        )

    def _option_menu(self, parent, variable, values, width=15):
        t = self.theme
        menu = tk.OptionMenu(parent, variable, *values)
        menu.configure(
            bg=t["panel_bg"], fg=t["text"], activebackground=t["primary"], activeforeground="white",
            relief="flat", bd=0, highlightthickness=1, highlightbackground=t["border"],
            font=(FONT, 10), padx=8, pady=4, cursor="hand2", anchor="w", width=width,
        )
        menu["menu"].configure(
            bg=t["panel_bg"], fg=t["text"], activebackground=t["primary"], activeforeground="white",
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
        
        # Проявляем окно только после того, как оно встало на место
        self.attributes("-alpha", 1.0)

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
        is_custom = self.repeat_var.get() == self._repeat_custom_label
        self.repeat_days_spin.configure(state="normal" if is_custom else "disabled")

    def _choose_image(self):
        path = filedialog.askopenfilename(
            title=_("Выберите изображение"),
            filetypes=[
                (_("Изображения"), "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                (_("Все файлы"), "*.*"),
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
            messagebox.showerror(_("Ошибка"), _("Введите текст напоминания."), parent=self)
            return

        try:
            when = date_utils.parse_input(self.date_entry.get(), self.time_entry.get())
        except ValueError:
            messagebox.showerror(
                _("Ошибка"),
                _("Неверный формат. Ожидается: {}").format(date_utils.input_hint()),
                parent=self,
            )
            return
        iso_datetime = date_utils.to_iso(when)

        image = self.sticker.get("image") if self.editing else None
        if self.selected_image:
            try:
                image = self._copy_image(self.selected_image)
            except OSError as error:
                messagebox.showerror(
                    _("Ошибка"),
                    _("Не удалось скопировать картинку:\n{}").format(error),
                    parent=self,
                )
                return

        repeat = self._repeat_value_by_label.get(self.repeat_var.get(), storage.REPEAT_NONE)
        if repeat == storage.REPEAT_CUSTOM:
            raw_days = self.repeat_days_spin.get().strip()
            try:
                repeat_days = int(raw_days)
            except ValueError:
                messagebox.showerror(_("Ошибка"), _("Введите целое число от 2 до 999."), parent=self)
                return

            if repeat_days == 1:
                messagebox.showwarning(_("Внимание"), _("Выберите — Каждый день."), parent=self)
                return

            if repeat_days < 2 or repeat_days > 999:
                messagebox.showerror(_("Ошибка"), _("Введите целое число от 2 до 999."), parent=self)
                return
        else:
            repeat_days = 2

        style = self._style_value_by_label.get(self.style_var.get(), STYLE_VALUES[0])

        if self.editing:
            storage.update_sticker(
                self.sticker.get("id"),
                text=text,
                image=image,
                datetime=iso_datetime,
                style=style,
                repeat=repeat,
                repeat_days=repeat_days,
                status=storage.STATUS_PENDING,
            )
        else:
            storage.add_sticker(
                text=text,
                image=image,
                datetime_str=iso_datetime,
                status=storage.STATUS_PENDING,
                style=style,
                repeat=repeat,
                repeat_days=repeat_days,
            )

        if callable(self.on_saved):
            try:
                self.on_saved()
            except Exception:
                pass

        messagebox.showinfo(
            _("Готово"),
            _("Изменения сохранены.") if self.editing else _("Напоминание создано."),
            parent=self,
        )
        self.destroy()

    def destroy(self):
        global _instance
        if _instance is self:
            _instance = None
        super().destroy()
