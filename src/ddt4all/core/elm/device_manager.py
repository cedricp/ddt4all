from ... import options

_ = options.translator('ddt4all')

class DeviceManager:
    """Enhanced device manager for OBD-II adapters with optimal settings and STN/STPX support"""

    @staticmethod
    def get_optimal_settings(device_type):
        """Get optimal connection settings for specific device types"""
        settings = {
            'vlinker': {
                'baudrate': 38400, 'timeout': 3, 'rtscts': False, 'dsrdtr': False,
                'stn_support': False, 'stpx_support': False, 'pin_swap': False
            },
            'elm327': {
                'baudrate': 38400, 'timeout': 5, 'rtscts': False, 'dsrdtr': False,
                'stn_support': False, 'stpx_support': False, 'pin_swap': False
            },
            'obdlink': {
                'baudrate': 115200, 'timeout': 2, 'rtscts': True, 'dsrdtr': False,
                'stn_support': True, 'stpx_support': True, 'pin_swap': True
            },
            'obdlink_ex': {
                'baudrate': 115200, 'timeout': 2, 'rtscts': True, 'dsrdtr': False,
                'stn_support': True, 'stpx_support': True, 'pin_swap': True
            },
            'els27': {
                'baudrate': 38400, 'timeout': 4, 'rtscts': False, 'dsrdtr': False, 'can_pins': '12-13',
                'stn_support': False, 'stpx_support': False, 'pin_swap': True
            },
            'vgate': {
                'baudrate': 115200, 'timeout': 2, 'rtscts': False, 'dsrdtr': False,
                'stn_support': True, 'stpx_support': True, 'pin_swap': True
            },
            'derlek_usb_diag2': {
                'baudrate': 38400, 'timeout': 4, 'rtscts': False, 'dsrdtr': False,
                'stn_support': False, 'stpx_support': False, 'pin_swap': True
            },
            'derlek_usb_diag3': {
                'baudrate': 38400, 'timeout': 4, 'rtscts': False, 'dsrdtr': False,
                'stn_support': False, 'stpx_support': False, 'pin_swap': True
            },
            'unknown': {
                'baudrate': 38400, 'timeout': 5, 'rtscts': False, 'dsrdtr': False,
                'stn_support': False, 'stpx_support': False, 'pin_swap': False
            },
            'usbcan': {
                'baudrate': 500000, 'timeout': 2, 'rtscts': False, 'dsrdtr': False,
                'stn_support': False, 'stpx_support': False, 'pin_swap': True
            }
        }
        return settings.get(DeviceManager.normalize_adapter_type(device_type), settings['unknown'])

    @staticmethod
    def normalize_adapter_type(adapter_type):
        """Normalize UI adapter types to internal device types"""
        adapter_mapping = {
            'STD_BT': 'elm327',  # Bluetooth ELM327
            'STD_WIFI': 'elm327',  # WiFi ELM327
            'STD_USB': 'elm327',  # USB ELM327
            'OBDLINK': 'obdlink',  # OBDLink devices
            'OBDLINK_EX': 'obdlink_ex',  # OBDLink EX devices
            'ELS27': 'els27',  # ELS27 devices
            'VLINKER': 'vlinker',  # Vlinker devices
            'VGATE': 'vgate',  # VGate devices
            'DERLEK': 'derlek_usb_diag2',  # DerleK USB-DIAG2 devices (default to DIAG2)
            'DERLEK_USB_DIAG2': 'derlek_usb_diag2',  # DerleK USB-DIAG2 devices
            'DERLEK_USB_DIAG3': 'derlek_usb_diag3',  # DerleK USB-DIAG3 devices
            'USBCAN': 'usbcan'  # USB CAN adapters - use usbdevice.py
        }
        return adapter_mapping.get(adapter_type.upper(), 'elm327')

    @staticmethod
    def detect_device_type(elm_instance):
        """Auto-detect device type from ELM responses"""
        try:
            if not elm_instance or not hasattr(elm_instance, 'cmd'):
                return 'unknown'
            
            # Get device identification
            elm_version = elm_instance.cmd("ATI")
            if not elm_version:
                return 'unknown'
            
            elm_version = elm_version.upper()
            
            # Check for specific device signatures
            if "VGATE" in elm_version or "ICAR" in elm_version:
                return 'vgate'
            elif "OBDLINK" in elm_version or "STN" in elm_version:
                return 'obdlink'
            elif "DERLEK USB-DIAG2" in elm_version or "DERLEK USB-DIAG3" in elm_version:
                if "DIAG2" in elm_version:
                    return 'derlek_usb_diag2'
                elif "DIAG3" in elm_version:
                    return 'derlek_usb_diag3'
                else:
                    return 'derlek_usb_diag2'  # Default to DIAG2
            elif "ELS27" in elm_version:
                return 'els27'
            elif "VLINKER" in elm_version:
                return 'vlinker'
            elif "ELM327" in elm_version:
                return 'elm327'
            else:
                return 'unknown'
                
        except Exception as e:
            print(_("Device detection error: %s") % e)
            return 'unknown'

    @staticmethod
    def initialize_device(elm_instance, device_type=None):
        """Complete device initialization with enhanced features"""
        try:
            if not elm_instance:
                return False
            
            # Auto-detect device type if not provided
            if not device_type:
                device_type = DeviceManager.detect_device_type(elm_instance)
            
            # Get optimal settings
            settings = DeviceManager.get_optimal_settings(device_type)
            
            return True
            
        except Exception as e:
            print(_("Device initialization error: %s") % e)
            return False
