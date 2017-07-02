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


class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.airbag_ecu = ecu.Ecu_file("RSAT4_ACU_eng_v15_20150511T131328", True)
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
        short_addr = elm.get_can_addr(self.airbag_ecu.ecu_send_id)
        ecu_conf = {'idTx': self.airbag_ecu.ecu_send_id, 'idRx':
            self.airbag_ecu.ecu_recv_id, 'ecuname': ""}
        if not options.simulation_mode:
            options.elm.set_can_addr(short_addr, ecu_conf)
        else:
            print "Connect to ", self.airbag_ecu.ecu_send_id, self.airbag_ecu.ecu_recv_id

    def check_virgin_status(self):
        crash_data_name = u"crash detected"
        crash_reset_request = self.airbag_ecu.requests[u'Reading of ECU state synthesis']
        virgin_data_bit = crash_reset_request.dataitems[crash_data_name]
        virgin_ecu_data = self.airbag_ecu.data[crash_data_name]

        request_stream = crash_reset_request.build_data_stream({})
        request_stream = " ".join(request_stream)

        self.start_diag_session_fb()
        if options.simulation_mode:
            # Simulate virgin ECU
            # Blank bit is 3rd byte bit 5
            elmstream = "61 02 00 00 00 00 00 00 00 00 00 00 00 FF 00"
            # Simulate coded ECU
            elmstream = "62 02 04 00 00 00 00 00 00 00 00 00 00 00 00"
            print "Send request stream", request_stream
        else:
            elmstream = options.elm.request(request_stream)

        if elmstream == "WRONG RESPONSE":
            self.virginize_button.setEnabled(False)
            self.status_check.setText("<font color='red'>Communication problem</font>")
            return

        crash = virgin_ecu_data.getIntValue(elmstream, virgin_data_bit, self.airbag_ecu.endianness) == 1

        if crash:
            self.status_check.setText("<font color='red'>CRASH DETECTED</font>")
        else:
            self.status_check.setText("<font color='green'>NO CRASH DETECTED</font>")

    def start_diag_session_fb(self):
        sds_request = self.airbag_ecu.requests[u"Start Diagnostic Session"]

        sds_stream = " ".join(sds_request.build_data_stream({u'Session Name': u'extendedDiagnosticSession'}))
        if options.simulation_mode:
            print "SdSEX stream", sds_stream
            return
        options.elm.start_session_can(sds_stream)

    def reset_ecu(self):
        reset_request = self.airbag_ecu.requests[u"Reset Crash"]
        reset_stream = " ".join(reset_request.build_data_stream({u'CLEDEV For reset crash': '13041976'}))
        self.start_diag_session_fb()
        if options.simulation_mode:
            print "Reset stream", reset_stream
            return
        # Reset can only be done in study diag session
        options.elm.request(reset_stream)


def plugin_entry():
    v = Virginizer()
    v.exec_()
