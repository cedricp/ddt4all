# -*- coding: utf-8 -*-

# (c) 2017


import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import ecu
import options
import elm

plugin_name = "Megane/Scenic III UCH Reset"
category = "UCH Tools"
need_hw = True


class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.megane_uch = ecu.Ecu_file("BCM_X95_SW_2_V_1_2.json", True)
        layout = gui.QVBoxLayout()
        infos = gui.QLabel("MEGANE III UCH VIRGINIZER<br><font color='red'>THIS PLUGIN WILL ERASE YOUR UCH<br>GO AWAY IF YOU HAVE NO IDEA OF WHAT IT MEANS</font")
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

    def ecu_connect(self):
        short_addr = elm.get_can_addr(self.megane_uch.ecu_send_id)
        ecu_conf = {'idTx': self.megane_uch.ecu_send_id, 'idRx':
            self.megane_uch.ecu_recv_id, 'ecuname': ""}
        if not options.simulation_mode:
            options.elm.set_can_addr(short_addr, ecu_conf)
        else:
            print "Connect to ", self.megane_uch.ecu_send_id, self.megane_uch.ecu_recv_id

    def check_virgin_status(self):
        virgin_data_name = u"VSC UCH vierge (NbBadgeAppris=0)"
        virigin_check_request = self.megane_uch.requests[u'Read_A_AC_General_Identifiers_Learning_Status_(bits)_BCM_Input/Output']
        virgin_data_bit = virigin_check_request.dataitems[virgin_data_name]
        virgin_ecu_data = self.megane_uch.data[virgin_data_name]

        request_stream = virigin_check_request.build_data_stream({})
        request_stream = " ".join(request_stream)

        self.start_diag_session_aftersales()
        if options.simulation_mode:
            # Simulate virgin ECU
            elmstream = "61 06 00 00 00 00 00 00 00 00 00 00 00 FF 00"
            # Simulate coded ECU
            elmstream = "61 06 00 00 00 00 00 00 00 00 00 00 00 00 00"
            print "Send request stream", request_stream
        else:
            elmstream = options.elm.request(request_stream)

        if elmstream == "WRONG RESPONSE":
            self.virginize_button.setEnabled(False)
            self.status_check.setText("<font color='red'>Communication problem</font>")
            return

        virgin = virgin_ecu_data.getIntValue(elmstream, virgin_data_bit, self.megane_uch.endianness) == 1

        if virgin:
            self.virginize_button.setEnabled(False)
            self.status_check.setText("<font color='green'>UCH virgin</font>")
            return
        else:
            self.virginize_button.setEnabled(True)
            self.status_check.setText("<font color='red'>UCH coded</font>")
            return

    def start_diag_session_aftersales(self):
        sds_request = self.megane_uch.requests[u"Start Diagnostic Session"]
        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print "SdSS stream", sds_stream
            return
        options.elm.start_session_can(sds_stream)

    def reset_ecu(self):
        reset_request = self.megane_uch.requests[u"SR_RESERVED VSC 1"]
        reset_stream = " ".join(reset_request.build_data_stream({}))
        self.start_diag_session_aftersales()
        if options.simulation_mode:
            print "Reset stream", reset_stream
            return
        # Reset can only be done in study diag session
        options.elm.request(reset_stream)


def plugin_entry():
    v = Virginizer()
    v.exec_()
