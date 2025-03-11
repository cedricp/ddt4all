# -*- coding: utf-8 -*-

# (c) 2017

import PyQt5.QtCore as core
import PyQt5.QtWidgets as gui

import ecu
import options

_ = options.translator('ddt4all')

plugin_name = _("Clio IV EPS Reset")
category = _("EPS Tools")
need_hw = True
ecufile = "X98ph2_X87ph2_EPS_HFP_v1.00_20150622T140219_20160726T172209"


class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.clio_eps = ecu.Ecu_file(ecufile, True)
        layout = gui.QVBoxLayout()
        infos = gui.QLabel(
            _("Clio IV EPS VIRGINIZER<br><font color='red'>THIS PLUGIN WILL RESET EPS IMMO DATA<br>GO AWAY IF YOU HAVE NO IDEA OF WHAT IT MEANS</font>"))
        infos.setAlignment(core.Qt.AlignHCenter)
        check_button = gui.QPushButton(_("Check EPS Virgin"))
        self.status_check = gui.QLabel(_("Waiting"))
        self.status_check.setAlignment(core.Qt.AlignHCenter)
        self.virginize_button = gui.QPushButton(_("Virginize EPS"))
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
        connection = self.clio_eps.connect_to_hardware()
        if not connection:
            options.main_window.logview.append(_("Cannot connect to ECU"))
            self.finished()

    def check_virgin_status(self):
        self.start_diag_session_c0()

        virigin_check_request = self.clio_eps.requests[u'DataRead.DongleState']
        request_values = virigin_check_request.send_request()

        if request_values is not None:
            if u'DongleState' in request_values:
                donglestate = request_values[u'DongleState']

                if donglestate == u'NotOperational':
                    self.virginize_button.setEnabled(False)
                    self.status_check.setText(_("<font color='green'>EPS not operational</font>"))
                    return

                if donglestate == u'OperationalBlanked':
                    self.virginize_button.setEnabled(False)
                    self.status_check.setText(_("<font color='green'>EPS virgin</font>"))
                    return

                if donglestate == u'OperationalLearnt':
                    self.virginize_button.setEnabled(True)
                    self.status_check.setText(_("<font color='red'>EPS coded</font>"))
                    return

        self.status_check.setText(_("<font color='red'>UNEXPECTED RESPONSE</font>"))

    def start_diag_session_fa(self):
        sds_request = self.clio_eps.requests[u"StartDiagnosticSession.supplierSession"]
        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print("SdSFA stream", sds_stream)
            return
        options.elm.start_session_can(sds_stream)

    def start_diag_session_c0(self):
        sds_request = self.clio_eps.requests[u"StartDiagnosticSession.extendedSession"]
        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print("SdSC0 stream", sds_stream)
            return
        options.elm.start_session_can(sds_stream)

    def reset_ecu(self):
        self.start_diag_session_fa()

        reset_request = self.clio_eps.requests[u"SRBLID.DongleBlanking.Request"]
        request_response = reset_request.send_request({u'Dongle.Code': '1976'})

        if request_response is not None:
            self.status_check.setText(_("<font color='green'>CLEAR EXECUTED</font>"))
        else:
            self.status_check.setText(_("<font color='red'>CLEAR FAILED</font>"))


def plugin_entry():
    v = Virginizer()
    v.exec_()
