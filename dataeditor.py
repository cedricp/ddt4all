import time
import ecu
import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import options, os

# self.minbytes = 0
# self.shiftbytescount = 0
# self.replybytes = ''
# self.manualsend = False
# self.sentbytes = ''
# self.dataitems = {}
# self.sendbyte_dataitems = {}
# self.name = ''
# self.endian = endian'

class requestTable(gui.QTableWidget):
    def __init__(self,  parent=None):
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

    def setSendByteEditor(self, sbe):
        self.sendbyteeditor = sbe
        self.cellClicked.connect(self.cell_clicked)

    def setReceiveByteEditor(self, rbe):
        self.rcvbyteeditor = rbe
        self.cellClicked.connect(self.cell_clicked)

    def cell_clicked(self, x, y):
        currenttext = unicode(self.item(x, 0).text().toUtf8(), encoding="UTF-8")
        self.sendbyteeditor.set_request(self.ecureq[currenttext])
        self.rcvbyteeditor.set_request(self.ecureq[currenttext])

    def init(self, ecureq):
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
            if not isinstance(request_inst, ecu.Ecu_request):
                continue
            bytes = request_inst.sentbytes
            manual = gui.QCheckBox()
            manual.setChecked(False)
            if request_inst.manualsend:
                manual.setChecked(True)

            self.setItem(count, 0, gui.QTableWidgetItem(req))
            self.setCellWidget(count, 1, manual)

            count += 1

        self.setRowCount(count)
        self.sortItems(core.Qt.AscendingOrder)
        self.resizeColumnsToContents()


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

    def set_ecufile(self, ef):
        self.ecufile = ef

    def set_request(self, req):
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

        count = 0
        for k in datak:
            dataitem = data[k]
            ecudata = self.ecufile.data[dataitem.name]
            endian = req.endian
            if dataitem.endian:
                endian = dataitem.endian

            endian_combo = gui.QComboBox()
            endian_combo.addItem("Little")
            endian_combo.addItem("Big")

            if endian == "Big":
                endian_combo.setCurrentIndex(1)
            else:
                endian_combo.setCurrentIndex(0)

            item_sb = gui.QTableWidgetItem(str(dataitem.firstbyte))
            item_boff = gui.QTableWidgetItem(str(dataitem.bitoffset))
            item_bc = gui.QTableWidgetItem(str(ecudata.bitscount))

            item_sb.setTextAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)
            item_boff.setTextAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)
            item_bc.setTextAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)

            self.table.setItem(count, 0, gui.QTableWidgetItem(dataitem.name))
            self.table.setItem(count, 1, item_sb)
            self.table.setItem(count, 2, item_boff)
            self.table.setItem(count, 3, item_bc)

            self.table.setCellWidget(count, 4, endian_combo)
            count += 1

        self.table.resizeColumnsToContents()
        self.table.setRowCount(count)


class dataEditor(gui.QWidget):
    """Main container for reauest editor"""
    def __init__(self, parent=None):
        super(dataEditor, self).__init__(parent)
        self.ecurequest = None
        self.layh = gui.QHBoxLayout()
        self.requesttable = requestTable()
        self.layh.addWidget(self.requesttable)

        self.layv = gui.QVBoxLayout()

        self.sendbyteeditor = paramEditor()
        self.receivebyteeditor = paramEditor(False)
        self.tabs = gui.QTabWidget()

        self.tabs.addTab(self.sendbyteeditor, "Send bytes")
        self.tabs.addTab(self.receivebyteeditor, "Receive bytes")

        self.layv.addWidget(self.tabs)

        self.layh.addLayout(self.layv)
        self.setLayout(self.layh)

        self.requesttable.setSendByteEditor(self.sendbyteeditor)
        self.requesttable.setReceiveByteEditor(self.receivebyteeditor)

    def set_ecu_file(self, ecu_file):
        self.ecurequestsparser = ecu.Ecu_file(ecu_file, True)
        self.requesttable.init(self.ecurequestsparser.requests)
        self.sendbyteeditor.set_ecufile(self.ecurequestsparser)
        self.receivebyteeditor.set_ecufile(self.ecurequestsparser)

