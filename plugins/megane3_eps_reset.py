# -*- coding: utf-8 -*-

# (c) 2017


import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import ecu
import options
import elm

plugin_name = "ZOE/FLENCE/Megane III/Scenic III EPS Reset"
category = "EPS Tools"
need_hw = True


class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.megane_eps = ecu.Ecu_file("DAE_X95_X38_X10_v1.88_20120228T113904", True)
        layout = gui.QVBoxLayout()
        infos = gui.QLabel("ZOE/FLENCE/Megane III/Scenic III EPS VIRGINIZER<br><font color='red'>THIS PLUGIN WILL RESET EPS IMMO DATA<br>GO AWAY IF YOU HAVE NO IDEA OF WHAT IT MEANS</font")
        infos.setAlignment(core.Qt.AlignHCenter)
        check_button = gui.QPushButton("Check EPS Virgin")
        self.status_check = gui.QLabel("Waiting")
        self.status_check.setAlignment(core.Qt.AlignHCenter)
        self.virginize_button = gui.QPushButton("Virginize EPS")
        layout.addWidget(infos)
        layout.addWidget(check_button)
        layout.addWidget(self.status_check)
        layout.addWidget(self.virginize_button)
        self.setLayout(layout)
        self.virginize_button.setEnabled(False)
        self.virginize_button.clicked.connect(self.reset_ecu)
        check_button.clicked.connect(self.check_virgin_status)
        self.ecu_connect()

    def ecu_connect(self):
        short_addr = elm.get_can_addr(self.megane_eps.ecu_send_id)
        ecu_conf = {'idTx': self.megane_eps.ecu_send_id, 'idRx':
            self.megane_eps.ecu_recv_id, 'ecuname': ""}
        if not options.simulation_mode:
            options.elm.set_can_addr(short_addr, ecu_conf)
        else:
            print "Connect to ", self.megane_eps.ecu_send_id, self.megane_eps.ecu_recv_id

    def check_virgin_status(self):
        virgin_data_name = u"DID - Dongle state"
        virigin_check_request = self.megane_eps.requests[u'DataRead.DID - Dongle state']
        virgin_data_bit = virigin_check_request.dataitems[virgin_data_name]
        virgin_ecu_data = self.megane_eps.data[virgin_data_name]

        request_stream = virigin_check_request.build_data_stream({})
        request_stream = " ".join(request_stream)

        self.start_diag_session_fa()
        if options.simulation_mode:
            # Simulate virgin ECU
            # Blank bit is 4th byte (0=learnt, 1=blank,3=not operational)
            elmstream = "62 01 64 00 00 00 00 00 00 00 00 00 00 FF 00"
            # Simulate coded ECU
            elmstream = "62 01 64 00 00 00 00 00 00 00 00 00 00 00 00"
            print "Send request stream", request_stream
        else:
            elmstream = options.elm.request(request_stream)

        if elmstream == "WRONG RESPONSE":
            self.virginize_button.setEnabled(False)
            self.status_check.setText("<font color='red'>Communication problem</font>")
            return

        value = virgin_ecu_data.getIntValue(elmstream, virgin_data_bit, self.megane_eps.endianness)
        virgin = value == 1
        not_operational = value == 3

        if not_operational:
            self.virginize_button.setEnabled(False)
            self.status_check.setText("<font color='green'>EPS not operational</font>")
            return

        if virgin:
            self.virginize_button.setEnabled(False)
            self.status_check.setText("<font color='green'>EPS virgin</font>")
            return
        else:
            self.virginize_button.setEnabled(True)
            self.status_check.setText("<font color='red'>EPS coded</font>")
            return

    def start_diag_session_fa(self):
        sds_request = self.megane_eps.requests[u"SDS - Start Diagnostic Session $FA"]
        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print "SdSFA stream", sds_stream
            return
        options.elm.start_session_can(sds_stream)

    def reset_ecu(self):
        reset_request = self.megane_eps.requests[u"SRBLID - Dongle blanking"]
        reset_stream = " ".join(reset_request.build_data_stream({}))
        self.start_diag_session_fa()
        if options.simulation_mode:
            print "Reset stream", reset_stream
            return
        # Reset can only be done in study diag session
        options.elm.request(reset_stream)


def plugin_entry():
    v = Virginizer()
    v.exec_()
