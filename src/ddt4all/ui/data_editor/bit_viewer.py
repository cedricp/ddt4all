import PyQt5.QtWidgets as widgets

from ddt4all.ui.data_editor.bit_container import BitContainer

class BitViewer(widgets.QScrollArea):
    def __init__(self, parent=None):
        super(BitViewer, self).__init__(parent)
        self.bc = []
        self.mainwidget = None

    def init(self, num):
        if self.mainwidget:
            self.mainwidget.setParent(None)
            self.mainwidget.deleteLater()

        self.mainwidget = widgets.QWidget()
        self.layout = widgets.QHBoxLayout()
        self.layout.setSpacing(2)
        self.bc = []

        for i in range(num):
            bc = BitContainer("00", i)
            self.bc.append(bc)
            self.layout.addWidget(bc)

        self.mainwidget.setLayout(self.layout)
        self.setWidget(self.mainwidget)

    def set_bytes_value(self, byte_list):
        num = len(byte_list)

        for i in range(num):
            if i >= len(self.bc):
                break
            self.bc[i].set_byte_value(byte_list[i])

        for i in range(num, len(self.bc)):
            self.bc[i].set_byte_value("00")

    def set_bytes(self, byte_list):
        num = len(byte_list)

        for i in range(num):
            if i >= len(self.bc):
                break
            self.bc[i].set_byte(byte_list[i])

        for i in range(num, len(self.bc)):
            self.bc[i].set_byte("00")

