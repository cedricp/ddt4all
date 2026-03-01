
import os

import PyQt5.QtCore as core
import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

import ddt4all.core.elm.elm as elm
import ddt4all.options as options
from ddt4all.ui.main_window.donation_widget import DonationWidget
from ddt4all.ui.main_window.utils import (
    set_theme_style,
    set_socket_timeout,
    set_language_realtime
)
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


class MainWindowOptions(widgets.QDialog):
    def __init__(self, app):
        portSpeeds = [38400, 57600, 115200, 230400, 500000, 1000000]
        self.port = None
        self.ports = {}
        self.mode = 0
        self.securitycheck = False
        self.selectedportspeed = 38400
        self.adapter = "STD"
        self.raise_port_speed = _("No")
        super(MainWindowOptions, self).__init__(None)
        # Set window icon and title
        appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
        self.setWindowIcon(appIcon)
        self.setWindowTitle(_("Options"))
        layout = widgets.QVBoxLayout()
        label = widgets.QLabel(self)
        label.setText(_("ELM port selection"))
        label.setAlignment(core.Qt.AlignHCenter | core.Qt.AlignVCenter)
        donationwidget = DonationWidget()
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

        layout.addLayout(medialayout)

        self.btbutton.toggled.connect(self.bt)
        self.wifibutton.toggled.connect(self.wifi)
        self.usbbutton.toggled.connect(self.usb)
        self.obdlinkbutton.toggled.connect(self.obdlink)
        self.elsbutton.toggled.connect(self.els)
        self.vlinkerbutton.toggled.connect(self.vlinker)
        self.derelekbutton.toggled.connect(self.derelek)
        self.vgatebutton.toggled.connect(self.vgate)

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
        self.darklayoutcheck.stateChanged.connect(
            lambda onoff: set_theme_style(app, onoff)
        )
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
                if len(p) >= 3:
                    port, desc, hwid = p
                else:
                    port, desc = p
                    hwid = ""
                
                # Use port description as-is
                item = widgets.QListWidgetItem(self.listview)
                itemname = f"{port}[{desc}]"
                item.setText(itemname)
                self.ports[itemname] = (port, desc, hwid)
                
                # Highlight potential OBD devices based on description
                desc_lower = desc.lower()
                if any(keyword in desc_lower for keyword in ['elm327', 'elm', 'obd', 'vlinker', 'obdlink', 'els27']):
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    item.setBackground(gui.QColor(200, 255, 200))  # Light green background
                    
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
        self.vlinkerbutton.blockSignals(False)
        self.derelekbutton.blockSignals(False)
        self.vgatebutton.blockSignals(False)
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

    def connectedMode(self):
        self.timer.stop()
        self.securitycheck = self.safetycheck.isChecked()
        self.selectedportspeed = int(self.speedcombo.currentText())
        if not self.securitycheck:
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
                self.port = self.ports[portinfo][0]
                options.port_name = self.ports[portinfo][1]
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
