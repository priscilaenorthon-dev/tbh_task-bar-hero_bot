from functools import partial
from tkinter import Button, Canvas, Entry, Frame, Label, Scrollbar, StringVar, ttk

import utils.global_variables as gv
from gui.gui_functions import open_set_region_drag, popup_rectangle_window, start_stash
from utils.config import dict

_HELP_FONT = ("Segoe UI", 8)
_SECTION_FONT = ("Segoe UI", 10, "bold")
_LABEL_FONT = ("Segoe UI", 9)


def stash_panel():
    outer = Frame(gv.root, padx=8, pady=8)
    outer.pack(fill="both", expand=True)

    notebook = ttk.Notebook(outer)
    notebook.pack(fill="both", expand=True)

    _screen_tab(notebook)
    _timing_tab(notebook)
    _templates_tab(notebook)
    _control_tab(notebook)

    footer = Frame(outer, pady=(8, 0))
    footer.pack(fill="x", side="bottom")

    gv.status_label = Label(
        footer,
        text=gv.status_message,
        wraplength=460,
        justify="left",
        font=_LABEL_FONT,
    )
    gv.status_label.pack(fill="x", pady=(0, 6))

    start_button = Button(footer, text="Start Stash", width=24)
    start_button.configure(command=partial(start_stash, start_button))
    start_button.pack(fill="x")


def _scrollable_tab(notebook, title):
    tab = Frame(notebook)
    notebook.add(tab, text=title)

    canvas = Canvas(tab, highlightthickness=0)
    scrollbar = Scrollbar(tab, orient="vertical", command=canvas.yview)
    inner = Frame(canvas)

    inner.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    return inner


def _screen_tab(notebook):
    panel = _scrollable_tab(notebook, "Screen")
    row = 0

    row = _section(panel, row, "Search region")
    row = _help(
        panel,
        row,
        "Screen rectangle where the bot looks for buttons and chest icons. "
        "Smaller areas run faster; too small and templates may be missed.",
    )
    row = _region_field(panel, row, "X (left)", dict["search_region"]["x"])
    row = _region_field(panel, row, "Y (top)", dict["search_region"]["y"])
    row = _region_field(panel, row, "Width", dict["search_region"]["width"])
    row = _region_field(panel, row, "Height", dict["search_region"]["height"])

    region = dict["search_region"]
    draw_button = Button(panel, text="Draw search region")
    draw_button.configure(
        command=partial(
            open_set_region_drag,
            region["x"],
            region["y"],
            region["width"],
            region["height"],
        )
    )
    draw_button.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 4))
    row += 1

    preview_button = Button(panel, text="Preview region")
    preview_button.configure(
        command=partial(
            popup_rectangle_window,
            preview_button,
            region["x"],
            region["y"],
            region["width"],
            region["height"],
        )
    )
    preview_button.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12))
    row += 1
    row = _help(
        panel,
        row,
        "Draw: dimmed fullscreen overlay — left-click and drag (watch the console for Region draw: logs). "
        "Set log level to DEBUG on the Run tab for drag coordinates. Preview: click once to close.",
    )

    row = _section(panel, row, "Template matching")
    row = _range_row(
        panel,
        row,
        "Match threshold",
        dict["matching"]["threshold"],
        dict["matching"]["threshold"],
        is_single=True,
        suffix="",
    )
    row = _help(
        panel,
        row,
        "How closely a screenshot must match a template (0–1). Lower = more lenient, more false positives. "
        "Changes apply on the next search while the bot is running.",
    )


def _timing_tab(notebook):
    panel = _scrollable_tab(notebook, "Timing")
    row = 0

    row = _section(panel, row, "Poll delays (while waiting for UI)")
    row = _ms_range_row(panel, row, "Loop retry", dict["timeouts"]["loop_ms"])
    row = _help(
        panel,
        row,
        "When a button or chest icon is not found, the bot waits a random time in this range (ms) "
        "before searching again. Wider ranges look less robotic.",
    )

    row = _section(panel, row, "After successful clicks")
    row = _seconds_range_row(panel, row, "Pause after click", dict["timeouts"]["after_click"])
    row = _help(
        panel,
        row,
        "Random pause (seconds) after stash steps, opening a chest, or finishing combine. "
        "Gives the game UI time to animate before the next action.",
    )

    row = _section(panel, row, "Auto Fill → Combine check")
    row = _ms_range_row(panel, row, "Wait before combine", dict["combine_flow"]["wait_ms"])
    row = _help(
        panel,
        row,
        "After clicking Auto Fill, the bot waits a random time in this range (ms), then looks for "
        "the combine prompt. Too short may miss the prompt; too long slows the loop.",
    )

    row = _section(panel, row, "Background stash / sort")
    row = _ms_range_row(
        panel, row, "Cycle interval", dict["periodic_stash_sort"]["interval_ms"]
    )
    row = _help(
        panel,
        row,
        "While running, the bot periodically tries Stash All + Sort and presses Space. "
        "Each cycle is scheduled after a random delay in this range (ms).",
    )
    row = _ms_range_row(
        panel, row, "Stash → Sort gap", dict["periodic_stash_sort"]["between_clicks_ms"]
    )
    row = _help(
        panel,
        row,
        "Random delay (ms) between the periodic Stash All click and the Sort click when both are found.",
    )

    row = _section(panel, row, "Click position jitter")
    row = _int_range_row(
        panel, row, "Pixel offset", dict["randomization"]["click_offset_px"]
    )
    row = _help(
        panel,
        row,
        "Each click adds a random X/Y offset within this range (pixels) from the template center. "
        "Helps avoid identical pixel-perfect clicks. Use negative min (e.g. -8) and positive max (e.g. 8).",
    )


def _templates_tab(notebook):
    panel = _scrollable_tab(notebook, "Templates")
    row = 0

    row = _section(panel, row, "Chest icons (open stash)")
    row = _help(
        panel,
        row,
        "Filenames in the assets/ folder. Boss chest is checked first, then normal chest.",
    )
    for entry in dict["chest_check"]:
        row = _template_row(panel, row, entry["name"], entry["template"])

    row = _section(panel, row, "Main stash steps")
    row = _help(
        panel,
        row,
        "Order is fixed: open chest → auto fill → stash all → close. Only steps with templates are listed.",
    )
    for step in dict["steps"]:
        if "template" not in step:
            continue
        row = _template_row(panel, row, step["name"], step["template"])

    row = _section(panel, row, "Combine flow")
    row = _template_row(panel, row, "Combine button", dict["combine_flow"]["template"])
    row = _template_row(panel, row, "Back arrow", dict["combine_flow"]["back_template"])

    row = _section(panel, row, "Periodic stash / sort")
    row = _template_row(
        panel, row, "Stash All", dict["periodic_stash_sort"]["stash_template"]
    )
    row = _template_row(panel, row, "Sort", dict["periodic_stash_sort"]["sort_template"])


def _control_tab(notebook):
    panel = Frame(notebook, padx=10, pady=10)
    notebook.add(panel, text="Run")

    row = 0
    row = _section(panel, row, "Logging")
    log_values = ("DEBUG", "INFO", "WARNING", "ERROR")
    Label(panel, text="Log level", font=_LABEL_FONT).grid(row=row, column=0, sticky="w")
    log_combo = ttk.Combobox(
        panel,
        textvariable=dict["log_lvl"],
        values=log_values,
        state="readonly",
        width=12,
    )
    log_combo.grid(row=row, column=1, sticky="w", padx=(8, 0))
    row += 1
    row = _help(
        panel,
        row,
        "Console detail while the bot runs. DEBUG shows every template score; INFO is recommended. "
        "Applied when you click Start Stash (button below the tabs).",
    )
    row = _help(
        panel,
        row,
        "All settings are read live while the bot runs. "
        "Config is saved to resources/config.yml when you close the app.",
    )


def _section(parent, row, title):
    Label(parent, text=title, font=_SECTION_FONT).grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(10, 4)
    )
    return row + 1


def _help(parent, row, text):
    Label(
        parent,
        text=text,
        font=_HELP_FONT,
        fg="#555555",
        wraplength=440,
        justify="left",
    ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 6))
    return row + 1


def _region_field(parent, row, label, variable):
    Label(parent, text=label, font=_LABEL_FONT).grid(row=row, column=0, sticky="w")
    Entry(parent, textvariable=variable, width=10).grid(
        row=row, column=1, sticky="w", padx=(8, 0)
    )
    return row + 1


def _ms_range_row(parent, row, label, range_dict):
    return _range_row(
        parent,
        row,
        label,
        range_dict["min"],
        range_dict["max"],
        suffix=" ms",
    )


def _seconds_range_row(parent, row, label, range_dict):
    return _range_row(
        parent,
        row,
        label,
        range_dict["min"],
        range_dict["max"],
        suffix=" s",
    )


def _int_range_row(parent, row, label, range_dict):
    return _range_row(
        parent,
        row,
        label,
        range_dict["min"],
        range_dict["max"],
        suffix=" px",
    )


def _range_row(parent, row, label, min_var, max_var, is_single=False, suffix=""):
    Label(parent, text=label, font=_LABEL_FONT).grid(row=row, column=0, sticky="w")
    frame = Frame(parent)
    frame.grid(row=row, column=1, sticky="w", padx=(8, 0))

    if is_single:
        Entry(frame, textvariable=min_var, width=8).pack(side="left")
    else:
        Label(frame, text="min", font=_HELP_FONT).pack(side="left")
        Entry(frame, textvariable=min_var, width=7).pack(side="left", padx=(4, 8))
        Label(frame, text="max", font=_HELP_FONT).pack(side="left")
        Entry(frame, textvariable=max_var, width=7).pack(side="left", padx=(4, 0))

    if suffix:
        Label(frame, text=suffix.strip(), font=_HELP_FONT).pack(side="left", padx=(6, 0))
    return row + 1


def _template_row(parent, row, label, variable: StringVar):
    Label(parent, text=label, font=_LABEL_FONT).grid(row=row, column=0, sticky="w")
    Entry(parent, textvariable=variable, width=28).grid(
        row=row, column=1, sticky="w", padx=(8, 0)
    )
    return row + 1
