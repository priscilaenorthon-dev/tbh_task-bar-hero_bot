import time
import win32api
import win32con


def click_mouse_with_coordinates(x, y):
    win32api.SetCursorPos((int(x), int(y)))
    time.sleep(0.05)   # pequena pausa para o jogo registrar o cursor na posição
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    time.sleep(0.05)   # pausa entre down e up
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)


def right_click_mouse_with_coordinates(x, y):
    win32api.SetCursorPos((int(x), int(y)))
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)

def space_bar():
    win32api.keybd_event(0x20, 0, 0, 0)
    win32api.keybd_event(0x20, 0, win32con.KEYEVENTF_KEYUP, 0)


def scroll_at(x, y, delta):
    """Roda o scroll do mouse na posição (x,y). delta > 0 = cima, delta < 0 = baixo."""
    win32api.SetCursorPos((int(x), int(y)))
    win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, int(delta), 0)
