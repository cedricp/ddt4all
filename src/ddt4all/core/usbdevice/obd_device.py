import array

from ddt4all.core.elm.elm import (
    get_can_addr,
    get_can_addr_ext,
    get_can_addr_snat,
    get_can_addr_snat_ext,
)
from ddt4all.core.usbdevice.usb_can import UsbCan
import ddt4all.options as options

_ = options.translator('ddt4all')

class OBDDevice:
    def __init__(self):
        self.device = UsbCan()
        if self.device is None or not self.device.is_init():
            self.connectionStatus = False
            return
        self.connectionStatus = True
        self.currentaddress = 0x00
        self.startSession = ""
        self.rsp_cache = {}
        self.device_type = self.device.device_type
        
        # Get device-specific settings
        self.settings = options.get_device_settings(self.device_type)

    def request(self, req, positive='', cache=True, serviceDelay="0"):
        req_as_bytes = array.array('B', [int("0x" + a, 16) for a in req.split(" ")])
        self.device.set_data(req_as_bytes)
        # Use device-specific timeout from settings
        timeout_ms = int(self.settings.get('timeout', 4) * 1000)  # Convert to milliseconds
        return self.device.get_buffer(timeout_ms)

    def close_protocol(self):
        pass

    def start_session_can(self, start_session):
        self.startSession = start_session
        self.device.set_data(self.startSession)
        retcode = self.device.get_data()  # Fixed: use self.device instead of self.data
        if retcode.startswith('50'):
            return True
        return False

    def init_can(self):
        self.device.set_can_mode_isotp()
        
        # ELS27 V5 specific initialization for CAN pins 12-13
        if self.device_type == "els27" and "V5" in self.device.descriptor.upper():
            try:
                print(_("Configuring ELS27 V5 CAN pins (12-13)"))
                # ELS27 V5 specific setup for CAN pins 12-13
                # This may require device-specific vendor requests
                self.device.set_vendor_request(0xFF, 0x12)  # Set CAN pin 12
                self.device.set_vendor_request(0xFE, 0x13)  # Set CAN pin 13
                print(_("ELS27 V5 CAN pin configuration complete"))
            except Exception as e:
                print(f"ELS27 V5 configuration warning: {e}")

    def clear_cache(self):
        ''' Clear L2 cache before screen update
        '''
        self.rsp_cache = {}

    def set_can_addr(self, addr, ecu, canline=0):
        if 'idTx' in ecu and 'idRx' in ecu:
            TXa = ecu['idTx']
            RXa = ecu['idRx']
            # self.currentaddress = get_can_addr(TXa) // TODO: https://github.com/cedricp/ddt4all/pull/1734
            self.currentaddress = addr
        elif get_can_addr(addr) is not None and get_can_addr_snat(addr) is not None:
            TXa = get_can_addr(addr)
            RXa = get_can_addr_snat(addr)
            # self.currentaddress = TXa // TODO: https://github.com/cedricp/ddt4all/pull/1734
            self.currentaddress = addr
        elif get_can_addr_ext(addr) is not None and get_can_addr_snat_ext(addr) is not None:
            TXa = get_can_addr_ext(addr)
            RXa = get_can_addr_snat_ext(addr)
            # self.currentaddress = TXa // TODO: https://github.com/cedricp/ddt4all/pull/1734
            self.currentaddress = addr
        else:
            return

        self.device.set_tx_addr(TXa)
        self.device.set_rx_addr(RXa)



if __name__ == '__main__':
    dev = OBDDevice()
    dev.init_can()
    dev.set_can_addr(26, {})
    print(dev.start_session_can("10C0"))