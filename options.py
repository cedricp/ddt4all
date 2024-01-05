#!/usr/bin/python3
# -*- coding: utf-8 -*-
import gettext
import locale
import os

import json

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
configuration = {
    "lang": None
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
    # print(f'Save dtt4all_data/config.json lang: {configuration["lang"]} -> Ok.')
    js = json.dumps(configuration, ensure_ascii=False, indent=True)
    f = open("dtt4all_data/config.json", "w", encoding="UTF-8")
    f.write(js)
    f.close()


def create_new_config():
    # print("configuration not found or not ok. Create one new")
    # print("Possible translations:")
    # codes = ''
    # for i in lang_list:
    #     print(i + " code: " + lang_list[i])
    #     codes += lang_list[i] + " "
    configuration["lang"] = get_translator_lang()
    # print("\nEdit it only if it not ok for you country language.")
    # print(f'Edit the `dtt4all_data/config.json`\nConfiguration however you want this to be translated.\nThe self-assigned code is: {lang}')
    # print(f'Close and edit the configuration for list: \n\t{codes.strip()} \nAnd reopen the application.')
    save_config()


def load_configuration():
    try:
        f = open("dtt4all_data/config.json", "r", encoding="UTF-8")
        configuration = json.loads(f.read())
        os.environ['LANG'] = configuration["lang"]
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
    t = gettext.translation(domain, 'dtt4all_data/locale', fallback=True)  # not ok in python 3.11.x, codeset="utf-8")
    return t.gettext
