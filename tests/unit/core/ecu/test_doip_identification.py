from types import SimpleNamespace

from ddt4all.core.ecu.ecu_ident import EcuIdent
from ddt4all.core.ecu.ecu_scanner import EcuScanner
import ddt4all.options as options


class LogView:
    def __init__(self):
        self.messages = []

    def append(self, message):
        self.messages.append(message)


class FakeDoIPDevice:
    def __init__(self):
        self.requests = []

    def start_session_can(self, request):
        return request == "1003"

    def request(self, request, cache=False):
        self.requests.append(request)
        responses = {
            "22F1A0": "62 F1 A0 08",
            "22F18A": "62 F1 8A 54 45 53 54",
            "22F194": "62 F1 94 53 4F 46 54",
            "22F195": "62 F1 95 56 45 52",
            "1001": "50 01",
        }
        return responses[request]


def make_scanner(target):
    scanner = EcuScanner.__new__(EcuScanner)
    scanner.ecu_database = SimpleNamespace(
        targets=[target],
        addr_group_mapping={"119": "Engine"},
        addr_group_mapping_long={"119": "Engine ECU"},
    )
    scanner.ecus = {}
    scanner.approximate_ecus = {}
    scanner.num_ecu_found = 0
    scanner.report_data = []
    return scanner


def test_doip_uds_identification_matches_real_data_to_can_database_entry(monkeypatch):
    target = EcuIdent(
        "8", "TEST", "SOFT", "VER", "Engine ECU", "Engine",
        "engine.json", "CAN", [], "04",
    )
    scanner = make_scanner(target)
    device = FakeDoIPDevice()
    logview = LogView()
    monkeypatch.setattr(options, "main_window", SimpleNamespace(logview=logview))

    scanner._identify_doip_ecu(device, "119", None)

    assert "[ Engine ] Engine ECU" in scanner.ecus
    assert target.addr == "119"
    assert device.requests == ["22F1A0", "22F18A", "22F194", "22F195", "1001"]
    assert logview.messages


def test_legacy_doip_identification_uses_same_record_parser_as_can(monkeypatch):
    target = EcuIdent(
        "8", "TEST", "534F", "5645", "Engine ECU", "Engine",
        "engine.json", "CAN", [], "04",
    )
    scanner = make_scanner(target)
    response = bytearray(20)
    response[0:2] = bytes.fromhex("61 80")
    response[7] = 8
    response[8:12] = b"TEST"
    response[16:18] = b"SO"
    response[18:20] = b"VE"
    logview = LogView()
    monkeypatch.setattr(options, "main_window", SimpleNamespace(logview=logview))

    scanner.check_ecu(" ".join("%02X" % byte for byte in response), None, "119", "DoIP")

    assert "[ Engine ] Engine ECU" in scanner.ecus
    assert target.addr == "119"


def test_can_identification_keeps_its_short_record_layout(monkeypatch):
    target = EcuIdent(
        "8", "TEST", "534F4654", "56455253", "Engine ECU", "Engine",
        "engine.json", "CAN", [], "04",
    )
    scanner = make_scanner(target)
    response = bytes.fromhex("61 80 08") + b"TEST" + b"SOFT" + b"VERS"
    monkeypatch.setattr(options, "main_window", SimpleNamespace(logview=LogView()))

    scanner.check_ecu(" ".join("%02X" % byte for byte in response), None, "04", "CAN")

    assert "[ Engine ] Engine ECU" in scanner.ecus
