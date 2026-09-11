"""Station list/detail editor, shared by the Pego and Gacha tabs."""
import tkinter as tk
from copy import deepcopy
from tkinter import font as tkfont
from tkinter import messagebox

import customtkinter as ctk

from logger.logger import logger
from settings import store as settings_store
from UI import station_store
from UI.cards import StatCard
from UI.theme import (
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_BG, COLOR_BORDER, COLOR_CARD,
    COLOR_CARD_HOVER, COLOR_GREEN, COLOR_RED, COLOR_SUBTEXT, COLOR_TEXT,
    COLOR_WARNING, FONT_FAMILY,
)


class StationCard(StatCard):
    """The dashboard's card component, made selectable for station lists."""

    def __init__(self, master, *, name, subtitle, selected, command):
        super().__init__(master, title=str(name), value=str(subtitle), height=60,
                         title_size=13, value_size=11,
                         accent=COLOR_ACCENT if selected else COLOR_BORDER,
                         fill=COLOR_CARD_HOVER if selected else COLOR_CARD)
        self._title = str(name)
        self._selected = selected
        self._name_font = tkfont.Font(font=self._title_font)
        self._detail_font = tkfont.Font(font=self._value_font)
        self.canvas.configure(cursor="hand2", takefocus=True)
        self.canvas.bind("<Enter>", lambda _event: self._highlight(True))
        self.canvas.bind("<Leave>", lambda _event: self._highlight(False))
        self.canvas.bind("<FocusIn>", lambda _event: self._highlight(True))
        self.canvas.bind("<FocusOut>", lambda _event: self._highlight(False))
        self.canvas.bind("<Button-1>", lambda _event: command())
        self.canvas.bind("<Return>", lambda _event: command())
        self.canvas.bind("<space>", lambda _event: command())

    def _highlight(self, active):
        self.fill = COLOR_CARD_HOVER if active or self._selected else COLOR_CARD
        self._redraw()

    @staticmethod
    def _fit(text, font, width):
        text = str(text).replace("\n", " ")
        if font.measure(text) <= width:
            return text
        while text and font.measure(text + "…") > width:
            text = text[:-1]
        return text + "…"

    def _redraw(self, event=None):
        super()._redraw(event)
        if self._placed:
            width = self.canvas.winfo_width() - 40
            self.canvas.itemconfigure("title", text=self._fit(self._title, self._name_font, width),
                                      fill=COLOR_TEXT)
            self.canvas.itemconfigure("value", text=self._fit(self._value, self._detail_font, width),
                                      fill=COLOR_SUBTEXT)


class StationScrollFrame(ctk.CTkScrollableFrame):
    """A quiet scrollbar with a stable gutter and no thumb when content fits."""

    def __init__(self, master, *, surface_color, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._surface_color = surface_color
        self._overflowing = None
        # CTkScrollableFrame exposes colors, but sizing and scroll callbacks
        # require its internal scrollbar/canvas. Keep that adaptation here.
        self._scrollbar.configure(width=12, border_spacing=4, corner_radius=6,
                                  fg_color=surface_color)
        self._parent_canvas.configure(yscrollcommand=self._update_scrollbar)

    def _update_scrollbar(self, first, last):
        self._scrollbar.set(first, last)
        overflowing = float(last) - float(first) < 0.999
        if overflowing != self._overflowing:
            self._overflowing = overflowing
            self._scrollbar.configure(
                button_color=COLOR_BORDER if overflowing else self._surface_color,
                button_hover_color=COLOR_SUBTEXT if overflowing else self._surface_color)


class StationEditorMixin:
    AUTOSAVE_DELAY_MS = 600

    def _init_editors(self):
        self._editors = {}
        self._craft_dirty = False

    def _editor_card(self, body, key, title, icon):
        page = ctk.CTkFrame(body, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        statuses = []
        card = self._card(page, icon, title, COLOR_ACCENT, statuses)
        card.grid_configure(row=0, sticky="nsew", pady=0)
        card.grid_rowconfigure(2, weight=1)
        panel = ctk.CTkFrame(card, fg_color="transparent")
        panel.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=16, pady=(8, 16))
        self._tab_pages[key] = page
        return panel, statuses[0]

    @staticmethod
    def _save_status(label, state):
        text, color = {
            "saved": ("\u2713  All changes saved", COLOR_GREEN),
            "pending": ("\u25cf  Unsaved changes", COLOR_WARNING),
            "invalid": ("!  Check highlighted fields", COLOR_WARNING),
            "error": ("!  Save failed \u2014 retry", COLOR_RED),
            "load_error": ("!  Could not load stations", COLOR_RED),
        }[state]
        label.configure(text=f"  {text}  ", text_color=color)

    @staticmethod
    def _text(parent, text, size=13, color=COLOR_SUBTEXT, bold=False, **kwargs):
        return ctk.CTkLabel(parent, text=text, text_color=color,
                            height=size + 6,
                            font=(FONT_FAMILY, size, "bold" if bold else "normal"), **kwargs)

    def _build_station_tab(self, body, kind, title, icon):
        panel, status = self._editor_card(body, kind + "s", title, icon)
        panel.grid_columnconfigure(1, weight=1)
        panel.grid_rowconfigure(0, weight=1)
        left = ctk.CTkFrame(panel, width=220, fg_color=COLOR_BG, corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left.grid_propagate(False)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)
        count = self._text(left, "YOUR STATIONS", 11, bold=True, anchor="w")
        count.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        listing = StationScrollFrame(left, surface_color=COLOR_BG, width=184)
        listing.grid(row=1, column=0, sticky="nsew", padx=4)
        add = ctk.CTkButton(left, text="+  Add station", height=36,
                           fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                           command=lambda: self._add_station(kind))
        add.grid(row=2, column=0, sticky="ew", padx=12, pady=12)
        detail = StationScrollFrame(panel, surface_color=COLOR_CARD)
        detail.grid(row=0, column=1, sticky="nsew")
        detail.grid_columnconfigure(0, weight=1)
        editor = dict(rows=[], selected=None, job=None, dirty=False, status=status,
                      listing=listing, detail=detail, count=count, widgets={}, buttons=[])
        self._editors[kind] = editor
        try:
            editor["rows"] = station_store.load(kind)
            editor["saved_rows"] = deepcopy(editor["rows"])
        except (OSError, ValueError) as error:
            add.configure(state="disabled")
            self._save_status(status, "load_error")
            self._text(detail, f"Could not read {kind}.json.\nFix the file and reopen the app.",
                       color=COLOR_RED, wraplength=300, justify="left").grid(sticky="w", pady=20)
            logger.error(f"Could not load {kind} stations: {error}")
            return
        self._save_status(status, "saved")
        self._refresh_list(kind)
        self._select_station(kind, 0 if editor["rows"] else None)

    def _refresh_list(self, kind):
        editor = self._editors[kind]
        for widget in editor["listing"].winfo_children():
            widget.destroy()
        editor["buttons"] = []
        editor["count"].configure(text=f"YOUR STATIONS  /  {len(editor['rows']):02d}")
        for index, row in enumerate(editor["rows"]):
            selected = editor["selected"] == index
            subtitle = row.get("teleporter") or "Teleporter needed"
            suffix = f"  ·  {row.get('side', '')}" if kind == "gacha" else ""
            button = StationCard(
                editor["listing"], name=row.get("name") or "Unnamed station",
                subtitle=f"{subtitle}{suffix}", selected=selected,
                command=lambda i=index: self._select_station(kind, i))
            button.pack(fill="x", pady=(0, 8), padx=2)
            editor["buttons"].append(button)
        if not editor["rows"]:
            self._text(editor["listing"], "No stations yet.", 12).pack(pady=16)

    def _select_station(self, kind, index):
        editor = self._editors[kind]
        editor["selected"] = index
        detail = editor["detail"]
        for widget in detail.winfo_children():
            widget.destroy()
        editor["widgets"] = {}
        editor["variables"] = {}
        self._refresh_list(kind)
        if index is None:
            self._text(detail, "Your first station starts here", 20, COLOR_TEXT, True,
                       wraplength=320).grid(sticky="w", pady=(20, 8))
            self._text(detail, "Add a station, then enter its teleporter and options.",
                       wraplength=300, justify="left").grid(sticky="w")
            return
        row = editor["rows"][index]
        self._text(detail, "STATION DETAILS", 11, COLOR_ACCENT, True).grid(sticky="w", pady=(4, 2))
        editor["title"] = self._text(detail, row.get("name") or "New station", 23, COLOR_TEXT, True,
                                      anchor="w", wraplength=330)
        editor["title"].grid(sticky="ew", pady=(0, 4))
        self._text(detail, "Changes save after you finish typing.", 12).grid(sticky="w", pady=(0, 18))
        fields = [("name", "Station name", "A unique name to identify this station."),
                  ("teleporter", "Teleporter", "Match the teleporter name in game.")]
        if kind == "pego":
            fields.append(("delay", "Visit interval (seconds)", "3300 seconds = 55 minutes between visits."))
        else:
            fields.extend([("resource_type", "Resource type", "Use the resource key, for example element."),
                           ("side", "Gacha side", "Which side of the teleporter is this Gacha on?")])
        for key, label, hint in fields:
            self._text(detail, label, 13, COLOR_TEXT, True).grid(sticky="w", pady=(8, 5))
            variable = tk.StringVar(value=str(row.get(key, "")))
            editor["variables"][key] = variable
            if key == "side":
                widget = ctk.CTkSegmentedButton(
                    detail, values=["left", "right"], variable=variable, height=36,
                    selected_color=COLOR_ACCENT, selected_hover_color=COLOR_ACCENT_HOVER,
                    unselected_color=COLOR_BG, unselected_hover_color=COLOR_CARD_HOVER,
                    fg_color=COLOR_BORDER)
            else:
                widget = ctk.CTkEntry(detail, textvariable=variable, height=38,
                                      fg_color=COLOR_BG, border_color=COLOR_BORDER,
                                      border_width=1, font=(FONT_FAMILY, 14))
            widget.grid(sticky="ew", padx=(0, 6))
            variable.trace_add("write", lambda *_args, k=key, v=variable: self._change(kind, index, k, v.get()))
            error_label = self._text(detail, hint, 11, wraplength=320, justify="left", anchor="w")
            error_label.grid(sticky="ew", pady=(3, 6))
            editor["widgets"][key] = (widget, error_label, hint)
        editor["message"] = self._text(detail, "Restart the bot to apply saved station changes.",
                                       11, wraplength=320, justify="left")
        editor["message"].grid(sticky="w", pady=(22, 8))
        editor["retry"] = ctk.CTkButton(detail, text="Retry save", width=100, height=28,
                      fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER,
                      hover_color=COLOR_CARD_HOVER,
                      command=lambda: self._save_stations(kind))
        editor["retry"].grid(sticky="w")
        editor["retry"].grid_remove()
        ctk.CTkButton(detail, text="Remove station", width=140, height=30,
                      fg_color=COLOR_CARD, hover_color=COLOR_CARD_HOVER,
                      text_color=COLOR_RED, border_width=1, border_color=COLOR_BORDER,
                      command=lambda: self._remove_station(kind)).grid(sticky="w", pady=(8, 4))
        self._validate_editor(kind)

    def _validate_editor(self, kind):
        editor = self._editors[kind]
        _, errors = station_store.validate(kind, editor["rows"])
        for key, (widget, label, hint) in editor["widgets"].items():
            error = errors.get((editor["selected"], key))
            if isinstance(widget, ctk.CTkEntry):
                widget.configure(border_color=COLOR_RED if error else COLOR_BORDER)
            label.configure(text=error or hint, text_color=COLOR_RED if error else COLOR_SUBTEXT)
        if editor.get("message") and editor["selected"] is not None:
            editor["message"].configure(
                text="Fix incomplete stations before this list can save." if errors else
                     "Restart the bot to apply saved station changes.",
                text_color=COLOR_WARNING if errors else COLOR_SUBTEXT)
        return errors

    def _change(self, kind, index, key, value):
        editor = self._editors[kind]
        editor["rows"][index][key] = value
        if key == "name":
            editor["title"].configure(text=value or "New station")
        editor["dirty"] = True
        if editor["job"]:
            self.after_cancel(editor["job"])
        errors = self._validate_editor(kind)
        self._save_status(editor["status"], "invalid" if errors else "pending")
        editor["job"] = self.after(self.AUTOSAVE_DELAY_MS, lambda: self._save_stations(kind))

    def _log_station_changes(self, kind, saved, removed_index=None):
        """Compare with the last successful write, retaining identity on rename."""
        editor = self._editors[kind]
        previous = list(editor["saved_rows"])
        if removed_index is not None and removed_index < len(previous):
            removed = previous.pop(removed_index)
            logger.info(f"Station removed: {kind.title()} {removed.get('name')!r} "
                        f"(teleporter: {removed.get('teleporter')!r}).")
        labels = {"name": "Name", "teleporter": "Teleporter", "delay": "Visit interval (seconds)",
                  "resource_type": "Resource type", "side": "Side"}
        for index, row in enumerate(saved):
            if index >= len(previous):
                details = ", ".join(f"{label}: {row[key]!r}" for key, label in labels.items()
                                    if key != "name" and key in row)
                logger.info(f"Station added: {kind.title()} {row.get('name')!r} ({details}).")
                continue
            old = previous[index]
            for key, label in labels.items():
                if old.get(key) != row.get(key):
                    logger.info(f"Station changed: {kind.title()} {old.get('name')!r}: "
                                f"{label}: {old.get(key)!r} → {row.get(key)!r}.")
        editor["saved_rows"] = deepcopy(saved)

    def _save_stations(self, kind):
        editor = self._editors[kind]
        if editor["job"]:
            self.after_cancel(editor["job"])
            editor["job"] = None
        if not editor["dirty"]:
            return
        if self._validate_editor(kind):
            self._save_status(editor["status"], "invalid")
            self._refresh_list(kind)
            return
        try:
            editor["rows"] = station_store.save(kind, editor["rows"])
        except (OSError, ValueError) as error:
            self._save_status(editor["status"], "error")
            editor["retry"].grid()
            logger.error(f"Could not save {kind} stations: {error}")
            return
        self._log_station_changes(kind, editor["rows"])
        editor["dirty"] = False
        editor["retry"].grid_remove()
        self._save_status(editor["status"], "saved")
        self._refresh_list(kind)

    def _remove_station(self, kind):
        editor = self._editors[kind]
        index = editor["selected"]
        if index is None:
            return
        name = editor["rows"][index].get("name") or "Unnamed station"
        if not messagebox.askyesno(
                "Remove station", f'Remove "{name}" from your {kind} stations?\n\n'
                "This also removes it from the saved station list.",
                parent=self, icon="warning", default="no"):
            return
        remaining = editor["rows"][:index] + editor["rows"][index + 1:]
        _, errors = station_store.validate(kind, remaining)
        if errors:
            messagebox.showerror("Station not removed",
                                 "Fix incomplete fields in the other stations before removing this one.",
                                 parent=self)
            return
        # Persist before changing selection, so a failed write keeps the
        # station and all in-progress edits available in the editor.
        try:
            saved = station_store.save(kind, remaining)
        except (OSError, ValueError) as error:
            logger.error(f"Could not remove {kind} station: {error}")
            messagebox.showerror("Station not removed",
                                 "Could not save the station list. The station has been kept.\n"
                                 "Try removing it again.", parent=self)
            return
        if editor["job"]:
            self.after_cancel(editor["job"])
            editor["job"] = None
        self._log_station_changes(kind, saved, removed_index=index)
        editor["rows"] = saved
        editor["dirty"] = False
        self._save_status(editor["status"], "saved")
        self._select_station(kind, min(index, len(saved) - 1) if saved else None)

    def _add_station(self, kind):
        editor = self._editors[kind]
        names = {str(row.get("name", "")).casefold() for row in editor["rows"]}
        number = 1
        while f"{kind}{number}" in names:
            number += 1
        row = dict(name=f"{kind}{number}", teleporter="")
        row.update(dict(delay=3300) if kind == "pego" else dict(resource_type="element", side="left"))
        editor["rows"].append(row)
        editor["dirty"] = True
        self._save_status(editor["status"], "invalid")
        self._select_station(kind, len(editor["rows"]) - 1)
        editor["widgets"]["teleporter"][0].focus_set()

    def _build_crafting_tab(self, body, icon):
        panel, self._craft_status = self._editor_card(body, "crafting", "Crafting", icon)
        panel.grid_columnconfigure(0, weight=1)
        self._text(panel, "CRAFTING OPTIONS", 11, COLOR_ACCENT, True).grid(sticky="w", pady=(8, 12))
        options = ctk.CTkFrame(panel, fg_color=COLOR_BG, corner_radius=10)
        options.grid(sticky="ew")
        options.grid_columnconfigure(0, weight=1)
        self._text(options, "Enable crafting", 14, COLOR_TEXT, True).grid(
            row=0, column=0, sticky="w", padx=18, pady=(16, 0))
        self._text(options, "Use the bot's crafting setting.", 12).grid(
            row=1, column=0, sticky="w", padx=18, pady=(0, 16))
        self._craft_enabled = tk.BooleanVar(value=bool(settings_store.load().get("crafting", False)))
        ctk.CTkSwitch(options, text="", width=46, variable=self._craft_enabled,
                       progress_color=COLOR_ACCENT, command=self._save_crafting).grid(
            row=0, column=1, rowspan=2, padx=18)
        self._text(panel, "Crafting station fields will go here.", 14, COLOR_TEXT, True).grid(
            sticky="w", padx=4, pady=(28, 4))
        self._text(panel, "The crafting routine is still a placeholder in the bot.\n"
                   "This switch saves your preference for when it is implemented.",
                   13, justify="left", wraplength=530).grid(sticky="w", padx=4)
        self._save_status(self._craft_status, "saved")
        self._craft_retry = ctk.CTkButton(panel, text="Retry save", width=100, height=28,
                                         command=self._save_crafting,
                                         fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER)
        self._craft_retry.grid(sticky="w", pady=12)
        self._craft_retry.grid_remove()

    def _save_crafting(self):
        self._craft_dirty = True
        try:
            data = settings_store.load()
            previous = bool(data.get("crafting", False))
            data["crafting"] = self._craft_enabled.get()
            settings_store.save(data)
        except (OSError, ValueError) as error:
            self._save_status(self._craft_status, "error")
            self._craft_retry.grid()
            logger.error(f"Could not save crafting preference: {error}")
            return
        if previous != data["crafting"]:
            logger.info(f"Station setting changed: Enable crafting: {previous!r} → {data['crafting']!r}.")
        self._save_status(self._craft_status, "saved")
        self._craft_dirty = False
        self._craft_retry.grid_remove()

    def on_leave(self):
        for kind in self._editors:
            self._save_stations(kind)
        if self._craft_dirty:
            self._save_crafting()
