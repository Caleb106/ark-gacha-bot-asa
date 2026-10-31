"""The desktop app: one fixed-size window, a sidebar, and three pages.

Read in this order - the file is laid out the same way:

    drawing helpers   draw_rounded_rect / draw_accent_strip and friends, the
                      canvas primitives every card is built out of
    reusable widgets  StatCard, ControlCard, SidebarButton, LegendChip, and
                      DashboardLogHandler (the bridge from logger.py)
    DashboardPage     bot control, live counts, the Event Log
    FormPage          shared scaffolding for the two form-shaped pages
    SettingsPage      settings.json behind a second category rail, autosaved
    SupportPage       versions, log paths, and the debug snapshot users paste
                      into Discord when reporting something
    UI                the window itself: sidebar plus the three pages

Things that will bite you if you don't know them:

  - CTk's automatic DPI scaling is turned off at import (see the note below
    ctk.deactivate_automatic_dpi_awareness). Every size in this file is a
    literal pixel, and font sizes are given negative so Tk reads them as
    pixels too rather than points.
  - The window is fixed-size and non-resizable, and the dashboard's column
    widths are computed once from that (CARD_W) instead of being left to
    Tk's grid - see the note above _CONTENT_W for what went wrong when they
    weren't.
  - Anywhere a card needs a rounded corner or an accent strip, it's drawn on
    a tk.Canvas rather than assembled from CTk widgets. The comments on
    StatCard and draw_accent_strip explain what CTk couldn't do here; both
    describe approaches that were tried and failed, so they're worth reading
    before "simplifying" either.
  - The three pages are stacked in one grid cell and swapped with tkraise(),
    so all three exist from startup - only one is drawn.

Colors and the font live in UI/theme.py; nothing here should hardcode a hex
value.
"""
import ctypes
import json
import logging
import os
import platform
import subprocess
import threading
import sys
import time
import tkinter as tk
import webbrowser
from datetime import datetime
import discord

import customtkinter as ctk
import PIL
from PIL import Image, ImageTk

from app_info import (
    APP_NAME, DISCORD_URL, GITHUB_URL, VERSION,
)
from logger.logger import LOG_PATH, PIPE_ENV, logger, relay_output
from settings import store as settings_store
from tools.format import format_count
from tools.recovery import CORRUPTED_DIR
from UI.resources import store as resources_store
from UI.station_editor import StationEditorMixin
from UI.cards import StatCard, draw_rounded_rect, draw_accent_strip
from UI.theme import (
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_BG, COLOR_BLUE, COLOR_BORDER,
    COLOR_CARD, COLOR_CARD_HOVER, COLOR_CRYSTAL, COLOR_CYAN,
    COLOR_ELECTRONICS, COLOR_GREEN, COLOR_METAL, COLOR_PASTE, COLOR_PEARL,
    COLOR_RAIL, COLOR_RED, COLOR_RED_HOVER, COLOR_ROW_ALT, COLOR_SIDEBAR,
    COLOR_SUBTEXT, COLOR_TEXT, COLOR_WARNING, FONT_FAMILY,
)

# Everything under UI/ (icons, resource art) is addressed relative to this
# file's own folder, so the app renders the same no matter which directory
# it's launched from.
UI_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# DİL DOSYASI YÜKLEYİCİ (TRANSLATION LOADER)
# ============================================================================
def load_language():
    try:
        current_settings = settings_store.load()
        app_lang = current_settings.get("language", "en")
    except Exception:
        app_lang = "en"

    if app_lang == "en":
        return {}

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lang_path = os.path.join(base_dir, 'languages', f'{app_lang}.json')
    try:
        with open(lang_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

lang = load_language()
'''
if "info" in lang and "translator" in lang["info"]:
    print(f"Arayüz Çevirisi Yüklendi. Çevirmen: {lang['info']['translator']}")
elif not lang:
    print("Arayüz Dili: İngilizce (Varsayılan)")
'''
def _t(group, key):
    """Yardımcı çeviri fonksiyonu: group dan key e karşılık gelen metni döner, bulamazsa orijinalini verir."""
    return lang.get(group, {}).get(key, key)
# ============================================================================


def asset(*parts):
    """Absolute path to a file inside the UI/ folder."""
    return os.path.join(UI_DIR, *parts)

ctk.deactivate_automatic_dpi_awareness()
ctk.set_widget_scaling(1.0)
ctk.set_window_scaling(1.0)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

WINDOW_W, WINDOW_H = 1280, 800
SIDEBAR_W = 220
SETTINGS_RAIL_W = 175
CONTENT_PADX = 28
CARD_H = 116
CARD_GAP = 16
STAT_ROW_H = 56

_CONTENT_W = WINDOW_W - SIDEBAR_W - 2 * CONTENT_PADX
CARD_W = (_CONTENT_W - 2 * CARD_GAP) // 3

EVENT_COLORS = {
    "DEBUG": COLOR_SUBTEXT,
    "INFO": COLOR_BLUE,
    "WARNING": COLOR_WARNING,
    "ERROR": COLOR_RED,
    "CRITICAL": COLOR_ACCENT,
}
EVENT_LABELS = {
    "DEBUG": _t("dashboard", "Debug"),
    "INFO": _t("dashboard", "Info"),
    "WARNING": _t("dashboard", "Warning"),
    "ERROR": _t("dashboard", "Error"),
    "CRITICAL": _t("dashboard", "Critical"),
}

def _lerp_color(c1, c2, t):
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def load_icon(path, size, tint=None):
    img = Image.open(path).convert("RGBA")
    if tint:
        rgb = (int(tint[1:3], 16), int(tint[3:5], 16), int(tint[5:7], 16))
        solid = Image.new("RGBA", img.size, rgb + (255,))
        solid.putalpha(img.getchannel("A"))
        img = solid
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


def draw_shadow_divider(master, width, bg_color, line_color=COLOR_BORDER, fade=3):
    canvas = tk.Canvas(master, width=width, height=fade + 1, bg=bg_color, highlightthickness=0)
    canvas.create_rectangle(0, 0, width, 1, fill=line_color, outline=line_color)
    for i in range(fade):
        t = ((i + 1) / fade) ** 2
        color = _lerp_color(line_color, bg_color, t)
        canvas.create_rectangle(0, i + 1, width, i + 2, fill=color, outline=color)
    return canvas


def draw_vertical_shadow_divider(master, height, bg_color, line_color=COLOR_BORDER, fade=3):
    canvas = tk.Canvas(master, width=fade + 1, height=height, bg=bg_color,
                        highlightthickness=0)
    canvas.create_rectangle(0, 0, 1, height, fill=line_color, outline=line_color)
    for i in range(fade):
        t = ((i + 1) / fade) ** 2
        color = _lerp_color(line_color, bg_color, t)
        canvas.create_rectangle(i + 1, 0, i + 2, height, fill=color, outline=color)
    return canvas


class ControlCard(ctk.CTkFrame):
    def __init__(self, master, on_toggle, height=CARD_H, **kwargs):
        super().__init__(master, fg_color="transparent", width=40, **kwargs)
        self.radius = 12
        self.bar_w = 5
        self.accent = COLOR_ACCENT

        self.canvas = tk.Canvas(self, width=40, height=height, bg=COLOR_BG,
                                 highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._redraw)

        self.toggle_button = ctk.CTkButton(
            self.canvas, text=_t("dashboard", "START BOT"), height=44, corner_radius=8,
            font=(FONT_FAMILY, 15, "bold"), fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER, command=on_toggle)

        self._runtime_text = f"\u25cf  00:00:00  {_t('dashboard', 'Runtime')}"
        self._runtime_color = COLOR_SUBTEXT

        self._placed = False
        self._button_window = None

    def _redraw(self, event=None):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 4 or h < 4:
            return
        self.canvas.delete("bg")
        draw_rounded_rect(self.canvas, 0, 0, w, h, self.radius, COLOR_CARD, tags="bg")
        draw_accent_strip(self.canvas, self.bar_w, self.radius, h, self.accent, tags="bg")

        pad = 18
        btn_width = max(120, w - pad * 2)
        btn_height = 44
        btn_center_y = pad + btn_height / 2
        if self._button_window is None:
            self._button_window = self.canvas.create_window(
                pad, btn_center_y, anchor="w", window=self.toggle_button,
                width=btn_width, height=btn_height)
        else:
            self.canvas.itemconfig(self._button_window, width=btn_width, height=btn_height)
            self.canvas.coords(self._button_window, pad, btn_center_y)

        if not self._placed:
            self.canvas.create_text(pad + 4, h * 0.78, anchor="w",
                                     text=self._runtime_text,
                                     font=(FONT_FAMILY, -14),
                                     fill=self._runtime_color, tags="runtime")
            self._placed = True
        else:
            self.canvas.tag_lower("bg")

    def set_running(self, running: bool):
        if running:
            self.toggle_button.configure(text=_t("dashboard", "STOP BOT"), fg_color=COLOR_ACCENT,
                                         hover_color=COLOR_ACCENT_HOVER)
        else:
            self.toggle_button.configure(text=_t("dashboard", "START BOT"), fg_color=COLOR_ACCENT,
                                         hover_color=COLOR_ACCENT_HOVER)
        self._redraw()

    def set_runtime(self, text, running: bool):
        dot_color = COLOR_GREEN if running else COLOR_SUBTEXT
        self._runtime_text = f"\u25cf  {text}  {_t('dashboard', 'Runtime')}"
        self._runtime_color = dot_color
        if self._placed:
            self.canvas.itemconfig("runtime", text=self._runtime_text, fill=dot_color)


class SidebarButton(ctk.CTkButton):
    def __init__(self, master, text, icon_path, command=None, header=False, **kwargs):
        self.header = header
        size = 24 if header else 20
        self._icon_rest = load_icon(icon_path, size,
                                     tint=COLOR_TEXT if header else COLOR_SUBTEXT)
        self._icon_active = load_icon(icon_path, size, tint="#ffffff")
        super().__init__(
            master,
            text=f"  {text}",
            image=self._icon_rest,
            compound="left",
            anchor="w",
            font=(FONT_FAMILY, 18, "bold") if header else (FONT_FAMILY, 16, "bold"),
            height=48 if header else 42,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_TEXT if header else COLOR_SUBTEXT,
            command=command,
            **kwargs,
        )

    def set_active(self, active: bool):
        if active:
            self.configure(fg_color=COLOR_ACCENT, text_color="white",
                           hover_color=COLOR_ACCENT, image=self._icon_active)
        else:
            self.configure(fg_color="transparent",
                           text_color=COLOR_TEXT if self.header else COLOR_SUBTEXT,
                           hover_color=COLOR_CARD_HOVER, image=self._icon_rest)


class LegendChip(ctk.CTkFrame):
    def __init__(self, master, label, color, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text="\u25cf", font=(FONT_FAMILY, 13), text_color=color
                     ).pack(side="left", padx=(0, 4))
        ctk.CTkLabel(self, text=label, font=(FONT_FAMILY, 13), text_color=COLOR_SUBTEXT
                     ).pack(side="left")


class DashboardLogHandler(logging.Handler):
    def __init__(self, dashboard):
        super().__init__()
        self.dashboard = dashboard

    def emit(self, record):
        self.dashboard.after(0, self.dashboard._log, record.levelname, self.format(record))


class DashboardPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=COLOR_BG)
        self.app = app
        self.running = False
        self.start_time = None
        self._log_index = 0
        self._stats_save_job = None
        self.process = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()

        self._tick_runtime()
        self._tick_stats_refresh()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 8))
        header.grid_columnconfigure(0, weight=1)

        # Sol taraf: Başlık ve Alt Başlık
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w")

        title = ctk.CTkLabel(title_frame, text=_t("menus", "Dashboard"), font=(FONT_FAMILY, 27, "bold"),
                              text_color=COLOR_TEXT)
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(title_frame, text=_t("dashboard", "Live overview of your bot"),
                                 font=(FONT_FAMILY, 15), text_color=COLOR_SUBTEXT)
        subtitle.pack(anchor="w", pady=(2, 0))

        # Sağ taraf: Dil Değiştirici Menü (OptionMenu)
        current_cfg = settings_store.load()
        current_lang = current_cfg.get("language", "en")

        lang_menu = ctk.CTkOptionMenu(
            header,
            values=["en", "tr", "cm"],
            width=85,
            height=32,
            font=(FONT_FAMILY, 14, "bold"),
            fg_color=COLOR_CARD,
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_HOVER,
            dropdown_fg_color=COLOR_CARD,
            command=self._change_language
        )
        lang_menu.set(current_lang)
        lang_menu.grid(row=0, column=1, sticky="e")

    def _change_language(self, new_lang):
        try:
            cfg = settings_store.load()
            if cfg.get("language") != new_lang:
                cfg["language"] = new_lang
                settings_store.save(cfg)
                logger.info(f"Language changed to {new_lang}. Restarting application...")
                
                # Uygulamayı otomatik olarak yeniden başlat
                python = sys.executable
                os.execl(python, python, *sys.argv)
        except Exception as e:
            logger.error(f"Failed to change language and restart: {e}")

    def _build_content(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=CONTENT_PADX, pady=(8, 24))
        for i in (0, 2, 4):
            content.grid_columnconfigure(i, weight=0, minsize=CARD_W)
        for i in (1, 3):
            content.grid_columnconfigure(i, weight=0, minsize=CARD_GAP)
        content.grid_rowconfigure(1, weight=1)

        self._build_summary_row(content)
        self._build_body(content)

    def _build_summary_row(self, content):
        self.control_card = ControlCard(content, self.toggle_bot)
        self.control_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.crystals_card = StatCard(content, _t("dashboard", "Crystals opened"), "0", accent=COLOR_CYAN,
                                       icon=asset("resources", "images", "gacha_crystal.png"))
        self.crystals_card.grid(row=0, column=2, sticky="ew", pady=(0, 8))

        self.dust_card = StatCard(content, _t("dashboard", "Dust Collected"), "0", accent=COLOR_CYAN,
                                   icon=asset("resources", "images", "element_dust.png"))
        self.dust_card.grid(row=0, column=4, sticky="ew", pady=(0, 8))

    def _build_body(self, content):
        log_panel = ctk.CTkFrame(content, fg_color=COLOR_CARD, corner_radius=12,
                                  border_width=1, border_color=COLOR_BORDER)
        log_panel.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        log_panel.grid_columnconfigure(0, weight=1)
        log_panel.grid_rowconfigure(2, weight=1)

        log_header = ctk.CTkFrame(log_panel, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 4))
        log_header.grid_columnconfigure(0, weight=1)

        log_title = ctk.CTkLabel(log_header, text=_t("dashboard", "Event Log"), font=(FONT_FAMILY, 17, "bold"),
                                  text_color=COLOR_TEXT, anchor="w")
        log_title.grid(row=0, column=0, sticky="w")

        legend = ctk.CTkFrame(log_header, fg_color="transparent")
        legend.grid(row=0, column=1, sticky="e")
        for i, (kind, label) in enumerate(EVENT_LABELS.items()):
            chip = LegendChip(legend, label, EVENT_COLORS[kind])
            chip.pack(side="left", padx=(10 if i else 0, 0))

        sep = ctk.CTkFrame(log_panel, fg_color=COLOR_BORDER, height=1)
        sep.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 8))

        self.log_box = ctk.CTkTextbox(
            log_panel, fg_color=COLOR_BG, text_color=COLOR_TEXT,
            font=("Consolas", 14), corner_radius=8, border_width=1,
            border_color=COLOR_BORDER, wrap="word", spacing1=2, spacing3=4)
        self.log_box.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.log_box.configure(state="disabled")

        for tag, color in EVENT_COLORS.items():
            self.log_box._textbox.tag_config(tag, foreground=color)
        self.log_box._textbox.tag_config("even", background=COLOR_ROW_ALT)
        self.log_box._textbox.tag_config("time", foreground=COLOR_SUBTEXT)

        logger.addHandler(DashboardLogHandler(self))
        logger.info("UI initialized.")

        stats_panel = ctk.CTkFrame(content, fg_color=COLOR_CARD, corner_radius=12,
                                    border_width=1, border_color=COLOR_BORDER)
        stats_panel.grid(row=1, column=4, sticky="nsew", pady=(8, 0))
        stats_panel.grid_columnconfigure(0, weight=1)
        stats_panel.grid_rowconfigure(1, weight=1)

        stats_title = ctk.CTkLabel(stats_panel, text=_t("dashboard", "Resources Farmed"),
                                    font=(FONT_FAMILY, 17, "bold"),
                                    text_color=COLOR_TEXT, anchor="w")
        stats_title.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 13))

        self._stats_body = ctk.CTkFrame(stats_panel, fg_color="transparent")
        self._stats_body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self._stats_body.grid_columnconfigure(0, weight=1)

        self.stat_cards = {}
        self._add_stat("black_pearls", _t("dashboard", "Black Pearls"),
                       asset("resources", "images", "black_pearls.png"), COLOR_PEARL)
        self._add_stat("metal_ingots", _t("dashboard", "Metal Ingots"),
                       asset("resources", "images", "metal_ingot.png"), COLOR_METAL)
        self._add_stat("flint", _t("dashboard", "Flint"),
                       asset("resources", "images", "flint.png"), COLOR_PASTE)
        self._add_stat("electronics", _t("dashboard", "Electronics"),
                       asset("resources", "images", "electronics.png"), COLOR_ELECTRONICS)
        self._add_stat("crystal", _t("dashboard", "Crystal"),
                       asset("resources", "images", "crystal.png"), COLOR_CRYSTAL)

        self.stat_cards["crystals_opened"] = self.crystals_card
        self.stat_cards["dust_collected"] = self.dust_card

        resources_store.on_start()
        self._stats = resources_store.load()
        for key, count in self._stats.items():
            self.stat_cards[key].set_count(count)

    def _add_stat(self, key, label, icon, accent):
        idx = len(self.stat_cards)
        row = idx * 2
        if idx:
            self._stats_body.grid_rowconfigure(row - 1, minsize=CARD_GAP)
        self._stats_body.grid_rowconfigure(row, weight=1, uniform="stats")
        card = StatCard(self._stats_body, label, "0", accent=accent, icon=icon,
                         height=STAT_ROW_H, fill=COLOR_BG, bg=COLOR_CARD,
                         icon_size=48, icon_pad=14, title_size=11, value_size=22)
        card.grid(row=row, column=0, sticky="nsew")
        self.stat_cards[key] = card

    STATS_SAVE_DELAY_MS = 1000

    def set_stat(self, key, value):
        if isinstance(value, (int, float)):
            self._stats[key] = int(value)
            self.stat_cards[key].set_count(value)
            if not self.running:
                self._schedule_stats_save()
        else:
            self.stat_cards[key].set_value(value)

    def _schedule_stats_save(self):
        if self._stats_save_job is None:
            self._stats_save_job = self.after(self.STATS_SAVE_DELAY_MS,
                                              self._save_stats)

    def _save_stats(self):
        self._stats_save_job = None
        resources_store.save(self._stats)

    def on_leave(self):
        if self._stats_save_job:
            self.after_cancel(self._stats_save_job)
            self._save_stats()

    def _log(self, level, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        row_tags = ("even",) if self._log_index % 2 == 0 else ()
        self._log_index += 1

        self.log_box.configure(state="normal")
        self.log_box.insert("end", "\u25cf ", (level,) + row_tags)
        self.log_box.insert("end", f"{timestamp}  ", ("time",) + row_tags)
        self.log_box.insert("end", f"{text}\n", (level,) + row_tags)
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def toggle_bot(self):
        if self.running:
            self._stop_bot()
        else:
            self._start_bot()

    def _start_bot(self):
        if self.process and self.process.poll() is None:
            logger.warning("Bot is already running.")
            return

        args = [sys.executable, "-u", "main_program.py"]
        if not settings_store.load().get("use_discord", True):
            args = [sys.executable, "-u", "task_manager.py"]
            logger.warning("Discord integration is disabled.")
        
        try:
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, PIPE_ENV: "1", "PYTHONIOENCODING": "utf-8"},
            )
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            return

        self.running = True
        self.start_time = time.time()
        self.control_card.set_running(True)
        logger.info("Bot has been started..")

        threading.Thread(target=self._read_output, daemon=True).start()

    def _stop_bot(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.running = False
            self.control_card.set_running(False)
            logger.info("Bot has been stopped.")

    def _read_output(self):
        process = self.process
        if process is None or process.stdout is None:
            return
        for line in process.stdout:
            relay_output(line.rstrip("\r\n"))

    def _tick_runtime(self):
        if self.running and self.start_time:
            elapsed = int(time.time() - self.start_time)
            h, rem = divmod(elapsed, 3600)
            m, s = divmod(rem, 60)
            self.control_card.set_runtime(f"{h:02d}:{m:02d}:{s:02d}", True)
        else:
            self.control_card.set_runtime("00:00:00", False)
        self.after(200, self._tick_runtime)

    STATS_REFRESH_MS = 2000
    def _tick_stats_refresh(self):
        fresh = resources_store.load()
        for key, value in fresh.items():
            if key in self.stat_cards and value != self._stats.get(key):
                self._stats[key] = value
                self.stat_cards[key].set_count(value)
        self.after(self.STATS_REFRESH_MS, self._tick_stats_refresh)


class FormPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=COLOR_BG)
        self.app = app
        self.grid_columnconfigure(0, weight=1)

    def _header(self, title, subtitle):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=CONTENT_PADX, pady=(24, 10))
        ctk.CTkLabel(header, text=title, font=(FONT_FAMILY, 27, "bold"),
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text=subtitle, font=(FONT_FAMILY, 15), text_color=COLOR_SUBTEXT
                     ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        return header

    def _card(self, column, icon, title, accent, status_list=None):
        card = ctk.CTkFrame(column, fg_color=COLOR_CARD, corner_radius=12,
                             border_width=1, border_color=COLOR_BORDER)
        card.grid(row=column.grid_size()[1], column=0, sticky="ew", pady=(0, CARD_GAP))
        card.grid_columnconfigure(1, weight=1)

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.grid(row=0, column=0, columnspan=4, sticky="ew", padx=16, pady=(14, 10))
        chip_bg = _lerp_color(accent, COLOR_CARD, 0.82)
        if icon.endswith(".png"):
            chip = ctk.CTkLabel(head, text="", image=load_icon(icon, 18, tint=accent),
                                 width=32, height=32, corner_radius=8, fg_color=chip_bg)
        else:
            chip = ctk.CTkLabel(head, text=icon, font=(FONT_FAMILY, 15, "bold"),
                                 width=32, height=32, corner_radius=8, text_color=accent,
                                 fg_color=chip_bg)
        chip.pack(side="left")
        ctk.CTkLabel(head, text=title, font=(FONT_FAMILY, 16, "bold"),
                     text_color=COLOR_TEXT).pack(side="left", padx=(10, 0))

        if status_list is not None:
            status = ctk.CTkLabel(head, text="", font=(FONT_FAMILY, 12, "bold"),
                                   height=26, corner_radius=8, fg_color=COLOR_BG)
            status.pack(side="right")
            status_list.append(status)

        sep = ctk.CTkFrame(card, fg_color=COLOR_BORDER, height=1)
        sep.grid(row=1, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 6))
        return card

    def _end_card(self, card):
        card.grid_rowconfigure(card.grid_size()[1], minsize=10)


class StationsPage(StationEditorMixin, FormPage):
    def __init__(self, master, app):
        super().__init__(master, app)
        self._init_editors()
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        divider = draw_vertical_shadow_divider(self, WINDOW_H, COLOR_RAIL)
        divider.grid(row=0, column=0, sticky="ns")

        rail = ctk.CTkFrame(self, fg_color=COLOR_RAIL, width=SETTINGS_RAIL_W,
                             corner_radius=0)
        rail.grid(row=0, column=1, sticky="nsw")
        rail.grid_propagate(False)

        ctk.CTkLabel(rail, text=_t("menus", "Stations"), font=(FONT_FAMILY, 18, "bold"),
                      text_color=COLOR_TEXT, anchor="w"
                      ).pack(side="top", fill="x", padx=22, pady=(28, 14))

        self._tabs = {}
        self._tab_pages = {}
        self._tab_icons = {}
        self._add_tab(rail, "pegos", "Pegos", asset("images", "pego.png"))
        self._add_tab(rail, "gachas", "Gachas", asset("images", "gacha.png"))
        self._add_tab(rail, "crafting", "Crafting", asset("images", "station.png"))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=2, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=CONTENT_PADX, pady=(24, 10))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=_t("menus", "Stations"), font=(FONT_FAMILY, 27, "bold"),
                      text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header,
                      text=_t("general", "Add or configure your stations \u2014 changes save automatically"),
                      font=(FONT_FAMILY, 15), text_color=COLOR_SUBTEXT
                      ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        body = ctk.CTkFrame(content, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=CONTENT_PADX, pady=(4, 24))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_station_tab(body, "pego", "Pegos", asset("images", "pego.png"))
        self._build_station_tab(body, "gacha", "Gachas", asset("images", "gacha.png"))
        self._build_crafting_tab(body, asset("images", "station.png"))
        self._show_tab("pegos")

    def _add_tab(self, rail, key, label, icon_path):
        icons = {"rest": load_icon(icon_path, 24, tint=COLOR_SUBTEXT),
                 "active": load_icon(icon_path, 24, tint="#ffffff")}
        btn = ctk.CTkButton(
            rail, text=f"  {label}", image=icons["rest"], compound="left",
            anchor="w", width=SETTINGS_RAIL_W - 20, height=40, corner_radius=8,
            font=(FONT_FAMILY, 14, "bold"),
            fg_color="transparent", hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_SUBTEXT, command=lambda: self._show_tab(key))
        btn.pack(side="top", fill="x", padx=10, pady=3)
        self._tabs[key] = btn
        self._tab_icons[key] = icons

    def _show_tab(self, key):
        for k, btn in self._tabs.items():
            active = k == key
            btn.configure(
                fg_color=COLOR_ACCENT if active else "transparent",
                text_color="white" if active else COLOR_SUBTEXT,
                hover_color=COLOR_ACCENT if active else COLOR_CARD_HOVER,
                image=self._tab_icons[k]["active" if active else "rest"])
        self._tab_pages[key].tkraise()


class SettingsPage(FormPage):
    AUTOSAVE_DELAY_MS = 600

    def __init__(self, master, app):
        super().__init__(master, app)
        self._cfg = settings_store.load()
        
        self._baseline = dict(self._cfg)
        self._fields = {}
        self._labels = {}
        self._status_labels = []
        self._save_job = None

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        divider = draw_vertical_shadow_divider(self, WINDOW_H, COLOR_RAIL)
        divider.grid(row=0, column=0, sticky="ns")

        rail = ctk.CTkFrame(self, fg_color=COLOR_RAIL, width=SETTINGS_RAIL_W,
                             corner_radius=0)
        rail.grid(row=0, column=1, sticky="nsw")
        rail.grid_propagate(False)

        ctk.CTkLabel(rail, text=_t("menus", "Settings"), font=(FONT_FAMILY, 18, "bold"),
                     text_color=COLOR_TEXT, anchor="w"
                     ).pack(side="top", fill="x", padx=22, pady=(28, 14))

        self._tabs = {}
        self._tab_pages = {}
        self._tab_icons = {}
        self._add_tab(rail, "discord", "Discord", asset("images", "discord_image.png"))
        self._add_tab(rail, "main", "Main Settings", asset("images", "settings.png"))
        self._add_tab(rail, "features", "Features", asset("images", "features.png"))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=2, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=CONTENT_PADX, pady=(24, 10))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=_t("menus", "Settings"), font=(FONT_FAMILY, 27, "bold"),
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header,
                     text=_t("general", "Configure how the bot behaves \u2014 changes save automatically"),
                     font=(FONT_FAMILY, 15), text_color=COLOR_SUBTEXT
                     ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        body = ctk.CTkFrame(content, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=CONTENT_PADX, pady=(4, 24))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        lhalf, rhalf = self._tab_page(body, "discord", asset("images", "discord_image.png"),
                                      "Discord", COLOR_ACCENT)
        self._switch_row(lhalf, _t("discord", "Use Discord"), "use_discord", COLOR_ACCENT)
        self._entry_row(lhalf, _t("discord", "Command Prefix"), "command_prefix")
        self._entry_row(rhalf, _t("discord", "Log Channel (Gacha)"), "log_channel_gacha")
        self._entry_row(rhalf, _t("discord", "Log Active Queue"), "log_active_queue")
        self._entry_row(rhalf, _t("discord", "Log Wait Queue"), "log_wait_queue")
        self._entry_row(lhalf, _t("discord", "Discord API Key"), "discord_api_key", show="*")

        lhalf, rhalf = self._tab_page(body, "main", asset("images", "settings.png"),
                                      "Main Settings", COLOR_ACCENT)

        self._entry_row(lhalf, _t("main_settings", "Server Number"), "server_number")
        self._entry_row(lhalf, _t("main_settings", "Lag Offset"), "lag_offset")
        self._entry_row(lhalf, _t("main_settings", "Station Yaw"), "station_yaw")
        self._entry_row(lhalf, _t("main_settings", "Render Pushout"), "render_pushout")
        self._entry_row(lhalf, _t("main_settings", "Replenish interval"), "replenish_interval")
        self._entry_row(lhalf, _t("main_settings", "Berry Type"), "berry_type")
        self._entry_row(lhalf, _t("main_settings", "Ledger amount"), "ledger_amount", validate=self._validate_digit_1_9)
        self._entry_row(lhalf, _t("main_settings", "Ledger gacha wait"), "ledger_gacha_wait")

        self._entry_row(rhalf, _t("main_settings", "Iguanadon"), "iguanadon")
        self._entry_row(rhalf, _t("main_settings", "Drop Off"), "drop_off")
        self._entry_row(rhalf, _t("main_settings", "Bed Spawn"), "bed_spawn")
        self._entry_row(rhalf, _t("main_settings", "Berry Station"), "berry_station")
        self._entry_row(rhalf, _t("main_settings", "Grindables"), "grindables")
        self._entry_row(rhalf, _t("main_settings", "Cargo Pickup"), "cargo_pickup")
        self._entry_row(rhalf, _t("main_settings", "OCR Path"), "ocr_path")

        lhalf, rhalf = self._tab_page(body, "features", asset("images", "features.png"),
                                      "Features", COLOR_ACCENT)

        self._switch_row(lhalf, _t("features", "External Berries"), "external_berry", COLOR_ACCENT)
        self._switch_row(lhalf, _t("features", "Seeds 230"), "seeds_230", COLOR_ACCENT)
        self._switch_row(lhalf, _t("features", "Side Crop Plot"), "side_crop_plot", COLOR_ACCENT)
        self._switch_row(lhalf, _t("features", "Y Trap Bot"), "y_trap_bot", COLOR_ACCENT)

        self._switch_row(rhalf, _t("features", "Singleplayer"), "singleplayer", COLOR_ACCENT)
        self._switch_row(rhalf, _t("features", "Cargo Ledger"), "cargo_ledger", COLOR_ACCENT)
        self._segmented_row(rhalf, _t("features", "Height Ele"), "height_ele", COLOR_ACCENT, ("2", "3"))
        self._segmented_row(rhalf, _t("features", "Height Grind"), "height_grind", COLOR_ACCENT, ("2", "3"))

        self._set_status("saved")
        self._show_tab("discord")

    def _add_tab(self, rail, key, label, icon_path):
        icons = {"rest": load_icon(icon_path, 24, tint=COLOR_SUBTEXT),
                 "active": load_icon(icon_path, 24, tint="#ffffff")}
        btn = ctk.CTkButton(
            rail, text=f"  {label}", image=icons["rest"], compound="left",
            anchor="w", width=SETTINGS_RAIL_W - 20, height=40, corner_radius=8,
            font=(FONT_FAMILY, 14, "bold"),
            fg_color="transparent", hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_SUBTEXT, command=lambda: self._show_tab(key))
        btn.pack(side="top", fill="x", padx=10, pady=3)
        self._tabs[key] = btn
        self._tab_icons[key] = icons

    def _show_tab(self, key):
        for k, btn in self._tabs.items():
            active = k == key
            btn.configure(
                fg_color=COLOR_ACCENT if active else "transparent",
                text_color="white" if active else COLOR_SUBTEXT,
                hover_color=COLOR_ACCENT if active else COLOR_CARD_HOVER,
                image=self._tab_icons[k]["active" if active else "rest"])
        self._tab_pages[key].tkraise()

    def _tab_page(self, body, key, icon, title, accent):
        page = ctk.CTkFrame(body, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        card = self._card(page, icon, title, accent, status_list=self._status_labels)
        card.grid_configure(row=0, sticky="nsew", pady=0)
        card.grid_columnconfigure((0, 1), weight=1, uniform=f"tab-{key}")
        halves = []
        for col, padx in ((0, (2, 8)), (1, (8, 2))):
            half = ctk.CTkFrame(card, fg_color="transparent")
            half.grid(row=2, column=col, sticky="new", padx=padx)
            half.grid_columnconfigure(1, weight=1)
            halves.append(half)
        self._tab_pages[key] = page
        return halves
    
    @staticmethod
    def _validate_digit_1_9(proposed):
        return proposed == "" or (len(proposed) == 1 and proposed in "123456789")
    
    def _entry_row(self, card, label, key, show=None, validate=None):
        row = card.grid_size()[1]
        ctk.CTkLabel(card, text=label, font=(FONT_FAMILY, 15), text_color=COLOR_TEXT,
                    anchor="w", width=160).grid(row=row, column=0, sticky="w",
                                                padx=(18, 10), pady=8)
        entry = ctk.CTkEntry(card, font=(FONT_FAMILY, 15), height=38, corner_radius=8,
                            fg_color=COLOR_BG, border_width=1,
                            border_color=COLOR_BORDER, show=show)
        if validate is not None:
            vcmd = (self.register(validate), "%P")
            entry.configure(validate="key", validatecommand=vcmd)
        entry.insert(0, str(self._cfg[key]))
        entry.grid(row=row, column=1, sticky="ew", padx=(0, 18), pady=8)
        entry.bind("<KeyRelease>", lambda _e: self._schedule_save())
        self._fields[key] = entry
        self._labels[key] = label

    def _switch_row(self, card, label, key, accent):
        row = card.grid_size()[1]
        ctk.CTkLabel(card, text=label, font=(FONT_FAMILY, 15), text_color=COLOR_TEXT,
                     anchor="w", width=160).grid(row=row, column=0, sticky="w",
                                                  padx=(18, 10), pady=8)
        switch = ctk.CTkSwitch(card, text="", width=48, switch_height=24,
                                switch_width=48, progress_color=accent,
                                button_color="#ffffff", command=self._on_toggle)
        if self._cfg[key]:
            switch.select()
        switch.grid(row=row, column=1, sticky="e", padx=(0, 18), pady=8)
        self._fields[key] = switch
        self._labels[key] = label

    def _segmented_row(self, card, label, key, accent, values):
        row = card.grid_size()[1]
        ctk.CTkLabel(card, text=label, font=(FONT_FAMILY, 15), text_color=COLOR_TEXT,
                     anchor="w", width=160).grid(row=row, column=0, sticky="w",
                                                  padx=(18, 10), pady=8)
        seg = ctk.CTkSegmentedButton(
            card, values=list(values), width=110, height=30,
            font=(FONT_FAMILY, 14, "bold"), corner_radius=8,
            fg_color=COLOR_BG, unselected_color=COLOR_BG,
            unselected_hover_color=COLOR_CARD_HOVER,
            selected_color=accent, selected_hover_color=accent,
            command=lambda _v: self._on_toggle())
        current = str(self._cfg.get(key, values[0]))
        seg.set(current if current in values else values[0])
        seg.grid(row=row, column=1, sticky="e", padx=(0, 18), pady=8)
        self._fields[key] = seg
        self._labels[key] = label

    def _set_status(self, kind):
        text, color = {
            "saved": (f"\u2713  {_t('general', 'All changes saved')}", COLOR_GREEN),
            "saving": ("\u25cf  Saving\u2026", COLOR_SUBTEXT),
            "invalid": ("\u2717  Invalid value \u2014 not saved", COLOR_RED),
        }[kind]
        for status in self._status_labels:
            status.configure(text=f"  {text}  ", text_color=color)

    def _schedule_save(self):
        if self._save_job:
            self.after_cancel(self._save_job)
        self._set_status("saving")
        self._save_job = self.after(self.AUTOSAVE_DELAY_MS, self._autosave)

    def _on_toggle(self):
        if self._save_job:
            self.after_cancel(self._save_job)
            self._save_job = None
        self._autosave()

    def _autosave(self):
        self._save_job = None
        invalid = []
        for key, widget in self._fields.items():
            field_type = settings_store.FIELD_TYPES.get(key)
            if field_type in (int, float):
                try:
                    field_type(widget.get())
                except ValueError:
                    invalid.append(key)
            if isinstance(widget, ctk.CTkEntry):
                widget.configure(
                    border_color=COLOR_RED if key in invalid else COLOR_BORDER)
        if invalid:
            self._set_status("invalid")
            return
        current = settings_store.load()
        current.update({k: w.get() for k, w in self._fields.items()})
        settings_store.save(current)
        self._set_status("saved")

    def _typed_values(self):
        out = {}
        for key, widget in self._fields.items():
            field_type = settings_store.FIELD_TYPES.get(key)
            try:
                out[key] = field_type(widget.get()) if field_type else widget.get()
            except ValueError:
                out[key] = self._baseline.get(key)
        return out

    def on_leave(self):
        if self._save_job:
            self.after_cancel(self._save_job)
            self._autosave()
        current = self._typed_values()
        for key, new in current.items():
            old = self._baseline.get(key)
            if new == old:
                continue
            if key == "discord_api_key":
                logger.info("Setting changed: Discord API Key updated (value hidden).")
            else:
                logger.info(f"Setting changed: {self._labels[key]}: {old!r} \u2192 {new!r}.")
        self._baseline = current


class SupportPage(FormPage):
    def __init__(self, master, app):
        super().__init__(master, app)
        self._header(_t("menus", "Support"), _t("support", "Diagnostics, logs, and ways to reach us"))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=CONTENT_PADX, pady=(8, 24))
        body.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        diag = self._card(body, asset("images", "logs.png"), _t("support", "Diagnostics & Logs"), COLOR_ACCENT)
        self._info_row(diag, _t("support", "App Version"), VERSION)
        self._info_row(diag, _t("support", "Log File Path"), LOG_PATH)
        buttons = [
            (_t("support", "Open Log File"), self._open_log_file),
            (_t("support", "Open Logs Folder"), self._open_log_folder),
            (_t("support", "Copy Debug Info"), self._copy_debug_info),
        ]
        if os.path.isdir(CORRUPTED_DIR) and os.listdir(CORRUPTED_DIR):
            buttons.append(("Open Corrupted Savefiles", self._open_corrupted_folder))
        btn_row = self._button_row(diag, buttons)
        self.diag_status = ctk.CTkLabel(btn_row, text="", font=(FONT_FAMILY, 13),
                                         text_color=COLOR_GREEN, anchor="w")
        self.diag_status.pack(side="left", padx=(14, 0))
        self._end_card(diag)

        contact = self._card(body, asset("images", "community.png"), _t("support", "Contact & Community"),
                             COLOR_ACCENT)
        self._link_row(contact, "Discord", DISCORD_URL)
        self._link_row(contact, "GitHub Repo", GITHUB_URL)
        self._info_row(contact, _t("support", "Bot Creator"), "Caleb106")
        self._info_row(contact, _t("support", "UI Creator"), "SwedishTerminator")
        self._info_row(contact, "Language support", "Turkish/Türkçe -> Tuncay_d | ")
        self._end_card(contact)

    def _info_row(self, card, label, value):
        row = card.grid_size()[1]
        ctk.CTkLabel(card, text=label, font=(FONT_FAMILY, 15), text_color=COLOR_TEXT,
                     anchor="w", width=160).grid(row=row, column=0, sticky="w",
                                                  padx=(18, 10), pady=8)
        ctk.CTkLabel(card, text=value, font=(FONT_FAMILY, 14), text_color=COLOR_SUBTEXT,
                     anchor="w").grid(row=row, column=1, columnspan=2, sticky="w",
                                       padx=(0, 18), pady=8)

    def _button_row(self, card, buttons):
        wrap = ctk.CTkFrame(card, fg_color="transparent")
        wrap.grid(row=card.grid_size()[1], column=0, columnspan=3, sticky="w",
                   padx=18, pady=(6, 4))
        for i, (text, command) in enumerate(buttons):
            btn = ctk.CTkButton(wrap, text=text, height=36, corner_radius=8,
                                 font=(FONT_FAMILY, 14, "bold"), fg_color=COLOR_CARD_HOVER,
                                 hover_color=COLOR_BORDER, text_color=COLOR_TEXT,
                                 command=command)
            btn.pack(side="left", padx=(0 if i == 0 else 10, 0))
        return wrap

    def _link_row(self, card, label, url):
        row = card.grid_size()[1]
        ctk.CTkLabel(card, text=label, font=(FONT_FAMILY, 15), text_color=COLOR_TEXT,
                     anchor="w", width=160).grid(row=row, column=0, sticky="w",
                                                  padx=(18, 10), pady=8)
        ctk.CTkLabel(card, text=url, font=(FONT_FAMILY, 14), text_color=COLOR_SUBTEXT,
                     anchor="w").grid(row=row, column=1, sticky="w", pady=8)
        ctk.CTkButton(card, text="Open", width=76, height=30, corner_radius=8,
                       font=(FONT_FAMILY, 13, "bold"), fg_color=COLOR_CARD_HOVER,
                       hover_color=COLOR_BORDER, text_color=COLOR_TEXT,
                       command=lambda: webbrowser.open(url)
                       ).grid(row=row, column=2, sticky="e", padx=(10, 18), pady=8)

    def _set_diag_status(self, text, ok=True):
        self.diag_status.configure(text=text, text_color=COLOR_GREEN if ok else COLOR_RED)
        self.after(3000, lambda: self.diag_status.configure(text=""))

    def _open_log_file(self):
        if os.path.exists(LOG_PATH):
            os.startfile(LOG_PATH)
        else:
            self._set_diag_status("No log file yet - logs.log hasn't been created.", ok=False)

    def _open_log_folder(self):
        os.startfile(os.path.dirname(LOG_PATH))

    def _open_corrupted_folder(self):
        if os.path.isdir(CORRUPTED_DIR):
            os.startfile(CORRUPTED_DIR)
        else:
            self._set_diag_status("Corrupted savefiles folder no longer exists.",
                                  ok=False)

    def _collect_debug_info(self):
        dash = self.app.pages["dashboard"]

        build = "frozen build" if getattr(sys, "frozen", False) else "source"
        tk_version = self.tk.call("info", "patchlevel")
        screen = f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}"
        try:
            scaling = f"{ctypes.windll.shcore.GetScaleFactorForDevice(0)}%"
        except (AttributeError, OSError):
            scaling = "unknown"

        if dash.running and dash.start_time:
            elapsed = int(time.time() - dash.start_time)
            h, rem = divmod(elapsed, 3600)
            m, s = divmod(rem, 60)
            runtime = f"{h:02d}:{m:02d}:{s:02d}"
        else:
            runtime = "00:00:00"

        def file_state(path):
            return "ok" if os.path.exists(path) else "missing"

        backups = (len(os.listdir(CORRUPTED_DIR))
                   if os.path.isdir(CORRUPTED_DIR) else 0)
        log_size = (f"{os.path.getsize(LOG_PATH) / 1024:.1f} KB"
                    if os.path.exists(LOG_PATH) else "missing")

        sections = [
            ("Application", [
                ("Name", APP_NAME),
                ("Version", f"{VERSION} ({build})"),
                ("Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ]),
            ("Environment", [
                ("Python", sys.version.split()[0]),
                ("CustomTkinter", ctk.__version__),
                ("Pillow", PIL.__version__),
                ("Tk", tk_version),
                ("Discord.py", discord.__version__),
                ("OS", platform.platform()),
                ("Display", f"{screen} @ {scaling} scaling"),
            ]),
            ("Bot", [
                ("Status", "running" if dash.running else "stopped"),
                ("Runtime", runtime),
            ]),
            ("Files", [
                ("settings.json", file_state(settings_store.SETTINGS_PATH)),
                ("resources.json", file_state(resources_store.RESOURCES_PATH)),
                ("corrupted", f"{backups} backup(s)"),
                ("logs.log", log_size),
            ]),
        ]

        width = max(len(label) for _, rows in sections for label, _ in rows)
        lines = ["```ini"]
        for title, rows in sections:
            if len(lines) > 1:
                lines.append("")
            lines.append(f"[{title}]")
            lines += [f"{label:<{width}} = {value}" for label, value in rows]
        lines.append("```")
        return "\n".join(lines)

    def _copy_debug_info(self):
        self.clipboard_clear()
        self.clipboard_append(self._collect_debug_info())
        self._set_diag_status("\u2713 Debug info copied - paste it into Discord")


class UI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - {VERSION}")
        self.wm_iconbitmap(asset("images", "element_dust.ico"))
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.minsize(WINDOW_W, WINDOW_H)
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()

        self.pages = {}
        self.container = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.pages["dashboard"] = DashboardPage(self.container, self)
        self.pages["settings"] = SettingsPage(self.container, self)
        self.pages["stations"] = StationsPage(self.container, self)
        self.pages["support"] = SupportPage(self.container, self)
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self._active_page = None
        self._show_page("dashboard")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=COLOR_SIDEBAR, width=SIDEBAR_W, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(3, weight=1)

        self.nav_buttons = {}

        dashboard_btn = SidebarButton(
            sidebar, _t("menus", "Dashboard"), asset("images", "home.png"), header=True,
            command=lambda: self._show_page("dashboard"))
        dashboard_btn.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 16))
        self.nav_buttons["dashboard"] = dashboard_btn

        sep_body = draw_shadow_divider(sidebar, width=SIDEBAR_W - 40, bg_color=COLOR_SIDEBAR)
        sep_body.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 16))

        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.grid(row=2, column=0, sticky="new")
        nav_frame.grid_columnconfigure(0, weight=1)

        body_items = [
            ("settings", _t("menus", "Settings"), asset("images", "settings.png")),
            ("stations", _t("menus", "Stations"), asset("images", "station.png")),
            ("support", _t("menus", "Support"), asset("images", "support.png")),
        ]
        for i, (key, label, icon) in enumerate(body_items):
            btn = SidebarButton(nav_frame, label, icon,
                                 command=lambda k=key: self._show_page(k))
            btn.grid(row=i, column=0, sticky="ew", padx=20, pady=4)
            self.nav_buttons[key] = btn

        version_label = ctk.CTkLabel(sidebar, text=VERSION,
                                      font=(FONT_FAMILY, 12), text_color=COLOR_SUBTEXT)
        version_label.grid(row=4, column=0, sticky="sw", padx=20, pady=16)

    def _show_page(self, key):
        if self._active_page != key:
            prev = self.pages.get(self._active_page)
            if prev is not None and hasattr(prev, "on_leave"):
                prev.on_leave()
        for k, btn in self.nav_buttons.items():
            btn.set_active(k == key)
        self.pages[key].tkraise()
        self._active_page = key

    def _on_close(self):
        page = self.pages.get(self._active_page)
        if page is not None and hasattr(page, "on_leave"):
            page.on_leave()
        dashboard = self.pages.get("dashboard")
        if dashboard is not None and dashboard is not page:
            dashboard.on_leave()
        self.destroy()