import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets

import ddt4all.options as options

_ = options.translator('ddt4all')

class NumericListPanel(widgets.QFrame):
    def __init__(self, dataitem, parent=None):
        super(NumericListPanel, self).__init__(parent)
        self.setFrameStyle(widgets.QFrame.Sunken)
        self.setFrameShape(widgets.QFrame.Box)
        self.data = dataitem

        layoutv = widgets.QVBoxLayout()
        layout = widgets.QGridLayout()
        labelnob = widgets.QLabel(_("Number of bits"))
        lablelsigned = widgets.QLabel(_("Signed"))
        newitem = widgets.QPushButton(_("Add item"))
        delitem = widgets.QPushButton(_("Del item"))

        newitem.clicked.connect(self.add_item)
        delitem.clicked.connect(self.def_item)

        layout.addWidget(labelnob, 0, 0)
        layout.addWidget(lablelsigned, 1, 0)
        layout.addWidget(newitem, 2, 0)
        layout.addWidget(delitem, 2, 1)

        self.inputnob = widgets.QSpinBox()
        self.inputnob.setRange(1, 32)
        self.inputsigned = widgets.QCheckBox()

        layout.addWidget(self.inputnob, 0, 1)
        layout.addWidget(self.inputsigned, 1, 1)

        layoutv.addLayout(layout)

        self.itemtable = widgets.QTableWidget()
        self.itemtable.setRowCount(1)
        self.itemtable.setColumnCount(2)
        self.itemtable.verticalHeader().hide()
        self.itemtable.setSelectionBehavior(widgets.QAbstractItemView.SelectRows)
        self.itemtable.setSelectionMode(widgets.QAbstractItemView.SingleSelection)

        layoutv.addWidget(self.itemtable)

        self.setLayout(layoutv)
        self.init()

    def add_item(self):
        value = -999
        self.itemtable.setRowCount(self.itemtable.rowCount() + 1)
        newrow = self.itemtable.rowCount() - 1
        spinvalue = widgets.QSpinBox()
        spinvalue.setRange(-1000000, 1000000)
        spinvalue.setValue(value)
        self.itemtable.setCellWidget(newrow, 0, spinvalue)
        self.itemtable.setItem(newrow, 1, widgets.QTableWidgetItem(_("New item")))
        self.itemtable.setItem(newrow, 0, widgets.QTableWidgetItem(str(value).zfill(5)))
        self.itemtable.resizeRowsToContents()
        self.itemtable.resizeColumnsToContents()

    def def_item(self):
        currentrow = self.itemtable.currentRow()
        if currentrow < 0:
            return

        self.itemtable.removeRow(currentrow)

    def validate(self):
        self.data.scaled = False
        self.data.bitscount = self.inputnob.value()
        self.data.unit = ""
        self.data.signed = self.inputsigned.isChecked()
        self.data.format = ""
        self.data.step = 1
        self.data.offset = 0
        self.data.divideby = 1
        self.data.bytesascii = False
        self.data.items = {}
        self.data.lists = {}

        for i in range(self.itemtable.rowCount()):
            key = self.itemtable.item(i, 1).text()
            val = self.itemtable.cellWidget(i, 0).value()
            while key in self.data.items:
                key += u"_"
            self.data.items[key] = val
            self.data.lists[val] = key

    def init(self):
        if not self.data:
            return

        self.itemtable.clear()

        keys = self.data.items.keys()
        self.itemtable.setRowCount(len(keys))

        self.inputsigned.setChecked(self.data.signed)
        self.inputnob.setValue(self.data.bitscount)

        count = 0
        for k, v in self.data.items.items():
            spinvalue = widgets.QSpinBox()
            spinvalue.setRange(-1000000, 1000000)
            spinvalue.setValue(int(v))
            self.itemtable.setCellWidget(count, 0, spinvalue)
            self.itemtable.setItem(count, 0, widgets.QTableWidgetItem(str(v).zfill(5)))
            self.itemtable.setItem(count, 1, widgets.QTableWidgetItem(k))
            count += 1

        headerstrings = _("Value;Text").split(";")
        self.itemtable.setHorizontalHeaderLabels(headerstrings)
        self.itemtable.resizeColumnsToContents()
        self.itemtable.resizeRowsToContents()
        self.itemtable.sortItems(0, core.Qt.AscendingOrder)
        # self.itemtable.setSortingEnabled(True)

