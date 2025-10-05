import numpy as np
import mss
import windows  # circular import is fine; used for hwnd
import ctypes
import time
from ctypes import wintypes

def _window_rect():
    rect = wintypes.RECT()
    if ctypes.windll.user32.GetWindowRect(windows.hwnd, ctypes.byref(rect)):
        return (rect.right - rect.left, rect.bottom - rect.top)
    return (2560, 1440)

# height used elsewhere in code as "screen_resolution"
_win_w, _win_h = _window_rect()
print(f"using {_win_w}x{_win_h} as screen resolution")

screen_resolution = _win_h  # 1080 or 1440 paths are preserved

# monitor box and ultrawide offset
if screen_resolution == 1080:
    mon = {"top": 0, "left": 0, "width": 1920, "height": 1080}
    ultra_offset_x = 0
elif screen_resolution == 1440:
    if _win_w >= 3440:
        mon = {"top": 0, "left": 0, "width": 3440, "height": 1440}
        ultra_offset_x = int((3440 - 2560) / 2)  # 440px center offset
    else:
        mon = {"top": 0, "left": 0, "width": 2560, "height": 1440}
        ultra_offset_x = 0
else:
    print(f"{_win_h} is not a supported height; expected 1080 or 1440")
    time.sleep(10)
    raise SystemExit(1)

def get_screen_roi(start_x, start_y, width, height):
    # center 2560-based ROIs on ultrawide
    left = start_x + (ultra_offset_x if screen_resolution == 1440 else 0)
    region = {"top": start_y, "left": left, "width": width, "height": height}
    with mss.mss() as sct:
        shot = sct.grab(region)
        return np.array(shot)

if __name__ == "__main__":
    pass
