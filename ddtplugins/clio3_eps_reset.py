# -*- coding: utf-8 -*-

# (c) 2017

import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import ecu
import options
import crcmod
from binascii import unhexlify

_ = options.translator('ddt4all')

plugin_name = _("Modus/Clio III EPS Reset")
category = _("EPS Tools")
need_hw = True
ecufile = "DAE_J77_X85_Gen2___v3.7"

def calc_crc(vin=None):
    VIN=vin.encode("hex")
    VININT=unhexlify(VIN)

    crc16 = crcmod.predefined.Crc('x-25')
    crc16.update(VININT)
    crcle = crc16.hexdigest()
    # Seems that computed CRC is returned in little endian way
    # Convert it to big endian
    return crcle[2:4] + crcle[0:2]

class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.clio_eps = ecu.Ecu_file(ecufile, True)
        layout = gui.QVBoxLayout()
        infos = gui.QLabel(_("Modus/Clio III EPS VIRGINIZER<br><font color='red'>THIS PLUGIN WILL RESET EPS IMMO DATA<br>GO AWAY IF YOU HAVE NO IDEA OF WHAT IT MEANS</font>"))
        infos.setAlignment(core.Qt.AlignHCenter)
        check_button = gui.QPushButton(_("BLANK STATUS & VIN READ"))
        self.status_check = gui.QLabel(_("Waiting"))
        self.status_check.setAlignment(core.Qt.AlignHCenter)
        self.virginize_button = gui.QPushButton(_("Virginize EPS"))

        self.setLayout(layout)
        self.virginize_button.setEnabled(False)
        self.virginize_button.clicked.connect(self.reset_ecu)
        check_button.clicked.connect(self.check_virgin_status)
        status_vin = gui.QLabel(_("VIN - READ"))
        status_vin.setAlignment(core.Qt.AlignHCenter)
        self.vin_input = gui.QLineEdit()
        self.vin_input.setReadOnly(True)

        status_vinout = gui.QLabel(_("VIN - WRITE"))
        status_vinout.setAlignment(core.Qt.AlignHCenter)
        self.vin_output = gui.QLineEdit()

        write_vin_button = gui.QPushButton(_("Write VIN"))
        write_vin_button.clicked.connect(self.write_vin)

        layout.addWidget(infos)
        layout.addWidget(check_button)
        layout.addWidget(self.status_check)
        layout.addWidget(self.virginize_button)
        layout.addWidget(self.virginize_button)

        layout.addWidget(status_vin)
        layout.addWidget(self.vin_input)
        layout.addWidget(status_vinout)
        layout.addWidget(self.vin_output)
        layout.addWidget(write_vin_button)

        self.ecu_connect()

    def read_vin(self):
        vin_read_request = self.clio_eps.requests[u'RDBLI - VIN']
        vin_values = vin_read_request.send_request({}, "61 81 68 69 70 65 65 65 65 65 65 65 65 65 65 65 65 65 66 00 00")
        self.vin_input.setText(vin_values[u'VIN'])

    def write_vin(self):
        try:
            vin = str(self.vin_output.text().toAscii()).upper()
            self.vin_output.setText(vin)
        except:
            self.status_check.setText(_("<font color='red'>VIN - INVALID</font>"))
            return

        if len(vin) != 17:
            self.status_check.setText(_("<font color='res'>VIN - BAD LENGTH</font>"))
            return

        crc = calc_crc(vin).decode('hex')
        self.start_diag_session()
        vin_wrtie_request = self.clio_eps.requests[u'WDBLI - VIN']
        write_response = vin_wrtie_request.send_request({u'VIN': vin, u'CRC VIN': crc})
        if write_response is None:
            self.status_check.setText(_("<font color='orange'>VIN WRITE FAILED</font>"))
            return

        self.status_check.setText(_("<font color='green'>VIN WRITE OK</font>"))

    def ecu_connect(self):
        connection = self.clio_eps.connect_to_hardware()
        if not connection:
            options.main_window.logview.append(_("Cannot connect to ECU"))
            self.finished()

    def check_virgin_status(self):
        self.start_diag_session()
        self.read_vin()
        virigin_check_request = self.clio_eps.requests[u'RDBLI - System Frame']
        virgin_check_values = virigin_check_request.send_request({}, "62 01 64 00 00 00 00 00 00 00 00 00 00 00 00 "\
                                                                 "00 00 00 00 00 00 00 00 00")

        if virgin_check_values is not None:
            virgin_status = virgin_check_values[u"Dongle status"]

            if options.debug:
                print virgin_status

            if virgin_status == u'Système VIERGE - Aucun code mémorisé':
                self.virginize_button.setEnabled(False)
                self.status_check.setText(_("<font color='green'>EPS virgin</font>"))
                return
            else:
                self.virginize_button.setEnabled(True)
                self.status_check.setText(_("<font color='red'>EPS coded</font>"))
                return

        self.status_check.setText(_("<font color='orange'>UNEXPECTED RESPONSE</font>"))

    def start_diag_session_fb(self):
        sds_request = self.clio_eps.requests[u"SDS - Start Diagnostic $FB"]
        sds_stream = " ".join(sds_request.build_data_stream({}))

        if options.simulation_mode:
            print "SdSFB stream", sds_stream
            return

        options.elm.start_session_can(sds_stream)

    def start_diag_session(self):
        sds_request = self.clio_eps.requests[u"Start Diagnostic Session"]
        sds_stream = " ".join(sds_request.build_data_stream({}))

        if options.simulation_mode:
            print "SdSC0 stream", sds_stream
            return

        options.elm.start_session_can(sds_stream)

    def reset_ecu(self):
        self.start_diag_session_fb()
        reset_request = self.clio_eps.requests[u"WDBLI - Erase of Dongle_ID code"]
        request_response = reset_request.send_request()

        if request_response is not None:
            self.status_check.setText(_("<font color='green'>CLEAR EXECUTED</font>"))
        else:
            self.status_check.setText(_("<font color='red'>CLEAR FAILED</font>"))


def plugin_entry():
    v = Virginizer()
    v.exec_()
