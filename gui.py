import tkinter as tk
from tkinter import ttk
import threading
import functools
from PIL import Image, ImageDraw, ImageTk
import config
import analyzer

BG = "#090708"
MAIN_SURF = "#131011"
SEC_SURF = "#191416"
HOVER_SURF = "#23171A"
BORDER = "#3A1118"
ACC_CRIMSON = "#B10F2E"
HOV_CRIMSON = "#CF1840"
PRS_CRIMSON = "#8D0C28"
SUCCESS = "#46B96B"
WARNING = "#D29A22"
ERROR_COLOR = "#D44B4B"
PRI_TEXT = "#F1E8EA"
SEC_TEXT = "#BDA9AE"
DIS_TEXT = "#6E5B5F"
SELECT = "#C01639"
CURSOR = "#FFFFFF"
ANIMATIONS_ENABLED = True


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    r, g, b = (max(0, min(255, round(c))) for c in rgb)
    return "#%02X%02X%02X" % (r, g, b)


def lerp_color(start, end, t):
    a = hex_to_rgb(start)
    b = hex_to_rgb(end)
    return rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def _quantize_color(value, step=6):
    if not value:
        return value
    r, g, b = hex_to_rgb(value)
    q = lambda c: min(255, (c // step) * step)
    return rgb_to_hex((q(r), q(g), q(b)))


@functools.lru_cache(maxsize=1024)
def _draw_rounded_rect(width, height, radius, fill, outline, outline_width, scale):
    w, h, r = width * scale, height * scale, radius * scale
    ow = outline_width * scale
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bounds = [ow / 2, ow / 2, w - 1 - ow / 2, h - 1 - ow / 2]
    if outline and outline_width:
        draw.rounded_rectangle(bounds, radius=r, fill=fill, outline=outline, width=int(ow))
    else:
        draw.rounded_rectangle(bounds, radius=r, fill=fill)
    return img.resize((width, height), Image.LANCZOS)


def rounded_rect_image(width, height, radius, fill, outline=None, outline_width=0, scale=2):
    width = max(int(round(width)), 2)
    height = max(int(round(height)), 2)
    radius = max(0, min(radius, width // 2, height // 2))
    fill_q = _quantize_color(fill)
    outline_q = _quantize_color(outline) if outline else outline
    img = _draw_rounded_rect(width, height, radius, fill_q, outline_q, outline_width, scale)
    return ImageTk.PhotoImage(img)


def animate(widget, start, end, apply_fn, duration, steps, on_done, token_attr, interpolate):
    if not ANIMATIONS_ENABLED:
        apply_fn(end)
        if on_done:
            on_done()
        return

    token = getattr(widget, token_attr, 0) + 1
    setattr(widget, token_attr, token)
    delay = max(10, duration // steps)

    def step(i):
        if getattr(widget, token_attr, None) != token:
            return
        if not widget.winfo_exists():
            return
        t = i / steps
        apply_fn(interpolate(start, end, t))
        if i < steps:
            widget.after(delay, lambda: step(i + 1))
        elif on_done:
            on_done()

    step(0)


def animate_color(widget, start, end, apply_fn, duration=110, steps=7, on_done=None,
                   token_attr="_anim_color"):
    animate(widget, start, end, apply_fn, duration, steps, on_done, token_attr, lerp_color)


def animate_value(widget, start, end, apply_fn, duration=140, steps=10, on_done=None,
                   token_attr="_anim_value"):
    def ease(a, b, t):
        eased = 1 - (1 - t) ** 3
        return a + (b - a) * eased

    animate(widget, start, end, apply_fn, duration, steps, on_done, token_attr, ease)


class RoundedSurface(tk.Frame):
    def __init__(self, parent, fill, radius=16, outline=None, outline_width=0, pad=0,
                 width=None, height=None):
        bg = parent.cget("bg")
        kwargs = {}
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        super().__init__(parent, bg=bg, highlightthickness=0, **kwargs)
        if width is not None or height is not None:
            self.pack_propagate(False)
            self.grid_propagate(False)

        self.fill = fill
        self.radius = radius
        self.outline = outline
        self.outline_width = outline_width
        self.pad = pad

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=fill, highlightthickness=0)
        self._img = None
        self._win = None
        self.canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        w, h = event.width, event.height
        if w < 4 or h < 4:
            return
        self._redraw(w, h)
        if self._win is None:
            self._win = self.canvas.create_window(self.pad, self.pad, anchor="nw",
                                                    window=self.body,
                                                    width=w - 2 * self.pad,
                                                    height=h - 2 * self.pad)
        else:
            self.canvas.coords(self._win, self.pad, self.pad)
            self.canvas.itemconfig(self._win, width=w - 2 * self.pad, height=h - 2 * self.pad)

    def _redraw(self, w, h):
        self._img = rounded_rect_image(w, h, self.radius, self.fill, self.outline,
                                        self.outline_width)
        self.canvas.delete("bg")
        self.canvas.create_image(0, 0, anchor="nw", image=self._img, tags="bg")
        self.canvas.tag_lower("bg")

    def set_fill(self, color):
        self.fill = color
        self.body.configure(bg=color)
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 4 and h > 4:
            self._redraw(w, h)


class RoundedButton(tk.Frame):
    def __init__(self, parent, text, width, height, command, bg, hover_bg, press_bg, fg,
                 font, radius=12, disabled_bg=None, disabled_fg=None):
        bg_parent = parent.cget("bg")
        super().__init__(parent, bg=bg_parent, highlightthickness=0, width=width, height=height)
        self.pack_propagate(False)
        self.grid_propagate(False)

        self.command = command
        self.width = width
        self.height = height
        self.radius = radius
        self.colors = {"normal": bg, "hover": hover_bg, "press": press_bg}
        self.fg_normal = fg
        self.disabled_bg = disabled_bg or SEC_SURF
        self.disabled_fg = disabled_fg or DIS_TEXT
        self.enabled = True
        self.current_bg = bg

        self.canvas = tk.Canvas(self, width=width, height=height, bg=bg_parent,
                                 highlightthickness=0, bd=0, cursor="hand2")
        self.canvas.place(x=0, y=0, width=width, height=height)
        self.text_id = self.canvas.create_text(width / 2, height / 2, text=text, fill=fg,
                                                font=font)
        self._draw(bg)

        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def _draw(self, color):
        img = rounded_rect_image(self.width, self.height, self.radius, color)
        self._img = img
        self.canvas.delete("bg")
        self.canvas.create_image(0, 0, anchor="nw", image=img, tags="bg")
        self.canvas.tag_lower("bg")
        self.current_bg = color

    def on_enter(self, event=None):
        if not self.enabled:
            return
        animate_color(self, self.current_bg, self.colors["hover"], self._draw)

    def on_leave(self, event=None):
        if not self.enabled:
            return
        animate_color(self, self.current_bg, self.colors["normal"], self._draw)

    def on_press(self, event=None):
        if not self.enabled:
            return
        animate_color(self, self.current_bg, self.colors["press"], self._draw, duration=80,
                      steps=6)

    def on_release(self, event=None):
        if not self.enabled:
            return
        animate_color(self, self.current_bg, self.colors["hover"], self._draw, duration=90,
                      steps=6)
        self.command()

    def set_text(self, text):
        self.canvas.itemconfig(self.text_id, text=text)

    def disable(self):
        self.enabled = False
        self.canvas.configure(cursor="arrow")
        animate_color(self, self.current_bg, self.disabled_bg, self._draw)
        self.canvas.itemconfig(self.text_id, fill=self.disabled_fg)

    def enable(self):
        self.enabled = True
        self.canvas.configure(cursor="hand2")
        animate_color(self, self.current_bg, self.colors["normal"], self._draw)
        self.canvas.itemconfig(self.text_id, fill=self.fg_normal)


class SegmentedControl(tk.Frame):
    def __init__(self, parent, options, default, command, width=88, height=38, radius=10):
        bg_parent = parent.cget("bg")
        super().__init__(parent, bg=bg_parent, highlightthickness=0)
        self.command = command
        self.current = default
        self.segments = {}

        for i, opt in enumerate(options):
            btn = RoundedButton(self, opt, width, height, lambda o=opt: self.select(o),
                                SEC_SURF, HOVER_SURF, HOVER_SURF, SEC_TEXT,
                                ("Segoe UI Semibold", 10), radius=radius)
            btn.grid(row=0, column=i, padx=(0, 6) if i < len(options) - 1 else 0)
            self.segments[opt] = btn

        self.update_ui(animate=False)

    def select(self, opt):
        if opt == self.current:
            return
        self.current = opt
        self.update_ui(animate=True)
        self.command(opt)

    def update_ui(self, animate=True):
        for opt, btn in self.segments.items():
            selected = opt == self.current
            target_bg = ACC_CRIMSON if selected else SEC_SURF
            target_fg = PRI_TEXT if selected else SEC_TEXT
            btn.colors["normal"] = target_bg
            btn.colors["hover"] = HOV_CRIMSON if selected else HOVER_SURF
            btn.colors["press"] = PRS_CRIMSON if selected else HOVER_SURF
            btn.fg_normal = target_fg
            if animate:
                animate_color(btn, btn.current_bg, target_bg, btn._draw)
            else:
                btn._draw(target_bg)
            btn.canvas.itemconfig(btn.text_id, fill=target_fg)


class ToggleSwitch(tk.Frame):
    def __init__(self, parent, initial=False, command=None, width=46, height=24):
        bg_parent = parent.cget("bg")
        super().__init__(parent, bg=bg_parent, highlightthickness=0, width=width, height=height)
        self.pack_propagate(False)
        self.command = command
        self.state = initial
        self.width = width
        self.height = height
        self.thumb_d = height - 6
        self.track_color = ACC_CRIMSON if initial else SEC_SURF

        self.canvas = tk.Canvas(self, width=width, height=height, bg=bg_parent,
                                 highlightthickness=0, bd=0, cursor="hand2")
        self.canvas.place(x=0, y=0)
        self.thumb_img = rounded_rect_image(self.thumb_d, self.thumb_d, self.thumb_d // 2,
                                            "#FFFFFF")
        self._draw_track(self.track_color)
        x = width - self.thumb_d - 3 if initial else 3
        self.thumb_id = self.canvas.create_image(x, height / 2, anchor="w", image=self.thumb_img)

        self.canvas.bind("<Button-1>", self.toggle)

    def _draw_track(self, color):
        self.track_color = color
        img = rounded_rect_image(self.width, self.height, self.height // 2, color)
        self._track_img = img
        self.canvas.delete("track")
        self.canvas.create_image(0, 0, anchor="nw", image=img, tags="track")
        self.canvas.tag_lower("track")

    def toggle(self, event=None):
        self.state = not self.state
        self._apply(animate=True)
        if self.command:
            self.command(self.state)

    def _apply(self, animate):
        target_track = ACC_CRIMSON if self.state else SEC_SURF
        target_x = self.width - self.thumb_d - 3 if self.state else 3
        if animate:
            animate_color(self, self.track_color, target_track, self._draw_track,
                          token_attr="_anim_track")
            current_x = self.canvas.coords(self.thumb_id)[0]
            animate_value(self, current_x, target_x,
                          lambda v: self.canvas.coords(self.thumb_id, v, self.height / 2),
                          token_attr="_anim_thumb")
        else:
            self._draw_track(target_track)
            self.canvas.coords(self.thumb_id, target_x, self.height / 2)

    def get(self):
        return self.state

    def set(self, value):
        self.state = value
        self._apply(animate=False)


class StatusBadge(tk.Frame):
    def __init__(self, parent, width=150, height=34, radius=17):
        bg_parent = parent.cget("bg")
        super().__init__(parent, bg=bg_parent, highlightthickness=0, width=width, height=height)
        self.pack_propagate(False)
        self.width = width
        self.height = height
        self.radius = radius
        self.idle_color = bg_parent
        self.canvas = tk.Canvas(self, width=width, height=height, bg=bg_parent,
                                 highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0)
        self.current_bg = bg_parent
        self.text_id = self.canvas.create_text(width / 2, height / 2, text="",
                                                fill=bg_parent, font=("Segoe UI Semibold", 10))
        self._draw(self.idle_color)

    def _draw(self, color):
        img = rounded_rect_image(self.width, self.height, self.radius, color)
        self._img = img
        self.canvas.delete("bg")
        self.canvas.create_image(0, 0, anchor="nw", image=img, tags="bg")
        self.canvas.tag_lower("bg")
        self.canvas.tag_raise(self.text_id)
        self.current_bg = color

    def show(self, text, bg_color, fg_color):
        self.canvas.itemconfig(self.text_id, text=text)
        animate_color(self, self.current_bg, bg_color, self._draw, token_attr="_anim_bg")
        current_fg = self.canvas.itemcget(self.text_id, "fill")
        animate_color(self, current_fg, fg_color,
                      lambda c: self.canvas.itemconfig(self.text_id, fill=c),
                      token_attr="_anim_fg")

    def hide(self):
        animate_color(self, self.current_bg, self.idle_color, self._draw, token_attr="_anim_bg")
        current_fg = self.canvas.itemcget(self.text_id, "fill")
        animate_color(self, current_fg, self.idle_color,
                      lambda c: self.canvas.itemconfig(self.text_id, fill=c),
                      token_attr="_anim_fg",
                      on_done=lambda: self.canvas.itemconfig(self.text_id, text=""))


class TabButton(RoundedSurface):
    def __init__(self, parent, text, on_click, width=150, height=40):
        super().__init__(parent, SEC_SURF, radius=12, width=width, height=height)
        self.on_click = on_click
        self.selected = False
        self.label = tk.Label(self.body, text=text, font=("Segoe UI Semibold", 10),
                              bg=SEC_SURF, fg=SEC_TEXT, cursor="hand2")
        self.label.pack(expand=True, fill="both", padx=20, pady=8)

        self.canvas.configure(cursor="hand2")
        self.body.configure(cursor="hand2")
        for widget in (self.canvas, self.body, self.label):
            widget.bind("<Button-1>", self._click)
            widget.bind("<Enter>", self._enter)
            widget.bind("<Leave>", self._leave)

    def _click(self, event):
        self.on_click()

    def _enter(self, event):
        if self.selected:
            return
        animate_color(self, self.fill, HOVER_SURF, self.set_fill, token_attr="_anim_bg")

    def _leave(self, event):
        if self.selected:
            return
        animate_color(self, self.fill, SEC_SURF, self.set_fill, token_attr="_anim_bg")

    def set_fill(self, color):
        super().set_fill(color)
        self.label.configure(bg=color)

    def set_text(self, text):
        self.label.configure(text=text)

    def set_selected(self, selected, animate=True):
        self.selected = selected
        target_bg = ACC_CRIMSON if selected else SEC_SURF
        target_fg = PRI_TEXT if selected else SEC_TEXT
        if animate:
            animate_color(self, self.fill, target_bg, self.set_fill, token_attr="_anim_bg")
            animate_color(self, self.label.cget("fg"), target_fg,
                          lambda c: self.label.configure(fg=c), token_attr="_anim_fg")
        else:
            self.set_fill(target_bg)
            self.label.configure(fg=target_fg)


class TabSwitcher(tk.Frame):
    def __init__(self, parent, names, panes, default, on_select):
        bg_parent = parent.cget("bg")
        super().__init__(parent, bg=bg_parent, highlightthickness=0, height=44)
        self.pack_propagate(False)
        self.names = names
        self.panes = panes
        self.current = default
        self.on_select = on_select
        self.labels = {name: name for name in names}
        self.buttons = {}

        self.bar = tk.Frame(self, bg=bg_parent, highlightthickness=0)
        self.bar.pack(fill="x")

        for index, name in enumerate(names):
            btn = TabButton(self.bar, name.upper(), lambda n=name: self.select(n))
            btn.pack(side="left", padx=(0, 10) if index < len(names) - 1 else 0)
            self.buttons[name] = btn

        self._update_display()

    def select(self, name):
        if name == self.current:
            return
        self.current = name
        self._update_display()
        self.on_select(name)

    def set_text(self, name, text):
        self.labels[name] = text
        self.buttons[name].set_text(text.upper())

    def _update_display(self):
        for name, btn in self.buttons.items():
            btn.set_selected(name == self.current, animate=False)
            btn.set_text(self.labels[name].upper())


class CrimsonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Crimson CDA")
        self.root.configure(bg=BG)
        self.root.minsize(1050, 700)
        self.root.option_add("*tearOff", False)
        self.center_window(1280, 820)

        self.current_mode = getattr(config, 'mode', 'api').upper()
        if self.current_mode not in ("LOCAL", "API"):
            self.current_mode = "API"

        self.analysis_running = False
        self.current_tab = "Source"
        self.animations_enabled = True
        self.auto_scroll_output = True
        self.editor_font_size = 11
        self.model_architecture = "Standard"
        self.api_timeout = 60
        self.theme_name = "Dark Crimson"
        self.settings_widgets = {}
        self.setup_styles()
        self.build_ui()

    def center_window(self, width, height):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = int((sw / 2) - (width / 2))
        y = int((sh / 2) - (height / 2))
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("Crimson.TCombobox",
                        fieldbackground=MAIN_SURF,
                        background=SEC_SURF,
                        foreground=PRI_TEXT,
                        arrowcolor=SEC_TEXT,
                        bordercolor=BORDER,
                        selectbackground=SELECT,
                        selectforeground=PRI_TEXT,
                        insertcolor=CURSOR,
                        relief="flat")
        style.map("Crimson.TCombobox",
                  fieldbackground=[("readonly", MAIN_SURF)],
                  background=[("active", HOVER_SURF), ("readonly", SEC_SURF)],
                  arrowcolor=[("active", PRI_TEXT)])

        style.configure("Vertical.TScrollbar",
                        background=SEC_SURF,
                        troughcolor=MAIN_SURF,
                        bordercolor=MAIN_SURF,
                        arrowcolor=SEC_TEXT,
                        relief="flat",
                        borderwidth=0,
                        highlightthickness=0)
        style.map("Vertical.TScrollbar",
                  background=[("active", HOVER_SURF)],
                  arrowcolor=[("active", PRI_TEXT)])

        style.configure("Horizontal.TScrollbar",
                        background=SEC_SURF,
                        troughcolor=MAIN_SURF,
                        bordercolor=MAIN_SURF,
                        arrowcolor=SEC_TEXT,
                        relief="flat",
                        borderwidth=0,
                        highlightthickness=0)
        style.map("Horizontal.TScrollbar",
                  background=[("active", HOVER_SURF)],
                  arrowcolor=[("active", PRI_TEXT)])

        self.root.option_add("*TCombobox*Listbox.background", MAIN_SURF)
        self.root.option_add("*TCombobox*Listbox.foreground", PRI_TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", SELECT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", PRI_TEXT)
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))

    def create_text_editor(self, parent, wrap="none", line_numbers=False, read_only=False,
                           radius=14):
        surface = RoundedSurface(parent, MAIN_SURF, radius=radius, outline=BORDER,
                                 outline_width=1, pad=2)
        body = surface.body

        line_nums_widget = None
        editor_host = body

        if line_numbers:
            ln_frame = tk.Frame(body, bg=SEC_SURF, width=52, highlightthickness=0)
            ln_frame.pack(side="left", fill="y")
            ln_frame.pack_propagate(False)

            line_nums_widget = tk.Text(ln_frame, bg=SEC_SURF, fg=DIS_TEXT,
                                       font=("Consolas", 11), relief="flat", borderwidth=0,
                                       highlightthickness=0, padx=8, pady=16, wrap="none",
                                       width=4, cursor="arrow", state="disabled")
            line_nums_widget.pack(fill="both", expand=True)
            line_nums_widget.tag_configure("right", justify="right")
            line_nums_widget.tag_add("right", "1.0", "end")

            editor_host = tk.Frame(body, bg=MAIN_SURF, highlightthickness=0)
            editor_host.pack(side="left", fill="both", expand=True)

        v_scroll = ttk.Scrollbar(body, orient="vertical")
        v_scroll.pack(side="right", fill="y")

        h_scroll_frame = tk.Frame(editor_host, bg=MAIN_SURF, highlightthickness=0)
        h_scroll_frame.pack(side="bottom", fill="x")

        txt = tk.Text(editor_host, bg=MAIN_SURF, fg=PRI_TEXT, font=("Consolas", 11),
                      insertbackground=CURSOR, selectbackground=SELECT,
                      selectforeground=PRI_TEXT, relief="flat", borderwidth=0,
                      highlightthickness=0, padx=16, pady=16, undo=True, wrap=wrap)
        txt.pack(side="left", fill="both", expand=True)

        if wrap == "none":
            h_scroll = ttk.Scrollbar(h_scroll_frame, orient="horizontal")
            h_scroll.pack(fill="x")
            txt.configure(xscrollcommand=h_scroll.set)
            h_scroll.configure(command=txt.xview)
        else:
            h_scroll_frame.pack_forget()

        if line_numbers and line_nums_widget is not None:
            def sync_scroll(*args):
                v_scroll.set(*args)
                line_nums_widget.yview_moveto(args[0])

            txt.configure(yscrollcommand=sync_scroll)
            v_scroll.configure(command=txt.yview)

            def on_mousewheel(event):
                if txt.winfo_exists():
                    txt.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"

            txt.bind("<MouseWheel>", on_mousewheel)
        else:
            txt.configure(yscrollcommand=v_scroll.set)
            v_scroll.configure(command=txt.yview)

        if read_only:
            txt.configure(state="disabled")

        return surface, txt, line_nums_widget

    def build_ui(self):
        self.outer_pad = tk.Frame(self.root, bg=BG, highlightthickness=0)
        self.outer_pad.pack(fill="both", expand=True, padx=28, pady=28)

        self.card = RoundedSurface(self.outer_pad, MAIN_SURF, radius=22, outline=BORDER,
                                   outline_width=2, pad=2)
        self.card.pack(fill="both", expand=True)

        self.content = tk.Frame(self.card.body, bg=MAIN_SURF, highlightthickness=0)
        self.content.pack(fill="both", expand=True, padx=22, pady=20)

        self.build_header(self.content)
        self.build_notebook(self.content)
        self.build_footer(self.content)

    def build_header(self, parent):
        self.header = tk.Frame(parent, bg=MAIN_SURF, height=60, highlightthickness=0)
        self.header.pack(fill="x", pady=(0, 18))
        self.header.pack_propagate(False)

        self.header.grid_columnconfigure(0, weight=0)
        self.header.grid_columnconfigure(1, weight=1)
        self.header.grid_columnconfigure(2, weight=0)
        self.header.grid_rowconfigure(0, weight=1)

        spacer = tk.Frame(self.header, bg=MAIN_SURF, width=150, height=1)
        spacer.grid(row=0, column=0)

        title = tk.Label(self.header, text="CRIMSON CDA", font=("Segoe UI", 23, "bold"),
                         bg=MAIN_SURF, fg=PRI_TEXT)
        title.grid(row=0, column=1)

        self.badge = StatusBadge(self.header, width=150, height=34)
        self.badge.grid(row=0, column=2, sticky="e")

    def build_notebook(self, parent):
        self.content_container = tk.Frame(parent, bg=MAIN_SURF, highlightthickness=0)
        self.content_container.pack(fill="both", expand=True)

        self.tab_source = tk.Frame(self.content_container, bg=BG, highlightthickness=0)
        self.tab_diag = tk.Frame(self.content_container, bg=BG, highlightthickness=0)
        self.tab_sett = tk.Frame(self.content_container, bg=BG, highlightthickness=0)

        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        panes = {"Source": self.tab_source, "Diagnosis": self.tab_diag,
                 "Settings": self.tab_sett}
        self.tabs = TabSwitcher(parent, ["Source", "Diagnosis", "Settings"], panes,
                                "Source", self.show_tab)
        self.tabs.pack(fill="x", pady=(0, 12))

        for name in panes:
            panes[name].grid(row=0, column=0, sticky="nsew")

        self.build_source_tab()
        self.build_diagnosis_tab()
        self.build_settings_tab()
        self.show_tab("Source")

    def build_source_tab(self):
        container = tk.Frame(self.tab_source, bg=BG, highlightthickness=0)
        container.pack(fill="both", expand=True)

        editor_frame, self.source_editor, self.line_numbers = self.create_text_editor(
            container, wrap="none", line_numbers=True
        )
        editor_frame.pack(fill="both", expand=True)

        self.update_line_numbers()
        self.source_editor.bind("<<Modified>>", lambda e: (
            self.source_editor.edit_modified(False),
            self.update_line_numbers()
        ))

        toolbar = tk.Frame(container, bg=BG, height=56, highlightthickness=0)
        toolbar.pack(fill="x", pady=(16, 0))
        toolbar.pack_propagate(False)

        left_section = tk.Frame(toolbar, bg=BG, highlightthickness=0)
        left_section.pack(side="left", fill="y")

        tk.Label(left_section, text="EXECUTION MODE", font=("Segoe UI Semibold", 10),
                 bg=BG, fg=SEC_TEXT).pack(side="left", padx=(0, 18))

        self.mode_control = SegmentedControl(left_section, ["API", "LOCAL"],
                                             self.current_mode, self.change_mode)
        self.mode_control.pack(side="left")

        divider = tk.Frame(toolbar, bg=BORDER, width=1, highlightthickness=0)
        divider.pack(side="left", fill="y", padx=24)

        self.btn_execute = RoundedButton(toolbar, "EXECUTE", 180, 44, self.start_analysis,
                                         ACC_CRIMSON, HOV_CRIMSON, PRS_CRIMSON, PRI_TEXT,
                                         ("Segoe UI Semibold", 11), radius=12)
        self.btn_execute.pack(side="right")

    def build_diagnosis_tab(self):
        container = tk.Frame(self.tab_diag, bg=BG, highlightthickness=0)
        container.pack(fill="both", expand=True)

        container.grid_rowconfigure(0, weight=0)
        container.grid_rowconfigure(1, weight=35)
        container.grid_rowconfigure(2, weight=0)
        container.grid_rowconfigure(3, weight=65)
        container.grid_columnconfigure(0, weight=1)

        trace_label = tk.Label(container, text="Traceback", font=("Segoe UI Semibold", 12),
                               bg=BG, fg=PRI_TEXT)
        trace_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        trace_frame, self.trace_editor, _ = self.create_text_editor(container, wrap="word")
        trace_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))

        diag_label = tk.Label(container, text="Diagnosis Output", font=("Segoe UI Semibold", 12),
                              bg=BG, fg=PRI_TEXT)
        diag_label.grid(row=2, column=0, sticky="w", pady=(0, 8))

        diag_frame, self.diag_editor, _ = self.create_text_editor(container, wrap="word",
                                                                    read_only=True)
        diag_frame.grid(row=3, column=0, sticky="nsew")

    def build_settings_tab(self):
        container = tk.Frame(self.tab_sett, bg=BG, highlightthickness=0)
        container.pack(fill="both", expand=True)

        panel = RoundedSurface(container, MAIN_SURF, radius=18, outline=BORDER,
                               outline_width=1, pad=2)
        panel.pack(fill="both", expand=True)

        content = tk.Frame(panel.body, bg=MAIN_SURF, highlightthickness=0)
        content.pack(fill="both", expand=True, padx=34, pady=28)

        settings_groups = [
            ("Interface", [
                ("UI Theme", "dropdown", ["Dark Crimson", "Pure Dark", "Charcoal"]),
                ("Editor Font Size", "dropdown", ["10", "11", "12", "13", "14"]),
                ("Word Wrap (Source)", "toggle", False),
                ("UI Animations", "toggle", True),
            ]),
            ("Behavior", [
                ("Auto-scroll Output", "toggle", True),
                ("Model Architecture", "dropdown", ["Standard", "Advanced", "Legacy"]),
            ]),
            ("Connection", [
                ("API Timeout (s)", "entry", "60"),
            ]),
        ]

        self.settings_widgets = {}

        for group_index, (group_name, rows) in enumerate(settings_groups):
            group_label = tk.Label(content, text=group_name.upper(),
                                   font=("Segoe UI Semibold", 10), bg=MAIN_SURF, fg=ACC_CRIMSON)
            group_label.pack(fill="x", pady=(0 if group_index == 0 else 18, 12))

            divider = tk.Frame(content, bg=BORDER, height=1, highlightthickness=0)
            divider.pack(fill="x", pady=(0, 16))

            for label_text, ctrl_type, ctrl_value in rows:
                row_frame = tk.Frame(content, bg=MAIN_SURF, highlightthickness=0)
                row_frame.pack(fill="x", pady=(0, 18))

                tk.Label(row_frame, text=label_text, font=("Segoe UI", 11), bg=MAIN_SURF,
                         fg=PRI_TEXT).pack(side="left")

                if ctrl_type == "toggle":
                    toggle = ToggleSwitch(row_frame, initial=ctrl_value,
                                          command=lambda s, name=label_text: self.setting_changed(
                                              name, s))
                    toggle.pack(side="right")
                    self.settings_widgets[label_text] = toggle

                elif ctrl_type == "dropdown":
                    var = tk.StringVar(value=ctrl_value[0])
                    combo = ttk.Combobox(row_frame, textvariable=var, values=ctrl_value,
                                         state="readonly", width=20, style="Crimson.TCombobox",
                                         font=("Segoe UI", 10))
                    combo.pack(side="right")
                    combo.bind("<<ComboboxSelected>>",
                              lambda e, name=label_text, v=var: self.setting_changed(name, v.get()))
                    self.settings_widgets[label_text] = var

                elif ctrl_type == "entry":
                    entry_surface = RoundedSurface(row_frame, MAIN_SURF, radius=8, outline=BORDER,
                                                   outline_width=1, pad=1, width=130, height=38)
                    entry_surface.pack(side="right")
                    entry = tk.Entry(entry_surface.body, bg=MAIN_SURF, fg=PRI_TEXT,
                                     insertbackground=CURSOR, relief="flat", borderwidth=0,
                                     highlightthickness=0, font=("Segoe UI", 10), justify="right")
                    entry.insert(0, ctrl_value)
                    entry.pack(fill="both", expand=True, padx=10, pady=6)
                    self.settings_widgets[label_text] = entry

        footer_row = tk.Frame(content, bg=MAIN_SURF, highlightthickness=0)
        footer_row.pack(fill="x", pady=(6, 0))
        tk.Label(footer_row, text="Settings are applied automatically", font=("Segoe UI", 9),
                 bg=MAIN_SURF, fg=DIS_TEXT).pack(side="right")

    def setting_changed(self, name, value):
        if name == "UI Theme":
            self.theme_name = value
            self.apply_theme(value)
        elif name == "Editor Font Size":
            self.editor_font_size = int(value)
            self.apply_editor_font()
        elif name == "Word Wrap (Source)":
            self.set_source_wrap(bool(value))
        elif name == "UI Animations":
            self.animations_enabled = bool(value)
            global ANIMATIONS_ENABLED
            ANIMATIONS_ENABLED = self.animations_enabled
        elif name == "Auto-scroll Output":
            self.auto_scroll_output = bool(value)
        elif name == "Model Architecture":
            self.model_architecture = value
        elif name == "API Timeout (s)":
            try:
                self.api_timeout = int(value)
            except ValueError:
                self.api_timeout = 60

    def build_footer(self, parent):
        self.footer = tk.Frame(parent, bg=MAIN_SURF, height=32, highlightthickness=0)
        self.footer.pack(fill="x", pady=(18, 0))
        self.footer.pack_propagate(False)

        tk.Label(self.footer, text="v2.0.0", font=("Segoe UI", 9), bg=MAIN_SURF,
                 fg=DIS_TEXT).pack(side="left")

        self.lbl_footer_mode = tk.Label(self.footer, text=f"MODE: {self.current_mode}",
                                        font=("Segoe UI Semibold", 9), bg=MAIN_SURF,
                                        fg=SEC_TEXT)
        self.lbl_footer_mode.pack(side="left", expand=True)

        tk.Label(self.footer, text="Crimson CDA", font=("Segoe UI", 9), bg=MAIN_SURF,
                 fg=DIS_TEXT).pack(side="right")

    def change_mode(self, mode):
        self.current_mode = mode
        self.lbl_footer_mode.configure(text=f"MODE: {mode}")

    def show_tab(self, name):
        self.current_tab = name
        self.tabs.panes[name].tkraise()

    def apply_theme(self, name):
        themes = {
            "Dark Crimson": {
                "BG": "#090708", "MAIN_SURF": "#131011", "SEC_SURF": "#191416",
                "HOVER_SURF": "#23171A", "BORDER": "#3A1118", "ACC_CRIMSON": "#B10F2E",
                "HOV_CRIMSON": "#CF1840", "PRS_CRIMSON": "#8D0C28", "SUCCESS": "#46B96B",
                "WARNING": "#D29A22", "ERROR_COLOR": "#D44B4B", "PRI_TEXT": "#F1E8EA",
                "SEC_TEXT": "#BDA9AE", "DIS_TEXT": "#6E5B5F", "SELECT": "#C01639",
                "CURSOR": "#FFFFFF"
            },
            "Pure Dark": {
                "BG": "#060606", "MAIN_SURF": "#101010", "SEC_SURF": "#171717",
                "HOVER_SURF": "#202020", "BORDER": "#2B2B2B", "ACC_CRIMSON": "#A6102B",
                "HOV_CRIMSON": "#B91532", "PRS_CRIMSON": "#851426", "SUCCESS": "#2E944D",
                "WARNING": "#C3921A", "ERROR_COLOR": "#B53A3A", "PRI_TEXT": "#ECECEC",
                "SEC_TEXT": "#B8B8B8", "DIS_TEXT": "#6C6C6C", "SELECT": "#B21435",
                "CURSOR": "#FFFFFF"
            },
            "Charcoal": {
                "BG": "#0A0C10", "MAIN_SURF": "#14171D", "SEC_SURF": "#1B2028",
                "HOVER_SURF": "#232831", "BORDER": "#303742", "ACC_CRIMSON": "#A91B35",
                "HOV_CRIMSON": "#BF203D", "PRS_CRIMSON": "#8C142A", "SUCCESS": "#3B9A5A",
                "WARNING": "#B98A1E", "ERROR_COLOR": "#C04A4A", "PRI_TEXT": "#F2F2F2",
                "SEC_TEXT": "#A8AEB8", "DIS_TEXT": "#6D7480", "SELECT": "#C31D3C",
                "CURSOR": "#FFFFFF"
            }
        }
        palette = themes.get(name, themes["Dark Crimson"])
        globals().update(palette)
        self.root.configure(bg=BG)
        if hasattr(self, "content"):
            self.content.configure(bg=MAIN_SURF)
        if hasattr(self, "header"):
            self.header.configure(bg=MAIN_SURF)
        if hasattr(self, "footer"):
            self.footer.configure(bg=MAIN_SURF)
        if hasattr(self, "card"):
            self.card.set_fill(MAIN_SURF)
        if hasattr(self, "source_editor"):
            self.apply_editor_font()
        self.setup_styles()

    def apply_editor_font(self):
        size = self.editor_font_size
        font = ("Consolas", size)
        for editor in (getattr(self, "source_editor", None), getattr(self, "trace_editor", None),
                      getattr(self, "diag_editor", None)):
            if editor is not None and editor.winfo_exists():
                editor.configure(font=font)
        if hasattr(self, "line_numbers") and self.line_numbers and self.line_numbers.winfo_exists():
            self.line_numbers.configure(font=font)

    def set_source_wrap(self, enabled):
        if hasattr(self, "source_editor") and self.source_editor.winfo_exists():
            self.source_editor.configure(wrap="word" if enabled else "none")

    def update_line_numbers(self, event=None):
        if not hasattr(self, 'line_numbers') or not self.line_numbers:
            return
        if not self.line_numbers.winfo_exists():
            return
        try:
            content = self.source_editor.get("1.0", "end-1c")
            line_count = content.count("\n") + 1
            self.line_numbers.configure(state="normal")
            self.line_numbers.delete("1.0", "end")
            lines_text = "\n".join(str(i) for i in range(1, line_count + 1))
            self.line_numbers.insert("1.0", lines_text)
            self.line_numbers.tag_add("right", "1.0", "end")
            self.line_numbers.configure(state="disabled")
        except tk.TclError:
            pass

    def start_analysis(self):
        if self.analysis_running:
            return
        self.analysis_running = True
        self.btn_execute.disable()
        self.badge.show("ANALYZING", ACC_CRIMSON, PRI_TEXT)
        self.tabs.set_text("Source", "Source ?")

        src = self.source_editor.get("1.0", "end-1c")
        trc = self.trace_editor.get("1.0", "end-1c")
        md = self.current_mode.lower()

        threading.Thread(target=self.run_thread, args=(src, trc, md), daemon=True).start()

    def run_thread(self, src, trc, md):
        self.root.after(350, lambda: self.tabs.set_text("Source", "Source !"))
        self.root.after(350, lambda: self.tabs.set_text("Diagnosis", "Diagnosis ?"))

        try:
            res = analyzer.check(src, trc, md)
        except Exception as e:
            self.root.after(0, lambda: self.finish_analysis_error(str(e)))
            return

        self.root.after(0, lambda: self.finish_analysis(res))

    def finish_analysis(self, res):
        self.tabs.set_text("Diagnosis", "Diagnosis !")
        self.badge.show("COMPLETE", SUCCESS, BG)

        self.diag_editor.configure(state="normal")
        self.diag_editor.delete("1.0", "end")
        self.diag_editor.insert("end", res)
        self.diag_editor.configure(state="disabled")
        if self.auto_scroll_output:
            self.diag_editor.see("end")

        self.btn_execute.enable()
        self.analysis_running = False
        self.root.after(2500, self.reset_ui)

    def finish_analysis_error(self, res):
        self.tabs.set_text("Diagnosis", "Diagnosis !")
        self.badge.show("ERROR", ERROR_COLOR, PRI_TEXT)

        self.diag_editor.configure(state="normal")
        self.diag_editor.delete("1.0", "end")
        self.diag_editor.insert("end", f"CRITICAL ERROR:\n{res}")
        self.diag_editor.configure(state="disabled")
        if self.auto_scroll_output:
            self.diag_editor.see("end")

        self.btn_execute.enable()
        self.analysis_running = False
        self.root.after(2500, self.reset_ui)

    def reset_ui(self):
        self.tabs.set_text("Source", "Source")
        self.tabs.set_text("Diagnosis", "Diagnosis")
        self.badge.hide()


def run():
    root = tk.Tk()
    CrimsonApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()
