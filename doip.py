#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""DoIP (Diagnostics over IP) Protocol Implementation

ISO 13400 Standard Implementation for Ethernet-based vehicle diagnostics

This module provides complete DoIP protocol support for modern automotive diagnostic
interfaces that support Ethernet communication, such as Bosch MTS, VXDIAG, VAG ODIS,
and JLR DoIP VCI devices.

DoIP is primarily used for newer vehicles (2016+) with extended 29-bit CAN identifiers
and modern ECU architectures requiring high-speed Ethernet diagnostics.

Note: Traditional ELM327-based adapters (OBDLink, VGate, DERLEK) do not support DoIP
as they lack Ethernet hardware and IP stack capabilities.

This module includes internationalization support for multi-language environments."""

import socket
import struct
import time
import threading
from enum import Enum

import options

_ = options.translator('ddt4all')


class DoIPMessageType(Enum):
    """DoIP Message Types according to ISO 13400"""
    VEHICLE_IDENTIFICATION_REQUEST = 0x0001
    VEHICLE_IDENTIFICATION_RESPONSE = 0x0002
    VEHICLE_ANNOUNCEMENT = 0x0003
    DIAGNOSTIC_SESSION_CONTROL = 0x4001
    DIAGNOSTIC_MESSAGE = 0x4002
    ALIVE_CHECK_REQUEST = 0x4003
    ALIVE_CHECK_RESPONSE = 0x4004
    ENTITY_STATUS_REQUEST = 0x4005
    ENTITY_STATUS_RESPONSE = 0x4006


class DoIPProtocolError(Exception):
    """DoIP Protocol specific errors"""
    pass


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
            except:
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
            self.currentaddress = TXa
            self.doip.source_address = TXa
            self.doip.target_address = RXa
        elif elm.get_can_addr(addr) is not None and elm.get_can_addr_snat(addr) is not None:
            TXa = elm.get_can_addr(addr)
            RXa = elm.get_can_addr_snat(addr)
            self.currentaddress = TXa
            self.doip.source_address = TXa
            self.doip.target_address = RXa
        elif elm.get_can_addr_ext(addr) is not None and elm.get_can_addr_snat_ext(addr) is not None:
            TXa =  elm.get_can_addr_ext(addr)
            RXa = elm.get_can_addr_snat_ext(addr)
            self.currentaddress = TXa
            self.doip.source_address = TXa
            self.doip.target_address = RXa
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


if __name__ == '__main__':
    # Test DoIP implementation with Electric ECU support
    doip_device = DoIPDevice()
    
    if doip_device.connect():
        print(_("DoIP device connected successfully"))
        
        # Test CAN initialization
        if doip_device.init_can():
            print(_("DoIP CAN initialized with Electric ECU support"))
        
        # Test diagnostic request
        try:
            response = doip_device.request("22 F1 90")  # Read VIN
            print(_("DoIP response: {}").format(response))
        except Exception as e:
            print(_("DoIP request failed: {}").format(e))
        
        # Test Electric ECU configurations
        electric_ecus = [
            ('EVC', {'idTx': 0x18DA10F1, 'idRx': 0x18DB10F1}),  # Electric Vehicle Controller
            ('BMS', {'idTx': 0x18DA20F1, 'idRx': 0x18DB20F1}),  # Battery Management System
            ('OBC', {'idTx': 0x18DA30F1, 'idRx': 0x18DB30F1}),  # On-Board Charger
            ('INV', {'idTx': 0x18DA40F1, 'idRx': 0x18DB40F1}),  # Inverter (Motor Control)
            ('VCM', {'idTx': 0x18DA50F1, 'idRx': 0x18DB50F1}),  # Vehicle Control Module
            ('BCM', {'idTx': 0x18DA60F1, 'idRx': 0x18DB60F1}),  # Body Control Module
            ('GWM', {'idTx': 0x18DA70F1, 'idRx': 0x18DB70F1})   # Gateway Module
        ]
        
        for ecu_name, ecu_data in electric_ecus:
            print("\n" + _("Testing Electric ECU: {}").format(ecu_name))
            doip_device.set_can_addr(ecu_name, ecu_data)
            response = doip_device.request("22 F1 90")  # Read VIN
            print(_("DoIP response: {}").format(response))
        
        doip_device.disconnect()
    else:
        print(_("Failed to connect to DoIP device"))
