# TBH Stash Bot

Python image-search bot that finds UI templates on screen and clicks them.

## Requirements

- Windows
- Python 3.10+

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

## Usage

1. Open the game and stand near your stash.
2. In the GUI **Screen** tab, set **UI scale** to match TBH (1, 1.25, 1.5, or 2), then click **Draw search region** and left-drag over your stash UI.
3. Adjust **Timing** and **Templates** tabs as needed (each field has a short explanation).
4. On the **Run** tab, choose log level and click **Start Stash**, then focus the game window.

The bot loops through these steps:

1. Open chest — right-clicks boss or normal chest icon (boss checked first)
2. Auto Fill — waits a **random** delay, then checks for combine
   - **If combine appears:** clicks combine → back → restarts from step 1
   - **If not:** continues to Stash All
3. Stash All
4. Close/back

While running, a **background timer** (random interval) tries Stash All → Sort with a random gap between clicks, then presses Space.

### Anti-detection randomization

All delays and click positions use **min/max ranges** configured in the GUI (Timing tab):

- Poll retries while waiting for UI
- Pause after successful clicks
- Combine check wait after Auto Fill
- Periodic stash/sort cycle interval and stash→sort gap
- Pixel offset from template center on every click

Wider ranges look more human but slow the bot slightly.

## Configuration

All settings are edited in the GUI and saved to `resources/config.yml` when you close the app. Template filenames are **base names** (e.g. `auto_fill.png`); scaled assets use suffixes `_1-25`, `_1-50`, or `_2` depending on window scale.

## Building an executable (optional)

```bash
pip install pyinstaller
pyinstaller --add-data "resources;resources" --add-data "assets;assets" bot.py
```

The executable will be in `dist/bot/bot.exe`.

## Template images

Place template PNGs in `assets/`. Capture small, unique crops at the same resolution and scale you play at.
