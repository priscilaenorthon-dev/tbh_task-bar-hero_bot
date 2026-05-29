from functools import partial

import utils.global_variables as gv
from gui.gui_functions import on_closing
from gui.stash_panel import stash_panel


def gui_init():
    gv.root.minsize(480, 520)
    gv.root.geometry("500x560")
    gv.root.resizable(True, True)
    gv.root.title("TBH Stash Bot")
    gv.root.protocol("WM_DELETE_WINDOW", partial(on_closing))
    stash_panel()
