# -*- coding: utf-8 -*-

# Plugin to program keys on Megane II
# (c) 2017
# This is an example plugin


import PyQt5.QtCore as core
import PyQt5.QtWidgets as gui

import ecu
import options

_ = options.translator('ddt4all')

plugin_name = _("Megane/Scenic II card programming")
category = _("Keys")
need_hw = True
ecufile = "UCH_84_J84_03_60"

a8_mess = [19, 29, 39, 4, 24, 46, 31, 12,
           16, 28, 7, 10, 15, 0, 40, 26,
           18, 20, 3, 8, 34, 8, 47, 21,
           2, 25, 38, 6, 4, 22, 14, 33,
           17, 1, 44, 11, 32, 41, 36, 42,
           5, 45, 5, 43, 30, 37, 13, 27]

a8_xor = [0x10, 0x20, 0x20, 0x10, 0x81, 0x88]
a8_xor_2 = [0x10, 0x20, 0x28, 0x10, 0x81, 0x88]


def a8(isk_c):
    '''MC9S12DG256 (Megane 2, Scenic 2)'''
    apv = ''
    isk = isk_c.replace(' ', '').decode('hex')
    if len(isk) != 6:
        return None
    bit_i = ''
    for c in isk:
        bit_i += bin(ord(c))[2:].zfill(8)

    # if not (bit_i[ 4]!=bit_i[23] and bit_i[12]==bit_i[43] and
    #        bit_i[ 4]==bit_i[35] and bit_i[ 8]==bit_i[ 9] and bit_i[ 4]==bit_i[ 5]):
    #  return 'Invalid ISK'

    base = ''
    for b in a8_xor:
        base = base + bin(b)[2:].zfill(8)

    i = 0
    for b in base:
        z = bit_i[a8_mess[i]]
        if b != z:
            z = '1'
        else:
            z = '0'
        base = base[:i] + z + base[i + 1:]
        i += 1

    for i in range(0, 6):
        apv += hex(int(base[i * 8:i * 8 + 8], 2))[2:].zfill(2).upper() + ' '

    return apv


def a8_2(isk_c):
    '''MC9S12DG256 (algo2)(Megane 2, Scenic 2)'''
    apv = ''
    isk = isk_c.replace(' ', '').decode('hex')
    if len(isk) != 6:
        return None
    bit_i = ''
    for c in isk:
        bit_i += bin(ord(c))[2:].zfill(8)

    base = ''
    for b in a8_xor_2:
        base = base + bin(b)[2:].zfill(8)

    i = 0
    for b in base:
        z = bit_i[a8_mess[i]]
        if b != z:
            z = '1'
        else:
            z = '0'
        base = base[:i] + z + base[i + 1:]
        i += 1

    for i in range(0, 6):
        apv += hex(int(base[i * 8:i * 8 + 8], 2))[2:].zfill(2).upper() + ' '

    return apv


def get_isk(ecu_response):
    ecu_response = ecu_response.replace(' ', '').strip()
    return ecu_response[19 * 2:25 * 2]


class CardProg(gui.QDialog):
    def __init__(self):
        super(CardProg, self).__init__()
        options.debug = True
        self.apvok = False
        self.megane_ecu = ecu.Ecu_file(ecufile, True)
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

        self.apv_access_button = gui.QPushButton(_("ENTER AFTER SALE MODE"))
        self.apv_access_button.clicked.connect(self.set_apv_from_input)
        self.pininput = gui.QLineEdit()
        self.pininput.setText("0" * 12)
        self.pininput.setInputMask("H" * 12)
        self.iskoutput = gui.QLineEdit()
        self.iskoutput.setInputMask("H" * 12)
        self.numkeys_label = gui.QLabel("0")
        self.currentcardide = gui.QLineEdit()
        self.currentcardide.setReadOnly(True)
        self.apv_status = gui.QLabel("")
        self.apv_status.setAlignment(core.Qt.AlignHCenter)
        label = gui.QLabel(_("<font color='red'>MEGANE II CARD PROGRAMMING<br>EXPERIMENTAL : NOT TESTED YET</font>"))
        label.setAlignment(core.Qt.AlignHCenter)
        self.learnbutton = gui.QPushButton(_("LEARN"))
        self.validatebutton = gui.QPushButton(_("VALIDATE"))
        self.cancelbutton = gui.QPushButton(_("CANCEL"))

        self.algocheck = gui.QCheckBox(_("Algo 2"))
        self.algocheck.setChecked(False)

        self.learnbutton.clicked.connect(self.learn_action)
        self.validatebutton.clicked.connect(self.validate_action)
        self.cancelbutton.clicked.connect(self.cancel_action)
        self.iskoutput.textChanged.connect(self.calculate_pin)
        self.algocheck.toggled.connect(self.calculate_pin)

        layout = gui.QGridLayout()
        layout.addWidget(label, 0, 0, 1, 0)
        layout.addWidget(gui.QLabel(_("ISK")), 1, 0)
        layout.addWidget(self.iskoutput, 1, 1)
        layout.addWidget(gui.QLabel(_("PIN")), 2, 0)
        layout.addWidget(self.pininput, 2, 1)
        layout.addWidget(self.algocheck, 3, 1)
        layout.addWidget(self.apv_access_button, 4, 0, 1, 0)
        layout.addWidget(self.apv_status, 5, 0, 1, 0)
        layout.addWidget(gui.QLabel(_("Num key learnt")), 6, 0)
        layout.addWidget(self.numkeys_label, 6, 1)
        layout.addWidget(gui.QLabel(_("CARD IDE")), 7, 0)
        layout.addWidget(self.currentcardide, 7, 1)
        layout.addWidget(self.learnbutton, 8, 0, 1, 0)
        layout.addWidget(self.validatebutton, 9, 0)
        layout.addWidget(self.cancelbutton, 9, 1)

        self.setLayout(layout)

        # I have to use a timer here to avoid ECU from escaping session mode
        # A shot every 1.5 seconds is enough, normally
        self.tester_timer = core.QTimer()
        self.tester_timer.setSingleShot(False)
        self.tester_timer.setInterval(1500)
        self.tester_timer.timeout.connect(self.check_all)

        isk = self.get_isk()
        self.iskoutput.setText(isk)

        self.tester_timer.start()

    def calculate_pin(self):
        ISK = ''.join(str(ord(c)) for c in str(self.iskoutput.text()))
        if len(ISK) == 12:
            if self.algocheck.checkState():
                PIN = a8_2(ISK)
            else:
                PIN = a8(ISK)
            if PIN is not None:
                self.pininput.setText(PIN)
                self.iskoutput.setStyleSheet("color: green;")
                return

        self.pininput.setText("000000000000")
        self.iskoutput.setStyleSheet("color: red;")

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

        if reply.startswith('7F') or reply.startswith('WRONG'):
            options.main_window.logview.append(_("Cannot get ISK, check connections and UCH compatibility"))
            return

        isk = reply.replace(' ', '').strip()
        return get_isk(isk)

    def ecu_connect(self):
        connection = self.megane_ecu.connect_to_hardware()
        if not connection:
            options.main_window.logview.append(_("Cannot connect to ECU"))
            self.finished()

    def check_all(self):
        self.check_apv_status()
        self.check_num_key_learnt()

    def set_apv_from_input(self):
        apv = ''.join(str(ord(c)) for c in str(self.pininput.text()))
        if len(apv) != 12:
            return
        self.after_sale_request.send_request({u'Code APV': apv})

    def enable_buttons(self, enable):
        self.learnbutton.setEnabled(enable)
        self.validatebutton.setEnabled(enable)
        self.cancelbutton.setEnabled(enable)

    def check_apv_status(self):
        key_bits_status_values = self.key_bits_status.send_request({}, "61 06 21 21 20 00 00 00 08 00 00 80 03")

        value_apv_ok = key_bits_status_values[u'VSC Code APV_Reconnu']
        value_apv_reaff = key_bits_status_values[u'VSC ModeAPV_ReaffArmé']
        value_apv_uch_reaff = key_bits_status_values[u'VSC ModeAPV_AppUCH_Armé']

        if value_apv_ok == '0':
            self.apv_status.setText(_("<font color='red'>PIN CODE NOT RECOGNIZED</font>"))
            self.apvok = False
            self.enable_buttons(False)
            return

        if value_apv_reaff == '1':
            self.apv_status.setText(_("<font color='green'>PIN CODE OK / KEY LEARNING</font>"))
            self.enable_buttons(True)
            self.apvok = True
            return

        elif value_apv_uch_reaff == '1':
            self.apv_status.setText(_("<font color='green'>PIN CODE OK / UCH LEARNING</font>"))
            self.enable_buttons(True)
            self.apvok = True
            return

        self.apvok = False
        self.enable_buttons(False)

        self.apv_status.setText("<font color='red'>UCH NOT READY</font>")

    def check_num_key_learnt(self):
        key_bytes_status_value = self.key_bytes_status.send_request({}, "61 08 00 00 00 00 00 00 0A 00 00 00 00 00 00 "
                                                                        "00 00 00 00 00 00 00 00 00 00 02 00 00 01 2C "
                                                                        "00 00 01 2C 00 00 2C 00 00 01 2C")

        num_key_learnt = key_bytes_status_value[u'VSC NbTotalDeBadgeAppris']
        current_key_ide = key_bytes_status_value[u'VSC Code_IDE']

        self.numkeys_label.setText(num_key_learnt)
        self.currentcardide.setText(current_key_ide)

    def start_diag_session(self):
        sds_request = self.megane_ecu.requests[u"Start Diagnostic Session"]
        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print("SdS stream", sds_stream)
            return
        options.elm.start_session_can(sds_stream)


def plugin_entry():
    cp = CardProg()
    cp.exec_()
