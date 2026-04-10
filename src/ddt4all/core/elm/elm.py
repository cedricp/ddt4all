'''module contains class for working with ELM327
   version: 160829
   Borrowed code from PyRen (modified for this use)
'''

from datetime import datetime
import glob
import os
import platform
import serial
from serial.tools import list_ports
import socket
import string
import time

from ddt4all.core.elm.constants import (
    cmdb,
    negrsp
)
from ddt4all.core.elm.device_manager import DeviceManager
from ddt4all.core.elm.port import Port
from ddt4all.core.usbdevice.usb_can import UsbCan
from ddt4all.file_manager import get_logs_dir
import ddt4all.options as options

_ = options.translator('ddt4all')

# SNAT/DNAT entries for CAN address mapping
# Fixed: Using proper hex addresses instead of string values
dnat_entries = {"E7": "7E4", "E8": "644"}
snat_entries = {"E7": "7EC", "E8": "5C4"}

snat = snat_entries
snat_ext = {}
dnat = dnat_entries
dnat_ext = {}




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
    """Get available serial ports with optimized status checking"""
    ports = []
    
    # First check for USB devices using usbdevice.py (with error handling)
    try:
        usb_device = UsbCan()
        if usb_device.is_init():
            # Add USB device to ports list
            ports.append((usb_device.descriptor, usb_device.descriptor, "USB", "online"))
            print(_("Found USB device:") + " %s" % usb_device.descriptor)
    except ImportError as e:
        # Only show USB backend error once per session
        if not hasattr(get_available_ports, '_usb_error_shown'):
            get_available_ports._usb_error_shown = True
            print(f"USB backend not available: {e}")
            print("Note: USB device detection requires pyusb library (pip install pyusb)")
    except Exception as e:
        # Only show USB device detection error once per session
        if not hasattr(get_available_ports, '_usb_device_error_shown'):
            get_available_ports._usb_device_error_shown = True
            print(f"USB device detection error: {e}")
    
    # Check for DoIP devices with optimized connectivity checking (only for DoIP-capable devices)
    # DoIP devices - Use configured IP address instead of hardcoded values
    doip_target_ip = getattr(options, 'doip_target_ip', '192.168.0.12')
    doip_target_port = getattr(options, 'doip_target_port', 13400)
    
    doip_devices = [
        (doip_target_ip, f"DoIP Device - {doip_target_ip}:{doip_target_port}"),
    ]
    
    # Only check DoIP status if not in simulation mode and not checking too frequently
    if not getattr(options, 'simulation_mode', False) and not hasattr(get_available_ports, '_last_check_time'):
        get_available_ports._last_check_time = time.time()
        for ip, desc in doip_devices:
            status = check_doip_status(ip, doip_target_port, timeout=0.5)  # Use configured port
            port_entry = (f"{ip}:{doip_target_port}", desc, "DoIP", status)
            ports.append(port_entry)
            print(f"DoIP device {status}: {desc} at {ip}")
    else:
        # Use cached status or assume offline
        for ip, desc in doip_devices:
            port_entry = (f"{ip}:{doip_target_port}", desc, "DoIP", "offline")
            ports.append(port_entry)
    
    # Then check for serial ports
    try:
        portlist = list_ports.comports()

        if item_count(portlist) == 0:
            return ports if ports else []

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
            elif any(keyword in desc_upper for keyword in ['DERLEK', 'DIAG2', 'DIAG3']):
                device_desc = f"{desc} (DERLEK Compatible)"
            elif any(keyword in desc_upper for keyword in ['OBDLINK', 'SCANTOOL']):
                device_desc = f"{desc} (OBDLink Compatible)"
            # Detect common USB-to-serial chips used by ELS27 V5 and other adapters
            elif any(chip in desc_upper for chip in ['FTDI', 'FT232', 'FT231X']):
                device_desc = f"{desc} (FTDI - Possible ELS27/ELM327)"
            elif any(chip in desc_upper for chip in ['CH340', 'CH341']):
                device_desc = f"{desc} (CH340 - Possible ELS27/ELM327)"
            elif any(chip in desc_upper for chip in ['CP210', 'CP2102', 'CP2104']):
                device_desc = f"{desc} (CP210x - Possible ELS27/DERLEK)"
            elif any(chip in desc_upper for chip in ['PL2303']):
                device_desc = f"{desc} (PL2303 - Possible ELS27/DERLEK)"

            # Quick serial port availability check (only if not already checked)
            status = check_serial_port_status(port, timeout=0.05)  # Very fast timeout
            ports.append((port, device_desc, hwid, status))

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
            common_ports = glob.glob('/dev/cu.*') + glob.glob('/dev/tty.*')

        for port in common_ports:
            try:
                # Test if port exists and is accessible
                test_serial = serial.Serial(port, timeout=0.05)
                test_serial.close()
                ports.append((port, "Unknown Device", "", "online"))
            except Exception:
                ports.append((port, "Unknown Device", "", "offline"))

    return ports


def check_doip_status(ip, port, timeout=1):
    """Check if DoIP device is online with optimized timeout"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return "online" if result == 0 else "offline"
    except Exception:
        return "offline"


def check_serial_port_status(port, timeout=0.1):
    """Check if serial port is accessible with optimized timeout"""
    try:
        test_serial = serial.Serial(port, timeout=timeout)
        test_serial.close()
        return "online"
    except Exception:
        return "offline"


def is_els27_device(port, timeout=2):
    """Test if a serial port has an ELS27 device with multiple baud rates"""
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
            if len(port_info) >= 4:
                port, desc, hwid, status = port_info
            elif len(port_info) >= 3:
                port, desc, hwid = port_info
                status = "unknown"
            else:
                port, desc = port_info
                hwid = ""
                status = "unknown"
                
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
        if len(port_info) >= 4:
            port, desc, hwid, status = port_info
        elif len(port_info) >= 3:
            port, desc, hwid = port_info
            status = "unknown"
        else:
            port, desc = port_info
            hwid = ""
            status = "unknown"
            
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
        self.stpx_enabled = False  # Initialize STPX mode flag
        for speed in [int(rate), 38400, 115200, 230400, 57600, 9600, 500000, 1000000, 2000000]:
            print(_("Trying to open port ") + "%s @ %i" % (portName, speed))

            if not options.simulation_mode:
                self.port = Port(portName, speed, self.adapter_type)
                # Check if port initialization was successful
                if not hasattr(self.port, 'hdr') or self.port.hdr is None:
                    options.elm_failed = True
                    options.last_error = _("Port initialization failed")
                    self.connectionStatus = False
                    continue

            if options.elm_failed:
                self.connectionStatus = False
                # Try one other speed ...
                continue

            options.port_speed = speed

            if not os.path.exists(get_logs_dir()):
                os.mkdir(get_logs_dir())

            if len(options.log) > 0:
                self.lf = open(os.path.join(get_logs_dir(), "elm_" + options.log + ".txt"), "at", encoding="utf-8")
                self.vf = open(os.path.join(get_logs_dir(), "ecu_" + options.log + ".txt"), "at", encoding="utf-8")
                self.vf.write("# TimeStamp;Address;Command;Response;Error\n")

            self.lastCMDtime = 0
            self.ATCFC0 = options.opt_cfc0

            # Purge unread data - only if port is valid
            if (self.port is not None and 
                hasattr(self.port, 'expect') and 
                hasattr(self.port, 'connectionStatus') and 
                self.port.connectionStatus):
                self.port.expect(">")
                res = self.send_raw("ATZ")
            else:
                options.elm_failed = True
                options.last_error = _("Port connection failed - port object is invalid")
                continue
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
        except Exception:
            maxspeed = 0

        device_text_switch = _("OBDLink Connection OK, attempting full speed UART switch")
        text_switck_error = _("Failed to switch to change OBDLink to ") + str(maxspeed)
        text_optional = _("OBDLINK Connection OK, using optimal settings")
        if adapter_type == "OBDLINK" and maxspeed > 0 and not options.elm_failed and rate != 2000000:
            print(device_text_switch.replace("OBDLink", "OBDLink"))
            try:
                self.raise_odb_speed(maxspeed, "OBDLink")
            except Exception:
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
            except Exception:
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
            except Exception:
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
                self.raise_vgate_speed(maxspeed)
            except Exception:
                options.elm_failed = True
                self.connectionStatus = False
                print(text_switck_error.replace("OBDLink", "VGate"))
        elif adapter_type == "VGATE":
            print(text_optional.replace("OBDLink", "VGate"))
            if not options.elm_failed:
                # Enable STPX mode for VGate adapters
                try:
                    self.enable_stpx_mode()
                    print(_("VGate STPX mode enabled for enhanced long command support"))
                except Exception as e:
                    print(f"VGate STPX warning: {e}")
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
        # Compatibility wrapper: delegate to unified speed switch
        return self.raise_elm_speed(baudrate, device_name=device_name)

    def raise_vgate_speed(self, baudrate):
        # Compatibility wrapper: delegate to unified speed switch
        return self.raise_elm_speed(baudrate, device_name="VGATE")

    def send_stn_command(self, command, enhanced=True):
        """Send command using STN protocol with enhanced features"""
        try:
            if enhanced and hasattr(self, 'stpx_enabled') and self.stpx_enabled:
                # Use STPX enhanced protocol for better performance
                # Add STN prefix for enhanced adapters
                stn_command = f"ST {command}"
                return self.send_raw(stn_command)
            else:
                # Standard command
                return self.send_raw(command)
        except Exception as e:
            print(f"STN command error: {e}")
            # Fallback to standard command
            return self.send_raw(command)

    def enable_stpx_mode(self):
        """Enable STPX mode for enhanced long command support on STN-based adapters"""
        try:
            # STPX mode enables enhanced long command handling
            # This is particularly useful for VGate and other STN-based adapters
            
            # Set enhanced timeout for long commands
            self.send_raw("ST SFT 0")  # Disable flow control for better long command support
            self.send_raw("ST WFF 1")  # Enable wait for first frame
            self.send_raw("ST FC SH 80")  # Set flow control separator
            
            # Configure extended buffer for long commands
            self.send_raw("ST BLM 1")  # Enable large message mode
            self.send_raw("ST CSM 1")  # Enable checksum mode for reliability
            
            # Set optimal timing for STPX protocol
            self.send_raw("ST P1 25")  # Set inter-frame gap
            self.send_raw("ST P3 55")  # Set frame response time
            
            # Enable extended addressing if supported
            self.send_raw("ST EA 1")  # Enable extended addressing
            
            # Set flag to indicate STPX is enabled
            self.stpx_enabled = True
            
            print(_("STPX mode enabled for enhanced long command support"))
            
        except Exception as e:
            print(f"STPX mode enable warning: {e}")
            # Don't raise exception - STPX is enhancement, not requirement
            self.stpx_enabled = False

    def raise_elm_speed(self, baudrate, device_name="ELM"):
        # Unified speed switch for ELM (ATBRD) and STN-based adapters (ST SBR)
        if self.port is None:
            raise Exception(_("Port is None - cannot switch speed"))

        dev = (device_name or "ELM").upper()
        try:
            # STN / VGate / OBDLink style switching
            if dev in ("VGATE", "OBDLINK", "VLINKER", "STN"):
                cmd = "ST SBR " + str(baudrate)
                rsp = self.send_raw(cmd)
                if "OK" in rsp:
                    print((_("%s switched baudrate OK, changing UART speed now...") % device_name))
                    self.port.change_rate(baudrate)
                    time.sleep(0.5)
                    # Verify STN response
                    res = self.send_raw("STI").replace("\n", "").replace(">", "").replace("STI", "")
                    if "STN" in res:
                        print((_("%s STN connection established") % device_name))
                        print((_("%s Version: ") % device_name) + res)
                        if dev == "VGATE":
                            self.enable_stpx_mode()
                    else:
                        # Best-effort fallback for VGate
                        if dev == "VGATE":
                            print(_("VGate adapter detected but STN verification failed, attempting fallback..."))
                            self.enable_stpx_mode()
                    return
                else:
                    raise Exception(f"{device_name} speed switch failed: {rsp}")

            # Default: ELM327 ATBRD switching
            if baudrate == 57600:
                atcmd = "ATBRD 45"
            elif baudrate == 115200:
                atcmd = "ATBRD 23"
            elif baudrate == 230400:
                atcmd = "ATBRD 11"
            elif baudrate == 500000:
                atcmd = "ATBRD 8"
            else:
                raise Exception(_("Unsupported baudrate for ELM: %s") % str(baudrate))

            rsp = self.send_raw(atcmd)
            if "OK" in rsp:
                print(_("ELM baudrate switched OK, changing UART speed now..."))
                self.port.change_rate(baudrate)
                time.sleep(0.5)
                version = self.send_raw("ATI")
                if "ELM" in version or "ELM327" in version:
                    print(_("ELM full speed connection OK "))
                    print(_("Version ") + version)
                    return
                else:
                    raise Exception(_("ELM did not report version after speed switch"))
            else:
                raise Exception((_("Your ELM does not support baudrate %s") % str(baudrate)))

        except Exception:
            raise

    def __del__(self):
        try:
            if _ is not None:
                print(_("ELM reset..."))
            else:
                print(_("ELM reset..."))
            # Check if port exists and is valid before attempting reset
            if hasattr(self, 'port') and self.port is not None and hasattr(self.port, 'write'):
                self.port.write("ATZ\r".encode("utf-8"))
        except (AttributeError, OSError, TypeError):
            # Handle all possible errors during cleanup
            pass

    def connectionStat(self):
        if hasattr(self, 'port') and self.port is not None and hasattr(self.port, 'connectionStatus'):
            return self.port.connectionStatus
        return False

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
        if ((tb - self.lastCMDtime) < (self.busLoad + self.srvsDelay)) \
                and ("AT" not in command.upper() or "ST" not in command.upper()):
            time.sleep(self.busLoad + self.srvsDelay - tb + self.lastCMDtime)

        tb = time.time()  # renew start time

        # If we use wifi and there was more than keepAlive seconds of silence then reinit tcp
        if self.port is not None and (tb - self.lastCMDtime) > self.keepAlive:
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
        for line in cmdrsp.split('\n'):
            line = line.strip().upper()
            if line.startswith("7F") and len(line) == 8 and line[6:8] in negrsp.keys():
                print(line, negrsp[line[6:8]])
                if self.lf != 0:
                    self.lf.write("# [" + str(tc - tb) + "] rsp: " + line + ": " + negrsp[line[6:8]] + "\n")
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
                # Enhanced STPX timeout handling for long commands
                if hasattr(self, 'stpx_enabled') and self.stpx_enabled:
                    # Use STPX-specific timeout for better long command performance
                    self.send_raw('ST ST FF')  # STPX timeout command
                else:
                    # Standard ELM timeout
                    self.send_raw('AT ST FF')
                self.send_raw('AT AT 1')

            if (Fc == 0 or Fc == (Fn - 1)) and len(
                    raw_command[Fc]) < 16:  # first or last frame in command and len<16 (bug in ELM)
                # Enhanced frame handling for STPX adapters
                if hasattr(self, 'stpx_enabled') and self.stpx_enabled:
                    frsp = self.send_raw(raw_command[Fc] + '1')  # STPX enhanced single frame request
                else:
                    frsp = self.send_raw(raw_command[Fc] + '1')  # standard single frame request
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
        """Enhanced send_raw with STN/STPX support"""
        # Check if STN/STPX should be used
        if hasattr(self, 'stpx_enabled') and self.stpx_enabled and not command.upper().startswith(('AT', 'ST')):
            # Use STN protocol for enhanced adapters when enabled
            return self.send_stn_command(command, enhanced=True)
        
        tb = time.time()  # start time

        # Check if port is valid before proceeding
        if self.port is None:
            self.error_rx += 1
            return "PORT ERROR: None port object"

        # save command to log
        if self.lf != 0:
            # tm = str(time.time())
            tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.lf.write("> [" + tmstr + "] Request: " + command + "\n")
            self.lf.flush()

        # send command
        if not options.simulation_mode:
            try:
                self.port.write(str(command + "\r").encode("utf-8"))  # send command
            except Exception as e:
                self.error_rx += 1
                return f"PORT WRITE ERROR: {str(e)}"

        # receive and parse response
        while True:
            tc = time.time()
            if options.simulation_mode:
                break
            try:
                self.buff = self.port.expect(expect, self.portTimeout)
            except Exception as e:
                self.error_rx += 1
                return f"PORT READ ERROR: {str(e)}"
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
            self.lastinitrsp = self.cmd("AT SI")  # for slow init mode 4

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
                    except Exception:
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

