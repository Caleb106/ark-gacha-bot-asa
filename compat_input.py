# compat_input.py
# Uniform input API for both pyautogui and pydirectinput, with small delays.

import time

DEFAULT_INTERVAL = 0.02  # ~20 ms between actions

try:
    import pydirectinput as _pdi

    class _Shim:
        def __init__(self, backend):
            self._b = backend
            self.PAUSE = DEFAULT_INTERVAL
            self.FAILSAFE = False  # no failsafe in pydirectinput

        def _sleep(self, t=None):
            time.sleep(self.PAUSE if t is None else float(t))

        # --- keyboard ---
        def press(self, key):
            self._b.press(key)
            self._sleep()

        def keyDown(self, key):
            self._b.keyDown(key)
            self._sleep()

        def keyUp(self, key):
            self._b.keyUp(key)
            self._sleep()

        def hotkey(self, *keys, interval=None):
            iv = DEFAULT_INTERVAL if interval is None else float(interval)
            for k in keys:
                self._b.keyDown(k)
                time.sleep(iv)
            for k in reversed(keys):
                self._b.keyUp(k)
                time.sleep(iv)

        def typewrite(self, msg, interval=None):
            iv = DEFAULT_INTERVAL if interval is None else float(interval)
            for ch in str(msg):
                self._b.press(ch)
                time.sleep(iv)

        write = typewrite  # alias

        # --- mouse ---
        def moveTo(self, *a, **kw):
            return self._b.moveTo(*a, **kw)

        def moveRel(self, *a, **kw):
            return self._b.moveRel(*a, **kw)

        def click(self, *a, **kw):
            r = self._b.click(*a, **kw)
            self._sleep()
            return r

        def mouseDown(self, *a, **kw):
            r = self._b.mouseDown(*a, **kw)
            self._sleep()
            return r

        def mouseUp(self, *a, **kw):
            r = self._b.mouseUp(*a, **kw)
            self._sleep()
            return r

        def scroll(self, *a, **kw):
            r = self._b.scroll(*a, **kw)
            self._sleep()
            return r

    pyautogui = _Shim(_pdi)

except Exception:
    # Fallback to real pyautogui; apply the same small pause
    import pyautogui  # type: ignore
    pyautogui.PAUSE = DEFAULT_INTERVAL
    pyautogui.FAILSAFE = False