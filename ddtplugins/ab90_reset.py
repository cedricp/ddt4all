# -*- coding: utf-8 -*-

# (c) 2017

import PyQt5.QtCore as core
import PyQt5.QtWidgets as gui

import ecu
import options

_ = options.translator('ddt4all')

plugin_name = _("AB90 AIRBAG Reset")
category = _("Airbag Tools")
need_hw = True
ecufile = "AB90_J77_X85"


class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.airbag_ecu = ecu.Ecu_file(ecufile, True)
        layout = gui.QVBoxLayout()
        infos = gui.QLabel(_("AB90 (Clio III)/2<br>"
                             "AIRBAG VIRGINIZER<br><font color='red'>THIS PLUGIN WILL UNLOCK AIRBAG CRASH DATA<br>"
                             "GO AWAY IF YOU HAVE NO IDEA OF WHAT IT MEANS</font>"))
        infos.setAlignment(core.Qt.AlignHCenter)
        check_button = gui.QPushButton(_("Check ACU Virgin"))
        self.status_check = gui.QLabel(_("Waiting"))
        self.status_check.setAlignment(core.Qt.AlignHCenter)
        self.virginize_button = gui.QPushButton(_("Virginize ACU"))
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
            options.main_window.logview.append(_("Cannot connect to ECU"))
            self.finished()

    def check_virgin_status(self):
        self.start_diag_session()

        crash_reset_request = self.airbag_ecu.requests[u'Synthèse état UCE']
        values_dict = crash_reset_request.send_request({}, "62 02 04 00 00 00 00 00 00 00 00 00 00 00 00")

        if values_dict is None:
            self.status_check.setText(_("<font color='orange'>UNEXPECTED RESPONSE</font>"))

        crash = values_dict[u'crash détecté']

        if crash == u'crash détecté':
            self.status_check.setText(_("<font color='red'>CRASH DETECTED</font>"))
        else:
            self.status_check.setText(_("<font color='green'>NO CRASH DETECTED</font>"))

    def start_diag_session(self):
        sds_request = self.airbag_ecu.requests[u"Start Diagnostic Session"]

        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print("SdS stream", sds_stream)
            return
        options.elm.start_session_can(sds_stream)

    def reset_ecu(self):
        self.start_diag_session()

        reset_request = self.airbag_ecu.requests[u"Reset crash ou accès au mode fournisseur"]
        request_response = reset_request.send_request({u"code d'accès pour reset UCE": '22041998'})

        if request_response is not None:
            self.status_check.setText(_("<font color='green'>CLEAR EXECUTED</font>"))
        else:
            self.status_check.setText(_("<font color='red'>CLEAR FAILED</font>"))


def plugin_entry():
    v = Virginizer()
    v.exec_()
