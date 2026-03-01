
import PyQt5.QtCore as core
import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

import ddt4all.options as options
import ddt4all.version as version

_ = options.translator('ddt4all')


class DonationWidget(widgets.QLabel):
    def __init__(self):
        super(DonationWidget, self).__init__()
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
