# AGENTS.md

## Project

Windows desktop automation for Ark: Survival Ascended, written in Python. The app provides a CustomTkinter GUI, a task scheduler, Discord control, and game automation using PyAutoGUI, image matching, and OCR.

Target Python 3.11, as configured in `setup.bat`. Treat live game automation separately from UI and persistence checks: passing those checks does not establish that the bot works in game.

## Entry points and setup

Run commands from the repository root; several backend paths are relative to the working directory.

```powershell
# Create an environment if one is not already available.
py -3.11 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Open the GUI.
.\venv\Scripts\python.exe main.py

# Start the scheduler without Discord.
.\venv\Scripts\python.exe task_manager.py

# Start the Discord bot without the GUI.
.\venv\Scripts\python.exe main_program.py
```

- Verify the existing virtual environment works before using it; a copied environment may reference an unavailable Python installation.
- Tesseract OCR must be installed. Its executable is configured through `ocr_path` in `settings/settings.json`.
- `setup.bat` installs prerequisites and dependencies. It can download and launch installers.
- `run.bat` runs `git pull` before opening the GUI. Use the direct Python command for local UI checks to avoid changing the checkout.
- Configure Discord credentials and channel IDs through Settings. Do not print or copy credentials into logs, examples, or test fixtures.

## Code map

| Location | Responsibility |
| --- | --- |
| `main.py` | Creates the GUI and starts Tk's event loop. |
| `UI/UI.py` | App window, sidebar, Dashboard, Settings, Stations page shell, Support, and subprocess controls. |
| `UI/cards.py` | Shared `StatCard`, rounded-rectangle drawing, and curved accent-strip drawing. |
| `UI/theme.py` | Shared colors and font family. |
| `UI/station_editor.py` | Gacha/Pego list and detail editors, station cards, autosave, removal, change logging, and Crafting panel. |
| `UI/station_store.py` | Station JSON loading, validation, and atomic writes. No game-automation imports. |
| `UI/resources/store.py` | Persistent resource counters and archives. |
| `UI/resources/render.py` | Resource summary image rendering for Discord. |
| `settings/store.py` | Settings defaults, types, loading, and saving. |
| `settings/__init__.py` | Settings exposed as module attributes for backend callers, loaded at import time. |
| `task_manager.py` | Priority-based task scheduling and loading station tasks. |
| `main_program.py`, `source/discord_commands/` | Discord startup and commands. |
| `source/gacha_bot/` | Farming routines, task implementations, deposits, and supporting structures. |
| `source/ASA/`, `source/utility/` | Game interactions, station metadata, screen capture, OCR, and image matching. |
| `logger/logger.py` | Shared logger, log archives, and exception handling. |
| `tools/recovery.py` | Quarantines corrupt save files in `CORRUPTED_SAVEFILES/`. |
| `app_info.py` | Application name, version, and project links. |

Preserve existing directory spellings such as `source/ASA/strucutres/` when referencing imports.

## Configuration and persistence

- `settings/settings.json` is the GUI/backend settings file. Do not confuse it with `json_files/settings.json`.
- `json_files/pego.json` contains a list of station objects with `name`, `teleporter`, and positive integer `delay` in seconds.
- `json_files/gacha.json` contains a list of station objects with `name`, `teleporter`, `resource_type`, and `side` (`left` or `right`).
- `json_files/stations.json` supplies position and orientation metadata used by `source/ASA/stations/custom_stations.py`; it is separate from the Gacha/Pego task lists.
- Resource totals are stored in `UI/resources/resources.json`.
- Station edits require restarting the bot to apply them to scheduled tasks. Do not imply that saving reconfigures an already running scheduler.

Preserve user configuration, unknown JSON fields, resource totals, and unrelated working-tree edits. Use repository-relative-to-module paths for new persistence code rather than depending on the launch directory.

Station saves validate the whole list and replace the destination through a temporary file in the same directory. Invalid edits and failed writes must not overwrite the last valid file. Keep names unique within each station type. Do not silently reset malformed station files.

When saving only part of Settings, merge with the current settings so other pages' values and unknown keys survive.

## UI conventions

- Reuse `UI/cards.py` for cards, including their rounded silhouette and full-height accent strip. Do not approximate the shared design with a separate polygon or an inset vertical line.
- Keep colors in `UI/theme.py`. Match existing typography, padding, and hover/selection states.
- The window currently uses a fixed 1280 by 800 layout with explicit scaling settings. Check changes at that size. Canvas fonts use negative sizes for pixels.
- Station cards use the shared `StatCard` component, a 60px height, and left-aligned name/details.
- Preserve the Stations category rail and list/detail layout. Pegos and Gachas have independent save states.
- Typing autosaves after a 600ms pause; toggles save immediately. Page departure flushes pending station saves.
- New stations remain drafts until required fields are valid. Removal confirms the station name and persists before changing the visible selection.
- Show validation and save failures accurately; do not report a change as saved when persistence failed.
- The Crafting panel currently saves the existing `crafting` preference. The scheduled crafting class in `source/gacha_bot/stations.py` remains a placeholder.
- The user explicitly removed the collection drop-off teleporter field and its required-field validation. Do not reintroduce them without a new request. Preserve any existing extra metadata in station files.

## Logging

Use `from logger.logger import logger`. The shared logger feeds `logger/logs.log` and the dashboard Event Log. Prior runs are kept in `logger/archives/`.

Import the shared logger directly in application modules. Legacy logging modules are compatibility re-exports only. Use `logger.template()` for noisy image-matching diagnostics; it is defined centrally and disabled at the default DEBUG level. Standard-library/dependency loggers forward through the shared logger as well.

GUI-started bot processes receive `ASA_BOT_LOG_PIPE=1` and send structured records over stdout. The GUI relays them through the shared logger, preserving severity and source information; only the parent writes/archives the file. Standalone runs write the same log file without console output. Keep Discord's default handler disabled (`log_handler=None`), and use `LOG_PATH` for log forwarding without truncating the shared file. Do not add console handlers or direct `print()` diagnostics; the piped handler exists only for GUI transport.

Station change logs are emitted only after a successful write:

- Edits identify the station, field, and old/new values.
- Additions and removals identify the station.
- Crafting preference changes include the old/new boolean values.
- Failed saves, cancelled removals, unchanged values, and discarded unsaved drafts must not produce successful-change logs.

Keep the saved baseline independent of editable dictionaries. Handle renames and index shifts after removal without misreporting other stations as changed.

## Validation and cleanup

There is currently no maintained automated test suite. Root `test.py` is an infinite-loop screen/image experiment, not a test runner; do not run it as routine validation.

For persistence or editor changes, use temporary data and mock game/Discord actions. Check the relevant paths: typed values, preserved metadata, invalid drafts, debounce/flush, add/remove, cancellation, last-station removal, write failures/retries, and change logging. For visual changes, render or inspect the affected UI at the app's intended size.

Do not start the scheduler or connect the Discord bot just to verify a UI change. Imports can also have side effects: settings may create/recover files and the logger manages log files on import. Isolate these when checking behavior.

Clean up task-created test scripts, screenshots, preview artifacts, and temporary data after verification, as requested by the user. Do not delete pre-existing files such as root `test.py` or user configuration. Report what was checked and distinguish isolated checks from live game validation.
