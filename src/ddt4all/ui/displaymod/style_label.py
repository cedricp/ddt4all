import PyQt5.QtWidgets as widgets

class StyleLabel(widgets.QLabel):
    def __init__(self, parent):
        super(StyleLabel, self).__init__(parent)
        self.defaultStyle = ""

    def setDefaultStyle(self, style):
        self.defaultStyle = style
        self.setStyleSheet(self.defaultStyle)

    def resetDefaultStyle(self):
        self.setStyleSheet(self.defaultStyle)