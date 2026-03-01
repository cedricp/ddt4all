import PyQt5.QtWidgets as widgets

class CheckBox(widgets.QCheckBox):
    def __init__(self, data, parent=None):
        super(CheckBox, self).__init__(parent)
        self.data = data
        if data.manualsend:
            self.setChecked(True)
        else:
            self.setChecked(False)

        self.stateChanged.connect(self.change)

    def change(self, state):
        if state:
            self.data.manualsend = True
        else:
            self.data.manualsend = False

