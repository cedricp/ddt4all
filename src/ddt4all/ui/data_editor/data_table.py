
import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets

import ddt4all.options as options

class DataTable(widgets.QTableWidget):
    gotoitem = core.pyqtSignal(object)
    removeitem = core.pyqtSignal(object)

    def __init__(self, parent=None):
        super(DataTable, self).__init__(parent)
        self.issend = None
        self.requestname = None

    def goto_item(self, item):
        self.gotoitem.emit(item)

    def remove_item(self, item):
        self.removeitem.emit(item)

    def add_to_screen(self, name, item):
        if not options.main_window.paramview:
            return
        itemtext = item
        options.main_window.paramview.addParameter(self.requestname, self.issend, name, itemtext)

    def init(self, issend, requestname):
        self.issend = issend
        self.requestname = requestname

    def contextMenuEvent(self, event):
        pos = event.pos()
        index = self.indexAt(pos)
        menu = widgets.QMenu()

        if index.column() == 0:
            item_name = self.itemAt(pos).text()
            if not item_name:
                return
            action_goto = widgets.QAction(_("Goto data"), menu)
            action_remove = widgets.QAction(_("Remove"), menu)

            action_goto.triggered.connect(lambda state, it=item_name: self.goto_item(it))
            action_remove.triggered.connect(lambda state, it=item_name: self.remove_item(it))

            screenMenu = widgets.QMenu(_("Add to screen"))
            for sn in options.main_window.screennames:
                sa = widgets.QAction(sn, screenMenu)
                sa.triggered.connect(lambda state, name=sn, it=item_name: self.add_to_screen(name, it))
                screenMenu.addAction(sa)

            menu.addActions([action_goto, action_remove])
            menu.addMenu(screenMenu)

            menu.exec_(event.globalPos())
            event.accept()

