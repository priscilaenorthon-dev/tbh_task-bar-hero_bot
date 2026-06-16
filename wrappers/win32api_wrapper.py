import math
import random
import time
import win32api
import win32con


def _move_mouse_human(x2, y2):
    """Move cursor to (x2, y2) along a slight Bezier curve to simulate human movement."""
    x1, y1 = win32api.GetCursorPos()
    dist = math.hypot(x2 - x1, y2 - y1)
    if dist < 20:
        win32api.SetCursorPos((int(x2), int(y2)))
        return
    steps = random.randint(15, 25)
    # Random control point offset gives the curve a natural arc
    cx = (x1 + x2) / 2 + random.randint(-60, 60)
    cy = (y1 + y2) / 2 + random.randint(-60, 60)
    step_delay = random.uniform(0.004, 0.010)
    for i in range(1, steps + 1):
        t = i / steps
        bx = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t ** 2 * x2
        by = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t ** 2 * y2
        win32api.SetCursorPos((int(bx), int(by)))
        time.sleep(step_delay)
    win32api.SetCursorPos((int(x2), int(y2)))


def click_mouse_with_coordinates(x, y):
    _move_mouse_human(x, y)
    time.sleep(random.uniform(0.03, 0.07))  # settle after arrival
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    time.sleep(random.uniform(0.04, 0.10))  # variable hold duration
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)


def right_click_mouse_with_coordinates(x, y):
    _move_mouse_human(x, y)
    time.sleep(random.uniform(0.03, 0.07))  # settle after arrival
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
    time.sleep(random.uniform(0.04, 0.10))  # variable hold duration
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)


def space_bar():
    win32api.keybd_event(0x20, 0, 0, 0)
    time.sleep(random.uniform(0.04, 0.09))  # variable key hold
    win32api.keybd_event(0x20, 0, win32con.KEYEVENTF_KEYUP, 0)


def scroll_at(x, y, delta):
    """Roda o scroll do mouse na posição (x,y). delta > 0 = cima, delta < 0 = baixo."""
    _move_mouse_human(x, y)
    time.sleep(random.uniform(0.02, 0.05))
    win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, int(delta), 0)
