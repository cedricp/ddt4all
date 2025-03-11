# -*- coding: utf-8 -*-

# (c) 2017
# This is an example plugin

import PyQt5.QtCore as core
import PyQt5.QtWidgets as gui

import ecu
import options

_ = options.translator('ddt4all')

plugin_name = _("Laguna II UCH Reset")
category = _("UCH Tools")
need_hw = True
ecufile = "UCH___M2S_X74_et_X73"


class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.laguna_uch = ecu.Ecu_file(ecufile, True)
        layout = gui.QVBoxLayout()
        infos = gui.QLabel(
            _("LAGUNA II UCH VIRGINIZER<br><font color='red'>THIS PLUGIN WILL ERASE YOUR UCH<br>GO AWAY IF YOU HAVE NO IDEA OF WHAT IT MEANS</font>"))
        infos.setAlignment(core.Qt.AlignHCenter)
        check_button = gui.QPushButton(_("Check UCH Virgin"))
        self.status_check = gui.QLabel(_("Waiting"))
        self.status_check.setAlignment(core.Qt.AlignHCenter)
        self.virginize_button = gui.QPushButton(_("Virginize UCH"))
        layout.addWidget(infos)
        layout.addWidget(check_button)
        layout.addWidget(self.status_check)
        layout.addWidget(self.virginize_button)
        self.setLayout(layout)
        self.virginize_button.setEnabled(False)
        self.virginize_button.clicked.connect(self.reset_ecu)
        check_button.clicked.connect(self.check_virgin_status)
        self.ecu_connect()
        # Start comm immediately
        self.start_diag_session_study()

    def ecu_connect(self):
        connection = self.laguna_uch.connect_to_hardware()
        if not connection:
            options.main_window.logview.append(_("Cannot connect to ECU"))
            self.finished()

    def check_virgin_status(self):
        self.start_diag_session_aftersales()

        virigin_check_request = self.laguna_uch.requests[u'Lecture Etats Antidémarrage et acces']
        response_values = virigin_check_request.send_request()

        if response_values is not None:
            virgin = response_values[u"UCH vierge"]

            if virgin == u'oui':
                self.virginize_button.setEnabled(False)
                self.status_check.setText(_("<font color='green'>UCH virgin</font>"))
                return

            if virgin == u'non':
                self.virginize_button.setEnabled(True)
                self.status_check.setText(_("<font color='red'>UCH coded</font>"))
                return

        self.status_check.setText(_("<font color='orange'>UNEXPECTED RESPONSE</font>"))

    def start_diag_session_study(self):
        sds_request = self.laguna_uch.requests[u"Start Diagnostic Session"]
        sds_stream = " ".join(sds_request.build_data_stream({u'Session Name': u'Etude'}))
        if options.simulation_mode:
            print("SdSA stream", sds_stream)
            return
        options.elm.start_session_iso(sds_stream)

    def start_diag_session_aftersales(self):
        sds_request = self.laguna_uch.requests[u"Start Diagnostic Session"]
        sds_stream = " ".join(sds_request.build_data_stream({u'Session Name': u'APV'}))
        if options.simulation_mode:
            print("SdSS stream", sds_stream)
            return
        options.elm.request(sds_stream)

    def reset_ecu(self):
        self.start_diag_session_study()

        reset_request = self.laguna_uch.requests[u"Effacement_données_antidem_acces"]
        request_response = reset_request.send_request()

        if request_response is not None:
            self.status_check.setText(_("<font color='green'>CLEAR EXECUTED</font>"))
        else:
            self.status_check.setText(_("<font color='red'>CLEAR FAILED</font>"))


def plugin_entry():
    v = Virginizer()
    v.exec_()
