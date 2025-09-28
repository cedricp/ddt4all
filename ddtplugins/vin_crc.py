# -*- coding: utf-8 -*-

# Plugin to compute CRC from VIN
# (c) 2017

from binascii import hexlify
from binascii import unhexlify

import PyQt5.QtCore as core
import PyQt5.QtWidgets as gui
import crcmod.predefined

import options

_ = options.translator('ddt4all')

plugin_name = _("CRC calculator")
category = _("VIN")
# We need an ELM to work
need_hw = False


def calc_crc(vin=None):
    VIN = hexlify(bytes(vin, 'utf-8'))
    VININT = unhexlify(VIN)

    crc16 = crcmod.predefined.mkCrcFun('x-25')
    crcle = hex(crc16(VININT))[2:].upper().zfill(4)
    print(crcle)
    #    crcle = crc16.hexdigest()
    # Seems that computed CRC is returned in little endian way
    # Convert it to big endian
    return crcle[2:4] + crcle[0:2]


class CrcWidget(gui.QDialog):
    def __init__(self):
        super(CrcWidget, self).__init__(None)
        layout = gui.QVBoxLayout()
        self.input = gui.QLineEdit()
        self.output = gui.QLineEdit()
        self.output.setStyleSheet("QLineEdit { color: rgb(255, 0, 0); }")
        info = gui.QLabel(_("CRC CALCULATOR"))
        info.setAlignment(core.Qt.AlignHCenter)
        self.output.setAlignment(core.Qt.AlignHCenter)
        layout.addWidget(info)
        layout.addWidget(self.input)
        layout.addWidget(self.output)
        self.input.textChanged.connect(self.recalc)
        self.setLayout(layout)
        self.output.setReadOnly(True)

    def recalc(self):
        vin = str(self.input.text()).upper()
        crc = calc_crc(vin)
        self.output.setText('%s' % crc)


def plugin_entry():
    a = CrcWidget()
    a.exec_()
