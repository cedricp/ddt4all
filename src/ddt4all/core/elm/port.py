import platform
import re
import serial
import select
import socket
import sys
import threading
import time

from ddt4all.core.elm.device_manager import DeviceManager
import ddt4all.options as options

_ = options.translator('ddt4all')

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
    settings = {}

    def __init__(self, portName, speed, adapter_type):
        options.elm_failed = False
        self.adapter_type = adapter_type
        self._lock = threading.Lock()
        self.reconnect_attempts = 0

        portName = portName.strip()

        # WiFi/TCP connection (e.g., 192.168.0.10:35000)
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$", portName):

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
                self.settings = saved_settings
                translate_arg = _("Using saved settings for")
                print (f"{translate_arg} {self.adapter_type}: {self.settings}")
            else:
                self.settings = DeviceManager.get_optimal_settings(self.adapter_type)
                translate_arg = _("Using optimal settings for")
                print(f"{translate_arg} {self.adapter_type}: {self.settings}")

            # Use provided speed if specified, otherwise use setting
            if speed > 0:
                self.settings['baudrate'] = speed

            # Check if this is a DoIP connection (only for non-ELM327 devices)
            if ":" in self.portName and self.portName.count(":") == 1:
                ip, port = self.portName.split(":")
                try:
                    port_num = int(port)
                    if port_num == 13400:  # DoIP port
                        # ELM327 doesn't support DoIP, only modern adapters
                        if self.adapter_type.upper() not in ['ELM327', 'STD_USB', 'STD_BT', 'STD_WIFI']:
                            self.init_doip(ip, port_num)
                            return
                        else:
                            print("ELM327 doesn't support DoIP, falling back to serial mode")
                except ValueError:
                    pass  # Not a valid port number, continue with serial

            # Platform-specific serial port configuration
            current_platform = platform.system().lower()

            # Enhanced serial parameters using device-specific settings
            serial_params = {
                'port': self.portName,
                'baudrate': self.settings.get('baudrate', speed),
                'timeout': self.settings.get('timeout', 5),
                'parity': serial.PARITY_NONE,
                'stopbits': serial.STOPBITS_ONE,
                'bytesize': serial.EIGHTBITS,
                'xonxoff': False,
                'rtscts': self.settings.get('rtscts', False),
                'dsrdtr': self.settings.get('dsrdtr', False)
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
            self.connectionStatus = True
            print(f"Serial connection established: {self.portName} @ {self.settings['baudrate']} baud")

        except Exception as e:
            print(f"Bluetooth connection failed: {e}")
            options.elm_failed = True
            self.connectionStatus = False

    def init_doip(self, ip, port):
        """Initialize DoIP connection"""
        try:
            print(f"Initializing DoIP connection to {ip}:{port}")
            self.doip_device = doip.DoIPDevice(ip)
            
            if self.doip_device.connect():
                self.connectionStatus = True
                self.portType = 3  # DoIP connection type
                print(f"DoIP connection established: {ip}:{port}")
            else:
                print(f"DoIP connection failed: {ip}:{port}")
                self.connectionStatus = False
                
        except Exception as e:
            print(f"DoIP initialization failed: {e}")
            self.connectionStatus = False
            options.elm_failed = True

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
                    try:
                        byte = self.hdr.recv(1)
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
                print(_("Serial error in read_byte: %s") % e)
                self.connectionStatus = False
                return None
            except Exception as e:
                print('*' * 40)
                print('*       ' + _('Connection to ELM was lost'))
                print(_('*       Error: %s') % e)
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
                    except Exception:
                        continue
                print(_("Cannot decode bytes %s") % str(byte))
                return ""
        except Exception as e:
            print(_("Error in read(): %s") % e)
            return None

    def change_rate(self, rate):
        if self.portType == 0:  # Serial/USB only
            self.hdr.baudrate = rate
        elif self.portType == 1:  # TCP/WiFi - no baudrate concept
            print("WiFi connection - baudrate change not applicable")
        else:  # Bluetooth
            if self.hdr and hasattr(self.hdr, 'baudrate'):
                self.hdr.baudrate = rate

    def write(self, data):
        """Enhanced write method with automatic reconnection and better error handling"""
        with self._lock:
            try:
                if not isinstance(data, bytes):
                    data = data.encode('utf-8')

                if self.portType == 1:  # TCP/WiFi
                    if self.tcp_needs_reconnect:
                        print(_("Attempting WiFi reconnection..."))
                        self.tcp_needs_reconnect = False
                        self.init_wifi(True)
                        if not self.connectionStatus:
                            return None
                    if self.hdr is None:
                        print(_("Port handler is None, cannot write"))
                        return None
                    return self.hdr.sendall(data)
                elif self.portType == 2:  # Bluetooth
                    if self.droid:
                        return self.droid.bluetoothWrite(data)
                    else:
                        # Fallback to serial write for Bluetooth-serial adapters
                        if self.hdr is None:
                            print(_("Port handler is None, cannot write"))
                            return None
                        return self.hdr.write(data)
                else:  # Serial/USB
                    if self.hdr is None:
                        print(_("Port handler is None, cannot write"))
                        return None
                    return self.hdr.write(data)

            except serial.SerialException as e:
                print(_("Serial write error: %s") % e)
                self.connectionStatus = False
                return None
            except Exception as e:
                print('*' * 40)
                print('*       ' + _('Connection to ELM was lost'))
                print(_('*       Write error: %s') % e)
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
        tb = time.time()
        self.buff = ""
        deadline = tb + time_out
    
        while True:
            if not options.simulation_mode:
                if self.portType == 1 and self.hdr is not None:
                    remaining = deadline - time.time()
                    if remaining <= 0:
                        return self.buff + _("TIMEOUT")
                    rlist, _, _ = select.select([self.hdr], [], [], min(0.05, remaining))
                    if not rlist:
                        continue
                byte = self.read()
            else:
                byte = '>'
    
            if byte == '\r':
                byte = '\n'
    
            if byte:
                self.buff += byte
    
            if pattern in self.buff:
                return self.buff
    
            if time.time() > deadline:
                return self.buff + _("TIMEOUT")
    def check_elm(self):

        timeout = 2

        for s in [38400, 115200, 230400, 57600, 9600, 500000]:
            print("\r\t\t\t\t\r" + _("Checking port speed:"), s, )
            sys.stdout.flush()

            if self.portType == 0:  # Serial/USB only
                self.hdr.baudrate = s
            elif self.portType == 1:  # TCP/WiFi - no baudrate concept
                print("WiFi connection - skipping baudrate check")
                break
            else:  # Bluetooth
                if self.hdr and hasattr(self.hdr, 'baudrate'):
                    self.hdr.baudrate = s
                else:
                    print("Bluetooth connection - skipping baudrate check")
                    break
            
            # self.hdr.flushInput()
            if self.portType == 0:  # Serial/USB only
                self.hdr.reset_input_buffer()
            elif self.portType == 1:  # TCP/WiFi - no buffer reset needed
                pass  # Sockets don't need buffer reset
            else:  # Bluetooth
                if self.hdr and hasattr(self.hdr, 'reset_input_buffer'):
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
                    if self.portType == 0:  # Serial/USB only
                        self.hdr.timeout = timeout
                    elif self.portType == 1:  # TCP/WiFi
                        self.hdr.settimeout(timeout)
                    else:  # Bluetooth
                        if self.hdr and hasattr(self.hdr, 'timeout'):
                            self.hdr.timeout = timeout
                    return True
                if (tc - tb) > 1:
                    break
        print("\n" + _("ELM not responding"))
        return False
