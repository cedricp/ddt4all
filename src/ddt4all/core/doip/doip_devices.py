from ddt4all.core.doip.doip_connection import DoIPConnection
from ddt4all.core.doip.doip_protocol_error import DoIPProtocolError
import ddt4all.options as options

_ = options.translator("ddt4all")


class DoIPDevice:
    """DDT4All diagnostic-device interface backed by ISO 13400."""

    is_doip_device = True
    adapter_type = "DOIP"

    def __init__(self, target_ip="192.168.0.12", target_port=13400):
        self.target_ip = target_ip
        self.target_port = int(target_port)
        self.doip = DoIPConnection(target_ip, self.target_port)
        self.connectionStatus = False
        self.currentaddress = None
        self.target_address = None
        self.source_address = self.doip.source_address
        self.startSession = ""
        self.rsp_cache = {}
        self.vehicle_info = []
        self.last_error = ""
        self.timeout = float(options.get_device_settings("doip_device").get("timeout", 4.0))
        self.doip.timeout = self.timeout

    @staticmethod
    def discover_vehicles(target_ip="255.255.255.255", target_port=13400, timeout=1.0):
        return DoIPConnection.discover(target_ip, target_port, timeout)

    def connect(self):
        self.disconnect()
        self.doip.timeout = self.timeout
        try:
            self.vehicle_info = self.doip.vehicle_identification_request(
                timeout=min(self.timeout, 1.0)
            )
            self.doip.connect()
            self.doip.routing_activation()
            self.connectionStatus = True
            self.last_error = ""
            return True
        except (DoIPProtocolError, OSError) as exc:
            self.last_error = str(exc)
            self.disconnect()
            options.last_error = self.last_error
            print(_("DoIP connection failed: %s") % exc)
            return False

    def disconnect(self):
        self.doip.disconnect()
        self.connectionStatus = False

    def close(self):
        self.disconnect()

    def connectionStat(self):
        return self.connectionStatus and self.doip.connection_status

    def set_target_address(self, address):
        if isinstance(address, str):
            address = address.strip()
            if not address:
                raise DoIPProtocolError("Target logical address must not be empty")
            try:
                address = int(address, 0) if address.lower().startswith("0x") else int(address, 10)
            except ValueError as exc:
                raise DoIPProtocolError("Invalid target logical address: %s" % address) from exc
        address = int(address)
        if not 0 <= address <= 0xFFFF:
            raise DoIPProtocolError("Target logical address is out of range")
        self.target_address = address
        self.currentaddress = address
        self.doip.target_address = address

    def request(self, req, positive="", cache=True, serviceDelay="0"):
        if not self.connectionStat():
            raise DoIPProtocolError(_("Not connected to DoIP device"))
        if self.target_address is None:
            raise DoIPProtocolError(_("No DoIP ECU logical address is selected"))
        try:
            req_bytes = bytes.fromhex(str(req).replace(" ", ""))
        except ValueError as exc:
            raise DoIPProtocolError(_("Invalid hex request format: %s") % exc) from exc
        response = self.doip.send_diagnostic_message(req_bytes)
        return " ".join("%02X" % byte for byte in response)

    def cmd(self, command, *args, **kwargs):
        command = str(command).strip()
        if command.upper().startswith("AT"):
            raise DoIPProtocolError(_("ELM AT commands are not supported over DoIP"))
        return self.request(command, *args, **kwargs)

    def start_session_can(self, start_session):
        try:
            response = self.request(start_session, cache=False)
        except DoIPProtocolError:
            raise
        response_bytes = bytes.fromhex(response) if response else b""
        if response_bytes and response_bytes[0] == 0x50:
            self.startSession = str(start_session)
            return True
        return False

    def init_can(self):
        if not self.connectionStat():
            return False
        return self.doip.routing_activated

    def set_can_addr(self, addr, ecu=None, canline=0):
        """Retain the selected DoIP logical address; CAN IDs are not DoIP addresses."""
        self.currentaddress = self.target_address

    def set_doip_addr(self, address, ecu=None):
        self.set_target_address(address)

    def init_iso(self):
        raise DoIPProtocolError(_("K-line initialization is not supported over DoIP"))

    def set_iso_addr(self, addr, ecu=None):
        raise DoIPProtocolError(_("K-line addressing is not supported over DoIP"))
