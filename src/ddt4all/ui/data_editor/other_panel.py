import PyQt5.QtWidgets as widgets

import ddt4all.options as options

_ = options.translator('ddt4all')

class OtherPanel(widgets.QFrame):
    def __init__(self, dataitem, parent=None):
        super(OtherPanel, self).__init__(parent)
        self.setFrameStyle(widgets.QFrame.Sunken)
        self.setFrameShape(widgets.QFrame.Box)
        self.data = dataitem

        layout = widgets.QGridLayout()
        labelnob = widgets.QLabel(_("Number of bytes"))
        lableunit = widgets.QLabel(_("Unit"))

        layout.addWidget(labelnob, 0, 0)
        layout.addWidget(lableunit, 1, 0)
        layout.setRowStretch(2, 1)

        self.inputnob = widgets.QSpinBox()
        self.inputnob.setRange(1, 10240)
        self.inputtype = widgets.QComboBox()
        self.inputtype.addItem("ASCII")
        self.inputtype.addItem("BCD/HEX")

        layout.addWidget(self.inputnob, 0, 1)
        layout.addWidget(self.inputtype, 1, 1)

        self.setLayout(layout)
        self.init()

    def validate(self):
        type = self.inputtype.currentIndex()
        self.data.scaled = False
        self.data.bytescount = self.inputnob.value()
        self.data.bitscount = self.data.bytescount * 8
        self.data.unit = ""
        self.data.signed = False
        self.data.format = ""
        self.data.step = 1
        self.data.offset = 0
        self.data.divideby = 1
        if type == 0:
            self.data.bytesascii = True
        else:
            self.data.bytesascii = False
        self.data.items = {}
        self.data.lists = {}

    def init(self):
        if self.data is None:
            return
        self.inputnob.setValue(self.data.bytescount)
        if self.data.bytesascii:
            self.inputtype.setCurrentIndex(0)
        else:
            self.inputtype.setCurrentIndex(1)
