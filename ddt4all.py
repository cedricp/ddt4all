#!/usr/bin/python

import sys
import os
import pickle
import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import parameters, ecu
import elm, options

class Ecu_list(gui.QDialog):
    def __init__(self, ecuscan):
        super(Ecu_list, self).__init__()
        self.selected = ''
        layout = gui.QVBoxLayout()
        self.setLayout(layout)
        self.list = gui.QListWidget(self)
        self.list.setSelectionMode(gui.QAbstractItemView.SingleSelection)
        layout.addWidget(self.list)
        self.ecuscan = ecuscan

        stored_ecus = []
        for ecu in self.ecuscan.ecu_database.targets:
            if not ecu.name in stored_ecus:
                self.list.addItem(ecu.name)
                stored_ecus.append(ecu.name)
            
        self.list.doubleClicked.connect(self.ecuSel)

    def ecuSel(self, index):
        item = self.list.model().itemData(index)
        self.selected = unicode(item[0].toPyObject().toUtf8(), encoding="UTF-8")
        target = self.ecuscan.ecu_database.getTarget(self.selected)
        if target:
            self.ecuscan.addTarget(target)
        self.close()


class Main_widget(gui.QMainWindow):
    def __init__(self, parent = None):
        super(Main_widget, self).__init__(parent)
        self.setWindowTitle("DDT4all")
        print "Scanning ECUs..."
        self.ecu_scan = ecu.Ecu_scanner()
        print "Done, %i loaded ECUs in database." % self.ecu_scan.getNumEcuDb()

        self.paramview = None

        self.statusBar = gui.QStatusBar()
        self.setStatusBar(self.statusBar)

        self.connectedstatus = gui.QLabel()
        self.connectedstatus.setAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)
        self.protocolstatus = gui.QLabel()
        self.progressstatus = gui.QProgressBar()
        self.infostatus = gui.QLabel()

        self.connectedstatus.setFixedWidth(100)
        self.protocolstatus.setFixedWidth(200)
        self.progressstatus.setFixedWidth(150)
        self.infostatus.setFixedWidth(200)

        self.setConnected(True)

        self.refreshtimebox = gui.QSpinBox()
        self.refreshtimebox.setRange(100, 2000)
        self.refreshtimebox.setSingleStep(100)
        self.refreshtimebox.valueChanged.connect(self.changeRefreshTime)
        refrestimelabel = gui.QLabel("Rafraichissement:")

        self.statusBar.addWidget(self.connectedstatus)
        self.statusBar.addWidget(self.protocolstatus)
        self.statusBar.addWidget(self.progressstatus)
        self.statusBar.addWidget(refrestimelabel)
        self.statusBar.addWidget(self.refreshtimebox)
        self.statusBar.addWidget(self.infostatus)

        self.scrollview = gui.QScrollArea()
        self.scrollview.setWidgetResizable(False)
        self.setCentralWidget(self.scrollview)

        self.treedock_params = gui.QDockWidget(self)
        self.treeview_params = gui.QTreeWidget(self.treedock_params)
        self.treedock_params.setWidget(self.treeview_params)
        self.treeview_params.setHeaderLabels(["Screens"])
        self.treeview_params.doubleClicked.connect(self.changeScreen)

        self.treedock_logs = gui.QDockWidget(self)
        self.logview = gui.QTextEdit()
        self.logview.setReadOnly(True)
        self.treedock_logs.setWidget(self.logview)

        self.treedock_ecu = gui.QDockWidget(self)
        self.treeview_ecu = gui.QListWidget(self.treedock_ecu)
        self.treedock_ecu.setWidget(self.treeview_ecu)
        self.treeview_ecu.doubleClicked.connect(self.changeECU)

        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treedock_ecu)
        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treedock_params)
        self.addDockWidget(core.Qt.BottomDockWidgetArea, self.treedock_logs)

        self.toolbar = self.addToolBar("File")

        scanaction = gui.QAction(gui.QIcon("icons/scan.png"), "Scanner les ECUs", self)
        scanaction.triggered.connect(self.scan)

        diagaction = gui.QAction(gui.QIcon("icons/dtc.png"), "Lire les Codes defauts", self)
        diagaction.triggered.connect(self.readDtc)

        self.log = gui.QAction(gui.QIcon("icons/log.png"), "Full log", self)
        self.log.setCheckable(True)
        self.log.setChecked(options.log_all)
        self.log.triggered.connect(self.changeLogMode)

        self.expert = gui.QAction(gui.QIcon("icons/expert.png"), "Mode Expert", self)
        self.expert.setCheckable(True)
        self.expert.setChecked(options.promode)
        self.expert.triggered.connect(self.changeUserMode)

        self.autorefresh = gui.QAction(gui.QIcon("icons/autorefresh.png"), "Rafraichissement automatique", self)
        self.autorefresh.setCheckable(True)
        self.autorefresh.setChecked(options.auto_refresh)
        self.autorefresh.triggered.connect(self.changeAutorefresh)

        self.refresh = gui.QAction(gui.QIcon("icons/refresh.png"), "Rafraichir page", self)
        self.refresh.triggered.connect(self.refreshParams)
        self.refresh.setEnabled(not options.auto_refresh)

        self.toolbar.addAction(scanaction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.log)
        self.toolbar.addAction(self.expert)
        self.toolbar.addAction(self.autorefresh)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.refresh)
        self.toolbar.addSeparator()
        self.toolbar.addAction(diagaction)

        vehicle_dir = "vehicles"
        if not os.path.exists(vehicle_dir):
            os.mkdir(vehicle_dir)

        ecu_files = []
        for filename in os.listdir(vehicle_dir):
            basename, ext = os.path.splitext(filename)
            if ext == '.ecu':
                ecu_files.append(basename)

        menu = self.menuBar()

        diagmenu = menu.addMenu("Fichier")
        savevehicleaction = diagmenu.addAction("Sauvegarder ce vehicule")
        savevehicleaction.triggered.connect(self.saveEcus)
        diagmenu.addSeparator()

        for ecuf in ecu_files:
            ecuaction = diagmenu.addAction(ecuf)
            ecuaction.triggered.connect(lambda state, a=ecuf: self.loadEcu(a))

        ecumenu = menu.addMenu("Ecu")
        selectecu = ecumenu.addAction("Selectionner ECU")
        selectecu.triggered.connect(self.addEcu)

        iskmenu = menu.addMenu("ISK")
        meg2isk = iskmenu.addAction("Megane II")
        meg2isk.triggered.connect(lambda: self.getISK('megane2'))

    def changeRefreshTime(self):
        if self.paramview:
            self.paramview.setRefreshTime(self.refreshtimebox.value())

    def getISK(self, vehicle):
        if options.simulation_mode:
            self.logview.append("Lecture ISK possible uniquement en mode connecte")
            return

        if self.paramview:
            self.paramview.init(None)

        if vehicle == "megane2":
            ecu_conf = {'idTx': '', 'idRx': '', 'ecuname': 'UCH'}
            options.elm.init_can()
            options.elm.set_can_addr('26', ecu_conf)
            # Entering service session
            resp = options.elm.start_session_can('1086')
            if not resp.startswith("50"):
                self.logview.append("Connection a l'UCH pour recuperation ISK impossible")
                return
            # Asking to dump parameters
            isk_data_request =  options.elm.request(req='21AB', positive='61', cache=False)
            if not resp.startswith("61"):
                self.logview.append("Reponse UCH pour recuperation ISK invalide")
                return
            # Return to default session
            options.elm.request(req='1081', positive='50', cache=False)
            isk_data_split = isk_data_request.split(" ")
            isk_bytes = " ".join(isk_data_split[19:25])
            self.logview.append('Votre code ISK : <font color=red>' + isk_bytes + '</font>')
            if self.paramview:
                self.paramview.initELM()

    def addEcu(self):
        eculist = Ecu_list(self.ecu_scan)
        eculist.exec_()
        if eculist.selected:
            self.treeview_ecu.addItem(eculist.selected)

    def scan(self):
        progressWidget = gui.QWidget(None)
        progressLayout = gui.QVBoxLayout()
        progressWidget.setLayout(progressLayout)
        self.progressstatus.setRange(0, self.ecu_scan.getNumAddr())
        self.progressstatus.setValue(0)

        self.ecu_scan.clear()
        self.ecu_scan.scan(self.progressstatus, self.infostatus)
        self.ecu_scan.scan_kwp(self.progressstatus, self.infostatus)

        self.treeview_ecu.clear()
        self.treeview_params.clear()
        if self.paramview:
            self.paramview.init(None)

        for ecu in self.ecu_scan.ecus.keys():
            item = gui.QListWidgetItem(ecu)
            self.treeview_ecu.addItem(item)

        self.progressstatus.setValue(0)

    def setConnected(self, on):
        if on:
            self.connectedstatus.setStyleSheet("background : green")
            self.connectedstatus.setText("CONNECTE")
        else:
            self.connectedstatus.setStyleSheet("background : red")
            self.connectedstatus.setText("DECONNECTE")

    def saveEcus(self):
        filename = gui.QFileDialog.getSaveFileName(self, "Sauvegarde vehicule (gardez l'extention .ecu)", "./vehicles/mycar.ecu", ".ecu")
        pickle.dump(self.ecu_scan.ecus, open(filename, "wb"))

    def loadEcu(self, name):
        vehicle_file = "vehicles/" + name + ".ecu"
        self.ecu_scan.ecus = pickle.load(open(vehicle_file, "rb"))

        self.treeview_ecu.clear()
        self.treeview_params.clear()
        if self.paramview:
            self.paramview.init(None)

        for ecu in self.ecu_scan.ecus.keys():
            item = gui.QListWidgetItem(ecu)
            self.treeview_ecu.addItem(item)

    def readDtc(self):
        if self.paramview:
            self.paramview.readDTC()

    def changeAutorefresh(self):
        options.auto_refresh = self.autorefresh.isChecked()
        self.refresh.setEnabled(not options.auto_refresh)

        if options.auto_refresh:
            if self.paramview:
                self.paramview.updateDisplays(True)

    def refreshParams(self):
        if self.paramview:
            self.paramview.updateDisplays(True)

    def changeUserMode(self):
        options.promode = self.expert.isChecked()

    def changeLogMode(self):
        options.log_all = self.log.isChecked()

    def readDTC(self):
        if self.paramview:
            self.paramview.readDTC()
        
    def changeScreen(self, index):
        item = self.treeview_params.model().itemData(index)
        screen = unicode(item[0].toPyObject().toUtf8(), encoding="UTF-8")
        self.paramview.init(screen)
        self.paramview.setRefreshTime(self.refreshtimebox.value())

    def changeECU(self, index):
        item = self.treeview_ecu.model().itemData(index)
        ecu_name = unicode(item[0].toString().toUtf8(), encoding="UTF-8")
        self.treeview_params.clear()

        ecu = self.ecu_scan.ecus[ecu_name]
        ecu_file = "ecus/" + ecu.href
        ecu_addr = ecu.addr
        self.paramview = parameters.paramWidget(self.scrollview, ecu_file, ecu_addr, ecu_name, self.logview)
        self.scrollview.setWidget(self.paramview)

        self.protocolstatus.setText(ecu.protocol)

        screens = self.paramview.categories.keys()
        for screen in screens:
            item = gui.QTreeWidgetItem(self.treeview_params, [screen])
            for param in self.paramview.categories[screen]:
                param_item = gui.QTreeWidgetItem(item, [param])
                param_item.setData(0, core.Qt.UserRole, param)


class donationWidget(gui.QLabel):
    def __init__(self):
        super(donationWidget, self).__init__()
        img = gui.QPixmap("icons/donate.png")
        self.setPixmap(img)
        self.setAlignment(core.Qt.AlignCenter)

    def mousePressEvent(self, mousevent):
        msgbox = gui.QMessageBox()
        msgbox.setText("<center>Ce logiciel est entierement gratuit et peut etre utilise librement. Faire un don me permettra de pouvoir acquerir du materiel afin de faire evoluer cette application. Merci pour votre aide</center>")
        okbutton = gui.QPushButton('Je fais un don')
        msgbox.addButton(okbutton, gui.QMessageBox.YesRole)
        msgbox.addButton(gui.QPushButton('Non merci'), gui.QMessageBox.NoRole)
        okbutton.clicked.connect(self.donate)
        msgbox.exec_()

    def donate(self):
        url = core.QUrl("https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=cedricpaille@gmail.com&lc=CY&item_name=codetronic&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG.if:NonHosted", core.QUrl.TolerantMode)
        gui.QDesktopServices().openUrl(url)
        msgbox = gui.QMessageBox()
        msgbox.setText("<center>Merci pour votre contribution, si votre navigteur ne s'ouvre pas, vous pouvez le faire depuis la page https://github.com/cedricp/ddt4all</center>")
        msgbox.exec_()


class portChooser(gui.QDialog):
    def __init__(self):
        portSpeeds = [38400, 57600, 115200, 230400, 500000]
        self.port = None
        self.mode = 0
        self.securitycheck = False
        self.selectedportspeed = 38400
        super(portChooser, self).__init__(None)
        ports = elm.get_available_ports()
        layout = gui.QVBoxLayout()
        label = gui.QLabel(self)
        label.setText("Selection du port ELM")
        label.setAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)
        donationwidget = donationWidget()
        self.setLayout(layout)
        
        self.listview = gui.QListWidget(self)

        layout.addWidget(donationwidget)
        layout.addWidget(label)
        layout.addWidget(self.listview)

        speedlayout = gui.QHBoxLayout()
        self.speedcombo = gui.QComboBox()
        speedlabel = gui.QLabel("Vitesse du port")
        speedlayout.addWidget(speedlabel)
        speedlayout.addWidget(self.speedcombo)

        for s in portSpeeds:
            self.speedcombo.addItem(str(s))

        self.speedcombo.setCurrentIndex(0)

        layout.addLayout(speedlayout)

        button_layout = gui.QHBoxLayout()
        button_con = gui.QPushButton("Mode CONNECTE")
        button_dmo = gui.QPushButton("Mode DEMO")

        wifilayout = gui.QHBoxLayout()
        self.wifienable = gui.QCheckBox()
        self.wifienable.setChecked(False)
        wifilabel = gui.QLabel("WiFi port : ")
        self.wifiinput = gui.QLineEdit()
        self.wifiinput.setText("192.168.0.10:35000")
        wifilayout.addWidget(self.wifienable)
        wifilayout.addWidget(wifilabel)
        wifilayout.addWidget(self.wifiinput)
        layout.addLayout(wifilayout)

        safetychecklayout = gui.QHBoxLayout()
        self.safetycheck = gui.QCheckBox()
        self.safetycheck.setChecked(False)
        safetylabel = gui.QLabel("J'ai bien lu les recommandations")
        safetychecklayout.addWidget(self.safetycheck)
        safetychecklayout.addWidget(safetylabel)
        layout.addLayout(safetychecklayout)

        button_layout.addWidget(button_con)
        button_layout.addWidget(button_dmo)
        layout.addLayout(button_layout)

        button_con.clicked.connect(self.connectedMode)
        button_dmo.clicked.connect(self.demoMode)
        self.wifienable.clicked.connect(self.wifiCheck)
        
        for p in ports:
            item = gui.QListWidgetItem(self.listview)
            item.setText(p)

    def wifiCheck(self):
        self.listview.setEnabled(not self.wifienable.isChecked())

    def connectedMode(self):
        self.securitycheck = self.safetycheck.isChecked()
        self.selectedportspeed = int(self.speedcombo.currentText())
        print self.selectedportspeed
        if not pc.securitycheck:
            msgbox = gui.QMessageBox()
            msgbox.setText("Vous devez cocher la case vous demandant si vous avez pris connaissance des recommandations")
            msgbox.exec_()
            return

        if self.wifienable.isChecked():
            self.port = str(self.wifiinput.text())
            self.mode = 1
            self.close()
        else:
            currentitem = self.listview.currentItem()
            if currentitem:
                self.port = currentitem.text()
                self.mode = 1
                self.close()
            else:
                msgbox = gui.QMessageBox()
                msgbox.setText("Vous devez selectionner un port communication")
                msgbox.exec_()

    def demoMode(self):
        self.securitycheck = self.safetycheck.isChecked()
        self.port = 'DUMMY'
        self.mode = 2
        self.close()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

    options.simultation_mode = True
    app = gui.QApplication(sys.argv)
    pc = portChooser()
    pc.exec_()

    if pc.mode == 0:
        exit(0)
    if pc.mode == 1:
        options.promode = False
        options.simulation_mode = False
    if pc.mode == 2:
         options.promode = False
         options.simulation_mode = True

    options.port = str(pc.port)
    port_speed = pc.selectedportspeed

    if not options.port:
        msgbox = gui.QMessageBox()
        msgbox.setText("Pas de port de communication selectionne")
        msgbox.exec_()
        exit(0)

    print "Initilizing ELM with speed %i..." % options.port_speed
    options.elm = elm.ELM(options.port, options.port_speed)
    if port_speed != options.port_speed:
        options.elm.port.soft_baudrate(port_speed)

    if options.elm_failed:
        msgbox = gui.QMessageBox()
        msgbox.setText("Pas d'ELM327 sur le port communication selectionne")
        msgbox.exec_()
        exit(0)

    w = Main_widget()
    w.show()
    app.exec_()
