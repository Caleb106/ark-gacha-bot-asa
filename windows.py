import ctypes
import local_player
import screen
import time
from ctypes import wintypes

def find_window_by_title(title):
    return ctypes.windll.user32.FindWindowW(None, title)

hwnd = find_window_by_title("ArkAscended")

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_MOVE_NOCOALESCE = 0x2000

if ctypes.sizeof(ctypes.c_void_p) == 8:
    ULONG_PTR = ctypes.c_uint64
else:
    ULONG_PTR = ctypes.c_uint32

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]

PIXELS_PER_DEGREE = 128.6 / 90.0
max_lr_sens = 3.2
max_ud_sens = 3.2
max_fov = 1.25

def turn(x: int, y: int):
    dx = int(round(x * PIXELS_PER_DEGREE * (max_lr_sens / local_player.get_look_lr_sens()) * (max_fov / local_player.get_fov())))
    dy = int(round(y * PIXELS_PER_DEGREE * (max_ud_sens / local_player.get_look_ud_sens()) * (max_fov / local_player.get_fov())))
    ev = INPUT(type=INPUT_MOUSE)
    ev.mi = MOUSEINPUT(dx=dx, dy=dy, mouseData=0, dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_MOVE_NOCOALESCE, time=0, dwExtraInfo=0)
    ctypes.windll.user32.SendInput(1, ctypes.byref(ev), ctypes.sizeof(INPUT))

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202

def _ux_offset_x():
    return screen.ultra_offset_x if (screen.screen_resolution == 1440 and screen.mon["width"] > 2560) else 0

def click(x, y):
    ox = _ux_offset_x()
    lp = ((y << 16) | (x + ox))
    ctypes.windll.user32.PostMessageW(hwnd, WM_LBUTTONDOWN, 0, lp)
    ctypes.windll.user32.PostMessageW(hwnd, WM_LBUTTONUP,   0, lp)
