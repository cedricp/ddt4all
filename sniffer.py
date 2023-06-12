#!/usr/bin/python3
# -*- coding: utf-8 -*-
import string
import time

import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets

import ecu
import options
import version

__author__ = version.__author__
__copyright__ = version.__copyright__
__credits__ = version.__credits__
__license__ = version.__license__
__version__ = version.__version__
__maintainer__ = version.__maintainer__
__email__ = version.__email__
__status__ = version.__status__

_ = options.translator('ddt4all')


class snifferThread(core.QThread):
    # Use a thread to avoid ELM buffer flooding
    try:
        dataready = core.pyqtSignal(basestring)
    except:
        dataready = core.pyqtSignal(str)

    def __init__(self, address, br):
        super(snifferThread, self).__init__()
        self.filter = address
        self.running = True
        if not options.simulation_mode:
            options.elm.monitorstop = False
            options.elm.init_can_sniffer(self.filter, br)

    def stop(self):
        if not options.simulation_mode:
            options.elm.monitorstop = True
        else:
            return

        while self.running:
            time.sleep(.1)

    def senddata(self, data):
        self.dataready.emit(data)

    def run(self):
        if options.simulation_mode:
            if options.simulation_mode:
                while 1:
                    time.sleep(.1)
                    # Test data
                    self.dataready.emit("0300000000400000")
            return

        while not options.elm.monitorstop:
            options.elm.monitor_can_bus(self.senddata)

        self.running = False


class sniffer(widgets.QWidget):
    def __init__(self, parent=None):
        super(sniffer, self).__init__(parent)
        self.ecu_file = None
        self.ecurequests = None
        self.snifferthread = None
        self.currentrequest = None
        self.names = []
        self.oktostart = False
        self.ecu_filter = ""

        hlayout = widgets.QHBoxLayout()

        self.framecombo = widgets.QComboBox()

        self.startbutton = widgets.QPushButton(">>")
        self.addressinfo = widgets.QLabel("0000")

        self.startbutton.setCheckable(True)
        self.startbutton.toggled.connect(self.startmonitoring)

        self.addressinfo.setFixedWidth(90)
        self.startbutton.setFixedWidth(90)

        hlayout.addWidget(self.addressinfo)
        hlayout.addWidget(self.framecombo)
        hlayout.addWidget(self.startbutton)

        vlayout = widgets.QVBoxLayout()
        self.setLayout(vlayout)

        vlayout.addLayout(hlayout)

        self.table = widgets.QTableWidget()
        vlayout.addWidget(self.table)

        self.framecombo.activated.connect(self.change_frame)

    def startmonitoring(self, onoff):
        if onoff:
            if self.oktostart:
                self.startthread(self.ecu_filter)
        else:
            self.stopthread()

    def change_frame(self):
        self.stopthread()
        self.startbutton.setChecked(False)
        self.names = []
        framename = self.framecombo.currentText()
        self.currentrequest = self.ecurequests.requests[framename]
        self.ecu_filter = self.currentrequest.sentbytes
        self.addressinfo.setText(self.ecu_filter)

        self.names = self.currentrequest.dataitems.keys()

        headernames = ";".join([n for n in self.names])

        self.table.clear()
        self.table.setColumnCount(1)
        self.table.setRowCount(len(self.names))
        headerstrings = headernames.split(";")
        self.table.setVerticalHeaderLabels(headerstrings)
        self.table.setHorizontalHeaderLabels([_("Values")])

        for i in range(0, len(self.names)):
            item = widgets.QTableWidgetItem(_("Waiting..."))
            item.setFlags(item.flags() ^ core.Qt.ItemIsEditable)
            self.table.setItem(i, 0, item)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(0, widgets.QHeaderView.Stretch)

    def stopthread(self):
        if self.snifferthread:
            self.snifferthread.stop()
            self.snifferthread.dataready.disconnect()
            self.snifferthread.quit()

        self.snifferthread = None
        self.framecombo.setEnabled(True)

    def startthread(self, ecu_filter):
        self.framecombo.setEnabled(False)
        self.stopthread()

        self.snifferthread = snifferThread(ecu_filter, self.ecurequests.baudrate)
        self.snifferthread.dataready.connect(self.callback)
        self.snifferthread.start()

    def set_file(self, ecufile):
        self.stopthread()
        self.ecu_file = ecufile
        return self.init()

    def callback(self, stream):
        data = str(stream).replace(" ", "").strip()

        if '0:' in data:
            return

        if len(data) > 16:
            print("Frame length error : ", data)
            return

        if not all(c in string.hexdigits for c in data):
            print(_("Frame hex error : "), data)
            return

        data = data.replace(' ', '').ljust(16, "0")

        if self.currentrequest:
            values = self.currentrequest.get_values_from_stream(data)
            i = 0
            for name in self.names:
                if name in values:
                    value = values[name]
                    if value is not None:
                        self.table.item(i, 0).setText(value)
                i += 1

    def init(self):
        self.ecurequests = ecu.Ecu_file(self.ecu_file, True)
        self.framecombo.clear()
        self.table.clear()
        self.table.setRowCount(0)
        self.currentrequest = None
        self.oktostart = False
        self.startbutton.setEnabled(False)

        if not (self.ecurequests.funcaddr == "00" or self.ecurequests.funcaddr == "FF"):
            self.ecu_file = None
            self.ecurequests = None
            return False

        for req in sorted(self.ecurequests.requests.keys()):
            if 'DTOOL' not in req.upper():
                self.framecombo.addItem(req)

        self.oktostart = True
        self.startbutton.setEnabled(True)
        return True
