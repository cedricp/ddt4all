import pickle
import socket
import struct

import pytest

from ddt4all.core.doip.doip_connection import DoIPConnection
from ddt4all.core.doip.doip_devices import DoIPDevice
from ddt4all.core.doip.doip_message_type import DoIPMessageType
from ddt4all.core.doip.doip_protocol_error import DoIPProtocolError


class FakeSocket:
    def __init__(self, incoming=b"", max_chunk=None):
        self.incoming = bytearray(incoming)
        self.max_chunk = max_chunk
        self.sent = []
        self.closed = False
        self.address = None

    def settimeout(self, timeout):
        self.timeout = timeout

    def connect(self, address):
        self.address = address

    def sendall(self, data):
        self.sent.append(data)

    def recv(self, size):
        if not self.incoming:
            raise socket.timeout()
        if self.max_chunk is not None:
            size = min(size, self.max_chunk)
        size = min(size, len(self.incoming))
        data = bytes(self.incoming[:size])
        del self.incoming[:size]
        return data

    def close(self):
        self.closed = True


def frame(message_type, payload=b"", version=2):
    return DoIPConnection._encode_message(message_type, payload, version)


def test_header_uses_iso13400_byte_layout():
    encoded = DoIPConnection._encode_message(
        DoIPMessageType.DIAGNOSTIC_MESSAGE, b"abc"
    )
    assert encoded == bytes.fromhex("02 FD 80 01 00 00 00 03") + b"abc"


def test_receive_message_reads_fragmented_tcp_frames():
    payload = b"identification"
    fake = FakeSocket(frame(DoIPMessageType.VEHICLE_IDENTIFICATION_RESPONSE, payload), 2)
    connection = DoIPConnection()
    connection.socket = fake
    connection.connection_status = True

    message_type, actual_payload = connection.receive_message()

    assert message_type is DoIPMessageType.VEHICLE_IDENTIFICATION_RESPONSE
    assert actual_payload == payload


def test_receive_timeout_closes_and_invalidates_connection():
    fake = FakeSocket()
    connection = DoIPConnection()
    connection.socket = fake
    connection.connection_status = True
    connection.routing_activated = True

    with pytest.raises(socket.timeout):
        connection.receive_message()

    assert fake.closed
    assert connection.socket is None
    assert not connection.connection_status
    assert not connection.routing_activated


def test_routing_activation_and_diagnostic_exchange(monkeypatch):
    tester_address = 0x0E00
    ecu_address = 0x0077
    routing_response = struct.pack(">HB", tester_address, 0) + b"\x00" * 4
    acknowledgement = struct.pack(">HHB", ecu_address, tester_address, 0)
    response = struct.pack(">HH", ecu_address, tester_address) + b"\x62\xF1\x90"
    incoming = (
        frame(DoIPMessageType.ROUTING_ACTIVATION_RESPONSE, routing_response)
        + frame(DoIPMessageType.DIAGNOSTIC_MESSAGE_ACK, acknowledgement)
        + frame(DoIPMessageType.ALIVE_CHECK_REQUEST)
        + frame(DoIPMessageType.DIAGNOSTIC_MESSAGE, response)
    )
    fake = FakeSocket(incoming, max_chunk=3)
    monkeypatch.setattr(
        "ddt4all.core.doip.doip_connection.socket.socket",
        lambda *_args, **_kwargs: fake,
    )
    connection = DoIPConnection("127.0.0.1")

    assert connection.connect()
    connection.routing_activation()
    connection.target_address = ecu_address
    actual = connection.send_diagnostic_message(bytes.fromhex("22 F1 90"))

    assert actual == bytes.fromhex("62 F1 90")
    assert connection.routing_activated
    assert fake.address == ("127.0.0.1", 13400)
    assert fake.sent[0][8:] == struct.pack(">HB", tester_address, 0) + b"\x00" * 4
    assert fake.sent[1][8:] == struct.pack(">HH", tester_address, ecu_address) + bytes.fromhex("22 F1 90")
    assert fake.sent[2] == frame(
        DoIPMessageType.ALIVE_CHECK_RESPONSE, struct.pack(">H", tester_address)
    )

    connection.disconnect()
    assert fake.closed
    assert not connection.connection_status
    assert not connection.routing_activated


def test_rejected_routing_activation_is_an_explicit_error(monkeypatch):
    response = struct.pack(">HB", 0x0E00, 0x01) + b"\x00" * 4
    fake = FakeSocket(frame(DoIPMessageType.ROUTING_ACTIVATION_RESPONSE, response))
    monkeypatch.setattr(
        "ddt4all.core.doip.doip_connection.socket.socket",
        lambda *_args, **_kwargs: fake,
    )
    connection = DoIPConnection()
    connection.connect()

    with pytest.raises(DoIPProtocolError, match="rejected"):
        connection.routing_activation()

    connection.disconnect()


def test_discovery_parses_vehicle_identification_and_closes_udp_socket(monkeypatch):
    vin = b"1HGCM82633A004352"
    payload = (
        vin
        + struct.pack(">H", 0x0E00)
        + bytes.fromhex("010203040506")
        + bytes.fromhex("A1A2A3A4A5A6")
        + b"\x00\x01"
    )

    class FakeDatagramSocket:
        def __init__(self):
            self.closed = False
            self.sent = None
            self.replies = [(
                frame(DoIPMessageType.VEHICLE_IDENTIFICATION_RESPONSE, payload),
                ("192.168.0.12", 13400),
            )]

        def setsockopt(self, *_args):
            pass

        def settimeout(self, timeout):
            self.timeout = timeout

        def sendto(self, data, address):
            self.sent = data, address

        def recvfrom(self, _size):
            if self.replies:
                return self.replies.pop(0)
            raise socket.timeout()

        def close(self):
            self.closed = True

    fake = FakeDatagramSocket()
    monkeypatch.setattr(
        "ddt4all.core.doip.doip_connection.socket.socket",
        lambda *_args, **_kwargs: fake,
    )

    vehicles = DoIPConnection.discover("192.168.0.12", timeout=0.01)

    assert len(vehicles) == 1
    assert vehicles[0]["vin"] == vin.decode("ascii")
    assert vehicles[0]["logical_address"] == 0x0E00
    assert vehicles[0]["eid"] == "010203040506"
    assert vehicles[0]["gid"] == "A1A2A3A4A5A6"
    assert vehicles[0]["further_action"] == 0
    assert vehicles[0]["synchronization_status"] == 1
    assert fake.sent[0][:2] == b"\xFF\x00"
    assert fake.sent[1] == ("192.168.0.12", 13400)
    assert fake.closed


def test_device_request_uses_selected_logical_address_and_elm_response_format():
    device = DoIPDevice()
    device.connectionStatus = True
    device.doip.connection_status = True
    device.doip.routing_activated = True
    device.doip.send_diagnostic_message = lambda request: b"\x62\xF1\x90"
    device.set_target_address("119")

    assert device.target_address == 119
    assert device.request("22 F1 90") == "62 F1 90"

    with pytest.raises(DoIPProtocolError, match="out of range"):
        device.set_target_address(0x10000)


def test_unconnected_doip_device_is_safe_to_pickle_for_process_startup():
    device = pickle.loads(pickle.dumps(DoIPDevice("127.0.0.1")))
    assert device.target_ip == "127.0.0.1"
    assert not device.connectionStatus
