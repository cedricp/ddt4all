# -*- coding: utf-8 -*-
import locale
import sys
import gettext
import os

simulation_mode = False
port_speed = 38400
port_name = ""
port = ""
promode = False
elm = None
log = "ddt"
opt_cfc0 = False
opt_n1c = True
log_all = False
auto_refresh = False
elm_failed = False
# KWP2000 Slow init
opt_si = False
report_data = True
ecus_dir = "ecus/"
graphics_dir = "graphics/"
last_error = ""
main_window = None
ecu_scanner = None
debug = 'DDTDEBUG' in os.environ
cantimeout = 0
refreshrate = 5
mode_edit = False
safe_commands = ["3E", "14", "21", "22", "17", "19", "10"]


def get_last_error():
    global last_error
    err = last_error
    last_error = ""
    return err


def translator(filename):
    if sys.platform.startswith('win'):
        if os.getenv('LANG') is None:
            lang, enc = locale.getdefaultlocale()
            os.environ['LANG'] = lang
    else:
        if "LANGUAGE" not in os.environ is None:
            os.environ["LANGUAGE"] = os.environ["LANG"]

    # Set up message catalog access
    t = gettext.translation(filename, 'locale', fallback=True, codeset="utf-8")
    try:
        return t.ugettext
    except:
        return t.gettext
