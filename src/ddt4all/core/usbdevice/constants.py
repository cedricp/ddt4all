from usb import util

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