# -*- coding: utf-8 -*-

# (c) 2017


import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import ecu
import options
import elm

plugin_name = "Megane3 AIRBAG Reset"
category = "Airbag Tools"
need_hw = True
ecufile = "MRSZ_X95_L38_L43_L47_20110505T101858"

class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.airbag_ecu = ecu.Ecu_file(ecufile, True)
        layout = gui.QVBoxLayout()
        infos = gui.QLabel("Megane III<br>"
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

        crash_reset_request = self.airbag_ecu.requests[u'Synthèse état UCE avant crash']
        values_dict = crash_reset_request.send_request({}, "62 02 04 00 00 00 00 00 00 00 00 00 00 00 00")

        if values_dict is None:
            self.status_check.setText("<font color='orange'>UNEXPECTED RESPONSE</font>")

        crash = values_dict[u'crash détecté']

        if options.debug:
            print ">> ", crash

        if crash == u'crash détecté':
            self.status_check.setText("<font color='red'>CRASH DETECTED</font>")
        else:
            self.status_check.setText("<font color='green'>NO CRASH DETECTED</font>")

    def start_diag_session_fa(self):
        sds_request = self.airbag_ecu.requests[u"Start Diagnostic Session"]

        sds_stream = " ".join(sds_request.build_data_stream({u"Session Name": u"systemSupplierSpecific"}))
        if options.simulation_mode:
            print "SdSFA stream", sds_stream
            return
        options.elm.start_session_can(sds_stream)

    def start_diag_session(self):
        sds_request = self.airbag_ecu.requests[u"Start Diagnostic Session"]

        sds_stream = " ".join(sds_request.build_data_stream({u"Session Name": u"extendedDiagnosticSession"}))
        if options.simulation_mode:
            print "SdS stream", sds_stream
            return
        options.elm.start_session_can(sds_stream)

    def reset_ecu(self):
        self.start_diag_session_fa()

        reset_request = self.airbag_ecu.requests[u"Reset crash ou accès au mode fournisseur"]
        request_response = reset_request.send_request({u"code d'accès pour reset UCE": '27081977'})

        if request_response is not None:
            self.status_check.setText("<font color='green'>CLEAR EXECUTED</font>")
        else:
            self.status_check.setText("<font color='red'>CLEAR FAILED</font>")


def plugin_entry():
    v = Virginizer()
    v.exec_()
