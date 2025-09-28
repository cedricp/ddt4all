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
        connection = self.megane_eps.connect_to_hardware()
        if not connection:
            options.main_window.logview.append("Cannot connect to ECU")
            self.finished()

    def check_virgin_status(self):
        self.start_diag_session_c0()

        virigin_check_request = self.megane_eps.requests[u'DataRead.DID - Dongle state']
        request_response = virigin_check_request.send_request({}, "62 01 64 00 00 00 00 00 00 00 00 00 00 00 00")

        if request_response is not None:
            if u'DID - Dongle state' in request_response:
                donglestate = request_response[u'DID - Dongle state']
                if donglestate == u'Not operational':
                    self.virginize_button.setEnabled(False)
                    self.status_check.setText("<font color='green'>EPS not operational</font>")
                    return

                if donglestate == u'Operational blank':
                    self.virginize_button.setEnabled(False)
                    self.status_check.setText("<font color='green'>EPS virgin</font>")
                    return

                if donglestate == u'Operational learnt':
                    self.virginize_button.setEnabled(True)
                    self.status_check.setText("<font color='red'>EPS coded</font>")
                    return

        self.status_check.setText("<font color='orange'>UNEXPECTED RESPONSE</font>")

    def start_diag_session_fa(self):
        sds_request = self.megane_eps.requests[u"SDS - Start Diagnostic Session $FA"]
        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print "SdSFA stream", sds_stream
            return
        options.elm.start_session_can(sds_stream)

    def start_diag_session_c0(self):
        sds_request = self.megane_eps.requests[u"SDS - Start Diagnostic Session $C0"]
        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print "SdSC0 stream", sds_stream
            return
        options.elm.start_session_can(sds_stream)

    def reset_ecu(self):
        self.start_diag_session_fa()

        reset_request = self.megane_eps.requests[u"SRBLID - Dongle blanking"]
        request_response = reset_request.send_request()

        if request_response is not None:
            self.status_check.setText("<font color='green'>CLEAR EXECUTED</font>")
        else:
            self.status_check.setText("<font color='red'>CLEAR FAILED</font>")

def plugin_entry():
    v = Virginizer()
    v.exec_()
