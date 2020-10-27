# -*- coding: utf-8 -*-
import ecu
import math
import string
import options
import copy
import codecs
hex_decoder = codecs.getdecoder("hex_codec")

import PyQt5.QtGui as gui
import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets

__author__ = "Cedric PAILLE"
__copyright__ = "Copyright 2016-2018"
__credits__ = []
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Cedric PAILLE"
__email__ = "cedricpaille@gmail.com"
__status__ = "Beta"

_ = options.translator('ddt4all')


def decode_hex(string):
    return hex_decoder(string)[0]


class Bit_container(widgets.QFrame):
    def __init__(self, data, num, parent=None):
        super(Bit_container, self).__init__(parent)
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


class Bit_viewer(widgets.QScrollArea):
    def __init__(self, parent=None):
        super(Bit_viewer, self).__init__(parent)
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
            bc = Bit_container("00", i)
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


class checkBox(widgets.QCheckBox):
    def __init__(self, data, parent=None):
        super(checkBox, self).__init__(parent)
        self.data = data
        if data.manualsend:
            self.setChecked(True)
        else:
            self.setChecked(False)

        self.stateChanged.connect(self.change)

    def change(self, state):
        if state:
            self.data.manualsend = True
        else:
            self.data.manualsend = False


class dataTable(widgets.QTableWidget):
    gotoitem = core.pyqtSignal(object)
    removeitem = core.pyqtSignal(object)

    def __init__(self, parent=None):
        super(dataTable, self).__init__(parent)
        self.issend = None
        self.requestname = None

    def goto_item(self, item):
        self.gotoitem.emit(item)

    def remove_item(self, item):
        self.removeitem.emit(item)

    def add_to_screen(self, name, item):
        if not options.main_window.paramview:
            return
        itemtext = item
        options.main_window.paramview.addParameter(self.requestname, self.issend, name, itemtext)

    def init(self, issend, requestname):
        self.issend = issend
        self.requestname = requestname

    def contextMenuEvent(self, event):
        pos = event.pos()
        index = self.indexAt(pos)
        menu = widgets.QMenu()

        if index.column() == 0:
            item_name = self.itemAt(pos).text()
            if not item_name:
                return
            action_goto = widgets.QAction(_("Goto data"), menu)
            action_remove = widgets.QAction(_("Remove"), menu)

            action_goto.triggered.connect(lambda state, it=item_name: self.goto_item(it))
            action_remove.triggered.connect(lambda state, it=item_name: self.remove_item(it))

            screenMenu = widgets.QMenu(_("Add to screen"))
            for sn in options.main_window.screennames:
                sa = widgets.QAction(sn, screenMenu)
                sa.triggered.connect(lambda state, name=sn, it=item_name: self.add_to_screen(name, it))
                screenMenu.addAction(sa)

            menu.addActions([action_goto, action_remove])
            menu.addMenu(screenMenu)

            menu.exec_(event.globalPos())
            event.accept()

class requestTable(widgets.QTableWidget):
    def __init__(self, parent=None):
        super(requestTable, self).__init__(parent)
        self.ecureq = None
        self.sendbyteeditor = None
        self.rcvbyteeditor = None
        self.reqs = []
        self.setFixedWidth(350)
        self.setSelectionBehavior(widgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        self.verticalHeader().hide()
        #self.setShowGrid(False)
        self.currentreq = None
        self.sdsupdate = True

    def cellModified(self, r, c):
        if not self.ecureq:
            return

        if c == 0:
            newname = self.item(r, c).text()

            # Avoid name clashes
            while newname in self.ecureq:
                newname += u"_"

            oldname = self.ecureq[self.currentreq].name
            self.ecureq[self.currentreq].name = newname
            self.ecureq[newname] = self.ecureq.pop(self.currentreq)

            self.init(self.ecureq)
            options.main_window.paramview.requestNameChanged(oldname, newname)
            self.select(newname)

    def update_sds(self, req):
        self.sdsupdate = False
        self.parent().init_sds(req)
        self.sdsupdate = True

    def set_sds(self, view):
        if not self.sdsupdate:
            return

        if not self.ecureq or self.currentreq is None:
            return

        self.ecureq[self.currentreq].sds['nosds'] = view.checknosds.isChecked()
        self.ecureq[self.currentreq].sds['plant'] = view.checkplant.isChecked()
        self.ecureq[self.currentreq].sds['aftersales'] = view.checkaftersales.isChecked()
        self.ecureq[self.currentreq].sds['engineering'] = view.checkengineering.isChecked()
        self.ecureq[self.currentreq].sds['supplier'] = view.checksupplier.isChecked()

    def select(self, name):
        items = self.findItems(name, core.Qt.MatchExactly)
        if len(items):
            self.selectRow(items[0].row())

    def setSendByteEditor(self, sbe):
        self.sendbyteeditor = sbe
        self.itemSelectionChanged.connect(self.onCellChanged)

    def setReceiveByteEditor(self, rbe):
        self.rcvbyteeditor = rbe
        self.itemSelectionChanged.connect(self.onCellChanged)

    def onCellChanged(self):
        if len(self.selectedItems()) == 0:
            return

        currentItem = self.selectedItems()[0]

        if not currentItem:
            return

        currenttext = currentItem.text()
        self.currentreq = currenttext

        if not currenttext:
            return

        self.sendbyteeditor.set_request(self.ecureq[currenttext])
        self.rcvbyteeditor.set_request(self.ecureq[currenttext])

        self.update_sds(self.ecureq[currenttext])

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
        self.setColumnCount(3)

        self.setHorizontalHeaderLabels(_("Request name;Bytes;Manual").split(";"))

        count = 0
        for req in requestsk:
            request_inst = self.ecureq[req]

            manual = checkBox(request_inst)

            self.setItem(count, 0, widgets.QTableWidgetItem(req))
            sbtext = request_inst.sentbytes
            if len(sbtext) > 10:
                sbtext = sbtext[0:10] + "..."
            self.setItem(count, 1, widgets.QTableWidgetItem(sbtext))
            self.setCellWidget(count, 2, manual)
            count += 1

        self.sortItems(0, core.Qt.AscendingOrder)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.cellChanged.connect(self.cellModified)


class paramEditor(widgets.QFrame):
    """Manages send/receive requests"""
    def __init__(self, issend=True, parent=None):
        super(paramEditor, self).__init__(parent)
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

        self.table = dataTable()
        self.table.gotoitem.connect(self.gotoitem)
        self.table.removeitem.connect(self.removeitem)
        self.table.setRowCount(50)
        self.table.setColumnCount(5)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(widgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        #self.table.setShowGrid(False)
        self.layoutv.addWidget(self.table)
        self.ecufile = None
        self.current_request = None
        self.table.itemSelectionChanged.connect(self.cell_clicked)

        self.bitviewer = Bit_viewer()
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
            self.current_request.sendbyte_dataitems[current_data_name] = ecu.Data_item(data, '', current_data_name)
        else:
            self.current_request.dataitems[current_data_name] = ecu.Data_item(data, '', current_data_name)

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
        if not item: return
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
        byteslisttosend = [bytestosend[a*2:a*2+2] for a in range(len(bytestosend) // 2)]
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

            item_bc.setTextAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)

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
        except:
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


class requestEditor(widgets.QWidget):
    """Main container for reauest editor"""
    def __init__(self, parent=None):
        super(requestEditor, self).__init__(parent)
        self.ecurequestsparser = None

        layoutsss = widgets.QHBoxLayout()

        self.checknosds = widgets.QCheckBox(_("No SDS"))
        self.checkplant = widgets.QCheckBox(_("Plant"))
        self.checkaftersales = widgets.QCheckBox(_("After Sale"))
        self.checkengineering = widgets.QCheckBox(_("Engineering"))
        self.checksupplier = widgets.QCheckBox(_("Supplier"))

        self.checknosds.toggled.connect(self.sdschanged)
        self.checkplant.toggled.connect(self.sdschanged)
        self.checkaftersales.toggled.connect(self.sdschanged)
        self.checkengineering.toggled.connect(self.sdschanged)
        self.checksupplier.toggled.connect(self.sdschanged)

        layoutsss.addWidget(self.checknosds)
        layoutsss.addWidget(self.checkplant)
        layoutsss.addWidget(self.checkaftersales)
        layoutsss.addWidget(self.checkengineering)
        layoutsss.addWidget(self.checksupplier)

        layout_action = widgets.QHBoxLayout()
        button_reload = widgets.QPushButton(_("Reload requests"))
        button_add = widgets.QPushButton(_("Add request"))
        layout_action.addWidget(button_reload)
        layout_action.addWidget(button_add)
        layout_action.addStretch()

        button_reload.clicked.connect(self.reload)
        button_add.clicked.connect(self.add_request)

        self.layh = widgets.QHBoxLayout()
        self.requesttable = requestTable()
        self.layh.addWidget(self.requesttable)

        self.layv = widgets.QVBoxLayout()

        self.sendbyteeditor = paramEditor()
        self.receivebyteeditor = paramEditor(False)
        self.tabs = widgets.QTabWidget()

        self.tabs.addTab(self.sendbyteeditor, _("Send bytes"))
        self.tabs.addTab(self.receivebyteeditor, _("Receive bytes"))

        self.layv.addLayout(layout_action)
        self.layv.addLayout(layoutsss)
        self.layv.addWidget(self.tabs)

        self.layh.addLayout(self.layv)
        self.setLayout(self.layh)

        self.requesttable.setSendByteEditor(self.sendbyteeditor)
        self.requesttable.setReceiveByteEditor(self.receivebyteeditor)
        self.enable_view(False)

    def refresh_data(self):
        self.sendbyteeditor.refresh_combo()
        self.receivebyteeditor.refresh_combo()

    def enable_view(self, enable):
        children = self.children()
        for c in children:
            if isinstance(c, widgets.QWidget):
                c.setEnabled(enable)

    def add_request(self):
        ecu_datareq = {}
        ecu_datareq['minbytes'] = 2
        ecu_datareq['shiftbytescount'] = 0
        ecu_datareq['replybytes'] = ''
        ecu_datareq['manualsend'] = False
        ecu_datareq['sentbytes'] = ''
        ecu_datareq['endian'] = ''
        ecu_datareq['name'] = u'New request'
        self.ecurequestsparser.requests[ecu_datareq['name']] = ecu.Ecu_request(ecu_datareq, self.ecurequestsparser)
        self.init()
        self.requesttable.select(ecu_datareq['name'])

    def sdschanged(self):
        if not self.ecurequestsparser:
            return

        self.requesttable.set_sds(self)

    def reload(self):
        if not self.ecurequestsparser:
            return
        self.init()

    def init(self):
        self.requesttable.init(self.ecurequestsparser.requests)
        self.sendbyteeditor.set_ecufile(self.ecurequestsparser)
        self.receivebyteeditor.set_ecufile(self.ecurequestsparser)

    def refresh_data(self):
        self.sendbyteeditor.refresh_data()
        self.receivebyteeditor.refresh_data()

    def init_sds(self, req):
        self.checknosds.setChecked(req.sds['nosds'])
        self.checkplant.setChecked(req.sds['plant'])
        self.checkaftersales.setChecked(req.sds['aftersales'])
        self.checkengineering.setChecked(req.sds['engineering'])
        self.checksupplier.setChecked(req.sds['supplier'])

    def set_ecu(self, ecu):
        self.ecurequestsparser = ecu
        self.init()
        self.enable_view(True)


class numericListPanel(widgets.QFrame):
    def __init__(self, dataitem, parent=None):
        super(numericListPanel, self).__init__(parent)
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
            spinvalue.setRange(-1000000,1000000)
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
        #self.itemtable.setSortingEnabled(True)


class otherPanel(widgets.QFrame):
    def __init__(self, dataitem, parent=None):
        super(otherPanel, self).__init__(parent)
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

class numericPanel(widgets.QFrame):
    def __init__(self, dataitem, parent=None):
        super(numericPanel, self).__init__(parent)
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


class dataEditor(widgets.QWidget):
    """Main container for data item editor"""
    def __init__(self, parent=None):
        super(dataEditor, self).__init__(parent)
        self.ecurequestsparser = None
        self.currentecudata = None

        layout_action = widgets.QHBoxLayout()
        button_new = widgets.QPushButton(_("New"))
        button_duplicate = widgets.QPushButton(_("Duplicate selected"))
        button_remove = widgets.QPushButton(_("Remove selected"))
        button_reload = widgets.QPushButton(_("Reload"))
        button_validate = widgets.QPushButton(_("Validate changes"))
        layout_action.addWidget(button_new)
        layout_action.addWidget(button_duplicate)
        layout_action.addWidget(button_remove)
        layout_action.addWidget(button_reload)
        layout_action.addWidget(button_validate)
        layout_action.addStretch()

        button_new.clicked.connect(self.new_request)
        button_reload.clicked.connect(self.reload)
        button_validate.clicked.connect(self.validate)
        button_duplicate.clicked.connect(self.duplicate_selected)
        button_remove.clicked.connect(self.remove_selected)

        self.layouth = widgets.QHBoxLayout()

        self.datatable = widgets.QTableWidget()
        self.datatable.setFixedWidth(350)
        self.datatable.setRowCount(1)
        self.datatable.setColumnCount(2)
        self.datatable.verticalHeader().hide()
        self.datatable.setSelectionBehavior(widgets.QAbstractItemView.SelectRows)
        self.datatable.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        #self.datatable.setShowGrid(False)

        self.layouth.addWidget(self.datatable)


        self.editorcontent = widgets.QFrame()
        self.editorcontent.setFrameStyle(widgets.QFrame.Sunken)
        self.editorcontent.setFrameShape(widgets.QFrame.Box)

        self.layoutv = widgets.QVBoxLayout()
        self.layouth.addLayout(self.layoutv)
        self.layoutv.addLayout(layout_action)

        desclayout = widgets.QHBoxLayout()
        labeldescr = widgets.QLabel(_("Description"))
        self.descpriptioneditor = widgets.QLineEdit()
        desclayout.addWidget(labeldescr)
        desclayout.addWidget(self.descpriptioneditor)

        typelayout = widgets.QHBoxLayout()
        typelabel = widgets.QLabel(_("Data type"))
        self.typecombo = widgets.QComboBox()
        self.typecombo.addItem(_("Numeric"))
        self.typecombo.addItem(_("Numeric items"))
        self.typecombo.addItem(_("Hex"))
        typelayout.addWidget(typelabel)
        typelayout.addWidget(self.typecombo)

        self.layoutv.addLayout(desclayout)
        self.layoutv.addLayout(typelayout)

        self.nonePanel = widgets.QWidget()
        self.layoutv.addWidget(self.nonePanel)
        self.currentWidget = self.nonePanel

        self.setLayout(self.layouth)

        self.typecombo.currentIndexChanged.connect(self.switchType)

        self.datatable.itemSelectionChanged.connect(self.changeData)
        self.enable_view(False)

    def remove_selected(self):
        if len(self.datatable.selectedItems()) == 0:
            return

        r = self.datatable.selectedItems()[-1].row()
        dataname = self.datatable.item(r, 0).text()

        # Check if data needed by request
        for reqname, request in self.ecurequestsparser.requests.items():
            for rcvname, rcvdi in request.dataitems.items():
                if rcvname == dataname:
                    msgbox = widgets.QMessageBox()
                    msgbox.setText(_("Data is used by request %s") % reqname)
                    msgbox.exec_()
                    return
            for sndname, snddi in request.sendbyte_dataitems.items():
                if sndname == dataname:
                    msgbox = widgets.QMessageBox()
                    msgbox.setText(_("Data is used by request %s") % reqname)
                    msgbox.exec_()
                    return

        self.ecurequestsparser.data.pop(dataname)

        self.reload()

    def duplicate_selected(self):
        if len(self.datatable.selectedItems()) == 0:
            return

        r = self.datatable.selectedItems()[-1].row()

        dataname = self.datatable.item(r, 0).text()
        self.currentecudata = self.ecurequestsparser.data[dataname]

        new_data_name = dataname
        while new_data_name in self.ecurequestsparser.data:
            new_data_name += u"_copy"

        deep_data_copy = copy.deepcopy(self.currentecudata)
        deep_data_copy.name = new_data_name
        self.ecurequestsparser.data[new_data_name] = deep_data_copy
        self.reload()

        copied_item = self.datatable.findItems(new_data_name, core.Qt.MatchExactly)
        self.datatable.selectRow(copied_item[0].row())

        options.main_window.requesteditor.init()

    def enable_view(self, enable):
        children = self.children()
        for c in children:
            if isinstance(c, widgets.QWidget):
                c.setEnabled(enable)

    def edititem(self, name):
        items = self.datatable.findItems(name, core.Qt.MatchExactly)
        if len(items):
            self.datatable.selectRow(items[0].row())
            self.changeData()

    def new_request(self):
        if not self.ecurequestsparser:
            return

        new_data_name = _("New data")

        while new_data_name in self.ecurequestsparser.data.keys():
            new_data_name += "_"

        new_data = ecu.Ecu_data(None, new_data_name)
        new_data.comment = _("Replace me with request description")
        self.ecurequestsparser.data[new_data_name] = new_data

        self.reload()

        new_item = self.datatable.findItems(new_data_name, core.Qt.MatchExactly)
        self.datatable.selectRow(new_item[0].row())

        # Refresh request data combo
        options.main_window.requesteditor.refresh_data()

    def cellModified(self, r, c):
        if c != 0:
            return

        currentecudata = self.currentecudata
        oldname = currentecudata.name
        self.ecurequestsparser.data.pop(oldname)
        item = self.datatable.item(r, c)
        newname = item.text()
        currentecudata.name = newname
        self.ecurequestsparser.data[newname] = currentecudata

        # Change requests data items name too
        for reqk, req in self.ecurequestsparser.requests.items():
            sbdata = req.sendbyte_dataitems
            rbdata = req.dataitems

            if oldname in sbdata.keys():
                sbdata[oldname].name = newname
                sbdata[newname] = sbdata.pop(oldname)

            if oldname in rbdata.keys():
                rbdata[oldname].name = newname
                rbdata[newname] = rbdata.pop(oldname)

        options.main_window.paramview.dataNameChanged(oldname, newname)
        options.main_window.requesteditor.refresh_data()

    def clear(self):
        self.datatable.clear()
        self.switchType(3)

    def reload(self):
        self.init_table()

    def validate(self):
        if "validate" not in dir(self.currentWidget):
            return

        comment = self.descpriptioneditor.text()
        self.currentecudata.comment = comment
        self.currentWidget.validate()
        options.main_window.requesteditor.refresh_data()

        # Update table entry
        if len(self.datatable.selectedItems()) == 0:
            return

        r = self.datatable.selectedItems()[-1].row()
        self.datatable.item(r, 1).setText(comment)

    def changeData(self):
        if len(self.datatable.selectedItems()) == 0:
            return

        r = self.datatable.selectedItems()[-1].row()


        dataname = self.datatable.item(r, 0).text()
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
            self.typecombo.setCurrentIndex(0)
            self.layoutv.removeWidget(self.currentWidget)
            self.currentWidget.hide()
            self.currentWidget.destroy()
            self.currentWidget = numericPanel(self.currentecudata)
            self.layoutv.addWidget(self.currentWidget)

        if num == 1:
            self.typecombo.setCurrentIndex(1)
            self.layoutv.removeWidget(self.currentWidget)
            self.currentWidget.hide()
            self.currentWidget.destroy()
            self.currentWidget = numericListPanel(self.currentecudata)
            self.layoutv.addWidget(self.currentWidget)

        if num == 2:
            self.typecombo.setCurrentIndex(2)
            self.layoutv.removeWidget(self.currentWidget)
            self.currentWidget.hide()
            self.currentWidget.destroy()
            self.currentWidget = otherPanel(self.currentecudata)
            self.layoutv.addWidget(self.currentWidget)

        if num == 3:
            self.layoutv.removeWidget(self.currentWidget)
            self.currentWidget.hide()
            self.currentWidget.destroy()
            self.currentWidget = widgets.QWidget()
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

            itemk = widgets.QTableWidgetItem(k)
            itemc = widgets.QTableWidgetItem(data.comment)

            itemc.setFlags(itemc.flags() ^ core.Qt.ItemIsEditable)

            self.datatable.setItem(count, 0, itemk)
            self.datatable.setItem(count, 1, itemc)

            count += 1

        self.datatable.sortItems(0, core.Qt.AscendingOrder)

        headerstrings = _("Data name;Description").split(";")
        self.datatable.setHorizontalHeaderLabels(headerstrings)
        self.datatable.resizeColumnsToContents()
        self.datatable.resizeRowsToContents()
        self.datatable.sortByColumn(0, core.Qt.AscendingOrder)
        self.connect_table()

    def set_ecu(self, ecu):
        self.ecurequestsparser = ecu
        self.switchType(3)
        self.init_table()
        self.enable_view(True)


class buttonData(widgets.QFrame):
    def __init__(self, parent=None):
        super(buttonData, self).__init__(parent)
        self.setFrameStyle(widgets.QFrame.Sunken)
        self.setFrameShape(widgets.QFrame.Box)
        self.buttonlayout = None
        self.ecurequests = None
        self.currentbuttonparams = None
        self.currentbuttonuniquename = None
        self.is_screen = None
        self.layout = None

        layout = widgets.QVBoxLayout()
        self.requesttable = widgets.QTableWidget()
        layout.addWidget(self.requesttable)

        layoutbar = widgets.QHBoxLayout()
        self.delaybox = widgets.QSpinBox()
        self.delaybox.setRange(0, 100000)
        self.delaybox.setSingleStep(50)
        self.delaybox.setFixedWidth(80)
        self.requestcombo = widgets.QComboBox()
        self.requestaddbutton = widgets.QPushButton(_("Add"))
        self.requestdelbutton = widgets.QPushButton(_("Del"))
        self.requestrefbutton = widgets.QPushButton(_("Refresh"))
        self.requestmoveupbutton = widgets.QPushButton(_("Move up"))
        self.requestcheckbutton = widgets.QPushButton(_("Check"))

        layoutbar.addWidget(self.delaybox)
        layoutbar.addWidget(self.requestcombo)
        layoutbar.addWidget(self.requestmoveupbutton)
        layoutbar.addWidget(self.requestaddbutton)
        layoutbar.addWidget(self.requestdelbutton)
        layoutbar.addWidget(self.requestrefbutton)
        layoutbar.addWidget(self.requestcheckbutton)

        self.requestrefbutton.setFixedWidth(80)
        self.requestdelbutton.setFixedWidth(60)
        self.requestaddbutton.setFixedWidth(60)
        self.requestmoveupbutton.setFixedWidth(70)
        self.requestcheckbutton.setFixedWidth(80)

        self.requestrefbutton.clicked.connect(self.refresh_request)
        self.requestdelbutton.clicked.connect(self.delete_request)
        self.requestaddbutton.clicked.connect(self.add_request)
        self.requestmoveupbutton.clicked.connect(self.move_up)
        self.requestcheckbutton.clicked.connect(self.check_data)

        layout.addLayout(layoutbar)

        self.setLayout(layout)

        self.requesttable.setColumnCount(2)
        self.requesttable.verticalHeader().hide()
        self.requesttable.setSelectionBehavior(widgets.QAbstractItemView.SelectRows)
        self.requesttable.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        #self.requesttable.setShowGrid(False)

    def check_data(self):
        if not self.ecurequests or not self.buttonlayout:
            return

        items = self.requesttable.selectedItems()
        if len(items) == 0:
            return

        currentrowidx = items[-1].row()
        requestname = self.currentbuttonparams[currentrowidx]['RequestName']

        if requestname not in self.ecurequests.requests.keys():
            options.main_window.logview.append(_("Request %s not found") % requestname)
            return

        request = self.ecurequests.requests[requestname]
        datasenditems = request.sendbyte_dataitems
        inputlayout = self.layout['inputs']

        itemsfound = {}
        numfound = 0
        for dataitemname in datasenditems.keys():
            for inp in inputlayout:
                itemsfound[dataitemname] = False
                if dataitemname == inp['text']:
                    if requestname == inp['request']:
                        itemsfound[dataitemname] = True
                        numfound += 1
                        break

        if len(itemsfound) == numfound:
            options.main_window.logview.append(_("<font color=green>Request <font color=blue>'%s'</font> has no missing input values</font>") % requestname)
            return

        options.main_window.logview.append(_("<font color=red>Request <font color=blue>'%s'</font> has missing inputs :</font>") % requestname)
        for k, v in itemsfound.items():
            if not v:
                options.main_window.logview.append(_("<font color=orange> - '%s'</font>") % k)

    def clear(self):
        self.requesttable.clear()

    def refresh_request(self):
        if not self.ecurequests or not self.buttonlayout:
            return
        self.init(self.ecurequests, self.layout)

    def init(self, ecureq, layout):
        self.buttonlayout = layout['buttons']
        self.layout = layout
        self.ecurequests = ecureq
        self.requestcombo.clear()

        for req in sorted(ecureq.requests.keys()):
            if ecureq.requests[req].manualsend:
                self.requestcombo.addItem(req)

    def move_up(self):
        items = self.requesttable.selectedItems()
        if len(items) == 0:
            return

        currentrowidx = items[-1].row()

        if currentrowidx < 1:
            return

        params = self.currentbuttonparams.pop(currentrowidx)
        self.currentbuttonparams.insert(currentrowidx - 1, params)
        self.init_table(self.currentbuttonuniquename, self.is_screen)
        self.requesttable.selectRow(currentrowidx - 1)

    def delete_request(self):
        items = self.requesttable.selectedItems()
        if len(items) == 0:
            return

        currentrowidx = items[-1].row()
        self.currentbuttonparams.pop(currentrowidx)
        self.init_table(self.currentbuttonuniquename, self.is_screen)

    def add_request(self):
        if self.currentbuttonparams is None:
            return

        delay = self.delaybox.value()
        request = self.requestcombo.currentText()

        smap = {
            'Delay': str(delay),
            'RequestName': request
        }

        self.currentbuttonparams.append(smap)
        self.init_table(self.currentbuttonuniquename, self.is_screen)

    def init_table(self, itemname, is_screen):
        self.is_screen = is_screen
        self.requesttable.clearSelection()
        self.requesttable.clear()
        self.currentbuttonparams = None
        self.currentbuttonuniquename = None

        if not self.is_screen:
            count = 0
            for butreq in self.buttonlayout:
                if butreq['uniquename'] == itemname:
                    self.currentbuttonuniquename = itemname
                    if 'send' not in butreq:
                        continue
                    sendparams = butreq['send']
                    self.requesttable.setRowCount(len(sendparams))
                    self.currentbuttonparams = sendparams
                    for sendparam in sendparams:
                        itemreq = widgets.QTableWidgetItem(sendparam['RequestName'])
                        itemdelay = widgets.QTableWidgetItem(sendparam['Delay'])
                        self.requesttable.setItem(count, 1, itemreq)
                        self.requesttable.setItem(count, 0, itemdelay)
                        itemreq.setFlags(core.Qt.ItemIsSelectable | core.Qt.ItemIsEnabled)
                        itemdelay.setFlags(core.Qt.ItemIsSelectable | core.Qt.ItemIsEnabled)
                        count += 1
        else:
            count = 0
            sendparams = self.layout['presend']
            self.requesttable.setRowCount(len(sendparams))
            self.currentbuttonparams = sendparams
            for sendparam in sendparams:
                itemreq = widgets.QTableWidgetItem(sendparam['RequestName'])
                itemdelay = widgets.QTableWidgetItem(sendparam['Delay'])
                self.requesttable.setItem(count, 1, itemreq)
                self.requesttable.setItem(count, 0, itemdelay)
                itemreq.setFlags(core.Qt.ItemIsSelectable | core.Qt.ItemIsEnabled)
                itemdelay.setFlags(core.Qt.ItemIsSelectable | core.Qt.ItemIsEnabled)
                count += 1

        headerstrings = _("Delay;Request").split(";")
        self.requesttable.setHorizontalHeaderLabels(headerstrings)
        self.requesttable.resizeColumnsToContents()
        self.requesttable.resizeRowsToContents()


class buttonEditor(widgets.QWidget):
    """Main container for button editor"""
    def __init__(self, parent=None):
        super(buttonEditor, self).__init__(parent)
        self.ecurequestsparser = None

        self.layout = None
        self.layouth = widgets.QHBoxLayout()
        self.buttontable = widgets.QTableWidget()
        self.layoutv = widgets.QVBoxLayout()

        self.layouth.addWidget(self.buttontable)
        self.layouth.addLayout(self.layoutv)

        self.buttondata = buttonData()
        self.layoutv.addWidget(self.buttondata)

        self.setLayout(self.layouth)

        self.buttontable.setFixedWidth(250)
        self.buttontable.setColumnCount(2)
        self.buttontable.verticalHeader().hide()
        self.buttontable.setSelectionBehavior(widgets.QAbstractItemView.SelectRows)
        self.buttontable.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        #self.buttontable.setShowGrid(False)
        self.buttontable.itemSelectionChanged.connect(self.selection_changed)
        self.enable_view(False)

    def name_changed(self, r, c):
        if r == 0:
            return

        currentitem = self.buttontable.item(r, 0)

        if not currentitem:
            return

        idx = currentitem.row() - 1
        buttondata = self.layout['buttons'][idx]
        textdata = currentitem.text()

        buttondata['text'] = textdata
        buttondata['uniquename'] = textdata + u"_" + str(idx)
        self.init()
        if options.main_window:
            options.main_window.paramview.reinitScreen()

    def selection_changed(self):
        selitems = self.buttontable.selectedItems()
        if not len(selitems):
            return

        current_row = selitems[-1].row()
        is_screen = current_row == 0
        current_item_name = self.buttontable.item(current_row, 1).text()
        self.buttondata.init_table(current_item_name, is_screen)

    def set_ecu(self, ecu):
        self.ecurequestsparser = ecu
        self.enable_view(True)

    def enable_view(self, enable):
        children = self.children()
        for c in children:
            if isinstance(c, widgets.QWidget):
                c.setEnabled(enable)

    def set_layout(self, layout):
        self.layout = layout
        self.init()

    def init(self):
        try:
            self.buttontable.cellChanged.disconnect(self.name_changed)
        except:
            pass

        self.buttontable.clearSelection()
        self.buttondata.clear()

        if self.ecurequestsparser:
            self.buttondata.init(self.ecurequestsparser, self.layout)

        num_buttons = len(self.layout['buttons'])
        self.buttontable.setRowCount(num_buttons + 1)

        scitem = widgets.QTableWidgetItem(_("Screen initialization"))
        noitem = widgets.QTableWidgetItem(_("Requests to send before screen drawing"))
        self.buttontable.setItem(0, 0, scitem)
        self.buttontable.setItem(0, 1, noitem)
        scitem.setFlags(core.Qt.ItemIsSelectable | core.Qt.ItemIsEnabled)
        noitem.setFlags(core.Qt.ItemIsSelectable | core.Qt.ItemIsEnabled)

        count = 1
        for button in self.layout['buttons']:
            uniquenameitem = widgets.QTableWidgetItem(button['uniquename'])
            self.buttontable.setItem(count, 0, widgets.QTableWidgetItem(button['text']))
            self.buttontable.setItem(count, 1, uniquenameitem)
            uniquenameitem.setFlags(core.Qt.ItemIsSelectable | core.Qt.ItemIsEnabled)
            count += 1

        headerstrings = _("Button name;Unique name").split(";")
        self.buttontable.setHorizontalHeaderLabels(headerstrings)
        self.buttontable.resizeColumnsToContents()
        self.buttontable.resizeRowsToContents()
        self.buttontable.selectRow(0)
        self.buttontable.cellChanged.connect(self.name_changed)


class hexLineEdit(widgets.QLineEdit):
    def __init__(self, num, alpha):
        widgets.QLineEdit.__init__(self)
        if not alpha:
            self.setInputMask("H" * num)
        else:
            self.setInputMask("N" * num)


class hexSpinBox(widgets.QSpinBox):
    def __init__(self, iscan=True):
        widgets.QSpinBox.__init__(self)
        self.set_can(iscan)

    def set_can(self, iscan):
        if iscan:
            self.setRange(0, 0x7FF)
            self.can = True
        else:
            self.setRange(0, 0xFF)
            self.can = False

    def textFromValue(self, value):
        if self.can:
            return "%03X" % value
        else:
            return "%02X" % value

    def valueFromText(self, text):
        if len(text) == 0:
            return 0
        return int("0x" + str(text), 16)

    def validate(self, input, pos):
        if len(str(input)) == 0:
            return (gui.QValidator.Acceptable, input, pos)

        try:
            value = int("0x" + str(input)[pos-1], 16)
        except:
            return (gui.QValidator.Invalid, input, pos)

        return (gui.QValidator.Acceptable, input, pos)

class ecuParamEditor(widgets.QFrame):
    def __init__(self, parent=None):
        super(ecuParamEditor, self).__init__(parent)
        self.ecurequestsparser = None
        self.targets = None

        layoutv = widgets.QVBoxLayout()
        self.setLayout(layoutv)

        gridlayout = widgets.QGridLayout()
        self.protocolcombo = widgets.QComboBox()
        self.funcadressedit = hexSpinBox(False)

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
        self.toolecuidbox = hexSpinBox()
        self.ecutoolidbox = hexSpinBox()
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
        self.inputdiag = hexLineEdit(2, False)
        self.inputsupplier = hexLineEdit(6, True)
        self.inputsoft = hexLineEdit(4, False)
        self.inputversion = hexLineEdit(4, False)
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
