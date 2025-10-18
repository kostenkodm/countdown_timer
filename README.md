# Transparent Timer

A lightweight, customizable, always-on-top countdown timer with transparent window support. Built with Python and Tkinter.

## Features

- Always-on-top timer window
- Draggable timer display
- Countdown with minutes and seconds
- Countdown can go negative (up to -5 minutes)
- Customizable font size
- Customizable window transparency
- Background color choice: White or Black
- Play custom WAV file when timer reaches zero
- Saves user settings and timer window position
- Works as standalone `.exe` using PyInstaller

## Installation

1. Clone or download the repository.
2. Install Python 3.10+.
3. Install dependencies (if not included in standard library):

```bash
pip install pyinstaller
```

Running
From source:

```bash
python timer.py
```
As executable:

The project can be compiled to a standalone .exe using PyInstaller:
```bash
pyinstaller --onefile --windowed --icon=icon.ico --add-data "alarm.wav;." timer.py
```
After building, the executable will be located in the dist/ folder.

## Usage

1. Open the timer.
2. Set minutes and seconds.
3. Adjust font size, transparency, and background color.
4. Select a custom WAV file if desired (default: alarm.wav).
5. Use Start, Pause, or Stop buttons.
6. Drag the timer window to any position on the screen. Position is saved automatically.

## Settings
Settings and timer position are saved in %APPDATA%\TransparentTimer (Windows) as settings.json and position.json.
Font size, background color, transparency, and chosen signal are remembered between sessions.