# -*- coding: utf-8 -*-

import time
import ecu
from uiutils import *
import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import options

__author__ = "Cedric PAILLE"
__copyright__ = "Copyright 2016-2017"
__credits__ = []
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Cedric PAILLE"
__email__ = "cedricpaille@gmail.com"
__status__ = "Beta"


class snifferThread(core.QThread):
    dataready = core.pyqtSignal(basestring)

    def __init__(self, address):
        super(snifferThread, self).__init__()
        self.filter = address
        self.running = True
        if not options.simulation_mode:
            options.elm.init_can_sniffer(self.filter)

    def stop(self):
        self.running = False

    def senddata(self, data):
        self.dataready.emit(data)

    def run(self):
        while self.running:
            if options.simulation_mode:
                time.sleep(.1)
                self.dataready.emit("065A 0123456789ABCDEF")
            else:
                options.elm.monitor_can_bus(self.senddata)

class sniffer(gui.QWidget):
    def __init__(self, parent=None):
        super(sniffer, self).__init__(parent)
        self.ecu_file = None
        self.ecurequests = None
        self.snifferthread = None
        self.currentrequest = None
        self.names = []
        self.oktostart = False
        self.ecu_filter = ""

        hlayout = gui.QHBoxLayout()

        self.framecombo = gui.QComboBox()

        self.startbutton = gui.QPushButton(">>")
        self.addressinfo = gui.QLabel("0000")

        self.startbutton.setCheckable(True)
        self.startbutton.toggled.connect(self.startmonitoring)

        self.addressinfo.setFixedWidth(90)
        self.startbutton.setFixedWidth(90)

        hlayout.addWidget(self.addressinfo)
        hlayout.addWidget(self.framecombo)
        hlayout.addWidget(self.startbutton)

        vlayout = gui.QVBoxLayout()
        self.setLayout(vlayout)

        vlayout.addLayout(hlayout)

        self.table = gui.QTableWidget()
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
        framename = unicode(self.framecombo.currentText().toUtf8(), encoding="UTF-8")
        self.currentrequest = self.ecurequests.requests[framename]
        self.ecu_filter = self.currentrequest.sentbytes
        self.addressinfo.setText(self.ecu_filter)

        self.names = self.currentrequest.dataitems.keys()

        headernames = ";".join([n for n in self.names])

        self.table.setColumnCount(1)
        self.table.setRowCount(len(self.names))
        headerstrings = core.QString(headernames).split(";")
        self.table.setVerticalHeaderLabels(headerstrings)
        self.table.setHorizontalHeaderLabels(["Values"])

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def stopthread(self):
        if self.snifferthread:
            self.snifferthread.dataready.disconnect()
            self.snifferthread.quit()
        self.snifferthread = None

    def startthread(self, ecu_filter):
        self.stopthread()

        self.snifferthread = snifferThread(ecu_filter)
        self.snifferthread.dataready.connect(self.callback)
        self.snifferthread.start()

    def set_file(self, ecufile):
        self.stopthread()
        self.ecu_file = ecufile
        return self.init()

    def callback(self, stream):
        stream = str(stream)
        data = stream.split(" ")[1]
        print data
        if self.currentrequest:
            values = self.currentrequest.get_values_from_stream(data)
            i = 0
            for name in self.names:
                if name in values:
                    self.table.setItem(i, 0, gui.QTableWidgetItem(values[name]))
                i += 1

    def init(self):
        self.ecurequests = ecu.Ecu_file(self.ecu_file, True)
        self.framecombo.clear()
        self.table.clear()
        self.currentrequest = None
        self.oktostart = False
        self.startbutton.setEnabled(False)

        if self.ecurequests.funcaddr != "00":
            self.ecu_file = None
            self.ecurequests = None
            return False

        for req in self.ecurequests.requests.keys():
            self.framecombo.addItem(req)

        self.oktostart = True
        self.startbutton.setEnabled(True)
        return True
