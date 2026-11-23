"""Regression tests for EcuScanner.check_ecu (issues #1925 / #1926).

Verifies that check_ecu does not crash on empty, invalid, or too-short
identification responses (which surface to the user as "NO DATA"), and that
valid responses are parsed and forwarded to check_ecu2.
"""

from types import SimpleNamespace

from ddt4all.core.ecu.ecu_scanner import EcuScanner
import ddt4all.options as options


class LogView:
    def __init__(self):
        self.messages = []

    def append(self, message):
        self.messages.append(message)


def make_scanner():
    scanner = EcuScanner.__new__(EcuScanner)
    scanner.ecu_database = SimpleNamespace(
        targets=[],
        addr_group_mapping={"04": "Engine"},
        addr_group_mapping_long={"04": "Engine ECU"},
    )
    scanner.ecus = {}
    scanner.approximate_ecus = {}
    scanner.num_ecu_found = 0
    scanner.report_data = []
    return scanner


def test_check_ecu_empty_response_does_not_crash(monkeypatch):
    monkeypatch.setattr(options, "main_window", SimpleNamespace(logview=LogView()))
    scanner = make_scanner()
    captured = {}

    def fake_check_ecu2(diagversion, supplier, soft, version, label, addr, protocol):
        captured["called"] = True

    scanner.check_ecu2 = fake_check_ecu2
    scanner.check_ecu(None, None, "04", "CAN")
    assert "called" not in captured


def test_check_ecu_invalid_hex_does_not_crash(monkeypatch):
    monkeypatch.setattr(options, "main_window", SimpleNamespace(logview=LogView()))
    scanner = make_scanner()
    captured = {}

    def fake_check_ecu2(diagversion, supplier, soft, version, label, addr, protocol):
        captured["called"] = True

    scanner.check_ecu2 = fake_check_ecu2
    scanner.check_ecu("NOT HEX !!", None, "04", "CAN")
    assert "called" not in captured


def test_check_ecu_too_short_does_not_crash(monkeypatch):
    monkeypatch.setattr(options, "main_window", SimpleNamespace(logview=LogView()))
    scanner = make_scanner()
    captured = {}

    def fake_check_ecu2(diagversion, supplier, soft, version, label, addr, protocol):
        captured["called"] = True

    scanner.check_ecu2 = fake_check_ecu2
    # Only 10 bytes (< 15 minimum).
    scanner.check_ecu("61 80 08 54 45 53 54 4F 4E", None, "04", "CAN")
    assert "called" not in captured


def test_check_ecu_long_response_forwards_to_check_ecu2(monkeypatch):
    monkeypatch.setattr(options, "main_window", SimpleNamespace(logview=LogView()))
    scanner = make_scanner()
    captured = {}

    def fake_check_ecu2(diagversion, supplier, soft, version, label, addr, protocol):
        captured.update(
            {
                "diagversion": diagversion,
                "supplier": supplier,
                "soft": soft,
                "version": version,
                "label": label,
                "addr": addr,
                "protocol": protocol,
            }
        )

    scanner.check_ecu2 = fake_check_ecu2
    # 20+ byte response: 61 80 <diag=8> TEST SOFT... VERS...
    response = bytearray(20)
    response[0:2] = bytes.fromhex("61 80")
    response[7] = 8
    response[8:12] = b"TEST"
    response[16:18] = b"SO"
    response[18:20] = b"VE"
    scanner.check_ecu(
        " ".join("%02X" % b for b in response), None, "119", "CAN"
    )
    assert captured["diagversion"] == "8"
    assert captured["supplier"] == "TEST"
    assert captured["soft"] == "534F"
    assert captured["version"] == "5645"
    assert captured["addr"] == "119"
    assert captured["protocol"] == "CAN"


def test_check_ecu_short_response_forwards_to_check_ecu2(monkeypatch):
    monkeypatch.setattr(options, "main_window", SimpleNamespace(logview=LogView()))
    scanner = make_scanner()
    captured = {}

    def fake_check_ecu2(diagversion, supplier, soft, version, label, addr, protocol):
        captured.update(
            {
                "diagversion": diagversion,
                "supplier": supplier,
                "soft": soft,
                "version": version,
            }
        )

    scanner.check_ecu2 = fake_check_ecu2
    # 15-byte response: 61 80 08 TEST SOFTVERS
    response = bytes.fromhex("61 80 08") + b"TEST" + b"SOFT" + b"VERS"
    scanner.check_ecu(
        " ".join("%02X" % b for b in response), None, "04", "CAN"
    )
    assert captured["diagversion"] == "8"
    assert captured["supplier"] == "TEST"
    assert captured["soft"] == "534F4654"
    assert captured["version"] == "56455253"