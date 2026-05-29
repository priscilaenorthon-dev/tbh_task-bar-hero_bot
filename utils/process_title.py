import sys

import utils.global_variables as gv


def apply_process_title():
    """Set visible process/window names on Windows (console + taskbar)."""
    gv.root.title(gv.APP_DISPLAY_NAME)
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleTitleW(gv.APP_DISPLAY_NAME)
    except (AttributeError, OSError):
        pass
