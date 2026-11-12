import os
import sys
import tkinter as tk
from datetime import datetime

try:
    from PIL import Image, ImageTk, ImageOps
except ImportError:
    Image = None
    ImageTk = None
    ImageOps = None

from core import storage

DEFAULT_PLACEHOLDER = "assets/default_placeholder.png"


def get_resource_path(relative_path):
    """Абсолютный путь к ресурсу — работает и в обычном режиме, и в PyInstaller.

    В собранном .exe файлы кладутся во временную папку sys._MEIPASS, в исходниках
    ресурсы лежат рядом с проектом (storage.BASE_DIR).
    """
    if os.path.isabs(relative_path):
        return relative_path
    base = getattr(sys, "_MEIPASS", None) or storage.BASE_DIR
    return os.path.join(base, relative_path)

# --- НАСТРОЙКИ ТЕМ (ЦВЕТА) ---
# "bg"    - базовый (светлый) цвет бумажки
# "shade" - более тёмный/насыщенный оттенок для градиента в правом нижнем углу
# "tape"  - цвет скотча сверху
THEMES = {
    "Желтый": {
        "bg": "#FFF9C4", "shade": "#FFE082", "head": "#FBC02D",
        "border": "#5D4037", "text": "#212121", "btn": "#4CAF50", "tape": "#FFFFFF",
    },
    "Розовый": {
        "bg": "#FCE4EC", "shade": "#F8BBD0", "head": "#F06292",
        "border": "#880E4F", "text": "#212121", "btn": "#4CAF50", "tape": "#FFFFFF",
    },
    "Фиолетовый": {
        "bg": "#2E1A47", "shade": "#1A0B2E", "head": "#3D2459",
        "border": "#D1B3E0", "text": "#FFFFFF", "btn": "#7E57C2", "tape": "#B0A4C4",
    },
}
# Обратная совместимость со старым названием темы
THEMES["Темный"] = THEMES["Фиолетовый"]

OVERDUE = {
    "bg": "#FFCDD2", "shade": "#E57373", "head": "#E53935",
    "border": "#B71C1C", "text": "#212121", "btn": "#D32F2F", "tape": "#FFFFFF",
}

IMAGE_MAX_SIZE = (260, 160)
CHROMA_KEY = "#FF00FF" # Секретный цвет для невидимой зоны скотча
Y_OFFSET = 17 # На сколько пикселей сдвигаем бумажку вниз, чтобы скотч торчал

# Кэш дефолтной картинки: большой PNG открываем и масштабируем лишь один раз
_placeholder_photo = None

class StickerWindow(tk.Toplevel):
    _open = []

    def __init__(self, root, text, image_path=None, is_overdue=False, sticker_id=None, on_complete=None, style="Желтый", datetime_str=None, repeat="none"):
        super().__init__(root)

        self.root = root
        self.sticker_id = sticker_id
        self.on_complete = on_complete
        self.is_overdue = is_overdue
        self.datetime_str = datetime_str
        self.repeat = repeat or storage.REPEAT_NONE
        
        self.colors = OVERDUE if is_overdue else THEMES.get(style, THEMES["Желтый"])
        
        self._photo = None
        self._bg_photo = None
        self._drag_x = 0
        self._drag_y = 0

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Делаем прозрачность для верхней зоны, где будет торчать скотч
        self.configure(bg=CHROMA_KEY)
        self.attributes("-transparentcolor", CHROMA_KEY)
        
        self._build(text, image_path)
        self.update_idletasks()
        self._place_window()

        self.bind("<Escape>", lambda event: self.destroy())
        StickerWindow._open.append(self)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build(self, text, image_path):
        w = 280
        h = 130 
        
        photo = self._load_image(image_path)
        if photo:
            h += photo.height() + 15
        if self.is_overdue:
            h += 25
            
        # 1. Создаем Холст (высота увеличена на Y_OFFSET)
        self.canvas = tk.Canvas(self, width=w, height=h + Y_OFFSET, bg=CHROMA_KEY, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # 2. Градиентный фон бумажки (PIL) — кладём самым нижним слоем
        self._bg_photo = self._make_gradient(
            w - 4, h - 2, self.colors["bg"], self.colors.get("shade", self.colors["bg"])
        )
        if self._bg_photo is not None:
            self.canvas.create_image(2, Y_OFFSET, image=self._bg_photo, anchor="nw")
            self.canvas.create_rectangle(2, Y_OFFSET, w-2, h + Y_OFFSET - 2, fill="", outline=self.colors["border"], width=3)
        else:
            # Резервный вариант, если PIL недоступен
            self.canvas.create_rectangle(2, Y_OFFSET, w-2, h + Y_OFFSET - 2, fill=self.colors["bg"], outline=self.colors["border"], width=3)
        
        # 4. Шапка (Header)
        self.canvas.create_rectangle(2, Y_OFFSET, w-2, Y_OFFSET + 35, fill=self.colors["head"], outline="")
        
        # 5. СКОТЧ ТОРЧИТ СВЕРХУ (начинается с y=0)
        tape_color = self.colors.get("tape", "#FFFFFF")
        self.canvas.create_rectangle(w//2 - 25, 0, w//2 + 25, Y_OFFSET + 12, fill=tape_color, outline=self.colors["border"], width=1, stipple="gray50")
        
        # 6. Заголовок
        if self.is_overdue:
            self.canvas.create_text(15, Y_OFFSET + 18, text="⚠", font=("Segoe UI", 12), fill="#FFFFFF", anchor="w")
            title_id = self.canvas.create_text(35, Y_OFFSET + 18, text="ПРОСРОЧЕНО", font=("Segoe UI", 10, "bold"), fill="#FFFFFF", anchor="w")
            dt_color = "#FFFFFF"
        else:
            self.canvas.create_oval(15, Y_OFFSET + 12, 23, Y_OFFSET + 20, fill="#F44336", outline="") 
            title_id = self.canvas.create_text(30, Y_OFFSET + 16, text="НАПОМИНАНИЕ", font=("Segoe UI", 10, "bold"), fill=self.colors["border"], anchor="w")
            dt_color = self.colors["border"]

        # 6.1 Дата и время напоминания в шапке (после заголовка)
        self._draw_datetime(title_id, w, dt_color)

        # 7. Крестик закрытия
        close_id = self.canvas.create_text(w - 15, Y_OFFSET + 18, text="✕", font=("Segoe UI", 12, "bold"), fill="#FFFFFF" if self.is_overdue else self.colors["border"])
        self.canvas.tag_bind(close_id, "<Button-1>", lambda e: self.destroy())
        self.canvas.tag_bind(close_id, "<Enter>", lambda e: self.canvas.itemconfig(close_id, fill="red"))
        self.canvas.tag_bind(close_id, "<Leave>", lambda e: self.canvas.itemconfig(close_id, fill="#FFFFFF" if self.is_overdue else self.colors["border"]))

        self.canvas.tag_bind("all", "<Button-1>", self._start_move)
        self.canvas.tag_bind("all", "<B1-Motion>", self._on_move)

        current_y = Y_OFFSET + 45
        
        # 8. Текст с подчеркиванием
        if text:
            text_id = self.canvas.create_text(w//2, current_y, text=text, font=("Segoe UI", 11), fill=self.colors["text"], width=w-30, anchor="n", justify="center")
            bbox = self.canvas.bbox(text_id) 
            current_y = bbox[3] + 5
            self.canvas.create_line(20, current_y, w-20, current_y, fill=self.colors["border"], width=1)
            current_y += 10

        # 9. Картинка (если есть)
        if photo:
            self._photo = photo
            self.canvas.create_image(w//2, current_y, image=photo, anchor="n")
            current_y += photo.height() + 10

        if self.is_overdue:
            self.canvas.create_text(w//2, current_y, text="⚠ Дедлайн уже прошёл!", font=("Segoe UI", 9, "italic"), fill=self.colors["border"], anchor="n")

        # 10. Кнопка
        btn = tk.Button(self, text="✔ Выполнено", command=self.complete, bg=self.colors["btn"], fg="white", 
                        activebackground="#388E3C" if not self.is_overdue else "#B71C1C", activeforeground="white",
                        relief="flat", font=("Segoe UI", 10, "bold"), cursor="hand2")
        # Кнопка прижата влево, чтобы правый нижний угол бумажки с градиентом был виден
        btn.place(x=14, y=h + Y_OFFSET - 40, width=150, height=32)

    def _format_datetime(self, value):
        """Разбирает сохранённую дату-время и возвращает (дата, время)."""
        if not value:
            return None, None
        try:
            due = datetime.strptime(value, storage.DATETIME_FORMAT)
            return due.strftime("%d.%m.%Y"), due.strftime("%H:%M")
        except (ValueError, TypeError):
            date_part, _, time_part = str(value).partition(" ")
            return date_part.strip() or None, time_part.strip()

    def _is_repeating(self):
        return bool(self.repeat) and self.repeat != storage.REPEAT_NONE

    def _repeat_badge_color(self):
        if self.is_overdue:
            return "#FFF176"
        if self.colors.get("text") == "#FFFFFF":
            return "#FFD54F"
        return "#2E7D32"

    def _draw_datetime(self, title_id, w, color):
        """Рисует дату и время после заголовка. Если в одну строку не влезает —
        время уходит под дату. Для повторяющихся событий добавляет значок ↻."""
        date_part, time_part = self._format_datetime(self.datetime_str)
        if not date_part:
            return

        font = ("Segoe UI", 8)
        x = self.canvas.bbox(title_id)[2] + 10
        right_limit = w - 30
        badge = "\u21bb" if self._is_repeating() else None  # ↻
        badge_font = ("Segoe UI", 10, "bold")
        badge_color = self._repeat_badge_color()

        line = "{}  {}".format(date_part, time_part) if time_part else date_part
        item = self.canvas.create_text(x, Y_OFFSET + 17, text=line, font=font, fill=color, anchor="w")

        if self.canvas.bbox(item)[2] > right_limit:
            # Не хватило ширины — выводим время под датой
            self.canvas.delete(item)
            date_item = self.canvas.create_text(x, Y_OFFSET + 11, text=date_part, font=font, fill=color, anchor="w")
            if time_part:
                self.canvas.create_text(x, Y_OFFSET + 25, text=time_part, font=font, fill=color, anchor="w")
            if badge:
                self.canvas.create_text(
                    self.canvas.bbox(date_item)[2] + 6, Y_OFFSET + 11,
                    text=badge, font=badge_font, fill=badge_color, anchor="w",
                )
            return

        if badge:
            self.canvas.create_text(
                self.canvas.bbox(item)[2] + 6, Y_OFFSET + 17,
                text=badge, font=badge_font, fill=badge_color, anchor="w",
            )

    def _make_gradient(self, width, height, base_hex, shade_hex):
        """Плавный радиальный градиент: базовый цвет + тень в правом нижнем углу.

        Возвращает ImageTk.PhotoImage (или None, если PIL недоступен).
        Ссылку на результат нужно хранить, иначе Tkinter удалит картинку сборщиком мусора.
        """
        if Image is None or ImageTk is None or ImageOps is None:
            return None
        if width <= 0 or height <= 0:
            return None

        try:
            resample = getattr(Image, "LANCZOS", getattr(Image, "BICUBIC", 3))

            base = Image.new("RGB", (width, height), base_hex)
            shade = Image.new("RGB", (width, height), shade_hex)

            # radial_gradient: тёмный центр, светлые края. Растягиваем в 2 раза и
            # берём верхний левый квадрант, затем разворачиваем на 180° —
            # так "светлая" (наиболее насыщенная) точка попадает в правый нижний угол.
            gradient = Image.radial_gradient("L").resize((width * 2, height * 2), resample)
            mask = gradient.crop((0, 0, width, height))
            mask = ImageOps.mirror(ImageOps.flip(mask))

            # Гамма-коррекция: прижимаем тень ближе к углу, делая переход плавным.
            mask = mask.point(lambda value: int(255 * (value / 255.0) ** 2.2))

            return ImageTk.PhotoImage(Image.composite(shade, base, mask))
        except (OSError, ValueError, AttributeError):
            return None

    def _load_image(self, image_path):
        global _placeholder_photo

        if Image is None or ImageTk is None:
            return None

        # Если пользователь не выбрал картинку — подставляем дефолтную заглушку
        is_default = not (image_path and str(image_path).strip())

        if is_default:
            path = get_resource_path(DEFAULT_PLACEHOLDER)
        else:
            path = str(image_path)
            if not os.path.isabs(path):
                path = os.path.join(storage.BASE_DIR, path)

        # Файл пропал или путь битый — снова откатываемся к заглушке
        if not os.path.exists(path):
            path = get_resource_path(DEFAULT_PLACEHOLDER)
            is_default = True
            if not os.path.exists(path):
                return None

        # Заглушку масштабируем один раз и переиспользуем
        if is_default and _placeholder_photo is not None:
            return _placeholder_photo

        try:
            image = Image.open(path)
            resample = getattr(Image, "LANCZOS", getattr(Image, "BICUBIC", 3))
            image.thumbnail(IMAGE_MAX_SIZE, resample)
            photo = ImageTk.PhotoImage(image)
        except (OSError, ValueError):
            return None

        if is_default:
            _placeholder_photo = photo
        return photo

    def _start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_move(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry("+{}+{}".format(x, y))

    def _place_window(self):
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        screen_w = self.winfo_screenwidth()
        index = len(StickerWindow._open) % 6
        x = max(0, screen_w - width - 30)
        y = 30 + index * (height + 10)
        self.geometry("{}x{}+{}+{}".format(width, height, x, y))

    def complete(self):
        if self.sticker_id is not None:
            storage.complete_sticker(self.sticker_id)
        if callable(self.on_complete):
            try:
                self.on_complete(self)
            except Exception:
                pass
        self.destroy()

    def destroy(self):
        if self in StickerWindow._open:
            StickerWindow._open.remove(self)
        super().destroy()