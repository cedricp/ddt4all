
import os
import re
import time

import PyQt5.QtCore as core
import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

import ddt4all.core.elm.elm as elm
import ddt4all.options as options
from ddt4all.ui.main_window.donation_widget import DonationWidget
from ddt4all.ui.main_window.icons_paths import (
    ICON_BT,
    ICON_DERELEK,
    ICON_DOIP,
    ICON_ELS27,
    ICON_OBD,
    ICON_OBDLINK,
    ICON_USB,
    ICON_VGATE,
    ICON_VLINKER,
    ICON_WIFI,
)
from ddt4all.ui.main_window.utils import (
    set_theme_style,
    set_socket_timeout
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


class PortScanWorker(core.QThread):
    portsFound = core.pyqtSignal(list)

    def run(self):
        ports = elm.get_available_ports()
        self.portsFound.emit(ports or [])


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
        appIcon = gui.QIcon(ICON_OBD)
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
        self.usbbutton.setIcon(gui.QIcon(ICON_USB))
        self.usbbutton.setIconSize(core.QSize(60, 60))
        self.usbbutton.setFixedHeight(64)
        self.usbbutton.setFixedWidth(64)
        self.usbbutton.setCheckable(True)
        self.usbbutton.setToolTip(_("USB"))
        medialayout.addWidget(self.usbbutton)

        self.wifibutton = widgets.QPushButton()
        self.wifibutton.setIcon(gui.QIcon(ICON_WIFI))
        self.wifibutton.setIconSize(core.QSize(60, 60))
        self.wifibutton.setFixedHeight(64)
        self.wifibutton.setFixedWidth(64)
        self.wifibutton.setCheckable(True)
        self.wifibutton.setToolTip(_("WiFi"))
        medialayout.addWidget(self.wifibutton)

        self.btbutton = widgets.QPushButton()
        self.btbutton.setIcon(gui.QIcon(ICON_BT))
        self.btbutton.setIconSize(core.QSize(60, 60))
        self.btbutton.setFixedHeight(64)
        self.btbutton.setFixedWidth(64)
        self.btbutton.setCheckable(True)
        self.btbutton.setToolTip(_("Bluetooth"))
        medialayout.addWidget(self.btbutton)

        self.obdlinkbutton = widgets.QPushButton()
        self.obdlinkbutton.setIcon(gui.QIcon(ICON_OBDLINK))
        self.obdlinkbutton.setIconSize(core.QSize(60, 60))
        self.obdlinkbutton.setFixedHeight(64)
        self.obdlinkbutton.setFixedWidth(64)
        self.obdlinkbutton.setCheckable(True)
        self.obdlinkbutton.setToolTip(_("OBDLINK SX/EX"))
        medialayout.addWidget(self.obdlinkbutton)

        self.elsbutton = widgets.QPushButton()
        self.elsbutton.setIcon(gui.QIcon(ICON_ELS27))
        self.elsbutton.setIconSize(core.QSize(60, 60))
        self.elsbutton.setFixedHeight(64)
        self.elsbutton.setFixedWidth(64)
        self.elsbutton.setCheckable(True)
        self.elsbutton.setToolTip(_("ELS27/ELS27 V5 - May appear as FTDI/CH340/CP210x device"))
        medialayout.addWidget(self.elsbutton)

        self.vlinkerbutton = widgets.QPushButton()
        self.vlinkerbutton.setIcon(gui.QIcon(ICON_VLINKER))
        self.vlinkerbutton.setIconSize(core.QSize(60, 60))
        self.vlinkerbutton.setFixedHeight(64)
        self.vlinkerbutton.setFixedWidth(64)
        self.vlinkerbutton.setCheckable(True)
        self.vlinkerbutton.setToolTip(_("Vlinker FS/MC"))
        medialayout.addWidget(self.vlinkerbutton)

        self.derelekbutton = widgets.QPushButton()
        self.derelekbutton.setIcon(gui.QIcon(ICON_DERELEK))
        self.derelekbutton.setIconSize(core.QSize(60, 60))
        self.derelekbutton.setFixedHeight(64)
        self.derelekbutton.setFixedWidth(64)
        self.derelekbutton.setCheckable(True)
        self.derelekbutton.setToolTip(_("DERLEK USB-DIAG2/3"))
        medialayout.addWidget(self.derelekbutton)

        self.vgatebutton = widgets.QPushButton()
        self.vgatebutton.setIcon(gui.QIcon(ICON_VGATE))
        self.vgatebutton.setIconSize(core.QSize(60, 60))
        self.vgatebutton.setFixedHeight(64)
        self.vgatebutton.setFixedWidth(64)
        self.vgatebutton.setCheckable(True)
        self.vgatebutton.setToolTip(_("VGate (High-Speed)"))
        medialayout.addWidget(self.vgatebutton)

        self.doipbutton = widgets.QPushButton()
        self.doipbutton.setIcon(gui.QIcon(ICON_DOIP))
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
        
        self.doip_presetcombo.activated.connect(self.apply_doip_preset)
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

        self._scan_worker = None
        self.timer = core.QTimer()
        self.timer.timeout.connect(self.rescan_ports)
        self.timer.start(2000)
        self.portcount = -1
        self.usb()
        self.rescan_ports()
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
        # Get the language code from the selected language name
        if language_name in options.lang_list:
            lang_code = options.lang_list[language_name]

            # Update configuration
            options.configuration["lang"] = lang_code

            # Update environment variable
            os.environ['LANG'] = lang_code

            # Save configuration
            options.save_config()

            # Reinitialize the global translator with new language
            global _
            _ = options.translator('ddt4all')

            # Close current window and return to main flow
            # This will allow the main application to recreate everything with new language
            self.mode = 0  # Set mode to 0 to trigger restart in main loop
            self.done(True)
            exit(0)

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
        if self._scan_worker is not None and self._scan_worker.isRunning():
            return
        self._scan_worker = PortScanWorker()
        self._scan_worker.portsFound.connect(self._on_ports_found)
        self._scan_worker.start()

    def _on_ports_found(self, ports):
        try:
            if not ports:
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

                # Use port description with USB VID:PID if available
                item = widgets.QListWidgetItem(self.listview)
                if hwid and 'USB VID:PID=' in hwid:
                    itemname = f"{port}[{desc}] {hwid}"
                else:
                    itemname = f"{port}[{desc}]"
                item.setText(itemname)
                self.ports[itemname] = (port, desc, hwid, status)

                # Highlight potential OBD devices based on description first
                desc_lower = desc.lower()
                is_obd_device = any(keyword in desc_lower for keyword in ['elm327', 'elm', 'obd', 'vlinker', 'obdlink', 'els27', 'doip'])
                
                # Set device type with realistic, distinctive colors
                if is_obd_device:
                    if 'doip' in desc_lower:
                        item.setData(32, "doip")  # Qt.UserRole + 1 for device type
                        item.setBackground(gui.QColor(135, 206, 235))  # Sky blue for DoIP
                    else:
                        item.setData(32, "obd")  # Qt.UserRole + 1 for device type
                        item.setBackground(gui.QColor(144, 238, 144))  # Light green for OBD
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                elif status == "online":
                    item.setBackground(gui.QColor(60, 179, 113))  # Medium sea green
                elif status == "offline":
                    item.setBackground(gui.QColor(205, 92, 92))  # Indian red
                else:
                    item.setBackground(gui.QColor(192, 192, 192))  # Silver

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

        except Exception as e:
            print(f"Error updating port list: {e}")

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

    def apply_doip_preset(self, index):
        """Apply DoIP device preset configurations"""
        # Prevent multiple rapid calls
        if hasattr(self, '_last_preset_time') and time.time() - self._last_preset_time < 1.0:
            return
        
        self._last_preset_time = time.time()
        
        preset_name = self.doip_presetcombo.itemText(index)
        
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
            
            # Update GUI fields
            self.doip_ipinput.setText(preset["ip"])
            self.doip_portinput.setValue(preset["port"])
            self.doip_timeoutinput.setValue(preset["timeout"])
            self.doip_announcecheck.setChecked(preset["announcement"])
            self.doip_reconnectcheck.setChecked(preset["auto_reconnect"])
            
            # Check if the IP actually changed BEFORE updating options
            current_ip = getattr(options, 'doip_target_ip', '192.168.0.12')
            ip_changed = current_ip != preset['ip']
            
            # Update options module variables
            options.doip_target_ip = preset["ip"]
            options.doip_target_port = preset["port"]
            options.doip_timeout = preset["timeout"]
            options.doip_vehicle_announcement = preset["announcement"]
            options.doip_auto_reconnect = preset["auto_reconnect"]
            options.doip_preset = preset_name
            
            # Update configuration dictionary
            options.configuration["doip_target_ip"] = preset["ip"]
            options.configuration["doip_target_port"] = preset["port"]
            options.configuration["doip_timeout"] = preset["timeout"]
            options.configuration["doip_vehicle_announcement"] = preset["announcement"]
            options.configuration["doip_auto_reconnect"] = preset["auto_reconnect"]
            options.configuration["doip_preset"] = preset_name
            
            # Save configuration automatically
            options.save_config()
            
            # Reload device list to reflect new DoIP configuration
            # Use robust DoIP-only mode to prevent all crashes
            try:
                if ip_changed:
                    # Use QTimer to delay the update and prevent crashes
                    core.QTimer.singleShot(300, self._force_doip_update)
                    print(f"DoIP preset applied: {preset_name} -> {preset['ip']}")
                else:
                    print(f"DoIP preset applied: {preset_name} (IP unchanged)")
            except Exception as e:
                print(f"Error preparing DoIP update: {e}")
            
            # Log the preset application
            self.logview.append(f"Applied {preset_name} preset:")
            self.logview.append(f"  IP: {preset['ip']}")
            self.logview.append(f"  Port: {preset['port']}")
            self.logview.append(f"  Timeout: {preset['timeout']}s")
            self.logview.append(f"  Configuration saved and device list reloaded")

    def _force_doip_update(self):
        """Force DoIP update bypassing all problematic operations"""
        try:
            # Get current DoIP configuration
            doip_ip = getattr(options, 'doip_target_ip', '192.168.0.12')
            doip_port = getattr(options, 'doip_target_port', 13400)
            
            # Clear the device list completely - no rescan_ports()
            self.listview.clear()
            self.ports = {}
            self.portcount = 0
            
            # Add only DoIP device - no COM port scanning

            item = widgets.QListWidgetItem(self.listview)
            itemname = f"{doip_ip}:{doip_port}[DoIP Device - {doip_ip}:{doip_port}]"
            item.setText(itemname)
            item.setBackground(gui.QColor(150, 50, 50))  # Dark red for offline
            self.ports[itemname] = (f"{doip_ip}:{doip_port}", f"DoIP Device - {doip_ip}:{doip_port}", "", "offline")
            
        except Exception as e:
            print(f"Error in force DoIP update: {e}")

    def _delayed_doip_update(self):
        """Delayed DoIP device list update to prevent crashes"""
        try:
            # Check if we're still in a valid state
            if not hasattr(self, 'listview') or self.listview is None:
                return
                
            # Force DoIP update - bypass all problematic operations
            self._force_doip_update()
                
        except Exception as e:
            print(f"Error in delayed DoIP update: {e}")
            # Try force update as last resort
            try:
                self._force_doip_update()
            except:
                pass

    def _update_doip_device_only(self):
        """Update only the DoIP device in the list without full rescan"""
        try:
            # Get current DoIP configuration
            doip_ip = getattr(options, 'doip_target_ip', '192.168.0.12')
            doip_port = getattr(options, 'doip_target_port', 13400)
            
            # Find and remove existing DoIP device
            items_to_remove = []
            for i in range(self.listview.count()):
                item = self.listview.item(i)
                item_text = item.text()
                if 'DoIP Device' in item_text and doip_ip in item_text:
                    items_to_remove.append(item)
            
            # Remove old DoIP devices
            for item in items_to_remove:
                row = self.listview.row(item)
                self.listview.takeItem(row)
                
            # Add new DoIP device
            item = widgets.QListWidgetItem(self.listview)
            itemname = f"{doip_ip}:{doip_port}[DoIP Device - {doip_ip}:{doip_port}]"
            item.setText(itemname)
            item.setBackground(core.QColor(150, 50, 50))  # Dark red for offline
            self.ports[itemname] = (f"{doip_ip}:{doip_port}", f"DoIP Device - {doip_ip}:{doip_port}", "", "offline")
            
            print(f"DoIP device updated: {doip_ip}:{doip_port}")
            
        except Exception as e:
            print(f"Error in targeted DoIP update: {e}")
            raise

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
        if self._scan_worker is not None and self._scan_worker.isRunning():
            self._scan_worker.wait()
        self.securitycheck = self.safetycheck.isChecked()
        self.selectedportspeed = int(self.speedcombo.currentText())
        if not self.securitycheck:
            msgbox = widgets.QMessageBox()
            appIcon = gui.QIcon(ICON_OBD)
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
                appIcon = gui.QIcon(ICON_OBD)
                msgbox.setWindowIcon(appIcon)
                msgbox.setWindowTitle(version.__appname__)
                msgbox.setText(_("Please select a communication port"))
                msgbox.exec_()

    def demoMode(self):
        self.timer.stop()
        if self._scan_worker is not None and self._scan_worker.isRunning():
            self._scan_worker.wait()
        self.securitycheck = self.safetycheck.isChecked()
        self.port = 'DUMMY'
        self.mode = 2
        options.report_data = False
        options.simulation_mode = True
        self.done(True)
