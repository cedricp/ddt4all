import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets


class HexSpinBox(widgets.QSpinBox):

    def __init__(self, iscan=True):
        widgets.QSpinBox.__init__(self)
        self.set_can(iscan)

    def set_can(self, iscan):
        if iscan:
            self.setRange(0, 0x7FF)
            self.can = True
        else:
            self.setRange(0, 0xFF)
            self.can = False

    def textFromValue(self, value):
        if self.can:
            return "%03X" % value
        else:
            return "%02X" % value

    def valueFromText(self, text):
        if len(text) == 0:
            return 0
        return int("0x" + str(text), 16)

    def validate(self, input, pos):
        if len(str(input)) == 0:
            return (gui.QValidator.Acceptable, input, pos)

        try:
            int("0x" + str(input)[pos - 1], 16)
        except Exception:
            return (gui.QValidator.Invalid, input, pos)

        return (gui.QValidator.Acceptable, input, pos)

