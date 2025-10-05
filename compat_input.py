import sys
if sys.version_info >= (3, 13):
    import pydirectinput as pyautogui
else:
    try:
        import pydirectinput as pyautogui
    except ImportError:
        import pyautogui
pyautogui.PAUSE = 0.0
pyautogui.FAILSAFE = False
