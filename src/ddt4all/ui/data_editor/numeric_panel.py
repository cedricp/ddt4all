import PyQt5.QtWidgets as widgets

import ddt4all.options as options

_ = options.translator('ddt4all')

class NumericPanel(widgets.QFrame):
    def __init__(self, dataitem, parent=None):
        super(NumericPanel, self).__init__(parent)
        self.setFrameStyle(widgets.QFrame.Sunken)
        self.setFrameShape(widgets.QFrame.Box)
        self.data = dataitem

        layout = widgets.QGridLayout()
        labelnob = widgets.QLabel(_("Number of bit"))
        lableunit = widgets.QLabel(_("Unit"))
        labelsigned = widgets.QLabel(_("Signed"))
        labelformat = widgets.QLabel(_("Format"))
        labeldoc = widgets.QLabel(_("Value = (AX+B) / C"))
        labela = widgets.QLabel("A")
        labelb = widgets.QLabel("B")
        labelc = widgets.QLabel("C")

        layout.addWidget(labelnob, 0, 0)
        layout.addWidget(lableunit, 1, 0)
        layout.addWidget(labelsigned, 2, 0)
        layout.addWidget(labelformat, 3, 0)
        layout.addWidget(labeldoc, 4, 0)
        layout.addWidget(labela, 5, 0)
        layout.addWidget(labelb, 6, 0)
        layout.addWidget(labelc, 7, 0)
        layout.setRowStretch(8, 1)

        self.inputnob = widgets.QSpinBox()
        self.inputnob.setRange(1, 32)
        self.inputunit = widgets.QLineEdit()
        self.inputsigned = widgets.QCheckBox()
        self.inputformat = widgets.QLineEdit()
        self.inputa = widgets.QDoubleSpinBox()
        self.inputb = widgets.QDoubleSpinBox()
        self.inputc = widgets.QDoubleSpinBox()
        self.inputc.setRange(-1000000, 1000000)
        self.inputb.setRange(-1000000, 1000000)
        self.inputa.setRange(-1000000, 1000000)
        self.inputa.setDecimals(4)
        self.inputb.setDecimals(4)
        self.inputc.setDecimals(4)

        layout.addWidget(self.inputnob, 0, 1)
        layout.addWidget(self.inputunit, 1, 1)
        layout.addWidget(self.inputsigned, 2, 1)
        layout.addWidget(self.inputformat, 3, 1)
        layout.addWidget(self.inputa, 5, 1)
        layout.addWidget(self.inputb, 6, 1)
        layout.addWidget(self.inputc, 7, 1)

        self.setLayout(layout)

        self.init()

    def validate(self):
        self.data.scaled = True
        self.data.bitscount = self.inputnob.value()
        self.data.unit = self.inputunit.text()
        self.data.signed = self.inputsigned.isChecked()
        self.data.format = self.inputformat.text()
        self.data.step = self.inputa.value()
        self.data.offset = self.inputb.value()
        self.data.divideby = self.inputc.value()
        self.data.bytesascii = False
        self.data.items = {}
        self.data.lists = {}

    def init(self):
        if self.data is None:
            return
        self.inputnob.setValue(self.data.bitscount)
        self.inputunit.setText(self.data.unit)
        self.inputsigned.setChecked(self.data.signed)
        self.inputformat.setText(self.data.format)
        self.inputa.setValue(self.data.step)
        self.inputb.setValue(self.data.offset)
        self.inputc.setValue(self.data.divideby)

