import math
import string

import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets

from ddt4all.core.ecu.data_item import DataItem
import ddt4all.options as options
from ddt4all.ui.data_editor.data_table import DataTable
from ddt4all.ui.data_editor.bit_viewer import BitViewer


_ = options.translator('ddt4all')

class ParamEditor(widgets.QFrame):
    """Manages send/receive requests"""

    def __init__(self, issend=True, parent=None):
        super(ParamEditor, self).__init__(parent)
        self.send = issend
        self.currentdataitem = None
        self.setFrameStyle(widgets.QFrame.Sunken)
        self.setFrameShape(widgets.QFrame.Box)
        self.layoutv = widgets.QVBoxLayout()

        add_layout = widgets.QHBoxLayout()
        self.data_list = widgets.QComboBox()
        self.button_add = widgets.QPushButton(_("Add"))
        self.button_add.setFixedWidth(50)

        add_layout.addWidget(self.data_list)
        add_layout.addWidget(self.button_add)

        if issend:
            self.labelreq = widgets.QLabel(_("Send request bytes (HEX)"))
        else:
            self.labelreq = widgets.QLabel(_("Receive bytes (HEX)"))
        self.inputreq = widgets.QLineEdit()
        self.inputreq.textChanged.connect(self.request_changed)
        self.button_add.clicked.connect(self.add_data)

        self.layoutv.addLayout(add_layout)
        self.layoutv.addWidget(self.labelreq)
        self.layoutv.addWidget(self.inputreq)

        if not issend:
            rcv_lay = widgets.QHBoxLayout()
            self.label_data_len = widgets.QLabel(_("Data length"))
            self.spin_data_len = widgets.QSpinBox()
            self.label_shift_bytes = widgets.QLabel(_("Shift byte count"))
            self.spin_shift_byte = widgets.QSpinBox()
            rcv_lay.addWidget(self.label_data_len)
            rcv_lay.addWidget(self.spin_data_len)
            rcv_lay.addWidget(self.label_shift_bytes)
            rcv_lay.addWidget(self.spin_shift_byte)
            self.layoutv.addLayout(rcv_lay)

            self.spin_shift_byte.valueChanged.connect(self.shift_bytes_change)
            self.spin_data_len.valueChanged.connect(self.data_len_change)

        self.setLayout(self.layoutv)

        self.table = DataTable()
        self.table.gotoitem.connect(self.gotoitem)
        self.table.removeitem.connect(self.removeitem)
        self.table.setRowCount(50)
        self.table.setColumnCount(5)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(widgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        # self.table.setShowGrid(False)
        self.layoutv.addWidget(self.table)
        self.ecufile = None
        self.current_request = None
        self.table.itemSelectionChanged.connect(self.cell_clicked)

        self.bitviewer = BitViewer()
        self.bitviewer.setFixedHeight(110)
        self.layoutv.addWidget(self.bitviewer)

    def refresh_combo(self):
        self.data_list.clear()

        for k in sorted(self.ecufile.data):
            self.data_list.addItem(k)

    def add_data(self):
        current_data_name = self.data_list.currentText()

        data = {}
        data['firstbyte'] = 2
        data['bitoffset'] = 0
        data['ref'] = False
        data['endian'] = ''

        if self.send:
            self.current_request.sendbyte_dataitems[current_data_name] = DataItem(data, '', current_data_name)
        else:
            self.current_request.dataitems[current_data_name] = DataItem(data, '', current_data_name)

        self.init(self.current_request)

    def removeitem(self, name):
        if self.send:
            self.current_request.sendbyte_dataitems.pop(name)
        else:
            self.current_request.dataitems.pop(name)
        self.init(self.current_request)

    def gotoitem(self, name):
        options.main_window.showDataTab(name)

    def cell_clicked(self):
        if len(self.table.selectedItems()) == 0:
            return

        r = self.table.selectedItems()[-1].row()

        item = self.table.item(r, 0)
        if not item:
            return
        dataname = item.text()
        self.currentdataitem = dataname
        self.update_bitview(dataname)
        self.update_bitview_value(dataname)

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
        valuetosend = valuetosend.replace("L", "")

        bytesarray = ["00" for a in range(bytes)]
        bytesarray = ecudata.setValue(valuetosend, bytesarray, dataitem, self.current_request.ecu_file.endianness, True)
        self.bitviewer.set_bytes(bytesarray)

    def update_bitview_value(self, dataname):
        bytestosend = str(self.inputreq.text())
        byteslisttosend = [bytestosend[a * 2:a * 2 + 2] for a in range(len(bytestosend) // 2)]
        self.bitviewer.set_bytes_value(byteslisttosend)

    def set_ecufile(self, ef):
        self.current_request = None
        self.ecufile = ef
        self.table.clear()
        self.inputreq.clear()

    def set_request(self, req):
        self.current_request = req
        self.init(req)

    def refresh_data(self):
        if self.current_request:
            self.init(self.current_request)

    def init(self, req):
        self.table.clear()
        self.data_list.clear()
        self.currentdataitem = None

        if self.send:
            self.inputreq.setText(req.sentbytes)
        else:
            self.inputreq.setText(req.replybytes)

        if self.send:
            data = req.sendbyte_dataitems
        else:
            data = req.dataitems
        datak = data.keys()

        for k in sorted(self.ecufile.data):
            self.data_list.addItem(k)

        if not self.send:
            self.spin_shift_byte.setValue(req.shiftbytescount)
            self.spin_data_len.setValue(req.minbytes)

        headerstrings = _("Data name;Start byte;Bit offset;Bit count;Endianess").split(";")
        self.table.setHorizontalHeaderLabels(headerstrings)
        self.table.init(self.send, self.current_request.name)

        bytescount = 0

        self.table.setRowCount(len(datak))
        count = 0
        for k in datak:
            dataitem = data[k]
            ecudata = self.ecufile.data[dataitem.name]
            endian = dataitem.endian

            ln = dataitem.firstbyte + math.ceil(float(ecudata.bitscount) / 8.)
            if ln > bytescount:
                bytescount = ln

            endian_combo = widgets.QComboBox()
            endian_combo.addItem(_("Little"))
            endian_combo.addItem(_("Big"))
            endian_combo.addItem(_("Inherits globals"))

            if endian == "Big":
                endian_combo.setCurrentIndex(1)
            elif endian == "Little":
                endian_combo.setCurrentIndex(0)
            else:
                endian_combo.setCurrentIndex(2)

            item_sb = widgets.QSpinBox()
            item_sb.setRange(1, 100000)
            item_sb.setValue(dataitem.firstbyte)
            item_boff = widgets.QSpinBox()
            item_boff.setRange(0, 7)
            item_boff.setValue(dataitem.bitoffset)
            item_bc = widgets.QTableWidgetItem(str(ecudata.bitscount))
            item_name = widgets.QTableWidgetItem(dataitem.name)
            item_name.setFlags(item_name.flags() ^ core.Qt.ItemIsEditable)
            item_bc.setFlags(item_bc.flags() ^ core.Qt.ItemIsEditable)

            item_bc.setTextAlignment(int(core.Qt.AlignHCenter) | int(core.Qt.AlignVCenter))

            item_sb.valueChanged.connect(lambda state,
                                                di=dataitem, slf=item_sb: self.start_byte_changed(di, slf))
            item_boff.valueChanged.connect(lambda state,
                                                  di=dataitem, slf=item_boff: self.bit_offset_changed(di, slf))
            endian_combo.activated.connect(lambda state,
                                                  di=dataitem, slf=endian_combo: self.endian_changed(di, slf))

            self.table.setItem(count, 0, item_name)
            self.table.setItem(count, 1, widgets.QTableWidgetItem(str(dataitem.firstbyte).zfill(5)))
            self.table.setCellWidget(count, 1, item_sb)
            self.table.setCellWidget(count, 2, item_boff)
            self.table.setItem(count, 3, item_bc)

            self.table.setCellWidget(count, 4, endian_combo)
            count += 1

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.sortItems(1)
        self.bitviewer.init(int(bytescount) + 2)

    def shift_bytes_change(self):
        if not self.current_request:
            return

        self.current_request.shiftbytescount = self.spin_shift_byte.value()

    def data_len_change(self):
        if not self.current_request:
            return

        self.current_request.minbytes = self.spin_data_len.value()

    def endian_changed(self, di, slf):
        if slf.currentText() == _("Inherits globals"):
            di.endian = ""
        elif slf.currentText() == _("Little"):
            di.endian = "Little"
        elif slf.currentText() == _("Big"):
            di.endian = "Big"
        self.currentdataitem = di.name
        self.update_bitview(self.currentdataitem)
        self.update_bitview_value(self.currentdataitem)

    def start_byte_changed(self, di, slf):
        di.firstbyte = slf.value()
        self.currentdataitem = di.name
        self.update_bitview(self.currentdataitem)
        self.update_bitview_value(self.currentdataitem)

    def bit_offset_changed(self, di, slf):
        di.bitoffset = slf.value()
        self.currentdataitem = di.name
        self.update_bitview(self.currentdataitem)
        self.update_bitview_value(self.currentdataitem)

    def request_changed(self):
        if not self.current_request:
            return

        self.inputreq.setStyleSheet("background-color: red")

        try:
            text = str(self.inputreq.text())
        except Exception:
            return

        if not all(c in string.hexdigits for c in text):
            return

        if len(text) % 2 == 1:
            return

        if self.currentdataitem:
            self.update_bitview_value(self.currentdataitem)

        self.inputreq.setStyleSheet("background-color: green")

        if self.send:
            self.current_request.sentbytes = text
        else:
            self.current_request.replybytes = text

