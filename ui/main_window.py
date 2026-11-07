import os
import shutil
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, ttk

from core import autostart, storage

_instance = None


def open_main_window(root):
    global _instance
    if _instance is not None and _instance.winfo_exists():
        _instance.deiconify()
        _instance.lift()
        _instance.focus_force()
        return _instance
    _instance = MainWindow(root)
    return _instance


class MainWindow(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)

        self.root = root
        self.selected_image = None

        self.title("MitaStickers — Новый стикер")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(padx=16, pady=16)

        self.autostart_var = tk.BooleanVar(value=autostart.is_in_startup())
        self.image_var = tk.StringVar(value="Картинка не выбрана")

        self._build()
        self._center()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    def _build(self):
        tk.Label(self, text="Текст напоминания:", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        self.text_widget = tk.Text(self, width=44, height=5, wrap="word", font=("Segoe UI", 10))
        self.text_widget.grid(row=1, column=0, columnspan=3, sticky="we", pady=(4, 12))

        now = datetime.now() + timedelta(minutes=5)
        tk.Label(self, text="Дата:", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w")
        self.date_entry = ttk.Entry(self, width=16)
        self.date_entry.insert(0, now.strftime("%Y-%m-%d"))
        self.date_entry.grid(row=3, column=0, sticky="w")

        tk.Label(self, text="Время:", font=("Segoe UI", 10)).grid(row=2, column=1, sticky="w", padx=(10, 0))
        self.time_entry = ttk.Entry(self, width=10)
        self.time_entry.insert(0, now.strftime("%H:%M"))
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
        self.style_var = tk.StringVar(value="Желтый")
        style_cb = ttk.Combobox(self, textvariable=self.style_var, values=["Желтый", "Розовый", "Фиолетовый"], state="readonly", width=13)
        style_cb.grid(row=7, column=0, sticky="w")

        tk.Checkbutton(
            self,
            text="Добавить в автозагрузку",
            variable=self.autostart_var,
            font=("Segoe UI", 10),
        ).grid(row=8, column=0, columnspan=3, sticky="w", pady=(12, 0))

        buttons = tk.Frame(self)
        buttons.grid(row=9, column=0, columnspan=3, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Создать", command=self._create).pack(side="left")

    def _center(self):
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 3
        self.geometry("+{}+{}".format(x, y))

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

    def _create(self):
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

        image = None
        if self.selected_image:
            try:
                image = self._copy_image(self.selected_image)
            except OSError as error:
                messagebox.showerror("Ошибка", "Не удалось скопировать картинку:\n{}".format(error), parent=self)
                return

        storage.add_sticker(
            text=text,
            image=image,
            datetime_str=when.strftime(storage.DATETIME_FORMAT),
            status=storage.STATUS_PENDING,
            style=self.style_var.get(),
        )

        if self.autostart_var.get():
            autostart.add_to_startup()
        else:
            autostart.remove_from_startup()

        messagebox.showinfo("Готово", "Напоминание создано.", parent=self)
        self.destroy()

    def destroy(self):
        global _instance
        if _instance is self:
            _instance = None
        super().destroy()
