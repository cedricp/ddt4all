#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import glob
import json
from importlib.machinery import SourceFileLoader

import PyQt5.QtGui as gui
import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets
try:
    import PyQt5.QtWebEngine as webkit
    import PyQt5.QtWebEngineWidgets as webkitwidgets
except:
    import PyQt5.QtWebKit as webkit
    import PyQt5.QtWebKitWidgets as webkitwidgets


def utf8(string):
    return string


import parameters, ecu
import elm, options, locale
import dataeditor
import sniffer
#import imp
import tempfile, errno
import codecs

__author__ = "Cedric PAILLE"
__copyright__ = "Copyright 2016-2020"
__credits__ = []
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Cedric PAILLE"
__email__ = "cedricpaille@gmail.com"
__status__ = "Beta"

_ = options.translator('ddt4all')
app = None

def isWritable(path):
    try:
        testfile = tempfile.TemporaryFile(dir=path)
        testfile.close()
    except OSError as e:
        if e.errno == errno.EACCES:  # 13
            return False
        e.filename = path
    except:
        return False
    return True

class Ecu_finder(widgets.QDialog):
    def __init__(self, ecuscanner):
        super(Ecu_finder, self).__init__()
        self.ecuscanner = ecuscanner
        layoutv = widgets.QVBoxLayout()
        layouth = widgets.QHBoxLayout()
        self.setLayout(layoutv)
        layoutv.addLayout(layouth)
        self.ecuaddr = widgets.QLineEdit()
        self.ecuident = widgets.QLineEdit()
        layouth.addWidget(widgets.QLabel("Addr :"))
        layouth.addWidget(self.ecuaddr)
        layouth.addWidget(widgets.QLabel("ID frame :"))
        layouth.addWidget(self.ecuident)
        button = widgets.QPushButton("VALIDATE")
        layouth.addWidget(button)
        button.clicked.connect(self.check)

    def check(self):
        addr = utf8(self.ecuaddr.text())
        frame = utf8(self.ecuident.text())
        self.ecuscanner.identify_from_frame(addr, frame)

class Ecu_list(widgets.QWidget):
    def __init__(self, ecuscan, treeview_ecu):
        super(Ecu_list, self).__init__()
        self.selected = ''
        self.treeview_ecu = treeview_ecu
        self.vehicle_combo = widgets.QComboBox()

        self.ecu_map = {}
        vehicles = [
            "ALL", "XBA - KWID CN", "XBB - KWID BR", "X06 - TWINGO", "X44 - TWINGO II",
            "X07 - TWINGO III", "X77 - MODUS", "X35 - SYMBOL/THALIA", "XJC - SYMBOL/THALIA II",
            "X65 - CLIO II",
            "X85 - CLIO III", "X98 - CLIO IV", "XJA - CLIO V", "X87 - CAPTUR", "XJB - CAPTUR II",
            "XJE - CAPTUR II CN", "X38 - FLUENCE", "XFF - FLUENCE II", "X64 - MEGANE/SCENIC I",
            "X84 - MEGANE/SCENIC II", "X84ph2 - MEGANE/SCENIC II Phase 2", "X95 - MEGANE/SCENIC III",
            "XFB - MEGANE IV", "XFF - MEGANE IV SEDAN",
            "XFA - SCENIC IV", "X56 - LAGUNA", "X74 - LAGUNA II", "X74ph2 - LAGUNA II Phase 2", "X91 - LAGUNA III",
            "X47 - LAGUNA III (tricorps)", "X66 - ESPACE III", "X81 - ESPACE IV", "XFC - ESPACE V",
            "X73 - VELSATIS", "X43 - LATITUDE", "XFD - TALISMAN", "H45 - KOLEOS", "XZG - KOLEOS II",
            "XZJ - KOLEOS II CN", "HFE - KADJAR", "XZH - KADJAR CN", "X33 - WIND", "X09 - TWIZY",
            "X10 - ZOE", "X10Ph2 - ZOE Ph2", "X76 - KANGOO I", "X61 - KANGOO II", "XFK - KANGOO III",
            "X24 - MASCOTT", "X83 - TRAFFIC II", "X82 - TRAFFIC III",
            "X70 - MASTER II", "X62 - MASTER III", "X90 - LOGAN/SANDERO",
            "X52 - LOGAN/SANDERO II", "X79 - DUSTER", "X79Ph2 - DUSTER Ph2", "XJD - DUSTER II", "X67 - DOKKER",
            "X92 - LODGY", "XGA - BM LADA", "AS1 - ALPINE", "X02 - MICRA (NISSAN)", "X02E - MICRA (NISSAN)",
            "X21 - NOTE (NISSAN)"
        ]

        for v in vehicles:
            self.vehicle_combo.addItem(v)

        self.vehicle_combo.activated.connect(self.filterProject)

        layout = widgets.QVBoxLayout()
        layouth = widgets.QHBoxLayout()
        scanbutton = widgets.QPushButton()
        scanbutton.setIcon(gui.QIcon("icons/scan.png"))
        scanbutton.clicked.connect(self.scanselvehicle)
        layouth.addWidget(self.vehicle_combo)
        layouth.addWidget(scanbutton)
        layout.addLayout(layouth)
        self.setLayout(layout)
        self.list = widgets.QTreeWidget(self)
        self.list.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        layout.addWidget(self.list)
        self.ecuscan = ecuscan
        self.list.doubleClicked.connect(self.ecuSel)
        self.init()

    def scanselvehicle(self):
        project = str(self.vehicle_combo.currentText()[0:3])
        self.parent().parent().scan_project(project)

    def init(self):
        self.list.clear()
        self.list.setColumnCount(8)
        self.list.model().setHeaderData(0, core.Qt.Horizontal, _('ECU name'))
        self.list.model().setHeaderData(1, core.Qt.Horizontal, _('ID'))
        self.list.model().setHeaderData(2, core.Qt.Horizontal, _('Protocol'))
        self.list.model().setHeaderData(3, core.Qt.Horizontal, _('Supplier'))
        self.list.model().setHeaderData(4, core.Qt.Horizontal, _('Diag'))
        self.list.model().setHeaderData(5, core.Qt.Horizontal, _('Soft'))
        self.list.model().setHeaderData(6, core.Qt.Horizontal, _('Version'))
        self.list.model().setHeaderData(7, core.Qt.Horizontal, _('Projets'))
        stored_ecus = {"Custom": []}

        custom_files = glob.glob("./json/*.json.targets")

        for cs in custom_files:
            f = open(cs, "r")
            jsoncontent = f.read()
            f.close()

            target = json.loads(jsoncontent)

            if not target:
                grp = "Custom"
                projects_list = []
                protocol = ''
            else:
                target = target[0]
                protocol = target['protocol']
                projects_list = target['projects']
                if target['address'] not in self.ecu_map:
                    grp = "Custom"
                else:
                    grp = self.ecu_map[target['address']]

            if not grp in stored_ecus:
                stored_ecus[grp] = []

            name = "/".join(projects_list)

            stored_ecus[grp].append([cs[:-8][7:], name, protocol])

        longgroupnames = {}
        for ecu in self.ecuscan.ecu_database.targets:
            if ecu.addr in self.ecuscan.ecu_database.addr_group_mapping:
                grp = self.ecuscan.ecu_database.addr_group_mapping[ecu.addr]
                if ecu.addr in self.ecuscan.ecu_database.addr_group_mapping_long:
                    longgroupnames[grp] = self.ecuscan.ecu_database.addr_group_mapping_long[ecu.addr]
            else:
                grp = "?"

            if not grp in stored_ecus:
                stored_ecus[grp] = []

            projname = "/".join(ecu.projects)

            soft = ecu.soft
            version = ecu.version
            supplier = ecu.supplier
            diag = ecu.diagversion

            row = [ecu.name, ecu.addr, ecu.protocol, supplier, diag, soft, version, projname]
            found = False
            for r in stored_ecus[grp]:
                if (r[0], r[1]) == (row[0], row[1]):
                    found = True
                    break
            if not found:
                stored_ecus[grp].append(row)

        keys = list(stored_ecus.keys())
        try:
            keys.sort(cmp=locale.strcoll)
        except:
            keys.sort()
        for e in keys:
            item = widgets.QTreeWidgetItem(self.list, [e])
            if e in longgroupnames:
                item.setToolTip(0, longgroupnames[e])
            if e in self.ecuscan.ecu_database.addr_group_mapping:
                item.setToolTip(self.ecuscan.ecu_database.addr_group_mapping[e])
            for t in stored_ecus[e]:
                widgets.QTreeWidgetItem(item, t)

        self.list.resizeColumnToContents(0)

    def filterProject(self):
        project = str(self.vehicle_combo.currentText().split(" ")[0])
        root = self.list.invisibleRootItem()
        root_items = [root.child(i) for i in range(root.childCount())]

        for root_item in root_items:
            root_hidden = True

            items = [root_item.child(i) for i in range(root_item.childCount())]
            for item in items:
                if (project.upper() in str(item.text(7)).upper().split("/")) or project == "ALL":
                    item.setHidden(False)
                    root_hidden = False
                else:
                    item.setHidden(True)
            root_item.setHidden(root_hidden)

    def ecuSel(self, index):
        if index.parent() == core.QModelIndex():
            return
        item = self.list.model().itemData(self.list.model().index(index.row(), 0, index.parent()))

        selected = item[0]
        target = self.ecuscan.ecu_database.getTarget(selected)
        name = selected
        if target:
            self.ecuscan.addTarget(target)
            if target.addr in self.ecuscan.ecu_database.addr_group_mapping:
                group = self.ecuscan.ecu_database.addr_group_mapping[target.addr]
            else:
                group = "Unknown"
            name = "[ " + group + " ] " + name
        if selected:
            if name not in options.main_window.ecunamemap:
                options.main_window.ecunamemap[name] = selected
                self.treeview_ecu.addItem(name)


class Main_widget(widgets.QMainWindow):
    def __init__(self, parent = None):
        super(Main_widget, self).__init__(parent)

        if not options.simulation_mode:
            if not os.path.exists("./logs"):
                os.mkdir("./logs")
            self.screenlogfile = open("./logs/screens.txt", "at")
        else:
            self.screenlogfile = None

        self.sdsready = False
        self.ecunamemap = {}
        self.plugins = {}
        self.setWindowTitle(_("DDT4All"))
        self.ecu_scan = ecu.Ecu_scanner()
        self.ecu_scan.qapp = app
        options.ecu_scanner = self.ecu_scan
        print(str(self.ecu_scan.getNumEcuDb()) + " " + _("loaded ECUs in database."))
        if self.ecu_scan.getNumEcuDb() == 0:
            msgbox = widgets.QMessageBox()
            msgbox.setIcon(widgets.QMessageBox.Warning)
            msgbox.setText("No database found")
            msgbox.setInformativeText("Check documentation")
            msgbox.exec_()

        self.paramview = None
        try:
            self.docview = webkitwidgets.QWebEngineView()
            self.docview.load(core.QUrl("https://github.com/cedricp/ddt4all/wiki"))
            self.docview.settings().setAttribute(webkitwidgets.QWebEngineSettings.JavascriptEnabled, True)
            self.docview.settings().setAttribute(webkitwidgets.QWebEngineSettings.PluginsEnabled, True)
            self.docview.settings().setAttribute(webkitwidgets.QWebEngineSettings.AutoLoadImages, True)
        except:
            self.docview = webkitwidgets.QWebView()
            self.docview.load(core.QUrl("https://github.com/cedricp/ddt4all/wiki"))
            self.docview.settings().setAttribute(webkit.QWebSettings.JavascriptEnabled, True)
            self.docview.settings().setAttribute(webkit.QWebSettings.PluginsEnabled, True)
            self.docview.settings().setAttribute(webkit.QWebSettings.AutoLoadImages, True)

        self.screennames = []

        self.statusBar = widgets.QStatusBar()
        self.setStatusBar(self.statusBar)

        self.connectedstatus = widgets.QLabel()
        self.connectedstatus.setAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)
        self.protocolstatus = widgets.QLabel()
        self.progressstatus = widgets.QProgressBar()
        self.infostatus = widgets.QLabel()

        self.connectedstatus.setFixedWidth(100)
        self.protocolstatus.setFixedWidth(200)
        self.progressstatus.setFixedWidth(150)
        self.infostatus.setFixedWidth(200)

        self.refreshtimebox = widgets.QSpinBox()
        self.refreshtimebox.setRange(5, 2000)
        self.refreshtimebox.setValue(options.refreshrate)
        self.refreshtimebox.setSingleStep(100)
        self.refreshtimebox.valueChanged.connect(self.changeRefreshTime)
        refrestimelabel = widgets.QLabel(_("Refresh rate (ms):"))

        self.cantimeout = widgets.QSpinBox()
        self.cantimeout.setRange(0, 1000)
        self.cantimeout.setSingleStep(200)
        self.cantimeout.setValue(options.cantimeout)
        self.cantimeout.valueChanged.connect(self.changeCanTimeout)
        cantimeoutlabel = widgets.QLabel(_("Can timeout (ms) [0:AUTO] :"))

        self.statusBar.addWidget(self.connectedstatus)
        self.statusBar.addWidget(self.protocolstatus)
        self.statusBar.addWidget(self.progressstatus)
        self.statusBar.addWidget(refrestimelabel)
        self.statusBar.addWidget(self.refreshtimebox)
        self.statusBar.addWidget(cantimeoutlabel)
        self.statusBar.addWidget(self.cantimeout)
        self.statusBar.addWidget(self.infostatus)

        self.tabbedview = widgets.QTabWidget()
        self.setCentralWidget(self.tabbedview)

        self.scrollview = widgets.QScrollArea()
        self.scrollview.setWidgetResizable(False)

        self.snifferview = sniffer.sniffer()

        self.tabbedview.addTab(self.docview, _("Documentation"))
        self.tabbedview.addTab(self.scrollview, _("Screen"))
        self.tabbedview.addTab(self.snifferview, _("CAN Sniffer"))

        if options.simulation_mode:
            self.buttonEditor = dataeditor.buttonEditor()
            self.requesteditor = dataeditor.requestEditor()
            self.dataitemeditor = dataeditor.dataEditor()
            self.ecuparameditor = dataeditor.ecuParamEditor()
            self.tabbedview.addTab(self.requesteditor, _("Requests"))
            self.tabbedview.addTab(self.dataitemeditor, _("Data"))
            self.tabbedview.addTab(self.buttonEditor, _("Buttons"))
            self.tabbedview.addTab(self.ecuparameditor, _("Ecu parameters"))

        screen_widget = widgets.QWidget()
        self.treedock_widget = widgets.QDockWidget(self)
        self.treedock_widget.setWidget(screen_widget)
        self.treeview_params = widgets.QTreeWidget()
        self.treeview_params.setSortingEnabled(True)
        self.treeview_params.sortByColumn(0, core.Qt.AscendingOrder)

        treedock_layout = widgets.QVBoxLayout()
        treedock_layout.addWidget(self.treeview_params)
        screen_widget.setLayout(treedock_layout)
        self.treeview_params.setHeaderLabels([_("Screens")])
        self.treeview_params.clicked.connect(self.changeScreen)

        self.treedock_logs = widgets.QDockWidget(self)
        self.logview = widgets.QTextEdit()
        self.logview.setReadOnly(True)
        self.treedock_logs.setWidget(self.logview)

        self.treedock_ecu = widgets.QDockWidget(self)
        self.treeview_ecu = widgets.QListWidget(self.treedock_ecu)
        self.treedock_ecu.setWidget(self.treeview_ecu)
        self.treeview_ecu.clicked.connect(self.changeECU)

        self.eculistwidget = Ecu_list(self.ecu_scan, self.treeview_ecu)
        self.treeview_eculist = widgets.QDockWidget(self)
        self.treeview_eculist.setWidget(self.eculistwidget)

        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treeview_eculist)
        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treedock_ecu)
        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treedock_widget)
        self.addDockWidget(core.Qt.BottomDockWidgetArea, self.treedock_logs)

        self.toolbar = self.addToolBar(_("File"))

        self.diagaction = widgets.QAction(gui.QIcon("icons/dtc.png"), _("Read DTC"), self)
        self.diagaction.triggered.connect(self.readDtc)
        self.diagaction.setEnabled(False)

        self.log = widgets.QAction(gui.QIcon("icons/log.png"), _("Full log"), self)
        self.log.setCheckable(True)
        self.log.setChecked(options.log_all)
        self.log.triggered.connect(self.changeLogMode)

        self.expert = widgets.QAction(gui.QIcon("icons/expert.png"), _("Expert mode (enable writing)"), self)
        self.expert.setCheckable(True)
        self.expert.setChecked(options.promode)
        self.expert.triggered.connect(self.changeUserMode)

        self.autorefresh = widgets.QAction(gui.QIcon("icons/autorefresh.png"), _("Auto refresh"), self)
        self.autorefresh.setCheckable(True)
        self.autorefresh.setChecked(options.auto_refresh)
        self.autorefresh.triggered.connect(self.changeAutorefresh)

        self.refresh = widgets.QAction(gui.QIcon("icons/refresh.png"), _("Refresh (one shot)"), self)
        self.refresh.triggered.connect(self.refreshParams)
        self.refresh.setEnabled(not options.auto_refresh)

        self.hexinput = widgets.QAction(gui.QIcon("icons/hex.png"), _("Manual command"), self)
        self.hexinput.triggered.connect(self.hexeditor)
        self.hexinput.setEnabled(False)

        self.cominput = widgets.QAction(gui.QIcon("icons/command.png"), _("Manual request"), self)
        self.cominput.triggered.connect(self.command_editor)
        self.cominput.setEnabled(False)

        self.fctrigger = widgets.QAction(gui.QIcon("icons/flowcontrol.png"), _("Software flow control"), self)
        self.fctrigger.setCheckable(True)
        self.fctrigger.triggered.connect(self.flow_control)

        self.canlinecombo = widgets.QComboBox()
        self.canlinecombo.setFixedWidth(150)

        self.sdscombo = widgets.QComboBox()
        self.sdscombo.setFixedWidth(300)
        self.sdscombo.currentIndexChanged.connect(self.changeSds)
        self.sdscombo.setEnabled(False)

        self.zoominbutton = widgets.QPushButton(_("Zoom In"))
        self.zoomoutbutton = widgets.QPushButton(_("Zoom Out"))
        self.zoominbutton.clicked.connect(self.zoomin)
        self.zoomoutbutton.clicked.connect(self.zoomout)

        self.toolbar.addSeparator()
        self.toolbar.addAction(self.log)
        self.toolbar.addAction(self.expert)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.autorefresh)
        self.toolbar.addAction(self.refresh)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.diagaction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.hexinput)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.cominput)
        self.toolbar.addAction(self.fctrigger)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.canlinecombo)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.sdscombo)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.zoominbutton)
        self.toolbar.addWidget(self.zoomoutbutton)

        if options.simulation_mode:
            self.toolbar.addSeparator()
            self.ui_edit_button = widgets.QPushButton(_("UI Edit"))
            self.ui_edit_button.setCheckable(True)
            self.toolbar.addSeparator()
            self.toolbar.addWidget(self.ui_edit_button)
            self.ui_edit_button.clicked.connect(self.toggle_edit)

        vehicle_dir = "vehicles"
        if not os.path.exists(vehicle_dir):
            os.mkdir(vehicle_dir)

        ecu_files = []
        for filename in os.listdir(vehicle_dir):
            basename, ext = os.path.splitext(filename)
            if ext == '.ecu':
                ecu_files.append(basename)

        menu = self.menuBar()

        diagmenu = menu.addMenu(_("File"))
        xmlopenaction = diagmenu.addAction(_("Open XML"))
        identecu = diagmenu.addAction(_("Identify ECU"))
        newecuction = diagmenu.addAction(_("Create New ECU"))
        saveecuaction = diagmenu.addAction(_("Save current ECU"))
        diagmenu.addSeparator()
        saverecordaction = diagmenu.addAction(_("Save last record"))
        diagmenu.addSeparator()
        savevehicleaction = diagmenu.addAction(_("Save ECU list"))
        savevehicleaction.triggered.connect(self.saveEcus)
        saveecuaction.triggered.connect(self.saveEcu)
        saverecordaction.triggered.connect(self.saveRecord)
        newecuction.triggered.connect(self.newEcu)
        xmlopenaction.triggered.connect(self.openxml)
        identecu.triggered.connect(self.identEcu)
        diagmenu.addSeparator()
        zipdbaction = diagmenu.addAction(_("Zip database"))
        zipdbaction.triggered.connect(self.zipdb)
        diagmenu.addSeparator()

        for ecuf in ecu_files:
            ecuaction = diagmenu.addAction(ecuf)
            ecuaction.triggered.connect(lambda state, a=ecuf: self.loadEcu(a))

        self.screenmenu = menu.addMenu(_("Screens"))

        actionmenu = self.screenmenu.addMenu(_("Action"))
        cat_action = widgets.QAction(_("New Category"), actionmenu)
        screen_action = widgets.QAction(_("New Screen"), actionmenu)
        rename_action = widgets.QAction(_("Rename"), actionmenu)
        actionmenu.addAction(cat_action)
        actionmenu.addAction(screen_action)
        actionmenu.addAction(rename_action)
        cat_action.triggered.connect(self.newCategory)
        screen_action.triggered.connect(self.newScreen)
        rename_action.triggered.connect(self.screenRename)

        plugins_menu = menu.addMenu(_("Plugins"))
        category_menus = {}
        plugins = glob.glob("./ddtplugins/*.py")
        for plugin in plugins:
            try:
                modulename = os.path.basename(plugin).replace(".py", "")
                plug = SourceFileLoader(modulename, plugin).load_module()

                category = plug.category
                name = plug.plugin_name
                need_hw = plug.need_hw

                #if options.simulation_mode and need_hw:
                #    continue

                if not category in category_menus:
                    category_menus[category] = plugins_menu.addMenu(category)

                plug_action = category_menus[category].addAction(name)
                plug_action.triggered.connect(lambda state, a=plug.plugin_entry: self.launchPlugin(a))

                self.plugins[modulename] = plug
            except Exception as e:
                print("Cannot load plugin "  + plugin)
                print(e)

        self.setConnected(True)
        self.tabbedview.setCurrentIndex(1)

    def set_can_combo(self, bus):
        self.canlinecombo.clear()
        try:
            self.canlinecombo.clicked.disconnect()
        except Exception:
            pass
        if bus == "CAN":
            self.canlinecombo.addItem("CAN Line 1 Auto")
            self.canlinecombo.addItem("CAN Line 1@500K")
            self.canlinecombo.addItem("CAN Line 1@250K")
            if options.elm is not None and options.elm.adapter_type == "ELS":
                self.canlinecombo.addItem("CAN Line 2@500K")
                self.canlinecombo.addItem("CAN Line 2@250K")
                self.canlinecombo.addItem("CAN Line 2@125K")
            self.canlinecombo.currentIndexChanged.connect(self.changecanspeed)
        else:
            if bus == "KWP2000":
                self.canlinecombo.addItem("KWP2000")
            if bus == "ISO8":
                self.canlinecombo.addItem("ISO8")

    def flow_control(self):
        enabled = self.fctrigger.isChecked()
        options.opt_cfc0 = enabled
        if self.paramview is not None:
            self.paramview.set_soft_fc(enabled)

    def identEcu(self):
        dialog = Ecu_finder(self.ecu_scan)
        dialog.exec_()

    def changecanspeed(self):
        item = self.canlinecombo.currentIndex()
        if self.paramview:
            self.paramview.setCanLine(item)

    def zoomin(self):
        if self.paramview:
            self.paramview.zoomin_page()

    def zoomout(self):
        if self.paramview:
            self.paramview.zoomout_page()

    def toggle_edit(self):
        options.mode_edit = self.ui_edit_button.isChecked()

        if self.paramview:
            self.paramview.reinitScreen()

    def changeSds(self):
        if not self.sdsready:
            return

        if self.paramview:
            currenttext = self.sdscombo.currentText()
            if len(currenttext):
                self.paramview.changeSDS(currenttext)

    def zipdb(self):
        filename_tuple = widgets.QFileDialog.getSaveFileName(self, _("Save database (keep '.zip' extension)"),
                                                   "./ecu.zip", "*.zip")

        filename = str(filename_tuple[0])

        if not filename.endswith(".zip"):
            filename += ".zip"

        if not isWritable(str(os.path.dirname(filename))):
            mbox = widgets.QMessageBox()
            mbox.setText("Cannot write to directory " + os.path.dirname(filename))
            mbox.exec_()
            return

        self.logview.append(_("Zipping XML database... (this can take a few minutes"))
        core.QCoreApplication.processEvents()
        parameters.zipConvertXML(filename)
        self.logview.append(_("Zip job finished"))

    def launchPlugin(self, pim):
        if self.paramview:
            self.paramview.init('')
        pim()
        if self.paramview:
            self.paramview.initELM()

    def screenRename(self):
        item = self.treeview_params.currentItem()
        if not item:
            return

        itemname = utf8(item.text(0))
        nin = widgets.QInputDialog.getText(self, 'DDT4All', _('Enter new name'))

        if not nin[1]:
            return

        newitemname = utf8(nin[0])

        if newitemname == itemname:
            return

        if item.parent():
            self.screennames.remove(itemname)
            self.screennames.append(newitemname)
            self.paramview.renameScreen(itemname, newitemname)
        else:
            self.paramview.renameCategory(itemname, newitemname)

        item.setText(0, newitemname)

    def newCategory(self):
        ncn = widgets.QInputDialog.getText(self, 'DDT4All', _('Enter category name'))
        necatname = utf8(ncn[0])
        if necatname:
            self.paramview.createCategory(necatname)
            self.treeview_params.addTopLevelItem(widgets.QTreeWidgetItem([necatname]))

    def newScreen(self):
        item = self.treeview_params.currentItem()

        if not item:
            self.logview.append("<font color=red>" + _("Please select a category before creating new screen") + "</font>")
            return

        if item.parent() is not None:
            item = item.parent()

        category = utf8(item.text(0))
        nsn = widgets.QInputDialog.getText(self, 'DDT4All', _('Enter screen name'))

        if not nsn[1]:
            return

        newscreenname = utf8(nsn[0])
        if newscreenname:
            self.paramview.createScreen(newscreenname, category)

            item.addChild(widgets.QTreeWidgetItem([newscreenname]))
            self.screennames.append(newscreenname)

    def showDataTab(self, name):
        self.tabbedview.setCurrentIndex(4)
        self.dataitemeditor.edititem(name)

    def hexeditor(self):
        if self.paramview:
            # Stop auto refresh
            options.auto_refresh = False
            self.refresh.setEnabled(False)
            self.paramview.hexeditor()

    def command_editor(self):
        if self.paramview:
            # Stop auto refresh
            options.auto_refresh = False
            self.refresh.setEnabled(False)
            self.paramview.command_editor()

    def changeRefreshTime(self):
        options.refreshrate = self.refreshtimebox.value()

    def changeCanTimeout(self):
        options.cantimeout = self.cantimeout.value()
        if self.paramview:
            self.paramview.setCanTimeout()

    def scan_project(self, project):
        if project == "ALL":
            self.scan()
            return
        self.ecu_scan.clear()
        self.ecu_scan.scan(self.progressstatus, self.infostatus, project)
        self.ecu_scan.scan_kwp(self.progressstatus, self.infostatus, project)

        for ecu in self.ecu_scan.ecus.keys():
            self.ecunamemap[ecu] = self.ecu_scan.ecus[ecu].name
            item = widgets.QListWidgetItem(ecu)
            if '.xml' in self.ecu_scan.ecus[ecu].href.lower():
                item.setForeground(core.Qt.yellow)
            else:
                item.setForeground(core.Qt.green)
            self.treeview_ecu.addItem(item)

        for ecu in self.ecu_scan.approximate_ecus.keys():
            self.ecunamemap[ecu] = self.ecu_scan.approximate_ecus[ecu].name
            item = widgets.QListWidgetItem(ecu)
            item.setForeground(core.Qt.red)
            self.treeview_ecu.addItem(item)

    def scan(self):
        msgBox = widgets.QMessageBox()
        msgBox.setText(_('Scan options'))
        scancan = False
        scancan2 = False
        scankwp = False

        canbutton = widgets.QPushButton('CAN')
        kwpbutton = widgets.QPushButton('KWP')
        cancelbutton = widgets.QPushButton(_('CANCEL'))

        msgBox.addButton(canbutton, widgets.QMessageBox.ActionRole)
        msgBox.addButton(kwpbutton, widgets.QMessageBox.ActionRole)
        msgBox.addButton(cancelbutton, widgets.QMessageBox.NoRole)
        msgBox.exec_()

        if msgBox.clickedButton() == cancelbutton:
            return

        if msgBox.clickedButton() == canbutton:
            self.logview.append(_("Scanning CAN"))
            scancan = True

        if msgBox.clickedButton() == kwpbutton:
            self.logview.append(_("Scanning KWP"))
            scankwp = True

        progressWidget = widgets.QWidget(None)
        progressLayout = widgets.QVBoxLayout()
        progressWidget.setLayout(progressLayout)
        self.progressstatus.setRange(0, self.ecu_scan.getNumAddr())
        self.progressstatus.setValue(0)

        self.ecu_scan.clear()
        if scancan:
            self.ecu_scan.scan(self.progressstatus, self.infostatus, None, self.canlinecombo.currentIndex())
        if scankwp:
            self.ecu_scan.scan_kwp(self.progressstatus, self.infostatus)

        self.treeview_ecu.clear()
        self.treeview_params.clear()
        self.ecunamemap = {}
        if self.paramview:
            self.paramview.init(None)

        for ecu in self.ecu_scan.ecus.keys():
            self.ecunamemap[ecu] = self.ecu_scan.ecus[ecu].name
            item = widgets.QListWidgetItem(ecu)
            if '.xml' in self.ecu_scan.ecus[ecu].href.lower():
                item.setForeground(core.Qt.yellow)
            else:
                item.setForeground(core.Qt.green)
            self.treeview_ecu.addItem(item)

        for ecu in self.ecu_scan.approximate_ecus.keys():
            self.ecunamemap[ecu] = self.ecu_scan.approximate_ecus[ecu].name
            item = widgets.QListWidgetItem(ecu)
            item.setForeground(core.Qt.red)
            self.treeview_ecu.addItem(item)

        self.progressstatus.setValue(0)

    def setConnected(self, on):
        if options.simulation_mode:
            self.connectedstatus.setStyleSheet("background-color : orange; color: black")
            self.connectedstatus.setText(_("EDITION MODE"))
            return
        if on:
            self.connectedstatus.setStyleSheet("background-color : green; color: black")
            self.connectedstatus.setText(_("CONNECTED"))
        else:
            self.connectedstatus.setStyleSheet("background-color : red; color: black")
            self.connectedstatus.setText(_("DISCONNECTED"))

    def saveEcus(self):
        filename_tuple = widgets.QFileDialog.getSaveFileName(self, _("Save vehicule (keep '.ecu' extension)"),
                                                    "./vehicles/mycar.ecu", "*.ecu")

        filename = str(filename_tuple[0])

        if filename == "":
            return        

        eculist = []
        numecus = self.treeview_ecu.count()
        for i in range(numecus):
            item = self.treeview_ecu.item(i)
            itemname = utf8(item.text())
            if itemname in self.ecunamemap:
                eculist.append((itemname, self.ecunamemap[itemname]))
            else:
                eculist.append((itemname, ""))

        jsonfile = open(filename, "w")
        jsonfile.write(json.dumps(eculist))
        jsonfile.close()

    def newEcu(self):
        filename_tuple = widgets.QFileDialog.getSaveFileName(self, _("Save ECU (keep '.json' extension)"), "./json/myecu.json",
                                                   "*.json")

        filename = str(filename_tuple[0])

        if filename == '':
            return

        basename = os.path.basename(utf8(filename))
        filename = os.path.join("./json", basename)
        ecufile = ecu.Ecu_file(None)
        layout = open(filename + ".layout", "w")
        layout.write('{"screens": {}, "categories":{"Category":[]} }')
        layout.close()

        targets = open(filename + ".targets", "w")
        targets.write('[]')
        targets.close()

        layout = open(filename, "w")
        layout.write(ecufile.dumpJson())
        layout.close()

        item = widgets.QListWidgetItem(basename)
        self.treeview_ecu.addItem(item)

    def saveEcu(self):
        if self.paramview:
            self.paramview.saveEcu()
        self.eculistwidget.init()
        self.eculistwidget.filterProject()

    def saveRecord(self):
        if not self.paramview:
            return

        filename_tuple = widgets.QFileDialog.getSaveFileName(self, _("Save record (keep '.txt' extension)"),
                                                   "./record.txt", "*.txt")
        filename = str(filename_tuple[0])

        self.paramview.export_record(filename)

    def openxml(self):
        filename_tuple = widgets.QFileDialog.getOpenFileName(self, "Open File", "./", "XML files (*.xml *.XML)")

        filename = str(filename_tuple[0])

        if filename == '':
            return

        self.set_param_file(filename, "", "", True)

    def loadEcu(self, name):
        vehicle_file = "vehicles/" + name + ".ecu"
        jsonfile = open(vehicle_file, "r")
        eculist = json.loads(jsonfile.read())
        jsonfile.close()

        self.treeview_ecu.clear()
        self.treeview_params.clear()
        if self.paramview:
            self.paramview.init(None)

        for ecu in eculist:
            item = widgets.QListWidgetItem(ecu[0])
            self.ecunamemap[ecu[0]] = ecu[1]
            self.treeview_ecu.addItem(item)

    def readDtc(self):
        if self.paramview:
            self.paramview.readDTC()

    def changeAutorefresh(self):
        options.auto_refresh = self.autorefresh.isChecked()
        self.refresh.setEnabled(not options.auto_refresh)

        if options.auto_refresh:
            if self.paramview:
                self.paramview.prepare_recording()
                self.paramview.updateDisplays(True)
        else:
            if self.paramview:
                self.logview.append("Recorded " + str(self.paramview.get_record_size()) + " entries")

    def refreshParams(self):
        if self.paramview:
            self.paramview.updateDisplays(True)

    def changeUserMode(self):
        options.promode = self.expert.isChecked()
        self.sdscombo.setEnabled(options.promode)

    def changeLogMode(self):
        options.log_all = self.log.isChecked()

    def readDTC(self):
        if self.paramview:
            self.paramview.readDTC()

    def changeScreen(self, index):
        item = self.treeview_params.model().itemData(index)

        screen = item[0]

        self.paramview.pagename = screen
        inited = self.paramview.init(screen, self.screenlogfile)
        self.diagaction.setEnabled(inited)
        self.hexinput.setEnabled(inited)
        self.cominput.setEnabled(inited)
        self.expert.setChecked(False)
        options.promode = False
        self.autorefresh.setChecked(False)
        options.auto_refresh = False
        self.refresh.setEnabled(True)

        if options.simulation_mode and self.paramview.layoutdict:
            if screen in self.paramview.layoutdict['screens']:
                self.buttonEditor.set_layout(self.paramview.layoutdict['screens'][screen])

        self.paramview.setRefreshTime(self.refreshtimebox.value())
        self.set_can_combo(self.paramview.ecurequestsparser.ecu_protocol)

    def closeEvent(self, event):
        if self.paramview:
            self.paramview.tester_timer.stop()
        self.snifferview.stopthread()
        super(Main_widget, self).closeEvent(event)
        try:
            del options.elm
        except:
            pass

    def changeECU(self, index):
        item = self.treeview_ecu.model().itemData(index)

        ecu_name = item[0]

        isxml = True

        ecu = None
        ecu_addr = "0"
        ecu_file = ecu_name
        if ecu_name in self.ecu_scan.ecus:
            ecu = self.ecu_scan.ecus[ecu_name]
        elif ecu_name in self.ecu_scan.approximate_ecus:
            ecu = self.ecu_scan.approximate_ecus[ecu_name]
        elif ecu_name in self.ecunamemap:
            name = self.ecunamemap[ecu_name]
            ecu = self.ecu_scan.ecu_database.getTarget(name)
        else:
            ecu = self.ecu_scan.ecu_database.getTarget(ecu_name)

        if ecu:
            if '.xml' not in ecu.href.lower():
                isxml = False
            ecu_file = options.ecus_dir + ecu.href
            ecu_addr = ecu.addr

        if self.snifferview.set_file(ecu_file):
            self.tabbedview.setCurrentIndex(2)
        else:
            if self.screenlogfile:
                self.screenlogfile.write("ECU : " + ecu.href + "\n")

        if self.paramview:
            if ecu_file == self.paramview.ddtfile:
                return
        self.set_param_file(ecu_file, ecu_addr, ecu_name, isxml)

    def set_param_file(self, ecu_file, ecu_addr, ecu_name, isxml):
        self.diagaction.setEnabled(True)
        self.hexinput.setEnabled(True)
        self.cominput.setEnabled(True)
        self.treeview_params.clear()

        uiscale_mem = 12

        if self.paramview:
            uiscale_mem = self.paramview.uiscale
            self.paramview.setParent(None)
            self.paramview.close()
            self.paramview.destroy()

        self.paramview = parameters.paramWidget(self.scrollview, ecu_file, ecu_addr, ecu_name, self.logview, self.protocolstatus, self.canlinecombo.currentIndex())
        self.paramview.infobox = self.infostatus
        if options.simulation_mode:
            self.requesteditor.set_ecu(self.paramview.ecurequestsparser)
            self.dataitemeditor.set_ecu(self.paramview.ecurequestsparser)
            self.buttonEditor.set_ecu(self.paramview.ecurequestsparser)
            self.ecuparameditor.set_ecu(self.paramview.ecurequestsparser)
            self.ecuparameditor.set_targets(self.paramview.targetsdata)
            if isxml:
                self.requesteditor.enable_view(False)
                self.dataitemeditor.enable_view(False)
                self.buttonEditor.enable_view(False)
                self.ecuparameditor.enable_view(False)

        self.paramview.uiscale = uiscale_mem

        self.scrollview.setWidget(self.paramview)
        screens = self.paramview.categories.keys()
        self.screennames = []
        for screen in screens:
            item = widgets.QTreeWidgetItem(self.treeview_params, [screen])
            for param in self.paramview.categories[screen]:
                param_item = widgets.QTreeWidgetItem(item, [param])
                param_item.setData(0, core.Qt.UserRole, param)
                self.screennames.append(param)


class donationWidget(widgets.QLabel):
    def __init__(self):
        super(donationWidget, self).__init__()
        img = gui.QPixmap("icons/donate.png")
        self.setPixmap(img)
        self.setAlignment(core.Qt.AlignCenter)
        self.setFrameStyle((widgets.QFrame.Panel | widgets.QFrame.StyledPanel))

    def mousePressEvent(self, mousevent):
        msgbox = widgets.QMessageBox()
        msgbox.setText(_("<center>This Software is free, but I need money to buy cables/ECUs and make this application more reliable</center>"))
        okbutton = widgets.QPushButton(_('Yes I contribute'))
        msgbox.addButton(okbutton, widgets.QMessageBox.YesRole)
        msgbox.addButton(widgets.QPushButton(_("No, I don't")), widgets.QMessageBox.NoRole)
        okbutton.clicked.connect(self.donate)
        msgbox.exec_()

    def donate(self):
        url = core.QUrl("https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=cedricpaille@gmail.com&lc=CY&item_name=codetronic&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG.if:NonHosted", core.QUrl.TolerantMode)
        gui.QDesktopServices().openUrl(url)
        msgbox = widgets.QMessageBox()
        msgbox.setText(_("<center>Thank you for you contribution, if nothing happens, please go to : https://github.com/cedricp/ddt4all</center>"))
        msgbox.exec_()

def set_dark_style(onoff):
    if (onoff):
        stylefile = core.QFile("qstyle.qss")
        stylefile.open(core.QFile.ReadOnly)

        StyleSheet = bytes(stylefile.readAll()).decode()
    else:
        StyleSheet = ""

    app.setStyleSheet(StyleSheet)

class portChooser(widgets.QDialog):
    def __init__(self):
        portSpeeds = [38400, 57600, 115200, 230400, 500000, 1000000]
        self.port = None
        self.ports = {}
        self.mode = 0
        self.securitycheck = False
        self.selectedportspeed = 38400
        self.adapter = "STD"
        self.raise_port_speed = "No"
        super(portChooser, self).__init__(None)
        layout = widgets.QVBoxLayout()
        label = widgets.QLabel(self)
        label.setText(_("ELM port selection"))
        label.setAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)
        donationwidget = donationWidget()
        self.setLayout(layout)
        
        self.listview = widgets.QListWidget(self)

        layout.addWidget(label)
        layout.addWidget(self.listview)

        medialayout = widgets.QHBoxLayout()
        self.usbbutton = widgets.QPushButton()
        self.usbbutton.setIcon(gui.QIcon("icons/usb.png"))
        self.usbbutton.setIconSize(core.QSize(60, 60))
        self.usbbutton.setFixedHeight(64)
        self.usbbutton.setFixedWidth(64)
        self.usbbutton.setCheckable(True)
        medialayout.addWidget(self.usbbutton)

        self.wifibutton = widgets.QPushButton()
        self.wifibutton.setIcon(gui.QIcon("icons/wifi.png"))
        self.wifibutton.setIconSize(core.QSize(60, 60))
        self.wifibutton.setFixedHeight(64)
        self.wifibutton.setFixedWidth(64)
        self.wifibutton.setCheckable(True)
        medialayout.addWidget(self.wifibutton)

        self.btbutton = widgets.QPushButton()
        self.btbutton.setIcon(gui.QIcon("icons/bt.png"))
        self.btbutton.setIconSize(core.QSize(60, 60))
        self.btbutton.setFixedHeight(64)
        self.btbutton.setFixedWidth(64)
        self.btbutton.setCheckable(True)
        medialayout.addWidget(self.btbutton)

        self.obdlinkbutton = widgets.QPushButton()
        self.obdlinkbutton.setIcon(gui.QIcon("icons/obdlink.png"))
        self.obdlinkbutton.setIconSize(core.QSize(60, 60))
        self.obdlinkbutton.setFixedHeight(64)
        self.obdlinkbutton.setFixedWidth(64)
        self.obdlinkbutton.setCheckable(True)
        medialayout.addWidget(self.obdlinkbutton)

        self.elsbutton = widgets.QPushButton()
        self.elsbutton.setIcon(gui.QIcon("icons/els27.png"))
        self.elsbutton.setIconSize(core.QSize(60, 60))
        self.elsbutton.setFixedHeight(64)
        self.elsbutton.setFixedWidth(64)
        self.elsbutton.setCheckable(True)
        medialayout.addWidget(self.elsbutton)

        layout.addLayout(medialayout)

        self.btbutton.toggled.connect(self.bt)
        self.wifibutton.toggled.connect(self.wifi)
        self.usbbutton.toggled.connect(self.usb)
        self.obdlinkbutton.toggled.connect(self.obdlink)
        self.elsbutton.toggled.connect(self.els)

        speedlayout = widgets.QHBoxLayout()
        self.speedcombo = widgets.QComboBox()
        speedlabel = widgets.QLabel(_("Port speed"))
        speedlayout.addWidget(speedlabel)
        speedlayout.addWidget(self.speedcombo)

        for s in portSpeeds:
            self.speedcombo.addItem(str(s))

        self.speedcombo.setCurrentIndex(0)

        layout.addLayout(speedlayout)

        button_layout = widgets.QHBoxLayout()
        button_con = widgets.QPushButton(_("Connected mode"))
        button_dmo = widgets.QPushButton(_("Edition mode"))
        button_elm_chk = widgets.QPushButton(_("ELM benchmark"))
        self.elmchk = button_elm_chk

        wifilayout = widgets.QHBoxLayout()
        wifilabel = widgets.QLabel(_("WiFi port : "))
        self.wifiinput = widgets.QLineEdit()
        self.wifiinput.setText("192.168.0.10:35000")
        wifilayout.addWidget(wifilabel)
        wifilayout.addWidget(self.wifiinput)
        layout.addLayout(wifilayout)

        safetychecklayout = widgets.QHBoxLayout()
        self.safetycheck = widgets.QCheckBox()
        self.safetycheck.setChecked(False)
        safetylabel = widgets.QLabel(_("I'm aware that I can harm my car if badly used"))
        safetychecklayout.addWidget(self.safetycheck)
        safetychecklayout.addWidget(safetylabel)
        safetychecklayout.addStretch()
        layout.addLayout(safetychecklayout)

        darkstylelayout = widgets.QHBoxLayout()
        self.darklayoutcheck = widgets.QCheckBox()
        self.darklayoutcheck.setChecked(False)
        self.darklayoutcheck.stateChanged.connect(set_dark_style)
        darkstylelabel = widgets.QLabel(_("Dark style"))
        darkstylelayout.addWidget(self.darklayoutcheck)
        darkstylelayout.addWidget(darkstylelabel)
        darkstylelayout.addStretch()
        layout.addLayout(darkstylelayout)

        obdlinkspeedlayout = widgets.QHBoxLayout()
        self.obdlinkspeedcombo = widgets.QComboBox()
        obdlinkspeedlabel = widgets.QLabel(_("Change UART speed"))
        obdlinkspeedlayout.addWidget(obdlinkspeedlabel)
        obdlinkspeedlayout.addWidget(self.obdlinkspeedcombo)
        obdlinkspeedlayout.addStretch()
        layout.addLayout(obdlinkspeedlayout)

        layout.addWidget(donationwidget)

        button_layout.addWidget(button_con)
        button_layout.addWidget(button_dmo)
        button_layout.addWidget(button_elm_chk)
        layout.addLayout(button_layout)

        self.logview = widgets.QTextEdit()
        layout.addWidget(self.logview)
        self.logview.hide()

        button_con.clicked.connect(self.connectedMode)
        button_dmo.clicked.connect(self.demoMode)
        button_elm_chk.clicked.connect(self.check_elm)

        self.timer = core.QTimer()
        self.timer.timeout.connect(self.rescan_ports)
        self.timer.start(500)
        self.portcount = -1
        self.usb()

        self.setWindowTitle("DDT4All")

    def check_elm(self):
        currentitem = self.listview.currentItem()
        self.logview.show()
        if self.wifibutton.isChecked():
            port = str(self.wifiinput.text())
        else:
            if not currentitem:
                self.logview.hide()
                return
            portinfo = currentitem.text()
            port = self.ports[portinfo][0]
        speed = int(self.speedcombo.currentText())
        res = elm.elm_checker(port, speed, self.logview, core.QCoreApplication)
        if not res:
            self.logview.append(options.get_last_error())

    def rescan_ports(self):
        ports = elm.get_available_ports()
        if ports == None:
            self.listview.clear()
            self.ports = {}
            self.portcount = 0
            return

        if len(ports) == self.portcount:
            return

        self.listview.clear()
        self.ports = {}
        self.portcount = len(ports)
        for p in ports:
            item = widgets.QListWidgetItem(self.listview)
            itemname = p[0] + "[" + p[1] + "]"
            item.setText(itemname)
            self.ports[itemname] = (p[0], p[1])

        self.timer.start(500)

    def bt(self):
        self.adapter = "STD_BT"
        self.obdlinkspeedcombo.clear()
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)

        self.speedcombo.setCurrentIndex(2)
        self.btbutton.setChecked(True)
        self.wifibutton.setChecked(False)
        self.usbbutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(True)
        self.obdlinkbutton.setChecked(False)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elmchk.setEnabled(True)

    def wifi(self):
        self.adapter = "STD_WIFI"
        self.obdlinkspeedcombo.clear()
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)

        self.wifibutton.setChecked(True)
        self.btbutton.setChecked(False)
        self.usbbutton.setChecked(False)
        self.wifiinput.setEnabled(True)
        self.speedcombo.setEnabled(False)
        self.obdlinkbutton.setChecked(False)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elmchk.setEnabled(True)

    def usb(self):
        self.adapter = "STD_USB"
        self.obdlinkspeedcombo.clear()
        self.obdlinkspeedcombo.addItem("No")
        self.obdlinkspeedcombo.addItem("57600")
        self.obdlinkspeedcombo.addItem("115200")
        self.obdlinkspeedcombo.addItem("230400")
        # This mode seems to not be supported by all adapters
        self.obdlinkspeedcombo.addItem("500000")
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)

        self.usbbutton.setChecked(True)
        self.speedcombo.setCurrentIndex(0)
        self.btbutton.setChecked(False)
        self.wifibutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(True)
        self.obdlinkbutton.setChecked(False)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elmchk.setEnabled(True)

    def obdlink(self):
        self.adapter = "OBDLINK"
        self.obdlinkspeedcombo.clear()
        self.obdlinkspeedcombo.addItem("No")
        self.obdlinkspeedcombo.addItem("500000")
        self.obdlinkspeedcombo.addItem("1000000")
        self.obdlinkspeedcombo.addItem("2000000")
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)

        self.usbbutton.setChecked(False)
        self.speedcombo.setCurrentIndex(2)
        self.btbutton.setChecked(False)
        self.wifibutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(True)
        self.obdlinkbutton.setChecked(True)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elmchk.setEnabled(False)

    def els(self):
        self.adapter = "ELS"
        self.obdlinkspeedcombo.clear()
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)

        self.usbbutton.setChecked(False)
        self.speedcombo.setCurrentIndex(2)
        self.btbutton.setChecked(False)
        self.wifibutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(True)
        self.obdlinkbutton.setChecked(True)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elmchk.setEnabled(False)

    def connectedMode(self):
        self.timer.stop()
        self.securitycheck = self.safetycheck.isChecked()
        self.selectedportspeed = int(self.speedcombo.currentText())
        if not pc.securitycheck:
            msgbox = widgets.QMessageBox()
            msgbox.setText(_("You must check the recommandations"))
            msgbox.exec_()
            return

        if self.wifibutton.isChecked():
            self.port = str(self.wifiinput.text())
            self.mode = 1
            self.done(True)
        else:
            currentitem = self.listview.currentItem()
            if currentitem:
                portinfo = utf8(currentitem.text())
                self.port = self.ports[portinfo][0]
                options.port_name = self.ports[portinfo][1]
                self.mode = 1
                self.raise_port_speed = self.obdlinkspeedcombo.currentText()
                self.done(True)
            else:
                msgbox = widgets.QMessageBox()
                msgbox.setText(_("Please select a communication port"))
                msgbox.exec_()

    def demoMode(self):
        self.timer.stop()
        self.securitycheck = self.safetycheck.isChecked()
        self.port = 'DUMMY'
        self.mode = 2
        options.report_data = False
        self.done(True)

if __name__ == '__main__':
    try:
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)
    except:
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

    options.simultation_mode = True
    app = widgets.QApplication(sys.argv)

    if sys.platform[:3] != "win":
        font = gui.QFont("Sans", 9)
        font.setBold(False)
        app.setFont(font)
        app.setStyle("plastic")

    ecudirfound = False
    if os.path.exists(options.ecus_dir + '/eculist.xml'):
        print(_("Using custom DDT database"))
        ecudirfound = True

    pc = portChooser()
    nok = True
    while nok:
        pcres = pc.exec_()

        if pc.mode == 0 or pcres == widgets.QDialog.Rejected:
            exit(0)
        if pc.mode == 1:
            options.promode = False
            options.simulation_mode = False
        if pc.mode == 2:
            options.promode = False
            options.simulation_mode = True
            break

        options.port = str(pc.port)
        port_speed = pc.selectedportspeed

        if not options.port:
            msgbox = widgets.QMessageBox()
            msgbox.setText(_("No COM port selected"))
            msgbox.exec_()

        print(_("Initilizing ELM with speed %i...") % port_speed)
        options.elm = elm.ELM(options.port, port_speed, pc.adapter, pc.raise_port_speed)
        if options.elm_failed:
            pc.show()
            pc.logview.append(options.get_last_error())
            msgbox = widgets.QMessageBox()
            msgbox.setText(_("No ELM327 or OBDLINK-SX detected on COM port ") + options.port)
            msgbox.exec_()
        else:
            nok = False

    w = Main_widget()
    options.main_window = w
    w.show()
    app.exec_()
