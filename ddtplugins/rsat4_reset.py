# -*- coding: utf-8 -*-

# (c) 2017


import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import ecu
import options
import elm

plugin_name = "RSAT4 AIRBAG Reset"
category = "Airbag Tools"
need_hw = True
ecufile = "RSAT4_ACU_eng_v15_20150511T131328"

class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.airbag_ecu = ecu.Ecu_file(ecufile, True)
        layout = gui.QVBoxLayout()
        infos = gui.QLabel("TWINGO III/ZOE/DOKKER/DUSTER ph2/TRAFIC III/CAPTUR/LODGY ph1/2<br>"
                           "AIRBAG VIRGINIZER<br><font color='red'>THIS PLUGIN WILL UNLOCK AIRBAG CRASH DATA<br>"
                           "GO AWAY IF YOU HAVE NO IDEA OF WHAT IT MEANS</font")
        infos.setAlignment(core.Qt.AlignHCenter)
        check_button = gui.QPushButton("Check ACU Virgin")
        self.status_check = gui.QLabel("Waiting")
        self.status_check.setAlignment(core.Qt.AlignHCenter)
        self.virginize_button = gui.QPushButton("Virginize ACU")
        layout.addWidget(infos)
        layout.addWidget(check_button)
        layout.addWidget(self.status_check)
        layout.addWidget(self.virginize_button)
        self.setLayout(layout)
        self.virginize_button.setEnabled(True)
        self.virginize_button.clicked.connect(self.reset_ecu)
        check_button.clicked.connect(self.check_virgin_status)
        self.ecu_connect()

    def ecu_connect(self):
        connection = self.airbag_ecu.connect_to_hardware()
        if not connection:
            options.main_window.logview.append("Cannot connect to ECU")
            self.finished()

    def check_virgin_status(self):
        self.start_diag_session()

        crash_reset_request = self.airbag_ecu.requests[u'Reading of ECU state synthesis']
        crash_response = crash_reset_request.send_request({}, "62 02 04 00 00 00 00 00 00 00 00 00 00 00 00")

        if crash_response is not None:
            if u"crash detected" in crash_response:
                crash = crash_response[u"crash detected"]

                if crash == u'crash detected':
                    self.status_check.setText("<font color='red'>CRASH DETECTED</font>")
                    return
                if crash == u'no crash detected':
                    self.status_check.setText("<font color='green'>NO CRASH DETECTED</font>")
                    return

        self.status_check.setText("<font color='orange'>UNEXPECTED RESPONSE</font>")

    def start_diag_session(self):
        sds_request = self.airbag_ecu.requests[u"Start Diagnostic Session"]

        sds_stream = " ".join(sds_request.build_data_stream({u'Session Name': u'extendedDiagnosticSession'}))
        if options.simulation_mode:
            print "SdSEX stream", sds_stream
            return
        options.elm.start_session_can(sds_stream)

    def reset_ecu(self):
        self.start_diag_session()

        reset_request = self.airbag_ecu.requests[u"Reset Crash"]
        request_response = reset_request.send_request({u'CLEDEV For reset crash': '13041976'})

        if request_response is not None:
            self.status_check.setText("<font color='green'>CLEAR EXECUTED</font>")
        else:
            self.status_check.setText("<font color='red'>CLEAR FAILED</font>")


def plugin_entry():
    v = Virginizer()
    v.exec_()
