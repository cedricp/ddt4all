

import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets

import ddt4all.options as options
from ddt4all.ui.data_editor.hex_line_edit import HexLineEdit
from ddt4all.ui.data_editor.hex_spin_box import HexSpinBox

_ = options.translator('ddt4all')

class EcuParamEditor(widgets.QFrame):
    def __init__(self, parent=None):
        super(EcuParamEditor, self).__init__(parent)
        self.ecurequestsparser = None
        self.targets = None

        layoutv = widgets.QVBoxLayout()
        self.setLayout(layoutv)

        gridlayout = widgets.QGridLayout()
        self.protocolcombo = widgets.QComboBox()
        self.funcadressedit = HexSpinBox(False)

        self.protocolcombo.addItem("CAN")
        self.protocolcombo.addItem("KWP2000 Slow Init")
        self.protocolcombo.addItem("KWP2000 Fast Init")
        self.protocolcombo.addItem("ISO8")
        gridlayout.addWidget(widgets.QLabel(_("ECU Function address")), 0, 0)
        gridlayout.addWidget(self.funcadressedit, 0, 1)

        gridlayout.addWidget(widgets.QLabel(_("ECU Protocol")), 4, 0)
        gridlayout.addWidget(self.protocolcombo, 4, 1)
        self.addr1label = widgets.QLabel(_("Tool > Ecu ID (Hex)"))
        gridlayout.addWidget(self.addr1label, 1, 0)
        self.addr2label = widgets.QLabel(_("Ecu > Tool ID (Hex)"))
        gridlayout.addWidget(self.addr2label, 2, 0)
        gridlayout.addWidget(widgets.QLabel(_("Coding")), 3, 0)
        self.toolecuidbox = HexSpinBox()
        self.ecutoolidbox = HexSpinBox()
        self.codingcombo = widgets.QComboBox()
        self.codingcombo.addItem(_("Big Endian"))
        self.codingcombo.addItem(_("Little Endian"))
        gridlayout.addWidget(self.toolecuidbox, 1, 1)
        gridlayout.addWidget(self.ecutoolidbox, 2, 1)
        gridlayout.addWidget(self.codingcombo, 3, 1)
        gridlayout.setColumnStretch(3, 1)
        layoutv.addLayout(gridlayout)

        autoident_label = widgets.QLabel(_("ECU Auto identification"))
        autoident_label.setAlignment(core.Qt.AlignCenter)

        self.identtable = widgets.QTableWidget()
        self.identtable.setColumnCount(4)
        self.identtable.verticalHeader().hide()
        self.identtable.setSelectionBehavior(widgets.QAbstractItemView.SelectRows)
        self.identtable.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        self.identtable.itemSelectionChanged.connect(self.selection_changed)
        layoutv.addWidget(autoident_label)
        layoutv.addWidget(self.identtable)

        headerstrings = _("Diag version;Supplier;Soft;Version").split(";")
        self.identtable.setHorizontalHeaderLabels(headerstrings)

        inputayout = widgets.QHBoxLayout()
        self.inputdiag = HexLineEdit(2, False)
        self.inputsupplier = HexLineEdit(6, True)
        self.inputsoft = HexLineEdit(4, False)
        self.inputversion = HexLineEdit(4, False)
        self.addbutton = widgets.QPushButton(_("Add new"))
        self.delbutton = widgets.QPushButton(_("Delete selected"))
        inputayout.addWidget(widgets.QLabel(_("Diag version")))
        inputayout.addWidget(self.inputdiag)

        inputayout.addWidget(widgets.QLabel(_("Supplier")))
        inputayout.addWidget(self.inputsupplier)

        inputayout.addWidget(widgets.QLabel(_("Soft")))
        inputayout.addWidget(self.inputsoft)

        inputayout.addWidget(widgets.QLabel(_("Version")))
        inputayout.addWidget(self.inputversion)

        inputayout.addWidget(self.addbutton)
        inputayout.addWidget(self.delbutton)

        layoutv.addLayout(inputayout)

        self.toolecuidbox.valueChanged.connect(self.toolecu_changed)
        self.ecutoolidbox.valueChanged.connect(self.ecutool_changed)
        self.codingcombo.activated.connect(self.coding_changed)
        self.protocolcombo.activated.connect(self.protcol_changed)
        self.addbutton.clicked.connect(self.add_ident)
        self.delbutton.clicked.connect(self.del_ident)
        self.funcadressedit.valueChanged.connect(self.funcadress_changed)

        self.enable_view(False)

    def funcadress_changed(self):
        self.ecurequestsparser.funcaddr = hex(self.funcadressedit.value())[2:]

    def del_ident(self):
        selitems = self.identtable.selectedItems()
        if not len(selitems):
            return

        current_row = selitems[-1].row()
        if len(self.targets):
            self.targets.pop(current_row)

        self.init()

    def add_ident(self):
        diagversion = self.inputdiag.text()
        suppliercode = self.inputsupplier.text()
        soft = self.inputsoft.text()
        version = self.inputversion.text()

        protocol = "Undefined"
        if self.protocolcombo.currentIndex() == 0:
            protocol = u"DiagOnCAN"
        elif self.protocolcombo.currentIndex() == 1:
            protocol = u"KWP2000 FastInit MonoPoint"
        elif self.protocolcombo.currentIndex() == 2:
            protocol = u"KWP2000 Init 5 Baud Type I and II"
        elif self.protocolcombo.currentIndex() == 3:
            protocol = u"ISO8"

        ident = {
            "diagnotic_version": diagversion,
            "supplier_code": suppliercode,
            "protocol": protocol,
            "soft_version": soft,
            "version": version,
            "address": "",
            "group": "",
            "projects": []
        }

        self.targets.append(ident)

        self.init()

    def coding_changed(self):
        if self.codingcombo.currentIndex() == 0:
            self.ecurequestsparser.endianness = 'Big'
        else:
            self.ecurequestsparser.endianness = 'Little'
        self.init()

    def protcol_changed(self):
        if self.protocolcombo.currentIndex() == 0:
            self.ecurequestsparser.ecu_protocol = "CAN"
            self.toolecuidbox.set_can(True)
            self.ecutoolidbox.set_can(True)
            self.addr1label.setText(_("Tool > Ecu ID (Hex)"))
            self.addr2label.setText(_("Ecu > Tool ID (Hex)"))
        elif self.protocolcombo.currentIndex() == 1:
            self.ecurequestsparser.ecu_protocol = "KWP2000"
            self.ecurequestsparser.fastinit = False
            self.toolecuidbox.set_can(False)
            self.ecutoolidbox.set_can(False)
            self.addr1label.setText("KW1")
            self.addr2label.setText("KW2")
        elif self.protocolcombo.currentIndex() == 2:
            self.ecurequestsparser.ecu_protocol = "KWP2000"
            self.ecurequestsparser.fastinit = True
            self.addr1label.setText("KW1")
            self.addr2label.setText("KW2")
            self.toolecuidbox.set_can(False)
            self.ecutoolidbox.set_can(False)
        elif self.protocolcombo.currentIndex() == 3:
            self.ecurequestsparser.ecu_protocol = "ISO8"
            self.ecurequestsparser.fastinit = False
            self.addr1label.setText("KW1")
            self.addr2label.setText("KW2")
            self.toolecuidbox.set_can(False)
            self.ecutoolidbox.set_can(False)

    def toolecu_changed(self):
        if self.ecurequestsparser.ecu_protocol == "CAN":
            self.ecurequestsparser.ecu_send_id = hex(self.toolecuidbox.value())[2:]
        else:
            self.ecurequestsparser.kw1 = hex(self.toolecuidbox.value())[2:]

    def ecutool_changed(self):
        if self.ecurequestsparser.ecu_protocol == "CAN":
            self.ecurequestsparser.ecu_recv_id = hex(self.ecutoolidbox.value())[2:]
        else:
            self.ecurequestsparser.kw2 = hex(self.ecutoolidbox.value())[2:]

    def set_ecu(self, ecu):
        self.ecurequestsparser = ecu
        self.enable_view(True)
        self.init()

    def enable_view(self, enable):
        children = self.children()
        for c in children:
            if isinstance(c, widgets.QWidget):
                c.setEnabled(enable)

    def set_targets(self, targets):
        self.targets = targets
        self.init()

    def selection_changed(self):
        selitems = self.identtable.selectedItems()
        if not len(selitems):
            return

        current_row = selitems[-1].row()
        diagversion = self.identtable.item(current_row, 0).text()
        suppliercode = self.identtable.item(current_row, 1).text()
        soft = self.identtable.item(current_row, 2).text()
        version = self.identtable.item(current_row, 3).text()

        self.inputdiag.setText(diagversion)
        self.inputsupplier.setText(suppliercode)
        self.inputsoft.setText(soft)
        self.inputversion.setText(version)

    def init(self):
        if self.targets is None:
            return

        if not self.ecurequestsparser:
            return

        if self.ecurequestsparser.ecu_protocol == "CAN":
            self.toolecuidbox.set_can(True)
            self.ecutoolidbox.set_can(True)
            self.protocolcombo.setCurrentIndex(0)
        elif self.ecurequestsparser.ecu_protocol == "KWP2000":
            self.toolecuidbox.set_can(False)
            self.ecutoolidbox.set_can(False)
            if self.ecurequestsparser.fastinit:
                self.protocolcombo.setCurrentIndex(2)
            else:
                self.protocolcombo.setCurrentIndex(1)

        elif self.ecurequestsparser.ecu_protocol == "ISO8":
            self.toolecuidbox.set_can(False)
            self.ecutoolidbox.set_can(False)
            self.protocolcombo.setCurrentIndex(3)

        self.protcol_changed()

        self.funcadressedit.setValue(int("0x" + self.ecurequestsparser.funcaddr, 16))

        if self.ecurequestsparser.endianness == 'Little':
            self.codingcombo.setCurrentIndex(1)
        else:
            self.codingcombo.setCurrentIndex(0)

        if self.ecurequestsparser.ecu_protocol == "CAN":
            self.toolecuidbox.setValue(int("0x" + str(self.ecurequestsparser.ecu_send_id), 16))
            self.ecutoolidbox.setValue(int("0x" + str(self.ecurequestsparser.ecu_recv_id), 16))
        else:
            self.toolecuidbox.setValue(int("0x" + str(self.ecurequestsparser.kw1), 16))
            self.ecutoolidbox.setValue(int("0x" + str(self.ecurequestsparser.kw2), 16))

        self.identtable.clearContents()

        count = 0
        self.identtable.setRowCount(len(self.targets))
        for target in self.targets:
            if 'diagnostic_version' in target:
                self.identtable.setItem(count, 0, widgets.QTableWidgetItem(target['diagnostic_version']))
            else:
                self.identtable.setItem(count, 0, widgets.QTableWidgetItem(target['diagnotic_version']))
            self.identtable.setItem(count, 1, widgets.QTableWidgetItem(target['supplier_code']))
            self.identtable.setItem(count, 2, widgets.QTableWidgetItem(target['soft_version']))
            self.identtable.setItem(count, 3, widgets.QTableWidgetItem(target['version']))
            count += 1

        self.identtable.resizeColumnsToContents()
        self.identtable.resizeRowsToContents()
        self.identtable.selectRow(0)
