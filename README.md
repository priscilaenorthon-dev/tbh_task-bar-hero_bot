# TBH Helper

Python helper that finds UI templates on screen and clicks them.

## Support 

https://saweria.co/goldiegaming | https://ko-fi.com/alandtiwa

## Requirements

- Windows
- Python 3.10+

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Usage

1. Open the game and stand near your stash.
2. In the GUI **Screen** tab, set **UI scale** to match TBH (1, 1.25, 1.5, or 2), then click **Draw search region** and left-drag over your stash UI.
3. Adjust **Timing** and **Templates** tabs as needed (each field has a short explanation).
4. On the **Run** tab, choose log level and click **Start Stash**, then focus the game window.

The app loops through these steps:

1. Open chest — right-clicks boss or normal chest icon (boss checked first)
2. Auto Fill — waits a **random** delay, then checks for combine
   - **If combine appears:** clicks combine → back → restarts from step 1
   - **If not:** continues to Stash All
3. Stash All
4. Close/back

While running, a **background timer** (random interval) tries Stash All → Sort with a random gap between clicks, then presses Space.

### Missing UI / stuck prevention

If a chest icon or step button is not found, the helper **retries** on the loop poll interval (Timing → **Loop retry**) until **Step wait limit** expires (default about 45–60 seconds, random in range). It then **skips to the next step** instead of waiting forever or restarting the whole loop.

| Situation | Behavior |
|-----------|----------|
| Chest or step button missing (after step wait limit) | Skip to the next step in the list |
| Combine prompt missing after Auto Fill | Skip ahead to Stash All (one check, no long wait) |
| `back_arrow` missing after combine (after step wait limit) | Skip to Stash All |
| Combine flow completes (combine + back found) | Restarts from open chest |
| Periodic stash/sort buttons missing | Skips that click for the cycle; continues on the next interval |

Status text and logs show `Skipped …, next: …` when a step is skipped.

### Anti-detection randomization

All delays and click positions use **min/max ranges** configured in the GUI (Timing tab):

- Poll retries while waiting for UI (**Loop retry**)
- Maximum time to keep waiting for one button or chest icon (**Step wait limit**)
- Pause after successful clicks or after skipping a step
- Combine check wait after Auto Fill
- Periodic stash/sort cycle interval and stash→sort gap
- Pixel offset from template center on every click

Wider ranges look more human but slow the loop slightly. A shorter step wait limit recovers faster when the UI is wrong or the game state changed; a longer limit avoids skipping during slow animations.

## Configuration

All settings are edited in the GUI and saved to `resources/config.yml` when you close the app. Template filenames are **base names** (e.g. `auto_fill.png`); scaled assets use suffixes `_1-25`, `_1-50`, or `_2` depending on window scale.

## Architecture

Developer reference for the stash **state machine** (steps, combine branch, skip/restart) and **template matcher** (capture, OpenCV, scale resolution):

**[docs/automation.md](docs/automation.md)**

## Building an executable

See **[RELEASES.md](RELEASES.md)** for local PyInstaller builds and publishing GitHub releases.

Quick local build:

```bash
pip install pyinstaller
pyinstaller --name TBHHelper --add-data "resources;resources" --add-data "assets;assets" main.py
```

Output: `dist/TBHHelper/TBHHelper.exe`

## Template images

Place template PNGs in `assets/`. Capture small, unique crops at the same resolution and scale you play at.
