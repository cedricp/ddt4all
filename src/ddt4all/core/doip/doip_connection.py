import socket
import struct

from ddt4all.core.doip.doip_message_type import DoIPMessageType
from ddt4all.core.doip.doip_protocol_error import DoIPProtocolError
import ddt4all.options as options

_ = options.translator('ddt4all')

class DoIPConnection:
    """DoIP Connection Handler for Ethernet-based diagnostic interfaces
    
    Supports ISO 13400 DoIP protocol for modern automotive diagnostic tools with
    Ethernet/WiFi connectivity. Compatible with Bosch MTS, VXDIAG, VAG ODIS, JLR DoIP VCI.
    
    Designed for newer vehicles (2016+) with extended 29-bit CAN identifiers and
    modern ECU architectures requiring high-speed Ethernet diagnostics.
    """
    
    def __init__(self, target_ip="192.168.0.12", target_port=13400):
        self.target_ip = target_ip
        self.target_port = target_port
        self.socket = None
        self.connection_status = False
        self.source_address = 0x0E00  # Default source address (tester)
        self.target_address = 0x0E01  # Default target address (ECU)
        self.timeout = 4.0  # Default timeout in seconds
        self.extended_29bit = True  # Support for 29-bit CAN identifiers
        
    def connect(self):
        """Establish DoIP connection"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.target_ip, self.target_port))
            self.connection_status = True
            print(f"DoIP connected to {self.target_ip}:{self.target_port}")
            return True
        except Exception as e:
            print(f"DoIP connection failed: {e}")
            self.connection_status = False
            return False
    
    def disconnect(self):
        """Close DoIP connection"""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            finally:
                self.socket = None
        self.connection_status = False
        print("DoIP connection closed")
    
    def send_message(self, message_type, payload=b''):
        """Send DoIP message"""
        if not self.connection_status or not self.socket:
            raise DoIPProtocolError("Not connected to DoIP server")
        
        # Create DoIP header: Protocol Version (2 bytes) + Inverse Version (2 bytes) + 
        # Payload Type (2 bytes) + Payload Length (4 bytes)
        header = struct.pack('>HHHI', 0x02, 0xFD, message_type.value, len(payload))
        
        # Send header + payload
        message = header + payload
        self.socket.send(message)
        
    def receive_message(self):
        """Receive DoIP message"""
        if not self.connection_status or not self.socket:
            raise DoIPProtocolError("Not connected to DoIP server")
        
        # Receive header (8 bytes)
        header = self.socket.recv(8)
        if len(header) < 8:
            raise DoIPProtocolError("Invalid DoIP header received")
        
        # Parse header
        protocol_version, inverse_version, message_type, payload_length = struct.unpack('>HHHI', header)
        
        # Validate protocol version
        if protocol_version != 0x02 or inverse_version != 0xFD:
            raise DoIPProtocolError(f"Invalid DoIP version: {protocol_version}")
        
        # Receive payload
        if payload_length > 0:
            payload = self.socket.recv(payload_length)
            if len(payload) < payload_length:
                raise DoIPProtocolError("Incomplete DoIP payload received")
        else:
            payload = b''
        
        return DoIPMessageType(message_type), payload
    
    def vehicle_identification_request(self):
        """Send vehicle identification request according to ISO 13400"""
        self.send_message(DoIPMessageType.VEHICLE_IDENTIFICATION_REQUEST)
        
        try:
            message_type, payload = self.receive_message()
            if message_type == DoIPMessageType.VEHICLE_IDENTIFICATION_RESPONSE:
                if len(payload) >= 5:
                    # Parse VIN (17 bytes), logical address (2 bytes), EID (6 bytes), GID (6 bytes), and additional data
                    vin = payload[0:17].decode('ascii', errors='ignore')
                    logical_address = struct.unpack('>H', payload[17:19])[0]
                    eid = payload[19:25].hex()
                    gid = payload[25:31].hex()
                    
                    return {
                        'vin': vin,
                        'logical_address': logical_address,
                        'eid': eid,
                        'gid': gid,
                        'additional_data': payload[31:] if len(payload) > 31 else b''
                    }
                else:
                    raise DoIPProtocolError(_("Insufficient vehicle identification data"))
            else:
                raise DoIPProtocolError(_("Expected vehicle identification response, got: {}").format(message_type))
        except Exception as e:
            raise DoIPProtocolError(_("Vehicle identification failed: {}").format(e))
    
    def diagnostic_session_control(self, session_type):
        """Control diagnostic session according to ISO 13400"""
        payload = struct.pack('>H', session_type)
        self.send_message(DoIPMessageType.DIAGNOSTIC_SESSION_CONTROL, payload)
        
        try:
            message_type, payload = self.receive_message()
            if message_type == DoIPMessageType.DIAGNOSTIC_SESSION_CONTROL:
                if len(payload) >= 2:
                    session_status = struct.unpack('>H', payload[0:2])[0]
                    return session_status
                else:
                    raise DoIPProtocolError(_("Insufficient session control data"))
            else:
                raise DoIPProtocolError(_("Expected diagnostic session control response, got: {}").format(message_type))
        except Exception as e:
            raise DoIPProtocolError(_("Diagnostic session control failed: {}").format(e))
    
    def send_diagnostic_message(self, req_bytes):
        """Send diagnostic message with addressing according to ISO 13400"""
        # Add source and target addresses (4 bytes total)
        payload = struct.pack('>HH', self.source_address, self.target_address) + req_bytes
        
        self.send_message(DoIPMessageType.DIAGNOSTIC_MESSAGE, payload)
        
        try:
            message_type, payload = self.receive_message()
            if message_type == DoIPMessageType.DIAGNOSTIC_MESSAGE:
                if len(payload) >= 4:
                    source_address, target_address = struct.unpack('>HH', payload[0:4])
                    response_data = payload[4:]
                    return {
                        'source_address': source_address,
                        'target_address': target_address,
                        'data': response_data,
                        'extended_29bit': self.extended_29bit,
                        'electric_ecu': self.extended_29bit  # Electric ECUs typically use extended
                    }
                else:
                    raise DoIPProtocolError(_("Insufficient diagnostic message data"))
            else:
                raise DoIPProtocolError(_("Expected diagnostic message response, got: {}").format(message_type))
        except Exception as e:
            raise DoIPProtocolError(_("DoIP request failed: {}").format(e))
    
    def alive_check(self):
        """Perform alive check according to ISO 13400"""
        self.send_message(DoIPMessageType.ALIVE_CHECK_REQUEST)
        
        try:
            message_type, payload = self.receive_message()
            if message_type == DoIPMessageType.ALIVE_CHECK_RESPONSE:
                if len(payload) >= 2:
                    client_status = struct.unpack('>H', payload[0:2])[0]
                    return client_status
                else:
                    raise DoIPProtocolError(_("Insufficient alive check data"))
            else:
                raise DoIPProtocolError(_("Expected alive check response, got: {}").format(message_type))
        except Exception as e:
            raise DoIPProtocolError(_("Alive check failed: {}").format(e))

