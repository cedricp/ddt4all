# -*- coding: utf-8 -*-

# (c) 2017
# This is an example plugin


import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import ecu
import options
import elm

plugin_name = "Laguna II UCH Reset"
category = "UCH Tools"
need_hw = True


class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.laguna_uch = ecu.Ecu_file("UCH___M2S_X74_et_X73.json", True)
        layout = gui.QVBoxLayout()
        infos = gui.QLabel("LAGUNA II UCH VIRGINIZER<br><font color='red'>THIS PLUGIN WILL ERASE YOUR UCH<br>GO AWAY IF YOU HAVE NO IDEA OF WHAT IT MEANS</font")
        infos.setAlignment(core.Qt.AlignHCenter)
        check_button = gui.QPushButton("Check UCH Virgin")
        self.status_check = gui.QLabel("Waiting")
        self.status_check.setAlignment(core.Qt.AlignHCenter)
        self.virginize_button = gui.QPushButton("Virginize UCH")
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
        ecu_conf = {'idTx': '', 'idRx': '', 'ecuname': '', 'protocol': 'KWP2000'}
        if not options.simulation_mode:
            options.elm.set_iso_addr(self.laguna_uch.funcaddr, ecu_conf)
        else:
            print "Connect to ", self.laguna_uch.funcaddr

    def check_virgin_status(self):
        virgin_data_name = u"UCH vierge"
        virigin_check_request = self.laguna_uch.requests[u'Lecture Etats Antidémarrage et acces']
        virgin_data_bit = virigin_check_request.dataitems[virgin_data_name]
        virgin_ecu_data = self.laguna_uch.data[virgin_data_name]

        request_stream = virigin_check_request.build_data_stream({})
        request_stream = " ".join(request_stream)

        self.start_diag_session_aftersales()
        if options.simulation_mode:
            # Simulate coded ECU (third byte 1st bit)
            elmstream = "61 DB 00 00 00 00 00 00 00 00 00 00 00 00 00"
            print "Send request stream", request_stream
        else:
            elmstream = options.elm.request(request_stream)

        if elmstream == "WRONG RESPONSE":
            self.virginize_button.setEnabled(False)
            self.status_check.setText("<font color='red'>Communication problem</font>")
            return

        virgin = virgin_ecu_data.getIntValue(elmstream, virgin_data_bit, self.laguna_uch.endianness) == 1

        if virgin:
            self.virginize_button.setEnabled(False)
            self.status_check.setText("<font color='green'>UCH virgin</font>")
            return
        else:
            self.virginize_button.setEnabled(True)
            self.status_check.setText("<font color='red'>UCH coded</font>")
            return

    def start_diag_session_study(self):
        sds_request = self.laguna_uch.requests[u"Start Diagnostic Session"]
        sds_stream = " ".join(sds_request.build_data_stream({u'Session Name': u'Etude'}))
        if options.simulation_mode:
            print "SdSA stream", sds_stream
            return
        options.elm.start_session_iso(sds_stream)

    def start_diag_session_aftersales(self):
        sds_request = self.laguna_uch.requests[u"Start Diagnostic Session"]
        sds_stream = " ".join(sds_request.build_data_stream({u'Session Name': u'APV'}))
        if options.simulation_mode:
            print "SdSS stream", sds_stream
            return
        options.elm.request(sds_stream)

    def reset_ecu(self):
        reset_request = self.laguna_uch.requests[u"Effacement_données_antidem_acces"]
        reset_stream = " ".join(reset_request.build_data_stream({u'Code effacement': 'C2'}))
        self.start_diag_session_study()
        if options.simulation_mode:
            print "Reset stream", reset_stream
            return
        # Reset can only be done in study diag session
        options.elm.request(reset_stream)


def plugin_entry():
    v = Virginizer()
    v.exec_()
