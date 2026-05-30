# AGENTS.md — TBH Helper

Guidance for AI agents working in this repository.

## Project summary

Windows-only Python helper for **Task Bar Hero (TBH)**. Uses **tkinter** GUI, **OpenCV** template matching, and **Win32** mouse/keyboard input to automate stash flow (open chest → auto fill → stash all → close) plus a background periodic stash/sort loop.

Entry point: `main.py` → `gui_init()` → `gv.root.mainloop()`.

## Requirements

- **Windows only** (pywin32, screen capture, input simulation)
- Python 3.10+
- Dependencies in `requirements.txt`

Do not introduce cross-platform abstractions unless explicitly requested. Do not replace Win32 input with other libraries.

## Layout

```
main.py                # Entry point
gui/                   # Tkinter UI (tabs, region draw, start/stop)
functionality/         # stash_loop state machine, image_search
utils/                 # config load/save, global_variables
wrappers/              # win32api, logging
resources/config.yml   # Persisted settings (saved on app close)
assets/                # Template PNGs (base + scaled variants)
```

## Configuration

- Runtime config lives in `utils/config.py` as `dict` (Tk `IntVar` / `DoubleVar` / `StringVar` bound to GUI).
- YAML is loaded at import; `save_data()` writes GUI values back on window close.
- **Do not** add `.env` or secret handling unless asked — not used today.

### Important config concepts

| Area | Notes |
|------|--------|
| `search_region` | Screen coords for template search; set via GUI draw overlay or numeric fields |
| `window_scale` | `1`, `1.25`, `1.5`, `2` — selects scaled template suffix (`_1-25`, `_1-50`, `_2`; scale `1` = no suffix) |
| Template names in YAML/GUI | **Base names only** (e.g. `auto_fill.png`); resolve via `template_path_for()` |
| Timings | Min/max ranges in **seconds**; use `random_timeout()` / `random_delay_ms()` — avoid fixed delays for automation actions |
| `log_lvl` | Applied when user clicks Start Stash (`apply_log_level()`) |

Process-facing name is **`TBH Helper`** (`APP_DISPLAY_NAME` in `utils/global_variables.py`). Do not add "bot" to window titles, logger names, or packaged exe names.

When adding new template references, wire through `template_path_for()` so window scale works.

## GUI conventions

- Main panel: `gui/stash_panel.py` — tabbed notebook + **footer** with status and Start/Stop (always visible).
- Region draw: `gui/gui_functions.py` — use semi-transparent overlay (`-alpha`), **not** `-transparentcolor` on Windows (clicks pass through).
- Prefer help text under settings explaining what each field changes.
- Keep window resizable; avoid breaking scrollable tabs.

## Automation logic

- Core loop: `functionality/stash_loop.py` — step index in `gv.current_step_index`, scheduled via `gv.root.after`.
- Step names are string-matched (`open_chest`, `auto_fill`, `stash_all`, …); changing step order/names requires YAML + code alignment.
- Image search: `functionality/image_search.py` — `find_template(region, path, threshold)` returns center in **screen** coordinates.
- Clicks: `wrappers/win32api_wrapper.py`; apply jitter via `random_click_offset()` in stash_loop, not raw center clicks.

## Assets

Scaled templates follow naming: `{base_stem}{suffix}.png` where suffix is `""`, `_1-25`, `_1-50`, or `_2`.

If a scaled file is missing, `template_path_for()` warns and falls back to the base file.

## Coding standards

- **Minimal diffs** — match existing style (plain functions, no over-abstraction).
- Reuse `dict`, `gv`, existing helpers before adding new modules.
- Comments only for non-obvious behavior (Windows quirks, timing rationale).
- Do not commit secrets, `venv/`, or `.cursor/`.
- Do not create git commits or PRs unless the user asks.

## Running locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Optional EXE and GitHub releases: see `RELEASES.md`. CI: `.github/workflows/build.yml`.

## Common tasks

| Task | Primary files |
|------|----------------|
| New GUI setting | `gui/stash_panel.py`, `utils/config.py`, `resources/config.yml` |
| New automation step | `functionality/stash_loop.py`, `resources/config.yml` |
| Template / scale behavior | `utils/config.py` (`template_path_for`, `scaled_template_name`) |
| Region overlay | `gui/gui_functions.py` |
| Randomization | `utils/config.py` helpers, callers in `stash_loop.py` |

## Testing changes

- Verify imports: `python -c "import gui.stash_panel; from utils.config import template_path_for"`
- Manual test on Windows with game focused; no automated test suite in repo.
- Check console logs at INFO/DEBUG when touching template match or region draw.
