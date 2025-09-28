# -*- coding: utf-8 -*-

# (c) 2017


import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import ecu
import options
import elm

_ = options.translator('ddt4all')

plugin_name = _("Megane/Scenic III UCH Reset")
category = _("UCH Tools")
need_hw = True
ecufile = "BCM_X95_SW_2_V_1_2"

class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.megane_uch = ecu.Ecu_file(ecufile, True)
        layout = gui.QVBoxLayout()
        infos = gui.QLabel(_("MEGANE III UCH VIRGINIZER<br><font color='red'>THIS PLUGIN WILL ERASE YOUR UCH<br>GO AWAY IF YOU HAVE NO IDEA OF WHAT IT MEANS</font>"))
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

    def ecu_connect(self):
        connection = self.megane_uch.connect_to_hardware()
        if not connection:
            options.main_window.logview.append(_("Cannot connect to ECU"))
            self.finished()

    def check_virgin_status(self):
        self.start_diag_session_aftersales()

        virigin_check_request = self.megane_uch.requests[u'Read_A_AC_General_Identifiers_Learning_Status_(bits)_BCM_Input/Output']
        virgin_check_request_values = virigin_check_request.send_request()

        if virgin_check_request_values is not None:
            virgin_value = virgin_check_request_values[u"VSC UCH vierge (NbBadgeAppris=0)"]

            if virgin_value == u'Actif':
                self.virginize_button.setEnabled(False)
                self.status_check.setText(_("<font color='green'>UCH virgin</font>"))
                return

            if virgin_value == u'inactif':
                self.virginize_button.setEnabled(True)
                self.status_check.setText(_("<font color='red'>UCH coded</font>"))
                return

        self.status_check.setText(_("<font color='orange'>UNEXPECTED RESPONSE</font>"))

    def start_diag_session_aftersales(self):
        sds_request = self.megane_uch.requests[u"Start Diagnostic Session"]
        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print "SdSS stream", sds_stream
            return
        options.elm.start_session_can(sds_stream)

    def reset_ecu(self):
        self.start_diag_session_aftersales()

        reset_request = self.megane_uch.requests[u"SR_RESERVED VSC 1"]
        request_response = reset_request.send_request()

        if request_response is not None:
            self.status_check.setText(_("<font color='green'>CLEAR EXECUTED</font>"))
        else:
            self.status_check.setText(_("<font color='red'>CLEAR FAILED</font>"))


def plugin_entry():
    v = Virginizer()
    v.exec_()
