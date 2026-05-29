import utils.global_variables as gv
from gui.gui_initializer import gui_init
from utils.process_title import apply_process_title

apply_process_title()
gui_init()
gv.root.mainloop()
