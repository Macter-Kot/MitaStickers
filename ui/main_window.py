import os
import shutil
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, ttk

from core import autostart, storage
from ui.sticker_window import get_resource_path

APP_ICON = get_resource_path("assets/icon.ico")

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

        self.title("MitaStickers — Редактирование" if self.editing else "MitaStickers — Новый стикер")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(padx=16, pady=16)
        self._apply_icon()

        self.autostart_var = tk.BooleanVar(value=autostart.is_in_startup())
        self.image_var = tk.StringVar()
        self.style_var = tk.StringVar(value="Желтый")
        self.repeat_var = tk.StringVar(value=REPEAT_TO_LABEL[storage.REPEAT_NONE])
        self.repeat_days_var = tk.IntVar(value=2)

        self._prefill()
        self._build()
        self._center()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
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

    def _build(self):
        tk.Label(self, text="Текст напоминания:", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        self.text_widget = tk.Text(self, width=44, height=5, wrap="word", font=("Segoe UI", 10))
        self.text_widget.grid(row=1, column=0, columnspan=3, sticky="we", pady=(4, 12))
        if self.editing:
            self.text_widget.insert("1.0", self.sticker.get("text", ""))

        when = datetime.now() + timedelta(minutes=5)
        if self.editing:
            try:
                when = datetime.strptime(self.sticker.get("datetime", ""), storage.DATETIME_FORMAT)
            except (ValueError, TypeError):
                pass

        tk.Label(self, text="Дата:", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w")
        self.date_entry = ttk.Entry(self, width=16)
        self.date_entry.insert(0, when.strftime("%Y-%m-%d"))
        self.date_entry.grid(row=3, column=0, sticky="w")

        tk.Label(self, text="Время:", font=("Segoe UI", 10)).grid(row=2, column=1, sticky="w", padx=(10, 0))
        self.time_entry = ttk.Entry(self, width=10)
        self.time_entry.insert(0, when.strftime("%H:%M"))
        self.time_entry.grid(row=3, column=1, sticky="w", padx=(10, 0))

        tk.Label(self, text="Формат: ГГГГ-ММ-ДД и ЧЧ:ММ", font=("Segoe UI", 8), fg="gray").grid(
            row=3, column=2, sticky="w", padx=(10, 0)
        )

        tk.Label(self, text="Картинка (необязательно):", font=("Segoe UI", 10, "bold")).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(12, 0)
        )
        ttk.Button(self, text="Выбрать файл...", command=self._choose_image).grid(
            row=5, column=0, sticky="w", pady=(4, 0)
        )
        tk.Label(self, textvariable=self.image_var, font=("Segoe UI", 8), fg="gray").grid(
            row=5, column=1, columnspan=2, sticky="w", padx=(10, 0)
        )

        # --- ВЫБОР СТИЛЯ ---
        tk.Label(self, text="Стиль стикера:", font=("Segoe UI", 10, "bold")).grid(row=6, column=0, sticky="w", pady=(12, 0))
        style_cb = ttk.Combobox(
            self,
            textvariable=self.style_var,
            values=["Желтый", "Розовый", "Фиолетовый"],
            state="readonly",
            width=13,
        )
        style_cb.grid(row=7, column=0, sticky="w")

        # --- ПОВТОР ---
        tk.Label(self, text="Повтор:", font=("Segoe UI", 10, "bold")).grid(
            row=6, column=1, sticky="w", padx=(10, 0), pady=(12, 0)
        )
        self.repeat_cb = ttk.Combobox(
            self,
            textvariable=self.repeat_var,
            values=[label for label, _ in REPEAT_LABELS],
            state="readonly",
            width=15,
        )
        self.repeat_cb.grid(row=7, column=1, sticky="w", padx=(10, 0))
        self.repeat_cb.bind("<<ComboboxSelected>>", lambda event: self._update_repeat_state())

        self.repeat_days_spin = tk.Spinbox(
            self, from_=2, to=999, width=5, textvariable=self.repeat_days_var, justify="center"
        )
        self.repeat_days_spin.grid(row=7, column=2, sticky="w", padx=(10, 0))
        self._update_repeat_state()

        tk.Checkbutton(
            self,
            text="Добавить в автозагрузку",
            variable=self.autostart_var,
            font=("Segoe UI", 10),
        ).grid(row=8, column=0, columnspan=3, sticky="w", pady=(12, 0))

        buttons = tk.Frame(self)
        buttons.grid(row=9, column=0, columnspan=3, sticky="we", pady=(16, 0))
        ttk.Button(buttons, text="Редактор", command=self._open_manager).pack(side="left")

        right = tk.Frame(buttons)
        right.pack(side="right")
        ttk.Button(right, text="Отмена", command=self.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(right, text="Сохранить" if self.editing else "Создать", command=self._save).pack(side="left")

    def _center(self):
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 3
        self.geometry("+{}+{}".format(x, y))

    def _open_manager(self):
        from ui.manager_window import open_manager_window

        open_manager_window(self.root)

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
                messagebox.showerror(
                    "Ошибка",
                    "Введите целое число от 2 до 999.",
                    parent=self,
                )
                return

            if repeat_days == 1:
                messagebox.showwarning(
                    "Внимание",
                    "Выберите — Каждый день.",
                    parent=self,
                )
                return

            if repeat_days < 2 or repeat_days > 999:
                messagebox.showerror(
                    "Ошибка",
                    "Введите целое число от 2 до 999.",
                    parent=self,
                )
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

        if self.autostart_var.get():
            autostart.add_to_startup()
        else:
            autostart.remove_from_startup()

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
