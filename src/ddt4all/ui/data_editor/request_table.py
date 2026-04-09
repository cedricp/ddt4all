

import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets

import ddt4all.options as options
from ddt4all.ui.data_editor.check_box import CheckBox

_ = options.translator('ddt4all')

class RequestTable(widgets.QTableWidget):
    def __init__(self, parent=None):
        super(RequestTable, self).__init__(parent)
        self.ecureq = None
        self.sendbyteeditor = None
        self.rcvbyteeditor = None
        self.reqs = []
        self.setFixedWidth(350)
        self.setSelectionBehavior(widgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        self.verticalHeader().hide()
        # self.setShowGrid(False)
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
        except Exception:
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

            manual = CheckBox(request_inst)

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
