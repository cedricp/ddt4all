# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
import re
import sys

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_data_files, collect_submodules


SPEC_DIR = Path(SPECPATH).resolve()
PROJECT_ROOT = SPEC_DIR.parents[1]
PACKAGE_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(PACKAGE_DIR))

APP_NAME = "DDT4ALL"
MAIN_SCRIPT = PACKAGE_DIR / "ddt4all" / "main.py"
ICON = PROJECT_ROOT / "resources" / "icons" / "obd.icns"
VEHICLES = PROJECT_ROOT / "vehicles"
LIBUSB = os.environ.get("DDT4ALL_LIBUSB_DYLIB")
TARGET_ARCH = os.environ.get("DDT4ALL_TARGET_ARCH")

for required_path in (MAIN_SCRIPT, ICON):
    if not required_path.exists():
        raise SystemExit("Required macOS build input is missing: {}".format(required_path))

if TARGET_ARCH not in ("x86_64", "arm64"):
    raise SystemExit("DDT4ALL_TARGET_ARCH must be x86_64 or arm64.")
if not LIBUSB or not Path(LIBUSB).is_file():
    raise SystemExit("DDT4ALL_LIBUSB_DYLIB must name the Homebrew libusb-1.0.0.dylib.")

version_text = (PACKAGE_DIR / "ddt4all" / "version.py").read_text(encoding="utf-8")
version_match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', version_text, re.MULTILINE)
if not version_match:
    raise SystemExit("Could not read __version__ from src/ddt4all/version.py.")
APP_VERSION = version_match.group(1)

datas = [
    entry
    for entry in collect_data_files("ddt4all")
    if Path(entry[0]).name.lower() != "ecu.zip"
]
datas.extend(
    [
        (str(PROJECT_ROOT / "license.txt"), "."),
        (str(PROJECT_ROOT / "README.md"), "."),
    ]
)
if VEHICLES.is_dir():
    vehicle_tree = Tree(str(VEHICLES), prefix="vehicles")
    datas.extend(
        entry
        for entry in vehicle_tree
        if Path(entry[0]).name.lower() != "ecu.zip"
    )

if any(Path(source).name.lower() == "ecu.zip" for source, _ in datas):
    raise SystemExit("ecu.zip must remain external to the macOS application.")

binaries = [(str(Path(LIBUSB).resolve()), ".")]

hiddenimports = collect_submodules("ddt4all")
hiddenimports += collect_submodules("serial.tools.list_ports")
hiddenimports += collect_submodules("usb.backend")
hiddenimports += [
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtNetwork",
    "PyQt5.QtPrintSupport",
    "PyQt5.QtSvg",
    "PyQt5.QtWebEngineCore",
    "PyQt5.QtWebEngineWidgets",
    "PyQt5.QtWidgets",
    "crcmod",
    "serial",
    "usb.core",
    "usb.legacy",
    "usb.util",
]

a = Analysis(
    [str(MAIN_SCRIPT)],
    pathex=[str(PACKAGE_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(SPEC_DIR / "runtime_hook.py")],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=TARGET_ARCH,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)

minimum_system_version = "11.0.0"
app = BUNDLE(
    coll,
    name="{}.app".format(APP_NAME),
    icon=str(ICON),
    bundle_identifier="com.github.cedricp.ddt4all",
    version=APP_VERSION,
    target_arch=TARGET_ARCH,
    info_plist={
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": "DDT4ALL Diagnostic Tool",
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "CFBundleExecutable": APP_NAME,
        "CFBundleIdentifier": "com.github.cedricp.ddt4all",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundlePackageType": "APPL",
        "CFBundleSignature": "DDT4",
        "LSMinimumSystemVersion": minimum_system_version,
        "LSApplicationCategoryType": "public.app-category.developer-tools",
        "NSHumanReadableCopyright": "Copyright 2016-2026 Cedric PAILLE",
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": False,
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeExtensions": ["ddt"],
                "CFBundleTypeName": "DDT4ALL Project File",
                "CFBundleTypeRole": "Editor",
                "LSHandlerRank": "Owner",
            }
        ],
    },
)
