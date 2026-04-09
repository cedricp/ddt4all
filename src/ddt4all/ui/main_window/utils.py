import errno
import os
from pathlib import Path
import sys
import tempfile

import PyQt5.QtCore as core

import ddt4all.options as options

_ = options.translator('ddt4all')

BASE_DIR = Path(__file__).resolve().parent
styles_base_dir = BASE_DIR / ".." / ".." / "resources" / "styles"

def isWritable(path):
    try:
        testfile = tempfile.TemporaryFile(dir=path)
        testfile.close()
        return True
    except OSError as e:
        if e.errno == errno.EACCES:  # 13
            return False
        e.filename = path
        return False
    except Exception:
        return False

def set_theme_style(app, onoff):

    if (onoff):
        stylefile = core.QFile(":/styles/qstyle-d.qss")
        options.dark_mode = True
        stylefile.open(core.QFile.ReadOnly)
        StyleSheet = bytes(stylefile.readAll()).decode()
    else:
        stylefile = core.QFile(":/styles/qstyle.qss")
        stylefile.open(core.QFile.ReadOnly)
        options.dark_mode = False
        StyleSheet = bytes(stylefile.readAll()).decode()

    # Apply platform-specific font size and font family adjustments
    if sys.platform == "darwin":
        # macOS: keep 14pt for better readability with .AppleSystemUIFont
        # Remove Windows-specific "Segoe UI" font to avoid 276ms lookup delay
        StyleSheet = StyleSheet.replace(
            '".AppleSystemUIFont", "Segoe UI", "Helvetica Neue",',
            '".AppleSystemUIFont", "Helvetica Neue",'
        )
    else:
        # Windows/Linux: revert to 10pt for proper sizing
        StyleSheet = StyleSheet.replace("font-size: 14pt;", "font-size: 10pt;")

    app.setStyleSheet(StyleSheet)
    options.configuration["dark"] = options.dark_mode
    options.save_config()


def set_socket_timeout(onoff):
    if (onoff):
        options.socket_timeout = True
    else:
        options.socket_timeout = False

    options.configuration["socket_timeout"] = options.socket_timeout
    options.save_config()



