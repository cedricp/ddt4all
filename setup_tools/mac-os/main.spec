# -*- mode: python ; coding: utf-8 -*-

# DDT4ALL PyInstaller specification for macOS
# Supports both Intel and Apple Silicon (M1/M2) architectures

import os
import sys

# Add the project root to the path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

a = Analysis(
    ['../../main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        ('../../ddt4all_data/icons', 'ddt4all_data/icons'),
        ('../../ddt4all_data/locale', 'ddt4all_data/locale'),
        ('../../ddt4all_data/tools', 'ddt4all_data/tools'),
        ('../../ddt4all_data/projects.json', 'ddt4all_data'),
        ('../../ddt4all_data/config.json', 'ddt4all_data'),
        ('../../ddtplugins', 'ddtplugins'),
        ('../../requirements.txt', '.'),
        ('../../license.txt', '.'),
        ('../../README.md', '.'),
    ],
    hiddenimports=[
        # PyQt5 modules that may not be auto-detected
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'PyQt5.QtNetwork',
        'PyQt5.QtPrintSupport',
        'PyQt5.QtSvg',
        'PyQt5.QtWebEngineWidgets',  # Optional but recommended
        
        # Serial communication
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        
        # USB support
        'usb',
        'usb.core',
        'usb.util',
        
        # Cryptographic functions
        'crcmod',
        'crcmod.crcmod',
        
        # Platform-specific modules
        'platform',
        'subprocess',
        'threading',
        'queue',
        'json',
        'xml.etree.ElementTree',
        'xml.dom.minidom',
        
        # DDT4ALL specific modules
        'ecu',
        'elm',
        'options',
        'parameters',
        'dataeditor',
        'displaymod',
        'sniffer',
        'uiutils',
        'usbdevice',
        'version',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce bundle size
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
    ],
    noarchive=False,
    optimize=0,
)

# Filter out QSS files and add them properly
qss_files = []
qss_dir = os.path.join(project_root, 'ddt4all_data')
if os.path.exists(qss_dir):
    for file in os.listdir(qss_dir):
        if file.endswith('.qss'):
            qss_files.append((os.path.join(qss_dir, file), 'ddt4all_data'))

# Add QSS files to datas
a.datas.extend(qss_files)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DDT4ALL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='universal2',  # Support both Intel and Apple Silicon
    codesign_identity=None,  # Set to your Developer ID for distribution
    entitlements_file=None,  # Add entitlements.plist for enhanced permissions
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DDT4ALL',
)

app = BUNDLE(
    coll,
    name='DDT4ALL.app',
    icon='../icons/obd.icns',
    bundle_identifier='com.github.cedricp.ddt4all',
    version='3.0.4',  # Should match version.py
    info_plist={
        'CFBundleName': 'DDT4ALL',
        'CFBundleDisplayName': 'DDT4ALL Diagnostic Tool',
        'CFBundleShortVersionString': '3.0.4',
        'CFBundleVersion': '3.0.4',
        'CFBundleExecutable': 'DDT4ALL',
        'CFBundleIdentifier': 'com.github.cedricp.ddt4all',
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'DDT4',
        'LSMinimumSystemVersion': '10.13.0',  # macOS High Sierra minimum
        'LSApplicationCategoryType': 'public.app-category.developer-tools',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
        'NSHumanReadableCopyright': 'Copyright ©2016-2025 Cedric PAILLE',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeExtensions': ['ddt'],
                'CFBundleTypeName': 'DDT4ALL Project File',
                'CFBundleTypeRole': 'Editor',
                'LSHandlerRank': 'Owner',
            }
        ],
        # USB and Serial port access permissions
        'NSBluetoothAlwaysUsageDescription': 'DDT4ALL needs Bluetooth access to communicate with OBD adapters.',
        'NSBluetoothPeripheralUsageDescription': 'DDT4ALL needs Bluetooth access to communicate with OBD adapters.',
        'NSLocationWhenInUseUsageDescription': 'DDT4ALL may use location services for enhanced diagnostic features.',
    },
)