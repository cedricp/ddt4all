# DDT4All Build Tools

This directory contains the build and packaging tools used to create distributable versions of DDT4All.

## Overview

DDT4All provides build scripts for creating platform-specific installers:

* **Windows**: Inno Setup-based installer with an embedded Python 2.7 runtime.

## Prerequisites

### Windows

* **Inno Setup 5.6.1(u)** - Download from https://jrsoftware.org/isdl.php
* **Python 2.7** - Embedded runtime located in `C:\DDT4ALL-Dist-Versions\Python27\`
* **Microsoft Visual C++ Redistributable** (included in `win32_deps/`)

## Windows Build Process

### 1. Prepare the Environment

The installer uses an embedded Python 2.7 runtime located at:

```text
C:\DDT4ALL-Dist-Versions\Python27\
```

### 2. Update Version Information

Edit `setup_tools/inno-win-setup/version.h`:

```c
#define __appname__ "DDT4ALL"
#define __version__ "1.0.3"
#define __codename__ "Windows XP"
#define __author__ "Cedric PAILLE"
#define __copyright__ "Copyright ©2016-2026"
#define __email__ "cedricpaille@gmail.com"
#define __status__ "dev"
```

### 3. Build the Installer

```bash
# Navigate to the setup tools directory
cd setup_tools/inno-win-setup

# Compile using the Inno Setup GUI
# Open wininstaller.iss in Inno Setup and click Compile

# Or compile from the command line
"C:\Program Files (x86)\Inno Setup 5\ISCC.exe" wininstaller.iss
```

### 4. Output

* **Installer:** `DDT4ALL-Windows-Installer-v1.0.3_Windows-XP-x86.exe`
* **Location:** Same directory as the `.iss` file
* **Size:** Depends on the embedded Python 2.7 runtime

## Windows Installer Features

* Embedded Python 2.7 runtime
* Compatible with **Windows XP, 7, 8, 10, and 11**
* Optional desktop shortcut creation
* Start Menu integration
* Complete uninstaller with cleanup
* Automatic user permission management for log and data directories

## Directory Structure

```text
setup_tools/
├── README.md                      # This file
└── inno-win-setup/
    ├── version.h                  # Version definitions
    ├── wininstaller.iss           # Inno Setup script
    ├── installer_wizard_image.bmp # Wizard image
    ├── WizardImage0.bmp           # Background image
    ├── win32_deps/
    │   └── VC_redist.x86.exe      # Visual C++ Redistributable
    └── Output/                    # Compiled installer output
```

## Notes

* The installer expects the embedded Python 2.7 runtime to be located at `\DDT4ALL-Dist-Versions\Python27\`.
* Make sure the `DDT4ALL-Dist-Versions` directory exists and contains the Python 2.7 runtime before compiling the installer.
* The installer is a **32-bit (x86)** application and is compatible with **Windows XP and later**.
