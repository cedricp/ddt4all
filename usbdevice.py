# -*- coding: utf-8 -*-
import usb
import elm
import array, time

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
REQUEST_TYPE_SEND = usb.util.build_request_type(usb.util.CTRL_OUT,
                                                usb.util.CTRL_TYPE_CLASS,
                                                usb.util.CTRL_RECIPIENT_DEVICE)
REQUEST_TYPE_RECV = usb.util.build_request_type(usb.util.CTRL_IN,
                                                usb.util.CTRL_TYPE_CLASS,
                                                usb.util.CTRL_RECIPIENT_DEVICE)
class UsbCan:
    def __init__(self):
        self.device = None
        self.descriptor = ""
        self.init()

    def init(self):
        self.device = usb.core.find(idVendor=0x16c0, idProduct=0x05df)
        if self.device:
            self.descriptor = self.get_string_descriptor()
            print("Found USB adapter : %s" % self.descriptor)
            return True

        self.device = None
        return False

    def is_init(self):
        return self.device is not None

    def get_string_descriptor(self, index):
        response = self.device.ctrl_transfer(usb.util.ENDPOINT_IN,
                                        usb.legacy.REQ_GET_DESCRIPTOR,
                                        (usb.util.DESC_TYPE_STRING << 8) | index,
                                        0,  # language id
                                        255)  # length
        return response[2:].tostring().decode('utf-16')

    def get_vendor_request(self, vendor_id):
        bytes = self.device.ctrl_transfer(bmRequestType=usb.util.CTRL_IN | usb.util.CTRL_TYPE_VENDOR,
                                          bRequest=CUSTOM_RQ_GET_STATUS,
                                          wIndex=vendor_id)
        return bytes

    def set_vendor_request(self, vendor_id, value):
        bytes = self.device.ctrl_transfer(bmRequestType=usb.util.CTRL_OUT | usb.util.CTRL_TYPE_VENDOR,
                                          bRequest=CUSTOM_RQ_SET_STATUS,
                                          wIndex=vendor_id,
                                          wValue=value)
        return bytes

    def get_data(self, length=511):
        response = self.device.ctrl_transfer(bmRequestType=REQUEST_TYPE_RECV,
                                             bRequest=USBRQ_HID_GET_REPORT,
                                             data_or_wLength=length)
        return " ".join([ hex(b)[2:].upper().zfill(2) for b in response])

    def set_data(self, data):
        response = self.device.ctrl_transfer(bmRequestType=REQUEST_TYPE_SEND,
                                             bRequest=USBRQ_HID_GET_REPORT,
                                             data_or_wLength=data)
        return " ".join([ hex(b)[2:].upper().zfill(2) for b in response])

    def get_read_buffer_length(self):
        ret = self.set_vendor_request(VENDOR_CAN_RX_SIZE, 0)
        length = int("0x" + "".join([ hex(b)[2:].upper().zfill(2) for b in ret]), 16)
        if length == 0xFFFF:
            return -1
        if length == 0xFFFE:
            return 0
        return length

    def get_buffer(self, timeout = 500):
        start = time.time()
        while 1:
            leng = self.get_read_buffer_length()
            if leng == -1:
                return("WRONG RESPONSE")
            if leng > 0:
                break
            if time.time() - start > timeout / 1000:
                return("TIMEOUT")
        return self.get_data(leng)


    def set_tx_addr(self, addr):
        self.set_vendor_request(VENDOR_CAN_TX, addr)

    def set_rx_addr(self, addr):
        self.set_vendor_request(VENDOR_CAN_RX, addr)

    def get_tx_addr(self, addr):
        return self.get_vendor_request(VENDOR_CAN_TX, addr)

    def get_rx_addr(self, addr):
        return self.get_vendor_request(VENDOR_CAN_RX, addr)

    def set_can_mode_isotp(self):
        self.set_vendor_request(VENDOR_CAN_MODE, CAN_ISOTP_MODE)

    def set_can_mode_monitor(self):
        self.set_vendor_request(VENDOR_CAN_MODE, CAN_MONITOR_MODE)


class OBDDevice:
    def __init__(self):
        self.device = UsbCan()
        if self.device is None:
            self.connectionStatus = False
            return
        self.connectionStatus = True
        self.currentaddress = 0x00
        self.startSession = ""
        self.rsp_cache = {}

    def request(self, req, positive='', cache=True, serviceDelay="0"):
        req_as_bytes = array.array('B', [int("0x"+a, 16) for a in req.split(" ")])
        self.device.set_data(req_as_bytes)
        return self.device.get_buffer(500)

    def close_protocol(self):
         pass

    def start_session_can(self, start_session):
        self.startSession = start_session
        self.device.set_data(self.startSession)
        retcode = self.data.get_data()
        if retcode.startswith('50'):
            return True
        return False

    def init_can(self):
        self.device.set_can_mode_isotp()

    def clear_cache(self):
        ''' Clear L2 cache before screen update
        '''
        self.rsp_cache = {}

    def set_can_addr(self, addr, ecu, canline=0):
        if 'idTx' in ecu and 'idRx' in ecu:
            TXa = ecu['idTx']
            RXa = ecu['idRx']
            self.currentaddress = elm.ELM.get_can_addr(TXa)
        else:
            TXa = elm.dnat[addr]
            RXa = elm.snat[addr]

        self.device.set_tx_addr(TXa)
        self.device.set_rx_addr(RXa)

if __name__ == '__main__':
    dev = OBDDevice()
    dev.init_can()
    dev.set_can_addr(26, {})
    print dev.start_session_can("10C0")

