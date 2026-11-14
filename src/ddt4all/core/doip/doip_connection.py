import socket
import struct
import time

from ddt4all.core.doip.doip_message_type import DoIPMessageType
from ddt4all.core.doip.doip_protocol_error import DoIPProtocolError


class DoIPConnection:
    """ISO 13400 TCP/UDP transport for DoIP diagnostics."""

    HEADER_SIZE = 8
    MAX_PAYLOAD_SIZE = 16 * 1024 * 1024
    PROTOCOL_VERSION = 0x02

    def __init__(self, target_ip="192.168.0.12", target_port=13400, timeout=4.0):
        self.target_ip = target_ip
        self.target_port = int(target_port)
        self.socket = None
        self.connection_status = False
        self.routing_activated = False
        self.source_address = 0x0E00
        self.target_address = None
        self.timeout = float(timeout)

    @staticmethod
    def _encode_message(message_type, payload=b"", version=PROTOCOL_VERSION):
        if not isinstance(payload, bytes):
            payload = bytes(payload)
        if len(payload) > DoIPConnection.MAX_PAYLOAD_SIZE:
            raise DoIPProtocolError("DoIP payload exceeds the maximum supported size")
        inverse_version = version ^ 0xFF
        return bytes((version, inverse_version)) + struct.pack(
            ">HI", message_type.value, len(payload)
        ) + payload

    @staticmethod
    def _decode_header(header):
        if len(header) != DoIPConnection.HEADER_SIZE:
            raise DoIPProtocolError("Invalid DoIP header length")
        version, inverse_version = header[0], header[1]
        if inverse_version != (version ^ 0xFF):
            raise DoIPProtocolError("Invalid DoIP protocol version complement")
        if version not in (0x02, 0x03):
            raise DoIPProtocolError("Unsupported DoIP protocol version: 0x%02X" % version)
        payload_type, payload_length = struct.unpack(">HI", header[2:])
        if payload_length > DoIPConnection.MAX_PAYLOAD_SIZE:
            raise DoIPProtocolError("DoIP payload exceeds the maximum supported size")
        try:
            message_type = DoIPMessageType(payload_type)
        except ValueError as exc:
            raise DoIPProtocolError("Unsupported DoIP payload type: 0x%04X" % payload_type) from exc
        return message_type, payload_length

    @staticmethod
    def _parse_vehicle_identification(payload, address):
        if len(payload) < 31:
            raise DoIPProtocolError("Vehicle identification response is incomplete")

        vin = payload[:17].decode("ascii", errors="replace")
        logical_address = struct.unpack(">H", payload[17:19])[0]
        result = {
            "vin": vin,
            "logical_address": logical_address,
            "eid": payload[19:25].hex().upper(),
            "gid": payload[25:31].hex().upper(),
            "address": address,
        }
        if len(payload) > 31:
            result["further_action"] = payload[31]
        if len(payload) > 32:
            result["synchronization_status"] = payload[32]
        if len(payload) > 33:
            result["additional_data"] = payload[33:]
        else:
            result["additional_data"] = b""
        return result

    @classmethod
    def discover(cls, target_ip="255.255.255.255", target_port=13400, timeout=1.0):
        """Broadcast or unicast a vehicle-identification request and collect replies."""
        request = cls._encode_message(
            DoIPMessageType.VEHICLE_IDENTIFICATION_REQUEST,
            version=0xFF,
        )
        vehicles = []
        discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            discovery_socket.settimeout(max(float(timeout), 0.01))
            discovery_socket.sendto(request, (target_ip, int(target_port)))
            deadline = time.monotonic() + max(float(timeout), 0.01)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                discovery_socket.settimeout(remaining)
                try:
                    packet, address = discovery_socket.recvfrom(cls.HEADER_SIZE + cls.MAX_PAYLOAD_SIZE)
                except socket.timeout:
                    break
                if len(packet) < cls.HEADER_SIZE:
                    continue
                try:
                    message_type, payload_length = cls._decode_header(packet[:cls.HEADER_SIZE])
                except DoIPProtocolError:
                    continue
                if message_type != DoIPMessageType.VEHICLE_IDENTIFICATION_RESPONSE:
                    continue
                if payload_length != len(packet) - cls.HEADER_SIZE:
                    continue
                try:
                    vehicles.append(
                        cls._parse_vehicle_identification(packet[cls.HEADER_SIZE:], address[0])
                    )
                except DoIPProtocolError:
                    continue
        finally:
            discovery_socket.close()
        return vehicles

    def connect(self):
        self.disconnect()
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.settimeout(self.timeout)
        try:
            connection.connect((self.target_ip, self.target_port))
        except OSError:
            connection.close()
            raise
        self.socket = connection
        self.connection_status = True
        return True

    def disconnect(self):
        self._invalidate_connection()

    def _invalidate_connection(self):
        connection = self.socket
        self.socket = None
        self.connection_status = False
        self.routing_activated = False
        if connection is not None:
            try:
                connection.close()
            except OSError:
                pass

    def _require_connection(self):
        if not self.connection_status or self.socket is None:
            raise DoIPProtocolError("Not connected to a DoIP entity")

    def send_message(self, message_type, payload=b""):
        self._require_connection()
        try:
            self.socket.sendall(self._encode_message(message_type, payload))
        except OSError:
            self._invalidate_connection()
            raise

    def _receive_exactly(self, count):
        self._require_connection()
        parts = []
        remaining = count
        while remaining:
            chunk = self.socket.recv(remaining)
            if not chunk:
                self._invalidate_connection()
                raise DoIPProtocolError("DoIP connection closed by peer")
            parts.append(chunk)
            remaining -= len(chunk)
        return b"".join(parts)

    def receive_message(self):
        self._require_connection()
        try:
            header = self._receive_exactly(self.HEADER_SIZE)
            message_type, payload_length = self._decode_header(header)
            payload = self._receive_exactly(payload_length) if payload_length else b""
        except (OSError, DoIPProtocolError):
            self._invalidate_connection()
            raise
        return message_type, payload

    def vehicle_identification_request(self, timeout=None):
        """Perform UDP vehicle discovery; identification is not a TCP message."""
        return self.discover(
            self.target_ip,
            self.target_port,
            self.timeout if timeout is None else timeout,
        )

    def routing_activation(self, activation_type=0x00):
        self._require_connection()
        if not 0 <= self.source_address <= 0xFFFF:
            raise DoIPProtocolError("Tester logical address is out of range")
        payload = struct.pack(">HB", self.source_address, activation_type) + b"\x00" * 4
        self.send_message(DoIPMessageType.ROUTING_ACTIVATION_REQUEST, payload)
        message_type, response = self.receive_message()
        if message_type != DoIPMessageType.ROUTING_ACTIVATION_RESPONSE:
            raise DoIPProtocolError(
                "Expected routing-activation response, received %s" % message_type.name
            )
        if len(response) < 3:
            raise DoIPProtocolError("Routing-activation response is incomplete")
        tester_address, response_code = struct.unpack(">HB", response[:3])
        if tester_address != self.source_address:
            raise DoIPProtocolError("Routing-activation response has the wrong tester address")
        if response_code != 0:
            raise DoIPProtocolError(
                "DoIP routing activation rejected with code 0x%02X" % response_code
            )
        self.routing_activated = True
        return response

    def _handle_alive_check(self, payload):
        if payload:
            raise DoIPProtocolError("Alive-check request must have an empty payload")
        response = struct.pack(">H", self.source_address)
        self.send_message(DoIPMessageType.ALIVE_CHECK_RESPONSE, response)

    def send_diagnostic_message(self, req_bytes, target_address=None):
        self._require_connection()
        if not self.routing_activated:
            raise DoIPProtocolError("DoIP routing has not been activated")
        if target_address is not None:
            self.target_address = int(target_address)
        if self.target_address is None or not 0 <= self.target_address <= 0xFFFF:
            raise DoIPProtocolError("A valid target logical address is required")
        if not isinstance(req_bytes, bytes):
            req_bytes = bytes(req_bytes)
        if not req_bytes:
            raise DoIPProtocolError("Diagnostic request must not be empty")

        request_payload = struct.pack(
            ">HH", self.source_address, self.target_address
        ) + req_bytes
        self.send_message(DoIPMessageType.DIAGNOSTIC_MESSAGE, request_payload)

        while True:
            message_type, response = self.receive_message()
            if message_type == DoIPMessageType.ALIVE_CHECK_REQUEST:
                self._handle_alive_check(response)
                continue
            if message_type in (
                DoIPMessageType.DIAGNOSTIC_MESSAGE_ACK,
                DoIPMessageType.DIAGNOSTIC_MESSAGE_NACK,
            ):
                if len(response) < 5:
                    raise DoIPProtocolError("DoIP diagnostic acknowledgement is incomplete")
                source, target, code = struct.unpack(">HHB", response[:5])
                if target != self.source_address:
                    raise DoIPProtocolError("DoIP acknowledgement has the wrong tester address")
                if source != self.target_address:
                    raise DoIPProtocolError("DoIP acknowledgement has the wrong ECU address")
                if message_type == DoIPMessageType.DIAGNOSTIC_MESSAGE_NACK or code:
                    raise DoIPProtocolError(
                        "DoIP diagnostic message rejected with code 0x%02X" % code
                    )
                continue
            if message_type != DoIPMessageType.DIAGNOSTIC_MESSAGE:
                raise DoIPProtocolError(
                    "Expected diagnostic response, received %s" % message_type.name
                )
            if len(response) < 5:
                raise DoIPProtocolError("DoIP diagnostic response is incomplete")
            source, target = struct.unpack(">HH", response[:4])
            if target != self.source_address:
                raise DoIPProtocolError("DoIP response has the wrong tester address")
            if source != self.target_address:
                raise DoIPProtocolError("DoIP response has the wrong ECU address")
            return response[4:]

    def alive_check(self):
        self.send_message(DoIPMessageType.ALIVE_CHECK_REQUEST)
        message_type, payload = self.receive_message()
        if message_type != DoIPMessageType.ALIVE_CHECK_RESPONSE or len(payload) != 2:
            raise DoIPProtocolError("Invalid DoIP alive-check response")
        return struct.unpack(">H", payload)[0]
