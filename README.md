# Pulsemeeter (Enhanced Fork)

A frontend to ease the use of PulseAudio / PipeWire's routing capabilities, much like Voicemeeter's workflow — enhanced with custom theming, exclusive routing toggles, keyboard shortcuts, category visibility controls, and a responsive layout.

> **Built with AI:** This fork was developed using **Gemini 4 Argon** and **Antigravity**.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Upstream](https://img.shields.io/badge/upstream-theRealCarneiro%2Fpulsemeeter-purple)](https://github.com/theRealCarneiro/pulsemeeter)

---

## New Features in This Fork

### 1. Hide / Show Input & Output Categories
- Toggle visibility of individual device and stream categories directly from the **Settings Menu** (`Visible Categories`):
  - **Hardware Inputs** (`hi`)
  - **Virtual Inputs** (`vi`)
  - **Hardware Outputs** (`a`)
  - **Virtual Outputs** (`b`)
  - **Application Outputs** (`sink_input`)
  - **Application Inputs** (`source_output`)

### 2. Exclusive Output Toggle Groups
- Right-click any output routing button (`A1`, `A2`, `B1`, etc.) on an input device and enable **Exclusive toggle group**.
- Activating one output in the group automatically disables all other outputs in that input's exclusive toggle group (ideal for switching between Speakers and Headphones with a single click).
- **CLI Support**: Cycle through an input's exclusive toggle group from scripts or system hotkeys:
  ```bash
  pulsemeeter toggle-group vi 1
  ```

### 3. Exclusive Hardware Input to Virtual Output Routing
- For **Hardware Inputs (`hi`)** routing to **Virtual Outputs (`b`)**, right-click the virtual output button (`B1`, etc.) and enable **Exclusive hardware input to this virtual output**.
- Routing `Hardware Input 1` to `Virtual Output 1` automatically disables routing from `Hardware Input 2` (and any other hardware inputs) to `Virtual Output 1`, and vice versa.

### 4. Per-Input Output Visibility (Hide Individual Output Buttons)
- Right-click any output routing button on a Hardware or Virtual Input and check **Hide output button** to declutter outputs you don't route that input to.
- Easily re-enable hidden output buttons at any time via the input device's **Settings Menu** (`Visible Outputs`).

### 5. Keyboard Shortcuts for Output Toggling & Group Cycling
- Bind custom keyboard shortcuts to:
  - **Individual output routes**: Right-click an output button (`A1`, `B1`, etc.) -> click **Shortcut** -> press your key combination.
  - **Cycle exclusive toggle group**: Open an input device's **Settings Menu** -> click **Cycle Toggle Group Shortcut** -> press your key combination.
- Supports both **XDG Desktop Portal `GlobalShortcuts`** (Wayland/X11 desktop-wide shortcuts) and window-level GTK4 shortcut capture.

### 6. Custom Theming Engine with Color Pickers & Translucent Backgrounds
- Customize the look and feel of Pulsemeeter live from the **Settings Menu** (`Theme` section):
  - **Background Mode**: Choose between **Solid**, **Linear Gradient** (with configurable gradient angle from `0°` to `360°`), or **Translucent** (allowing your desktop wallpaper to show through).
  - **Background Opacity Slider**: Fine-tune background transparency (`0.05` – `1.00`).
  - **Full RGBA Color Pickers**: Customize Primary Background, Gradient End, Card Background (with alpha), Accent Color, and Text Color with instant live preview.

### 7. Scroll Wheel Volume Control Toggle
- Enable or disable adjusting volume sliders with the mouse scroll wheel via **Enable scroll wheel on volume sliders** in the **Settings Menu** to prevent accidental volume changes while scrolling.

### 8. Responsive Scaling & Multi-Line Text Wrapping
- **Dynamic Card Scaling**: Category containers, device cards, application cards, and routing buttons scale cleanly based on the window size across `Blocks`, `Bars`, and `Tabbed` layouts.
- **Multi-Line Label Wrapping**: Long input/output source names, device descriptions, routing button labels, and application stream dropdowns wrap cleanly onto the next line instead of clipping or locking the window width.

---

## Core Pulsemeeter Features
- Create virtual inputs and outputs
- Route audio from input devices to output devices, either hardware or virtual
- Per-device and per-route (`pw-loopback`) volume and mute control
- Channel layout for virtual devices (mono, stereo, surround, etc.)
- Port selection for hardware devices and custom port-to-port connection mapping
- Real-time VU level meters

---

## Installation & Running from Source

### Dependencies
- Python 3.10+
- PyGObject (`Gtk 4.0`, `Pango 1.0`)
- `pydantic`
- `pulsectl` & `pulsectl-asyncio`
- PipeWire (`pw-link`, `pw-loopback`, `pactl`) / PulseAudio

### Run Directly from Source
```bash
git clone git@github.com:hqcd/pulsemeeter.git
cd pulsemeeter
PYTHONPATH=src python3 -m pulsemeeter
```

### Install with `pip`
```bash
pip install .
```

### Run Unit Tests
```bash
PYTHONPATH=src python3 -m unittest discover -s tests/unit -p "*_test.py"
```

---

## Upstream Wiki & Credits
- Original project by [theRealCarneiro](https://github.com/theRealCarneiro/pulsemeeter) — see the upstream [Installation Wiki](https://github.com/theRealCarneiro/pulsemeeter/wiki/Installation) and [Usage Guide](https://github.com/theRealCarneiro/pulsemeeter/wiki/How-to-use).
- Fork enhancements developed using **Gemini 4 Argon** and **Antigravity**.
