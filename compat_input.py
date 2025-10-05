# compat_input.py
# Uniform input API for both pyautogui and pydirectinput.

import time

try:
    import pydirectinput as _pdi

    class _Shim:
        def __init__(self, backend):
            self._b = backend
            self.PAUSE = 0.0
            self.FAILSAFE = False  # pydirectinput has no failsafe

        # keyboard
        def press(self, key):
            self._b.press(key)

        def keyDown(self, key):
            self._b.keyDown(key)

        def keyUp(self, key):
            self._b.keyUp(key)

        def hotkey(self, *keys, interval: float = 0.0):
            # Emulate pyautogui.hotkey
            for k in keys:
                self._b.keyDown(k)
                if interval:
                    time.sleep(interval)
            for k in reversed(keys):
                self._b.keyUp(k)
                if interval:
                    time.sleep(interval)

        def typewrite(self, msg, interval: float = 0.0):
            # Emulate pyautogui.typewrite
            for ch in str(msg):
                self._b.press(ch)
                if interval:
                    time.sleep(interval)

        write = typewrite  # alias

        # mouse (pass-throughs commonly used by bot)
        def moveTo(self, *a, **kw):
            return self._b.moveTo(*a, **kw)

        def moveRel(self, *a, **kw):
            return self._b.moveRel(*a, **kw)

        def click(self, *a, **kw):
            return self._b.click(*a, **kw)

        def mouseDown(self, *a, **kw):
            return self._b.mouseDown(*a, **kw)

        def mouseUp(self, *a, **kw):
            return self._b.mouseUp(*a, **kw)

        def scroll(self, *a, **kw):
            return self._b.scroll(*a, **kw)

    pyautogui = _Shim(_pdi)

except Exception:
    # Fallback to real pyautogui when available
    import pyautogui  # type: ignore
    pyautogui.PAUSE = 0.0
    pyautogui.FAILSAFE = False