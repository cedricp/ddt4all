#!/usr/bin/python3
# -*- coding: utf-8 -*-
import array
import time

from usb import util, core, legacy

import elm
import options

# HID TYPES
USBRQ_HID_GET_REPORT = 0x01
USBRQ_HID_SET_REPORT = 0x09
USB_HID_REPORT_TYPE_FEATURE = 0x02

# CUSTOM REQUESTS TYPES
CUSTOM_RQ_SET_STATUS = 0x01
CUSTOM_RQ_GET_STATUS = 0x02

# VENDOR TYPES
VENDOR_CAN_MODE = 0x00
VENDOR_CAN_TX = 0x01
VENDOR_CAN_RX = 0x02
VENDOR_CAN_RX_SIZE = 0x03

# CAN MODE
CAN_MONITOR_MODE = 0x00
CAN_ISOTP_MODE = 0x01

# HELPERS
REQUEST_TYPE_SEND = util.build_request_type(util.CTRL_OUT,
                                            util.CTRL_TYPE_CLASS,
                                            util.CTRL_RECIPIENT_DEVICE)
REQUEST_TYPE_RECV = util.build_request_type(util.CTRL_IN,
                                            util.CTRL_TYPE_CLASS,
                                            util.CTRL_RECIPIENT_DEVICE)

_ = options.translator('ddt4all')


class UsbCan:
    def __init__(self):
        self.device = None
        self.descriptor = ""
        self.device_type = "unknown"
        self.init()

    def init(self):
        # Try to find various USB CAN adapters
        # Standard USB CAN adapter
        self.device = core.find(idVendor=0x16c0, idProduct=0x05df)
        if self.device:
            self.descriptor = self.get_string_descriptor()
            self.device_type = "usbcan"
            print(_("Found USB adapter:") + " %s" % self.descriptor)
            return True
        
        # Try various USB OBD-II adapters that may support direct USB communication
        usb_adapters = [
            # ELS27 V5 and variants
            (0x0403, 0x6001, "FTDI based ELS27/ELM327"),
            (0x10c4, 0xea60, "CP210x based ELS27/ELM327"), 
            (0x1a86, 0x7523, "CH340 based ELS27/ELM327"),
            (0x067b, 0x2303, "PL2303 based ELS27/ELM327"),
            # VGate USB CAN adapters
            (0x1209, 0x0001, "VGate USB CAN"),
            (0x04d8, 0x000a, "VGate iCar Pro USB"),
            # ObdLink USB variants
            (0x0403, 0x6015, "ObdLink USB CAN"),
            (0x16d0, 0x0498, "ObdLink Direct USB"),
            # Vlinker USB variants
            (0x1a86, 0x7584, "Vlinker USB CAN"),
            (0x0403, 0x6010, "Vlinker FTDI USB"),
        ]
        
        for vid, pid, desc in usb_adapters:
            self.device = core.find(idVendor=vid, idProduct=pid)
            if self.device:
                try:
                    descriptor_str = self.get_string_descriptor()
                    # Determine device type from descriptor content
                    if "ELS27" in descriptor_str.upper():
                        self.device_type = "els27"
                        device_name = "ELS27 V5" if "V5" in descriptor_str.upper() else "ELS27"
                    elif "VGATE" in descriptor_str.upper() or "ICAR" in descriptor_str.upper():
                        self.device_type = "vgate"  
                        device_name = "VGate"
                    elif "VLINKER" in descriptor_str.upper():
                        self.device_type = "vlinker"
                        device_name = "Vlinker"
                    elif "OBDLINK" in descriptor_str.upper():
                        self.device_type = "obdlink"
                        device_name = "ObdLink"
                    elif "ELM327" in descriptor_str.upper():
                        self.device_type = "elm327"
                        device_name = "ELM327"
                    else:
                        self.device_type = "els27"  # Default to ELS27
                        device_name = "ELS27"
                    
                    self.descriptor = f"{device_name}: {descriptor_str}"
                    print(_("Found USB adapter:") + " %s" % self.descriptor)
                    return True
                except:
                    # If we can't get descriptor, determine type from VID/PID and description
                    if "ELS27" in desc or "ELM327" in desc:
                        self.device_type = "els27"
                        device_name = "ELS27 V5"
                    elif "VGate" in desc:
                        self.device_type = "vgate"
                        device_name = "VGate"
                    elif "Vlinker" in desc:
                        self.device_type = "vlinker" 
                        device_name = "Vlinker"
                    elif "ObdLink" in desc:
                        self.device_type = "obdlink"
                        device_name = "ObdLink"
                    else:
                        self.device_type = "usbcan"
                        device_name = "USB CAN"
                    
                    self.descriptor = f"{device_name} (VID:{vid:04X} PID:{pid:04X})"
                    print(_("Found USB adapter:") + " %s" % self.descriptor)
                    return True

        self.device = None
        return False

    def is_init(self):
        return self.device is not None

    def get_string_descriptor(self):
        try:
            response = self.device.ctrl_transfer(util.ENDPOINT_IN,
                                                 legacy.REQ_GET_DESCRIPTOR,
                                                 util.DESC_TYPE_STRING,
                                                 0,  # language id
                                                 255)  # length
            if len(response) >= 2:
                return response[2:].tostring().decode('utf-16')
            else:
                return "USB Device"
        except Exception as e:
            # Fallback for devices with limited descriptor support
            print(f"Warning: Could not read string descriptor: {e}")
            return "USB OBD Device"

    def get_vendor_request(self, vendor_id):
        try:
            bytes = self.device.ctrl_transfer(bmRequestType=util.CTRL_IN | util.CTRL_TYPE_VENDOR,
                                              bRequest=CUSTOM_RQ_GET_STATUS,
                                              wIndex=vendor_id)
            return bytes
        except Exception as e:
            print(f"Warning: Vendor request failed: {e}")
            return b''

    def set_vendor_request(self, vendor_id, value):
        try:
            bytes = self.device.ctrl_transfer(bmRequestType=util.CTRL_OUT | util.CTRL_TYPE_VENDOR,
                                              bRequest=CUSTOM_RQ_SET_STATUS,
                                              wIndex=vendor_id,
                                              wValue=value)
            return bytes
        except Exception as e:
            print(f"Warning: Vendor request failed: {e}")
            return b''

    def get_data(self, length=511):
        response = self.device.ctrl_transfer(bmRequestType=REQUEST_TYPE_RECV,
                                             bRequest=USBRQ_HID_GET_REPORT,
                                             data_or_wLength=length)
        return " ".join([hex(b)[2:].upper().zfill(2) for b in response])

    def set_data(self, data):
        response = self.device.ctrl_transfer(bmRequestType=REQUEST_TYPE_SEND,
                                             bRequest=USBRQ_HID_GET_REPORT,
                                             data_or_wLength=data)
        return " ".join([hex(b)[2:].upper().zfill(2) for b in response])

    def get_read_buffer_length(self):
        ret = self.set_vendor_request(VENDOR_CAN_RX_SIZE, 0)
        length = int("0x" + "".join([hex(b)[2:].upper().zfill(2) for b in ret]), 16)
        if length == 0xFFFF:
            return -1
        if length == 0xFFFE:
            return 0
        return length

    def get_buffer(self, timeout=500):
        start = time.time()
        while 1:
            leng = self.get_read_buffer_length()
            if leng == -1:
                return ("WRONG RESPONSE")
            if leng > 0:
                break
            if time.time() - start > timeout / 1000:
                return ("TIMEOUT")
        return self.get_data(leng)

    def set_tx_addr(self, addr):
        self.set_vendor_request(VENDOR_CAN_TX, addr)

    def set_rx_addr(self, addr):
        self.set_vendor_request(VENDOR_CAN_RX, addr)

    def get_tx_addr(self):
        return self.get_vendor_request(VENDOR_CAN_TX)

    def get_rx_addr(self):
        return self.get_vendor_request(VENDOR_CAN_RX)

    def set_can_mode_isotp(self):
        self.set_vendor_request(VENDOR_CAN_MODE, CAN_ISOTP_MODE)

    def set_can_mode_monitor(self):
        self.set_vendor_request(VENDOR_CAN_MODE, CAN_MONITOR_MODE)


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
            self.currentaddress = elm.get_can_addr(TXa)
        elif elm.get_can_addr(addr) is not None and elm.get_can_addr_snat(addr) is not None:
            TXa = elm.get_can_addr(addr)
            RXa = elm.get_can_addr_snat(addr)
            self.currentaddress = TXa
        elif elm.get_can_addr_ext(addr) is not None and elm.get_can_addr_snat_ext(addr) is not None:
            TXa = elm.get_can_addr_ext(addr)
            RXa = elm.get_can_addr_snat_ext(addr)
            self.currentaddress = TXa
        else:
            return

        self.device.set_tx_addr(TXa)
        self.device.set_rx_addr(RXa)


if __name__ == '__main__':
    dev = OBDDevice()
    dev.init_can()
    dev.set_can_addr(26, {})
    print(dev.start_session_can("10C0"))
