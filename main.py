#!/usr/bin/python

import sys, os
import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import parameters, ecu


class Main_widget(gui.QMainWindow):
    def __init__(self, parent = None):
        super(Main_widget, self).__init__(parent)
        self.initUI()
        
    def initUI(self):
        self.scrollview = gui.QScrollArea()
        self.paramview = parameters.Param_widget(self.scrollview, "ecus/UCT_E84_PS.xml")
        self.scrollview.setWidget(self.paramview)
        self.scrollview.setWidgetResizable(False)
        self.setCentralWidget(self.scrollview)
        self.treedock = gui.QDockWidget(self)
        self.treeview = gui.QTreeWidget(self.treedock)
        self.treedock.setWidget(self.treeview)
        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treedock)
        self.treeview.doubleClicked.connect(self.changeScreen)
        screens = self.paramview.categories.keys()
        for screen in screens:
            item = gui.QTreeWidgetItem(self.treeview, [screen])
            for param in self.paramview.categories[screen]:
                param_item = gui.QTreeWidgetItem(item, [param])
                param_item.setData(0, core.Qt.UserRole, param)
         
        menu = self.menuBar()
        diagmenu = menu.addMenu("Diagnostic")
        dtcaction = diagmenu.addAction("Lire DTC")
        dtcaction.triggered.connect(self.readDTC)
        
        
    def readDTC(self):
        print "DTC"
    def changeScreen(self, index):
        item = self.treeview.model().itemData(index)
        screen = unicode(item[0].toPyObject().toUtf8(), encoding="UTF-8")
        self.paramview.init(screen)
        
        
if __name__ == '__main__':
    ecu_scan = ecu.Ecu_scanner()
    ecu_scan.scan()
    app = gui.QApplication(sys.argv)
    w = Main_widget()
    w.show()
    app.exec_()
