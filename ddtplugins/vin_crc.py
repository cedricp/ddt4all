# -*- coding: utf-8 -*-

# Plugin to compute CRC from VIN
# (c) 2017

import crcmod
from binascii import unhexlify


import PyQt4.QtGui as gui
import PyQt4.QtCore as core

plugin_name = "CRC calculator"
category = "VIN"
# We need an ELM to work
need_hw = False

def calc_crc(vin=None):
    VIN=vin.encode("hex")
    VININT=unhexlify(VIN)

    crc16 = crcmod.predefined.Crc('x-25')
    crc16.update(VININT)
    crcle = crc16.hexdigest()
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
        info = gui.QLabel("CRC CALCULATOR")
        info.setAlignment(core.Qt.AlignHCenter)
        self.output.setAlignment(core.Qt.AlignHCenter)
        layout.addWidget(info)
        layout.addWidget(self.input)
        layout.addWidget(self.output)
        self.input.textChanged.connect(self.recalc)
        self.setLayout(layout)
        self.output.setReadOnly(True)

    def recalc(self):
        vin = str(self.input.text().toAscii()).upper()
        crc = calc_crc(vin)
        self.output.setText('%s' % crc)


def plugin_entry():
    a = CrcWidget()
    a.exec_()
