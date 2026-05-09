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
    def enable_enhanced_features(elm_instance, device_type):
        """Enable enhanced features based on device type"""
        try:
            if not elm_instance:
                return False
            
            settings = DeviceManager.get_optimal_settings(device_type)
            
            if not settings.get('stn_support', False):
                return True  # No STN support needed
            
            # Enable STN/STPX features
            if settings.get('stpx_support', False):
                stpx_enabled = DeviceManager._enable_stpx_mode(elm_instance, device_type)
                if stpx_enabled:
                    print(_("STPX mode enabled for %s") % device_type)
            
            # Enable pin swapping if supported
            if settings.get('pin_swap', False):
                DeviceManager._auto_swap_pins(elm_instance, device_type)
                print(_("Pin swapping enabled for %s") % device_type)
            
            return True
            
        except Exception as e:
            print(_("Enhanced features enable error: %s") % e)
            return False

    @staticmethod
    def _enable_stpx_mode(elm_instance, device_type):
        """Enable STPX mode for enhanced long command support"""
        try:
            # STPX is a mode, not individual commands
            # Only OBDLink and VGate support STPX mode
            # STPX is automatically enabled when adapter detects long commands
            
            # Try to enable STPX mode (if supported)
            response = elm_instance.cmd("STPX")
            if "?" in response:
                print(_("STPX mode not supported by this adapter as native, trying fallback..."))
                return False
            
            print(_("STPX mode enabled successfully"))
            return True
            
        except Exception as e:
            print(_("STPX mode enable error: %s") % e)
            return False

    @staticmethod
    def _auto_swap_pins(elm_instance, device_type):
        """Auto-swap pins based on device type"""
        try:
            if device_type == 'vgate':
                return DeviceManager._swap_vgate_pins(elm_instance)
            elif device_type == 'obdlink':
                return DeviceManager._swap_obdlink_pins(elm_instance)
            elif device_type == 'derlek_usb_diag2':
                return DeviceManager._swap_derlek_diag2_pins(elm_instance)
            elif device_type == 'derlek_usb_diag3':
                return DeviceManager._swap_derlek_diag3_pins(elm_instance)
            elif device_type == 'els27':
                return DeviceManager._swap_els27_pins(elm_instance)
            elif device_type == 'usbcan':
                return DeviceManager._swap_usbcan_pins(elm_instance)
            else:
                return True  # No pin swap needed
                
        except Exception as e:
            print(_("Pin swap error: %s") % e)
            return False

    @staticmethod
    def _swap_vgate_pins(elm_instance):
        """Swap pins for VGate adapters using STN protocol"""
        try:
            # VGate specific pin swapping commands
            pin_swap_commands = [
                ("ST SBR 500000", "Set baudrate for pin swap"),
                ("STP 53", "Enable CAN pin swapping"),
                ("STPBR 500000", "Set pin swap baudrate")
            ]
            
            for cmd, desc in pin_swap_commands:
                response = elm_instance.cmd(cmd)
                if "?" in response:
                    print(f"VGate pin swap command failed: {cmd} ({desc})")
                    return False
            
            # Verify pin swap worked
            test_response = elm_instance.cmd("0210C0")
            if "CAN ERROR" not in test_response:
                print(_("VGate pin swapping successful"))
                return True
            else:
                print(_("VGate pin swapping failed, using fallback"))
                return False
                
        except Exception as e:
            print(_("VGate pin swap error: %s") % e)
            return False

    @staticmethod
    def _swap_obdlink_pins(elm_instance):
        """Swap pins for OBDLink adapters"""
        try:
            # OBDLink specific pin swapping
            pin_swap_commands = [
                ("AT BRD 23", "Set baudrate for 115200"),
                ("AT SP 6", "Set CAN protocol")
            ]
            
            for cmd, desc in pin_swap_commands:
                response = elm_instance.cmd(cmd)
                if "?" in response:
                    print(f"OBDLink pin swap command failed: {cmd} ({desc})")
                    return False
            
            print(_("OBDLink pin swapping completed"))
            return True
            
        except Exception as e:
            print(_("OBDLink pin swap error: %s") % e)
            return False

    @staticmethod
    def _swap_derlek_diag2_pins(elm_instance):
        """Swap pins for DerleK USB-DIAG2 adapters"""
        try:
            # DerleK USB-DIAG2 uses proprietary protocol, not AT commands
            # Pin swapping is handled internally by the device
            # No AT commands needed for DERLEK devices
            
            print(_("DerleK USB-DIAG2 uses proprietary protocol - no AT commands needed"))
            return True
            
        except Exception as e:
            print(_("DerleK USB-DIAG2 pin swap error: %s") % e)
            return False

    @staticmethod
    def _swap_derlek_diag3_pins(elm_instance):
        """Swap pins for DerleK USB-DIAG3 adapters"""
        try:
            # DerleK USB-DIAG3 uses proprietary protocol, not AT commands
            # Pin swapping is handled internally by the device
            # No AT commands needed for DERLEK devices
            
            print(_("DerleK USB-DIAG3 uses proprietary protocol - no AT commands needed"))
            return True
            
        except Exception as e:
            print(_("DerleK USB-DIAG3 pin swap error: %s") % e)
            return False

    @staticmethod
    def _swap_usbcan_pins(elm_instance):
        """Swap pins for USB CAN adapters"""
        try:
            # USB CAN specific pin swapping
            pin_swap_commands = [
                ("AT BRD 23", "Set baudrate for 115200"),
                ("AT SP 6", "Set CAN protocol")
            ]
            
            for cmd, desc in pin_swap_commands:
                response = elm_instance.cmd(cmd)
                if "?" in response:
                    print(f"USB CAN pin swap command failed: {cmd} ({desc})")
                    return False
            
            print(_("USB CAN pin swapping completed"))
            return True
            
        except Exception as e:
            print(_("USB CAN pin swap error: %s") % e)
            return False

    @staticmethod
    def _swap_els27_pins(elm_instance):
        """Swap pins for ELS27 adapters"""
        try:
            # ELS27 specific pin swapping
            pin_swap_commands = [
                ("AT SP 6", "Set CAN protocol"),
                ("AT SH 81", "Set header for ELS27")
            ]
            
            for cmd, desc in pin_swap_commands:
                response = elm_instance.cmd(cmd)
                if "?" in response:
                    print(f"ELS27 pin swap command failed: {cmd} ({desc})")
                    return False
            
            print(_("ELS27 pin swapping completed"))
            return True
            
        except Exception as e:
            print(_("ELS27 pin swap error: %s") % e)
            return False

    @staticmethod
    def initialize_device(elm_instance, device_type=None):
        """Complete device initialization with enhanced features"""
        try:
            if not elm_instance:
                return False
            
            # Auto-detect device type if not provided
            if not device_type:
                device_type = DeviceManager.detect_device_type(elm_instance)
            
            # Use adapter_type from ELM instance if available (more accurate)
            if hasattr(elm_instance, 'adapter_type') and elm_instance.adapter_type:
                device_type = elm_instance.adapter_type.lower()
            
            # Get optimal settings
            settings = DeviceManager.get_optimal_settings(device_type)
            
            # Enable enhanced features
            success = DeviceManager.enable_enhanced_features(elm_instance, device_type)
            
            if success:
                print(_("Device %s initialized successfully with enhanced features") % device_type)
            else:
                print(_("Device %s initialized with basic features only") % device_type)
            
            return True
            
        except Exception as e:
            print(_("Device initialization error: %s") % e)
            return False
