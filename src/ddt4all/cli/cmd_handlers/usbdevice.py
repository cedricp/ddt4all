import argparse

from ddt4all.core.usbdevice.obd_device import OBDDevice

def cmd_usbdevice(args: argparse.Namespace) -> int:
    dev = OBDDevice()
    dev.init_can()
    dev.set_can_addr(26, {})
    print(dev.start_session_can("10C0"))