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

def set_language_realtime(language_name):
    """Change language in real-time without restart"""
    global _
    
    if language_name in options.lang_list:
        lang_code = options.lang_list[language_name]
        
        # Update environment and configuration
        os.environ['LANG'] = lang_code
        options.configuration["lang"] = lang_code
        options.save_config()
        
        # Reload translator
        import gettext
        try:
            t = gettext.translation('ddt4all', 'ddt4all_data/locale', languages=[lang_code], fallback=True)
            _ = t.gettext
            
            # Update main window if it exists
            if hasattr(options, 'main_window') and options.main_window:
                main_window = options.main_window
                # Update menu bar
                main_window.updateMenuBar()
                # Update status bar using the widget directly
                if hasattr(main_window, 'statusbar_widget') and main_window.statusbar_widget:
                    main_window.statusbar_widget.showMessage(_("Language changed to") + " " + language_name, 3000)
            
            print(f"Language changed to {language_name} ({lang_code})")
            return True
        except Exception as e:
            print(f"Error changing language: {e}")
            return False
    return False

def set_socket_timeout(onoff):
    if (onoff):
        options.socket_timeout = True
    else:
        options.socket_timeout = False

    options.configuration["socket_timeout"] = options.socket_timeout
    options.save_config()



