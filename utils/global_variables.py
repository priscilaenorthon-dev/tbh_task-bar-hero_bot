from pathlib import Path
from tkinter import Tk

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "resources" / "config.yml"

# Shown in window title, taskbar, and console — avoid "bot" in process-facing names
APP_DISPLAY_NAME = "TBH Helper"
APP_LOGGER_NAME = "tbh_helper"

root = Tk()
continue_stash = False
stash_paused = False
current_step_index = 0
status_message = "Ocioso"
status_label = None
combine_check_pending = False
step_wait_deadline = None

# Chest session counters
session_chest_count = 0
session_boss_chest_count = 0
chests_per_map = {}

# Counter UI labels (set by stash_panel)
lbl_chest_count = None
lbl_boss_chest_count = None
lbl_total_count = None

# Activity log widget and log path label (set by stash_panel)
activity_log_widget = None
lbl_log_path = None

# Map Runner state
continue_map_runner = False
mr_current_map_index = 0
mr_map_last_collected = {}
mr_stash_phase_deadline = None
mr_status_label = None
mr_status_message = "Ocioso"
