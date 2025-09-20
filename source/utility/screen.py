import numpy as np
import mss
from ctypes import wintypes
import ctypes
import time 

def find_window_by_title(title):
    return ctypes.windll.user32.FindWindowW(None, title)


def find_screen_size():
    hwnd = find_window_by_title("ArkAscended") 
    rect = wintypes.RECT()
    if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        height = rect.bottom - rect.top
        width = rect.right - rect.left
        print(f"application size is {width}x{height}")
        return width,height
    
screen_width,screen_height = find_screen_size()

if (screen_width,screen_height) == (1920,1080):
    mon = {"top": 0, "left": 0, "width": 1920, "height": 1080}
    screen_resolution = screen_height
elif (screen_width,screen_height) == (2560,1440):
    mon = {"top": 0, "left": 0, "width": 2560, "height": 1440}
    screen_resolution = screen_height
else:
    print(f"{screen_width}x{screen_height} is not a valid screen res it needs to be 1920x1080 or 2560x1440")
    input(f"")# prevents the closing of the window instantly  
    exit()

def get_screen_roi(start_x, start_y, width, height):

    region = {"top": start_y, "left": start_x, "width": width, "height": height}
    with mss.mss() as sct:
        screenshot = sct.grab(region)
        return np.array(screenshot)
    
if __name__ =="__main__":
    pass