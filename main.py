#!/usr/bin/python

import sys
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
        self.ecu_scan.scan()
        print "Scan finished, %i ECU(s) found on CAN" % self.ecu_scan.num_ecu_found
        self.initUI()
        
    def initUI(self):
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
        self.treeview_ecu = gui.QTreeWidget(self.treedock_ecu)
        self.treeview_ecu.setHeaderLabels(["ECUs"])
        self.treedock_ecu.setWidget(self.treeview_ecu)
        self.treeview_ecu.doubleClicked.connect(self.changeECU)
        
        i = 0
        for ecu in self.ecu_scan.ecus:
            item = gui.QTreeWidgetItem(self.treeview_ecu, [ecu.name])
            item.setData(0, core.Qt.UserRole, str(i))
            i += 1
        
        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treedock_ecu)
        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treedock_params)
        self.addDockWidget(core.Qt.BottomDockWidgetArea, self.treedock_logs)
        
        menu = self.menuBar()
        diagmenu = menu.addMenu("Diagnostic")
        dtcaction = diagmenu.addAction("Lire DTC")
        dtcaction.triggered.connect(self.readDTC)
        
        
    def readDTC(self):
        if self.paramview:
            self.paramview.readDTC()
        
    def changeScreen(self, index):
        item = self.treeview_params.model().itemData(index)
        screen = unicode(item[0].toPyObject().toUtf8(), encoding="UTF-8")
        self.paramview.init(screen)
    
    def changeECU(self, index):
        item = self.treeview_params.model().itemData(index)
        ecu_from_index = item[core.Qt.UserRole].toInt()
        
        if ecu_from_index[1] == False:
            print "Changement ECU impossible"
            return

        self.treeview_params.clear()
        
        ecu_name = ecu_from_index[0]
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
        button_pro = gui.QPushButton("Mode PRO")
        button_jnr = gui.QPushButton("Mode LECTURE")
        button_dmo = gui.QPushButton("Mode DEMO")
        button_layout.addWidget(button_jnr)
        button_layout.addWidget(button_pro)
        button_layout.addWidget(button_dmo)
        layout.addLayout(button_layout)
        
        button_pro.clicked.connect(self.proMode)
        button_jnr.clicked.connect(self.dumbMode)
        button_dmo.clicked.connect(self.demoMode)
        
        for p in ports:
            item = gui.QListWidgetItem(self.listview)
            item.setText(p)
    
    def proMode(self):
        self.port = self.listview.currentItem().text()
        self.mode = 1
        self.close()

    def dumbMode(self):
        self.port = self.listview.currentItem().text()
        self.mode = 2    
        self.close()

    def demoMode(self):
        self.port = ''
        self.mode = 3    
        self.close()
        
if __name__ == '__main__':
    options.simultation_mode = True
    app = gui.QApplication(sys.argv)
    pc = portChooser()
    pc.exec_()
    if pc.mode == 0:
        exit(0)
    if pc.mode == 1:
        options.promode = True
        options.simulation_mode = False
    if pc.mode == 2:
        options.promode = False
        options.simulation_mode = False
    if pc.mode == 3:
         options.promode = False
         options.simulation_mode = True
    options.port = str(pc.port)
    
    print "Initilizing ELM..."
    options.elm = elm.ELM(options.port, options.port_speed)
    w = Main_widget()
    w.show()
    app.exec_()
