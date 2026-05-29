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
2. In the GUI, set the **search region** (`x`, `y`, `width`, `height`) to cover the stash UI area. Smaller regions run faster.
3. Click **Preview region** to verify the green rectangle.
4. Adjust **match threshold** if needed (default `0.7`; lower = more lenient).
5. Click **Start Stash** and focus the game window.

The bot loops through these steps:

1. Open chest — right-clicks `boss_chest_icon.png` or `chest_icon.png` (boss chest checked first)
2. Auto Fill (`auto_fill.png`)
   - Waits **5 seconds**, then checks for a combine prompt (`combine.png`)
   - **If combine appears:** clicks combine → clicks back → restarts from step 1
   - **If combine does not appear:** continues to Stash All
3. Stash All (`stash_all.png`)
4. Close/back (`back_arrow.png`)

Combine wait time is configured in `resources/config.yml` under `combine_flow.wait_ms` (default `5000`).

While the bot is running, it also **every 5 seconds** tries to click **Stash All** then **Sort** (`periodic_stash_sort` in config). If either button is not visible, that cycle is skipped quietly.

## Configuration

Settings are saved to `resources/config.yml` when you close the app. You can also edit timeouts and the step sequence there.

## Building an executable (optional)

```bash
pip install pyinstaller
pyinstaller --add-data "resources;resources" --add-data "assets;assets" bot.py
```

The executable will be in `dist/bot/bot.exe`.

## Template images

Place template PNGs in `assets/`. Capture small, unique crops at the same resolution and scale you play at.
