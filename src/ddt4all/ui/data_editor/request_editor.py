import PyQt5.QtWidgets as widgets

from ddt4all.core.ecu.ecu_request import EcuRequest
import ddt4all.options as options
from ddt4all.ui.data_editor.param_editor import ParamEditor
from ddt4all.ui.data_editor.request_table import RequestTable

_ = options.translator('ddt4all')

class RequestEditor(widgets.QWidget):
    """Main container for reauest editor"""

    def __init__(self, parent=None):
        super(RequestEditor, self).__init__(parent)
        self.ecurequestsparser = None

        layoutsss = widgets.QHBoxLayout()

        self.checknosds = widgets.QCheckBox(_("No SDS"))
        self.checkplant = widgets.QCheckBox(_("Plant"))
        self.checkaftersales = widgets.QCheckBox(_("After Sale"))
        self.checkengineering = widgets.QCheckBox(_("Engineering"))
        self.checksupplier = widgets.QCheckBox(_("Supplier"))

        self.checknosds.toggled.connect(self.sdschanged)
        self.checkplant.toggled.connect(self.sdschanged)
        self.checkaftersales.toggled.connect(self.sdschanged)
        self.checkengineering.toggled.connect(self.sdschanged)
        self.checksupplier.toggled.connect(self.sdschanged)

        layoutsss.addWidget(self.checknosds)
        layoutsss.addWidget(self.checkplant)
        layoutsss.addWidget(self.checkaftersales)
        layoutsss.addWidget(self.checkengineering)
        layoutsss.addWidget(self.checksupplier)

        layout_action = widgets.QHBoxLayout()
        button_reload = widgets.QPushButton(_("Reload requests"))
        button_add = widgets.QPushButton(_("Add request"))
        layout_action.addWidget(button_reload)
        layout_action.addWidget(button_add)
        layout_action.addStretch()

        button_reload.clicked.connect(self.reload)
        button_add.clicked.connect(self.add_request)

        self.layh = widgets.QHBoxLayout()
        self.requesttable = RequestTable()
        self.layh.addWidget(self.requesttable)

        self.layv = widgets.QVBoxLayout()

        self.sendbyteeditor = ParamEditor()
        self.receivebyteeditor = ParamEditor(False)
        self.tabs = widgets.QTabWidget()

        self.tabs.addTab(self.sendbyteeditor, _("Send bytes"))
        self.tabs.addTab(self.receivebyteeditor, _("Receive bytes"))

        self.layv.addLayout(layout_action)
        self.layv.addLayout(layoutsss)
        self.layv.addWidget(self.tabs)

        self.layh.addLayout(self.layv)
        self.setLayout(self.layh)

        self.requesttable.setSendByteEditor(self.sendbyteeditor)
        self.requesttable.setReceiveByteEditor(self.receivebyteeditor)
        self.enable_view(False)

    def refresh_data(self):
        self.sendbyteeditor.refresh_combo()
        self.receivebyteeditor.refresh_combo()

    def enable_view(self, enable):
        children = self.children()
        for c in children:
            if isinstance(c, widgets.QWidget):
                c.setEnabled(enable)

    def add_request(self):
        ecu_datareq = {}
        ecu_datareq['minbytes'] = 2
        ecu_datareq['shiftbytescount'] = 0
        ecu_datareq['replybytes'] = ''
        ecu_datareq['manualsend'] = False
        ecu_datareq['sentbytes'] = ''
        ecu_datareq['endian'] = ''
        ecu_datareq['name'] = u'New request'
        self.ecurequestsparser.requests[ecu_datareq['name']] = EcuRequest(ecu_datareq, self.ecurequestsparser)
        self.init()
        self.requesttable.select(ecu_datareq['name'])

    def sdschanged(self):
        if not self.ecurequestsparser:
            return

        self.requesttable.set_sds(self)

    def reload(self):
        if not self.ecurequestsparser:
            return
        self.init()

    def init(self):
        self.requesttable.init(self.ecurequestsparser.requests)
        self.sendbyteeditor.set_ecufile(self.ecurequestsparser)
        self.receivebyteeditor.set_ecufile(self.ecurequestsparser)

    def init_sds(self, req):
        self.checknosds.setChecked(req.sds['nosds'])
        self.checkplant.setChecked(req.sds['plant'])
        self.checkaftersales.setChecked(req.sds['aftersales'])
        self.checkengineering.setChecked(req.sds['engineering'])
        self.checksupplier.setChecked(req.sds['supplier'])

    def set_ecu(self, ecu):
        self.ecurequestsparser = ecu
        self.init()
        self.enable_view(True)

