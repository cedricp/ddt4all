import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets

import ddt4all.options as options

_ = options.translator('ddt4all')


class ButtonData(widgets.QFrame):
    def __init__(self, parent=None):
        super(ButtonData, self).__init__(parent)
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
        # self.requesttable.setShowGrid(False)

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
            options.main_window.logview.append(
                _("<font color=green>Request</font><font color=blue>'%s'</font> has no missing input values") % requestname)
            return

        options.main_window.logview.append(
            _("<font color=red>Request</font><font color=blue>'%s'</font> has missing inputs :") % requestname)
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
