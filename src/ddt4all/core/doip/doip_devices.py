from ddt4all.core.elm.elm import (
    get_can_addr,
    get_can_addr_ext,
    get_can_addr_snat,
    get_can_addr_snat_ext
)
from ddt4all.core.doip.doip_connection import DoIPConnection
from ddt4all.core.doip.doip_protocol_error import DoIPProtocolError
import ddt4all.options as options

_ = options.translator('ddt4all')

class DoIPDevice:
    """DoIP Device Interface for Ethernet-based diagnostic tools
    
    Provides high-level interface for DoIP communication with modern automotive
    diagnostic interfaces. Compatible with Bosch MTS, VXDIAG, VAG ODIS, JLR DoIP VCI and other
    ISO 13400 compliant devices.
    """
    
    def __init__(self, target_ip="192.168.0.12"):
        self.doip = DoIPConnection(target_ip)
        self.connectionStatus = False
        self.currentaddress = 0x00
        self.startSession = ""
        self.rsp_cache = {}
        self.device_type = "doip_device"
        
        # Get device-specific settings
        self.settings = options.get_device_settings(self.device_type)
        self.timeout = self.settings.get('timeout', 4.0)
        self.doip.timeout = self.timeout
    
    def connect(self):
        """Establish DoIP connection with vehicle identification"""
        if self.doip.connect():
            self.connectionStatus = True
            # Perform vehicle identification according to ISO 13400
            try:
                vehicle_info = self.doip.vehicle_identification_request()
                print(f"DoIP Vehicle identified: VIN={vehicle_info['vin']}, Address={vehicle_info['logical_address']}")
                self.target_address = vehicle_info['logical_address']
                return True
            except Exception as e:
                print(f"DoIP vehicle identification failed: {e}")
                self.disconnect()
                return False
        return False
    
    def disconnect(self):
        """Close DoIP connection gracefully"""
        self.doip.disconnect()
        self.connectionStatus = False
    
    def request(self, req, positive='', cache=True, serviceDelay="0"):
        """Send diagnostic request over DoIP with proper error handling"""
        if not self.connectionStatus:
            raise DoIPProtocolError(_("Not connected to DoIP device"))
        
        # Convert hex string to bytes with validation
        try:
            req_bytes = bytes.fromhex(req.replace(' ', ''))
        except ValueError as e:
            raise DoIPProtocolError(_("Invalid hex request format: {}").format(e))
        
        # Send diagnostic message with addressing
        try:
            response = self.doip.send_diagnostic_message(req_bytes)
            return response
        except Exception as e:
            raise DoIPProtocolError(_("DoIP request failed: {}").format(e))
    
    def start_session_can(self, start_session):
        """Start diagnostic session over DoIP according to ISO 13400"""
        if not self.connectionStatus:
            return False
        
        try:
            # Convert start session command to hex bytes
            session_bytes = bytes.fromhex(start_session.replace(' ', ''))
            response = self.doip.send_diagnostic_message(session_bytes)
            if len(response['data']) >= 1 and response['data'][0] == 0x50:
                self.startSession = start_session
                return True
            return False
        except Exception as e:
            raise DoIPProtocolError(_("DoIP session start failed: {}").format(e))
    
    def init_can(self):
        """Initialize CAN communication over DoIP"""
        if not self.connectionStatus:
            return False
        
        try:
            # Start diagnostic session with extended addressing
            return self.start_session_can("10C0")
        except Exception as e:
            raise DoIPProtocolError(_("DoIP CAN initialization failed: {}").format(e))
            return False
    
    def set_can_addr(self, addr, ecu, canline=0):
        """Set CAN addressing for DoIP communication with Electric ECU support
        
        Special support for Electric ECUs and EVC (Electric Vehicle Controller) in newer vehicles.
        Electric vehicles use various addressing schemes including 29-bit, extended addressing,
        and special protocols for high-voltage systems.
        """
        if 'idTx' in ecu and 'idRx' in ecu:
            TXa = ecu['idTx']
            RXa = ecu['idRx']
            self.doip.source_address = TXa
            self.doip.target_address = RXa
            # self.currentaddress =  get_can_addr(TXa) // TODO: https://github.com/cedricp/ddt4all/pull/1734
            self.currentaddress = addr
        elif get_can_addr(addr) is not None and get_can_addr_snat(addr) is not None:
            TXa = get_can_addr(addr)
            RXa = get_can_addr_snat(addr)
            self.doip.source_address = TXa
            self.doip.target_address = RXa
            # self.currentaddress = TXa // TODO: https://github.com/cedricp/ddt4all/pull/1734
            self.currentaddress = addr
        elif get_can_addr_ext(addr) is not None and get_can_addr_snat_ext(addr) is not None:
            TXa =  get_can_addr_ext(addr)
            RXa = get_can_addr_snat_ext(addr)
            self.doip.source_address = TXa
            self.doip.target_address = RXa
            # self.currentaddress = TXa // TODO: https://github.com/cedricp/ddt4all/pull/1734
            self.currentaddress = addr
        else:
            return

        # Special handling for Electric ECUs and EVC
        addr_upper = addr.upper()
        is_electric_ecu = addr_upper in ['EVC', 'BMS', 'OBC', 'MCU', 'PEB', 'LBC', 'INV', 'VCM', 'BCM', 'GWM']
        
        if is_electric_ecu:
            self.doip.extended_29bit = True
            print(_("DoIP: Electric ECU detected - {}").format(addr))
            print(_("DoIP: Using extended addressing for Electric Vehicle Systems"))
            # Configure for 29-bit addressing if needed (newer vehicles)
            # Electric ECUs and EVC typically use 29-bit addressing
            if TXa > 0x7FF or RXa > 0x7FF:
                self.doip.extended_29bit = True
                print(_("DoIP: Using 29-bit extended addressing - TX:0x{:04X}, RX:0x{:04X}").format(TXa, RXa))
            else:
                self.doip.extended_29bit = False
                print(_("DoIP: Using 11-bit standard addressing - TX:0x{:03X}, RX:0x{:03X}").format(TXa, RXa))
        else:
            # Configure for 29-bit addressing if needed (newer vehicles)
            if TXa > 0x7FF or RXa > 0x7FF:
                self.doip.extended_29bit = True
                print(_("DoIP: Using 29-bit extended addressing - TX:0x{:04X}, RX:0x{:04X}").format(TXa, RXa))
            else:
                self.doip.extended_29bit = False
                print(_("DoIP: Using 11-bit standard addressing - TX:0x{:03X}, RX:0x{:03X}").format(TXa, RXa))

        self.doip.source_address = TXa
        self.doip.target_address = RXa
