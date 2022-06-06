#!/usr/bin/env python


###############################################################################
# Copyright (c) 2020 Riverbank Computing Limited.
###############################################################################


import sys
import sysconfig

from PyQt5.QtCore import PYQT_VERSION_STR, QT_VERSION_STR, QFile, QIODevice
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QLabel, QTabWidget, QTreeView,
                             QVBoxLayout, QWidget)

try:
    from pdytools import hexversion as pdy_hexversion
except ImportError:
    pdy_hexversion = 0

# Try and import the platform-specific modules.
platform_module = "Not available"

try:
    import PyQt5.QtAndroidExtras

    platform_module = 'QtAndroidExtras'
except ImportError:
    pass

try:
    import PyQt5.QtMacExtras

    platform_module = 'QtMacExtras'
except ImportError:
    pass

try:
    import PyQt5.QtWinExtras

    platform_module = 'QtWinExtras'
except ImportError:
    pass

try:
    import PyQt5.QtX11Extras

    platform_module = 'QtX11Extras'
except ImportError:
    pass

# Try and import the optional products.
optional_products = []

try:
    import PyQt5.Qt3DCore

    optional_products.append("PyQt3D")
except ImportError:
    pass

try:
    import PyQt5.QtChart

    optional_products.append("PyQtChart")
except ImportError:
    pass

try:
    import PyQt5.QtDataVisualization

    optional_products.append("PyQtDataVisualization")
except ImportError:
    pass

try:
    import PyQt5.QtPurchasing

    optional_products.append("PyQtPurchasing")
except ImportError:
    pass

try:
    import PyQt5.Qsci

    optional_products.append("QScintilla")
except ImportError:
    pass


class SummaryView(QTreeView):
    """ A read-only view for displaying a model. """

    def __init__(self, model):
        """ Initialise the object. """

        super().__init__()

        self.setModel(model)
        self.setRootIsDecorated(False)
        self.setEditTriggers(self.EditTrigger(0))
        self.resizeColumnToContents(0)


class Model(QStandardItemModel):
    """ A model containing a collection of interesting values. """

    def __init__(self):
        """ Initialise the object. """

        super().__init__()

        self.setHorizontalHeaderLabels(["Name", "Value"])

        # Populate the model.
        self.add_value("Platform", sysconfig.get_platform())
        self.add_value("PyQt version", PYQT_VERSION_STR)
        self.add_value("Python version", self.from_hexversion(sys.hexversion))
        self.add_value("Qt version", QT_VERSION_STR)
        self.add_value("sys.platform", sys.platform)
        self.add_value("sys.path", str(sys.path))
        self.add_value("sys.path_hooks", str(sys.path_hooks))
        self.add_value("sys.meta_path", str(sys.meta_path))

        self.add_value("Platform module", platform_module)

        avail = "unavailable"
        try:
            import zlib

            avail = "available ({0})".format(zlib.ZLIB_VERSION)
        except ImportError:
            pass

        self.add_value("zlib support", avail)

        avail = "unavailable"
        try:
            import ssl

            avail = "available ({0})".format(ssl.OPENSSL_VERSION)
        except ImportError:
            pass

        self.add_value("Python SSL support", avail)

        avail = "unavailable"
        try:
            from PyQt5.QtNetwork import QSslSocket

            if QSslSocket.supportsSsl():
                avail = "available ({0})".format(
                    QSslSocket.sslLibraryVersionString())
        except ImportError:
            pass

        self.add_value("Qt SSL support", avail)

        for product in optional_products:
            self.add_value(product, "imported")

    def add_value(self, name, value):
        """ Add a name/value pair to the model. """

        self.appendRow([QStandardItem(name), QStandardItem(value)])

    @staticmethod
    def from_hexversion(hexversion):
        """ Convert a hexadecimal version number to a string. """

        return '%s.%s.%s' % ((hexversion >> 24) & 0xff,
                             (hexversion >> 16) & 0xff, (hexversion >> 8) & 0xff)


def get_source_code():
    """ Return a copy of this source code. """

    if pdy_hexversion == 0:
        # We are running in a non-deployed state so use this copy of the
        # source.
        with open(__file__, encoding='utf-8') as f:
            source = f.read()
    else:
        # Use the resources package if the version of Python is new enough.
        try:
            from importlib.resources import read_text
        except ImportError:
            source = get_source_code_using_qt()
        else:
            source = read_text('data', 'pyqt-demo.py.dat')

    return source


def get_source_code_using_qt():
    """ Return a copy of this source code using QFile's support for embedded
    resources.
    """

    import data_mobile

    # Getting the path name of the embedded source file this way means we don't
    # need to know the path separator.
    qf = QFile(data_mobile.__file__.replace('__init__.pyo', 'make_mobile_app_data_test.py.dat'))

    qf.open(QIODevice.ReadOnly | QIODevice.Text)
    source = qf.readAll()
    qf.close()

    return bytes(source).decode()


def create_qscintilla_code_view():
    """ Create a QScintilla based view containing a copy of this source code.
    """

    from PyQt5.Qsci import QsciLexerPython, QsciScintilla

    view = QsciScintilla()
    view.setReadOnly(True)
    view.setUtf8(True)
    view.setLexer(QsciLexerPython())
    view.setFolding(QsciScintilla.PlainFoldStyle)
    view.setText(get_source_code())

    return view


def create_fallback_code_view():
    """ Create a QTextEdit based view containing a copy of this source code.
    """

    from PyQt5.QtWidgets import QTextEdit

    view = QTextEdit(readOnly=True)
    view.setPlainText(get_source_code())

    return view


# Create the GUI.
app = QApplication(sys.argv)

shell = QWidget(windowTitle="PyQt Demo")
shell_layout = QVBoxLayout()

header = QLabel("""<p>
This is a simple Python application using the PyQt bindings for the
cross-platform Qt application framework.
</p>
<p>
It will run on macOS, Linux, Windows, iOS and Android without changes to the
source code.
</p>
<p>
For more information about PyQt go to
<a href="https://www.riverbankcomputing.com">www.riverbankcomputing.com</a>.
</p>""")
header.setOpenExternalLinks(True)
header.setWordWrap(True)
shell_layout.addWidget(header)

views = QTabWidget()

summary = SummaryView(Model())
views.addTab(summary, "Summary")

if "QScintilla" in optional_products:
    code = create_qscintilla_code_view()
else:
    code = create_fallback_code_view()

views.addTab(code, "Source Code")

shell_layout.addWidget(views)

if pdy_hexversion != 0:
    footer = QLabel("<p>It is a self-contained executable created using pyqtdeploy v%s.</p>" % Model.from_hexversion(pdy_hexversion))
    footer.setWordWrap(True)
    shell_layout.addWidget(footer)

shell.setLayout(shell_layout)

# Show the GUI and interact with it.
shell.show()
app.exec()

# All done.
sys.exit()
