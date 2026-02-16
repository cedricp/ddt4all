#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import codecs
import errno
import glob
import locale
import os
import sys
import tempfile
from importlib.machinery import SourceFileLoader

import PyQt5.QtCore as core
import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

# Optional WebEngine import for enhanced features
try:
    import PyQt5.QtWebEngineWidgets as webkitwidgets
    HAS_WEBENGINE = True
except ImportError:
    print(_("Warning: PyQtWebEngine not available. Some features may be limited."))
    webkitwidgets = None
    HAS_WEBENGINE = False

import dataeditor
import ecu
import elm
import json
import options
import parameters
import sniffer
import version

_ = options.translator('ddt4all')
app = None

# remove Warning: Ignoring XDG_SESSION_TYPE=wayland on Gnome. Use QT_QPA_PLATFORM=wayland to run on Wayland anyway 
if sys.platform[:3] == "lin":
    os.environ["XDG_SESSION_TYPE"] = "xcb"


def load_this():
    try:
        with open("ddt4all_data/projects.json", "r", encoding="UTF-8") as f:
            vehicles_loc = json.loads(f.read())
        ecu.addressing = vehicles_loc["projects"]["All"]["addressing"]
        elm.snat = vehicles_loc["projects"]["All"]["snat"]
        elm.snat_ext = vehicles_loc["projects"]["All"]["snat_ext"]
        elm.dnat = vehicles_loc["projects"]["All"]["dnat"]
        elm.dnat_ext = vehicles_loc["projects"]["All"]["dnat_ext"]
        return vehicles_loc
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(_("ddt4all_data/projects.json not found or not ok.") + f" Error: {e}")
        exit(-1)


vehicles = load_this()

# args
parser = argparse.ArgumentParser()
parser.add_argument("-git_test", "--git_workfallowmode", action='store_true', help="Mode build test's")
args = parser.parse_args()
not_qt5_show = args.git_workfallowmode


def isWritable(path):
    try:
        testfile = tempfile.TemporaryFile(dir=path)
        testfile.close()
        return True
    except OSError as e:
        if e.errno == errno.EACCES:  # 13
            return False
        e.filename = path
        return False
    except Exception:
        return False


class Ecu_finder(widgets.QDialog):
    def __init__(self, ecuscanner):
        super(Ecu_finder, self).__init__()
        # Set window icon and title
        appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
        self.setWindowIcon(appIcon)
        self.setWindowTitle(_("ECU Finder"))
        self.ecuscanner = ecuscanner
        layoutv = widgets.QVBoxLayout()
        layouth = widgets.QHBoxLayout()
        self.setLayout(layoutv)
        layoutv.addLayout(layouth)
        self.ecuaddr = widgets.QLineEdit()
        self.ecuident = widgets.QLineEdit()
        layouth.addWidget(widgets.QLabel(_("Address :")))
        layouth.addWidget(self.ecuaddr)
        layouth.addWidget(widgets.QLabel(_("ID frame :")))
        layouth.addWidget(self.ecuident)
        button = widgets.QPushButton(_("VALIDATE"))
        layouth.addWidget(button)
        button.clicked.connect(self.check)

    def check(self):
        addr = self.ecuaddr.text()
        frame = self.ecuident.text()
        self.ecuscanner.identify_from_frame(addr, frame)


class Ecu_list(widgets.QWidget):
    def __init__(self, ecuscan, treeview_ecu):
        super(Ecu_list, self).__init__()
        self.selected = ''
        self.treeview_ecu = treeview_ecu
        self.vehicle_combo = widgets.QComboBox()
        self.ecuscan = ecuscan  # Store reference to ecuscan
        self.ecu_map = {}

        self.populateVehicleCombo()

        self.vehicle_combo.activated.connect(self.filterProject)

        layout = widgets.QVBoxLayout()
        layouth = widgets.QHBoxLayout()
        scanbutton = widgets.QPushButton()
        scanbutton.setIcon(gui.QIcon("ddt4all_data/icons/scan.png"))
        scanbutton.clicked.connect(self.scanselvehicle)
        layouth.addWidget(self.vehicle_combo)
        layouth.addWidget(scanbutton)
        layout.addLayout(layouth)
        self.setLayout(layout)
        self.list = widgets.QTreeWidget(self)
        self.list.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        layout.addWidget(self.list)
        self.ecuscan = ecuscan  # Store reference to ecuscan
        self.list.doubleClicked.connect(self.ecuSel)
        self.init()

    def populateVehicleCombo(self):
        """Populate vehicle combo box based on current sorting mode"""
        self.vehicle_combo.clear()
        
        # Check if vehicles database is available AND has ECUs
        if not vehicles or not vehicles.get("projects") or self.ecuscan.getNumEcuDb() == 0:
            # No database available - add placeholder item
            self.vehicle_combo.addItem(_("No vehicles available"))
            self.vehicle_combo.setEnabled(False)
            return
        
        # Get current sorting mode from configuration
        sort_mode = options.get_carlist_sort_mode()
        
        if sort_mode == "name":
            # Sort by car name (extract from project key)
            vehicle_items = []
            for project_key in vehicles["projects"].keys():
                if project_key == "All":
                    # Keep "All" as is
                    display_name = "All"
                else:
                    # Extract car name from project key
                    # Format: [CODE] - Car Name -> Display: Car Name - [CODE]
                    if " - " in project_key:
                        parts = project_key.split(" - ", 1)
                        code_part = parts[0]  # [CODE]
                        name_part = parts[1]  # Car Name
                        display_name = f"{name_part} - {code_part}"
                    else:
                        display_name = project_key
                
                vehicle_items.append((display_name, project_key))
            
            # Sort by display name
            vehicle_items.sort(key=lambda x: x[0])
            
            # Add to combo box
            for display_name, project_key in vehicle_items:
                self.vehicle_combo.addItem(display_name, project_key)
        else:
            # Sort by project code (default behavior)
            for k in sorted(vehicles["projects"].keys()):
                self.vehicle_combo.addItem(k, k)
        
        # Enable combo box only if we have vehicles
        self.vehicle_combo.setEnabled(True)

    def refreshVehicleList(self):
        """Refresh the vehicle combo box when sorting mode changes"""
        current_selection = self.vehicle_combo.currentText()
        current_data = self.vehicle_combo.currentData()
        
        self.populateVehicleCombo()
        
        # Try to restore previous selection
        if current_data:
            index = self.vehicle_combo.findData(current_data)
            if index >= 0:
                self.vehicle_combo.setCurrentIndex(index)
        elif current_selection:
            index = self.vehicle_combo.findText(current_selection)
            if index >= 0:
                self.vehicle_combo.setCurrentIndex(index)

    def scanselvehicle(self):
        # Check if vehicles database is available AND has ECUs
        if not vehicles or not vehicles.get("projects") or self.ecuscan.getNumEcuDb() == 0:
            return  # No database available, do nothing
        
        # Get project key (works for both sorting modes)
        project_key = self.vehicle_combo.currentData()
        if project_key is None:
            # Fallback to current text for backward compatibility
            project_key = self.vehicle_combo.currentText()
        
        # Skip if it's placeholder message
        if project_key == _("No vehicles available"):
            return
        
        project = str(vehicles["projects"][project_key]["code"])
        ecu.addressing = vehicles["projects"][project_key]["addressing"]
        elm.snat = vehicles["projects"][project_key]["snat"]
        elm.snat_ext = vehicles["projects"][project_key]["snat_ext"]
        elm.dnat = vehicles["projects"][project_key]["dnat"]
        elm.dnat_ext = vehicles["projects"][project_key]["dnat_ext"]
        self.parent().parent().scan_project(project)

    def init(self):
        self.list.clear()
        self.list.setSortingEnabled(True)
        self.list.setColumnCount(8)
        self.list.model().setHeaderData(0, core.Qt.Horizontal, _('ECU name'))
        self.list.model().setHeaderData(1, core.Qt.Horizontal, _('ID'))
        self.list.model().setHeaderData(2, core.Qt.Horizontal, _('Protocol'))
        self.list.model().setHeaderData(3, core.Qt.Horizontal, _('Supplier'))
        self.list.model().setHeaderData(4, core.Qt.Horizontal, _('Diag'))
        self.list.model().setHeaderData(5, core.Qt.Horizontal, _('Soft'))
        self.list.model().setHeaderData(6, core.Qt.Horizontal, _('Version'))
        self.list.model().setHeaderData(7, core.Qt.Horizontal, _('Projets'))
        self.list.sortByColumn(0, core.Qt.AscendingOrder)
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
            keys.sort(key=locale.strxfrm)
        except (locale.Error, AttributeError):
            keys.sort()
        for e in keys:
            item = widgets.QTreeWidgetItem(self.list, [e])
            if e in longgroupnames:
                item.setToolTip(0, longgroupnames[e])
            elif e in self.ecuscan.ecu_database.addr_group_mapping:
                item.setToolTip(0, self.ecuscan.ecu_database.addr_group_mapping[e])
            for t in stored_ecus[e]:
                widgets.QTreeWidgetItem(item, t)

        self.list.resizeColumnToContents(0)

    def filterProject(self):
        # Check if vehicles database is available AND has ECUs
        if not vehicles or not vehicles.get("projects") or self.ecuscan.getNumEcuDb() == 0:
            return  # No database available, do nothing
        
        # Get project key (works for both sorting modes)
        project_key = self.vehicle_combo.currentData()
        if project_key is None:
            # Fallback to current text for backward compatibility
            project_key = self.vehicle_combo.currentText()
        
        # Skip if it's placeholder message
        if project_key == _("No vehicles available"):
            return
        
        project = str(vehicles["projects"][project_key]["code"])
        ecu.addressing = vehicles["projects"][project_key]["addressing"]
        elm.snat = vehicles["projects"][project_key]["snat"]
        elm.snat_ext = vehicles["projects"][project_key]["snat_ext"]
        elm.dnat = vehicles["projects"][project_key]["dnat"]
        elm.dnat_ext = vehicles["projects"][project_key]["dnat_ext"]

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
    def __init__(self, parent=None):
        super(Main_widget, self).__init__(parent)
        self.setIcon()
        if not options.simulation_mode:
            if not os.path.exists("./logs"):
                os.mkdir("./logs")
            self.screenlogfile = open("./logs/screens.txt", "at", encoding="utf-8")
        else:
            self.screenlogfile = None

        self.plugins = {}
        self.carlist_sort_mode = "code"  # Default sorting by project code
        options.main_window = self  # Set reference for language switching
        self.setWindowTitle(version.__appname__ + " - Version: " + version.__version__ + " - Build status: " + version.__status__)
        self.ecu_scan = ecu.Ecu_scanner()
        self.ecu_scan.qapp = app
        options.socket_timeout = False
        options.ecu_scanner = self.ecu_scan
        print(_("%d loaded ECUs in database.") % self.ecu_scan.getNumEcuDb())
        if self.ecu_scan.getNumEcuDb() == 0:
            msgbox = widgets.QMessageBox()
            appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
            msgbox.setWindowIcon(appIcon)
            msgbox.setWindowTitle(version.__appname__)
            msgbox.setIcon(widgets.QMessageBox.Warning)
            msgbox.setText(_("No database found"))
            msgbox.setInformativeText(_("Check documentation"))
            msgbox.exec_()

        self.paramview = None
        
        # Initialize documentation view based on WebEngine availability
        if HAS_WEBENGINE:
            self.docview = webkitwidgets.QWebEngineView()
            self.docview.load(core.QUrl("https://github.com/cedricp/ddt4all/wiki"))
            
            # Configure WebEngine settings for optimal GitHub wiki experience
            settings = self.docview.settings()
            settings.setAttribute(webkitwidgets.QWebEngineSettings.JavascriptEnabled, False)  # Disabled to prevent compatibility errors
            settings.setAttribute(webkitwidgets.QWebEngineSettings.AutoLoadImages, True)     # Better visual experience
            settings.setAttribute(webkitwidgets.QWebEngineSettings.PluginsEnabled, False)    # Security: disable plugins
            settings.setAttribute(webkitwidgets.QWebEngineSettings.LocalStorageEnabled, False)  # Security: no local storage
            settings.setAttribute(webkitwidgets.QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)  # Security
        else:
            # Fallback to basic text widget for documentation
            self.docview = widgets.QTextEdit()
            self.docview.setReadOnly(True)
            self.docview.setHtml(f"""
            <h2>{_("DDT4All Documentation")}</h2>
            <p><strong>{_("WebEngine not available.")}</strong> {_("For full documentation with web browsing capability, install PyQtWebEngine:")}</p>
            <pre>pip install PyQtWebEngine</pre>
            <p>{_("Visit the online documentation at:")} <br>
            <a href="https://github.com/cedricp/ddt4all/wiki">https://github.com/cedricp/ddt4all/wiki</a></p>
            <p>{_("This basic view will still show ECU documentation when available.")}</p>
            """)

        self.screennames = []

        self.statusbar_widget = widgets.QStatusBar()
        self.setStatusBar(self.statusbar_widget)

        self.connectedstatus = widgets.QLabel()
        self.connectedstatus.setAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)
        self.protocolstatus = widgets.QLabel()
        self.progressstatus = widgets.QProgressBar()
        self.infostatus = widgets.QLabel()

        # Remove fixed widths to allow widgets to size properly
        self.connectedstatus.setMinimumWidth(120)
        self.connectedstatus.setSizePolicy(widgets.QSizePolicy.Preferred, widgets.QSizePolicy.Fixed)
        
        self.protocolstatus.setMinimumWidth(180)
        self.protocolstatus.setSizePolicy(widgets.QSizePolicy.Preferred, widgets.QSizePolicy.Fixed)
        
        self.progressstatus.setMinimumWidth(200)
        self.progressstatus.setMaximumHeight(20)
        self.progressstatus.setSizePolicy(widgets.QSizePolicy.Preferred, widgets.QSizePolicy.Fixed)
        
        self.infostatus.setMinimumWidth(200)
        self.infostatus.setSizePolicy(widgets.QSizePolicy.Expanding, widgets.QSizePolicy.Fixed)

        self.refreshtimebox = widgets.QSpinBox()
        self.refreshtimebox.setRange(5, 2000)
        self.refreshtimebox.setValue(options.refreshrate)
        self.refreshtimebox.setSingleStep(100)
        self.refreshtimebox.setMinimumWidth(60)
        self.refreshtimebox.setSizePolicy(widgets.QSizePolicy.Preferred, widgets.QSizePolicy.Fixed)
        self.refreshtimebox.valueChanged.connect(self.changeRefreshTime)
        refrestimelabel = widgets.QLabel(_("Refresh rate (ms):"))
        refrestimelabel.setSizePolicy(widgets.QSizePolicy.Preferred, widgets.QSizePolicy.Fixed)

        self.cantimeout = widgets.QSpinBox()
        self.cantimeout.setRange(0, 1000)
        self.cantimeout.setSingleStep(200)
        self.cantimeout.setValue(options.cantimeout)
        self.cantimeout.setMinimumWidth(60)
        self.cantimeout.setSizePolicy(widgets.QSizePolicy.Preferred, widgets.QSizePolicy.Fixed)
        self.cantimeout.valueChanged.connect(self.changeCanTimeout)
        cantimeoutlabel = widgets.QLabel(_("Can timeout (ms) [0:AUTO] :"))
        cantimeoutlabel.setSizePolicy(widgets.QSizePolicy.Preferred, widgets.QSizePolicy.Fixed)

        self.statusbar_widget.addWidget(self.connectedstatus)
        self.statusbar_widget.addWidget(self.protocolstatus)
        self.statusbar_widget.addWidget(self.progressstatus)
        self.statusbar_widget.addWidget(refrestimelabel)
        self.statusbar_widget.addWidget(self.refreshtimebox)
        self.statusbar_widget.addWidget(cantimeoutlabel)
        self.statusbar_widget.addWidget(self.cantimeout)
        self.statusbar_widget.addWidget(self.infostatus)

        self.tabbedview = widgets.QTabWidget()
        self.setCentralWidget(self.tabbedview)

        self.scrollview = widgets.QScrollArea()
        self.scrollview.setWidgetResizable(False)
        self.scrollview.setHorizontalScrollBarPolicy(core.Qt.ScrollBarAsNeeded)
        self.scrollview.setVerticalScrollBarPolicy(core.Qt.ScrollBarAsNeeded)

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
        self.treedock_widget.setWindowTitle(_("Ecran Window"))
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
        self.treedock_logs.setWindowTitle(_("Logs Window"))
        self.logview = widgets.QTextEdit()
        self.logview.setReadOnly(True)
        self.treedock_logs.setWidget(self.logview)

        self.treedock_ecu = widgets.QDockWidget(self)
        self.treedock_ecu.setWindowTitle(_("Ecu Window"))
        self.treeview_ecu = widgets.QListWidget(self.treedock_ecu)
        self.treedock_ecu.setWidget(self.treeview_ecu)
        self.treeview_ecu.clicked.connect(self.changeECU)
        
        self.ecunamemap = {}

        self.eculistwidget = Ecu_list(self.ecu_scan, self.treeview_ecu)
        self.treeview_eculist = widgets.QDockWidget(self)
        self.treeview_eculist.setWindowTitle(_("Ecu List Window"))
        self.treeview_eculist.setWidget(self.eculistwidget)

        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treeview_eculist)
        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treedock_ecu)
        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treedock_widget)
        self.addDockWidget(core.Qt.BottomDockWidgetArea, self.treedock_logs)

        self.toolbar = self.addToolBar(_("ToolBar"))

        self.diagaction = widgets.QAction(gui.QIcon("ddt4all_data/icons/dtc.png"), _("Read DTC"), self)
        self.diagaction.triggered.connect(self.readDtc)
        self.diagaction.setEnabled(False)

        self.log = widgets.QAction(gui.QIcon("ddt4all_data/icons/log.png"), _("Full log"), self)
        self.log.setCheckable(True)
        self.log.setChecked(options.log_all)
        self.log.triggered.connect(self.changeLogMode)
        if options.dark_mode:
            self.expert = widgets.QAction(gui.QIcon("ddt4all_data/icons/expert-b.png"), _("Expert mode (enable writing)"), self)
        else:
            self.expert = widgets.QAction(gui.QIcon("ddt4all_data/icons/expert.png"), _("Expert mode (enable writing)"), self)
        self.expert.setCheckable(True)
        self.expert.setChecked(options.promode)
        self.expert.triggered.connect(self.changeUserMode)

        self.autorefresh = widgets.QAction(gui.QIcon("ddt4all_data/icons/autorefresh.png"), _("Auto refresh"), self)
        self.autorefresh.setCheckable(True)
        self.autorefresh.setChecked(options.auto_refresh)
        self.autorefresh.triggered.connect(self.changeAutorefresh)

        self.refresh = widgets.QAction(gui.QIcon("ddt4all_data/icons/refresh.png"), _("Refresh (one shot)"), self)
        self.refresh.triggered.connect(self.refreshParams)
        self.refresh.setEnabled(not options.auto_refresh)

        self.hexinput = widgets.QAction(gui.QIcon("ddt4all_data/icons/hex.png"), _("Manual command"), self)
        self.hexinput.triggered.connect(self.hexeditor)
        self.hexinput.setEnabled(False)

        self.cominput = widgets.QAction(gui.QIcon("ddt4all_data/icons/command.png"), _("Manual request"), self)
        self.cominput.triggered.connect(self.command_editor)
        self.cominput.setEnabled(False)

        self.fctrigger = widgets.QAction(gui.QIcon("ddt4all_data/icons/flowcontrol.png"), _("Software flow control"), self)
        self.fctrigger.setCheckable(True)
        self.fctrigger.triggered.connect(self.flow_control)

        self.canlinecombo = widgets.QComboBox()
        self.canlinecombo.setMinimumWidth(120)
        self.canlinecombo.setSizePolicy(widgets.QSizePolicy.Preferred, widgets.QSizePolicy.Fixed)

        self.sdscombo = widgets.QComboBox()
        self.sdscombo.setMinimumWidth(250)
        self.sdscombo.setSizePolicy(widgets.QSizePolicy.Expanding, widgets.QSizePolicy.Fixed)
        self.sdscombo.currentIndexChanged.connect(self.changeSds)
        self.sdscombo.setEnabled(False)

        self.zoominbutton = widgets.QPushButton(_("Zoom In"))
        self.zoomoutbutton = widgets.QPushButton(_("Zoom Out"))
        self.zoominbutton.clicked.connect(self.zoomin)
        self.zoomoutbutton.clicked.connect(self.zoomout)

        self.toolbar.addSeparator()
        self.toolbar.addAction(self.log)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.expert)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.autorefresh)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.refresh)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.diagaction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.hexinput)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.cominput)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.fctrigger)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.canlinecombo)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.sdscombo)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.zoominbutton)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.zoomoutbutton)

        if options.simulation_mode:
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
        closeAllThis = diagmenu.addAction(_("Exit"))
        closeAllThis.triggered.connect(self.exit_all)
        diagmenu.addSeparator()

        for ecuf in ecu_files:
            ecuaction = diagmenu.addAction(ecuf)
            ecuaction.triggered.connect(lambda state, a=ecuf: self.loadEcu(a))

        self.screenmenu = menu.addMenu(_("Screens"))

        # View menu
        view_menu = menu.addMenu(_("View"))
        carlist_order_menu = view_menu.addMenu(_("CarList Order"))
        
        self.carlist_order_by_code = widgets.QAction(_("By Project Code"), carlist_order_menu)
        self.carlist_order_by_code.setCheckable(True)
        self.carlist_order_by_code.setChecked(options.get_carlist_sort_mode() == "code")
        self.carlist_order_by_code.triggered.connect(self.setCarListOrderCode)
        carlist_order_menu.addAction(self.carlist_order_by_code)
        
        self.carlist_order_by_name = widgets.QAction(_("By Car Name"), carlist_order_menu)
        self.carlist_order_by_name.setCheckable(True)
        self.carlist_order_by_name.setChecked(options.get_carlist_sort_mode() == "name")
        self.carlist_order_by_name.triggered.connect(self.setCarListOrderName)
        carlist_order_menu.addAction(self.carlist_order_by_name)
        
        # Make actions mutually exclusive
        self.carlist_order_group = widgets.QActionGroup(self)
        self.carlist_order_group.addAction(self.carlist_order_by_code)
        self.carlist_order_group.addAction(self.carlist_order_by_name)

        # Theme menu (moved under View menu) with explicit Dark/Light selection
        theme_menu = view_menu.addMenu(_("Theme"))

        theme_dark_action = widgets.QAction(_("Dark Theme"), theme_menu)
        theme_dark_action.setCheckable(True)
        theme_light_action = widgets.QAction(_("Light Theme"), theme_menu)
        theme_light_action.setCheckable(True)

        # Group theme actions so only one can be active
        theme_action_group = widgets.QActionGroup(self)
        theme_action_group.addAction(theme_dark_action)
        theme_action_group.addAction(theme_light_action)
        theme_action_group.setExclusive(True)

        # Set initial checked state
        if options.dark_mode:
            theme_dark_action.setChecked(True)
        else:
            theme_light_action.setChecked(True)

        # Connect actions to set the theme explicitly
        theme_dark_action.triggered.connect(lambda checked: set_theme_style(2))
        theme_light_action.triggered.connect(lambda checked: set_theme_style(0))

        theme_menu.addAction(theme_dark_action)
        theme_menu.addAction(theme_light_action)

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

                # if options.simulation_mode and need_hw:
                #    continue

                if not category in category_menus:
                    category_menus[category] = plugins_menu.addMenu(category)

                plug_action = category_menus[category].addAction(name)
                plug_action.triggered.connect(lambda state, a=plug.plugin_entry: self.launchPlugin(a))

                self.plugins[modulename] = plug
            except Exception as e:
                print(_("Cannot load plugin ") + plugin)
                print(e)

        # Help menu
        help_menu = menu.addMenu(_("Help"))
        wiki_about = help_menu.addAction(_("Web Wiki"))
        wiki_about.triggered.connect(self.wiki_about)
        help_menu.addSeparator()
        devs = help_menu.addMenu(_("About Developers"))
        about_cedric = devs.addAction("Cedric PAILLE")
        about_cedric.triggered.connect(self.about_cedric)
        about_furtif = devs.addAction("--=FurtiF™=--")
        about_furtif.triggered.connect(self.about_furtif)
        help_menu.addSeparator()
        githubupdate = help_menu.addAction(_("Get Git update"))
        githubupdate.triggered.connect(self.git_update)
        help_menu.addSeparator()
        about_content = help_menu.addAction(_("About"))
        about_content.triggered.connect(self.about_content_msg)

        self.setConnected(True)
        self.tabbedview.setCurrentIndex(1)
        self.showMaximized()

    def about_content_msg(self):
        msgbox = widgets.QMessageBox()
        appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
        msgbox.setWindowIcon(appIcon)
        msgbox.setIcon(widgets.QMessageBox.Information)
        msgbox.setWindowTitle(_("About DDT4ALL"))
        text_about = version.__appname__ + _(" version:") + " %s" % version.__version__
        msgbox.setText(text_about)
        html = '<h2>' + _("Created by:") + " %s" % (version.__author__) + '</h2><table>'
        for name, role in version.__contributors__.items():
            html += f'<tr><td><a href="https://github.com/{name}" style="text-decoration: none; cursor: pointer;" target="_blank">{name}</a>: </td><td>{role}</td></tr>'
        html += '</table>'
        msgbox.setInformativeText(html)
        msgbox.exec_()

    def setCarListOrderCode(self):
        """Set CarList sorting to by project code"""
        options.set_carlist_sort_mode("code")
        self.carlist_order_by_code.setChecked(True)
        self.carlist_order_by_name.setChecked(False)
        # Refresh the vehicle combo box
        self.eculistwidget.refreshVehicleList()

    def setCarListOrderName(self):
        """Set CarList sorting to by car name"""
        options.set_carlist_sort_mode("name")
        self.carlist_order_by_name.setChecked(True)
        self.carlist_order_by_code.setChecked(False)
        # Refresh the vehicle combo box
        self.eculistwidget.refreshVehicleList()

    def wiki_about(self):
        url = core.QUrl("https://github.com/cedricp/ddt4all/wiki", core.QUrl.TolerantMode)
        gui.QDesktopServices().openUrl(url)

    def about_cedric(self):
        url = core.QUrl("https://github.com/cedricp", core.QUrl.TolerantMode)
        gui.QDesktopServices().openUrl(url)

    def about_furtif(self):
        url = core.QUrl("https://github.com/Furtif", core.QUrl.TolerantMode)
        gui.QDesktopServices().openUrl(url)

    def git_update(self):
        url = core.QUrl("https://github.com/cedricp/ddt4all/releases", core.QUrl.TolerantMode)
        gui.QDesktopServices().openUrl(url)

    def setIcon(self):
        appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
        self.setWindowIcon(appIcon)

    def updateMenuBar(self):
        """Update menu bar texts after language change"""
        try:
            # Update menu titles - find menus by object name or recreate
            menu_bar = self.menuBar()
            for action in menu_bar.actions():
                menu = action.menu()
                if menu:
                    # Update menu titles based on current translation
                    if "File" in action.text() or _("File") in action.text():
                        menu.setTitle(_("File"))
                    elif "Screens" in action.text() or _("Screens") in action.text():
                        menu.setTitle(_("Screens"))
                    elif "View" in action.text() or _("View") in action.text():
                        menu.setTitle(_("View"))
                    elif "Options" in action.text() or _("Options") in action.text():
                        menu.setTitle(_("Options"))
                    elif "Plugins" in action.text() or _("Plugins") in action.text():
                        menu.setTitle(_("Plugins"))
                    elif "Help" in action.text() or _("Help") in action.text():
                        menu.setTitle(_("Help"))
            
            # Update vehicle list with new language
            if hasattr(self, 'eculistwidget') and self.eculistwidget:
                self.eculistwidget.refreshVehicleList()
            
        except Exception as e:
            print(f"Error updating menu bar: {e}")
            
    def toggle_theme(self):
        """Toggle theme between light and dark"""
        new_theme = not options.dark_mode
        set_theme_style(2 if new_theme else 0)
        
    def show_options_dialog(self):
        """Show options dialog for device settings"""
        options_dialog = main_window_options()
        options_dialog.exec_()

    def set_can_combo(self, bus):
        self.canlinecombo.clear()
        try:
            self.canlinecombo.clicked.disconnect()
        except Exception:
            pass
        if bus == "CAN":
            self.canlinecombo.addItem(_("CAN Line 1 Auto"))
            self.canlinecombo.addItem(_("CAN Line 1@500K"))
            self.canlinecombo.addItem(_("CAN Line 1@250K"))
            if options.elm is not None and options.elm.adapter_type == "ELS":
                self.canlinecombo.addItem(_("CAN Line 2@500K"))
                self.canlinecombo.addItem(_("CAN Line 2@250K"))
                self.canlinecombo.addItem(_("CAN Line 2@125K"))
            self.canlinecombo.currentIndexChanged.connect(self.changecanspeed)
        else:
            if bus == "KWP2000":
                self.canlinecombo.addItem(_("KWP2000"))
            if bus == "ISO8":
                self.canlinecombo.addItem(_("ISO8"))

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

    def exit_all(self):
        self.close()
        exit(0)

    def zipdb(self):
        filename_tuple = widgets.QFileDialog.getSaveFileName(self, _("Save database (keep '.zip' extension)"),
                                                             "./ecu.zip", "*.zip")

        filename = str(filename_tuple[0])

        if not filename.endswith(".zip"):
            filename += ".zip"

        if not isWritable(str(os.path.dirname(filename))):
            mbox = widgets.QMessageBox()
            appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
            mbox.setWindowIcon(appIcon)
            mbox.setWindowTitle(version.__appname__)
            mbox.setText("Cannot write to directory " + os.path.dirname(filename))
            mbox.exec_()
            return

        self.logview.append(_("Zipping XML database... (this can take a few minutes)"))
        core.QCoreApplication.processEvents()
        parameters.zipConvertXML(filename)
        self.logview.append(_("Zip job finished"))

    def launchPlugin(self, pim):
        if self.paramview:
            self.paramview.init('')
        if self.ecu_scan.getNumEcuDb() == 0:
            msgbox = widgets.QMessageBox()
            appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
            msgbox.setWindowIcon(appIcon)
            msgbox.setWindowTitle(version.__appname__)
            msgbox.setIcon(widgets.QMessageBox.Warning)
            msgbox.setText(_("No database found"))
            msgbox.setInformativeText(_("Check documentation"))
            msgbox.exec_()
            return
        pim()
        if self.paramview:
            self.paramview.initELM()

    def screenRename(self):
        item = self.treeview_params.currentItem()
        if not item:
            return

        itemname = item.text(0)
        nin = widgets.QInputDialog.getText(self, 'DDT4All', _('Enter new name'))

        if not nin[1]:
            return

        newitemname = nin[0]

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
        necatname = ncn[0]
        if necatname:
            if self.ecu_scan.getNumEcuDb() == 0:
                msgbox = widgets.QMessageBox()
                appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
                msgbox.setWindowIcon(appIcon)
                msgbox.setWindowTitle(version.__appname__)
                msgbox.setIcon(widgets.QMessageBox.Warning)
                msgbox.setText(_("No database found"))
                msgbox.setInformativeText(_("Check documentation"))
                msgbox.exec_()
                return
            self.paramview.createCategory(necatname)
            self.treeview_params.addTopLevelItem(widgets.QTreeWidgetItem([necatname]))

    def newScreen(self):
        item = self.treeview_params.currentItem()

        if not item:
            self.logview.append(
                "<font color=red>" + _("Please select a category before creating new screen") + "</font>")
            return

        if item.parent() is not None:
            item = item.parent()

        category = item.text(0)
        nsn = widgets.QInputDialog.getText(self, 'DDT4All', _('Enter screen name'))

        if not nsn[1]:
            return

        newscreenname = nsn[0]
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
        self.logview.append(_("Scanning CAN") + " -> " + project)
        self.ecu_scan.scan(self.progressstatus, self.infostatus, project)
        self.logview.append(_("Scanning KWP") + " -> " + project)
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
            item.setForeground(core.Qt.blue)
            self.treeview_ecu.addItem(item)

        self.progressstatus.setValue(0)

    def scan(self):
        msgBox = widgets.QMessageBox()
        appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
        msgBox.setWindowIcon(appIcon)
        msgBox.setWindowTitle(version.__appname__)
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
            item.setForeground(core.Qt.blue)
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
            itemname = item.text()
            if itemname in self.ecunamemap:
                eculist.append((itemname, self.ecunamemap[itemname]))
            else:
                eculist.append((itemname, ""))

        jsonfile = open(filename, "w")
        jsonfile.write(json.dumps(eculist))
        jsonfile.close()

    def newEcu(self):
        filename_tuple = widgets.QFileDialog.getSaveFileName(self, _("Save ECU (keep '.json' extension)"),
                                                             "./json/myecu.json",
                                                             "*.json")

        filename = str(filename_tuple[0])

        if filename == '':
            return

        basename = os.path.basename(filename)
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
                self.logview.append(_("Recorded ") + str(self.paramview.get_record_size()) + _(" entries"))

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
        
        # Adjust screen width to use full viewport width while preserving vertical scrolling
        if inited and hasattr(self.paramview, 'panel') and self.paramview.panel:
            viewport_width = self.scrollview.viewport().width()
            if viewport_width > self.paramview.panel.screen_width:
                self.paramview.panel.screen_width = viewport_width
                self.paramview.panel.resize(self.paramview.panel.screen_width, self.paramview.panel.screen_height)
                self.paramview.resize(self.paramview.panel.screen_width + 50, self.paramview.panel.screen_height + 50)
        
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
        except AttributeError:
            pass
    
    def resizeEvent(self, event):
        """Handle window resize to adjust screen widths while preserving vertical scrolling"""
        super(Main_widget, self).resizeEvent(event)
        
        # Adjust screen width when window is resized
        if hasattr(self, 'paramview') and self.paramview and hasattr(self.paramview, 'panel') and self.paramview.panel:
            viewport_width = self.scrollview.viewport().width()
            if viewport_width > self.paramview.panel.screen_width:
                self.paramview.panel.screen_width = viewport_width
                self.paramview.panel.resize(self.paramview.panel.screen_width, self.paramview.panel.screen_height)
                self.paramview.resize(self.paramview.panel.screen_width + 50, self.paramview.panel.screen_height + 50)

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

        self.paramview = parameters.paramWidget(self.scrollview, ecu_file, ecu_addr, ecu_name, self.logview,
                                                self.protocolstatus, self.canlinecombo.currentIndex())
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
        
        # Adjust screen width to use full viewport width while preserving vertical scrolling
        if hasattr(self.paramview, 'panel') and self.paramview.panel:
            viewport_width = self.scrollview.viewport().width()
            if viewport_width > self.paramview.panel.screen_width:
                self.paramview.panel.screen_width = viewport_width
                self.paramview.panel.resize(self.paramview.panel.screen_width, self.paramview.panel.screen_height)
                self.paramview.resize(self.paramview.panel.screen_width + 50, self.paramview.panel.screen_height + 50)
        
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
        img = gui.QPixmap("ddt4all_data/icons/donate.png")
        self.setPixmap(img)
        self.setAlignment(core.Qt.AlignCenter)
        self.setFrameStyle((widgets.QFrame.Panel | widgets.QFrame.StyledPanel))

    def mousePressEvent(self, mousevent):
        msgbox = widgets.QMessageBox()
        appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
        msgbox.setWindowIcon(appIcon)
        msgbox.setWindowTitle(version.__appname__)
        msgbox.setText(
            _("<center>This Software is free, but I need money to buy cables/ECUs and make this application more reliable</center>"))
        okbutton = widgets.QPushButton(_('Yes I contribute'))
        msgbox.addButton(okbutton, widgets.QMessageBox.YesRole)
        msgbox.addButton(widgets.QPushButton(_("No, I don't")), widgets.QMessageBox.NoRole)
        okbutton.clicked.connect(self.donate)
        msgbox.exec_()

    def donate(self):
        url = core.QUrl(
            "https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=cedricpaille@gmail.com&lc=CY&item_name=codetronic&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG.if:NonHosted",
            core.QUrl.TolerantMode)
        gui.QDesktopServices().openUrl(url)
        msgbox = widgets.QMessageBox()
        msgbox.setWindowTitle(version.__appname__)
        appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
        msgbox.setWindowIcon(appIcon)
        translate_arg = _("Thank you for you contribution, if nothing happens, please go to")
        msgbox.setText("<center>" + translate_arg + ": https://github.com/cedricp/ddt4all</center>")
        msgbox.exec_()


def set_theme_style(onoff):
    global app
    if (onoff):
        stylefile = core.QFile("ddt4all_data/qstyle-d.qss")
        options.dark_mode = True
        stylefile.open(core.QFile.ReadOnly)
        StyleSheet = bytes(stylefile.readAll()).decode()
    else:
        stylefile = core.QFile("ddt4all_data/qstyle.qss")
        stylefile.open(core.QFile.ReadOnly)
        options.dark_mode = False
        StyleSheet = bytes(stylefile.readAll()).decode()

    # Apply platform-specific font size and font family adjustments
    if sys.platform == "darwin":
        # macOS: keep 14pt for better readability with .AppleSystemUIFont
        # Remove Windows-specific "Segoe UI" font to avoid 276ms lookup delay
        StyleSheet = StyleSheet.replace(
            '".AppleSystemUIFont", "Segoe UI", "Helvetica Neue",',
            '".AppleSystemUIFont", "Helvetica Neue",'
        )
    else:
        # Windows/Linux: revert to 10pt for proper sizing
        StyleSheet = StyleSheet.replace("font-size: 14pt;", "font-size: 10pt;")

    app.setStyleSheet(StyleSheet)
    options.configuration["dark"] = options.dark_mode
    options.save_config()


def set_language_realtime(language_name):
    """Change language in real-time without restart"""
    global _
    
    if language_name in options.lang_list:
        lang_code = options.lang_list[language_name]
        
        # Update environment and configuration
        os.environ['LANG'] = lang_code
        options.configuration["lang"] = lang_code
        options.save_config()
        
        # Reload translator
        import gettext
        try:
            t = gettext.translation('ddt4all', 'ddt4all_data/locale', languages=[lang_code], fallback=True)
            _ = t.gettext
            
            # Update main window if it exists
            if hasattr(options, 'main_window') and options.main_window:
                main_window = options.main_window
                # Update menu bar
                main_window.updateMenuBar()
                # Update status bar using the widget directly
                if hasattr(main_window, 'statusbar_widget') and main_window.statusbar_widget:
                    main_window.statusbar_widget.showMessage(_("Language changed to") + " " + language_name, 3000)
            
            print(f"Language changed to {language_name} ({lang_code})")
            return True
        except Exception as e:
            print(f"Error changing language: {e}")
            return False
    return False

def set_socket_timeout(onoff):
    if (onoff):
        options.socket_timeout = True
    else:
        options.socket_timeout = False

    options.configuration["socket_timeout"] = options.socket_timeout
    options.save_config()

class main_window_options(widgets.QDialog):
    def __init__(self):
        portSpeeds = [38400, 57600, 115200, 230400, 500000, 1000000]
        self.port = None
        self.ports = {}
        self.mode = 0
        self.securitycheck = False
        self.selectedportspeed = 38400
        self.adapter = "STD"
        self.raise_port_speed = _("No")
        super(main_window_options, self).__init__(None)
        # Set window icon and title
        appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
        self.setWindowIcon(appIcon)
        self.setWindowTitle(_("Options"))
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
        self.usbbutton.setIcon(gui.QIcon("ddt4all_data/icons/usb.png"))
        self.usbbutton.setIconSize(core.QSize(60, 60))
        self.usbbutton.setFixedHeight(64)
        self.usbbutton.setFixedWidth(64)
        self.usbbutton.setCheckable(True)
        self.usbbutton.setToolTip(_("USB"))
        medialayout.addWidget(self.usbbutton)

        self.wifibutton = widgets.QPushButton()
        self.wifibutton.setIcon(gui.QIcon("ddt4all_data/icons/wifi.png"))
        self.wifibutton.setIconSize(core.QSize(60, 60))
        self.wifibutton.setFixedHeight(64)
        self.wifibutton.setFixedWidth(64)
        self.wifibutton.setCheckable(True)
        self.wifibutton.setToolTip(_("WiFi"))
        medialayout.addWidget(self.wifibutton)

        self.btbutton = widgets.QPushButton()
        self.btbutton.setIcon(gui.QIcon("ddt4all_data/icons/bt.png"))
        self.btbutton.setIconSize(core.QSize(60, 60))
        self.btbutton.setFixedHeight(64)
        self.btbutton.setFixedWidth(64)
        self.btbutton.setCheckable(True)
        self.btbutton.setToolTip(_("Bluetooth"))
        medialayout.addWidget(self.btbutton)

        self.obdlinkbutton = widgets.QPushButton()
        self.obdlinkbutton.setIcon(gui.QIcon("ddt4all_data/icons/obdlink.png"))
        self.obdlinkbutton.setIconSize(core.QSize(60, 60))
        self.obdlinkbutton.setFixedHeight(64)
        self.obdlinkbutton.setFixedWidth(64)
        self.obdlinkbutton.setCheckable(True)
        self.obdlinkbutton.setToolTip(_("OBDLINK SX/EX"))
        medialayout.addWidget(self.obdlinkbutton)

        self.elsbutton = widgets.QPushButton()
        self.elsbutton.setIcon(gui.QIcon("ddt4all_data/icons/els27.png"))
        self.elsbutton.setIconSize(core.QSize(60, 60))
        self.elsbutton.setFixedHeight(64)
        self.elsbutton.setFixedWidth(64)
        self.elsbutton.setCheckable(True)
        self.elsbutton.setToolTip(_("ELS27/ELS27 V5 - May appear as FTDI/CH340/CP210x device"))
        medialayout.addWidget(self.elsbutton)

        self.vlinkerbutton = widgets.QPushButton()
        self.vlinkerbutton.setIcon(gui.QIcon("ddt4all_data/icons/vlinker.png"))
        self.vlinkerbutton.setIconSize(core.QSize(60, 60))
        self.vlinkerbutton.setFixedHeight(64)
        self.vlinkerbutton.setFixedWidth(64)
        self.vlinkerbutton.setCheckable(True)
        self.vlinkerbutton.setToolTip(_("Vlinker FS/MC"))
        medialayout.addWidget(self.vlinkerbutton)

        self.derelekbutton = widgets.QPushButton()
        self.derelekbutton.setIcon(gui.QIcon("ddt4all_data/icons/derelek.png"))
        self.derelekbutton.setIconSize(core.QSize(60, 60))
        self.derelekbutton.setFixedHeight(64)
        self.derelekbutton.setFixedWidth(64)
        self.derelekbutton.setCheckable(True)
        self.derelekbutton.setToolTip(_("DERLEK USB-DIAG2/3"))
        medialayout.addWidget(self.derelekbutton)

        self.vgatebutton = widgets.QPushButton()
        self.vgatebutton.setIcon(gui.QIcon("ddt4all_data/icons/vgate.png"))
        self.vgatebutton.setIconSize(core.QSize(60, 60))
        self.vgatebutton.setFixedHeight(64)
        self.vgatebutton.setFixedWidth(64)
        self.vgatebutton.setCheckable(True)
        self.vgatebutton.setToolTip(_("VGate (High-Speed)"))
        medialayout.addWidget(self.vgatebutton)

        self.doipbutton = widgets.QPushButton()
        self.doipbutton.setIcon(gui.QIcon("ddt4all_data/icons/doip.png"))
        self.doipbutton.setIconSize(core.QSize(60, 60))
        self.doipbutton.setFixedHeight(64)
        self.doipbutton.setFixedWidth(64)
        self.doipbutton.setCheckable(True)
        self.doipbutton.setToolTip(_("DoIP (Diagnostics over IP)"))
        medialayout.addWidget(self.doipbutton)

        layout.addLayout(medialayout)

        self.btbutton.toggled.connect(self.bt)
        self.wifibutton.toggled.connect(self.wifi)
        self.usbbutton.toggled.connect(self.usb)
        self.obdlinkbutton.toggled.connect(self.obdlink)
        self.elsbutton.toggled.connect(self.els)
        self.vlinkerbutton.toggled.connect(self.vlinker)
        self.derelekbutton.toggled.connect(self.derelek)
        self.vgatebutton.toggled.connect(self.vgate)
        self.doipbutton.toggled.connect(self.doip)

        # languages setting
        if "LANG" not in os.environ.keys():
            os.environ["LANG"] = "en_US"
        langlayout = widgets.QHBoxLayout()
        self.langcombo = widgets.QComboBox()
        langlabels = widgets.QLabel(_("Interface language"))
        langlayout.addWidget(langlabels)
        langlayout.addWidget(self.langcombo)
        for s in options.lang_list:
            self.langcombo.addItem(s)
            if options.lang_list[s].split("_")[0] == os.environ['LANG'].split("_")[0]:
                self.langcombo.setCurrentText(s)
        
        # Connect to real-time language switching
        self.langcombo.currentTextChanged.connect(self.change_language_realtime)
        
        layout.addLayout(langlayout)
        #

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
        button_save = widgets.QPushButton(_("Close"))

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
        self.darklayoutcheck.setChecked(options.dark_mode)
        self.darklayoutcheck.stateChanged.connect(set_theme_style)
        darkstylelabel = widgets.QLabel(_("Dark style"))
        darkstylelayout.addWidget(self.darklayoutcheck)
        darkstylelayout.addWidget(darkstylelabel)
        darkstylelayout.addStretch()
        layout.addLayout(darkstylelayout)

        socket_timeoutlayout = widgets.QHBoxLayout()
        self.socket_timeoutcheck = widgets.QCheckBox()
        self.socket_timeoutcheck.setChecked(options.socket_timeout)
        self.socket_timeoutcheck.stateChanged.connect(set_socket_timeout)
        socket_timeoutlabel = widgets.QLabel("WiFi Socket-TimeOut")
        socket_timeoutlayout.addWidget(self.socket_timeoutcheck)
        socket_timeoutlayout.addWidget(socket_timeoutlabel)
        socket_timeoutlayout.addStretch()
        layout.addLayout(socket_timeoutlayout)

        # DoIP configuration section
        doip_grouplayout = widgets.QVBoxLayout()
        doip_groupbox = widgets.QGroupBox(_("DoIP (Diagnostics over IP) Configuration"))
        doip_groupbox.setLayout(doip_grouplayout)
        
        # DoIP Preset Configuration
        doip_presetlayout = widgets.QHBoxLayout()
        doip_presetlabel = widgets.QLabel(_("Device Preset : "))
        self.doip_presetcombo = widgets.QComboBox()
        self.doip_presetcombo.addItem(_("Custom"))
        self.doip_presetcombo.addItem(_("Bosch MTS"))
        self.doip_presetcombo.addItem(_("VXDIAG VCX Nano"))
        self.doip_presetcombo.addItem(_("VAG ODIS"))
        self.doip_presetcombo.addItem(_("JLR DoIP VCI"))
        self.doip_presetcombo.addItem(_("Generic DoIP"))
        
        # Set current preset from saved configuration
        saved_preset = getattr(options, 'doip_preset', 'Custom')
        index = self.doip_presetcombo.findText(saved_preset)
        if index >= 0:
            self.doip_presetcombo.setCurrentIndex(index)
        
        self.doip_presetcombo.currentTextChanged.connect(self.apply_doip_preset)
        doip_presetlayout.addWidget(doip_presetlabel)
        doip_presetlayout.addWidget(self.doip_presetcombo)
        doip_presetlayout.addStretch()
        doip_grouplayout.addLayout(doip_presetlayout)
        
        # DoIP IP Address configuration
        doip_iplayout = widgets.QHBoxLayout()
        doip_iplabel = widgets.QLabel(_("DoIP Target IP : "))
        self.doip_ipinput = widgets.QLineEdit()
        self.doip_ipinput.setText(getattr(options, 'doip_target_ip', '192.168.0.12'))
        doip_iplayout.addWidget(doip_iplabel)
        doip_iplayout.addWidget(self.doip_ipinput)
        doip_grouplayout.addLayout(doip_iplayout)
        
        # DoIP Port configuration
        doip_portlayout = widgets.QHBoxLayout()
        doip_portlabel = widgets.QLabel(_("DoIP Port : "))
        self.doip_portinput = widgets.QSpinBox()
        self.doip_portinput.setRange(1, 65535)
        self.doip_portinput.setValue(getattr(options, 'doip_target_port', 13400))
        doip_portlayout.addWidget(doip_portlabel)
        doip_portlayout.addWidget(self.doip_portinput)
        doip_portlayout.addStretch()
        doip_grouplayout.addLayout(doip_portlayout)
        
        # DoIP Timeout configuration
        doip_timeoutlayout = widgets.QHBoxLayout()
        doip_timeoutlabel = widgets.QLabel(_("DoIP Timeout (seconds) : "))
        self.doip_timeoutinput = widgets.QSpinBox()
        self.doip_timeoutinput.setRange(1, 60)
        self.doip_timeoutinput.setValue(getattr(options, 'doip_timeout', 5))
        doip_timeoutlayout.addWidget(doip_timeoutlabel)
        doip_timeoutlayout.addWidget(self.doip_timeoutinput)
        doip_timeoutlayout.addStretch()
        doip_grouplayout.addLayout(doip_timeoutlayout)
        
        # DoIP Vehicle Announcement
        doip_announcelayout = widgets.QHBoxLayout()
        self.doip_announcecheck = widgets.QCheckBox()
        self.doip_announcecheck.setChecked(getattr(options, 'doip_vehicle_announcement', True))
        doip_announcelabel = widgets.QLabel(_("Enable Vehicle Announcement Discovery"))
        doip_announcelayout.addWidget(self.doip_announcecheck)
        doip_announcelayout.addWidget(doip_announcelabel)
        doip_announcelayout.addStretch()
        doip_grouplayout.addLayout(doip_announcelayout)
        
        # DoIP Auto-reconnect
        doip_reconnectlayout = widgets.QHBoxLayout()
        self.doip_reconnectcheck = widgets.QCheckBox()
        self.doip_reconnectcheck.setChecked(getattr(options, 'doip_auto_reconnect', False))
        doip_reconnectlabel = widgets.QLabel(_("Auto-reconnect on connection loss"))
        doip_reconnectlayout.addWidget(self.doip_reconnectcheck)
        doip_reconnectlayout.addWidget(doip_reconnectlabel)
        doip_reconnectlayout.addStretch()
        doip_grouplayout.addLayout(doip_reconnectlayout)
        
        layout.addWidget(doip_groupbox)

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
        button_layout.addWidget(button_save)
        button_layout.addWidget(button_elm_chk)
        layout.addLayout(button_layout)

        self.logview = widgets.QTextEdit()
        layout.addWidget(self.logview)
        self.logview.hide()

        button_con.clicked.connect(self.connectedMode)
        button_dmo.clicked.connect(self.demoMode)
        button_save.clicked.connect(self.save_config)
        button_elm_chk.clicked.connect(self.check_elm)

        self.timer = core.QTimer()
        self.timer.timeout.connect(self.rescan_ports)
        self.timer.start(500)
        self.portcount = -1
        self.usb()
        self.setWindowTitle(version.__appname__ + " - Version: " + version.__version__ + " - Build status: " + version.__status__)

    def save_config(self):
        # Save configuration (language is already saved by real-time switching)
        options.configuration["dark"] = options.dark_mode
        options.configuration["socket_timeout"] = options.socket_timeout
        
        # Save DoIP configuration
        options.doip_target_ip = self.doip_ipinput.text()
        options.doip_target_port = self.doip_portinput.value()
        options.doip_timeout = self.doip_timeoutinput.value()
        options.doip_vehicle_announcement = self.doip_announcecheck.isChecked()
        options.doip_auto_reconnect = self.doip_reconnectcheck.isChecked()
        options.doip_preset = self.doip_presetcombo.currentText()
        
        options.configuration["doip_target_ip"] = options.doip_target_ip
        options.configuration["doip_target_port"] = options.doip_target_port
        options.configuration["doip_timeout"] = options.doip_timeout
        options.configuration["doip_vehicle_announcement"] = options.doip_vehicle_announcement
        options.configuration["doip_auto_reconnect"] = options.doip_auto_reconnect
        options.configuration["doip_preset"] = options.doip_preset
        
        options.save_config()
        self.close()  # Just close dialog, don't exit app

    def change_language_realtime(self, language_name):
        """Handle real-time language change from combo box"""
        set_language_realtime(language_name)
        # Language change is now real-time, no message box needed

    def check_elm(self):
        """Enhanced ELM connection checker with better error handling"""
        self.elmchk.setEnabled(False)
        self.elmchk.setText(_("Checking..."))
        currentitem = self.listview.currentItem()
        self.logview.show()
        self.logview.clear()
        options.simulation_mode = False
        
        try:
            if self.wifibutton.isChecked():
                port = str(self.wifiinput.text()).strip()
                if not port:
                    self.logview.append(_("Please enter WiFi adapter IP address"))
                    return
                # Validate IP:port format
                import re
                if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$", port):
                    self.logview.append(_("Invalid WiFi format. Use IP:PORT (e.g., 192.168.0.10:35000)"))
                    return
            else:
                if not currentitem:
                    self.logview.append(_("Please select a serial port"))
                    self.logview.hide()
                    return
                portinfo = currentitem.text()
                if portinfo not in self.ports:
                    self.logview.append(_("Selected port is no longer available"))
                    return
                port = self.ports[portinfo][0]

            speed = int(self.speedcombo.currentText())
            
            # Show connection attempt
            self.logview.append(_("Attempting connection..."))
            self.logview.append(_("Port: ") + str(port))
            self.logview.append(_("Speed: ") + str(speed))
            
            # Process events to update UI
            core.QCoreApplication.processEvents()
            
            res = elm.elm_checker(port, speed, self.adapter, self.logview, core.QCoreApplication) 
            if not res:
                error_msg = options.get_last_error()
                if error_msg:
                    self.logview.append(_("Connection failed: ") + error_msg)
                else:
                    self.logview.append(_("Connection test failed"))
                    
                # Suggest troubleshooting steps
                self.logview.append("")
                self.logview.append(_("Troubleshooting suggestions:"))
                self.logview.append(_("1. Check device is properly connected"))
                self.logview.append(_("2. Try different baud rates"))
                self.logview.append(_("3. Ensure device drivers are installed"))
                if not self.wifibutton.isChecked():
                    self.logview.append(_("4. Check port permissions (Linux/macOS)"))
            else:
                self.logview.append("")
                self.logview.append(_("Connection test successful!"))
                self.logview.append(_("Checking port speed:") + " " + str(options.port_speed))
                
        except Exception as e:
            self.logview.append(_("Error during connection test: ") + str(e))
        finally:
            self.elmchk.setText(_("Reset and Recheck"))
            self.elmchk.setEnabled(True)
            
    def rescan_ports(self):
        """Enhanced port rescanning with device identification"""
        try:
            ports = elm.get_available_ports()
            if ports is None:
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
                if len(p) >= 4:
                    port, desc, hwid, status = p
                elif len(p) >= 3:
                    port, desc, hwid = p
                    status = "unknown"
                else:
                    port, desc = p
                    hwid = ""
                    status = "unknown"
                
                # Use port description as-is
                item = widgets.QListWidgetItem(self.listview)
                itemname = f"{port}[{desc}]"
                item.setText(itemname)
                self.ports[itemname] = (port, desc, hwid, status)
                
                # Set color based on status (optimized for dark theme)
                if status == "online":
                    item.setBackground(gui.QColor(50, 150, 50))  # Dark green background
                elif status == "offline":
                    item.setBackground(gui.QColor(150, 50, 50))  # Dark red background
                else:
                    item.setBackground(gui.QColor(100, 100, 100))  # Dark gray background
                
                # Highlight potential OBD devices based on description
                desc_lower = desc.lower()
                if any(keyword in desc_lower for keyword in ['elm327', 'elm', 'obd', 'vlinker', 'obdlink', 'els27', 'doip']):
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    
            # Auto-select first OBD device if available
            if self.listview.count() > 0 and not self.listview.currentItem():
                # Prioritize known OBD devices
                for i in range(self.listview.count()):
                    item = self.listview.item(i)
                    if any(device in item.text().upper() for device in ['ELM', 'OBD', 'VLINKER', 'OBDLINK']):
                        self.listview.setCurrentItem(item)
                        break
                else:
                    # If no known OBD device, select first item
                    self.listview.setCurrentItem(self.listview.item(0))

            self.timer.start(500)
            
        except Exception as e:
            print(f"Error rescanning ports: {e}")
            self.timer.start(500)

    def bt(self):
        self.adapter = "STD_BT"
        self.obdlinkspeedcombo.clear()
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)
        self.elsbutton.blockSignals(True)
        self.vlinkerbutton.blockSignals(True)
        self.derelekbutton.blockSignals(True)

        self.speedcombo.setCurrentIndex(2)
        self.btbutton.setChecked(True)
        self.wifibutton.setChecked(False)
        self.usbbutton.setChecked(False)
        self.obdlinkbutton.setChecked(False)
        self.elsbutton.setChecked(False)
        self.vlinkerbutton.setChecked(False)
        self.derelekbutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(True)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elsbutton.blockSignals(False)
        self.vlinkerbutton.blockSignals(False)
        self.derelekbutton.blockSignals(False)
        # self.elmchk.setEnabled(True)

    def wifi(self):
        self.adapter = "STD_WIFI"
        self.obdlinkspeedcombo.clear()
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)
        self.elsbutton.blockSignals(True)
        self.vlinkerbutton.blockSignals(True)
        self.derelekbutton.blockSignals(True)

        self.wifibutton.setChecked(True)
        self.btbutton.setChecked(False)
        self.usbbutton.setChecked(False)
        self.obdlinkbutton.setChecked(False)
        self.elsbutton.setChecked(False)
        self.vlinkerbutton.setChecked(False)
        self.derelekbutton.setChecked(False)
        self.wifiinput.setEnabled(True)
        self.speedcombo.setEnabled(False)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elsbutton.blockSignals(False)
        self.vlinkerbutton.blockSignals(False)
        self.derelekbutton.blockSignals(False)
        # self.elmchk.setEnabled(True)

    def usb(self):
        self.adapter = "STD_USB"
        self.obdlinkspeedcombo.clear()
        self.obdlinkspeedcombo.addItem(_("No"))
        self.obdlinkspeedcombo.addItem(_("57600"))
        self.obdlinkspeedcombo.addItem(_("115200"))
        self.obdlinkspeedcombo.addItem(_("230400"))
        # This mode seems to not be supported by all adapters
        self.obdlinkspeedcombo.addItem(_("500000"))
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)
        self.elsbutton.blockSignals(True)
        self.vlinkerbutton.blockSignals(True)
        self.derelekbutton.blockSignals(True)

        self.usbbutton.setChecked(True)
        self.speedcombo.setCurrentIndex(0)
        self.btbutton.setChecked(False)
        self.wifibutton.setChecked(False)
        self.obdlinkbutton.setChecked(False)
        self.elsbutton.setChecked(False)
        self.vlinkerbutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(True)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elsbutton.blockSignals(False)
        self.vlinkerbutton.blockSignals(False)
        self.derelekbutton.blockSignals(False)
        # self.elmchk.setEnabled(True)

    def obdlink(self):
        self.adapter = "OBDLINK"
        self.obdlinkspeedcombo.clear()
        self.obdlinkspeedcombo.addItem(_("No"))
        self.obdlinkspeedcombo.addItem(_("500000"))
        self.obdlinkspeedcombo.addItem(_("1000000"))
        self.obdlinkspeedcombo.addItem(_("2000000"))
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)
        self.elsbutton.blockSignals(True)
        self.vlinkerbutton.blockSignals(True)
        self.derelekbutton.blockSignals(True)

        self.usbbutton.setChecked(False)
        self.speedcombo.setCurrentIndex(2)  # 115200 baud for OBDLINK
        self.btbutton.setChecked(False)
        self.wifibutton.setChecked(False)
        self.elsbutton.setChecked(False)
        self.vlinkerbutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(True)
        self.obdlinkbutton.setChecked(True)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elsbutton.blockSignals(False)
        self.vlinkerbutton.blockSignals(False)
        self.derelekbutton.blockSignals(False)
        # self.elmchk.setEnabled(False)

    def els(self):
        self.adapter = "ELS27"
        self.obdlinkspeedcombo.clear()
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)
        self.vlinkerbutton.blockSignals(True)

        self.usbbutton.setChecked(False)
        self.speedcombo.setCurrentIndex(0)  # 38400 baud for ELS27
        self.btbutton.setChecked(False)
        self.wifibutton.setChecked(False)
        self.obdlinkbutton.setChecked(False)
        self.vlinkerbutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(True)
        self.elsbutton.setChecked(True)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.vlinkerbutton.blockSignals(False)
        # self.elmchk.setEnabled(False)

    def vlinker(self):
        self.adapter = "VLINKER"
        self.obdlinkspeedcombo.clear()
        self.obdlinkspeedcombo.addItem(_("No"))
        self.obdlinkspeedcombo.addItem(_("57600"))
        self.obdlinkspeedcombo.addItem(_("115200"))  # Vlinker can handle moderate speeds
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)
        self.elsbutton.blockSignals(True)
        self.derelekbutton.blockSignals(True)
        self.vgatebutton.blockSignals(True)

        self.usbbutton.setChecked(False)
        self.speedcombo.setCurrentIndex(0)  # 38400 baud for Vlinker
        self.btbutton.setChecked(False)
        self.wifibutton.setChecked(False)
        self.obdlinkbutton.setChecked(False)
        self.elsbutton.setChecked(False)
        self.derelekbutton.setChecked(False)
        self.vgatebutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(True)
        self.vlinkerbutton.setChecked(True)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elsbutton.blockSignals(False)
        self.derelekbutton.blockSignals(False)
        self.vgatebutton.blockSignals(False)

    def derelek(self):
        self.adapter = "DERLEK"
        self.obdlinkspeedcombo.clear()
        self.obdlinkspeedcombo.addItem(_("No"))
        self.obdlinkspeedcombo.addItem(_("38400"))
        self.obdlinkspeedcombo.addItem(_("115200"))  # DERLEK can handle high speeds (optional)
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)
        self.elsbutton.blockSignals(True)
        self.vlinkerbutton.blockSignals(True)
        self.derelekbutton.blockSignals(True)
        self.vgatebutton.blockSignals(True)

        self.usbbutton.setChecked(False)
        self.speedcombo.setCurrentIndex(0)  # 38400 baud for DERLEK
        self.btbutton.setChecked(False)
        self.wifibutton.setChecked(False)
        self.obdlinkbutton.setChecked(False)
        self.elsbutton.setChecked(False)
        self.vlinkerbutton.setChecked(False)
        self.vgatebutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(True)
        self.derelekbutton.setChecked(True)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elsbutton.blockSignals(False)
        self.obdlinkspeedcombo.addItem(_("500000"))
        self.obdlinkspeedcombo.addItem(_("1000000"))  # VGate can handle very high speeds
        
        # Display STPX support information
        self.logview.append(_("VGate iCar Pro selected - Enhanced STN/STPX support enabled"))
        self.logview.append(_("Long command support and high-speed communication available"))
        
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)
        self.elsbutton.blockSignals(True)
        self.vlinkerbutton.blockSignals(True)
        self.derelekbutton.blockSignals(True)

        self.usbbutton.setChecked(False)
        self.speedcombo.setCurrentIndex(2)  # 115200 baud for VGate (high speed)
        self.btbutton.setChecked(False)
        self.wifibutton.setChecked(False)
        self.obdlinkbutton.setChecked(False)
        self.elsbutton.setChecked(False)
        self.vlinkerbutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(True)
        self.vgatebutton.setChecked(True)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elsbutton.blockSignals(False)
        self.vlinkerbutton.blockSignals(False)
        self.derelekbutton.blockSignals(False)
        # self.elmchk.setEnabled(False)

    def vgate(self):
        self.adapter = "VGATE"
        self.obdlinkspeedcombo.clear()
        self.obdlinkspeedcombo.addItem(_("No"))
        self.obdlinkspeedcombo.addItem(_("115200"))
        self.obdlinkspeedcombo.addItem(_("230400"))
        self.obdlinkspeedcombo.addItem(_("500000"))
        self.obdlinkspeedcombo.addItem(_("1000000"))  # VGate can handle very high speeds
        
        # Display STPX support information
        self.logview.append(_("VGate iCar Pro selected - Enhanced STN/STPX support enabled"))
        self.logview.append(_("Long command support and high-speed communication available"))
        
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)
        self.elsbutton.blockSignals(True)
        self.vlinkerbutton.blockSignals(True)
        self.derelekbutton.blockSignals(True)

        self.usbbutton.setChecked(False)
        self.speedcombo.setCurrentIndex(2)  # 115200 baud for VGate (high speed)
        self.btbutton.setChecked(False)
        self.wifibutton.setChecked(False)
        self.obdlinkbutton.setChecked(False)
        self.elsbutton.setChecked(False)
        self.vlinkerbutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(True)
        self.vgatebutton.setChecked(True)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elsbutton.blockSignals(False)
        self.vlinkerbutton.blockSignals(False)
        self.derelekbutton.blockSignals(False)
        # self.elmchk.setEnabled(False)

    def apply_doip_preset(self, preset_name):
        """Apply DoIP device preset configurations"""
        presets = {
            _("Bosch MTS"): {
                "ip": "192.168.0.100",
                "port": 13400,
                "timeout": 10,
                "announcement": True,
                "auto_reconnect": True
            },
            _("VXDIAG VCX Nano"): {
                "ip": "192.168.0.200",
                "port": 13400,
                "timeout": 8,
                "announcement": True,
                "auto_reconnect": False
            },
            _("VAG ODIS"): {
                "ip": "192.168.0.10",
                "port": 13400,
                "timeout": 5,
                "announcement": True,
                "auto_reconnect": True
            },
            _("JLR DoIP VCI"): {
                "ip": "192.168.0.50",
                "port": 13400,
                "timeout": 7,
                "announcement": True,
                "auto_reconnect": True
            },
            _("Generic DoIP"): {
                "ip": "192.168.0.12",
                "port": 13400,
                "timeout": 5,
                "announcement": True,
                "auto_reconnect": False
            }
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            self.doip_ipinput.setText(preset["ip"])
            self.doip_portinput.setValue(preset["port"])
            self.doip_timeoutinput.setValue(preset["timeout"])
            self.doip_announcecheck.setChecked(preset["announcement"])
            self.doip_reconnectcheck.setChecked(preset["auto_reconnect"])
            
            # Log the preset application
            self.logview.append(f"Applied {preset_name} preset:")
            self.logview.append(f"  IP: {preset['ip']}")
            self.logview.append(f"  Port: {preset['port']}")
            self.logview.append(f"  Timeout: {preset['timeout']}s")

    def doip(self):
        self.adapter = "DOIP"
        self.obdlinkspeedcombo.clear()
        self.obdlinkspeedcombo.addItem(_("N/A"))  # DoIP doesn't use UART speeds
        
        # Display DoIP support information
        self.logview.append(_("DoIP (Diagnostics over IP) selected"))
        self.logview.append(_("Ethernet-based diagnostic communication"))
        self.logview.append(_("Compatible with Bosch MTS, VXDIAG, VAG ODIS, JLR DoIP VCI"))
        
        self.wifibutton.blockSignals(True)
        self.btbutton.blockSignals(True)
        self.usbbutton.blockSignals(True)
        self.obdlinkbutton.blockSignals(True)
        self.elsbutton.blockSignals(True)
        self.vlinkerbutton.blockSignals(True)
        self.derelekbutton.blockSignals(True)
        self.vgatebutton.blockSignals(True)

        self.usbbutton.setChecked(False)
        self.btbutton.setChecked(False)
        self.wifibutton.setChecked(False)
        self.obdlinkbutton.setChecked(False)
        self.elsbutton.setChecked(False)
        self.vlinkerbutton.setChecked(False)
        self.vgatebutton.setChecked(False)
        self.wifiinput.setEnabled(False)
        self.speedcombo.setEnabled(False)  # DoIP doesn't use serial port speeds
        self.doipbutton.setChecked(True)

        self.wifibutton.blockSignals(False)
        self.btbutton.blockSignals(False)
        self.usbbutton.blockSignals(False)
        self.obdlinkbutton.blockSignals(False)
        self.elsbutton.blockSignals(False)
        self.vlinkerbutton.blockSignals(False)
        self.derelekbutton.blockSignals(False)
        self.vgatebutton.blockSignals(False)
        # self.elmchk.setEnabled(False)

    def connectedMode(self):
        self.timer.stop()
        self.securitycheck = self.safetycheck.isChecked()
        self.selectedportspeed = int(self.speedcombo.currentText())
        if not pc.securitycheck:
            msgbox = widgets.QMessageBox()
            appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
            msgbox.setWindowIcon(appIcon)
            msgbox.setWindowTitle(version.__appname__)
            msgbox.setText(_("You must check the recommandations"))
            msgbox.exec_()
            return

        options.simulation_mode = False

        if self.wifibutton.isChecked():
            self.port = str(self.wifiinput.text())
            self.mode = 1
            self.done(True)
        else:
            currentitem = self.listview.currentItem()
            if currentitem:
                portinfo = currentitem.text()
                port_data = self.ports[portinfo]
                self.port = port_data[0]
                options.port_name = port_data[1]
                self.mode = 1
                self.raise_port_speed = self.obdlinkspeedcombo.currentText()
                self.done(True)
            else:
                msgbox = widgets.QMessageBox()
                appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
                msgbox.setWindowIcon(appIcon)
                msgbox.setWindowTitle(version.__appname__)
                msgbox.setText(_("Please select a communication port"))
                msgbox.exec_()

    def demoMode(self):
        self.timer.stop()
        self.securitycheck = self.safetycheck.isChecked()
        self.port = 'DUMMY'
        self.mode = 2
        options.report_data = False
        options.simulation_mode = True
        self.done(True)


if __name__ == '__main__':
    # For InnoSetup version.h auto generator
    if os.path.isdir('ddt4all_data/inno-win-setup'):
        try:
            with open("ddt4all_data/inno-win-setup/version.h", "w", encoding="UTF-8") as f:
                f.write(f'#define __appname__ "{version.__appname__}"\n')
                f.write(f'#define __author__ "{version.__author__}"\n')
                f.write(f'#define __copyright__ "{version.__copyright__}"\n')
                f.write(f'#define __version__ "{version.__version__}"\n')
                f.write(f'#define __email__ "{version.__email__}"\n')
                f.write(f'#define __status__ "{version.__status__}"')
        except (OSError, IOError) as e:
            print(f"Warning: Could not write version.h: {e}")
            
    if not_qt5_show:
        exit(0)
    try:
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)
    except (OSError, ValueError):
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

    options.simulation_mode = True
    options.socket_timeout = False
    app = widgets.QApplication(sys.argv)

    try:
        with open("ddt4all_data/config.json", "r", encoding="UTF-8") as f:
            configuration = json.loads(f.read())
        if configuration["dark"]:
            set_theme_style(2)
        else:
            set_theme_style(0)
        if configuration["socket_timeout"]:
            set_socket_timeout(1)
        else:
            set_socket_timeout(0)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        set_theme_style(0)

    app.setStyle("plastic")

    ecudirfound = False
    if os.path.exists(options.ecus_dir + '/eculist.xml'):
        print(_("Using custom DDT database"))
        ecudirfound = True

    if not os.path.exists("./json"):
        os.mkdir("./json")

    if not os.path.exists("./logs"):
        os.mkdir("./logs")

    pc = main_window_options()
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
            appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
            msgbox.setWindowIcon(appIcon)
            msgbox.setWindowTitle(version.__appname__)
            msgbox.setText(_("No COM port selected"))
            msgbox.exec_()

        print(_("Initilizing ELM with speed %i...") % port_speed)
        options.elm = elm.ELM(options.port, port_speed, pc.adapter, pc.raise_port_speed)
        if options.elm_failed:
            pc.show()
            pc.logview.append(options.get_last_error())
            msgbox = widgets.QMessageBox()
            appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
            msgbox.setWindowIcon(appIcon)
            msgbox.setWindowTitle(version.__appname__)
            msgbox.setText(_("No ELM327 or OBDLINK-SX detected on COM port ") + options.port)
            msgbox.exec_()
        else:
            nok = False

    w = Main_widget()
    options.main_window = w
    w.show()
    app.exec_()

