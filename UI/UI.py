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


def asset(*parts):
    """Absolute path to a file inside the UI/ folder."""
    return os.path.join(UI_DIR, *parts)

# Lock the UI to real, literal pixels. CTk otherwise auto-detects each
# monitor's Windows/macOS display scaling and multiplies every widget's
# size and font by that factor - which is why a 1080p and a 1440p screen
# (often set to different scaling %) rendered this differently, and why
# the fixed-pixel canvases here fell out of sync with the auto-scaled
# widgets drawn on top of them. Pinning scaling to 1.0 makes 1 pixel =
# 1 pixel everywhere, consistently across monitors.
ctk.deactivate_automatic_dpi_awareness()
ctk.set_widget_scaling(1.0)
ctk.set_window_scaling(1.0)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

WINDOW_W, WINDOW_H = 1280, 800
SIDEBAR_W = 220
SETTINGS_RAIL_W = 170  # the settings page's own vertical category navbar
CONTENT_PADX = 28
CARD_H = 116  # uniform height for the top row of cards
CARD_GAP = 16  # gap between the 3 top cards, and between the panels below them
STAT_ROW_H = 56  # minimum height of the mini stat cards in the resources
                 # panel - kept low on purpose; the rows stretch to split
                 # the panel's height evenly, this only guards the layout
                 # from collapsing before the first resize event lands

# The dashboard's 3 top cards + the event log/items panels below them all
# share one fixed-pixel column grid (see DashboardPage._build_content).
# Tk's grid "uniform" column groups don't stay equal once a widget spans
# more than one uniform column - Tk grows only the columns that widget
# actually spans to fit it, and any other uniform-group column not part of
# that span is left sized by its own content instead of following along.
# The event log spans 2 of the 3 card columns, which reliably triggered
# that: it made the control + crystals columns wider than the dust column
# next to them. Since this window is fixed-size and non-resizable, doing
# the pixel math once up front and using it as a hard minsize sidesteps the
# whole issue - there's no "extra" space left for Tk to redistribute unevenly.
_CONTENT_W = WINDOW_W - SIDEBAR_W - 2 * CONTENT_PADX
CARD_W = (_CONTENT_W - 2 * CARD_GAP) // 3

# ----------------------------------------------------------------------------
# EVENT LOG STYLING
# ----------------------------------------------------------------------------
# Mirrors logger.Logging._LOG_LEVEL_MAP so the on-screen event log reads the
# same as logs.log.
EVENT_COLORS = {
    "DEBUG": COLOR_SUBTEXT,
    "INFO": COLOR_BLUE,
    "WARNING": COLOR_WARNING,
    "ERROR": COLOR_RED,
    "CRITICAL": COLOR_ACCENT,
}
EVENT_LABELS = {
    "DEBUG": "Debug",
    "INFO": "Info",
    "WARNING": "Warning",
    "ERROR": "Error",
    "CRITICAL": "Critical",
}
# ----------------------------------------------------------------------------
# DRAWING HELPER
# ----------------------------------------------------------------------------
def _lerp_color(c1, c2, t):
    """Blend two "#rrggbb" colors; t=0 -> c1, t=1 -> c2."""
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def load_icon(path, size, tint=None):
    """Load an icon file as a square CTkImage. With `tint`, the file's own
    pixels are discarded and only its alpha silhouette is kept, filled with
    the tint color - the supplied icon files are black glyphs, which would
    be invisible on this dark theme without retinting."""
    img = Image.open(path).convert("RGBA")
    if tint:
        rgb = (int(tint[1:3], 16), int(tint[3:5], 16), int(tint[5:7], 16))
        solid = Image.new("RGBA", img.size, rgb + (255,))
        solid.putalpha(img.getchannel("A"))
        img = solid
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


def draw_shadow_divider(master, width, bg_color, line_color=COLOR_BORDER, fade=3):
    """A hairline divider with a quick drop-shadow falloff underneath it,
    instead of a flat 1px line or a tall, evenly-graded gradient band -
    the eased (not linear) falloff keeps the shadow itself short and
    subtle rather than reading as a second, thicker bar of its own.
    """
    canvas = tk.Canvas(master, width=width, height=fade + 1, bg=bg_color, highlightthickness=0)
    canvas.create_rectangle(0, 0, width, 1, fill=line_color, outline=line_color)
    for i in range(fade):
        t = ((i + 1) / fade) ** 2
        color = _lerp_color(line_color, bg_color, t)
        canvas.create_rectangle(0, i + 1, width, i + 2, fill=color, outline=color)
    return canvas


def draw_vertical_shadow_divider(master, height, bg_color, line_color=COLOR_BORDER, fade=3):
    """Vertical twin of draw_shadow_divider: same 1px line and short eased
    falloff, just cast sideways - used between the two navbars."""
    canvas = tk.Canvas(master, width=fade + 1, height=height, bg=bg_color,
                        highlightthickness=0)
    canvas.create_rectangle(0, 0, 1, height, fill=line_color, outline=line_color)
    for i in range(fade):
        t = ((i + 1) / fade) ** 2
        color = _lerp_color(line_color, bg_color, t)
        canvas.create_rectangle(i + 1, 0, i + 2, height, fill=color, outline=color)
    return canvas


# ----------------------------------------------------------------------------
# REUSABLE WIDGETS
# ----------------------------------------------------------------------------
class ControlCard(ctk.CTkFrame):
    """The primary control card: big START/STOP button on top, runtime
    readout underneath as the secondary element."""

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
            self.canvas, text="START BOT", height=44, corner_radius=8,
            font=(FONT_FAMILY, 15, "bold"), fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER, command=on_toggle)

        # Canvas text item, not a CTkLabel - see the note in StatCard: an
        # embedded label leaks a 1px seam of its auto-detected background
        # at its edge.
        self._runtime_text = "\u25cf  00:00:00  Runtime"
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
        # Centered `pad` below the card's top edge - same margin as its
        # left edge - rather than a fixed fraction of h, so a taller
        # button doesn't creep closer to the top edge or crowd the
        # runtime label as its height changes.
        btn_center_y = pad + btn_height / 2
        if self._button_window is None:
            self._button_window = self.canvas.create_window(
                pad, btn_center_y, anchor="w", window=self.toggle_button,
                width=btn_width, height=btn_height)
        else:
            # Setting width/height directly on the canvas window item -
            # rather than trusting the button's own .configure(width=...)
            # to propagate - is what keeps the button from overflowing the
            # card when it wants more space than it's given.
            self.canvas.itemconfig(self._button_window, width=btn_width, height=btn_height)
            self.canvas.coords(self._button_window, pad, btn_center_y)

        if not self._placed:
            # Negative size = pixels, matching CTk's font sizing (see the
            # font note in StatCard).
            self.canvas.create_text(pad + 4, h * 0.78, anchor="w",
                                     text=self._runtime_text,
                                     font=(FONT_FAMILY, -14),
                                     fill=self._runtime_color, tags="runtime")
            self._placed = True
        else:
            # Push the freshly redrawn "bg" back under the runtime text
            # (canvas z-order is creation order).
            self.canvas.tag_lower("bg")

    def set_running(self, running: bool):
        if running:
            self.toggle_button.configure(text="STOP BOT", fg_color=COLOR_ACCENT,
                                          hover_color=COLOR_ACCENT_HOVER)
        else:
            self.toggle_button.configure(text="START BOT", fg_color=COLOR_ACCENT,
                                          hover_color=COLOR_ACCENT_HOVER)
        self._redraw()

    def set_runtime(self, text, running: bool):
        dot_color = COLOR_GREEN if running else COLOR_SUBTEXT
        self._runtime_text = f"\u25cf  {text}  Runtime"
        self._runtime_color = dot_color
        if self._placed:
            self.canvas.itemconfig("runtime", text=self._runtime_text, fill=dot_color)


class SidebarButton(ctk.CTkButton):
    """Nav button used in the sidebar, with an active/inactive style.

    `header=True` renders it as the sidebar's one standout destination
    (bigger, bolder, brighter at rest) rather than a regular item in the
    nav body list below it.
    """

    def __init__(self, master, text, icon_path, command=None, header=False, **kwargs):
        self.header = header
        size = 24 if header else 20
        # Icon follows the label's color through every state, so it's
        # pre-tinted once per state and swapped in set_active.
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
    """Small colored-dot + label used in the event log legend."""

    def __init__(self, master, label, color, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text="\u25cf", font=(FONT_FAMILY, 13), text_color=color
                     ).pack(side="left", padx=(0, 4))
        ctk.CTkLabel(self, text=label, font=(FONT_FAMILY, 13), text_color=COLOR_SUBTEXT
                     ).pack(side="left")


class DashboardLogHandler(logging.Handler):
    """Routes logger.py's records into the dashboard's Event Log.

    This is the only thing that drives that panel - nothing generates
    placeholder events. Any logger.info() / .warning() / etc, from anywhere
    in the bot, appears there live and in logs.log both.

    emit() can be called on whatever thread did the logging, and Tk widgets
    must only be touched from the thread running the mainloop, so it hands
    the actual textbox update over with `after(0, ...)` instead of writing to
    the widget itself. Keep it that way - this is what lets the bot log from
    its own thread.
    """

    def __init__(self, dashboard):
        super().__init__()
        self.dashboard = dashboard

    def emit(self, record):
        self.dashboard.after(0, self.dashboard._log, record.levelname, self.format(record))


# ----------------------------------------------------------------------------
# DASHBOARD PAGE
# ----------------------------------------------------------------------------
class DashboardPage(ctk.CTkFrame):
    """The app's main page: start/stop the bot, watch what it's farming.

    Three summary cards across the top (control, crystals, dust), and below
    them the Event Log beside the Resources Farmed panel. Every count on the
    page - the two top cards and the five loot cards - is registered in
    `stat_cards` under the same keys resources.json uses, so set_stat() and
    persistence treat them all alike.

    Counts are saved on a throttle rather than on every change; on_leave()
    is what guarantees the last of them reaches disk."""

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
    # -- header -------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 8))

        title = ctk.CTkLabel(header, text="Dashboard", font=(FONT_FAMILY, 27, "bold"),
                              text_color=COLOR_TEXT)
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(header, text="Live overview of your bot",
                                 font=(FONT_FAMILY, 15), text_color=COLOR_SUBTEXT)
        subtitle.grid(row=1, column=0, sticky="w", pady=(2, 0))

    # -- shared grid for the card row + the panels below it -------------------
    # 5 fixed-width columns (see CARD_W/CARD_GAP): 3 equal card columns
    # (0, 2, 4) separated by 2 gap columns (1, 3). Cards get zero padx and
    # just fill their own column, so their widths only ever depend on this
    # fixed grid - not on how many neighbors' padding happened to eat into
    # them (that's what made the middle card narrower than the other two
    # before). The panels below share this same grid and span whole card
    # columns, so the event log's right edge locks to the crystals card and
    # the items panel's left edge locks to the dust card.
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

    # -- summary cards --------------------------------------------------------
    def _build_summary_row(self, content):
        self.control_card = ControlCard(content, self.toggle_bot)
        self.control_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.crystals_card = StatCard(content, "Crystals opened", "0", accent=COLOR_CYAN,
                                       icon=asset("resources", "images", "gacha_crystal.png"))
        self.crystals_card.grid(row=0, column=2, sticky="ew", pady=(0, 8))

        self.dust_card = StatCard(content, "Dust Collected", "0", accent=COLOR_CYAN,
                                   icon=asset("resources", "images", "element_dust.png"))
        self.dust_card.grid(row=0, column=4, sticky="ew", pady=(0, 8))

    # -- body: event log + loot stats ----------------------------------------
    def _build_body(self, content):
        # --- event log --- spans the control + crystals card columns and the
        # gap column between them, so it ends flush with the crystals card
        # above it, leaving the dust card's column free for the items panel.
        log_panel = ctk.CTkFrame(content, fg_color=COLOR_CARD, corner_radius=12,
                                  border_width=1, border_color=COLOR_BORDER)
        log_panel.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        log_panel.grid_columnconfigure(0, weight=1)
        log_panel.grid_rowconfigure(2, weight=1)

        log_header = ctk.CTkFrame(log_panel, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 4))
        log_header.grid_columnconfigure(0, weight=1)

        log_title = ctk.CTkLabel(log_header, text="Event Log", font=(FONT_FAMILY, 17, "bold"),
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

        # tag colors + zebra-stripe background for the textbox
        for tag, color in EVENT_COLORS.items():
            self.log_box._textbox.tag_config(tag, foreground=color)
        self.log_box._textbox.tag_config("even", background=COLOR_ROW_ALT)
        self.log_box._textbox.tag_config("time", foreground=COLOR_SUBTEXT)

        # Everything written to `logger` (logger/logger.py) from anywhere in
        # the bot - not just this UI - lands here from now on.
        logger.addHandler(DashboardLogHandler(self))
        logger.info("UI initialized.")

        # --- resources panel --- occupies exactly the dust card's column,
        # one card's width, with the column-1 gap providing the same
        # spacing used everywhere else in this grid. Holds the fixed set of
        # five resource cards (same look as the top StatCards, just
        # smaller), stretched to split the panel's height evenly.
        stats_panel = ctk.CTkFrame(content, fg_color=COLOR_CARD, corner_radius=12,
                                    border_width=1, border_color=COLOR_BORDER)
        stats_panel.grid(row=1, column=4, sticky="nsew", pady=(8, 0))
        stats_panel.grid_columnconfigure(0, weight=1)
        stats_panel.grid_rowconfigure(1, weight=1)

        stats_title = ctk.CTkLabel(stats_panel, text="Resources Farmed",
                                    font=(FONT_FAMILY, 17, "bold"),
                                    text_color=COLOR_TEXT, anchor="w")
        # Bottom pad is 13, not 10: the event log panel stacks header +
        # separator above its box, this panel only a title - 13 is what
        # lands the first card's top border on the exact same pixel row as
        # the log box's (measured off the rendered window).
        stats_title.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 13))

        # Insets match the event log box: 18px on the sides and bottom.
        # Card rows and the gaps between them are laid out by _add_stat.
        self._stats_body = ctk.CTkFrame(stats_panel, fg_color="transparent")
        self._stats_body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self._stats_body.grid_columnconfigure(0, weight=1)

        self.stat_cards = {}
        self._add_stat("black_pearls", "Black Pearls",
                       asset("resources", "images", "black_pearls.png"), COLOR_PEARL)
        self._add_stat("metal_ingots", "Metal Ingots",
                       asset("resources", "images", "metal_ingot.png"), COLOR_METAL)
        self._add_stat("flint", "Flint",
                       asset("resources", "images", "flint.png"), COLOR_PASTE)
        self._add_stat("electronics", "Electronics",
                       asset("resources", "images", "electronics.png"), COLOR_ELECTRONICS)
        self._add_stat("crystal", "Crystal",
                       asset("resources", "images", "crystal.png"), COLOR_CRYSTAL)

        # The two top summary cards join the same keyed map, so set_stat
        # and persistence treat every resource uniformly. Registered only
        # after the mini cards: _add_stat derives its grid row from the
        # map's size.
        self.stat_cards["crystals_opened"] = self.crystals_card
        self.stat_cards["dust_collected"] = self.dust_card

        # Restore last session's counts onto the cards. Loaded here, not in
        # __init__: load() logs when it has to (re)create resources.json,
        # and only from this point on is the event-log handler attached -
        # any earlier and that line would reach logs.log but never the
        # on-screen event log.
        resources_store.on_start()
        self._stats = resources_store.load()
        for key, count in self._stats.items():
            self.stat_cards[key].set_count(count)

    # -- stats ---------------------------------------------------------------
    def _add_stat(self, key, label, icon, accent):
        """Append one mini stat card to the resources panel.

        Cards land on alternating grid rows: even rows are the cards
        themselves (equal weight, one uniform group, so they always share
        the body's height in exactly equal parts), odd rows are fixed
        CARD_GAP spacers. Gaps as rows instead of pady keeps every card's
        row the same size - pady would count against its own row's share
        and make that card visibly shorter than the rest."""
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
        """Update one of the resource cards by key (any stat_cards key,
        e.g. "black_pearls" or "crystals_opened"). Numbers are compacted
        for display (14300 -> '14.3k') and persisted to
        resources/resources.json;
        strings pass through to the card as-is and are not persisted."""
        if isinstance(value, (int, float)):
            self._stats[key] = int(value)
            self.stat_cards[key].set_count(value)
            if not self.running:
                self._schedule_stats_save()
        else:
            self.stat_cards[key].set_value(value)

    def _schedule_stats_save(self):
        """Trailing throttle, not a debounce: the first update schedules a
        save and further updates ride along with it, so a bot hammering
        set_stat hits the disk at most once per interval - a debounce that
        resets on every call could starve the save forever."""
        if self._stats_save_job is None:
            self._stats_save_job = self.after(self.STATS_SAVE_DELAY_MS,
                                              self._save_stats)

    def _save_stats(self):
        self._stats_save_job = None
        resources_store.save(self._stats)

    # -- page lifecycle -------------------------------------------------------
    def on_leave(self):
        """Flush any pending stats save when the user navigates off the
        dashboard or closes the app."""
        if self._stats_save_job:
            self.after_cancel(self._stats_save_job)
            self._save_stats()

    # -- logging helper -------------------------------------------------------
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

    # -- bot control ------------------------------------------------------------
    # NOTE: nothing below actually runs the bot yet. Start/stop flip this
    # page's own state - the button label, the runtime clock, a log line -
    # and that is all they do. The bot itself is not wired in; when it is,
    # _start_bot/_stop_bot are where it gets launched and told to stop, and
    # `running` is what the rest of the UI already reads to tell whether it
    # should be going.
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
        """Relay child records through the shared logger; its handler updates Tk."""
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
        """Re-read resources.json periodically - the bot subprocess writes to
        it directly, and this process has no other way to notice a change."""
        fresh = resources_store.load()
        for key, value in fresh.items():
            if key in self.stat_cards and value != self._stats.get(key):
                self._stats[key] = value
                self.stat_cards[key].set_count(value)
        self.after(self.STATS_REFRESH_MS, self._tick_stats_refresh)


# ----------------------------------------------------------------------------
# SHARED PAGE SCAFFOLDING (header + a stack of titled section cards)
# ----------------------------------------------------------------------------
class FormPage(ctk.CTkFrame):
    """Base for pages built as a header over icon-chip section cards -
    Settings and Support both follow this same shape."""

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

    # -- section-card builders ------------------------------------------------
    def _card(self, column, icon, title, accent, status_list=None):
        """Section card with an icon-chip header. `icon` is either a glyph
        string or a .png path (tinted with the accent color). If
        `status_list` is given, a status pill is added to the card's
        top-right corner and appended to that list so the caller can update
        every card's pill in lockstep."""
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
        # Bottom breathing room as an EMPTY grid row: a real (even
        # "transparent") frame paints the parent's fill color and would
        # square off the card's rounded bottom corner / cover its border.
        card.grid_rowconfigure(card.grid_size()[1], minsize=10)


# ----------------------------------------------------------------------------
# STATIONS PAGE
# ----------------------------------------------------------------------------
class StationsPage(StationEditorMixin, FormPage):
    """Station configuration behind Pego, Gacha, and Crafting tabs."""

    def __init__(self, master, app):
        super().__init__(master, app)
        self._init_editors()
        # --- second navbar: vertical category rail beside the main sidebar ---
        # Column layout: shadow divider | rail | content. The rail sits on a
        # darker tone than the main sidebar and the divider is a 1px line
        # with a short drop-shadow fading into the rail, so the sidebar
        # reads as a separate layer above it instead of blending in.
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        divider = draw_vertical_shadow_divider(self, WINDOW_H, COLOR_RAIL)
        divider.grid(row=0, column=0, sticky="ns")

        rail = ctk.CTkFrame(self, fg_color=COLOR_RAIL, width=SETTINGS_RAIL_W,
                              corner_radius=0)
        rail.grid(row=0, column=1, sticky="nsw")
        rail.grid_propagate(False)

        # Sized and padded to sit level with the main sidebar's Dashboard
        # header, so the two navbars share one visual rhythm.
        ctk.CTkLabel(rail, text="Stations", font=(FONT_FAMILY, 18, "bold"),
                      text_color=COLOR_TEXT, anchor="w"
                      ).pack(side="top", fill="x", padx=22, pady=(28, 14))

        self._tabs = {}
        self._tab_pages = {}
        self._tab_icons = {}
        self._add_tab(rail, "pegos", "Pegos", asset("images", "pego.png"))
        self._add_tab(rail, "gachas", "Gachas", asset("images", "gacha.png"))
        self._add_tab(rail, "crafting", "Crafting", asset("images", "station.png"))

        # --- content column: header + the active category's card ---
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=2, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=CONTENT_PADX, pady=(24, 10))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Stations", font=(FONT_FAMILY, 27, "bold"),
                      text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header,
                      text="Add or configure your stations \u2014 changes save automatically",
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



# ----------------------------------------------------------------------------
# SETTINGS PAGE
# ----------------------------------------------------------------------------
class SettingsPage(FormPage):
    """Settings, organized behind a second navbar: a vertical category rail
    (Discord / Main Settings / Features) beside the main sidebar, each
    category showing one section card with a color-coded icon chip echoing
    the dashboard's accent system.

    There is no Save button: every edit is validated and written to
    settings.json automatically - debounced while typing, instantly for
    toggles - and the pill in the header reports the save state. When the
    user navigates away from this page (or closes the app while on it),
    every setting that changed since the page was last left is written to
    the log, one line per setting.
    """

    AUTOSAVE_DELAY_MS = 600

    def __init__(self, master, app):
        super().__init__(master, app)
        self._cfg = settings_store.load()
        # What the diff-on-leave compares against. Updated on every
        # on_leave, so each visit only logs its own changes.
        self._baseline = dict(self._cfg)
        self._fields = {}   # setting key -> entry/switch widget
        self._labels = {}   # setting key -> human label (for log lines)
        self._status_labels = []  # one save-status pill per category card
        self._save_job = None

        # --- second navbar: vertical category rail beside the main sidebar ---
        # Column layout: shadow divider | rail | content. The rail sits on a
        # darker tone than the main sidebar and the divider is a 1px line
        # with a short drop-shadow fading into the rail, so the sidebar
        # reads as a separate layer above it instead of blending in.
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        divider = draw_vertical_shadow_divider(self, WINDOW_H, COLOR_RAIL)
        divider.grid(row=0, column=0, sticky="ns")

        rail = ctk.CTkFrame(self, fg_color=COLOR_RAIL, width=SETTINGS_RAIL_W,
                             corner_radius=0)
        rail.grid(row=0, column=1, sticky="nsw")
        rail.grid_propagate(False)

        # Sized and padded to sit level with the main sidebar's Dashboard
        # header, so the two navbars share one visual rhythm.
        ctk.CTkLabel(rail, text="Settings", font=(FONT_FAMILY, 18, "bold"),
                     text_color=COLOR_TEXT, anchor="w"
                     ).pack(side="top", fill="x", padx=22, pady=(28, 14))

        self._tabs = {}
        self._tab_pages = {}
        self._tab_icons = {}
        self._add_tab(rail, "discord", "Discord", asset("images", "discord_image.png"))
        self._add_tab(rail, "main", "Main Settings", asset("images", "settings.png"))
        self._add_tab(rail, "features", "Features", asset("images", "features.png"))

        # --- content column: header + the active category's card ---
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=2, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=CONTENT_PADX, pady=(24, 10))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Settings", font=(FONT_FAMILY, 27, "bold"),
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header,
                     text="Configure how the bot behaves \u2014 changes save automatically",
                     font=(FONT_FAMILY, 15), text_color=COLOR_SUBTEXT
                     ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        body = ctk.CTkFrame(content, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=CONTENT_PADX, pady=(4, 24))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        lhalf, rhalf = self._tab_page(body, "discord", asset("images", "discord_image.png"),
                                      "Discord", COLOR_ACCENT)
        self._switch_row(lhalf, "Use Discord", "use_discord", COLOR_ACCENT)
        self._entry_row(lhalf, "Command Prefix", "command_prefix")
        self._entry_row(rhalf, "Log Channel (Gacha)", "log_channel_gacha")
        self._entry_row(rhalf, "Log Active Queue", "log_active_queue")
        self._entry_row(rhalf, "Log Wait Queue", "log_wait_queue")
        self._entry_row(lhalf, "Discord API Key", "discord_api_key", show="*")

        lhalf, rhalf = self._tab_page(body, "main", asset("images", "settings.png"),
                                      "Main Settings", COLOR_ACCENT)

        #Left half, from top to bottom
        self._entry_row(lhalf, "Server Number", "server_number")
        self._entry_row(lhalf, "Lag Offset", "lag_offset")
        self._entry_row(lhalf, "Station Yaw", "station_yaw")
        self._entry_row(lhalf, "Render Pushout", "render_pushout")
        self._entry_row(lhalf, "Replenish interval", "replenish_interval")
        self._entry_row(lhalf, "Berry Type", "berry_type")

        #Right half, from top to bottom
        self._entry_row(rhalf, "Iguanadon", "iguanadon")
        self._entry_row(rhalf, "Drop Off", "drop_off")
        self._entry_row(rhalf, "Bed Spawn", "bed_spawn")
        self._entry_row(rhalf, "Berry Station", "berry_station")
        self._entry_row(rhalf, "Grindables", "grindables")
        self._entry_row(rhalf, "Cargo Pickup","cargo_pickup")
        self._entry_row(rhalf, "OCR Path","ocr_path")

        lhalf, rhalf = self._tab_page(body, "features", asset("images", "features.png"),
                                      "Features", COLOR_ACCENT)

        self._switch_row(lhalf, "External Berries", "external_berry", COLOR_ACCENT)
        self._switch_row(lhalf, "Seeds 230", "seeds_230", COLOR_ACCENT)
        self._switch_row(lhalf, "Side Crop Plot", "side_crop_plot", COLOR_ACCENT)
        self._switch_row(lhalf, "Y Trap Bot", "y_trap_bot", COLOR_ACCENT)

        self._switch_row(rhalf, "Singleplayer", "singleplayer", COLOR_ACCENT)
        self._switch_row(rhalf, "Cargo Ledger", "cargo_ledger", COLOR_ACCENT)
        self._segmented_row(rhalf, "Height Ele", "height_ele", COLOR_ACCENT, ("2", "3"))
        self._segmented_row(rhalf, "Height Grind", "height_grind", COLOR_ACCENT, ("2", "3"))

        self._set_status("saved")
        self._show_tab("discord")

    # -- category tabs --------------------------------------------------------
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
        """One category page: a single card filling all available page space,
        its fields laid out across two equal-width halves."""
        page = ctk.CTkFrame(body, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        # Every category card carries its own save-status pill (top right);
        # _set_status updates them all in lockstep so the indicator is
        # visible no matter which tab is open.
        card = self._card(page, icon, title, accent, status_list=self._status_labels)
        # row=0 explicitly: _card picks its row via grid_size(), which
        # already counts the weighted (still empty) row 0 registered by
        # grid_rowconfigure above and would otherwise land the card in
        # row 1 - beneath all the stretch space.
        card.grid_configure(row=0, sticky="nsew", pady=0)
        card.grid_columnconfigure((0, 1), weight=1, uniform=f"tab-{key}")
        # The halves are inset 2px from the card's left/right edges: a CTk
        # "transparent" frame really paints its parent's fill color as a
        # solid block, and a child gridded flush against the card edge sits
        # on top of the card's 1px border, erasing it for the child's whole
        # height.
        halves = []
        for col, padx in ((0, (2, 8)), (1, (8, 2))):
            half = ctk.CTkFrame(card, fg_color="transparent")
            half.grid(row=2, column=col, sticky="new", padx=padx)
            half.grid_columnconfigure(1, weight=1)
            halves.append(half)
        self._tab_pages[key] = page
        return halves

    def _entry_row(self, card, label, key, show=None):
        row = card.grid_size()[1]
        ctk.CTkLabel(card, text=label, font=(FONT_FAMILY, 15), text_color=COLOR_TEXT,
                     anchor="w", width=160).grid(row=row, column=0, sticky="w",
                                                  padx=(18, 10), pady=8)
        # border_width=1 matches the card's own hairline border - CTkEntry's
        # default 2px outline reads noticeably brighter than every other
        # edge on the page.
        entry = ctk.CTkEntry(card, font=(FONT_FAMILY, 15), height=38, corner_radius=8,
                              fg_color=COLOR_BG, border_width=1,
                              border_color=COLOR_BORDER, show=show)
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
        """Fixed-choice setting rendered as a segmented button, so an
        out-of-range value can't even be typed."""
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
        # Clamp a stray stored value to a legal choice instead of showing
        # nothing selected.
        current = str(self._cfg[key])
        seg.set(current if current in values else values[-1])
        seg.grid(row=row, column=1, sticky="e", padx=(0, 18), pady=8)
        self._fields[key] = seg
        self._labels[key] = label

    # -- auto-save ------------------------------------------------------------
    def _set_status(self, kind):
        text, color = {
            "saved": ("\u2713  All changes saved", COLOR_GREEN),
            "saving": ("\u25cf  Saving\u2026", COLOR_SUBTEXT),
            "invalid": ("\u2717  Invalid value \u2014 not saved", COLOR_RED),
        }[kind]
        for status in self._status_labels:
            status.configure(text=f"  {text}  ", text_color=color)

    def _schedule_save(self):
        """Debounce typing: (re)start the countdown on every keystroke and
        only hit the disk once it goes quiet."""
        if self._save_job:
            self.after_cancel(self._save_job)
        self._set_status("saving")
        self._save_job = self.after(self.AUTOSAVE_DELAY_MS, self._autosave)

    def _on_toggle(self):
        # Toggles are a single deliberate click - no debounce needed.
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
        """Current widget values cast to their real types, so diffing against
        the (typed) baseline never flags '0' vs 0. A field holding an invalid
        value was never saved, so it reports its baseline value - not changed."""
        out = {}
        for key, widget in self._fields.items():
            field_type = settings_store.FIELD_TYPES.get(key)
            try:
                out[key] = field_type(widget.get()) if field_type else widget.get()
            except ValueError:
                out[key] = self._baseline.get(key)
        return out

    # -- page lifecycle -------------------------------------------------------
    def on_leave(self):
        """Called by App when the user navigates off this page (or closes the
        app while on it): flush any pending debounced save, then log every
        setting that changed during this visit."""
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


# ----------------------------------------------------------------------------
# SUPPORT PAGE
# ----------------------------------------------------------------------------
class SupportPage(FormPage):
    """Where a user goes when something has gone wrong: the log file, the
    quarantined savefiles if there are any, and a one-click debug snapshot
    formatted for pasting into the Discord support channel.

    The snapshot deliberately carries no settings values and no resource
    counts - see _collect_debug_info."""

    def __init__(self, master, app):
        super().__init__(master, app)
        self._header("Support", "Diagnostics, logs, and ways to reach us")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=CONTENT_PADX, pady=(8, 24))
        body.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        diag = self._card(body, asset("images", "logs.png"), "Diagnostics & Logs", COLOR_ACCENT)
        self._info_row(diag, "App Version", VERSION)
        self._info_row(diag, "Log File Path", LOG_PATH)
        buttons = [
            ("Open Log File", self._open_log_file),
            ("Open Logs Folder", self._open_log_folder),
            ("Copy Debug Info", self._copy_debug_info),
        ]
        # Only offered when there is actually something to recover -
        # quarantining only happens while the stores load at startup, so
        # by the time this page is built the folder's state is settled.
        if os.path.isdir(CORRUPTED_DIR) and os.listdir(CORRUPTED_DIR):
            buttons.append(("Open Corrupted Savefiles", self._open_corrupted_folder))
        btn_row = self._button_row(diag, buttons)
        # Status message sits inline next to the buttons rather than on its
        # own row, keeping the card's bottom edge tight.
        self.diag_status = ctk.CTkLabel(btn_row, text="", font=(FONT_FAMILY, 13),
                                         text_color=COLOR_GREEN, anchor="w")
        self.diag_status.pack(side="left", padx=(14, 0))
        self._end_card(diag)

        contact = self._card(body, asset("images", "community.png"), "Contact & Community",
                             COLOR_ACCENT)
        self._link_row(contact, "Discord", DISCORD_URL)
        self._link_row(contact, "GitHub Repo", GITHUB_URL)
        self._info_row(contact, "Bot Creator", "Caleb106")
        self._info_row(contact, "UI Creator", "SwedishTerminator")
        self._end_card(contact)

    # -- Support-specific layout helpers ---------------------------------------
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

    # -- diagnostics actions ----------------------------------------------------
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
        # Re-checked here: the user may have deleted the folder (or its
        # contents) since the page was built.
        if os.path.isdir(CORRUPTED_DIR):
            os.startfile(CORRUPTED_DIR)
        else:
            self._set_diag_status("Corrupted savefiles folder no longer exists.",
                                  ok=False)

    def _collect_debug_info(self):
        """One support-ready snapshot: environment, app state, and savefile
        health, so a bug report doesn't start with three rounds of 'what
        version / what monitor / is the bot running'. Wrapped in a Discord
        code fence, since that is where the reports land."""
        dash = self.app.pages["dashboard"]

        # -- environment
        build = "frozen build" if getattr(sys, "frozen", False) else "source"
        tk_version = self.tk.call("info", "patchlevel")
        screen = f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}"
        try:
            scaling = f"{ctypes.windll.shcore.GetScaleFactorForDevice(0)}%"
        except (AttributeError, OSError):
            scaling = "unknown"

        # -- app state
        if dash.running and dash.start_time:
            elapsed = int(time.time() - dash.start_time)
            h, rem = divmod(elapsed, 3600)
            m, s = divmod(rem, 60)
            runtime = f"{h:02d}:{m:02d}:{s:02d}"
        else:
            runtime = "00:00:00"

        # -- savefile health: whether the stores are readable, never what is
        # in them - settings and resource counts are the user's business.
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

        # ``ini`` is the fence Discord colours "key = value" with, and the
        # padding is what keeps the values in one column once it renders -
        # Discord's code blocks are monospaced, so the alignment survives.
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


# ----------------------------------------------------------------------------
# MAIN APP / SIDEBAR
# ----------------------------------------------------------------------------
class UI(ctk.CTk):
    """The window. Owns the sidebar and the three pages.

    Pages are built once at startup and stacked in a single grid cell;
    _show_page raises one and tells the outgoing one it's leaving, which is
    how settings flush their pending saves. Closing the window goes through
    the same path, plus a guaranteed dashboard flush - see _on_close."""

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
        # Closing the window also "leaves" the current page, so e.g. pending
        # settings changes still get flushed and logged.
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=COLOR_SIDEBAR, width=SIDEBAR_W, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        # column must stretch to the sidebar's full width, otherwise sticky="ew"
        # children only get as wide as their own content and the active-tab
        # highlight ends up flush on one side and short on the other.
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(3, weight=1)

        self.nav_buttons = {}

        # -- header: Dashboard stands alone as the app's main destination,
        # set apart from the rest of the nav (bigger/bolder, own section)
        # rather than just another row in the list below it. There's no
        # logo above it to anchor to (unlike the reference this pattern
        # was borrowed from), so instead its top padding is tuned to put
        # its vertical center level with the page title's - 18px puts it
        # within half a pixel of that, measured directly off the rendered
        # widgets rather than guessed from the two paddings independently.
        dashboard_btn = SidebarButton(
            sidebar, "Dashboard", asset("images", "home.png"), header=True,
            command=lambda: self._show_page("dashboard"))
        dashboard_btn.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 16))
        self.nav_buttons["dashboard"] = dashboard_btn

        sep_body = draw_shadow_divider(sidebar, width=SIDEBAR_W - 40, bg_color=COLOR_SIDEBAR)
        sep_body.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 16))

        # -- body: everything else (just Settings for now) lives here as a
        # regular nav list underneath the Dashboard header.
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.grid(row=2, column=0, sticky="new")
        nav_frame.grid_columnconfigure(0, weight=1)

        body_items = [
            ("settings", "Settings", asset("images", "settings.png")),
            ("stations", "Stations", asset("images", "station.png")),
            ("support", "Support", asset("images", "support.png")),
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
        """Switch pages, giving the outgoing one its on_leave() first. That
        callback is the only thing that flushes a page's pending writes, so
        nothing should raise a page past this method."""
        if self._active_page != key:
            prev = self.pages.get(self._active_page)
            if prev is not None and hasattr(prev, "on_leave"):
                prev.on_leave()
        for k, btn in self.nav_buttons.items():
            btn.set_active(k == key)
        self.pages[key].tkraise()
        self._active_page = key

    def _on_close(self):
        """Shut down cleanly: whatever page is open gets its on_leave(), and
        so does the dashboard regardless, since its throttled resource saves
        would otherwise be dropped when the app is closed from another
        page."""
        page = self.pages.get(self._active_page)
        if page is not None and hasattr(page, "on_leave"):
            page.on_leave()
        # The dashboard buffers resource-stat saves, so it needs its flush
        # even when the app is closed from some other page.
        dashboard = self.pages.get("dashboard")
        if dashboard is not None and dashboard is not page:
            dashboard.on_leave()
        self.destroy()
