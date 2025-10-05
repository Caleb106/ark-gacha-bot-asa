# compat_input.py
import sys

if sys.version_info >= (3, 13):
    import pydirectinput as pyautogui
else:
    import pyautogui

pyautogui.PAUSE = 0.0
pyautogui.FAILSAFE = False
