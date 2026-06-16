from pathlib import Path
from tkinter import Tk

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "resources" / "config.yml"

# Shown in window title, taskbar, and console — avoid "bot" in process-facing names
APP_DISPLAY_NAME = "TBH Helper"
APP_LOGGER_NAME = "tbh_helper"

root = Tk()
continue_stash = False
current_step_index = 0
status_message = "Ocioso"
status_label = None
combine_check_pending = False
step_wait_deadline = None

# Map Runner state
continue_map_runner = False
mr_current_map_index = 0
mr_map_last_collected = {}
mr_stash_phase_deadline = None
mr_status_label = None
mr_status_message = "Ocioso"
