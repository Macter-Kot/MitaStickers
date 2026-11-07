import os
import tkinter as tk

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

from core import storage

# --- НАСТРОЙКИ ТЕМ (ЦВЕТА) ---
THEMES = {
    "Желтый": {"bg": "#FFF9C4", "head": "#FBC02D", "border": "#5D4037", "text": "#212121", "btn": "#4CAF50"},
    "Розовый": {"bg": "#FCE4EC", "head": "#F06292", "border": "#880E4F", "text": "#212121", "btn": "#4CAF50"},
    "Темный": {"bg": "#212121", "head": "#424242", "border": "#9C27B0", "text": "#FFFFFF", "btn": "#9C27B0"}
}
OVERDUE = {"bg": "#FFEBEE", "head": "#E53935", "border": "#B71C1C", "text": "#212121", "btn": "#D32F2F"}

IMAGE_MAX_SIZE = (260, 160)
CHROMA_KEY = "#FF00FF" # Секретный цвет для невидимой зоны скотча
Y_OFFSET = 17 # На сколько пикселей сдвигаем бумажку вниз, чтобы скотч торчал

class StickerWindow(tk.Toplevel):
    _open = []

    def __init__(self, root, text, image_path=None, is_overdue=False, sticker_id=None, on_complete=None, style="Желтый"):
        super().__init__(root)

        self.root = root
        self.sticker_id = sticker_id
        self.on_complete = on_complete
        self.is_overdue = is_overdue
        
        self.colors = OVERDUE if is_overdue else THEMES.get(style, THEMES["Желтый"])
        
        self._photo = None
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
        
        # 2. Градиент
        self._draw_gradient(w, h, Y_OFFSET)
        
        # 3. Рамка стикера (сдвинута вниз на Y_OFFSET)
        self.canvas.create_rectangle(2, Y_OFFSET, w-2, h + Y_OFFSET - 2, fill=self.colors["bg"], outline=self.colors["border"], width=3)
        
        # 4. Шапка (Header)
        self.canvas.create_rectangle(2, Y_OFFSET, w-2, Y_OFFSET + 35, fill=self.colors["head"], outline="")
        
        # 5. СКОТЧ ТОРЧИТ СВЕРХУ (начинается с y=0)
        tape_color = "#FFFFFF" if self.colors["bg"] != "#212121" else "#757575"
        self.canvas.create_rectangle(w//2 - 25, 0, w//2 + 25, Y_OFFSET + 12, fill=tape_color, outline=self.colors["border"], width=1, stipple="gray50")
        
        # 6. Заголовок
        if self.is_overdue:
            self.canvas.create_text(15, Y_OFFSET + 18, text="⚠", font=("Segoe UI", 12), fill="#FFFFFF", anchor="w")
            self.canvas.create_text(35, Y_OFFSET + 18, text="ПРОСРОЧЕНО", font=("Segoe UI", 10, "bold"), fill="#FFFFFF", anchor="w")
        else:
            self.canvas.create_oval(15, Y_OFFSET + 12, 23, Y_OFFSET + 20, fill="#F44336", outline="") 
            self.canvas.create_text(30, Y_OFFSET + 16, text="НАПОМИНАНИЕ", font=("Segoe UI", 10, "bold"), fill=self.colors["border"], anchor="w")
            
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
        btn.place(x=2, y=h + Y_OFFSET - 36, width=w-4, height=34)

    def _draw_gradient(self, w, h, y_offset):
        base_color = self.colors["bg"]
        if base_color == "#FFF9C4": shade = "#FFF59D" 
        elif base_color == "#FCE4EC": shade = "#F8BBD0" 
        elif base_color == "#FFEBEE": shade = "#FFCDD2" # <-- Добавил градиент для просрочки!
        else: return
            
        for i in range(40):
            self.canvas.create_line(w - 60 + i, h + y_offset - 35, w, h + y_offset - 75 + i, fill=shade, width=2)

    def _load_image(self, image_path):
        if not image_path or Image is None or ImageTk is None:
            return None
        path = image_path
        if not os.path.isabs(path):
            path = os.path.join(storage.BASE_DIR, path)
        if not os.path.exists(path):
            return None
        try:
            image = Image.open(path)
            image.thumbnail(IMAGE_MAX_SIZE)
            return ImageTk.PhotoImage(image)
        except (OSError, ValueError):
            return None

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
            storage.update_sticker(self.sticker_id, status=storage.STATUS_COMPLETED)
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