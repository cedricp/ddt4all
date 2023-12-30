#!/usr/bin/python3
# -*- coding: utf-8 -*-
import gettext
import locale
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


def translator(domain):
    # default translation if err set to en_US
    check = 'en_US'
    try:
        lang, enc = locale.getlocale()
        check = lang
    except:
        pass

    if check == 'en_US':
        try:
            lang, enc = locale.getdefaultlocale()
            check = lang
        except:
            pass

    # Set up message catalog access
    os.environ['LANG'] = check
    t = gettext.translation(domain, 'dtt4all_data/locale', fallback=True)  # not ok in python 3.11.x, codeset="utf-8")
    return t.gettext
