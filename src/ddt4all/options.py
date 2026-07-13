#!/usr/bin/python3
# -*- coding: utf-8 -*-
import gettext
import json
import locale
import os
import time
import sys
from pathlib import Path

from ddt4all.file_manager import get_config_dir

_current_translation = gettext.NullTranslations()

def _dynamic_gettext(message):
    return _current_translation.gettext(message)


simulation_mode = False
port_speed = 38400
port_name = ""
port = ""
promode = False
elm = None
log = "ddt"
opt_caf = False
opt_can2 = False
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
safe_commands = ['10','12','14','17','19','1A','21','22','23','3E']

# TODO: Review DoIP configuration defaults and runtime flags.
# DoIP Configuration
doip_target_ip = "192.168.0.12"
doip_target_port = 13400
doip_timeout = 5
doip_vehicle_announcement = True
doip_auto_reconnect = False
doip_preset = "Custom"
doip_scan = True  # Enable DoIP scanning

# STN/STPX Configuration
opt_stpx_full = False  # Full STPX support detected
opt_stn_basic = False  # Basic STN protocol support detected
elm_uart_buffer_size = 0x1ff  # UART buffer size for STN-based adapters

lang_list = {
    "Default":"en_US",
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
    "Czech":"cs_CZ",
    "Turkish": "tr",
    "Ukrainian": "uk_UA"
}

configuration = {
    "lang": lang_list["Default"],
    "dark": False,
    "socket_timeout": False,
    "device_settings": {},
    "auto_detect_devices": True,
    "connection_timeout": 10,
    "read_timeout": 5,
    "max_reconnect_attempts": 3,
    "preferred_device_order": ["vlinker", "vgate", "derlek_usb_diag2", "derlek_usb_diag3", "obdlink", "obdlink_ex", "elm327", "els27"],
    "enable_device_validation": True,
    "carlist_sort_mode": "code",
    "doip_target_ip": "192.168.0.12",
    "doip_target_port": 13400,
    "doip_timeout": 5,
    "doip_vehicle_announcement": True,
    "doip_auto_reconnect": False,
    "doip_preset": "Custom",
    "doip_scan": False,
    "last_selected_vehicle": None,
    "last_opened_ecu": None
}


BASE_DIR = Path(__file__).resolve().parent

def save_config():
    # print(f'Save ddt4all_data/config.json lang: {configuration["lang"]} -> Ok.')
    config_path = get_config_dir() / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    js = json.dumps(configuration, ensure_ascii=False, indent=True)
    f = open(str(config_path), "w", encoding="UTF-8")
    f.write(js)
    f.close()


def create_new_config():
    configuration["lang"] = get_translator_lang()
    configuration["dark"] = False
    configuration["socket_timeout"] = False
    configuration["device_settings"] = {}
    configuration["auto_detect_devices"] = True
    configuration["connection_timeout"] = 10
    configuration["read_timeout"] = 5
    configuration["max_reconnect_attempts"] = 3
    configuration["preferred_device_order"] = ["vlinker", "vgate", "derlek_usb_diag2", "derlek_usb_diag3", "obdlink", "obdlink_ex", "els27", "elm327"]
    configuration["enable_device_validation"] = True
    configuration["carlist_sort_mode"] = "code"
    configuration["doip_scan"] = False
    configuration["last_selected_vehicle"] = None
    configuration["last_opened_ecu"] = None
    save_config()


def load_configuration():
    try:
        f = open(get_config_dir() / "config.json", "r", encoding="UTF-8")
        config = json.loads(f.read())
        # load config as multiplatform (mac fix macOs load conf)
        configuration["lang"] = config.get("lang", get_translator_lang())
        configuration["dark"] = config.get("dark", False)
        configuration["socket_timeout"] = config.get("socket_timeout", False)
        
        # Load enhanced device settings with defaults
        configuration["device_settings"] = config.get("device_settings", {})
        configuration["auto_detect_devices"] = config.get("auto_detect_devices", True)
        configuration["connection_timeout"] = config.get("connection_timeout", 10)
        configuration["read_timeout"] = config.get("read_timeout", 5)
        configuration["max_reconnect_attempts"] = config.get("max_reconnect_attempts", 3)
        configuration["preferred_device_order"] = config.get("preferred_device_order", 
                                                           ["vlinker", "vgate", "derlek_usb_diag2", "derlek_usb_diag3", "obdlink", "obdlink_ex", "els27", "elm327"])
        configuration["enable_device_validation"] = config.get("enable_device_validation", True)
        configuration["carlist_sort_mode"] = config.get("carlist_sort_mode", "code")
        
        # Load DoIP configuration
        global doip_target_ip, doip_target_port, doip_timeout, doip_vehicle_announcement, doip_auto_reconnect, doip_preset, doip_scan
        doip_target_ip = config.get("doip_target_ip", "192.168.0.12")
        doip_target_port = config.get("doip_target_port", 13400)
        doip_timeout = config.get("doip_timeout", 5)
        doip_vehicle_announcement = config.get("doip_vehicle_announcement", True)
        doip_auto_reconnect = config.get("doip_auto_reconnect", False)
        doip_preset = config.get("doip_preset", "Custom")
        doip_scan = config.get("doip_scan", False)
        
        configuration["doip_target_ip"] = doip_target_ip
        configuration["doip_target_port"] = doip_target_port
        configuration["doip_timeout"] = doip_timeout
        configuration["doip_vehicle_announcement"] = doip_vehicle_announcement
        configuration["doip_auto_reconnect"] = doip_auto_reconnect
        configuration["doip_preset"] = doip_preset
        configuration["doip_scan"] = doip_scan
        
        # Load last selected vehicle and ECU
        configuration["last_selected_vehicle"] = config.get("last_selected_vehicle", None)
        configuration["last_opened_ecu"] = config.get("last_opened_ecu", None)
        
        os.environ['LANG'] = str(configuration["lang"])
        f.close()
    except Exception:
        print("Configuration file not found. Creating new configuration...")
        create_new_config()


def get_last_error():
    global last_error
    err = last_error
    last_error = ""
    return err


def get_translator_lang():
    """Return the system locale language or the configured default."""
    try:
        locale.setlocale(locale.LC_CTYPE, "")
        return locale.getlocale()[0] or lang_list["Default"]
    except (locale.Error, ValueError):
        return lang_list["Default"]

def get_device_settings(device_type, port=None):
    """Get device-specific settings with fallback to defaults"""
    device_key = f"{device_type}_{port}" if port else device_type
    
    # Default settings by device type
    defaults = {
        'vlinker': {'baudrate': 38400, 'timeout': 3, 'rtscts': False, 'dsrdtr': False},
        'elm327': {'baudrate': 38400, 'timeout': 5, 'rtscts': False, 'dsrdtr': False},
        'obdlink': {'baudrate': 115200, 'timeout': 2, 'rtscts': True, 'dsrdtr': False},
        'obdlink_ex': {'baudrate': 115200, 'timeout': 2, 'rtscts': True, 'dsrdtr': False},
        'els27': {'baudrate': 38400, 'timeout': 4, 'rtscts': False, 'dsrdtr': False},  # ELS27 V5 with CAN on pins 12-13
        'vgate': {'baudrate': 115200, 'timeout': 2, 'rtscts': False, 'dsrdtr': False},

        'unknown': {'baudrate': 38400, 'timeout': 5, 'rtscts': False, 'dsrdtr': False}
    }
    
    # Get saved settings or use defaults
    saved_settings = configuration.get("device_settings", {}).get(device_key, {})
    default_settings = defaults.get(device_type, defaults['unknown'])
    
    # Merge saved settings with defaults
    settings = default_settings.copy()
    settings.update(saved_settings)
    
    return settings


def save_device_settings(device_type, settings, port=None):
    """Save device-specific settings"""
    device_key = f"{device_type}_{port}" if port else device_type
    
    if "device_settings" not in configuration:
        configuration["device_settings"] = {}
    
    configuration["device_settings"][device_key] = settings
    save_config()


def get_connection_timeout():
    """Get connection timeout from configuration"""
    return configuration.get("connection_timeout", 10)


def get_read_timeout():
    """Get read timeout from configuration"""
    return configuration.get("read_timeout", 5)


def get_max_reconnect_attempts():
    """Get maximum reconnection attempts"""
    return configuration.get("max_reconnect_attempts", 3)


def is_device_validation_enabled():
    """Check if device validation is enabled"""
    return configuration.get("enable_device_validation", True)


def get_preferred_device_order():
    """Get preferred device detection order"""
    return configuration.get("preferred_device_order", ["vlinker", "vgate", "derlek_usb_diag2", "derlek_usb_diag3", "obdlink", "obdlink_ex", "els27", "elm327"])


def get_carlist_sort_mode():
    """Get carlist sort mode from configuration"""
    return configuration.get("carlist_sort_mode", "code")


def set_carlist_sort_mode(mode):
    """Set carlist sort mode and save configuration"""
    configuration["carlist_sort_mode"] = mode
    save_config()


def get_last_selected_vehicle():
    """Get last selected vehicle from configuration"""
    return configuration.get("last_selected_vehicle", None)


def set_last_selected_vehicle(vehicle):
    """Set last selected vehicle and save configuration"""
    configuration["last_selected_vehicle"] = vehicle
    save_config()


def get_last_opened_ecu():
    """Get last opened ECU from configuration"""
    return configuration.get("last_opened_ecu", None)


def set_last_opened_ecu(ecu):
    """Set last opened ECU and save configuration"""
    configuration["last_opened_ecu"] = ecu
    save_config()


def clear_history():
    """Clear last selected vehicle and last opened ECU from configuration"""
    configuration["last_selected_vehicle"] = None
    configuration["last_opened_ecu"] = None
    save_config()


def translator(domain, lang=None):
    load_configuration()
    # Use provided language or configuration language
    target_lang = lang if lang else configuration.get("lang", lang_list["Default"])
    # Set up message catalog access with specific language
    global _current_translation
    _current_translation = gettext.translation(domain, str(BASE_DIR / "generated" / "locales"), languages=[str(target_lang)], fallback=True)
    return _dynamic_gettext

def dtt4all_time():
    if (sys.version_info[0] * 100 + sys.version_info[1]) > 306:
        return time.perf_counter_ns() / 1e9
    else:
        return time.time()