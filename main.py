#!/usr/bin/python

import sys
import os
import pickle
import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import parameters, ecu
import elm, options

class Main_widget(gui.QMainWindow):
    def __init__(self, parent = None):
        super(Main_widget, self).__init__(parent)
        self.setWindowTitle("DDT4all")
        print "Scanning ECUs..."
        self.ecu_scan = ecu.Ecu_scanner()
        print "Done, %i loaded ECUs in database." % self.ecu_scan.getNumEcuDb()
        self.initUI()

    def scan(self):
        progressWidget = gui.QWidget(None)
        progressLayout = gui.QVBoxLayout()
        labelWidget = gui.QLabel()
        progress = gui.QProgressBar()
        progressLayout.addWidget(progress)
        progressLayout.addWidget(labelWidget)
        progressWidget.setLayout(progressLayout)
        progress.setRange(0, self.ecu_scan.getNumAddr())
        progressWidget.show()
        progress.setValue(0)

        self.ecu_scan.scan(progress, labelWidget)

        self.treeview_ecu.clear()
        self.treeview_params.clear()
        if self.paramview:
            self.paramview.init(None)

        for ecu in self.ecu_scan.ecus.keys():
            item = gui.QListWidgetItem(ecu)
            self.treeview_ecu.addItem(item)
        
    def initUI(self):
        self.paramview = None

        self.scrollview = gui.QScrollArea()
        self.scrollview.setWidgetResizable(False)
        self.setCentralWidget(self.scrollview)
        
        self.treedock_params = gui.QDockWidget(self)
        self.treeview_params = gui.QTreeWidget(self.treedock_params)
        self.treedock_params.setWidget(self.treeview_params)
        self.treeview_params.setHeaderLabels(["Screens"])
        self.treeview_params.doubleClicked.connect(self.changeScreen)

        self.treedock_logs = gui.QDockWidget(self)
        self.logview       = gui.QTextEdit()
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
        diagmenu = menu.addMenu("Diagnostic")
        savevehicleaction = diagmenu.addAction("Sauvegarder ce vehicule")
        savevehicleaction.triggered.connect(self.saveEcus)
        diagmenu.addSeparator()

        for ecu in ecu_files:
            ecuaction = diagmenu.addAction(ecu)
            ecuaction.triggered.connect(lambda state, a=ecu: self.loadEcu(a))

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

    def changeECU(self, index):
        item = self.treeview_ecu.model().itemData(index)
        ecu_name = unicode(item[0].toString().toUtf8(), encoding="UTF-8")
        self.treeview_params.clear()

        ecu = self.ecu_scan.ecus[ecu_name]
        ecu_file = "ecus/" + ecu.href
        ecu_addr = ecu.addr
        self.paramview = parameters.paramWidget(self.scrollview, ecu_file, ecu_addr, ecu_name, self.logview)
        self.scrollview.setWidget(self.paramview)
        
        screens = self.paramview.categories.keys()
        for screen in screens:
            item = gui.QTreeWidgetItem(self.treeview_params, [screen])
            for param in self.paramview.categories[screen]:
                param_item = gui.QTreeWidgetItem(item, [param])
                param_item.setData(0, core.Qt.UserRole, param)


class portChooser(gui.QDialog):
    def __init__(self):
        self.port = None
        self.mode = 0
        super(portChooser, self).__init__(None)
        ports = elm.get_available_ports()
        layout = gui.QVBoxLayout()
        label = gui.QLabel(self)
        label.setText("Selection du port ELM")
        label.setAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)
        
        self.setLayout(layout)
        
        self.listview = gui.QListWidget(self)
        
        layout.addWidget(label)
        layout.addWidget(self.listview)
        
        button_layout = gui.QHBoxLayout()
        button_con = gui.QPushButton("Mode CONNECTE")
        button_dmo = gui.QPushButton("Mode DEMO")

        button_layout.addWidget(button_con)
        button_layout.addWidget(button_dmo)
        layout.addLayout(button_layout)

        button_con.clicked.connect(self.connectedMode)
        button_dmo.clicked.connect(self.demoMode)
        
        for p in ports:
            item = gui.QListWidgetItem(self.listview)
            item.setText(p)

    def connectedMode(self):
        currentitem = self.listview.currentItem()
        if currentitem:
            self.port = currentitem.text()
        self.mode = 1
        self.close()

    def demoMode(self):
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

    if not options.port:
        msgbox = gui.QMessageBox()
        msgbox.setText("Pas de port de communication selectionne")
        msgbox.exec_()
        exit(0)

    print "Initilizing ELM..."
    options.elm = elm.ELM(options.port, options.port_speed)

    if options.elm_failed:
        msgbox = gui.QMessageBox()
        msgbox.setText("Pas d'ELM327 sur le port communication selectionne")
        msgbox.exec_()
        exit(0)

    w = Main_widget()
    w.show()
    app.exec_()
