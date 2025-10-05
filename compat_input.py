# compat_input.py
try:
    import pydirectinput as pyautogui
except Exception:
    import pyautogui

pyautogui.PAUSE = 0.0
pyautogui.FAILSAFE = False
