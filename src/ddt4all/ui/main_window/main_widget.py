import glob
from importlib.machinery import SourceFileLoader
import json
import os
from pathlib import Path

import PyQt5.QtCore as core
import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

import ddt4all.options as options
from ddt4all.core.ecu.ecu_file import EcuFile
from ddt4all.core.ecu.ecu_scanner import EcuScanner
from ddt4all.file_manager import (
    get_logs_dir,
    get_vehicles_dir,
    is_not_package_file
)
from ddt4all.ui.data_editor.button_editor import ButtonEditor
from ddt4all.ui.data_editor.request_editor import RequestEditor
from ddt4all.ui.data_editor.ecu_param_editor import EcuParamEditor
from ddt4all.ui.data_editor.data_editor import DataEditor
from ddt4all.ui.parameters.utils import zipConvertXML
from ddt4all.ui.main_window.ecu_finder import EcuFinder
from ddt4all.ui.main_window.ecu_list import EcuList
from ddt4all.ui.main_window.icons_paths import (
    ICON_OBD,
    ICON_DTC,
    ICON_LOG,
    ICON_EXPERT,
    ICON_EXPERT_B,
    ICON_AUTOREFRESH,
    ICON_REFRESH,
    ICON_HEX,
    ICON_COMMAND,
    ICON_FLOWCONTROL,
)
from ddt4all.ui.main_window.main_window_options import MainWindowOptions
from ddt4all.ui.main_window.utils import (
    isWritable,
    set_theme_style
)
from ddt4all.ui.parameters.param_widget import ParamWidget
from ddt4all.ui.sniffer.sniffer import Sniffer
import ddt4all.version as version

_ = options.translator('ddt4all')

# Optional WebEngine import for enhanced features
try:
    import PyQt5.QtWebEngineWidgets as webkitwidgets
    HAS_WEBENGINE = True
except ImportError:
    print(_("Warning: PyQtWebEngine not available. Some features may be limited."))
    webkitwidgets = None
    HAS_WEBENGINE = False

BASE_DIR = Path(__file__).resolve().parent
plugins_base_dir = BASE_DIR / ".." / ".." / "plugins"

class MainWidget(widgets.QMainWindow):
    def __init__(self, app, vehicles, parent=None):
        super(MainWidget, self).__init__(parent)
        self.setIcon()
        if not options.simulation_mode:
            if not os.path.exists(get_logs_dir()):
                os.mkdir(get_logs_dir())
            self.screenlogfile = open(get_logs_dir() / "screens.txt", "at", encoding="utf-8")
        else:
            self.screenlogfile = None

        self.app = app
        self.vehicles = vehicles
        self.plugins = {}
        self.carlist_sort_mode = "code"  # Default sorting by project code
        options.main_window = self  # Set reference for language switching
        self.setWindowTitle(version.__appname__ + " - Version: " + version.__version__ + " - Build status: " + version.__status__)
        self.ecu_scan = EcuScanner()
        self.ecu_scan.qapp = app
        options.socket_timeout = False
        options.ecu_scanner = self.ecu_scan
        print(_("%d loaded ECUs in database.") % self.ecu_scan.getNumEcuDb())
        if self.ecu_scan.getNumEcuDb() == 0:
            msgbox = widgets.QMessageBox()
            appIcon = gui.QIcon(ICON_OBD)
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

        self.snifferview = Sniffer()

        self.tabbedview.addTab(self.docview, _("Documentation"))
        self.tabbedview.addTab(self.scrollview, _("Screen"))
        self.tabbedview.addTab(self.snifferview, _("CAN Sniffer"))

        if options.simulation_mode:
            self.buttonEditor = ButtonEditor()
            self.requesteditor = RequestEditor()
            self.dataitemeditor = DataEditor()
            self.ecuparameditor = EcuParamEditor()
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

        self.eculistwidget = EcuList(self.ecu_scan, self.treeview_ecu, self.vehicles)
        self.treeview_eculist = widgets.QDockWidget(self)
        self.treeview_eculist.setWindowTitle(_("Ecu List Window"))
        self.treeview_eculist.setWidget(self.eculistwidget)

        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treeview_eculist)
        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treedock_ecu)
        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.treedock_widget)
        self.addDockWidget(core.Qt.BottomDockWidgetArea, self.treedock_logs)

        self.toolbar = self.addToolBar(_("ToolBar"))

        self.diagaction = widgets.QAction(gui.QIcon(ICON_DTC), _("Read DTC"), self)
        self.diagaction.triggered.connect(self.readDtc)
        self.diagaction.setEnabled(False)

        self.log = widgets.QAction(gui.QIcon(ICON_LOG), _("Full log"), self)
        self.log.setCheckable(True)
        self.log.setChecked(options.log_all)
        self.log.triggered.connect(self.changeLogMode)
        if options.dark_mode:
            self.expert = widgets.QAction(gui.QIcon(ICON_EXPERT_B), _("Expert mode (enable writing)"), self)
        else:
            self.expert = widgets.QAction(gui.QIcon(ICON_EXPERT), _("Expert mode (enable writing)"), self)
        self.expert.setCheckable(True)
        self.expert.setChecked(options.promode)
        self.expert.triggered.connect(self.changeUserMode)

        self.autorefresh = widgets.QAction(gui.QIcon(ICON_AUTOREFRESH), _("Auto refresh"), self)
        self.autorefresh.setCheckable(True)
        self.autorefresh.setChecked(options.auto_refresh)
        self.autorefresh.triggered.connect(self.changeAutorefresh)

        self.refresh = widgets.QAction(gui.QIcon(ICON_REFRESH), _("Refresh (one shot)"), self)
        self.refresh.triggered.connect(self.refreshParams)
        self.refresh.setEnabled(not options.auto_refresh)

        self.hexinput = widgets.QAction(gui.QIcon(ICON_HEX), _("Manual command"), self)
        self.hexinput.triggered.connect(self.hexeditor)
        self.hexinput.setEnabled(False)

        self.cominput = widgets.QAction(gui.QIcon(ICON_COMMAND), _("Manual request"), self)
        self.cominput.triggered.connect(self.command_editor)
        self.cominput.setEnabled(False)

        self.fctrigger = widgets.QAction(gui.QIcon(ICON_FLOWCONTROL), _("Software flow control"), self)
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

        if not os.path.exists(get_vehicles_dir()):
            os.mkdir(get_vehicles_dir())

        ecu_files = []
        for filename in os.listdir(get_vehicles_dir()):
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
        theme_dark_action.triggered.connect(lambda checked: set_theme_style(app, 2))
        theme_light_action.triggered.connect(lambda checked: set_theme_style(app, 0))

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

        plugins = list(filter(is_not_package_file, glob.glob(str(plugins_base_dir) + "/*.py")))
        for plugin in plugins:
            try:
                modulename = os.path.basename(plugin).replace(".py", "")
                plug = SourceFileLoader(modulename, plugin).load_module()

                category = plug.category
                name = plug.plugin_name

                # if options.simulation_mode and need_hw:
                #    continue

                if category not in category_menus:
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
        appIcon = gui.QIcon(ICON_OBD)
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
        appIcon = gui.QIcon(ICON_OBD)
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
        options_dialog = MainWindowOptions(self.app)
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
        dialog = EcuFinder(self.ecu_scan)
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
            appIcon = gui.QIcon(ICON_OBD)
            mbox.setWindowIcon(appIcon)
            mbox.setWindowTitle(version.__appname__)
            mbox.setText("Cannot write to directory " + os.path.dirname(filename))
            mbox.exec_()
            return

        self.logview.append(_("Zipping XML database... (this can take a few minutes)"))
        core.QCoreApplication.processEvents()
        zipConvertXML(filename)
        self.logview.append(_("Zip job finished"))

    def launchPlugin(self, pim):
        if self.paramview:
            self.paramview.init('')
        if self.ecu_scan.getNumEcuDb() == 0:
            msgbox = widgets.QMessageBox()
            appIcon = gui.QIcon(ICON_OBD)
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
                appIcon = gui.QIcon(ICON_OBD)
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
        appIcon = gui.QIcon(ICON_OBD)
        msgBox.setWindowIcon(appIcon)
        msgBox.setWindowTitle(version.__appname__)
        msgBox.setText(_('Scan options'))
        scancan = False
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
        ecufile = EcuFile(None)
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
        super(MainWidget, self).closeEvent(event)
        try:
            del options.elm
        except AttributeError:
            pass
    
    def resizeEvent(self, event):
        """Handle window resize to adjust screen widths while preserving vertical scrolling"""
        super(MainWidget, self).resizeEvent(event)
        
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

        self.paramview = ParamWidget(self.scrollview, ecu_file, ecu_addr, ecu_name, self.logview,
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
