import codecs
import string

import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets

class BitContainer(widgets.QFrame):
    def __init__(self, data, num, parent=None):
        super(BitContainer, self).__init__(parent)
        self.data = data
        self.setFrameStyle(widgets.QFrame.Sunken)
        self.setFrameShape(widgets.QFrame.Box)
        self.setFixedWidth(140)

        self.layout = widgets.QVBoxLayout()
        cblayout = widgets.QHBoxLayout()
        cblayout.setContentsMargins(0, 0, 0, 0)
        cblayout.setSpacing(0)
        data = int("0x" + data, 16)
        databin = bin(data)[2:].zfill(8)

        self.checkboxes = []
        for i in range(8):
            cb = widgets.QCheckBox()
            cb.setEnabled(False)
            if databin[i] == "1":
                cb.setChecked(True)
            self.checkboxes.append(cb)
            cblayout.addWidget(cb)
            cb.setStyleSheet("color: green")

        label = widgets.QLabel(str(num + 1).zfill(2))
        label.setAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)

        self.labelvaluehex = widgets.QLabel("$00")
        self.labelvaluehex.setAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)

        self.layout.addWidget(label)
        self.layout.addWidget(self.labelvaluehex)
        self.layout.addLayout(cblayout)
        self.setLayout(self.layout)

    def set_value_hex(self, val):
        char = decode_hex(val)
        repr = ""
        if ord(char) < 127 and str(char) in string.printable:
            repr = " [" + char + "]"

        self.labelvaluehex.setText("<font color='green'>$" + val.zfill(2) + repr + "</font>")

    def set_byte_value(self, byte):
        if 'L' in byte:
            byte = byte.replace('L', '')

        binary = bin(int("0x" + byte, 16))[2:].zfill(8)
        for i in range(8):
            if binary[i] == "1":
                self.checkboxes[i].setChecked(True)
            else:
                self.checkboxes[i].setChecked(False)

        self.set_value_hex(byte)

    def set_byte(self, byte):
        if 'L' in byte:
            byte = byte.replace('L', '')

        binary = bin(int("0x" + byte, 16))[2:].zfill(8)
        for i in range(8):
            if binary[i] == "1":
                self.checkboxes[i].setStyleSheet("border: 1px solid #00FF00;")
            else:
                self.checkboxes[i].setStyleSheet("border: 1px solid #FFFFFF;")


def decode_hex(string):
    hex_decoder = codecs.getdecoder("hex_codec")
    return hex_decoder(string)[0]