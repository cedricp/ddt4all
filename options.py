# -*- coding: utf-8 -*-
import locale
import sys
import gettext
import os

simulation_mode = False
port_speed = 38400
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
last_error = ""
main_window = None
ecu_scanner = None


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
            os.environ["LANGUAGE"] = os.environ["LANGUAGE"]

    # Set up message catalog access
    t = gettext.translation(filename, 'locale', fallback=True)
    return t.ugettext
