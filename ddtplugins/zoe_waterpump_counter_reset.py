# -*- coding: utf-8 -*-

# (c) 2025
# Zoé EVC water pump counter reset values (low, medium, high speed + timer)
# cf error code: SYST ELEC A CONTROLLER

import PyQt5.QtCore as core
import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as gui
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
import ecu
import options

_ = options.translator('ddt4all')

plugin_name = _("Zoe water pump Reset")
category = _("EVC Tools")
need_hw = True
ecufile = "EVC_3180_RH5_510_V1.1_20210422T184714"

class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.evc_ecu = ecu.Ecu_file(ecufile, True)
        self.setWindowTitle(_("Water pump counters"))
        # Set window icon
        appIcon = qtgui.QIcon("ddt4all_data/icons/obd.png")
        self.setWindowIcon(appIcon)
        layout = gui.QVBoxLayout()
        # Création du tableau
        self.table = QTableWidget()
        self.table.setRowCount(4)  # Number of lines
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([_("Name"), _("Values"), _("Action")])  # columns headers
        self.table.setColumnWidth(0, 200)

        # Add data to table
        data = [
            [_("Low Speed"), "", ""],
            [_("Middle Speed"), "", ""],
            [_("High Speed"), "", ""],
            [_("V_Timer_DrivWEP_ON"), "", ""], #V_Timer_DrivWEP_ON
        ]

        for row, (nom, valeur, action) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(nom))
            self.table.setItem(row, 1, QTableWidgetItem(valeur))
            self.table.setItem(row, 2, QTableWidgetItem(action))

        resetLabel = _("Reset")
        resetlowBtn = gui.QPushButton(resetLabel)
        self.table.setCellWidget(0, 2, resetlowBtn)
        resetlowBtn.clicked.connect(self.reset_lowcounter)

        resetmiddleBtn = gui.QPushButton(resetLabel)
        self.table.setCellWidget(1, 2, resetmiddleBtn)
        resetmiddleBtn.clicked.connect(self.reset_middlecounter)

        resethighBtn = gui.QPushButton(resetLabel)
        self.table.setCellWidget(2, 2, resethighBtn)
        resethighBtn.clicked.connect(self.reset_highcounter)

        resetdrivewepBtn = gui.QPushButton(resetLabel)
        self.table.setCellWidget(3, 2, resetdrivewepBtn)
        resetdrivewepBtn.clicked.connect(self.reset_DrivWEP)

        # Add table to layout
        layout.addWidget(self.table)

        infos = gui.QLabel(_("Zoe water pump counters<br>"
                             "<font color='red'>THIS PLUGIN WILL ERASE WATER PUMP COUNTERS<br>GO AWAY IF YOU HAVE NO IDEA OF WHAT IT MEANS</font>"))

        infos.setAlignment(core.Qt.AlignHCenter)
        check_button = gui.QPushButton(_("Check values"))
        self.status_check = gui.QLabel(_("Waiting action"))
        self.status_check.setAlignment(core.Qt.AlignHCenter)
        self.virginize_button = gui.QPushButton(_("Reset all counters"))
        layout.addWidget(infos)
        layout.addWidget(check_button)
        layout.addWidget(self.status_check)
        layout.addWidget(self.virginize_button)

        # Tips list as HTML
        instructions_html = _("<h1>TIPS</h1><ul><li>Insert key CARD</li><li>Put D position</li><li>Press/Stay START until <b>Remove card</b> message</li><li>Put P position</li><li>Keep key card inserted</li></ul>")

        label = QLabel(instructions_html)
        layout.addWidget(label)

        self.setLayout(layout)
        self.virginize_button.setEnabled(True)
        self.virginize_button.clicked.connect(self.reset_ecu)
        check_button.clicked.connect(self.get_counters_values)
        self.ecu_connect()

    def ecu_connect(self):
        connection = self.evc_ecu.connect_to_hardware()
        if not connection:
            options.main_window.logview.append(_("Cannot connect to ECU"))
            self.finished()

    def get_counters_values(self):
        self.start_diag_session()
        self.get_low_speed_counter()
        self.get_medium_speed_counter()
        self.get_high_speed_counter()
        self.get_timer_DrivWEP_ON()
        self.status_check.setText(_("<font color='green'>Values read</font>"))


    def get_timer_DrivWEP_ON(self):
        key_name = "($3531) V_Timer_DrivWEP_ON"
        pumptimer_check_request = self.evc_ecu.requests[
            u'DataRead.($3531) V_Timer_DrivWEP_ON']

        options.main_window.logview.append("reading V_Timer_DrivWEP_ON")
        pumptimer_check_values = pumptimer_check_request.send_request()
        if pumptimer_check_values:
            value = pumptimer_check_values.get(key_name)
        else:
            value = "Not found"
        self.table.setItem(3, 1, QTableWidgetItem(value))

    def get_low_speed_counter(self):
        key_name = "($3349) Time Counter for the driving WEP in Low Speed"
        lowspeed_check_request = self.evc_ecu.requests[
            u'DataRead.($3349) Time Counter for the driving WEP in Low Speed']
        options.main_window.logview.append(_("Reading Low speed"))
        lowspeed_check_values = lowspeed_check_request.send_request()
        print(lowspeed_check_values)
        value = lowspeed_check_values.get(key_name)
        value = str(value)

        options.main_window.logview.append(value)
        self.table.setItem(0, 1, QTableWidgetItem(value))

    def get_medium_speed_counter(self):
        key_name = "($334A) Time Counter for the driving WEP in Middle Speed"
        middlespeed_check_request = self.evc_ecu.requests[
            u'DataRead.($334A) Time Counter for the driving WEP in Middle Speed']

        options.main_window.logview.append(_("Reading Middle speed"))

        middlespeed_check_values = middlespeed_check_request.send_request()
        print(middlespeed_check_values)
        value = middlespeed_check_values.get(key_name)
        value = str(value)

        options.main_window.logview.append(value)
        self.table.setItem(1, 1, QTableWidgetItem(value))

    def get_high_speed_counter(self):
        key_name = "($334B) Time Counter for the driving WEP in High Speed"
        highspeed_check_request = self.evc_ecu.requests[
            u'DataRead.($334B) Time Counter for the driving WEP in High Speed']

        options.main_window.logview.append(_("Reading High speed"))

        highspeed_check_values = highspeed_check_request.send_request()
        print(highspeed_check_values)
        value = highspeed_check_values.get(key_name)
        value = str(value)

        options.main_window.logview.append(value)
        self.table.setItem(2, 1, QTableWidgetItem(value))

    def start_diag_extend_session(self):
        sds_request = self.evc_ecu.requests[u"StartDiagnosticSession.ExtendedDiagnosticSession"]

        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print("SdS stream", sds_stream)
            return
        options.elm.start_session_can(sds_stream)

    def start_diag_session(self):
        sds_request = self.evc_ecu.requests[u"StartDiagnosticSession.Default"]

        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print("SdS stream", sds_stream)
            return
        options.elm.start_session_can(sds_stream)

    def reset_lowcounter(self):
        self.start_diag_extend_session()
        self.reset_low_speed_counter()

    def reset_middlecounter(self):
        self.start_diag_extend_session()
        self.reset_middle_speed_counter()

    def reset_highcounter(self):
        self.start_diag_extend_session()
        self.reset_high_speed_counter()

    def reset_DrivWEP(self):
        self.start_diag_extend_session()
        self.reset_timer_DrivWEP()

    def reset_ecu(self):
        self.start_diag_session()
        self.reset_low_speed_counter()
        self.reset_middlecounter()
        self.reset_high_speed_counter()
        self.reset_timer_DrivWEP()

    def reset_timer_DrivWEP(self):
        reset_request = self.evc_ecu.requests[u"DataWrite.($3531) V_Timer_DrivWEP_ON"]
        request_response = reset_request.send_request({"($3531) V_Timer_DrivWEP_ON": "0"})
        print(request_response)
        if request_response is not None:
            self.status_check.setText(_("<font color='green'>CLEAR V_Timer_DrivWEP_ON EXECUTED</font>"))
        else:
            self.status_check.setText(_("<font color='red'>CLEAR V_Timer_DrivWEP_ON FAILED</font>"))
        # self.get_timer_DrivWEP_ON()

    def reset_low_speed_counter(self):
        reset_request = self.evc_ecu.requests[u"DataWrite.($3349) Time Counter for the driving WEP in Low Speed"]
        request_response = reset_request.send_request({"($3349) Time Counter for the driving WEP in Low Speed": 0})
        print(request_response)
        if request_response is not None:
            self.status_check.setText(_("<font color='green'>CLEAR Low EXECUTED</font>"))
        else:
            self.status_check.setText(_("<font color='red'>CLEAR Low FAILED</font>"))
        # self.get_low_speed_counter()

    def reset_middle_speed_counter(self):
        reset_request = self.evc_ecu.requests[u"DataWrite.($334A) Time Counter for the driving WEP in Middle Speed"]
        request_response = reset_request.send_request({"($334A) Time Counter for the driving WEP in Middle Speed": 0})
        print(request_response)
        if request_response is not None:
            self.status_check.setText(_("<font color='green'>CLEAR Medium EXECUTED</font>"))
        else:
            self.status_check.setText(_("<font color='red'>CLEAR Medium FAILED</font>"))
        # self.get_medium_speed_counter()

    def reset_high_speed_counter(self):
        reset_request = self.evc_ecu.requests[u"DataWrite.($334B) Time Counter for the driving WEP in High Speed"]
        request_response = reset_request.send_request({"($334B) Time Counter for the driving WEP in High Speed": 0})
        print(request_response)
        if request_response is not None:
            self.status_check.setText(_("<font color='green'>CLEAR HIGH EXECUTED</font>"))
        else:
            self.status_check.setText(_("<font color='red'>CLEAR HIGH FAILED</font>"))
        # self.get_high_speed_counter()

def plugin_entry():
    v = Virginizer()
    v.exec_()