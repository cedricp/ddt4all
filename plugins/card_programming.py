# -*- coding: utf-8 -*-

# Plugin to program keys on Megane II
# (c) 2017
# This is an example plugin


import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import ecu
import elm
import options

plugin_name = "Megane/Scenic II card programming"
category = "Keys"
need_hw = True


def get_isk(ecu_response):
    ecu_response = ecu_response.replace(' ', '').strip()
    return ecu_response[19 * 2:25 * 2]


class CardProg(gui.QDialog):
    def __init__(self):
        super(CardProg, self).__init__()
        options.debug = True
        self.megane_ecu = ecu.Ecu_file("UCH_84_J84_03_60", True)
        self.start_session_request = self.megane_ecu.requests[u'Start Diagnostic Session']
        self.after_sale_request = self.megane_ecu.requests[u'ACCEDER AU MODE APRES-VENTE']
        self.learn_key_request = self.megane_ecu.requests[u'APPRENDRE BADGE']
        self.key_bits_status = self.megane_ecu.requests[u'Status général des opérations badges Bits']
        self.key_bytes_status = self.megane_ecu.requests[u'Status général des opérations badges Octets']
        self.reserved_frame_request = self.megane_ecu.requests[u'Trame AB: Trame réservée']
        self.learn_validate_request = self.megane_ecu.requests[u'SORTIE DU MODE APV : VALIDATION']
        self.learn_cancel_request = self.megane_ecu.requests[u'SORTIE DU MODE APV : ABANDON']

        self.ecu_connect()
        self.start_diag_session()
        isk = self.get_isk()

        self.apv_access_button = gui.QPushButton("ENTER AFTER SALE MODE")
        self.apv_access_button.clicked.connect(self.set_apv_from_input)
        self.pininput = gui.QLineEdit()
        self.pininput.setText("0" * 12)
        self.pininput.setInputMask("H" * 12)
        self.iskoutput = gui.QLineEdit()
        self.iskoutput.setReadOnly(True)
        self.iskoutput.setText(isk)
        self.numkeys_label = gui.QLabel("0")
        self.currentcardide = gui.QLineEdit()
        self.currentcardide.setReadOnly(True)
        self.apv_status = gui.QLabel("")
        self.apv_status.setAlignment(core.Qt.AlignHCenter)
        label = gui.QLabel("<font color='red'>MEGANE II CARD PROGRAMMING<br>EXPERIMENTAL : NOT TESTED YET</font>")
        label.setAlignment(core.Qt.AlignHCenter)
        self.learnbutton = gui.QPushButton("LEARN")
        self.validatebutton = gui.QPushButton("VALIDATE")
        self.validatebutton = gui.QPushButton("VALIDATE")
        self.cancelbutton = gui.QPushButton("CANCEL")

        self.learnbutton.clicked.connect(self.learn_action)
        self.validatebutton.clicked.connect(self.validate_action)
        self.cancelbutton.clicked.connect(self.cancel_action)

        layout = gui.QGridLayout()
        layout.addWidget(label, 0, 0, 1, 0)
        layout.addWidget(gui.QLabel("ISK"), 1, 0)
        layout.addWidget(self.iskoutput, 1, 1)
        layout.addWidget(gui.QLabel("PIN"), 2, 0)
        layout.addWidget(self.pininput, 2, 1)
        layout.addWidget(self.apv_access_button, 3, 0, 1, 0)
        layout.addWidget(self.apv_status, 4, 0, 1, 0)
        layout.addWidget(gui.QLabel("Num key learnt"), 5, 0)
        layout.addWidget(self.numkeys_label, 5, 1)
        layout.addWidget(gui.QLabel("CARD IDE"), 6, 0)
        layout.addWidget(self.currentcardide, 6, 1)
        layout.addWidget(self.learnbutton, 7, 0, 1, 0)
        layout.addWidget(self.validatebutton, 8, 0)
        layout.addWidget(self.cancelbutton, 8, 1)

        self.setLayout(layout)

        # I have to use a timer here to avoid ECU from escaping session mode
        # A shot every 1.5 seconds is enough, normally
        self.tester_timer = core.QTimer()
        self.tester_timer.setSingleShot(False)
        self.tester_timer.setInterval(1500)
        self.tester_timer.timeout.connect(self.check_all)

        self.tester_timer.start()

    def learn_action(self):
        self.learn_key_request.send_request()

    def validate_action(self):
        self.learn_validate_request.send_request()

    def cancel_action(self):
        self.learn_cancel_request.send_request()

    def get_isk(self):
        # No dataitem for ISK :(
        # Need to decode by myself
        if options.simulation_mode:
            reply = "61 AB 02 FC 0D 08 51 4C 86 55 54 00 00 00 00 00 00 00 00 8D E8 EE 16 79 D3 C9 A7 A7 CC " \
                    "F6 AC 00 00 00 00 00 00 2A"
        else:
            reply = options.elm.request(self.reserved_frame_request.sentbytes)

        if reply.startswith('7F') or reply == 'WRONG RESPONSE':
            options.main_window.logview.append("Cannot get ISK, check connections and UCH compatibility")
            return

        isk = reply.replace(' ', '').strip()
        return get_isk(isk)

    def ecu_connect(self):
        connection = self.megane_ecu.connect_to_hardware()
        if not connection:
            options.main_window.logview.append("Cannot connect to UCH")
            self.close()

    def check_all(self):
        self.check_apv_status()
        self.check_num_key_learnt()

    def set_apv_from_input(self):
        apv = str(self.pininput.text().toAscii())
        if len(apv) != 12:
            return
        print apv
        self.after_sale_request.send_request({u'Code APV': apv})

    def check_apv_status(self):
        key_bits_status_values = self.key_bits_status.send_request({}, "62 01 64 00 00 00 00 00 00 00 00 00 00 00 00")

        value_apv_ok = key_bits_status_values[u'VSC Code APV_Reconnu']
        value_apv_reaff = key_bits_status_values[u'VSC ModeAPV_ReaffArmé']
        value_apv_uch_reaff = key_bits_status_values[u'VSC ModeAPV_AppUCH_Armé']

        if value_apv_ok == '0':
            self.apv_status.setText("<font color='red'>PIN CODE NOT RECOGNIZED</font>")
            self.learnbutton.setEnabled(False)
            self.validatebutton.setEnabled(False)
            self.cancelbutton.setEnabled(False)
            return
        else:
            self.learnbutton.setEnabled(True)
            self.validatebutton.setEnabled(True)
            self.cancelbutton.setEnabled(True)
            if value_apv_reaff == '1':
                self.apv_status.setText("<font color='green'>PIN CODE OK / KEY LEARNING</font>")
                return
            elif value_apv_uch_reaff == '1':
                self.apv_status.setText("<font color='green'>PIN CODE OK / UCH LEARNING</font>")
                return
            else:
                self.apv_status.setText("<font color='green'>PIN CODE OK</font>")
                return

        self.learnbutton.setEnabled(False)
        self.validatebutton.setEnabled(False)
        self.cancelbutton.setEnabled(False)
        self.apv_status.setText("<font color='red'>WEIRD UCH STATE</font>")

    def check_num_key_learnt(self):
        key_bytes_status_value = self.key_bytes_status.send_request({}, "61 08 00 00 00 00 00 00 00 00 00 00 00 00 00 "\
                                                                        "00 00 00 00 00 00 00 00 "\
                                                                        "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00")

        num_key_learnt = key_bytes_status_value[u'VSC NbTotalDeBadgeAppris']
        current_key_ide = key_bytes_status_value[u'VSC Code_IDE']

        self.numkeys_label.setText(num_key_learnt)
        self.currentcardide.setText(current_key_ide)

    def start_diag_session(self):
        sds_request = self.megane_ecu.requests[u"Start Diagnostic Session"]
        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print "SdS stream", sds_stream
            return
        options.elm.start_session_can(sds_stream)

def plugin_entry():
    cp = CardProg()
    cp.exec_()


