import ecu, math, string
import PyQt4.QtGui as gui
import PyQt4.QtCore as core


class Bit_container(gui.QFrame):
    def __init__(self, data, num, parent=None):
        super(Bit_container, self).__init__(parent)
        self.data = data
        self.setFrameStyle(gui.QFrame.Sunken)
        self.setFrameShape(gui.QFrame.Box)
        self.setFixedWidth(130)

        self.layout = gui.QVBoxLayout()
        cblayout = gui.QHBoxLayout()
        cblayout.setContentsMargins(0, 0, 0, 0)
        cblayout.setSpacing(0)
        data = int("0x" + data, 16)
        databin = bin(data)[2:].zfill(8)

        self.checkboxes = []
        for i in range(8):
            cb = gui.QCheckBox()
            cb.setEnabled(False)
            if databin[i] == "1":
                cb.setChecked(True)
            self.checkboxes.append(cb)
            cblayout.addWidget(cb)
            cb.setStyleSheet("color: green")

        label = gui.QLabel(str(num+1).zfill(2))
        label.setAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)

        self.layout.addWidget(label)
        self.layout.addLayout(cblayout)
        self.setLayout(self.layout)

    def set_byte(self, byte):
        binary = bin(int("0x" + byte, 16))[2:].zfill(8)
        for i in range(8):
            if binary[i] == "1":
                self.checkboxes[i].setChecked(True)
            else:
                self.checkboxes[i].setChecked(False)


class Bit_viewer(gui.QScrollArea):
    def __init__(self, parent=None):
        super(Bit_viewer, self).__init__(parent)
        self.bc = []
        self.mainwidget = None

    def init(self, num):
        if self.mainwidget:
            self.mainwidget.setParent(None)
            self.mainwidget.deleteLater()

        self.mainwidget = gui.QWidget()
        self.layout = gui.QHBoxLayout()
        self.layout.setSpacing(2)
        self.bc = []

        for i in range(num):
            bc = Bit_container("00", i)
            self.bc.append(bc)
            self.layout.addWidget(bc)

        self.mainwidget.setLayout(self.layout)
        self.setWidget(self.mainwidget)

    def set_bytes(self, byte_list):
        num = len(byte_list)

        for i in range(num):
            self.bc[i].set_byte(byte_list[i])

        for i in range(num, len(self.bc)):
            self.bc[i].set_byte("00")


class checkBox(gui.QCheckBox):
    def __init__(self, data, parent=None):
        super(checkBox, self).__init__(parent)
        self.data = data
        if data.manualsend:
            self.setChecked(True)
        else:
            self.setChecked(False)

        self.stateChanged.connect(self.change)

    def change(self, state):
        print state
        if state:
            self.data.manualsend = True
        else:
            self.data.manualsend = False

class requestTable(gui.QTableWidget):
    def __init__(self, parent=None):
        super(requestTable, self).__init__(parent)
        self.ecureq = None
        self.sendbyteeditor = None
        self.rcvbyteeditor = None
        self.reqs = []
        self.setFixedWidth(350)
        self.setSelectionBehavior(gui.QAbstractItemView.SelectRows)
        self.setSelectionMode(gui.QAbstractItemView.SingleSelection)
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.currentreq = None

    def cellModified(self, r, c):
        if not self.ecureq:
            return

        if c == 0:
            newname = unicode(self.item(r, c).text().toUtf8(), encoding="UTF-8")
            self.ecureq[self.currentreq].name = newname
            self.ecureq[newname] = self.ecureq.pop(self.currentreq)

    def setSendByteEditor(self, sbe):
        self.sendbyteeditor = sbe
        self.cellClicked.connect(self.cellSel)

    def setReceiveByteEditor(self, rbe):
        self.rcvbyteeditor = rbe
        self.cellClicked.connect(self.cellSel)

    def cellSel(self, x, y):
        currenttext = unicode(self.item(x, 0).text().toUtf8(), encoding="UTF-8")
        self.sendbyteeditor.set_request(self.ecureq[currenttext])
        self.rcvbyteeditor.set_request(self.ecureq[currenttext])
        self.currentreq = currenttext

    def init(self, ecureq):
        try:
            self.cellChanged.disconnect()
        except:
            pass

        self.clear()
        self.ecureq = ecureq

        requestsk = self.ecureq.keys()
        numrows = len(requestsk)
        self.setRowCount(numrows)
        self.setColumnCount(2)

        self.setHorizontalHeaderLabels(core.QString("Request name;Manual").split(";"))

        count = 0
        for req in requestsk:
            request_inst = self.ecureq[req]
            #if not isinstance(request_inst, ecu.Ecu_request):
            #    continue

            manual = checkBox(request_inst)

            self.setItem(count, 0, gui.QTableWidgetItem(req))
            self.setCellWidget(count, 1, manual)

            count += 1

        self.setRowCount(count)
        self.sortItems(0, core.Qt.AscendingOrder)
        self.resizeColumnsToContents()
        self.cellChanged.connect(self.cellModified)

class paramEditor(gui.QFrame):
    """Manages send/receive requests"""
    def __init__(self, issend=True, parent=None):
        super(paramEditor, self).__init__(parent)
        self.send = issend
        self.setFrameStyle(gui.QFrame.Sunken)
        self.setFrameShape(gui.QFrame.Box)
        self.layoutv = gui.QVBoxLayout()

        if issend:
            self.labelreq = gui.QLabel("Send request bytes (HEX)")
        else:
            self.labelreq = gui.QLabel("Receive bytes (HEX)")
        self.inputreq = gui.QLineEdit()
        self.inputreq.textChanged.connect(self.request_changed)

        self.layoutv.addWidget(self.labelreq)
        self.layoutv.addWidget(self.inputreq)

        if not issend:
            rcv_lay = gui.QHBoxLayout()
            self.label_data_len = gui.QLabel("Data length")
            self.spin_data_len = gui.QSpinBox()
            self.label_shift_bytes = gui.QLabel("Shift byte count")
            self.spin_shift_byte = gui.QSpinBox()
            rcv_lay.addWidget(self.label_data_len)
            rcv_lay.addWidget(self.spin_data_len)
            rcv_lay.addWidget(self.label_shift_bytes)
            rcv_lay.addWidget(self.spin_shift_byte)
            self.layoutv.addLayout(rcv_lay)

            self.spin_shift_byte.valueChanged.connect(self.shift_bytes_change)
            self.spin_data_len.valueChanged.connect(self.data_len_change)

        self.setLayout(self.layoutv)

        self.table = gui.QTableWidget()
        self.table.setRowCount(50)
        self.table.setColumnCount(5)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(gui.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(gui.QAbstractItemView.SingleSelection)
        self.table.setShowGrid(False)
        self.layoutv.addWidget(self.table)
        self.ecufile = None
        self.current_request = None
        self.table.cellClicked.connect(self.cell_clicked)

        self.bitviewer = Bit_viewer()
        self.bitviewer.setFixedHeight(90)
        self.layoutv.addWidget(self.bitviewer)

    def cell_clicked(self, r, c):
        dataname = unicode(self.table.item(r, 0).text().toUtf8(), encoding="UTF-8")
        self.update_bitview(dataname)

    def update_bitview(self, dataname):
        bytes = self.current_request.minbytes
        if self.send:
            dataitem = self.current_request.sendbyte_dataitems[dataname]
        else:
            dataitem = self.current_request.dataitems[dataname]

        ecudata = self.ecufile.data[dataname]
        minbytes = dataitem.firstbyte + ecudata.bytescount
        if bytes < minbytes:
            bytes = minbytes

        bitscount = ecudata.bitscount
        valuetosend = hex(int("0b" + str("1" * bitscount), 2))[2:]

        if "L" in valuetosend:
            valuetosend = valuetosend.replace("L", "")

        bytesarray = ["00" for a in range(bytes)]
        bytesarray = ecudata.setValue(valuetosend, bytesarray, dataitem, self.current_request.endian, True)
        self.bitviewer.set_bytes(bytesarray)

    def set_ecufile(self, ef):
        self.ecufile = ef
        self.table.clear()
        self.inputreq.clear()

    def set_request(self, req):
        self.current_request = req
        self.init(req)

    def init(self, req):
        self.table.clear()
        if self.send:
            self.inputreq.setText(req.sentbytes)
        else:
            self.inputreq.setText(req.replybytes)

        if self.send:
            data = req.sendbyte_dataitems
        else:
            data = req.dataitems
        datak = data.keys()

        if not self.send:
            self.spin_shift_byte.setValue(req.shiftbytescount)
            self.spin_data_len.setValue(req.minbytes)

        headerstrings = core.QString("Data name;Start byte;Bit offset;Bit count;Endianess").split(";")
        self.table.setHorizontalHeaderLabels(headerstrings)

        bytescount = 0

        count = 0
        for k in datak:
            dataitem = data[k]
            ecudata = self.ecufile.data[dataitem.name]
            endian = dataitem.endian

            ln = dataitem.firstbyte + math.ceil(float(ecudata.bitscount) / 8.)
            if ln > bytescount:
                bytescount = ln

            endian_combo = gui.QComboBox()
            endian_combo.addItem("Little")
            endian_combo.addItem("Big")
            endian_combo.addItem("Inherits globals")

            if endian == "Big":
                endian_combo.setCurrentIndex(1)
            elif endian == "Little":
                endian_combo.setCurrentIndex(0)
            else:
                endian_combo.setCurrentIndex(2)

            item_sb = gui.QSpinBox()
            item_sb.setRange(0, 100000)
            item_sb.setValue(dataitem.firstbyte)
            item_boff = gui.QSpinBox()
            item_boff.setRange(0, 7)
            item_boff.setValue(dataitem.bitoffset)
            item_bc = gui.QTableWidgetItem(str(ecudata.bitscount))
            item_name = gui.QTableWidgetItem(dataitem.name)
            item_name.setFlags(item_name.flags() ^ core.Qt.ItemIsEditable)
            item_bc.setFlags(item_bc.flags() ^ core.Qt.ItemIsEditable)

            item_bc.setTextAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)

            item_sb.valueChanged.connect(lambda state,
                                                di=dataitem, slf=item_sb: self.start_byte_changed(di, slf))
            item_boff.valueChanged.connect(lambda state,
                                                  di=dataitem, slf=item_boff: self.bit_offset_changed(di, slf))
            endian_combo.activated.connect(lambda state,
                                                  di=dataitem, slf=endian_combo: self.endian_changed(di, slf))

            self.table.setItem(count, 0, item_name)
            self.table.setCellWidget(count, 1, item_sb)
            self.table.setCellWidget(count, 2, item_boff)
            self.table.setItem(count, 3, item_bc)

            self.table.setCellWidget(count, 4, endian_combo)
            count += 1

        self.table.resizeColumnsToContents()
        self.table.setRowCount(count)
        self.bitviewer.init(int(bytescount)+2)

    def shift_bytes_change(self):
        if not self.current_request:
            return

        self.current_request.shiftbytescount = self.spin_shift_byte.value()

    def data_len_change(self):
        if not self.current_request:
            return

        self.current_request.minbytes = self.spin_data_len.value()

    def endian_changed(self, di, slf):
        if slf.currentText() == "Inherits globals":
            di.endian = ""
        elif slf.currentText() == "Little":
            di.endian = "Little"
        elif slf.currentText() == "Big":
            di.endian = "Big"

    def start_byte_changed(self, di, slf):
        di.firstbyte = slf.value()
        self.update_bitview(di.name)

    def bit_offset_changed(self, di, slf):
        di.bitoffset = slf.value()
        self.update_bitview(di.name)

    def request_changed(self):
        if not self.current_request:
            return

        self.inputreq.setStyleSheet("background-color: red")

        try:
            text = str(self.inputreq.text())
        except:
            return

        if not all(c in string.hexdigits for c in text):
            return

        if len(text) % 2 == 1:
            return

        self.inputreq.setStyleSheet("background-color: green")
        if self.send:
            self.current_request.sentbytes = text
        else:
            self.current_request.replybytes = text

class requestEditor(gui.QWidget):
    """Main container for reauest editor"""
    def __init__(self, parent=None):
        super(requestEditor, self).__init__(parent)
        self.ecurequestsparser = None

        layout_action = gui.QHBoxLayout()
        button_reload = gui.QPushButton("Reload")
        layout_action.addWidget(button_reload)
        layout_action.addStretch()

        button_reload.clicked.connect(self.reload)

        self.layh = gui.QHBoxLayout()
        self.requesttable = requestTable()
        self.layh.addWidget(self.requesttable)

        self.layv = gui.QVBoxLayout()

        self.sendbyteeditor = paramEditor()
        self.receivebyteeditor = paramEditor(False)
        self.tabs = gui.QTabWidget()

        self.tabs.addTab(self.sendbyteeditor, "Send bytes")
        self.tabs.addTab(self.receivebyteeditor, "Receive bytes")

        self.layv.addLayout(layout_action)
        self.layv.addWidget(self.tabs)

        self.layh.addLayout(self.layv)
        self.setLayout(self.layh)

        self.requesttable.setSendByteEditor(self.sendbyteeditor)
        self.requesttable.setReceiveByteEditor(self.receivebyteeditor)

    def reload(self):
        if not self.ecurequestsparser:
            return
        self.init()

    def init(self):
        self.requesttable.init(self.ecurequestsparser.requests)
        self.sendbyteeditor.set_ecufile(self.ecurequestsparser)
        self.receivebyteeditor.set_ecufile(self.ecurequestsparser)

    def set_ecu(self, ecu):
        self.ecurequestsparser = ecu
        self.init()


class numericListPanel(gui.QFrame):
    def __init__(self, dataitem, parent=None):
        super(numericListPanel, self).__init__(parent)
        self.setFrameStyle(gui.QFrame.Sunken)
        self.setFrameShape(gui.QFrame.Box)
        self.data = dataitem

        layoutv = gui.QVBoxLayout()
        layout = gui.QGridLayout()
        labelnob = gui.QLabel("Number of bits")
        lablelsigned = gui.QLabel("Signed")

        layout.addWidget(labelnob, 0, 0)
        layout.addWidget(lablelsigned, 1, 0)

        self.inputnob = gui.QSpinBox()
        self.inputnob.setRange(1, 32)
        self.inputsigned = gui.QCheckBox()

        layout.addWidget(self.inputnob, 0, 1)
        layout.addWidget(self.inputsigned, 1, 1)

        layoutv.addLayout(layout)

        self.itemtable = gui.QTableWidget()
        self.itemtable.setRowCount(1)
        self.itemtable.setColumnCount(2)
        self.itemtable.verticalHeader().hide()
        self.itemtable.setSelectionBehavior(gui.QAbstractItemView.SelectRows)
        self.itemtable.setSelectionMode(gui.QAbstractItemView.SingleSelection)

        layoutv.addWidget(self.itemtable)

        self.setLayout(layoutv)
        self.init()

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
            key = unicode(self.itemtable.item(i, 1).text().toUtf8(), encoding="UTF-8")
            val = self.itemtable.cellWidget(i, 0).value()
            self.data.items[key] = val

    def init(self):
        keys = self.data.items.keys()
        self.itemtable.setRowCount(len(keys))

        self.inputsigned.setChecked(self.data.signed)
        self.inputnob.setValue(self.data.bitscount)

        count = 0
        for k in keys:
            currentitem = self.data.items[k]
            spinvalue = gui.QSpinBox()
            spinvalue.setRange(-1000000,1000000)
            spinvalue.setValue(int(currentitem))
            self.itemtable.setCellWidget(count, 0, spinvalue)
            self.itemtable.setItem(count, 0, gui.QTableWidgetItem(str(currentitem).zfill(5)))
            self.itemtable.setItem(count, 1, gui.QTableWidgetItem(k))
            count += 1


        headerstrings = core.QString("Value;Text").split(";")
        self.itemtable.setHorizontalHeaderLabels(headerstrings)
        self.itemtable.resizeColumnsToContents()
        self.itemtable.sortItems(0, core.Qt.AscendingOrder)
        self.itemtable.setSortingEnabled(True)


class otherPanel(gui.QFrame):
    def __init__(self, dataitem, parent=None):
        super(otherPanel, self).__init__(parent)
        self.setFrameStyle(gui.QFrame.Sunken)
        self.setFrameShape(gui.QFrame.Box)
        self.data = dataitem

        layout = gui.QGridLayout()
        labelnob = gui.QLabel("Number of bytes")
        lableunit = gui.QLabel("Unit")

        layout.addWidget(labelnob, 0, 0)
        layout.addWidget(lableunit, 1, 0)
        layout.setRowStretch(2, 1)

        self.inputnob = gui.QSpinBox()
        self.inputnob.setRange(1, 10240)
        self.inputtype = gui.QComboBox()
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
        self.inputnob.setValue(self.data.bytescount)
        if self.data.bytesascii:
            self.inputtype.setCurrentIndex(0)
        else:
            self.inputtype.setCurrentIndex(1)

class numericPanel(gui.QFrame):
    def __init__(self, dataitem, parent=None):
        super(numericPanel, self).__init__(parent)
        self.setFrameStyle(gui.QFrame.Sunken)
        self.setFrameShape(gui.QFrame.Box)
        self.data = dataitem

        layout = gui.QGridLayout()
        labelnob = gui.QLabel("Number of bit")
        lableunit = gui.QLabel("Unit")
        labelsigned = gui.QLabel("Signed")
        labelformat = gui.QLabel("Format")
        labeldoc = gui.QLabel("Value = (AX+B) / C")
        labela = gui.QLabel("A")
        labelb = gui.QLabel("B")
        labelc = gui.QLabel("C")

        layout.addWidget(labelnob, 0, 0)
        layout.addWidget(lableunit, 1, 0)
        layout.addWidget(labelsigned, 2, 0)
        layout.addWidget(labelformat, 3, 0)
        layout.addWidget(labeldoc, 4, 0)
        layout.addWidget(labela, 5, 0)
        layout.addWidget(labelb, 6, 0)
        layout.addWidget(labelc, 7, 0)
        layout.setRowStretch(8, 1)

        self.inputnob = gui.QSpinBox()
        self.inputnob.setRange(1, 32)
        self.inputunit = gui.QLineEdit()
        self.inputsigned = gui.QCheckBox()
        self.inputformat = gui.QLineEdit()
        self.inputa = gui.QDoubleSpinBox()
        self.inputb = gui.QDoubleSpinBox()
        self.inputc = gui.QDoubleSpinBox()
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
        self.data.unit = unicode(self.inputunit.text().toUtf8(), encoding="UTF-8")
        self.data.signed = self.inputsigned.isChecked()
        self.data.format = unicode(self.inputformat.text().toUtf8(), encoding="UTF-8")
        self.data.step = self.inputa.value()
        self.data.offset = self.inputb.value()
        self.data.divideby = self.inputc.value()
        self.data.bytesascii = False
        self.data.items = {}
        self.data.lists = {}

    def init(self):
        self.inputnob.setValue(self.data.bitscount)
        self.inputunit.setText(self.data.unit)
        self.inputsigned.setChecked(self.data.signed)
        self.inputformat.setText(self.data.format)
        self.inputa.setValue(self.data.step)
        self.inputb.setValue(self.data.offset)
        self.inputc.setValue(self.data.divideby)


class dataEditor(gui.QWidget):
    """Main container for data item editor"""
    def __init__(self, parent=None):
        super(dataEditor, self).__init__(parent)
        self.ecurequestsparser = None
        self.currentecudata = None

        layout_action = gui.QHBoxLayout()
        button_new = gui.QPushButton("New")
        button_reload = gui.QPushButton("Reload")
        button_validate = gui.QPushButton("Validate changes")
        layout_action.addWidget(button_new)
        layout_action.addWidget(button_reload)
        layout_action.addWidget(button_validate)
        layout_action.addStretch()

        button_new.clicked.connect(self.new_request)
        button_reload.clicked.connect(self.reload)
        button_validate.clicked.connect(self.validate)

        self.layouth = gui.QHBoxLayout()

        self.datatable = gui.QTableWidget()
        self.datatable.setFixedWidth(350)
        self.datatable.setRowCount(1)
        self.datatable.setColumnCount(2)
        self.datatable.verticalHeader().hide()
        self.datatable.setSelectionBehavior(gui.QAbstractItemView.SelectRows)
        self.datatable.setSelectionMode(gui.QAbstractItemView.SingleSelection)
        self.datatable.setShowGrid(False)

        self.layouth.addWidget(self.datatable)


        self.editorcontent = gui.QFrame()
        self.editorcontent.setFrameStyle(gui.QFrame.Sunken)
        self.editorcontent.setFrameShape(gui.QFrame.Box)

        self.layoutv = gui.QVBoxLayout()
        self.layouth.addLayout(self.layoutv)
        self.layoutv.addLayout(layout_action)

        desclayout = gui.QHBoxLayout()
        labeldescr = gui.QLabel("Description")
        self.descpriptioneditor = gui.QLineEdit()
        desclayout.addWidget(labeldescr)
        desclayout.addWidget(self.descpriptioneditor)

        typelayout = gui.QHBoxLayout()
        typelabel = gui.QLabel("Data type")
        self.typecombo = gui.QComboBox()
        self.typecombo.addItem("Numeric")
        self.typecombo.addItem("Numeric items")
        self.typecombo.addItem("Hex")
        typelayout.addWidget(typelabel)
        typelayout.addWidget(self.typecombo)

        self.layoutv.addLayout(desclayout)
        self.layoutv.addLayout(typelayout)

        self.nonePanel = gui.QWidget()
        self.layoutv.addWidget(self.nonePanel)
        self.currentWidget = self.nonePanel

        self.setLayout(self.layouth)

        self.typecombo.currentIndexChanged.connect(self.switchType)

        self.datatable.cellClicked.connect(self.changeData)

    def new_request(self):
        if not self.ecurequestsparser:
            return

        new_data_name = "New data"

        while new_data_name in self.ecurequestsparser.data.keys():
            new_data_name += "_"

        new_data = ecu.Ecu_data(None, new_data_name)
        new_data.comment = "Replace me with request description"
        self.ecurequestsparser.data[new_data_name] = new_data

        self.reload()

        new_item = self.datatable.findItems(new_data_name, core.Qt.MatchExactly)
        self.datatable.selectRow(new_item[0].row())

    def cellModified(self, r, c):
        if c != 0:
            return

        currentecudata = self.currentecudata
        oldname = currentecudata.name
        self.ecurequestsparser.data.pop(oldname)
        item = self.datatable.item(r, c)
        newname = unicode(item.text().toUtf8(), encoding="UTF-8")
        currentecudata.name = newname
        self.ecurequestsparser.data[newname] = currentecudata

        # Change requests data items name too
        for reqk, req in self.ecurequestsparser.requests.iteritems():
            sbdata = req.sendbyte_dataitems
            rbdata = req.dataitems

            if oldname in sbdata.keys():
                sbdata[oldname].name = newname
                sbdata[newname] = sbdata.pop(oldname)

            if oldname in rbdata.keys():
                rbdata[oldname].name = newname
                rbdata[newname] = rbdata.pop(oldname)

    def clear(self):
        self.datatable.clear()
        self.switchType(3)

    def reload(self):
        self.init_table()

    def validate(self):
        if "validate" not in dir(self.currentWidget):
            return

        comment = unicode(self.descpriptioneditor.text().toUtf8(), encoding="UTF-8")
        self.currentecudata.comment = comment
        self.currentWidget.validate()

    def changeData(self, r, c):
        dataname = unicode(self.datatable.item(r, 0).text().toUtf8(), encoding="UTF-8")
        self.currentecudata = self.ecurequestsparser.data[dataname]
        self.descpriptioneditor.setText(self.currentecudata.comment)
        if self.currentecudata.scaled:
            self.switchType(0)
        elif len(self.currentecudata.items):
            self.switchType(1)
        else:
            self.switchType(2)

    def switchType(self, num):
        self.descpriptioneditor.setEnabled(True)
        self.typecombo.setEnabled(True)
        if num == 0:
            self.layoutv.removeWidget(self.currentWidget)
            self.currentWidget.hide()
            self.currentWidget.destroy()
            self.currentWidget = numericPanel(self.currentecudata)
            self.layoutv.addWidget(self.currentWidget)

        if num == 1:
            self.layoutv.removeWidget(self.currentWidget)
            self.currentWidget.hide()
            self.currentWidget.destroy()
            self.currentWidget = numericListPanel(self.currentecudata)
            self.layoutv.addWidget(self.currentWidget)

        if num == 2:
            self.layoutv.removeWidget(self.currentWidget)
            self.currentWidget.hide()
            self.currentWidget.destroy()
            self.currentWidget = otherPanel(self.currentecudata)
            self.layoutv.addWidget(self.currentWidget)

        if num == 3:
            self.layoutv.removeWidget(self.currentWidget)
            self.currentWidget.hide()
            self.currentWidget.destroy()
            self.currentWidget = gui.QWidget()
            self.layoutv.addWidget(self.currentWidget)
            self.descpriptioneditor.setEnabled(False)
            self.typecombo.setEnabled(False)

    def disconnect_table(self):
        try:
            self.datatable.cellChanged.disconnect()
        except:
            pass

    def connect_table(self):
        self.datatable.cellChanged.connect(self.cellModified)

    def init_table(self):
        self.disconnect_table()

        self.datatable.clear()
        dataItems = self.ecurequestsparser.data.keys()
        self.datatable.setRowCount(len(dataItems))

        count = 0
        for k in dataItems:
            data = self.ecurequestsparser.data[k]

            itemk = gui.QTableWidgetItem(k)
            itemc = gui.QTableWidgetItem(data.comment)

            itemc.setFlags(itemc.flags() ^ core.Qt.ItemIsEditable)

            self.datatable.setItem(count, 0, itemk)
            self.datatable.setItem(count, 1, itemc)

            count += 1

        self.datatable.sortItems(0, core.Qt.AscendingOrder)

        headerstrings = core.QString("Data name;Description").split(";")
        self.datatable.setHorizontalHeaderLabels(headerstrings)
        self.datatable.resizeColumnsToContents()
        self.datatable.sortByColumn(0)
        self.connect_table()

    def set_ecu(self, ecu):
        self.ecurequestsparser = ecu
        self.switchType(3)
        self.init_table()
