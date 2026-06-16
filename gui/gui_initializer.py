from functools import partial
from tkinter import ttk

import utils.global_variables as gv
from gui.gui_functions import on_closing
from gui.stash_panel import stash_panel


def gui_init():
    gv.root.minsize(600, 580)
    gv.root.geometry("680x680")
    gv.root.resizable(True, True)
    gv.root.title(gv.APP_DISPLAY_NAME)
    gv.root.protocol("WM_DELETE_WINDOW", partial(on_closing))

    style = ttk.Style()
    style.theme_use("clam")

    stash_panel()
