import time

import PyQt5.QtCore as core

import ddt4all.options as options

class SnifferThread(core.QThread):
    # Use a thread to avoid ELM buffer flooding
    try:
        # TODO:// basestring not defined use bytes.
        # dataready = core.pyqtSignal(basestring)
        dataready = core.pyqtSignal(bytes)
    except Exception:
        dataready = core.pyqtSignal(str)

    def __init__(self, address, br):
        super(SnifferThread, self).__init__()
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
