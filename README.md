# DDT4ALL

[![Build](https://github.com/cedricp/ddt4all/actions/workflows/python-app.yml/badge.svg)](https://github.com/cedricp/ddt4all/actions/workflows/python-app.yml)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=cedricpaille%40gmail.com&item_name=codetronic&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted)
[![Sponsor](https://img.shields.io/badge/💖%20Sponsor-Support%20me-ea4aaa)](https://github.com/sponsors/Furtif)
[![Discord](https://img.shields.io/discord/1117970325267820675?label=Discord&style=flat-square)](https://discord.gg/cBqDh9bTHP)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL%203.0-green.svg)](https://opensource.org/licenses/GPL-3.0)

DDT4ALL is a cross-platform diagnostic application for CAN bus vehicle networks.
It lets you **create your own ECU parameter screens** and **communicate with ECUs**
through various OBD-II interfaces, including ELM327, Vlinker FS, VGate iCar Pro,
OBDLink SX/EX and ELS27 adapters.

- **Current version:** `v3.1.3` (Celestial Nemean)
- **License:** [GPL-3.0-or-later](https://opensource.org/licenses/GPL-3.0)

---

## Warnings

- This application is **work in progress**. Use **Expert mode** only if you know what you are doing.
- In **non-expert** mode the tool is meant to be harmless for the vehicle (keep the Expert mode button in its released state).
- **Do not use this software if you do not understand how a CAN network (or an ECU) works** — serious damage is possible on a live vehicle.
- Maintenance, testing and research only; the author declines responsibility for any use. **You are responsible.**

---

## Features

- **Diagnostics**: Read / Clear DTC, manual ECU requests, auto-scan ECUs, live parameter monitoring.
- **Screens**: Custom ECU parameter screens designer, screen recorder, data editor.
- **Networks**: CAN bus sniffing (with live non-blocking capture), DoIP, KWP2000.
- **Database**: XML + ZIP (auto `ecu.zip`), JSON internal conversion, graphics extraction.
- **Automation**: Plugin system (vehicle-specific procedures) and extensible Python CLI.
- **Internationalization**: gettext/polib catalogs in 14 languages, real-time switch, HTML-aware strings.

---

## Supported devices

| Device | Available speeds | Default baud | Timeout | Flow control | Category | Notes |
|--------|------------------|--------------|---------|--------------|----------|-------|
| VLinker FS | 57600, 115200 | 38400 | 3 s | None | Enhanced | Most stable, best compatibility |
| VGate iCar Pro | 115200, 230400, 500000, 1000000 | 115200 | 2 s | None | Enhanced | High-speed (up to 1 000 000 bps) |
| ELM327 (original) | standard | 38400 | 5 s | None | General | Usually marked `PIC18F25K80` |
| ELM327 (clone) | standard | 9600–38400 | 5 s | None | Budget | Try different baud settings |
| ELM327 USB | standard | 38400 | 5 s | None | USB | Dedicated ELM327 USB (`STD_USB`) |
| OBDLink SX | 500k / 1M / 2M | 115200 | 2 s | RTS/CTS | Professional | Highest-speed adapter |
| OBDLink EX | 500k / 1M / 2M | 115200 | 2 s | RTS/CTS | Professional | Tested and confirmed |
| ELS27 | standard | 38400 | 4 s | None | Alternative | Good ELM327 equivalent |
| ELS27 V5 | standard | 38400 | 4 s | None | Enhanced | CAN pins 12-13, PyRen / Renolink compatible |
| DERLEK USB-DIAG2/3 | standard | 38400 | 4 s | None | Professional | Auto pin swap, STN/STPX support * |
| USB CAN | varies | 38400 | 5 s | None | Special | Automatic detection / fallback |

> \* DERLEK USB-DIAG2/3 status: not checked on real hardware yet.

### Connection methods

- **USB** — recommended for diagnostics (serial-over-USB on a COM/LPT port).
- **Bluetooth** — convenient, occasional dropouts possible.
- **WiFi** — TCP/IP, `IP:PORT` format (e.g. `192.168.0.10:35000`).

> Most adapters appear as a standard serial port. Dedicated USB-CAN / USB-ELM327
> devices are handled natively with an automatic fallback.

---

## Language support

gettext catalogs are authored under `locales/` and compiled into
`src/ddt4all/generated/locales/`. English is the source language (used as `msgid`);
the following catalogues are shipped:

| Code | Language |
|------|----------|
| `fr` | Français |
| `pt` | Português |
| `de` | Deutsch |
| `es` | Español |
| `it` | Italiano |
| `ru` | Русский |
| `pl` | Polski |
| `nl` | Nederlands |
| `hu` | Magyar |
| `ro` | Română |
| `sr` | Српски |
| `tr` | Türkçe |
| `cs_CZ` | Czech |
| `uk_UA` | Українська |

All catalogs are complete (content of all `msgstr` fields is present
and no `#, fuzzy` remains), keep valid gettext syntax and preserve the original
`%s` / named placeholders.

---

## Requirements

- **Python** `>=3.8` (3.10 or newer recommended)
- **PyQt5** `>=5.15, <5.16` — GUI framework
- **PyQtWebEngine** `>=5.15, <5.16` — optional, full HTML documentation view
- **pyserial** `==3.5` — serial port communication
- **pyusb** `==1.2.1` — USB access
- **crcmod** `==1.7` — checksums
- **polib**, **platformdirs**
- **pywin32** `>=227` — Windows (serial)

## Installation

### Modern (recommended)

```bash
git clone https://github.com/cedricp/ddt4all.git
cd ddt4all
python -m venv ./venv

# activate virtual environment
#   Windows:
.\venv\Scripts\activate.bat
#   Linux / macOS:
source ./venv/bin/activate

# install the package (editable for development)
pip install -e .

# launch application
ddt4all
# or
python -m ddt4all
```

### With optional features

```bash
pip install -e ".[dev]"                    # pytest, linting
pip install -e ".[can]"                    # python-can, obd
pip install -e ".[network]"                # requests, websockets
pip install -e ".[bluetooth]"              # pybluez / bleak
# all together:
pip install -e ".[dev,can,network,bluetooth]"
```

### Legacy (manual dependencies)

```bash
pip install "PyQt5>=5.15,<5.16" "PyQtWebEngine>=5.15,<5.16" pyserial==3.5 pyusb==1.2.1 crcmod==1.7 polib platformdirs
```

---

## Platform notes

- **Linux** — add the current user to the `dialout` group to access serial ports:
  ```bash
  sudo usermod -a -G dialout $USER
  # logout and login again
  ```
- **Windows** — ensure the serial/USB drivers are installed and that a COM port is
  assigned to the adapter. Run with administrator rights if port access fails.
- **macOS** — if an editable-install error is raised by `pip install -e .`, update the
  packaging tools first:
  ```bash
  python3 -m pip install --upgrade pip setuptools wheel
  python3 -m pip install -e .
  ```
  If the package data is missing at runtime (`resources/projects.json not found`),
  reinstall from the repository root:
  ```bash
  python3 -m pip install --force-reinstall -e .
  ```

## Quick start

```bash
# after a successful install
ddt4all
#   or, from source (development mode):
python -m ddt4all
```

Use the built-in **connection test** to let DDT4ALL auto-detect the adapter and the
correct baud rate. On discovery, the optimal device configuration is applied.

### Shortcut / alias (optional)

```bash
# Linux / macOS
alias ddt4all-dev='cd /path/to/ddt4all && source ./venv/bin/activate && python -m ddt4all'
# Windows (PowerShell)
Set-Alias -Name ddt4all -Value "ddt4all"
```

## Plugin system

Vehicle-specific procedures are provided as Python modules under
`src/ddt4all/plugins/`:

- `ab90_reset.py` — AB90 air-bag reset
- `card_programming.py` — ECU card programming
- `clio3_eps_reset.py`, `clio4_eps_reset.py` — Clio 3/4 EPS reset
- `laguna2_uch_reset.py`, `laguna3_uch_reset.py` — Laguna 2/3 UCH
- `megane2_uch_reset.py`, `megane3_uch_reset.py` — Megane 2/3 UCH
- `megane3_ab_reset.py` — Megane 3 air-bag reset
- `megane3_eps_reset.py` — Megane 3 EPS
- `rsat4_reset.py` — RSAT4 system reset
- `vin_crc.py` — VIN CRC calculation
- `zoe_waterpump_counter_reset.py` — ZOE water-pump counting reset

The plugin architecture allows custom procedures for other ECUs and brands.

---

## Architecture

### Core modules

- `src/ddt4all/main.py` — entry point (PyQt GUI + connection handling)
- `src/ddt4all/version.py` — version / codename / contributors
- `src/ddt4all/options.py` — configuration & device settings persistence
- `src/ddt4all/file_manager.py` — file and directory utilities
- `src/ddt4all/cli/` — command-line interface handlers (DoIP, parameters, USB device)

### Communication

- `core/elm/` — ELM327 / adapter communication (`elm.py`, `device_manager.py`,
  `port.py`, `constants.py`)
- `core/ecu/` — ECU database, files and scanning (`ecu_database.py`,
  `ecu_scanner.py`, `ecu_device.py`, `ecu_file.py`, `ecu_request.py`,
  `ecu_ident.py`, `data_item.py`, `utils.py`)
- `core/doip/` — DoIP (Diagnostics over IP) protocol support
- `core/parameters/helpers.py` — parameter parsing / helpers
- `core/usbdevice/` — USB CAN devices (`obd_device.py`, `usb_can.py`, `constants.py`)

### Modern UI

- `ui/` — main window, widgets, dialogs
- `ui/displaymod/` — display widgets / graphical elements
- `ui/data_editor/` — ECU qualitative data editing
- `ui/sniffer/` — CAN sniffing with a QThread-based thread

### Data & resources

- `generated/` — compiled resources and `.mo` translation catalogs
- `resources.qrc` — Qt resource descriptor
- `vehicles/` — vehicle-specific files
- `json/` — JSON database folder
- `logs/` — runtime logs (see also the platform user-log directory)

### Threading

- QThread for the network sniffer (non-blocking capture)
- `threading.Lock()` in the ELM layer for safe serial operations
- `QTimer` for periodic refresh and connection monitoring

---

## Testing

```bash
pip install -e ".[dev]"
pytest
```

Test suites are in `tests/` (`unit`, `integration`, `smoke`). A GitHub Actions
workflow (`python-app.yml`) runs the test suite on multiple OSes.

## Distribution / build

- **Windows**: InnoSetup installer under `setup_tools/inno-win-setup/`
  (`wininstaller.iss`, `version.h`, `win32_deps/`).
- **macOS**: DMG build via `setup_tools/mac-os/builddmg.sh` (with `main.spec`,
  `entitlements.plist`).
- **Linux**: AppImage build scripts / workflow (see `setup_tools/`).

Prebuilt installers are published on the [Releases page](https://github.com/cedricp/ddt4all/releases).

---

## Troubleshooting

### Connection

- **No serial port listed** — check driver installation. On Linux, verify the user
  is in the `dialout` group. On Windows, try running as administrator.
- **Adapter not detected** — test every available COM/USB port with the connection
  test; try another baud rate (38400, 9600, 115200).
- **ELS27 V5 special case** — check the driver (PyRen / Reolink), then select the
  proper serial port manually (device may appear as `FTDI`, `CH340` or `CP210x`).
- **WiFi** — format `IP:PORT`, same local network, firewall open.

### Installation

- **PyQtWebEngine missing** — DDT4All still works; only the full web-based
  documentation view is limited (graceful fallback).
- **Windows serial fails** — reinstall `pywin32` and run
  `python -m pywin32_postinstall -install`, ideally with admin rights.

## Documentation & videos

See the project [Wiki](https://github.com/cedricp/ddt4all/wiki) (Android port,
device notes) and the YouTube channel (CAN sniffing, AirBag DTC, Megane examples).

## Community

- **Discord**: [Join the community](https://discord.gg/cBqDh9bTHP)
- **Issues**: [GitHub Issues](https://github.com/cedricp/ddt4all/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cedricp/ddt4all/discussions)

## Contributing

- **Report bugs** — add a screenshot, your `Logs/` file, `[Bug]` in the title, OS + Python + adapter info.
- **Suggestions / ideas** — open a discussion with `[Suggestion]` in the title.
- **Translations** — improve or add language catalogs under `locales/`.
- **Donations** — financial (PayPal / GitHub Sponsors) and hardware donations
  (OBD-II interfaces, ECU devices) are welcome to extend device support.

## License & disclaimer

This project is **free software** under the **GPL-3.0-or-later** license. DDT4ALL is
an independent, unofficial, educational tool and is *not* affiliated with any
vehicle/software brand. It is provided for study, testing and research only; it is
not a replacement for factory/bench diagnostic tools. Use on a real vehicle is at
your own risk — see the warnings at the top of this file.

**Happy CAN studying!** 🚗🔧
