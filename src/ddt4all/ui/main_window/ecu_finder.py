import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

import ddt4all.options as options

_ = options.translator('ddt4all')

# Optional WebEngine import for enhanced features
try:
    import PyQt5.QtWebEngineWidgets as webkitwidgets
    HAS_WEBENGINE = True
except ImportError:
    print(_("Warning: PyQtWebEngine not available. Some features may be limited."))
    webkitwidgets = None
    HAS_WEBENGINE = False

class EcuFinder(widgets.QDialog):
    def __init__(self, ecuscanner):
        super(EcuFinder, self).__init__()
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
