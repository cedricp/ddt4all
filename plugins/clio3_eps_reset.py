# -*- coding: utf-8 -*-

# (c) 2017


import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import ecu
import options
import elm

plugin_name = "Modus/Clio III EPS Reset"
category = "EPS Tools"
need_hw = True
ecufile = "DAE_J77_X85_Gen2___v3.7"

class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.clio_eps = ecu.Ecu_file(ecufile, True)
        layout = gui.QVBoxLayout()
        infos = gui.QLabel("Modus/Clio III EPS VIRGINIZER<br><font color='red'>THIS PLUGIN WILL RESET EPS IMMO DATA<br>GO AWAY IF YOU HAVE NO IDEA OF WHAT IT MEANS</font")
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
        connection = self.clio_eps.connect_to_hardware()
        if not connection:
            options.main_window.logview.append("Cannot connect to ECU")
            self.finished()

    def check_virgin_status(self):
        virigin_check_request = self.clio_eps.requests[u'RDBLI - System Frame']
        virgin_check_values = virigin_check_request.send_request({}, "62 01 64 00 00 00 00 00 00 00 00 00 00 00 00"\
                                                                 "00 00 00 00 00 00 00 00 00")

        if virgin_check_values is not None:
            virgin_status = virgin_check_values[u"Dongle status"]

            if options.debug:
                print virgin_status

            if virgin_status == u'Système VIERGE - Aucun code mémorisé':
                self.virginize_button.setEnabled(False)
                self.status_check.setText("<font color='green'>EPS virgin</font>")
                return
            else:
                self.virginize_button.setEnabled(True)
                self.status_check.setText("<font color='red'>EPS coded</font>")
                return

        self.status_check.setText("<font color='orange'>UNEXPECTED RESPONSE</font>")

    def start_diag_session_fb(self):
        sds_request = self.clio_eps.requests[u"SDS - Start Diagnostic $FB"]
        sds_stream = " ".join(sds_request.build_data_stream({}))

        if options.simulation_mode:
            print "SdSFB stream", sds_stream
            return

        options.elm.start_session_can(sds_stream)

    def reset_ecu(self):
        reset_request = self.clio_eps.requests[u"WDBLI - Erase of Dongle_ID code"]
        request_response = reset_request.send_request()

        if request_response is not None:
            self.status_check.setText("<font color='green'>CLEAR EXECUTED</font>")
        else:
            self.status_check.setText("<font color='red'>CLEAR FAILED</font>")


def plugin_entry():
    v = Virginizer()
    v.exec_()
