#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''module contains class for working with ELM327
   version: 160829
   Borrowed code from PyRen (modified for this use)
'''

import os
import platform
import re
import string
import sys
import threading
import time
from datetime import datetime

import serial
from serial.tools import list_ports

import options

_ = options.translator('ddt4all')
# //TODO missing entries this need look side ecu addressing missing entries or ignore {}
dnat_entries = {"E7": "7E4", "E8": "644"}
snat_entries = {"E7": "7EC", "E8": "5C4"}

snat = snat_entries
snat_ext = {}
dnat = dnat_entries
dnat_ext = {}

# Code snippet from https://github.com/rbei-etas/busmaster
negrsp = {"10": "NR: General Reject",
          "11": "NR: Service Not Supported",
          "12": "NR: SubFunction Not Supported",
          "13": "NR: Incorrect Message Length Or Invalid Format",
          "21": "NR: Busy Repeat Request",
          "22": "NR: Conditions Not Correct Or Request Sequence Error",
          "23": "NR: Routine Not Complete",
          "24": "NR: Request Sequence Error",
          "31": "NR: Request Out Of Range",
          "33": "NR: Security Access Denied- Security Access Requested  ",
          "35": "NR: Invalid Key",
          "36": "NR: Exceed Number Of Attempts",
          "37": "NR: Required Time Delay Not Expired",
          "40": "NR: Download not accepted",
          "41": "NR: Improper download type",
          "42": "NR: Can not download to specified address",
          "43": "NR: Can not download number of bytes requested",
          "50": "NR: Upload not accepted",
          "51": "NR: Improper upload type",
          "52": "NR: Can not upload from specified address",
          "53": "NR: Can not upload number of bytes requested",
          "70": "NR: Upload Download NotAccepted",
          "71": "NR: Transfer Data Suspended",
          "72": "NR: General Programming Failure",
          "73": "NR: Wrong Block Sequence Counter",
          "74": "NR: Illegal Address In Block Transfer",
          "75": "NR: Illegal Byte Count In Block Transfer",
          "76": "NR: Illegal Block Transfer Type",
          "77": "NR: Block Transfer Data Checksum Error",
          "78": "NR: Request Correctly Received-Response Pending",
          "79": "NR: Incorrect ByteCount During Block Transfer",
          "7E": "NR: SubFunction Not Supported In Active Session",
          "7F": "NR: Service Not Supported In Active Session",
          "80": "NR: Service Not Supported In Active Diagnostic Mode",
          "81": "NR: Rpm Too High",
          "82": "NR: Rpm Too Low",
          "83": "NR: Engine Is Running",
          "84": "NR: Engine Is Not Running",
          "85": "NR: Engine RunTime TooLow",
          "86": "NR: Temperature Too High",
          "87": "NR: Temperature Too Low",
          "88": "NR: Vehicle Speed Too High",
          "89": "NR: Vehicle Speed Too Low",
          "8A": "NR: Throttle/Pedal Too High",
          "8B": "NR: Throttle/Pedal Too Low",
          "8C": "NR: Transmission Range In Neutral",
          "8D": "NR: Transmission Range In Gear",
          "8F": "NR: Brake Switch(es)NotClosed (brake pedal not pressed or not applied)",
          "90": "NR: Shifter Lever Not In Park ",
          "91": "NR: Torque Converter Clutch Locked",
          "92": "NR: Voltage Too High",
          "93": "NR: Voltage Too Low"
          }

cmdb = '''
#v1.0 ;AC P; ATZ                   ; Z                  ; reset all
#v1.0 ;AC P; ATE1                  ; E0, E1             ; Echo off, or on*
#v1.0 ;AC P; ATL0                  ; L0, L1             ; Linefeeds off, or on
#v1.0 ;AC  ; ATI                   ; I                  ; print the version ID
#v1.0 ;AC  ; AT@1                  ; @1                 ; display the device description
#v1.0 ;AC P; ATAL                  ; AL                 ; Allow Long (>7 byte) messages
#v1.0 ;AC  ; ATBD                  ; BD                 ; perform a Buffer Dump
#V1.0 ;ACH ; ATSP4                 ; SP h               ; Set Protocol to h and save it
#v1.0 ;AC  ; ATBI                  ; BI                 ; Bypass the Initialization sequence
#v1.0 ;AC P; ATCAF0                ; CAF0, CAF1         ; Automatic Formatting off, or on*
#v1.0 ;AC  ; ATCFC1                ; CFC0, CFC1         ; Flow Controls off, or on*
#v1.0 ;AC  ; ATCP 01               ; CP hh              ; set CAN Priority to hh (29 bit)
#v1.0 ;AC  ; ATCS                  ; CS                 ; show the CAN Status counts
#v1.0 ;AC  ; ATCV 1250             ; CV dddd            ; Calibrate the Voltage to dd.dd volts
#v1.0 ;AC  ; ATD                   ; D                  ; set all to Defaults
#v1.0 ;AC  ; ATDP                  ; DP                 ; Describe the current Protocol
#v1.0 ;AC  ; ATDPN                 ; DPN                ; Describe the Protocol by Number
#v1.0 ;AC P; ATH0                  ; H0, H1             ; Headers off*, or on
#v1.0 ;AC  ; ATI                   ; I                  ; print the version ID
#v1.0 ;AC P; ATIB 10               ; IB 10              ; set the ISO Baud rate to 10400*
#v1.0 ;AC  ; ATIB 96               ; IB 96              ; set the ISO Baud rate to 9600
#v1.0 ;AC  ; ATL1                  ; L0, L1             ; Linefeeds off, or on
#v1.0 ;AC  ; ATM0                  ; M0, M1             ; Memory off, or on
#v1.0 ; C  ; ATMA                  ; MA                 ; Monitor All
#v1.0 ; C  ; ATMR 01               ; MR hh              ; Monitor for Receiver = hh
#v1.0 ; C  ; ATMT 01               ; MT hh              ; Monitor for Transmitter = hh
#v1.0 ;AC  ; ATNL                  ; NL                 ; Normal Length messages*
#v1.0 ;AC  ; ATPC                  ; PC                 ; Protocol Close
#v1.0 ;AC  ; ATR1                  ; R0, R1             ; Responses off, or on*
#v1.0 ;AC  ; ATRV                  ; RV                 ; Read the input Voltage
#v1.0 ;ACH ; ATSP7                 ; SP h               ; Set Protocol to h and save it
#v1.0 ;ACH ; ATSH 00000000         ; SH wwxxyyzz        ; Set Header to wwxxyyzz
#v1.0 ;AC  ; ATSH 001122           ; SH xxyyzz          ; Set Header to xxyyzz
#v1.0 ;AC P; ATSH 012              ; SH xyz             ; Set Header to xyz
#v1.0 ;AC  ; ATSP A6               ; SP Ah              ; Set Protocol to Auto, h and save it
#v1.0 ;AC  ; ATSP 6                ; SP h               ; Set Protocol to h and save it
#v1.0 ;AC  ; ATCM 123              ; CM hhh             ; set the ID Mask to hhh
#v1.0 ;AC  ; ATCM 12345678         ; CM hhhhhhhh        ; set the ID Mask to hhhhhhhh
#v1.0 ;AC  ; ATCF 123              ; CF hhh             ; set the ID Filter to hhh
#v1.0 ;AC  ; ATCF 12345678         ; CF hhhhhhhh        ; set the ID Filter to hhhhhhhh
#v1.0 ;AC P; ATST FF               ; ST hh              ; Set Timeout to hh x 4 msec
#v1.0 ;AC P; ATSW 96               ; SW 00              ; Stop sending Wakeup messages
#v1.0 ;AC P; ATSW 34               ; SW hh              ; Set Wakeup interval to hh x 20 msec
#v1.0 ;AC  ; ATTP A6               ; TP Ah              ; Try Protocol h with Auto search
#v1.0 ;AC  ; ATTP 6                ; TP h               ; Try Protocol h
#v1.0 ;AC P; ATWM 817AF13E         ; WM [1 - 6 bytes]   ; set the Wakeup Message
#v1.0 ;AC P; ATWS                  ; WS                 ; Warm Start (quick software reset)
#v1.1 ;AC P; ATFC SD 300000        ; FC SD [1 - 5 bytes]; FC, Set Data to [...]
#v1.1 ;AC P; ATFC SH 012           ; FC SH hhh          ; FC, Set the Header to hhh
#v1.1 ;AC P; ATFC SH 00112233      ; FC SH hhhhhhhh     ; Set the Header to hhhhhhhh
#v1.1 ;AC P; ATFC SM 1             ; FC SM h            ; Flow Control, Set the Mode to h
#v1.1 ;AC  ; ATPP FF OFF           ; PP FF OFF          ; all Prog Parameters disabled
#v1.1 ;AC  ; ATPP FF ON            ; PP FF ON           ; all Prog Parameters enabled
#v1.1 ;    ;                       ; PP xx OFF          ; disable Prog Parameter xx
#v1.1 ;    ;                       ; PP xx ON           ; enable Prog Parameter xx
#v1.1 ;    ;                       ; PP xx SV yy        ; for PP xx, Set the Value to yy
#v1.1 ;AC  ; ATPPS                 ; PPS                ; print a PP Summary
#v1.2 ;AC  ; ATAR                  ; AR                 ; Automatically Receive
#v1.2 ;AC 0; ATAT1                 ; AT0, 1, 2          ; Adaptive Timing off, auto1*, auto2
#v1.2 ;    ;                       ; BRD hh             ; try Baud Rate Divisor hh
#v1.2 ;    ;                       ; BRT hh             ; set Baud Rate Timeout
#v1.2 ;ACH ; ATSPA                 ; SP h               ; Set Protocol to h and save it
#v1.2 ; C  ; ATDM1                 ; DM1                ; monitor for DM1 messages
#v1.2 ; C  ; ATIFR H               ; IFR H, S           ; IFR value from Header* or Source
#v1.2 ; C  ; ATIFR0                ; IFR0, 1, 2         ; IFRs off, auto*, or on
#v1.2 ;AC  ; ATIIA 01              ; IIA hh             ; set ISO (slow) Init Address to hh
#v1.2 ;AC  ; ATKW0                 ; KW0, KW1           ; Key Word checking off, or on*
#v1.2 ; C  ; ATMP 0123             ; MP hhhh            ; Monitor for PGN 0hhhh
#v1.2 ; C  ; ATMP 0123 4           ; MP hhhh n          ; and get n messages
#v1.2 ; C  ; ATMP 012345           ; MP hhhhhh          ; Monitor for PGN hhhhhh
#v1.2 ; C  ; ATMP 012345 6         ; MP hhhhhh n        ; and get n messages
#v1.2 ;AC  ; ATSR 01               ; SR hh              ; Set the Receive address to hh
#v1.3 ;    ; AT@2                  ; @2                 ; display the device identifier
#v1.3 ;AC P; ATCRA 012             ; CRA hhh            ; set CAN Receive Address to hhh
#v1.3 ;AC  ; ATCRA 01234567        ; CRA hhhhhhhh       ; set the Rx Address to hhhhhhhh
#v1.3 ;AC  ; ATD0                  ; D0, D1             ; display of the DLC off*, or on
#v1.3 ;AC  ; ATFE                  ; FE                 ; Forget Events
#v1.3 ;AC  ; ATJE                  ; JE                 ; use J1939 Elm data format*
#v1.3 ;AC  ; ATJS                  ; JS                 ; use J1939 SAE data format
#v1.3 ;AC  ; ATKW                  ; KW                 ; display the Key Words
#v1.3 ;AC  ; ATRA 01               ; RA hh              ; set the Receive Address to hh
#v1.3 ;ACH ; ATSP6                 ; SP h               ; Set Protocol to h and save it
#v1.3 ;ACH ; ATRTR                 ; RTR                ; send an RTR message
#v1.3 ;AC  ; ATS1                  ; S0, S1             ; printing of aces off, or on*
#v1.3 ;AC  ; ATSP 00               ; SP 00              ; Erase stored protocol
#v1.3 ;AC  ; ATV0                  ; V0, V1             ; use of Variable DLC off*, or on
#v1.4 ;AC  ; ATCEA                 ; CEA                ; turn off CAN Extended Addressing
#v1.4 ;AC  ; ATCEA 01              ; CEA hh             ; use CAN Extended Address hh
#v1.4 ;AC  ; ATCV 0000             ; CV 0000            ; restore CV value to factory setting
#v1.4 ;AC  ; ATIB 48               ; IB 48              ; set the ISO Baud rate to 4800
#v1.4 ;AC  ; ATIGN                 ; IGN                ; read the IgnMon input level
#v1.4 ;    ;                       ; LP                 ; go to Low Power mode
#v1.4 ;AC  ; ATPB 01 23            ; PB xx yy           ; Protocol B options and baud rate
#v1.4 ;AC  ; ATRD                  ; RD                 ; Read the stored Data
#v1.4 ;AC  ; ATSD 01               ; SD hh              ; Save Data byte hh
#v1.4 ;ACH ; ATSP4                 ; SP h               ; Set Protocol to h and save it
#v1.4 ;AC P; ATSI                  ; SI                 ; perform a Slow (5 baud) Initiation
#v1.4 ;ACH ; ATZ                   ; Z                  ; reset all
#v1.4 ;ACH ; ATSP5                 ; SP h               ; Set Protocol to h and save it
#v1.4 ;AC P; ATFI                  ; FI                 ; perform a Fast Initiation
#v1.4 ;ACH ; ATZ                   ; Z                  ; reset all
#v1.4 ;AC  ; ATSS                  ; SS                 ; use Standard Search order (J1978)
#v1.4 ;AC  ; ATTA 12               ; TA hh              ; set Tester Address to hh
#v1.4 ;ACH ; ATSPA                 ; SP h               ; Set Protocol to h and save it
#v1.4 ;AC  ; ATCSM1                ; CSM0, CSM1         ; Silent Monitoring off, or on*
#v1.4 ;AC  ; ATJHF1                ; JHF0, JHF1         ; Header Formatting off, or on*
#v1.4 ;AC  ; ATJTM1                ; JTM1               ; set Timer Multiplier to 1*
#v1.4 ;AC  ; ATJTM5                ; JTM5               ; set Timer Multiplier to 5
#v1.4b;AC  ; ATCRA                 ; CRA                ; reset the Receive Address filters
#v2.0 ;AC  ; ATAMC                 ; AMC                ; display Activity Monitor Count
#v2.0 ;AC  ; ATAMT 20              ; AMT hh             ; set the Activity Mon Timeout to hh
#v2.1 ;AC  ; ATCTM1                ; CTM1               ; set Timer Multiplier to 1*
#v2.1 ;AC  ; ATCTM5                ; CTM5               ; set Timer Multiplier to 5
#v2.1 ;ACH ; ATZ                   ; Z                  ; reset all
'''


def clean_bytestring(value):
    # If is bytes -> decode
    # print(repr(value), type(value))
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='ignore')
    # If is string type "b'xxxx'" -> remove prefix b''
    value = str(value)
    if value.startswith("b'") and value.endswith("'"):
        return value[2:-1]
    return value


def addr_exist(addr):
    result = True
    if addr not in dnat:
        if addr not in dnat_ext:
            result = False
    return result


def get_can_addr(txa):
    for d in dnat.keys():
        if dnat[d].upper() == txa.upper():
            return d
    return None


def get_can_addr_ext(txa):
    for d in dnat_ext.keys():
        if dnat_ext[d].upper() == txa.upper():
            return d
    return None


def get_can_addr_snat(txa):
    for d in snat.keys():
        if snat[d].upper() == txa.upper():
            return d
    return None


def get_can_addr_snat_ext(txa):
    for d in snat_ext.keys():
        if snat_ext[d].upper() == txa.upper():
            return d
    return None


def item_count(items):
    return sum(1 for _ in items)


def get_available_ports():
    """Get available serial ports"""
    ports = []
    try:
        portlist = list_ports.comports()

        if item_count(portlist) == 0:
            return []

        iterator = sorted(list(portlist))
        for port, desc, hwid in iterator:
            # Enhanced device identification for ELS27 and other adapters
            device_desc = desc
            desc_upper = desc.upper()

            # Direct device name detection
            if any(keyword in desc_upper for keyword in ['ELS27', 'ELM327']):
                if 'ELS27' in desc_upper:
                    device_desc = f"{desc} (ELS27 V5 Compatible)"
                else:
                    device_desc = f"{desc} (ELM327 Compatible)"
            elif any(keyword in desc_upper for keyword in ['VLINKER', 'OBDII']):
                device_desc = f"{desc} (Vlinker Compatible)"
            elif any(keyword in desc_upper for keyword in ['VGATE', 'ICAR']):
                device_desc = f"{desc} (VGate Compatible)"
            elif any(keyword in desc_upper for keyword in ['OBDLINK', 'SCANTOOL']):
                device_desc = f"{desc} (OBDLink Compatible)"
            # Detect common USB-to-serial chips used by ELS27 V5 and other adapters
            elif any(chip in desc_upper for chip in ['FTDI', 'FT232', 'FT231X']):
                device_desc = f"{desc} (FTDI - Possible ELS27/ELM327)"
            elif any(chip in desc_upper for chip in ['CH340', 'CH341']):
                device_desc = f"{desc} (CH340 - Possible ELS27/ELM327)"
            elif any(chip in desc_upper for chip in ['CP210', 'CP2102', 'CP2104']):
                device_desc = f"{desc} (CP210x - Possible ELS27/ELM327)"
            elif any(chip in desc_upper for chip in ['PL2303']):
                device_desc = f"{desc} (PL2303 - Possible ELS27/ELM327)"

            ports.append((port, device_desc, hwid))

    except Exception as e:
        print(f"Error detecting serial ports: {e}")
        # Fallback: try common port patterns
        common_ports = []
        if platform.system().lower() == 'windows':
            common_ports = [f'COM{i}' for i in range(1, 21)]
        elif platform.system().lower() == 'linux':
            common_ports = [f'/dev/ttyUSB{i}' for i in range(0, 5)] + \
                           [f'/dev/ttyACM{i}' for i in range(0, 5)] + \
                           [f'/dev/rfcomm{i}' for i in range(0, 5)]
        elif platform.system().lower() == 'darwin':
            import glob
            common_ports = glob.glob('/dev/cu.*') + glob.glob('/dev/tty.*')

        for port in common_ports:
            try:
                # Test if port exists and is accessible
                test_serial = serial.Serial(port, timeout=0.1)
                test_serial.close()
                ports.append((port, "Unknown Device", ""))
            except:
                continue

    return ports


class DeviceManager:
    """Device manager for OBD-II adapters with optimal settings"""

    @staticmethod
    def get_optimal_settings(device_type):
        """Get optimal connection settings for specific device types"""
        settings = {
            'vlinker': {'baudrate': 38400, 'timeout': 3, 'rtscts': False, 'dsrdtr': False},
            'elm327': {'baudrate': 38400, 'timeout': 5, 'rtscts': False, 'dsrdtr': False},
            'obdlink': {'baudrate': 115200, 'timeout': 2, 'rtscts': True, 'dsrdtr': False},
            'obdlink_ex': {'baudrate': 115200, 'timeout': 2, 'rtscts': True, 'dsrdtr': False},
            'els27': {'baudrate': 38400, 'timeout': 4, 'rtscts': False, 'dsrdtr': False, 'can_pins': '12-13'},
            'vgate': {'baudrate': 115200, 'timeout': 2, 'rtscts': False, 'dsrdtr': False},

            'unknown': {'baudrate': 38400, 'timeout': 5, 'rtscts': False, 'dsrdtr': False}
        }
        return settings.get(DeviceManager.normalize_adapter_type(device_type), settings['unknown'])

    @staticmethod
    def normalize_adapter_type(adapter_type):
        """Normalize UI adapter types to internal device types"""
        adapter_mapping = {
            'STD_BT': 'elm327',  # Bluetooth ELM327
            'STD_WIFI': 'elm327',  # WiFi ELM327
            'STD_USB': 'elm327',  # USB ELM327
            'STD': 'elm327',  # Standard ELM327
            'OBDLINK': 'obdlink',  # OBDLink devices
            'OBDLINK_EX': 'obdlink_ex',  # OBDLink EX devices
            'ELS27': 'els27',  # ELS27 devices
            'VLINKER': 'vlinker',  # Vlinker devices
            'VGATE': 'vgate',  # VGate devices
            'USBCAN': 'unknown'  # USB CAN adapters - use unknown defaults
        }
        return adapter_mapping.get(adapter_type.upper(), 'elm327')


def is_els27_device(port, timeout=2):
    """Test if a serial port has an ELS27 device with multiple baud rates"""
    import serial
    test_bauds = [38400, 9600, 115200]  # Common ELS27 baud rates

    for baud in test_bauds:
        try:
            ser = serial.Serial(port, baud, timeout=timeout)

            # Clear buffers
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            # Send ATZ (reset) command
            ser.write(b'ATZ\r')
            response = ser.read(100).decode('ascii', errors='ignore')
            ser.close()

            # Check for ELS27 or ELM327 response
            response_upper = response.upper()
            if any(keyword in response_upper for keyword in ['ELS27', 'ELM327', 'OBD']):
                return True, f"{response.strip()} (at {baud} baud)"

        except Exception:
            continue

    return False, "No ELS27 response at any baud rate"


def reconnect_elm():
    """Enhanced reconnection with device-specific handling"""
    ports = get_available_ports()
    current_adapter = "STD"
    if options.elm:
        current_adapter = options.elm.adapter_type

    # Try to reconnect to the same port first
    if options.port_name:
        for port_info in ports:
            port, desc, hwid = port_info if len(port_info) == 3 else (port_info[0], port_info[1], "")
            if port == options.port_name or desc == options.port_name:
                print(f"Attempting reconnection to {port}")
                try:
                    # Use saved settings for reconnection
                    device_key = DeviceManager.normalize_adapter_type(current_adapter)
                    saved_settings = options.get_device_settings(device_key, port)
                    speed = saved_settings.get('baudrate', options.port_speed) if saved_settings else options.port_speed

                    options.elm = ELM(port, speed, current_adapter)
                    if options.elm.connectionStatus:
                        return True
                except Exception as e:
                    print(f"Reconnection failed: {e}")
                    continue

    # Try other available ports
    for port_info in ports:
        port, desc, hwid = port_info if len(port_info) == 3 else (port_info[0], port_info[1], "")
        device_key = DeviceManager.normalize_adapter_type(current_adapter)
        saved_settings = options.get_device_settings(device_key, port)

        if saved_settings and 'baudrate' in saved_settings:
            settings = saved_settings
            print(f"Trying {current_adapter} device at {port} with saved settings")
        else:
            settings = DeviceManager.get_optimal_settings(current_adapter)
            print(f"Trying {current_adapter} device at {port} with optimal settings")

        try:
            options.elm = ELM(port, settings['baudrate'], current_adapter)
            if options.elm.connectionStatus:
                options.port_name = port
                options.port_speed = settings['baudrate']
                return True
        except Exception as e:
            print(f"Connection to {port} failed: {e}")
            continue

    return False


def errorval(val):
    if val in list(negrsp.keys()):
        return negrsp[val]

    return "Unregistered error"


class Port:
    '''Enhanced serial port and TCP connection handler
       Supports USB, Bluetooth, WiFi OBD-II devices with cross-platform compatibility
       - Serial ports: USB ELM327, Vlinker FS, ObdLink SX, ELS27
       - TCP/WiFi: WiFi ELM327 adapters (192.168.0.10:35000 format)
       - Bluetooth: Bluetooth ELM327 adapters
    '''
    connectionStatus = False
    portType = 0  # 0-serial 1-tcp 2-bluetooth
    ipaddr = '192.168.0.10'
    tcpprt = 35000
    portName = ""
    droid = None
    btcid = None

    hdr = None
    _lock = None  # Thread lock for connection safety
    tcp_needs_reconnect = False
    reconnect_attempts = 0
    max_reconnect_attempts = 3

    def __init__(self, portName, speed, adapter_type):
        options.elm_failed = False
        self.adapter_type = adapter_type
        self._lock = threading.Lock()
        self.reconnect_attempts = 0

        portName = portName.strip()

        # WiFi/TCP connection (e.g., 192.168.0.10:35000)
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$", portName):
            import socket
            self.ipaddr, self.tcpprt = portName.split(':')
            self.tcpprt = int(self.tcpprt)
            self.portType = 1
            self.portName = portName
            self.init_wifi()
        # Bluetooth connection detection (common Bluetooth patterns)
        elif any(bt_pattern in portName.lower() for bt_pattern in ['rfcomm', 'bluetooth', 'bt']):
            self.portName = portName
            self.portType = 2
            self.init_bluetooth()
        # Serial/USB connection
        else:
            self.portName = portName
            self.portType = 0
            self.init_serial(speed)

    def init_serial(self, speed):
        """Initialize serial/USB connection with enhanced error handling"""
        try:
            # Check for saved device settings first, use optimal settings as fallback
            device_key = DeviceManager.normalize_adapter_type(self.adapter_type)
            saved_settings = options.get_device_settings(device_key, self.portName)

            if saved_settings and 'baudrate' in saved_settings:
                settings = saved_settings
                translate_arg = _("Using saved settings for")
                print (f"{translate_arg} {self.adapter_type}: {settings}")
            else:
                settings = DeviceManager.get_optimal_settings(self.adapter_type)
                translate_arg = _("Using optimal settings for")
                print(f"{translate_arg} {self.adapter_type}: {settings}")

            # Use provided speed if specified, otherwise use setting
            if speed > 0:
                settings['baudrate'] = speed

            # Platform-specific serial port configuration
            current_platform = platform.system().lower()

            # Enhanced serial parameters using device-specific settings
            serial_params = {
                'port': self.portName,
                'baudrate': settings.get('baudrate', speed),
                'timeout': settings.get('timeout', 5),
                'parity': serial.PARITY_NONE,
                'stopbits': serial.STOPBITS_ONE,
                'bytesize': serial.EIGHTBITS,
                'xonxoff': False,
                'rtscts': settings.get('rtscts', False),
                'dsrdtr': settings.get('dsrdtr', False)
            }

            # Platform-specific adjustments
            if current_platform == 'linux':
                # Linux: Set exclusive access to prevent conflicts
                serial_params['exclusive'] = True
            elif current_platform == 'darwin':
                # macOS: Specific settings for USB-serial adapters
                serial_params['rtscts'] = False
                serial_params['dsrdtr'] = False

            self.hdr = serial.Serial(**serial_params)

            # Flush buffers to ensure clean start
            self.hdr.reset_input_buffer()
            self.hdr.reset_output_buffer()

            translate_arg = _("Serial port opened")
            print(f"{translate_arg}: {self.hdr}")
            self.connectionStatus = True

            # Save successful connection settings
            if self.connectionStatus:
                connection_settings = {
                    'baudrate': serial_params['baudrate'],
                    'timeout': serial_params['timeout'],
                    'rtscts': serial_params['rtscts'],
                    'dsrdtr': serial_params['dsrdtr']
                }
                options.save_device_settings(device_key, connection_settings, self.portName)

        except serial.SerialException as e:
            error_msg = f"Serial connection error: {e}"
            print(_("Error: ") + error_msg)
            print(_("ELM not connected or wrong COM port"), self.portName)
            options.last_error = error_msg
            options.elm_failed = True
            self.connectionStatus = False
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(_("Error: ") + error_msg)
            options.last_error = error_msg
            options.elm_failed = True
            self.connectionStatus = False

    def init_bluetooth(self):
        """Initialize Bluetooth connection"""
        try:
            # For now, treat Bluetooth as serial with special handling
            # Future enhancement: implement proper Bluetooth socket handling
            self.init_serial(38400)
            print(f"Bluetooth connection attempted: {self.portName}")
        except Exception as e:
            print(f"Bluetooth connection failed: {e}")
            options.elm_failed = True
            self.connectionStatus = False

    def close(self):
        """Enhanced close method with proper cleanup"""
        with self._lock:
            try:
                if self.hdr:
                    if self.portType == 0:  # Serial
                        if hasattr(self.hdr, 'reset_input_buffer'):
                            self.hdr.reset_input_buffer()
                        if hasattr(self.hdr, 'reset_output_buffer'):
                            self.hdr.reset_output_buffer()
                    self.hdr.close()
                    print(_("Port closed"))
                self.connectionStatus = False
            except (AttributeError, OSError, Exception) as e:
                print(f"Error closing port: {e}")
            finally:
                self.hdr = None

    def init_wifi(self, reinit=False):
        '''
        Enhanced WiFi/TCP connection with better error handling and reconnection
        '''
        if self.portType != 1:
            return

        import socket

        try:
            if reinit and self.hdr:
                self.hdr.close()

            self.hdr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.hdr.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.hdr.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Set connection timeout
            self.hdr.settimeout(10)  # 10 seconds for connection

            print(f"Connecting to WiFi adapter at {self.ipaddr}:{self.tcpprt}")
            self.hdr.connect((self.ipaddr, self.tcpprt))

            # Configure socket timeout based on settings
            if getattr(options, "socket_timeout", True):
                self.hdr.settimeout(5)
            else:
                self.hdr.setblocking(True)

            self.connectionStatus = True
            self.tcp_needs_reconnect = False
            self.reconnect_attempts = 0
            print(f"WiFi connection established: {self.ipaddr}:{self.tcpprt}")

        except socket.timeout:
            error_msg = f"WiFi connection timeout to {self.ipaddr}:{self.tcpprt}"
            print(_("Error: ") + error_msg)
            options.last_error = error_msg
            options.elm_failed = True
            self.connectionStatus = False
        except socket.error as e:
            error_msg = f"WiFi connection error: {e}"
            print(_("Error: ") + error_msg)
            options.last_error = error_msg
            options.elm_failed = True
            self.connectionStatus = False
        except Exception as e:
            error_msg = f"Unexpected WiFi error: {e}"
            print(_("Error: ") + error_msg)
            options.last_error = error_msg
            options.elm_failed = True
            self.connectionStatus = False

    def read_byte(self):
        """Enhanced read_byte with better error handling and reconnection"""
        with self._lock:
            try:
                byte = b""
                if self.portType == 1:  # TCP/WiFi
                    import socket
                    try:
                        # byte = self.hdr.recv(1)
                        byte = self.hdr.read(1)
                        if options.debug:
                            print(f"WiFi recv: {byte}")
                    except socket.timeout:
                        self.tcp_needs_reconnect = True
                        return None
                    except (socket.error, ConnectionResetError) as e:
                        print(f"WiFi connection error: {e}")
                        self.tcp_needs_reconnect = True
                        return None
                elif self.portType == 2:  # Bluetooth
                    if self.droid and self.droid.bluetoothReadReady():
                        byte = self.droid.bluetoothRead(1).result
                    else:
                        # Fallback to serial read for Bluetooth-serial adapters
                        if self.hdr and hasattr(self.hdr, 'in_waiting') and self.hdr.in_waiting:
                            byte = self.hdr.read(1)
                else:  # Serial/USB
                    if self.hdr and hasattr(self.hdr, 'in_waiting') and self.hdr.in_waiting:
                        byte = self.hdr.read(1)
                    elif self.hdr and hasattr(self.hdr, 'inWaiting') and self.hdr.inWaiting():
                        byte = self.hdr.read(1)

                return byte

            except serial.SerialException as e:
                print(f"Serial error in read_byte: {e}")
                self.connectionStatus = False
                return None
            except Exception as e:
                print('*' * 40)
                print('*       ' + _('Connection to ELM was lost'))
                print(f'*       Error: {e}')
                self.connectionStatus = False
                self.close()
                return None

    def read(self):
        """Enhanced read method with better error handling"""
        try:
            byte = self.read_byte()
            if byte is None:
                return None

            try:
                return byte.decode("utf-8")
            except UnicodeDecodeError:
                # Try different encodings
                for encoding in ['latin1', 'ascii', 'cp1252']:
                    try:
                        return byte.decode(encoding)
                    except:
                        continue
                print(_("Cannot decode bytes ") + str(byte))
                return ""
        except Exception as e:
            print(f"Error in read(): {e}")
            return None

    def change_rate(self, rate):
        self.hdr.baudrate = rate

    def write(self, data):
        """Enhanced write method with automatic reconnection and better error handling"""
        with self._lock:
            try:
                if not isinstance(data, bytes):
                    data = data.encode('utf-8')

                if self.portType == 1:  # TCP/WiFi
                    if self.tcp_needs_reconnect:
                        print("Attempting WiFi reconnection...")
                        self.tcp_needs_reconnect = False
                        self.init_wifi(True)
                        if not self.connectionStatus:
                            return None
                    # return self.hdr.sendall(data)
                    return self.hdr.write(data)
                elif self.portType == 2:  # Bluetooth
                    if self.droid:
                        return self.droid.bluetoothWrite(data)
                    else:
                        # Fallback to serial write for Bluetooth-serial adapters
                        return self.hdr.write(data)
                else:  # Serial/USB
                    return self.hdr.write(data)

            except serial.SerialException as e:
                print(f"Serial write error: {e}")
                self.connectionStatus = False
                return None
            except Exception as e:
                print('*' * 40)
                print('*       ' + _('Connection to ELM was lost'))
                print(f'*       Write error: {e}')
                self.connectionStatus = False
                self.close()
                return None

    def expect_carriage_return(self, time_out=1):
        tb = time.time()  # start time
        self.buff = b""

        while True:
            if not options.simulation_mode:
                byte = self.read_byte()
            else:
                byte = '>'

            if byte:
                self.buff += byte
            tc = time.time()

            if b'\r' in self.buff:
                return self.buff.decode('utf8')

            if (tc - tb) > time_out:
                return self.buff + b"TIMEOUT"

        # self.close()
        # self.connectionStatus = False
        # return ''

    def expect(self, pattern, time_out=1):
        tb = time.time()  # start time
        self.buff = ""

        while True:
            if not options.simulation_mode:
                byte = self.read()
            else:
                byte = '>'

            if byte == '\r':
                byte = '\n'
            if byte:
                self.buff += byte
            tc = time.time()
            if pattern in self.buff:
                return self.buff
            if (tc - tb) > time_out:
                return self.buff + _("TIMEOUT")

        # self.close()
        # self.connectionStatus = False
        # return ''

    def check_elm(self):

        timeout = 2

        for s in [38400, 115200, 230400, 57600, 9600, 500000]:
            print("\r\t\t\t\t\r" + _("Checking port speed:"), s, )
            sys.stdout.flush()

            self.hdr.baudrate = s
            # self.hdr.flushInput()
            self.hdr.reset_input_buffer()
            self.write("\r")

            # search > string
            tb = time.time()  # start time
            self.buff = ""
            while (True):
                if not options.simulation_mode:
                    byte = self.read()
                else:
                    byte = '>'
                self.buff += byte
                tc = time.time()
                if '>' in self.buff:
                    options.port_speed = s
                    print("\n" + _("Start COM speed :"), s)
                    self.hdr.timeout = timeout
                    return True
                if (tc - tb) > 1:
                    break
        print("\n" + _("ELM not responding"))
        return False


class ELM:
    '''ELM327 class'''

    port = 0
    lf = 0
    vf = 0

    keepAlive = 4  # send startSession to CAN after silence if startSession defined
    busLoad = 0  # I am sure than it should be zero
    srvsDelay = 0  # the delay next command requested by service
    lastCMDtime = 0  # time when last command was sent to bus
    portTimeout = 5  # timeout of port (com or tcp)
    elmTimeout = 0  # timeout set by ATST

    # error counters
    error_frame = 0
    error_bufferfull = 0
    error_question = 0
    error_nodata = 0
    error_timeout = 0
    error_rx = 0
    error_can = 0
    canline = 0

    response_time = 0

    buff = ""
    currentprotocol = ""
    currentsubprotocol = ""
    currentaddress = ""
    startSession = ""
    lastinitrsp = ""
    adapter_type = "STD"  # ELM adapter type: STD, OBDLINK, etc.

    rsp_cache = {}
    l1_cache = {}

    ATR1 = True
    ATCFC0 = False

    portName = ""

    lastMessage = ""
    monitorstop = False

    connectionStatus = False

    def __init__(self, portName, rate, adapter_type, maxspeed="No"):
        self.adapter_type = adapter_type
        options.port_speed = rate
        for speed in [int(rate), 38400, 115200, 230400, 57600, 9600, 500000, 1000000, 2000000]:
            print(_("Trying to open port ") + "%s @ %i" % (portName, speed))

            if not options.simulation_mode:
                self.port = Port(portName, speed, self.adapter_type)

            if options.elm_failed:
                self.connectionStatus = False
                # Try one other speed ...
                continue

            options.port_speed = speed

            if not os.path.exists("./logs"):
                os.mkdir("./logs")

            if len(options.log) > 0:
                self.lf = open("./logs/elm_" + options.log + ".txt", "at", encoding="utf-8")
                self.vf = open("./logs/ecu_" + options.log + ".txt", "at", encoding="utf-8")
                self.vf.write("# TimeStamp;Address;Command;Response;Error\n")

            self.lastCMDtime = 0
            self.ATCFC0 = options.opt_cfc0

            # Purge unread data
            self.port.expect(">")
            res = self.send_raw("ATZ")
            if 'ELM' in res or 'OBDII' in res:
                options.last_error = ""
                options.elm_failed = False
                self.connectionStatus = True
                rate = speed
                break
            else:
                options.elm_failed = True
                options.last_error = _("No ELM interface on port") + " %s" % portName

        try:
            maxspeed = int(maxspeed)
        except:
            maxspeed = 0

        device_text_switch = _("OBDLink Connection OK, attempting full speed UART switch")
        text_switck_error = _("Failed to switch to change OBDLink to ") + str(maxspeed)
        text_optional = _("OBDLINK Connection OK, using optimal settings")
        if adapter_type == "OBDLINK" and maxspeed > 0 and not options.elm_failed and rate != 2000000:
            print(device_text_switch.replace("OBDLink", "OBDLink"))
            try:
                self.raise_odb_speed(maxspeed, "OBDLink")
            except:
                options.elm_failed = True
                self.connectionStatus = False
                print(text_switck_error.replace("OBDLink", "OBDLink"))
        elif adapter_type == "OBDLINK":
            print(text_optional.replace("OBDLink", "OBDLink"))
            if not options.elm_failed:
                print(_("Connection established successfully"))
        elif adapter_type == "STD_USB" and rate != 115200 and maxspeed > 0:
            print(device_text_switch.replace("OBDLink", "ELM"))
            try:
                self.raise_elm_speed(maxspeed)
            except:
                options.elm_failed = True
                self.connectionStatus = False
                print(text_switck_error.replace("OBDLink", "ELM"))
        elif adapter_type == "STD_USB":
            print(text_optional.replace("OBDLink", "ELM"))
            if not options.elm_failed:
                print(_("Connection established successfully"))
        elif adapter_type == "VLINKER" and 0 < maxspeed != rate:
            print(device_text_switch.replace("OBDLink", "Vlinker"))
            try:
                self.raise_elm_speed(maxspeed)
            except:
                options.elm_failed = True
                self.connectionStatus = False
                print(text_switck_error.replace("OBDLink", "Vlinker"))
        elif adapter_type == "VLINKER":
            print(text_optional.replace("OBDLink", "Vlinker"))
            if not options.elm_failed:
                print(_("Connection established successfully"))
        elif adapter_type == "VGATE" and 0 < maxspeed != rate:
            print(device_text_switch.replace("OBDLink", "Vgate"))
            try:
                self.raise_odb_speed(maxspeed, "VGate")
            except:
                options.elm_failed = True
                self.connectionStatus = False
                print(text_switck_error.replace("OBDLink", "VGate"))
        elif adapter_type == "VGATE":
            print(text_optional.replace("OBDLink", "VGate"))
            if not options.elm_failed:
                print(_("Connection established successfully"))
        elif adapter_type == "ELS27":
            print(text_optional.replace("OBDLink", "ELS27"))
            if not options.elm_failed:
                # ELS27 V5 specific initialization - set CAN pins 12-13
                try:
                    print(_("Configuring ELS27 V5 CAN pins (12-13)"))
                    # Send ELS27 specific commands for CAN pin configuration
                    self.send_raw("ATSP6")  # Set protocol to CAN
                    self.send_raw("ATSH81")  # Set header for CAN
                    print(_("ELS27 V5 CAN configuration complete"))
                except Exception as e:
                    print(f"ELS27 V5 configuration warning: {e}")
                print(_("Connection established successfully"))
        elif adapter_type in ["STD_BT", "STD_WIFI"]:
            print(text_optional.replace("OBDLink", adapter_type))
            if not options.elm_failed:
                print(_("Connection established successfully"))

    def raise_odb_speed(self, baudrate, device_name="OBDLINK"):
        # Software speed switch
        res = self.port.write(("ST SBR " + str(baudrate) + "\r").encode('utf-8'))

        # Command echo
        res = self.port.expect_carriage_return()
        # Command result
        res = self.port.expect_carriage_return()
        if "OK" in res:
            text = _("OBDLINK switched baurate OK, changing UART speed now...").replace("OBDLINK", device_name)
            print(text)
            self.port.change_rate(baudrate)
            time.sleep(0.5)
            res = self.send_raw("STI").replace("\n", "").replace(">", "").replace("STI", "")
            if "STN" in res:
                text1 = _("OBDLINK full speed connection OK").replace("OBDLINK", device_name)
                print(text1)
                text2 = _("OBDLink Version ").replace("OBDLINK", device_name) + res
                print(text2)
            else:
                raise
        else:
            raise

    def raise_elm_speed(self, baudrate):
        # Software speed switch to 115Kbps
        if baudrate == 57600:
            self.port.write("ATBRD 45\r".encode("utf-8"))
        elif baudrate == 115200:
            self.port.write("ATBRD 23\r".encode("utf-8"))
        elif baudrate == 230400:
            self.port.write("ATBRD 11\r".encode("utf-8"))
        elif baudrate == 500000:
            self.port.write("ATBRD 8\r".encode("utf-8"))
        else:
            return

        # Command echo result
        res = self.port.expect_carriage_return()
        if "OK" in res:
            print(_("ELM baudrate switched OK, changing UART speed now..."))
            self.port.change_rate(baudrate)
            version = self.port.expect_carriage_return()
            if "ELM327" in version:
                self.port.write('\r'.encode('utf-8'))
                res = self.port.expect('>')
                if "OK" in res:
                    print(_("ELM full speed connection OK "))
                    print(_("Version ") + version)
                else:
                    raise
            else:
                raise
        else:
            print(_("Your ELM does not support baudrate ") + str(baudrate))
            raise

    def __del__(self):
        try:
            if _ is not None:
                print(_("ELM reset..."))
            else:
                print("ELM reset...")
            self.port.write("ATZ\r".encode("utf-8"))
        except (AttributeError, OSError):
            pass

    def connectionStat(self):
        return self.port.connectionStatus

    def clear_cache(self):
        ''' Clear L2 cache before screen update
        '''
        self.rsp_cache = {}

    def request(self, req, positive='', cache=True, serviceDelay="0"):
        ''' Check if request is saved in L2 cache.
            If not then
              - make real request
              - convert responce to one line
              - save in L2 cache
            returns response without consistency check
        '''
        if cache and req in self.rsp_cache.keys():
            return self.rsp_cache[req]

        # send cmd
        rsp = self.cmd(req, serviceDelay)
        if 'WRONG' in rsp:
            return rsp

        # parse responce
        res = ""
        if self.currentprotocol != "can":
            # Trivially reject first line (echo)
            rsp_split = rsp.split('\n')[1:]
            for s in rsp_split:
                if '>' not in s and len(s.strip()):
                    res += s.strip() + ' '
        else:
            for s in rsp.split('\n'):
                if ':' in s:
                    res += s[2:].strip() + ' '
                else:  # responce consists only from one frame
                    if s.replace(' ', '').startswith(positive.replace(' ', '')):
                        res += s.strip() + ' '

        rsp = res

        # populate L2 cache
        self.rsp_cache[req] = rsp

        # save log

        if self.vf != 0:
            errorstr = "Unknown"
            if rsp[6:8] in list(negrsp.keys()):
                errorstr = errorval(rsp[6:8])
            tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            if self.currentaddress in dnat_ext and len(self.currentaddress) == 8:
                self.vf.write(tmstr + ";" + dnat_ext[
                    self.currentaddress] + ";" + req.replace(' ', '') + ";" + rsp + ";" + errorstr + "\n")
            elif self.currentaddress in dnat:
                self.vf.write(tmstr + ";" + dnat[
                    self.currentaddress] + ";" + req.replace(' ', '') + ";" + rsp + ";" + errorstr + "\n")
            else:
                print(_("Unknown address: "), self.currentaddress, req.replace(' ', ''))
            self.vf.flush()

        return rsp

    def cmd(self, command, serviceDelay="0"):
        tb = time.time()  # start time

        # Ensure time gap between commands
        dl = self.busLoad + self.srvsDelay - tb + self.lastCMDtime
        if ((tb - self.lastCMDtime) < (self.busLoad + self.srvsDelay)) \
                and ("AT" not in command.upper() or "ST" not in command.upper()):
            time.sleep(self.busLoad + self.srvsDelay - tb + self.lastCMDtime)

        tb = time.time()  # renew start time

        # If we use wifi and there was more than keepAlive seconds of silence then reinit tcp
        if (tb - self.lastCMDtime) > self.keepAlive:
            self.port.init_wifi(True)

        # If we are on CAN and there was more than keepAlive seconds of silence and
        # start_session_can was executed then send startSession command again
        # if ((tb-self.lastCMDtime)>self.keepAlive and self.currentprotocol=="can"
        if ((tb - self.lastCMDtime) > self.keepAlive
                and self.currentprotocol == "can"
                and len(self.startSession) > 0):

            # log KeepAlive event
            if self.lf != 0:
                tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self.lf.write("# [" + tmstr + "] KeepAlive\n")
                self.lf.flush()

                # send keepalive
            self.send_cmd(self.startSession)
            self.lastCMDtime = time.time()  # for not to get into infinite loop

        # send command
        cmdrsp = self.send_cmd(command)
        self.lastCMDtime = tc = time.time()

        # add srvsDelay to time gap before send next command
        self.srvsDelay = float(serviceDelay) / 1000.

        # check for negative response
        for l in cmdrsp.split('\n'):
            l = l.strip().upper()
            if l.startswith("7F") and len(l) == 8 and l[6:8] in negrsp.keys():
                print(l, negrsp[l[6:8]])
                if self.lf != 0:
                    self.lf.write("# [" + str(tc - tb) + "] rsp: " + l + ": " + negrsp[l[6:8]] + "\n")
                    self.lf.flush()
        return cmdrsp

    def set_can_timeout(self, value):
        val = value // 4
        if val > 255:
            val = 255
        val = hex(val)[2:].upper().zfill(2)
        self.cmd("AT ST %s" % val)

    def send_cmd(self, command):
        if "AT" in command.upper() or "ST" in command.upper() or self.currentprotocol != "can":
            return self.send_raw(command)
        if self.ATCFC0:
            return self.send_can_cfc0(command)
        else:
            rsp = self.send_can(command)
            return rsp

    def send_can(self, command):
        command = command.strip().replace(' ', '')

        if len(command) % 2 != 0 or len(command) == 0:
            return "ODD ERROR"
        if not all(c in string.hexdigits for c in command):
            return "HEX ERROR"

        # do framing
        raw_command = []
        cmd_len = int(len(command) / 2)
        if cmd_len < 8:  # single frame
            # check L1 cache here
            if command in self.l1_cache.keys():
                raw_command.append(("%0.2X" % cmd_len) + command + self.l1_cache[command])
            else:
                raw_command.append(("%0.2X" % cmd_len) + command)
        else:
            # first frame
            raw_command.append("1" + ("%0.3X" % cmd_len)[-3:] + command[:12])
            command = command[12:]
            # consecutive frames
            frame_number = 1
            while (len(command)):
                raw_command.append("2" + ("%X" % frame_number)[-1:] + command[:14])
                frame_number = frame_number + 1
                command = command[14:]

        responses = []

        # send frames
        for f in raw_command:
            # send next frame
            frsp = self.send_raw(f)
            # analyse response (1 phase)
            for s in frsp.split('\n'):
                if s.strip() == f:  # echo cancellation
                    continue
                s = s.strip().replace(' ', '')
                if len(s) == 0:  # empty string
                    continue
                if all(c in string.hexdigits for c in s):  # some data
                    if s[:1] == '3':  # flow control, just ignore it in this version
                        continue
                    responses.append(s)

        # analyse response (2 phases)
        result = ""
        noerrors = True
        cframe = 0  # frame counter
        nbytes = 0  # number bytes in response
        nframes = 0

        if len(responses) == 0:  # no data in response
            return ""

        if len(responses) > 1 and responses[0].startswith('037F') and responses[0][6:8] == '78':
            responses = responses[1:]

        if len(responses) == 1:  # single frame response
            if responses[0][:1] == '0':
                nbytes = int(responses[0][1:2], 16)
                nframes = 1
                result = responses[0][2:2 + nbytes * 2]
            else:  # wrong response (not all frames received)
                self.error_frame += 1
                noerrors = False
        else:  # multi frame response
            if responses[0][:1] == '1':  # first frame
                nbytes = int(responses[0][1:4], 16)
                nframes = nbytes / 7 + 1
                cframe = 1
                result = responses[0][4:16]
            else:  # wrong response (first frame omitted)
                self.error_frame += 1
                noerrors = False

            for fr in responses[1:]:
                if fr[:1] == '2':  # consecutive frames
                    tmp_fn = int(fr[1:2], 16)
                    if tmp_fn != (cframe % 16):  # wrong response (frame lost)
                        self.error_frame += 1
                        noerrors = False
                        continue
                    cframe += 1
                    result += fr[2:16]
                else:  # wrong response
                    self.error_frame += 1
                    noerrors = False

        errorstr = "Unknown"
        # check for negative response (repeat the same as in cmd())
        if result[:2] == '7F':
            noerrors = False
            if result[4:6] in list(negrsp.keys()):
                errorstr = errorval(result[4:6])
            if self.vf != 0:
                tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                if self.currentaddress in dnat_ext and len(self.currentaddress) == 8:
                    self.vf.write(tmstr + ";" + dnat_ext[
                        self.currentaddress] + ";" + command + ";" + result + ";" + errorstr + "\n")
                elif self.currentaddress in dnat:
                    self.vf.write(tmstr + ";" + dnat[
                        self.currentaddress] + ";" + command + ";" + result + ";" + errorstr + "\n")
                self.vf.flush()

        # populate L1 cache
        if noerrors and nframes < 16 and command[:1] == '2' and not options.opt_n1c:
            self.l1_cache[command] = str(nframes)

        if len(result) / 2 >= nbytes and noerrors:
            # Remove unnecessary bytes
            result = result[0:nbytes * 2]
            # split by bytes and return
            result = ' '.join(a + b for a, b in zip(result[::2], result[1::2]))
            return result
        else:
            return "WRONG RESPONSE : " + errorstr + "(" + result + ")"

    def send_can_cfc0(self, command):
        command = command.strip().replace(' ', '')

        if len(command) % 2 != 0 or len(command) == 0:
            return "ODD ERROR"
        if not all(c in string.hexdigits for c in command):
            return "HEX ERROR"

        # do framing
        raw_command = []
        cmd_len = int(len(command) / 2)
        if cmd_len < 8:  # single frame
            raw_command.append(("%0.2X" % cmd_len) + command)
        else:
            # first frame
            raw_command.append("1" + ("%0.3X" % cmd_len)[-3:] + command[:12])
            command = command[12:]
            # consecutive frames
            frame_number = 1
            while len(command):
                raw_command.append("2" + ("%X" % frame_number)[-1:] + command[:14])
                frame_number += 1
                command = command[14:]

        responses = []

        # send frames
        BS = 1  # Burst Size
        ST = 0  # Frame Interval
        Fc = 0  # Current frame
        Fn = len(raw_command)  # Number of frames

        if Fn > 1 or len(raw_command[0]) > 15:
            if options.cantimeout > 0:
                self.set_can_timeout(options.cantimeout)
            else:
                # set elm timeout to 300ms for first response
                self.send_raw('AT ST 4B')

        while Fc < Fn:
            # enable responses
            if not self.ATR1:
                frsp = self.send_raw('AT R1')
                self.ATR1 = True

            tb = time.time()  # time of sending (ff)

            if Fn > 1 and Fc == (Fn - 1):  # set elm timeout to maximum for last response on long command
                self.send_raw('AT ST FF')
                self.send_raw('AT AT 1')

            if (Fc == 0 or Fc == (Fn - 1)) and len(
                    raw_command[Fc]) < 16:  # first or last frame in command and len<16 (bug in ELM)
                frsp = self.send_raw(raw_command[Fc] + '1')  # we'll get only 1 frame: nr, fc, ff or sf
            else:
                frsp = self.send_raw(raw_command[Fc])

            Fc = Fc + 1

            # analyse response
            for s in frsp.split('\n'):
                if s.strip()[:len(raw_command[Fc - 1])] == raw_command[Fc - 1]:  # echo cancelation
                    continue

                s = s.strip().replace(' ', '')
                if len(s) == 0:  # empty string
                    continue

                if all(c in string.hexdigits for c in s):  # some data
                    if s[:1] == '3':  # FlowControl

                        # extract Burst Size
                        BS = s[2:4]
                        BS = int(BS, 16)

                        # extract Frame Interval
                        ST = s[4:6]
                        if ST[:1].upper() == 'F':
                            ST = int(ST[1:2], 16) * 100
                        else:
                            ST = int(ST, 16)
                        print('BS:', BS, 'ST:', ST)
                        break  # go to sending consequent frames
                    else:
                        responses.append(s)
                        continue

            # sending consequent frames according to FlowControl

            cf = min(BS - 1, (Fn - Fc) - 1)  # number of frames to send without response

            # disable responses
            if cf > 0:
                if self.ATR1:
                    self.send_raw('AT R0')
                    self.ATR1 = False

            while cf > 0:
                cf -= 1

                # Ensure time gap between frames according to FlowControl
                tc = time.time()  # current time
                if (tc - tb) * 1000. < ST:
                    time.sleep(ST / 1000. - (tc - tb))
                tb = tc

                self.send_raw(raw_command[Fc])
                Fc += 1

        # now we are going to receive data. st or ff should be in responses[0]
        if len(responses) != 1:
            return "WRONG RESPONSE MULTILINE CFC0"

        result = ""
        noerrors = True
        nbytes = 0  # number bytes in response

        if responses[0][:1] == '0':  # single frame (sf)
            nbytes = int(responses[0][1:2], 16)
            result = responses[0][2:2 + nbytes * 2]

        elif responses[0][:1] == '1':  # first frame (ff)
            nbytes = int(responses[0][1:4], 16)
            nframes = nbytes / 7 + 1
            cframe = 1
            result = responses[0][4:16]

            # receiving consecutive frames
            while len(responses) < nframes:
                # now we should send ff
                sBS = hex(min(int(nframes) - len(responses), 0xf))[2:]
                frsp = self.send_raw('300' + sBS + '00' + sBS)

                # analyse response
                for s in frsp.split('\n'):

                    if s.strip()[:len(raw_command[Fc - 1])] == raw_command[Fc - 1]:
                        # discard echo
                        continue

                    s = s.strip().replace(' ', '')
                    if len(s) == 0:
                        # empty string
                        continue

                    if all(c in string.hexdigits for c in s):  # some data
                        responses.append(s)
                        if s[:1] == '2':  # consecutive frames (cf)
                            tmp_fn = int(s[1:2], 16)
                            if tmp_fn != (cframe % 16):  # wrong response (frame lost)
                                self.error_frame += 1
                                noerrors = False
                                continue
                            cframe += 1
                            result += s[2:16]
                        continue

        else:  # wrong response (first frame omitted)
            self.error_frame += 1
            noerrors = False

        errorstr = "Unknown"
        # check for negative response (repeat the same as in cmd())
        if result[:2] == '7F':
            if result[6:8] in negrsp.keys():
                errorstr = negrsp[result[4:6]]
            noerrors = False

        if len(result) / 2 >= nbytes and noerrors:
            result = result[0:nbytes * 2]
            # split by bytes and return
            result = ' '.join(a + b for a, b in zip(result[::2], result[1::2]))
            return result
        else:
            return "WRONG RESPONSE CFC0 " + errorstr

    def send_raw(self, command, expect='>'):
        tb = time.time()  # start time

        # save command to log
        if self.lf != 0:
            # tm = str(time.time())
            tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.lf.write("> [" + tmstr + "] Request: " + command + "\n")
            self.lf.flush()

        # send command
        if not options.simulation_mode:
            self.port.write(str(command + "\r").encode("utf-8"))  # send command

        # receive and parse response
        while True:
            tc = time.time()
            if options.simulation_mode:
                break
            self.buff = self.port.expect(expect, self.portTimeout)
            if not self.port.connectionStatus:
                break
            tc = time.time()
            if (tc - tb) > self.portTimeout and "TIMEOUT" not in self.buff:
                self.buff += " TIMEOUT"
            if "TIMEOUT" in self.buff:
                self.error_timeout += 1
                break
            if command in self.buff:
                break
            elif self.lf != 0:
                tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self.lf.write("< [" + tmstr + "] Response: " + self.buff + "\n<shifted> Request: " + command + "\n")
                self.lf.flush()

        # count errors
        if "?" in self.buff:
            self.error_question += 1
        if "BUFFER FULL" in self.buff:
            self.error_bufferfull += 1
        if "NO DATA" in self.buff:
            self.error_nodata += 1
        if "RX ERROR" in self.buff:
            self.error_rx += 1
        if "CAN ERROR" in self.buff:
            self.error_can += 1

        self.response_time = ((self.response_time * 9) + (tc - tb)) / 10

        # save response to log
        if self.lf != 0:
            self.lf.write("< [" + str(round(tc - tb, 3)) + "] Response: " + self.buff + "\n")
            self.lf.flush()

        return self.buff

    def close_protocol(self):
        self.cmd("atpc")

    def start_session_can(self, start_session):
        self.startSession = start_session
        retcode = self.cmd(self.startSession)
        if retcode.startswith('50'):
            return True
        return False

    def init_can_sniffer(self, filter_addr, br):
        if options.simulation_mode:
            return

        # self.cmd('AT WS')
        self.cmd("AT E1")
        self.cmd("AT L0")
        self.cmd("AT H0")
        self.cmd("AT D0")
        if br == 250000:
            self.cmd("AT SP 8")
        else:
            self.cmd("AT SP 6")
        self.cmd("AT S0")
        self.cmd("AT AL")
        self.cmd("AT CAF0")
        if filter_addr:
            self.cmd("AT CRA " + filter_addr[-3:])

    def monitor_can_bus(self, callback):
        if options.simulation_mode:
            pass
        else:
            self.port.write("AT MA\r".encode('utf-8'))
            stream = ""
            while not self.monitorstop:
                byte = self.port.read()
                if byte == '\r' or byte == '<' or byte == '\n':
                    if stream == "AT MA" or stream == "DATA ERROR":
                        # Prefiltering echo and error reports (if any)
                        stream = ""
                        continue

                    # Ok to handle stream
                    callback(stream)
                    stream = ""
                elif byte == ">":
                    break
                if byte:
                    stream += byte

            self.port.write("AT\r".encode('utf-8'))
            self.port.expect('>')

    def init_can(self):
        self.currentprotocol = "can"
        self.currentaddress = ""
        self.startSession = ""
        self.lastCMDtime = 0
        self.l1_cache = {}

        if self.lf != 0:
            tmstr = datetime.now().strftime("%x %H:%M:%S.%f")[:-3]
            self.lf.write('#' * 60 + "\n# [" + tmstr + "] Init CAN\n" + '#' * 60 + "\n")
            self.lf.flush()
        # self.cmd("AT WS")
        self.cmd("AT E1")
        self.cmd("AT S0")
        self.cmd("AT H0")
        self.cmd("AT L0")
        self.cmd("AT AL")
        self.cmd("AT CAF0")
        if self.ATCFC0:
            self.cmd("AT CFC0")

        self.lastCMDtime = 0

    def set_can_addr(self, addr, ecu, canline=0):
        if self.currentprotocol == "can" and self.currentaddress == addr and self.canline == canline:
            return

        if canline == -1:
            canline = 0

        if self.lf != 0:
            self.lf.write('#' * 60 + "\n# Connect to: [" + clean_bytestring(
                ecu['ecuname']) + "] Addr: " + addr + "\n" + '#' * 60 + "\n")
            self.lf.flush()

        self.currentprotocol = "can"
        self.currentaddress = addr
        self.startSession = ""
        self.lastCMDtime = 0
        self.l1_cache = {}
        self.canline = canline

        if 'idTx' in ecu and 'idRx' in ecu:
            TXa = ecu['idTx']
            RXa = ecu['idRx']
            self.currentaddress = get_can_addr(TXa)
        elif get_can_addr(addr) is not None and get_can_addr_snat(addr) is not None:
            TXa = get_can_addr(addr)
            RXa = get_can_addr_snat(addr)
            self.currentaddress = TXa
        elif get_can_addr_ext(addr) is not None and get_can_addr_snat_ext(addr) is not None:
            TXa = get_can_addr_ext(addr)
            RXa = get_can_addr_snat_ext(addr)
            self.currentaddress = TXa
        else:
            return

        extended_can = False
        if len(RXa) == 8:
            # Extended (29bits) addressing
            extended_can = True

        if extended_can:
            self.cmd("AT CP " + TXa[:2])
            self.cmd("AT SH " + TXa[2:])
        else:
            self.cmd("AT SH " + TXa)

        self.cmd("AT CRA " + RXa)
        self.cmd("AT FC SH " + TXa)
        self.cmd("AT FC SD 30 00 00")  # status BS STmin
        self.cmd("AT FC SM 1")
        if canline == 0:
            # TODO: Find a better way to detect baud rate, some XML files are wrong
            if 0 and 'brp' in ecu.keys() and ecu['brp'] == "1":  # I suppose that brp=1 means 250kBps CAN
                if extended_can:
                    self.cmd("AT SP 9")
                else:
                    self.cmd("AT SP 8")
            else:
                if extended_can:
                    self.cmd("AT SP 7")
                else:
                    self.cmd("AT SP 6")
        elif canline == 1:
            if extended_can:
                self.cmd("AT SP 7")
            else:
                self.cmd("AT SP 6")
        elif canline == 2:
            if extended_can:
                self.cmd("AT SP 9")
            else:
                self.cmd("AT SP 8")
        else:
            self.cmd("STP 53")
            if canline == 3:
                self.cmd("STPBR 500000")
            elif canline == 4:
                self.cmd("STPBR 250000")
            elif canline == 5:
                self.cmd("STPBR 125000")

        if options.cantimeout > 0:
            self.set_can_timeout(options.cantimeout)

        return TXa, RXa

    def start_session_iso(self, start_session):
        self.startSession = start_session

        if len(self.startSession) > 0:
            self.lastinitrsp = self.cmd(self.startSession)
            if self.lastinitrsp.startswith('50'):
                return True
            return False

    def init_iso(self):
        self.currentprotocol = "iso"
        self.currentsubprotocol = ""
        self.currentaddress = ""
        self.startSession = ""
        self.lastCMDtime = 0
        self.lastinitrsp = ""

        if self.lf != 0:
            tmstr = datetime.now().strftime("%x %H:%M:%S.%f")[:-3]
            self.lf.write('#' * 60 + "\n# [" + tmstr + "] Init ISO\n" + '#' * 60 + "\n")
            self.lf.flush()
        # self.cmd("AT WS")
        self.cmd("AT E1")
        self.cmd("AT L0")
        self.cmd("AT D1")
        self.cmd("AT H0")  # headers off
        self.cmd("AT AL")  # Allow Long (>7 byte) messages
        self.cmd("AT KW0")

    def set_iso8_addr(self, addr, ecu):
        if self.currentprotocol == "iso" and self.currentaddress == addr and self.currentsubprotocol == ecu['protocol']:
            return

        if self.lf != 0:
            self.lf.write(
                '#' * 60 + "\n# Connect to: [" + clean_bytestring(ecu['ecuname']) + "] Addr: " + addr + " Protocol: " +
                ecu['protocol'] + "\n" + '#' * 60 + "\n")
            self.lf.flush()

        self.currentprotocol = "iso"
        self.currentsubprotocol = ecu['protocol']
        self.currentaddress = addr
        self.startSession = ""
        self.lastCMDtime = 0
        self.lastinitrsp = ""

        self.cmd("AT SH 81 " + addr + " F1")  # set address
        self.cmd("AT SW 96")  # wakeup message period 3 seconds
        self.cmd("AT WM 81 " + addr + " F1 3E")  # set wakeup message
        self.cmd("AT IB10")  # baud rate 10400
        self.cmd("AT ST FF")  # set timeout to 1 second
        self.cmd("AT SP 3")
        self.cmd("AT AT 0")  # enable adaptive timing
        self.cmd("AT SI")  # ISO8 needs slow init
        self.cmd("AT AT 1")

    def set_iso_addr(self, addr, ecu):
        if self.currentprotocol == "iso" and self.currentaddress == addr and self.currentsubprotocol == ecu['protocol']:
            return

        if self.lf != 0:
            self.lf.write(
                '#' * 60 + "\n# Connect to: [" + clean_bytestring(ecu['ecuname']) + "] Addr: " + addr + " Protocol: " +
                ecu['protocol'] + "\n" + '#' * 60 + "\n")
            self.lf.flush()

        self.currentprotocol = "iso"
        self.currentsubprotocol = ecu['protocol']
        self.currentaddress = addr
        self.startSession = ""
        self.lastCMDtime = 0
        self.lastinitrsp = ""

        self.cmd("AT SH 81 " + addr + " F1")  # set address
        self.cmd("AT SW 96")  # wakeup message period 3 seconds
        self.cmd("AT WM 81 " + addr + " F1 3E")  # set wakeup message
        self.cmd("AT IB10")  # baud rate 10400
        self.cmd("AT ST FF")  # set timeout to 1 second
        self.cmd("AT AT 0")  # disable adaptive timing

        if options.opt_si:
            self.cmd("AT SP 4")  # slow init mode 4
            self.cmd("AT IIA " + addr)  # address for slow init
            rsp = self.lastinitrsp = self.cmd("AT SI")  # for slow init mode 4

        if 'OK' not in self.lastinitrsp:
            self.cmd("AT SP 5")  # fast init mode 5
            self.lastinitrsp = self.cmd("AT FI")  # perform fast init mode 5

        if 'OK' not in self.lastinitrsp:
            return False

        self.cmd("AT AT 1")  # enable adaptive timing
        return True


def elm_checker(port, speed, adapter, logview, app):
    """Enhanced ELM327 checker with better error handling and device detection"""
    good = 0
    total = 0
    pycom = 0
    vers = ''

    try:
        # Check for saved settings first, use optimal settings as fallback
        device_key = DeviceManager.normalize_adapter_type(adapter)
        saved_settings = options.get_device_settings(device_key, port)

        if saved_settings and 'baudrate' in saved_settings:
            settings = saved_settings
            speed = settings.get('baudrate', speed)
            logview.append(_("Using saved device settings"))
        else:
            settings = DeviceManager.get_optimal_settings(adapter)
            speed = settings.get('baudrate', speed)
            logview.append(_("Using optimal device settings"))

        logview.append(_("Connecting to device at port: ") + str(port))
        logview.append(_("Using baudrate: ") + str(speed))

        # For ELS27 adapters, do a quick pre-test to verify device presence
        if adapter == "ELS27":
            logview.append(_("Testing for ELS27 device..."))
            app.processEvents()  # Update UI
            is_els27, response = is_els27_device(port, timeout=3)
            if is_els27:
                logview.append(_("ELS27 device detected: ") + response)
                # Extract baud rate from response if found
                if "at " in response and "baud" in response:
                    try:
                        baud_str = response.split("at ")[1].split(" baud")[0]
                        detected_baud = int(baud_str)
                        if detected_baud != speed:
                            logview.append(_("Using detected baud rate: ") + str(detected_baud))
                            speed = detected_baud
                    except:
                        pass
            else:
                logview.append(_("Warning: No ELS27 response detected"))
                logview.append(_("Will attempt connection anyway..."))

        options.elm = ELM(port, speed, adapter)

        if options.elm_failed:
            logview.append(_("Connection failed: ") + str(options.last_error))
            return False

        options.elm.portTimeout = 5

        # Test basic connectivity
        logview.append(_("Testing basic connectivity..."))
        test_response = options.elm.send_raw("ATZ")  # Reset command
        if not test_response or "ELM" not in test_response:
            logview.append(_("Warning: Device may not be ELM327 compatible"))
        else:
            logview.append(_("ELM327 device detected successfully"))

        # Get version information
        version_response = options.elm.send_raw("ATI")
        if version_response:
            vers = version_response.strip()
            logview.append(_("Device version: ") + vers)

    except Exception as e:
        logview.append(_("Connection error: ") + str(e))
        return False

    for st in cmdb.split('#'):
        cm = st.split(';')

        if len(cm) > 1:
            if 'C' not in cm[1].upper():
                continue

            if len(cm[2].strip()):

                res = options.elm.send_raw(cm[2])

                if 'H' in cm[1].upper():
                    continue
                total += 1
                print(cm[2] + " " + res.strip())
                if '?' in res:
                    chre = '<font color=red>[' + _('FAIL') + ']</font>'
                    if 'P' in cm[1].upper():
                        pycom += 1
                # Timeout is not an error
                elif 'TIMEOUT' in res:
                    chre = '<font color=green>[' + _('OK/TIMEOUT') + ']</font>'
                    good += 1
                    vers = cm[0]

                else:
                    chre = '<font color=green>[' + _('OK') + ']</font>'
                    good += 1
                    vers = cm[0]

                logview.append("%5s %10s %s" % (cm[0], cm[2], chre))
                app.processEvents()

    if pycom > 0:
        logview.append('<font color=red>' + _('Incompatible adapter on ARM core') + '</font> \n')
    logview.append(
        _('Result: ') + str(good) + _(' succeeded from ') + str(total) + '\n' + _('ELM Max version:') + vers + '\n')
    return True
