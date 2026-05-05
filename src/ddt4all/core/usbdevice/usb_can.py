import time

try:
    from usb import (
        util,
        core,
        legacy
    )
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False

from ddt4all.core.usbdevice.constants import (
    CAN_ISOTP_MODE,
    CAN_MONITOR_MODE,
    CUSTOM_RQ_GET_STATUS,
    CUSTOM_RQ_SET_STATUS,
    REQUEST_TYPE_RECV,
    REQUEST_TYPE_SEND,
    USBRQ_HID_GET_REPORT,
    VENDOR_CAN_MODE,
    VENDOR_CAN_RX,
    VENDOR_CAN_RX_SIZE,
    VENDOR_CAN_TX,
)
import ddt4all.options as options

_ = options.translator('ddt4all')

class UsbCan:
    def __init__(self):
        self.device = None
        self.descriptor = ""
        self.device_type = "unknown"
        self.init()

    def init(self):
        # Check if USB is available before attempting device detection
        if not USB_AVAILABLE:
            return False
        
        # Test if USB backend is available before attempting device detection
        try:
            import usb.backend.libusb1
            backend = usb.backend.libusb1.get_backend()
            if backend is None:
                return False
        except ImportError:
            return False
            
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
            # DERLEK USB-DIAG adapters
            (0x0483, 0x5740, "DERLEK USB-DIAG2"),
            (0x0483, 0x5741, "DERLEK USB-DIAG3"),
            # Bosch MTS adapters (RNM Manager compatible)
            (0x108c, 0x0156, "Bosch MTS 6531"),
            (0x108c, 0x0157, "Bosch MTS 6532"),
            (0x108c, 0x0158, "Bosch MTS 6533"),
            (0x108c, 0x0159, "Bosch MTS 6534"),
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
                    elif "DERLEK" in descriptor_str.upper() or "DIAG" in descriptor_str.upper():
                        if "DIAG3" in descriptor_str.upper():
                            self.device_type = "derlek_usb_diag3"
                            device_name = "DERLEK USB-DIAG3"
                        else:
                            self.device_type = "derlek_usb_diag2"
                            device_name = "DERLEK USB-DIAG2"
                    elif "BOSCH" in descriptor_str.upper() or "MTS" in descriptor_str.upper():
                        self.device_type = "bosch_mts"
                        device_name = "Bosch MTS"
                    elif "ELM327" in descriptor_str.upper():
                        self.device_type = "elm327"
                        device_name = "ELM327"
                    else:
                        self.device_type = "els27"  # Default to ELS27
                        device_name = "ELS27"
                    
                    self.descriptor = f"{device_name}: {descriptor_str}"
                    print(_("Found USB adapter:") + " %s" % self.descriptor)
                    return True
                except Exception:
                    # If we can't get descriptor, determine type from VID/PID and description
                    if "ELS27" in desc or "ELM327" in desc:
                        self.device_type = "elm327"
                        device_name = "ELM327"
                    elif "VGATE" in desc:
                        self.device_type = "vgate"
                        device_name = "VGate"
                    elif "Vlinker" in desc:
                        self.device_type = "vlinker" 
                        device_name = "Vlinker"
                    elif "OBDLINK" in desc:
                        self.device_type = "obdlink"
                        device_name = "ObdLink"
                    elif "DERLEK" in desc or "DIAG" in desc:
                        if "DIAG3" in desc:
                            self.device_type = "derlek_usb_diag3"
                            device_name = "DERLEK USB-DIAG3"
                        else:
                            self.device_type = "derlek_usb_diag2"
                            device_name = "DERLEK USB-DIAG2"
                    elif "BOSCH" in desc or "MTS" in desc:
                        self.device_type = "bosch_mts"
                        device_name = "Bosch MTS"
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
        if not USB_AVAILABLE:
            return _("USB not available")
            
        try:
            response = self.device.ctrl_transfer(util.ENDPOINT_IN,
                                                 legacy.REQ_GET_DESCRIPTOR,
                                                 util.DESC_TYPE_STRING,
                                                 0,  # language id
                                                 255)  # length
            if len(response) >= 2:
                return response[2:].tostring().decode('utf-16')
            else:
                return _("USB Device")
        except Exception as e:
            # Fallback for devices with limited descriptor support
            print(_("Warning: Could not read string descriptor:") + f" {e}")
            return _("USB OBD Device")

    def get_vendor_request(self, vendor_id):
        try:
            bytes = self.device.ctrl_transfer(bmRequestType=util.CTRL_IN | util.CTRL_TYPE_VENDOR,
                                              bRequest=CUSTOM_RQ_GET_STATUS,
                                              wIndex=vendor_id)
            return bytes
        except Exception as e:
            print(_("Warning: Vendor request failed:") + f" {e}")
            return b''

    def set_vendor_request(self, vendor_id, value):
        try:
            bytes = self.device.ctrl_transfer(bmRequestType=util.CTRL_OUT | util.CTRL_TYPE_VENDOR,
                                              bRequest=CUSTOM_RQ_SET_STATUS,
                                              wIndex=vendor_id,
                                              wValue=value)
            return bytes
        except Exception as e:
            print(_("Warning: Vendor request failed:") + f" {e}")
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

