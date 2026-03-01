import copy

import PyQt5.QtCore as core
import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

from ddt4all.core.ecu.ecu_data import EcuData
import ddt4all.options as options
from ddt4all.ui.data_editor.numeric_list_panel import NumericListPanel
from ddt4all.ui.data_editor.numeric_panel import NumericPanel
from ddt4all.ui.data_editor.other_panel import OtherPanel
import ddt4all.version as version

_ = options.translator('ddt4all')

class DataEditor(widgets.QWidget):
    """Main container for data item editor"""

    def __init__(self, parent=None):
        super(DataEditor, self).__init__(parent)
        self.ecurequestsparser = None
        self.currentecudata = None

        layout_action = widgets.QHBoxLayout()
        button_new = widgets.QPushButton(_("New"))
        button_duplicate = widgets.QPushButton(_("Duplicate selected"))
        button_remove = widgets.QPushButton(_("Remove selected"))
        button_reload = widgets.QPushButton(_("Reload"))
        button_validate = widgets.QPushButton(_("Validate changes"))
        layout_action.addWidget(button_new)
        layout_action.addWidget(button_duplicate)
        layout_action.addWidget(button_remove)
        layout_action.addWidget(button_reload)
        layout_action.addWidget(button_validate)
        layout_action.addStretch()

        button_new.clicked.connect(self.new_request)
        button_reload.clicked.connect(self.reload)
        button_validate.clicked.connect(self.validate)
        button_duplicate.clicked.connect(self.duplicate_selected)
        button_remove.clicked.connect(self.remove_selected)

        self.layouth = widgets.QHBoxLayout()

        self.datatable = widgets.QTableWidget()
        self.datatable.setFixedWidth(350)
        self.datatable.setRowCount(1)
        self.datatable.setColumnCount(2)
        self.datatable.verticalHeader().hide()
        self.datatable.setSelectionBehavior(widgets.QAbstractItemView.SelectRows)
        self.datatable.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        # self.datatable.setShowGrid(False)

        self.layouth.addWidget(self.datatable)

        self.editorcontent = widgets.QFrame()
        self.editorcontent.setFrameStyle(widgets.QFrame.Sunken)
        self.editorcontent.setFrameShape(widgets.QFrame.Box)

        self.layoutv = widgets.QVBoxLayout()
        self.layouth.addLayout(self.layoutv)
        self.layoutv.addLayout(layout_action)

        desclayout = widgets.QHBoxLayout()
        labeldescr = widgets.QLabel(_("Description"))
        self.descpriptioneditor = widgets.QLineEdit()
        desclayout.addWidget(labeldescr)
        desclayout.addWidget(self.descpriptioneditor)

        typelayout = widgets.QHBoxLayout()
        typelabel = widgets.QLabel(_("Data type"))
        self.typecombo = widgets.QComboBox()
        self.typecombo.addItem(_("Numeric"))
        self.typecombo.addItem(_("Numeric items"))
        self.typecombo.addItem(_("Hex"))
        typelayout.addWidget(typelabel)
        typelayout.addWidget(self.typecombo)

        self.layoutv.addLayout(desclayout)
        self.layoutv.addLayout(typelayout)

        self.nonePanel = widgets.QWidget()
        self.layoutv.addWidget(self.nonePanel)
        self.currentWidget = self.nonePanel

        self.setLayout(self.layouth)

        self.typecombo.currentIndexChanged.connect(self.switchType)

        self.datatable.itemSelectionChanged.connect(self.changeData)
        self.enable_view(False)

    def remove_selected(self):
        if len(self.datatable.selectedItems()) == 0:
            return

        r = self.datatable.selectedItems()[-1].row()
        dataname = self.datatable.item(r, 0).text()

        # Check if data needed by request
        for reqname, request in self.ecurequestsparser.requests.items():
            for rcvname, rcvdi in request.dataitems.items():
                if rcvname == dataname:
                    msgbox = widgets.QMessageBox()
                    appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
                    msgbox.setWindowIcon(appIcon)
                    msgbox.setWindowTitle(version.__appname__)
                    msgbox.setText(_("Data is used by request %s") % reqname)
                    msgbox.exec_()
                    return
            for sndname, snddi in request.sendbyte_dataitems.items():
                if sndname == dataname:
                    msgbox = widgets.QMessageBox()
                    appIcon = gui.QIcon("ddt4all_data/icons/obd.png")
                    msgbox.setWindowIcon(appIcon)
                    msgbox.setWindowTitle(version.__appname__)
                    msgbox.setText(_("Data is used by request %s") % reqname)
                    msgbox.exec_()
                    return

        self.ecurequestsparser.data.pop(dataname)

        self.reload()

    def duplicate_selected(self):
        if len(self.datatable.selectedItems()) == 0:
            return

        r = self.datatable.selectedItems()[-1].row()

        dataname = self.datatable.item(r, 0).text()
        self.currentecudata = self.ecurequestsparser.data[dataname]

        new_data_name = dataname
        while new_data_name in self.ecurequestsparser.data:
            new_data_name += u"_copy"

        deep_data_copy = copy.deepcopy(self.currentecudata)
        deep_data_copy.name = new_data_name
        self.ecurequestsparser.data[new_data_name] = deep_data_copy
        self.reload()

        copied_item = self.datatable.findItems(new_data_name, core.Qt.MatchExactly)
        self.datatable.selectRow(copied_item[0].row())

        options.main_window.requesteditor.init()

    def enable_view(self, enable):
        children = self.children()
        for c in children:
            if isinstance(c, widgets.QWidget):
                c.setEnabled(enable)

    def edititem(self, name):
        items = self.datatable.findItems(name, core.Qt.MatchExactly)
        if len(items):
            self.datatable.selectRow(items[0].row())
            self.changeData()

    def new_request(self):
        if not self.ecurequestsparser:
            return

        new_data_name = _("New data")

        while new_data_name in self.ecurequestsparser.data.keys():
            new_data_name += "_"

        new_data = EcuData(None, new_data_name)
        new_data.comment = _("Replace me with request description")
        self.ecurequestsparser.data[new_data_name] = new_data

        self.reload()

        new_item = self.datatable.findItems(new_data_name, core.Qt.MatchExactly)
        self.datatable.selectRow(new_item[0].row())

        # Refresh request data combo
        options.main_window.requesteditor.refresh_data()

    def cellModified(self, r, c):
        if c != 0:
            return

        currentecudata = self.currentecudata
        oldname = currentecudata.name
        self.ecurequestsparser.data.pop(oldname)
        item = self.datatable.item(r, c)
        newname = item.text()
        currentecudata.name = newname
        self.ecurequestsparser.data[newname] = currentecudata

        # Change requests data items name too
        for reqk, req in self.ecurequestsparser.requests.items():
            sbdata = req.sendbyte_dataitems
            rbdata = req.dataitems

            if oldname in sbdata.keys():
                sbdata[oldname].name = newname
                sbdata[newname] = sbdata.pop(oldname)

            if oldname in rbdata.keys():
                rbdata[oldname].name = newname
                rbdata[newname] = rbdata.pop(oldname)

        options.main_window.paramview.dataNameChanged(oldname, newname)
        options.main_window.requesteditor.refresh_data()

    def clear(self):
        self.datatable.clear()
        self.switchType(3)

    def reload(self):
        self.init_table()

    def validate(self):
        if "validate" not in dir(self.currentWidget):
            return

        comment = self.descpriptioneditor.text()
        self.currentecudata.comment = comment
        self.currentWidget.validate()
        options.main_window.requesteditor.refresh_data()

        # Update table entry
        if len(self.datatable.selectedItems()) == 0:
            return

        r = self.datatable.selectedItems()[-1].row()
        self.datatable.item(r, 1).setText(comment)

    def changeData(self):
        if len(self.datatable.selectedItems()) == 0:
            return

        r = self.datatable.selectedItems()[-1].row()

        dataname = self.datatable.item(r, 0).text()
        self.currentecudata = self.ecurequestsparser.data[dataname]
        self.descpriptioneditor.setText(self.currentecudata.comment)
        if self.currentecudata.scaled:
            self.switchType(0)
        elif len(self.currentecudata.items):
            self.switchType(1)
        else:
            self.switchType(2)

    def switchType(self, num):
        self.descpriptioneditor.setEnabled(True)
        self.typecombo.setEnabled(True)
        if num == 0:
            self.typecombo.setCurrentIndex(0)
            self.layoutv.removeWidget(self.currentWidget)
            self.currentWidget.hide()
            self.currentWidget.destroy()
            self.currentWidget = NumericPanel(self.currentecudata)
            self.layoutv.addWidget(self.currentWidget)

        if num == 1:
            self.typecombo.setCurrentIndex(1)
            self.layoutv.removeWidget(self.currentWidget)
            self.currentWidget.hide()
            self.currentWidget.destroy()
            self.currentWidget = NumericListPanel(self.currentecudata)
            self.layoutv.addWidget(self.currentWidget)

        if num == 2:
            self.typecombo.setCurrentIndex(2)
            self.layoutv.removeWidget(self.currentWidget)
            self.currentWidget.hide()
            self.currentWidget.destroy()
            self.currentWidget = OtherPanel(self.currentecudata)
            self.layoutv.addWidget(self.currentWidget)

        if num == 3:
            self.layoutv.removeWidget(self.currentWidget)
            self.currentWidget.hide()
            self.currentWidget.destroy()
            self.currentWidget = widgets.QWidget()
            self.layoutv.addWidget(self.currentWidget)
            self.descpriptioneditor.setEnabled(False)
            self.typecombo.setEnabled(False)

    def disconnect_table(self):
        try:
            self.datatable.cellChanged.disconnect()
        except Exception:
            pass

    def connect_table(self):
        self.datatable.cellChanged.connect(self.cellModified)

    def init_table(self):
        self.disconnect_table()

        self.datatable.clear()
        dataItems = self.ecurequestsparser.data.keys()
        self.datatable.setRowCount(len(dataItems))

        count = 0
        for k in dataItems:
            data = self.ecurequestsparser.data[k]

            itemk = widgets.QTableWidgetItem(k)
            itemc = widgets.QTableWidgetItem(data.comment)

            itemc.setFlags(itemc.flags() ^ core.Qt.ItemIsEditable)

            self.datatable.setItem(count, 0, itemk)
            self.datatable.setItem(count, 1, itemc)

            count += 1

        self.datatable.sortItems(0, core.Qt.AscendingOrder)

        headerstrings = _("Data name;Description").split(";")
        self.datatable.setHorizontalHeaderLabels(headerstrings)
        self.datatable.resizeColumnsToContents()
        self.datatable.resizeRowsToContents()
        self.datatable.sortByColumn(0, core.Qt.AscendingOrder)
        self.connect_table()

    def set_ecu(self, ecu):
        self.ecurequestsparser = ecu
        self.switchType(3)
        self.init_table()
        self.enable_view(True)
