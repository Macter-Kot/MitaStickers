import os
import tkinter as tk
from tkinter import messagebox

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover
    Image = None
    ImageTk = None

from core import autostart, i18n, settings
from core.i18n import _
from core.theme import THEME_LABELS, get_theme, get_theme_name, set_theme
from ui.sticker_window import get_resource_path
from ui.manager_window import (
    CARTRIDGE,
    CHROMA_KEY,
    CUTOUT,
    DISPLAY_WIDTH,
    IMAGE_SIZE,
    make_scrollbar,
    tint_cartridge,
)

_instance = None


def open_settings_window(root):
    global _instance
    if _instance is not None and _instance.winfo_exists():
        _instance.deiconify()
        _instance.lift()
        _instance.focus_force()
        return _instance
    _instance = SettingsWindow(root)
    return _instance


class SettingsWindow(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)

        self.root = root
        self.theme = get_theme()
        self._bg_photo = None
        self._tooltips = []
        self._drag_x = 0
        self._drag_y = 0

        try:
            self.autostart_enabled = bool(autostart.is_in_startup())
        except Exception:
            self.autostart_enabled = False

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

    # ---------- геометрия ----------
    def _cutout_rect(self):
        x0 = round(CUTOUT[0] * self.scale)
        y0 = round(CUTOUT[1] * self.scale)
        x1 = round(CUTOUT[2] * self.scale)
        y1 = round(CUTOUT[3] * self.scale)
        return x0, y0, x1, y1

    # ---------- интерфейс ----------
    def _build(self):
        t = self.theme

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
            self.canvas.create_rectangle(0, 0, self.disp_w, self.disp_h, fill=t["panel_border"], outline="")

        x0, y0, x1, y1 = self._cutout_rect()

        self.panel = tk.Frame(self, bg=t["panel_bg"], highlightthickness=2, highlightbackground=t["panel_border"])
        self.panel.place(x=x0, y=y0, width=x1 - x0, height=y1 - y0)
        self.panel.grid_rowconfigure(1, weight=1)
        self.panel.grid_columnconfigure(0, weight=1)

        tk.Label(
            self.panel,
            text=_("НАСТРОЙКИ"),
            bg=t["panel_bg"],
            fg=t["panel_border"],
            font=("Segoe UI", 11, "bold"),
            pady=6,
        ).grid(row=0, column=0, sticky="ew")

        list_wrap = tk.Frame(self.panel, bg=t["panel_bg"])
        list_wrap.grid(row=1, column=0, sticky="nsew", padx=6)
        list_wrap.grid_rowconfigure(0, weight=1)
        list_wrap.grid_columnconfigure(0, weight=1)

        self.list_canvas = tk.Canvas(list_wrap, bg=t["panel_bg"], highlightthickness=0)
        scroll = make_scrollbar(list_wrap, self.list_canvas.yview, t)
        self.list_inner = tk.Frame(self.list_canvas, bg=t["panel_bg"])
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

        self._build_list()

        bottom = tk.Frame(self.panel, bg=t["panel_bg"])
        bottom.grid(row=2, column=0, sticky="ew", pady=6)
        self.btn_save = tk.Button(
            bottom, text=_("Сохранить"), command=self._save,
            font=("Segoe UI", 9, "bold"), relief="flat", bd=0, height=1, padx=12, cursor="hand2",
            bg=t["green"], fg="white", activebackground=t["green_dark"], activeforeground="white",
        )
        self.btn_cancel = tk.Button(
            bottom, text=_("Отмена"), command=self.destroy,
            font=("Segoe UI", 9, "bold"), relief="flat", bd=0, height=1, padx=12, cursor="hand2",
            bg=t["red"], fg="white", activebackground=t["red_dark"], activeforeground="white",
        )
        self.btn_save.pack(side="left", expand=True, fill="x", padx=(6, 3))
        self.btn_cancel.pack(side="left", expand=True, fill="x", padx=(3, 6))

        # крестик закрытия на корпусе картриджа (справа сверху, в выемке)
        close_x = x1 - 15
        close_y = y0 - 65
        close_id = self.canvas.create_text(
            close_x, close_y, text="✕", font=("Arial Black", 18, "bold"),
            fill=t["text"], activefill=t["red"],
        )
        self.canvas.tag_bind(close_id, "<Button-1>", lambda event: self.destroy())
        self.canvas.tag_bind(close_id, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(close_id, "<Leave>", lambda e: self.canvas.config(cursor=""))

    # ---------- карточки ----------
    def _card(self, title, subtitle):
        t = self.theme
        card = tk.Frame(self.list_inner, bg=t["card_bg"], highlightthickness=1, highlightbackground=t["card_border"])
        card.pack(fill="x", padx=4, pady=4)

        info = tk.Frame(card, bg=t["card_bg"])
        info.pack(side="left", fill="x", expand=True, padx=(12, 6), pady=10)
        tk.Label(info, text=title, bg=t["card_bg"], fg=t["text"], font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(info, text=subtitle, bg=t["card_bg"], fg=t["muted"], font=("Segoe UI", 8)).pack(
            anchor="w", pady=(2, 0)
        )
        return card

    def _option_menu(self, parent, variable, values, command=None, width=12):
        t = self.theme
        menu = tk.OptionMenu(parent, variable, *values, command=command) if command else tk.OptionMenu(
            parent, variable, *values
        )
        menu.configure(
            bg=t["panel_bg"], fg=t["text"], activebackground=t["primary"], activeforeground="white",
            relief="flat", bd=0, highlightthickness=1, highlightbackground=t["card_border"],
            font=("Segoe UI", 9), padx=8, pady=2, cursor="hand2", anchor="w", width=width,
        )
        menu["menu"].configure(
            bg=t["panel_bg"], fg=t["text"], activebackground=t["primary"], activeforeground="white",
            font=("Segoe UI", 9), bd=0,
        )
        return menu

    def _build_list(self):
        self._add_autostart_card()
        self._add_theme_card()
        self._add_language_card()

    def _add_autostart_card(self):
        t = self.theme
        card = self._card(_("Добавить в автозагрузку"), _("Запускать MitaStickers при входе в Windows"))

        self.toggle = tk.Label(
            card, text=" ", width=3, height=1, font=("Segoe UI", 13, "bold"),
            bg=t["card_bg"], fg="white", cursor="hand2", highlightthickness=2,
            highlightbackground=t["muted"],
        )
        self.toggle.pack(side="right", padx=(6, 12))
        self.toggle.bind("<Button-1>", lambda event: self._toggle_autostart())
        self._update_toggle()

    def _add_theme_card(self):
        card = self._card(_("Тема"), _("Тема оформления"))

        self._theme_code_by_label = {_(source): code for code, source in THEME_LABELS.items()}
        labels = list(self._theme_code_by_label.keys())
        current_code = get_theme_name()
        current_label = next(
            (label for label, code in self._theme_code_by_label.items() if code == current_code),
            labels[0],
        )
        self.theme_var = tk.StringVar(value=current_label)
        menu = self._option_menu(card, self.theme_var, labels, command=self._on_theme_change, width=18)
        menu.pack(side="right", padx=(6, 12))

    def _add_language_card(self):
        card = self._card(_("Язык"), _("Язык интерфейса"))

        langs = i18n.available_languages()
        self._lang_code_by_label = {name: code for code, name in langs.items()}
        self.lang_var = tk.StringVar(value=langs.get(i18n.get_language(), langs["ru"]))
        menu = self._option_menu(card, self.lang_var, list(langs.values()), command=self._on_language_change, width=10)
        menu.pack(side="right", padx=(6, 12))

    def _toggle_autostart(self):
        self.autostart_enabled = not self.autostart_enabled
        self._update_toggle()

    def _update_toggle(self):
        t = self.theme
        if self.autostart_enabled:
            self.toggle.configure(text="\u2714", bg=t["green"], highlightbackground=t["green_dark"])
        else:
            self.toggle.configure(text=" ", bg=t["card_bg"], highlightbackground=t["muted"])

    def _on_theme_change(self, label):
        code = self._theme_code_by_label.get(label)
        if not code or code == get_theme_name():
            return
        set_theme(code)
        messagebox.showinfo(
            _("Тема"),
            _("Перезапустите приложение, чтобы применить тему."),
            parent=self,
        )
        root = self.root
        self.destroy()
        root.after(10, lambda: open_settings_window(root))

    def _on_language_change(self, label):
        code = self._lang_code_by_label.get(label)
        if not code or code == i18n.get_language():
            return
        i18n.set_language(code)
        messagebox.showinfo(
            _("Язык"),
            _("Перезапустите приложение, чтобы применить язык полностью."),
            parent=self,
        )
        root = self.root
        self.destroy()
        root.after(10, lambda: open_settings_window(root))

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

    # ---------- действия ----------
    def _save(self):
        try:
            if self.autostart_enabled:
                autostart.add_to_startup()
            else:
                autostart.remove_from_startup()
        except Exception:
            pass

        current = settings.load_settings()
        current["autostart"] = bool(self.autostart_enabled)
        settings.save_settings(current)
        self.destroy()

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

        image = tint_cartridge(image, self.theme.get("cartridge_tint"))

        key = tuple(int(CHROMA_KEY[i:i + 2], 16) for i in (1, 3, 5))
        key_image = Image.new("RGB", image.size, key)
        flat = Image.new("RGB", image.size, key)
        flat.paste(image, (0, 0), image)
        transparent = image.getchannel("A").point(lambda a: 255 if a < 200 else 0)
        flat.paste(key_image, (0, 0), transparent)
        return ImageTk.PhotoImage(flat)

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
