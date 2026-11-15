import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover
    Image = None
    ImageTk = None

from core import storage
from core.i18n import _
from ui.sticker_window import get_resource_path

CARTRIDGE = "assets/cartridge.png"
PLACEHOLDER = "assets/default_placeholder.png"

# Геометрия картриджа (в пикселях исходного изображения 2386x1620)
IMAGE_SIZE = (2386, 1620)
CUTOUT = (123, 239, 2246, 1341)  # прозрачный вырез под список
DISPLAY_WIDTH = 880

THUMB_SIZE = (84, 60)
CHROMA_KEY = "#FF00FF"

PANEL_BG = "#FFF8E1"
PANEL_BORDER = "#F06292"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#FBC02D"
TEXT_COLOR = "#3E2723"
DATE_COLOR = "#8D6E63"
GREEN = "#66BB6A"
GREEN_DARK = "#43A047"
RED = "#EF5350"
RED_DARK = "#C62828"
PRIMARY = "#F4A7B9"
PRIMARY_DARK = "#EC8FA6"
OFF = "#E0E0E0"
OFF_DARK = "#CFCFCF"

_instance = None


def open_manager_window(root):
    global _instance
    if _instance is not None and _instance.winfo_exists():
        _instance.refresh()
        _instance.deiconify()
        _instance.lift()
        _instance.focus_force()
        return _instance
    _instance = ManagerWindow(root)
    return _instance


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        self.after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, event=None):
        self._cancel()
        self.after_id = self.widget.after(400, self._show)

    def _show(self):
        if self.tip is not None:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.attributes("-topmost", True)
        tk.Label(
            self.tip,
            text=self.text,
            bg="#212121",
            fg="white",
            font=("Segoe UI", 8),
            padx=6,
            pady=2,
        ).pack()
        self.tip.update_idletasks()
        width = self.tip.winfo_reqwidth()
        self.tip.wm_geometry("+%d+%d" % (x - width // 2, y))

    def _hide(self, event=None):
        self._cancel()
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None

    def _cancel(self):
        if self.after_id is not None:
            try:
                self.widget.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None


class ManagerWindow(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)

        self.root = root
        self.filter_mode = "active"
        self._bg_photo = None
        self._thumbs = []
        self._tooltips = []
        self._drag_x = 0
        self._drag_y = 0

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=CHROMA_KEY)
        try:
            self.attributes("-transparentcolor", CHROMA_KEY)
        except tk.TclError:
            pass

        self.scale = DISPLAY_WIDTH / IMAGE_SIZE[0]
        self.disp_w = DISPLAY_WIDTH
        self.disp_h = round(IMAGE_SIZE[1] * self.scale)

        self._build()
        self._center()

        self.bind("<Escape>", lambda event: self.destroy())
        self.focus_force()
        self.refresh()

    # ---------- геометрия ----------
    def _cutout_rect(self):
        x0 = round(CUTOUT[0] * self.scale)
        y0 = round(CUTOUT[1] * self.scale)
        x1 = round(CUTOUT[2] * self.scale)
        y1 = round(CUTOUT[3] * self.scale)
        return x0, y0, x1, y1

    # ---------- интерфейс ----------
    def _build(self):
        self.canvas = tk.Canvas(
            self, width=self.disp_w, height=self.disp_h, bg=CHROMA_KEY, highlightthickness=0
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._start_move)
        self.canvas.bind("<B1-Motion>", self._on_move)

        self._bg_photo = self._load_cartridge()
        if self._bg_photo is not None:
            self.canvas.create_image(0, 0, image=self._bg_photo, anchor="nw")
        else:
            self.canvas.create_rectangle(0, 0, self.disp_w, self.disp_h, fill="#FBC02D", outline="")

        x0, y0, x1, y1 = self._cutout_rect()

        # панель со списком внутри выреза
        self.panel = tk.Frame(self, bg=PANEL_BG, highlightthickness=2, highlightbackground=PANEL_BORDER)
        self.panel.place(x=x0, y=y0, width=x1 - x0, height=y1 - y0)
        self.panel.grid_rowconfigure(1, weight=1)
        self.panel.grid_columnconfigure(0, weight=1)

        tk.Label(
            self.panel,
            text=_("РЕДАКТОР НАПОМИНАНИЙ"),
            bg=PANEL_BG,
            fg=PANEL_BORDER,
            font=("Segoe UI", 11, "bold"),
            pady=6,
        ).grid(row=0, column=0, sticky="ew")

        list_wrap = tk.Frame(self.panel, bg=PANEL_BG)
        list_wrap.grid(row=1, column=0, sticky="nsew", padx=6)
        list_wrap.grid_rowconfigure(0, weight=1)
        list_wrap.grid_columnconfigure(0, weight=1)

        self.list_canvas = tk.Canvas(list_wrap, bg=PANEL_BG, highlightthickness=0)
        scroll = ttk.Scrollbar(list_wrap, orient="vertical", command=self.list_canvas.yview)
        self.list_inner = tk.Frame(self.list_canvas, bg=PANEL_BG)
        self.list_window = self.list_canvas.create_window((0, 0), window=self.list_inner, anchor="nw")
        self.list_canvas.configure(yscrollcommand=scroll.set)
        self.list_canvas.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.list_inner.bind(
            "<Configure>",
            lambda event: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all")),
        )
        self.list_canvas.bind(
            "<Configure>",
            lambda event: self.list_canvas.itemconfigure(self.list_window, width=event.width),
        )
        self._bind_wheel(self.list_canvas)

        bottom = tk.Frame(self.panel, bg=PANEL_BG)
        bottom.grid(row=2, column=0, sticky="ew", pady=6)
        self.btn_active = tk.Button(
            bottom, text=_("Актуальные"), command=lambda: self._set_filter("active"),
            font=("Segoe UI", 9, "bold"), relief="flat", bd=0, height=1, padx=12, cursor="hand2",
        )
        self.btn_done = tk.Button(
            bottom, text=_("Завершённые"), command=lambda: self._set_filter("done"),
            font=("Segoe UI", 9, "bold"), relief="flat", bd=0, height=1, padx=12, cursor="hand2",
        )
        self.btn_active.pack(side="left", expand=True, fill="x", padx=(6, 3))
        self.btn_done.pack(side="left", expand=True, fill="x", padx=(3, 6))
        self._update_toggle_styles()

        # крестик закрытия на корпусе картриджа (справа сверху)
        close_x = x1 - 15  # Координата X
        close_y = y0 - 65  # Координата Y
        
        close_id = self.canvas.create_text(
            close_x, close_y, text="✕", font=("Arial Black", 18, "bold"),
            fill=PANEL_BORDER, activefill=RED_DARK
        )
        # Назначаем клик и курсор
        self.canvas.tag_bind(close_id, "<Button-1>", lambda event: self.destroy())
        self.canvas.tag_bind(close_id, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(close_id, "<Leave>", lambda e: self.canvas.config(cursor=""))

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.disp_w) // 2
        y = (self.winfo_screenheight() - self.disp_h) // 2
        self.geometry("{}x{}+{}+{}".format(self.disp_w, self.disp_h, x, y))

    def _bind_wheel(self, widget):
        widget.bind("<Enter>", lambda event: widget.bind_all("<MouseWheel>", self._on_wheel), add="+")
        widget.bind("<Leave>", lambda event: widget.unbind_all("<MouseWheel>"), add="+")

    def _on_wheel(self, event):
        self.list_canvas.yview_scroll(int(-event.delta / 120), "units")

    # ---------- фильтр ----------
    def _set_filter(self, mode):
        self.filter_mode = mode
        self._update_toggle_styles()
        self.refresh()

    def _update_toggle_styles(self):
        active = self.filter_mode == "active"
        self.btn_active.configure(
            bg=GREEN if active else OFF,
            fg="white" if active else "#555555",
            activebackground=GREEN_DARK if active else OFF_DARK,
            activeforeground="white" if active else "#333333",
        )
        self.btn_done.configure(
            bg=RED if not active else OFF,
            fg="white" if not active else "#555555",
            activebackground=RED_DARK if not active else OFF_DARK,
            activeforeground="white" if not active else "#333333",
        )

    # ---------- список ----------
    def refresh(self):
        if not getattr(self, "list_inner", None) or not self.list_inner.winfo_exists():
            return

        for child in self.list_inner.winfo_children():
            child.destroy()
        self._thumbs = []
        self._tooltips = []

        stickers = storage.load_stickers()
        if self.filter_mode == "active":
            items = [s for s in stickers if s.get("status") != storage.STATUS_COMPLETED]
        else:
            items = [s for s in stickers if s.get("status") == storage.STATUS_COMPLETED]
        items.sort(key=lambda s: str(s.get("datetime", "")))

        if not items:
            tk.Label(
                self.list_inner, text=_("Здесь пусто"), bg=PANEL_BG, fg=DATE_COLOR,
                font=("Segoe UI", 10, "italic"),
            ).pack(pady=24)
        else:
            for sticker in items:
                self._build_card(sticker)

        self.list_canvas.yview_moveto(0)

    def _build_card(self, sticker):
        card = tk.Frame(self.list_inner, bg=CARD_BG, highlightthickness=1, highlightbackground=CARD_BORDER)
        card.pack(fill="x", padx=4, pady=4)
        card.grid_columnconfigure(0, weight=1)

        info = tk.Frame(card, bg=CARD_BG)
        info.grid(row=0, column=0, sticky="nsew", padx=(10, 6), pady=8)
        tk.Label(
            info, text=sticker.get("text", ""), bg=CARD_BG, fg=TEXT_COLOR,
            font=("Segoe UI", 10, "bold"), wraplength=420, justify="left", anchor="w",
        ).pack(anchor="w")

        date_part, time_part = self._format_datetime(sticker.get("datetime"))
        meta = tk.Frame(info, bg=CARD_BG)
        meta.pack(anchor="w", pady=(4, 0))
        tk.Label(
            meta, text=" ".join(part for part in (date_part, time_part) if part),
            bg=CARD_BG, fg=DATE_COLOR, font=("Segoe UI", 8),
        ).pack(side="left")
        if sticker.get("repeat", storage.REPEAT_NONE) not in ("", storage.REPEAT_NONE, None):
            tk.Label(
                meta, text="\u21bb", bg=CARD_BG, fg="#2E7D32", font=("Segoe UI", 10, "bold"),
            ).pack(side="left", padx=(6, 0))

        thumb = self._load_thumb(sticker.get("image"))
        if thumb is not None:
            tk.Label(card, image=thumb, bg=CARD_BG).grid(row=0, column=1, padx=6, pady=8)

        controls = tk.Frame(card, bg=CARD_BG)
        controls.grid(row=0, column=2, sticky="n", padx=(0, 8), pady=8)

        if sticker.get("status") != storage.STATUS_COMPLETED:
            edit_btn = self._icon_button(controls, "✎", PANEL_BORDER, lambda: self._edit(sticker))
            self._add_tooltip(edit_btn, _("Редактировать"))
        del_btn = self._icon_button(controls, "✕", RED_DARK, lambda: self._delete(sticker.get("id")))
        self._add_tooltip(del_btn, _("Удалить"))

    def _icon_button(self, parent, text, color, command):
        button = tk.Label(
            parent, text=text, bg=CARD_BG, fg=color, font=("Segoe UI", 12, "bold"),
            cursor="hand2", width=2,
        )
        button.pack(pady=1)
        button.bind("<Button-1>", lambda event: command())
        button.bind("<Enter>", lambda event: button.config(bg="#F5F5F5"))
        button.bind("<Leave>", lambda event: button.config(bg=CARD_BG))
        return button

    def _add_tooltip(self, widget, text):
        tooltip = Tooltip(widget, text)
        self._tooltips.append(tooltip)
        return tooltip

    # ---------- действия ----------
    def _edit(self, sticker):
        from ui.main_window import open_main_window

        open_main_window(self.root, sticker=dict(sticker), on_saved=self.refresh)

    def _delete(self, sticker_id):
        if sticker_id is None:
            return
        storage.delete_sticker(sticker_id)
        self.refresh()

    # ---------- картинки ----------
    def _load_cartridge(self):
        if Image is None or ImageTk is None:
            return None
        path = get_resource_path(CARTRIDGE)
        if not os.path.exists(path):
            return None
        try:
            image = Image.open(path).convert("RGBA")
        except OSError:
            return None

        resample = getattr(Image, "LANCZOS", getattr(Image, "BICUBIC", 3))
        image = image.resize((self.disp_w, self.disp_h), resample)

        key = tuple(int(CHROMA_KEY[i:i + 2], 16) for i in (1, 3, 5))
        key_image = Image.new("RGB", image.size, key)
        flat = Image.new("RGB", image.size, key)
        flat.paste(image, (0, 0), image)
        # отвердеваем края, чтобы не было фиолетового ореола от прозрачности
        transparent = image.getchannel("A").point(lambda a: 255 if a < 200 else 0)
        flat.paste(key_image, (0, 0), transparent)
        return ImageTk.PhotoImage(flat)

    def _load_thumb(self, image_path):
        if Image is None or ImageTk is None:
            return None

        if image_path and str(image_path).strip():
            path = str(image_path)
            if not os.path.isabs(path):
                path = os.path.join(storage.BASE_DIR, path)
        else:
            path = get_resource_path(PLACEHOLDER)

        if not os.path.exists(path):
            path = get_resource_path(PLACEHOLDER)
            if not os.path.exists(path):
                return None

        try:
            image = Image.open(path)
            resample = getattr(Image, "LANCZOS", getattr(Image, "BICUBIC", 3))
            image.thumbnail(THUMB_SIZE, resample)
            photo = ImageTk.PhotoImage(image)
        except (OSError, ValueError):
            return None

        self._thumbs.append(photo)
        return photo

    def _format_datetime(self, value):
        if not value:
            return "", ""
        try:
            due = datetime.strptime(value, storage.DATETIME_FORMAT)
            return due.strftime("%d.%m.%Y"), due.strftime("%H:%M")
        except (ValueError, TypeError):
            date_part, _, time_part = str(value).partition(" ")
            return date_part.strip(), time_part.strip()

    # ---------- перетаскивание ----------
    def _start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_move(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry("+{}+{}".format(x, y))

    def destroy(self):
        global _instance
        for tooltip in self._tooltips:
            tooltip._hide()
        if _instance is self:
            _instance = None
        super().destroy()
