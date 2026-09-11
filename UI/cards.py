"""Shared canvas cards and their rounded drawing primitives."""
import math
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageTk

from tools.format import format_count
from UI.theme import COLOR_ACCENT, COLOR_BG, COLOR_CARD, COLOR_SUBTEXT, COLOR_TEXT, FONT_FAMILY


def draw_rounded_rect(canvas, x1, y1, x2, y2, r, fill, corners=(True, True, True, True), tags=None):
    """Fill a rectangle with independently roundable corners.

    corners = (top_left, top_right, bottom_right, bottom_left)
    Square corners are filled solid so the shape still reaches the full
    bounding box - this lets a square-cornered edge butt cleanly against
    a neighboring rounded corner of the same size.
    """
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    kwargs = {"fill": fill, "outline": fill}
    if tags:
        kwargs["tags"] = tags
    if r <= 0:
        canvas.create_rectangle(x1, y1, x2, y2, **kwargs)
        return
    tl, tr, br, bl = corners
    # center bands
    canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs)
    canvas.create_rectangle(x1, y1 + r, x2, y2 - r, **kwargs)
    # corner pieces: (rounded?, arc bbox..., square-fill bbox...)
    pieces = [
        (tl, x1, y1, x1 + 2 * r, y1 + 2 * r, 90, x1, y1, x1 + r, y1 + r),
        (tr, x2 - 2 * r, y1, x2, y1 + 2 * r, 0, x2 - r, y1, x2, y1 + r),
        (br, x2 - 2 * r, y2 - 2 * r, x2, y2, 270, x2 - r, y2 - r, x2, y2),
        (bl, x1, y2 - 2 * r, x1 + 2 * r, y2, 180, x1, y2 - r, x1 + r, y2),
    ]
    for rounded, ax1, ay1, ax2, ay2, start, sx1, sy1, sx2, sy2 in pieces:
        if rounded:
            canvas.create_arc(ax1, ay1, ax2, ay2, start=start, extent=90,
                               style="pieslice", **kwargs)
        else:
            canvas.create_rectangle(sx1, sy1, sx2, sy2, **kwargs)


def draw_accent_strip(canvas, bar_w, radius, h, fill, tags=None):
    """Accent bar whose corners trace the exact same circle as the card's
    own rounded corners (same radius), clipped to the strip's own width so
    it never bulges past the flat line below it.

    Two earlier approaches both failed here. Drawing the strip wide and
    erasing the overshoot with a flat rectangle doesn't work: the region
    being erased partly falls *outside* the card's true circle too (right
    near the corner tip), so a flat erase paints a small square patch back
    in past where the card's rounded silhouette already ends. And handing
    draw_rounded_rect the strip's own narrow bounds makes it clamp the
    radius down to fit (radius <= width/2), which draws a smaller, tighter
    curve than the card's actual corner - close, but not the same circle.
    The fix is to trace the card's true circle (radius `radius`, centered
    `radius` in from the strip's top/left) and only keep the part of it
    that's already within x <= bar_w, using the closed-form circle
    boundary (x = cx - sqrt(r^2 - (y-cy)^2)) instead of an arc primitive,
    since Tk's create_arc has no way to clip a pieslice to a rectangle.
    """
    r = min(radius, h / 2)
    kwargs = {"fill": fill, "outline": fill}
    if tags:
        kwargs["tags"] = tags
    if r <= 0 or bar_w <= 0:
        if bar_w > 0:
            canvas.create_rectangle(0, 0, bar_w, h, **kwargs)
        return

    if bar_w >= r:
        # The strip is already at least as wide as the corner radius, so
        # the card's true curve fits inside it without any clipping.
        canvas.create_arc(0, 0, 2 * r, 2 * r, start=90, extent=90, style="pieslice", **kwargs)
        canvas.create_arc(0, h - 2 * r, 2 * r, h, start=180, extent=90, style="pieslice", **kwargs)
    else:
        steps = 16

        def curve(y_lo, y_hi):
            """Points along the true corner circle (center (r, r) in the
            corner's own local frame) from y_lo to y_hi, i.e. from where
            it crosses x = bar_w down to where it goes fully flat at
            x = 0, y = r."""
            pts = []
            for i in range(steps + 1):
                y = y_lo + (y_hi - y_lo) * i / steps
                x = r - math.sqrt(max(r * r - (y - r) ** 2, 0))
                pts.append((min(x, bar_w), y))
            return pts

        # y where the card's true corner curve first crosses x = bar_w -
        # above this (closer to the corner tip) the curve hasn't reached
        # into the strip's width yet, so - same as the card's own corner -
        # there's nothing to draw there; it stays background.
        y0 = r - math.sqrt(max(r * r - (r - bar_w) ** 2, 0))

        top = curve(y0, r) + [(bar_w, r)]
        canvas.create_polygon([c for pt in top for c in pt], **kwargs)

        bottom = [(x, h - y) for x, y in curve(y0, r)] + [(bar_w, h - r)]
        canvas.create_polygon([c for pt in bottom for c in pt], **kwargs)

    canvas.create_rectangle(0, r, bar_w, h - r, **kwargs)


class StatCard(ctk.CTkFrame):
    """Summary card with a rounded accent strip that hugs the card's own
    rounded corners (drawn on one canvas so there's no visible seam)."""

    ICON_SIZE = 72   # fits inside CARD_H with even top/bottom breathing room
    ICON_PAD = 18    # right-edge inset, matching the card's other paddings

    def __init__(self, master, title, value, accent=COLOR_ACCENT, icon=None,
                 height=116, fill=COLOR_CARD, bg=COLOR_BG,
                 icon_size=ICON_SIZE, icon_pad=ICON_PAD,
                 title_size=13, value_size=30, **kwargs):
        super().__init__(master, fg_color="transparent", width=40, **kwargs)
        self.accent = accent
        self.fill = fill
        self.radius = 12
        self.bar_w = 5
        self.icon_pad = icon_pad

        # PhotoImage must be kept referenced for the lifetime of the canvas
        # item, or Tk renders nothing - hence storing it on self.
        self._icon = None
        if icon:
            img = Image.open(icon).convert("RGBA")
            img = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            self._icon = ImageTk.PhotoImage(img)

        self.canvas = tk.Canvas(self, width=40, height=height, bg=bg,
                                 highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._redraw)

        # Title/value are drawn straight onto the canvas as text items, NOT
        # as embedded CTkLabel windows: a label widget paints its own
        # background rectangle, and the parent color it auto-detects leaks
        # out as a 1px seam at the widget's edge - visible as a faint
        # vertical line right next to the text. Canvas text has no
        # background at all, so there's nothing to leak.
        # Negative font sizes = pixels. Tk reads positive sizes as points
        # (~1/3 bigger on a 96 DPI screen), while CTk widgets size their
        # fonts in pixels - so pixels here keeps this text identical to
        # the CTkLabels these items replaced.
        self._title = title.upper()
        self._value = value
        self._title_font = (FONT_FAMILY, -title_size, "bold")
        self._value_font = (FONT_FAMILY, -value_size, "bold")
        self._placed = False

    def _redraw(self, event=None):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 4 or h < 4:
            return
        self.canvas.delete("bg")
        draw_rounded_rect(self.canvas, 0, 0, w, h, self.radius, self.fill, tags="bg")
        draw_accent_strip(self.canvas, self.bar_w, self.radius, h, self.accent, tags="bg")
        if not self._placed:
            if self._icon:
                self.canvas.create_image(w - self.icon_pad, h / 2, anchor="e",
                                          image=self._icon, tags="icon")
            self.canvas.create_text(20, h * 0.34, anchor="w", text=self._title,
                                     font=self._title_font, fill=COLOR_SUBTEXT,
                                     tags="title")
            self.canvas.create_text(20, h * 0.68, anchor="w", text=self._value,
                                     font=self._value_font, fill=COLOR_TEXT,
                                     tags="value")
            self._placed = True
        else:
            # The freshly redrawn "bg" items stack above everything created
            # earlier (canvas z-order is creation order), so push them back
            # underneath, then re-anchor the foreground to the new size -
            # the mini stat cards are resized by their layout after the
            # first draw.
            self.canvas.tag_lower("bg")
            if self._icon:
                self.canvas.coords("icon", w - self.icon_pad, h / 2)
            self.canvas.coords("title", 20, h * 0.34)
            self.canvas.coords("value", 20, h * 0.68)

    def set_value(self, value):
        """Set the big number as literal text. Stored even before the card
        has been drawn, so a value set during construction isn't lost - the
        canvas items don't exist until the first <Configure> lands."""
        self._value = value
        if self._placed:
            self.canvas.itemconfig("value", text=value)

    def set_count(self, n):
        """Set the value from a raw integer, compacted for display
        (14300 -> '14.3k', 1_200_000 -> '1.2m')."""
        self.set_value(format_count(n))


