import PyQt5.QtWidgets as widgets

from ddt4all.ui.utils import (
    colorConvert,
    getChildNodesByName,
)

class ScreenWidget(widgets.QFrame):
    def __init__(self, parent, uiscale):
        super(ScreenWidget, self).__init__(parent)
        self.jsondata = None
        self.ismovable = False
        self.uiscale = uiscale
        self.setContentsMargins(0, 0, 0, 0)
        self.screen_height = 0
        self.screen_width = 0
        self.presend = []
        self.toggle_selected(False)

    def toggle_selected(self, sel):
        if sel:
            self.setFrameStyle(widgets.QFrame.Panel | widgets.QFrame.StyledPanel)
        else:
            self.setFrameStyle(widgets.QFrame.NoFrame)

    def change_ratio(self, x):
        return

    def initXML(self, xmldata):
        screencolorxml = xmldata.getAttribute("Color")
        self.screencolor = colorConvert(screencolorxml)
        self.screen_width = int(int(xmldata.getAttribute("Width")) / self.uiscale)
        self.screen_height = int(int(xmldata.getAttribute("Height")) / self.uiscale)
        self.setStyleSheet("background-color: %s" % self.screencolor)
        
        # Use full width of scroll area viewport if available, otherwise use XML width
        parent = self.parent()
        if parent:
            # Check if parent is a QScrollArea or has a viewport
            if hasattr(parent, 'viewport'):
                viewport_width = parent.viewport().width()
                if viewport_width > self.screen_width:
                    self.screen_width = viewport_width
            elif hasattr(parent, 'width'):
                parent_width = parent.width()
                if parent_width > self.screen_width:
                    self.screen_width = parent_width
        
        self.resize(self.screen_width, self.screen_height)

        for elem in getChildNodesByName(xmldata, u"Send"):
            delay = elem.getAttribute('Delay')
            req_name = elem.getAttribute('RequestName')
            self.presend.append({'Delay': delay, 'RequestName': req_name})

    def initJson(self, jsdata):
        self.screen_width = int(int(jsdata['width']) / self.uiscale)
        self.screen_height = int(int(jsdata['height']) / self.uiscale)
        self.setStyleSheet("background-color: %s" % jsdata['color'])
        
        # Use full width of scroll area viewport if available, otherwise use JSON width
        parent = self.parent()
        if parent:
            # Check if parent is a QScrollArea or has a viewport
            if hasattr(parent, 'viewport'):
                viewport_width = parent.viewport().width()
                if viewport_width > self.screen_width:
                    self.screen_width = viewport_width
            elif hasattr(parent, 'width'):
                parent_width = parent.width()
                if parent_width > self.screen_width:
                    self.screen_width = parent_width
        
        self.resize(self.screen_width, self.screen_height)
        self.presend = jsdata['presend']
        self.jsondata = jsdata

    def resize(self, x, y):
        super(ScreenWidget, self).resize(int(x), int(y))
        self.update_json()
    
    def resizeEvent(self, event):
        """Handle resize events to maintain full width"""
        super(ScreenWidget, self).resizeEvent(event)
        # Update screen_width to match actual width
        self.screen_width = self.width()
        self.screen_height = self.height()

    def lock(self, lock):
        pass

    def move(self, x, y):
        super(ScreenWidget, self).move(int(x), int(y))
        self.update_json()

    def update_json(self):
        if self.jsondata:
            # TODO : Manage colors and presend commands
            self.jsondata['width'] = self.width() * self.uiscale
            self.jsondata['height'] = self.height() * self.uiscale
