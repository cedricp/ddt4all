#!/usr/bin/python3
# -*- coding: utf-8 -*-
import gettext
import json
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
dark_mode = False
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
configuration = {
    "lang": None,
    "dark": False
}
lang_list = {
    "English": "en_US",
    "German": "de",
    "Spanish": "es",
    "French": "fr",
    "Hungarian": "hu",
    "Italian": "it",
    "Dutch": "nl",
    "Polish": "pl",
    "Portuguese": "pt",
    "Romanian": "ro",
    "Russian": "ru",
    "Serbian": "sr",
    "Turkish": "tr",
    "Ukrainian": "uk_UA"
}


def save_config():
    # print(f'Save ddt4all_data/config.json lang: {configuration["lang"]} -> Ok.')
    js = json.dumps(configuration, ensure_ascii=False, indent=True)
    f = open("ddt4all_data/config.json", "w", encoding="UTF-8")
    f.write(js)
    f.close()


def create_new_config():
    configuration["lang"] = get_translator_lang()
    configuration["dark"] = False
    save_config()


def load_configuration():
    try:
        f = open("ddt4all_data/config.json", "r", encoding="UTF-8")
        config = json.loads(f.read())
        # load config as multiplatform (mac fix macOs load conf)
        configuration["lang"] = config["lang"]
        configuration["dark"] = config["dark"]
        os.environ['LANG'] = config["lang"]
        f.close()
    except:
        create_new_config()


def get_last_error():
    global last_error
    err = last_error
    last_error = ""
    return err


def get_translator_lang():
    # default translation if err set to en_US
    loc_lang = "en_US"
    try:
        lang, enc = locale.getdefaultlocale()
        loc_lang = lang
    except:
        try:
            lang, enc = locale.getlocale()
            loc_lang = lang
        except:
            pass
    return loc_lang


def translator(domain):
    load_configuration()
    # Set up message catalog access
    t = gettext.translation(domain, 'ddt4all_data/locale', fallback=True)  # not ok in python 3.11.x, codeset="utf-8")
    return t.gettext
