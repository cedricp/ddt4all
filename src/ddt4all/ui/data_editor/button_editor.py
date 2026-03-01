import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets

import ddt4all.options as options
from ddt4all.ui.data_editor.button_data import ButtonData

_ = options.translator('ddt4all')


class ButtonEditor(widgets.QWidget):
    """Main container for button editor"""

    def __init__(self, parent=None):
        super(ButtonEditor, self).__init__(parent)
        self.ecurequestsparser = None

        self.layout = None
        self.layouth = widgets.QHBoxLayout()
        self.buttontable = widgets.QTableWidget()
        self.layoutv = widgets.QVBoxLayout()

        self.layouth.addWidget(self.buttontable)
        self.layouth.addLayout(self.layoutv)

        self.buttondata = ButtonData()
        self.layoutv.addWidget(self.buttondata)

        self.setLayout(self.layouth)

        self.buttontable.setFixedWidth(250)
        self.buttontable.setColumnCount(2)
        self.buttontable.verticalHeader().hide()
        self.buttontable.setSelectionBehavior(widgets.QAbstractItemView.SelectRows)
        self.buttontable.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        # self.buttontable.setShowGrid(False)
        self.buttontable.itemSelectionChanged.connect(self.selection_changed)
        self.enable_view(False)

    def name_changed(self, r, c):
        if r == 0:
            return

        currentitem = self.buttontable.item(r, 0)

        if not currentitem:
            return

        idx = currentitem.row() - 1
        buttondata = self.layout['buttons'][idx]
        textdata = currentitem.text()

        buttondata['text'] = textdata
        buttondata['uniquename'] = textdata + u"_" + str(idx)
        self.init()
        if options.main_window:
            options.main_window.paramview.reinitScreen()

    def selection_changed(self):
        selitems = self.buttontable.selectedItems()
        if not len(selitems):
            return

        current_row = selitems[-1].row()
        is_screen = current_row == 0
        current_item_name = self.buttontable.item(current_row, 1).text()
        self.buttondata.init_table(current_item_name, is_screen)

    def set_ecu(self, ecu):
        self.ecurequestsparser = ecu
        self.enable_view(True)

    def enable_view(self, enable):
        children = self.children()
        for c in children:
            if isinstance(c, widgets.QWidget):
                c.setEnabled(enable)

    def set_layout(self, layout):
        self.layout = layout
        self.init()

    def init(self):
        try:
            self.buttontable.cellChanged.disconnect(self.name_changed)
        except Exception:
            pass

        self.buttontable.clearSelection()
        self.buttondata.clear()

        if self.ecurequestsparser:
            self.buttondata.init(self.ecurequestsparser, self.layout)

        num_buttons = len(self.layout['buttons'])
        self.buttontable.setRowCount(num_buttons + 1)

        scitem = widgets.QTableWidgetItem(_("Screen initialization"))
        noitem = widgets.QTableWidgetItem(_("Requests to send before screen drawing"))
        self.buttontable.setItem(0, 0, scitem)
        self.buttontable.setItem(0, 1, noitem)
        scitem.setFlags(core.Qt.ItemIsSelectable | core.Qt.ItemIsEnabled)
        noitem.setFlags(core.Qt.ItemIsSelectable | core.Qt.ItemIsEnabled)

        count = 1
        for button in self.layout['buttons']:
            uniquenameitem = widgets.QTableWidgetItem(button['uniquename'])
            self.buttontable.setItem(count, 0, widgets.QTableWidgetItem(button['text']))
            self.buttontable.setItem(count, 1, uniquenameitem)
            uniquenameitem.setFlags(core.Qt.ItemIsSelectable | core.Qt.ItemIsEnabled)
            count += 1

        headerstrings = _("Button name;Unique name").split(";")
        self.buttontable.setHorizontalHeaderLabels(headerstrings)
        self.buttontable.resizeColumnsToContents()
        self.buttontable.resizeRowsToContents()
        self.buttontable.selectRow(0)
        self.buttontable.cellChanged.connect(self.name_changed)
