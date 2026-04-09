import PyQt5.QtWidgets as widgets

class HexLineEdit(widgets.QLineEdit):
    def __init__(self, num, alpha):
        widgets.QLineEdit.__init__(self)
        if not alpha:
            self.setInputMask("H" * num)
        else:
            self.setInputMask("N" * num)
