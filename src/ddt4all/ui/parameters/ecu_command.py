import PyQt5.QtCore as core
import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

import ddt4all.options as options
import ddt4all.version as version

_ = options.translator('ddt4all')

class EcuCommand(widgets.QDialog):
    def __init__(self, paramview, ecurequestparser, sds):
        super(EcuCommand, self).__init__(None)
        # Set window icon and title
        appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
        self.setWindowIcon(appIcon)
        self.setWindowTitle(_("ECU Command"))
        self.ecu = ecurequestparser
        self.ecu.requests.keys()
        self.sds = sds
        self.paramview = paramview

        layout = widgets.QVBoxLayout()
        self.req_combo = widgets.QComboBox()
        self.sds_combo = widgets.QComboBox()
        self.com_table = widgets.QTableWidget()
        self.rcv_table = widgets.QTableWidget()
        self.isotp_frame_edit = widgets.QLineEdit()
        self.com_table.setColumnCount(2)
        self.com_table.verticalHeader().hide()

        self.rcv_table.setColumnCount(2)
        self.rcv_table.verticalHeader().hide()
        layout.addWidget(widgets.QLabel("Start diagnostic session"))
        layout.addWidget(self.sds_combo)
        layout.addWidget(widgets.QLabel("Request"))
        layout.addWidget(self.req_combo)
        layout.addWidget(widgets.QLabel("Data to send"))
        layout.addWidget(self.com_table)
        layout.addWidget(widgets.QLabel("Computed ISOTP Frame"))
        layout.addWidget(self.isotp_frame_edit)
        checkbutton = widgets.QPushButton("Compute frame")
        layout.addWidget(checkbutton)
        layout.addWidget(widgets.QLabel("Data received"))
        layout.addWidget(self.rcv_table)
        button = widgets.QPushButton("Execute")
        layout.addWidget(button)
        button.clicked.connect(self.execute)
        self.setLayout(layout)
        self.reqs = []
        self.send_data = []
        self.current_request = None
        checkbutton.clicked.connect(self.recompute)

        reqlist = [a for a in self.ecu.requests.keys()]
        reqlist.sort()
        for k in reqlist:
            self.req_combo.addItem(k)
            self.reqs.append(k)
        self.req_combo.currentIndexChanged.connect(self.req_changed)

        for k, v in self.sds.items():
            self.sds_combo.addItem(k)

        text = "<center>This feature is experimental</center>\n"
        text += "<center>Use it at your own risk</center>\n"
        text += "<center>and if you know exactely what you do</center>\n"
        msgbox = widgets.QMessageBox()
        appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
        msgbox.setWindowIcon(appIcon)
        msgbox.setWindowTitle(version.__appname__)
        msgbox.setText(text)
        msgbox.exec_()

    def recompute(self):
        frame = self.compute_frame(False)
        self.isotp_frame_edit.setText(frame)

    def compute_frame(self, check=True):
        data_to_stream = {}
        for i in range(0, self.com_table.rowCount()):
            cellwidget = self.com_table.cellWidget(i, 1)
            reqkey = self.com_table.item(i, 0).text()
            if cellwidget:
                curtext = cellwidget.currentText()
            elif self.com_table.item(i, 1) is not None:
                curtext = self.com_table.item(i, 1).text()
            else:
                if check:
                    msgbox = widgets.QMessageBox()
                    appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
                    msgbox.setWindowIcon(appIcon)
                    msgbox.setWindowTitle(version.__appname__)
                    msgbox.setText("Missing data in table")
                    msgbox.exec_()
                return "Missing input data"

            if curtext is None:
                # Error here
                data_to_stream[reqkey] = ""
            else:
                data_to_stream[reqkey] = curtext

        stream_to_send = " ".join(self.current_request.build_data_stream(data_to_stream))
        return stream_to_send

    def execute(self):
        if self.current_request is None:
            return

        sds = self.sds[self.sds_combo.currentText()]
        self.paramview.sendElm(sds)

        stream_to_send = self.compute_frame()
        reveived_stream = self.paramview.sendElm(stream_to_send, False, True)
        if reveived_stream.startswith("WRONG"):
            msgbox = widgets.QMessageBox()
            appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
            msgbox.setWindowIcon(appIcon)
            msgbox.setWindowTitle(version.__appname__)
            msgbox.setText("ECU returned error (check logview)")
            msgbox.exec_()
            return
        received_data = self.current_request.get_values_from_stream(reveived_stream)

        self.rcv_table.setRowCount(len(received_data))
        itemcount = 0
        for k, v in received_data.items():
            item = widgets.QTableWidgetItem(k)
            self.rcv_table.setItem(itemcount, 0, item)
            if v is not None:
                item = widgets.QTableWidgetItem(v)
            else:
                item = widgets.QTableWidgetItem("NONE")
            self.rcv_table.setItem(itemcount, 1, item)
            itemcount += 1

        self.rcv_table.resizeColumnsToContents()
        self.rcv_table.resizeRowsToContents()

    def req_changed(self, item):
        self.com_table.clear()
        self.com_table.setColumnCount(5)
        self.current_request = self.ecu.requests[self.reqs[item]]
        self.com_table.setRowCount(len(self.current_request.sendbyte_dataitems))
        self.send_data = []

        self.com_table.setHorizontalHeaderLabels(["Key", "Value", "Unit", "Data type", "Description"])
        self.rcv_table.setHorizontalHeaderLabels(["Key", "Value"])

        itemcount = 0
        for k, v in self.current_request.sendbyte_dataitems.items():
            self.send_data.append(k)
            ecudata = self.ecu.data[k]

            item = widgets.QTableWidgetItem(k)
            item.setFlags(item.flags() ^ core.Qt.ItemIsEditable)
            self.com_table.setItem(itemcount, 0, item)
            item = widgets.QTableWidgetItem(ecudata.unit)
            item.setFlags(item.flags() ^ core.Qt.ItemIsEditable)
            self.com_table.setItem(itemcount, 2, item)
            if ecudata.scaled:
                item = widgets.QTableWidgetItem("Numeric decimal")
            elif len(ecudata.items):
                item = widgets.QTableWidgetItem("List")
            elif ecudata.bytesascii:
                item = widgets.QTableWidgetItem("String")
            else:
                item = widgets.QTableWidgetItem("Hexadecimal")
            item.setFlags(item.flags() ^ core.Qt.ItemIsEditable)
            self.com_table.setItem(itemcount, 3, item)
            item = widgets.QTableWidgetItem(ecudata.description)
            item.setFlags(item.flags() ^ core.Qt.ItemIsEditable)
            self.com_table.setItem(itemcount, 4, item)

            if len(ecudata.items):
                items = ecudata.items.keys()
                combo = widgets.QComboBox()
                for item in items:
                    combo.addItem(item)
                self.com_table.setCellWidget(itemcount, 1, combo)
            itemcount += 1

        self.com_table.resizeColumnsToContents()
        self.com_table.resizeRowsToContents()
        self.rcv_table.setRowCount(0)
