import os
import tkinter as tk

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover
    Image = None
    ImageTk = None

from core import storage

BG_NORMAL = "#FFF9C4"
HEAD_NORMAL = "#FBC02D"
TITLE_NORMAL = "#5D4037"

BG_OVERDUE = "#FFC9C9"
HEAD_OVERDUE = "#E53935"
TITLE_OVERDUE = "#7F0000"

TEXT_COLOR = "#212121"
IMAGE_MAX_SIZE = (240, 160)


class StickerWindow(tk.Toplevel):
    _open = []

    def __init__(
        self,
        root,
        text,
        image_path=None,
        is_overdue=False,
        sticker_id=None,
        on_complete=None,
    ):
        super().__init__(root)

        self.root = root
        self.sticker_id = sticker_id
        self.on_complete = on_complete
        self.is_overdue = is_overdue
        self._photo = None
        self._drag_x = 0
        self._drag_y = 0

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.95)
        except tk.TclError:
            pass

        bg = BG_OVERDUE if is_overdue else BG_NORMAL
        head_bg = HEAD_OVERDUE if is_overdue else HEAD_NORMAL
        title_color = TITLE_OVERDUE if is_overdue else TITLE_NORMAL
        self.configure(bg=head_bg)
        self.highlightthickness = 2
        self.highlightbackground = head_bg

        self._build(text, image_path, bg, head_bg, title_color)

        self.update_idletasks()
        self._place_window()

        self.bind("<Escape>", lambda event: self.destroy())
        StickerWindow._open.append(self)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build(self, text, image_path, bg, head_bg, title_color):
        header = tk.Frame(self, bg=head_bg)
        header.pack(fill="x")

        title = "ПРОСРОЧЕНО" if self.is_overdue else "НАПОМИНАНИЕ"
        tk.Label(
            header,
            text="\u26A0 " + title if self.is_overdue else "\u25CF " + title,
            bg=head_bg,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=6,
        ).pack(side="left")

        close_btn = tk.Label(
            header,
            text="\u2715",
            bg=head_bg,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            cursor="hand2",
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda event: self.destroy())

        self._make_draggable(header)

        body = tk.Frame(self, bg=bg, padx=14, pady=12)
        body.pack(fill="both", expand=True)

        if text:
            tk.Label(
                body,
                text=text,
                bg=bg,
                fg=TEXT_COLOR,
                font=("Segoe UI", 11),
                justify="left",
                wraplength=260,
            ).pack(anchor="w")

        photo = self._load_image(image_path)
        if photo is not None:
            self._photo = photo
            tk.Label(body, image=photo, bg=bg).pack(anchor="center", pady=(10, 0))

        if self.is_overdue:
            tk.Label(
                body,
                text="\u26A0 Дедлайн уже прошёл!",
                bg=bg,
                fg="#B71C1C",
                font=("Segoe UI", 9, "italic"),
            ).pack(anchor="w", pady=(10, 0))

        tk.Button(
            body,
            text="\u2714 Выполнено",
            command=self.complete,
            bg="#4CAF50" if not self.is_overdue else "#D32F2F",
            fg="white",
            activebackground="#388E3C" if not self.is_overdue else "#B71C1C",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(anchor="e", pady=(12, 0))

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

    def _make_draggable(self, widget):
        widget.bind("<Button-1>", self._start_move)
        widget.bind("<B1-Motion>", self._on_move)

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
