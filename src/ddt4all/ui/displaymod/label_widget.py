import os
import zipfile

import PyQt5.QtCore as core
import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

import ddt4all.options as options
from ddt4all.ui.utils import (
    colorConvert,
    jsonFont,
    getChildNodesByName,
    getFontColor,
    getRectangleXML,
    getXMLFont,
)

_ = options.translator('ddt4all')

class LabelWidget(widgets.QLabel):
    def __init__(self, parent, uiscale):
        super(LabelWidget, self).__init__(parent)
        self.buffer = None
        self.jsondata = None
        self.ismovable = True
        self.uiscale = uiscale
        self.toggle_selected(False)
        self.setWordWrap(True)
        self.img = None
        self.area = 0

    def toggle_selected(self, sel):
        if sel:
            self.setFrameStyle(widgets.QFrame.Panel | widgets.QFrame.StyledPanel)
        else:
            self.setFrameStyle(widgets.QFrame.NoFrame)

    def change_ratio(self, x):
        return

    def get_zip_graphic(self, name):
        if os.path.exists("ecu.zip"):
            zf = zipfile.ZipFile("ecu.zip", "r")
            zname = "graphics/" + name + ".gif"
            if zname not in zf.namelist():
                zname = "graphics/" + name + ".GIF"
            if zname in zf.namelist():
                ba = core.QByteArray(zf.read(zname))
                self.buffer = core.QBuffer()
                self.buffer.setData(ba)
                self.buffer.open(core.QIODevice.ReadOnly)
                self.img = gui.QMovie(self.buffer, b"gif")

    def initXML(self, xmldata):
        text = xmldata.getAttribute("Text")
        color = xmldata.getAttribute("Color")
        alignment = xmldata.getAttribute("Alignment")

        if text.startswith("::pic:"):
            self.setScaledContents(True)
            img_name = text.replace("::pic:", "").replace("\\", "/")
            self.get_zip_graphic(img_name)
            if self.img is None:
                imgname = os.path.join(options.graphics_dir, img_name) + ".gif"
                if not os.path.exists(imgname):
                    imgname = os.path.join(options.graphics_dir, img_name) + ".GIF"
                # Ensure the path is a string and the file exists
                if isinstance(imgname, str) and os.path.exists(imgname):
                    self.img = gui.QMovie(imgname)
            if self.img.isValid():
                self.setMovie(self.img)
                self.img.start()
            else:
                self.setText(text)
        else:
            self.setText(text)

        rect = getRectangleXML(getChildNodesByName(xmldata, "Rectangle")[0], self.uiscale)
        qfnt = getXMLFont(xmldata, self.uiscale)

        self.area = rect['width'] * rect['height']
        self.setFont(qfnt)
        self.resize(rect['width'], rect['height'])
        self.setStyleSheet("background: %s; color: %s" % (colorConvert(color), getFontColor(xmldata)))

        self.move(rect['left'], rect['top'])
        if alignment == '2':
            self.setAlignment(core.Qt.AlignHCenter)
        elif alignment == '1':
            self.setAlignment(core.Qt.AlignRight)
        else:
            self.setAlignment(core.Qt.AlignLeft)

    def initJson(self, jsdata):
        text = jsdata['text']
        color = jsdata['color']
        alignment = jsdata['alignment']
        fontcolor = jsdata['fontcolor']

        rect = jsdata['bbox']
        self.area = rect['width'] * rect['height']
        qfnt = jsonFont(jsdata['font'], self.uiscale)

        self.ismovable = True
        self.setFont(qfnt)

        if text.startswith("::pic:"):
            self.setScaledContents(True)
            img_name = text.replace("::pic:", "").replace("\\", "/")
            self.get_zip_graphic(img_name)
            if self.img is None:
                imgname = os.path.join(options.graphics_dir, img_name) + ".gif"
                if not os.path.exists(imgname):
                    imgname = os.path.join(options.graphics_dir, img_name) + ".GIF"
                # Ensure the path is a string and the file exists
                if isinstance(imgname, str) and os.path.exists(imgname):
                    self.img = gui.QMovie(imgname)
            if self.img.isValid():
                self.setMovie(self.img)
                self.img.start()
            else:
                self.setText(text)
        else:
            self.setText(text)

        self.resize(rect['width'] / self.uiscale, rect['height'] / self.uiscale)
        self.setStyleSheet("background: %s; color: %s" % (color, fontcolor))

        self.move(rect['left'] / self.uiscale, rect['top'] / self.uiscale)
        if alignment == '2':
            self.setAlignment(core.Qt.AlignHCenter)
        elif alignment == '1':
            self.setAlignment(core.Qt.AlignRight)
        else:
            self.setAlignment(core.Qt.AlignLeft)

        self.jsondata = jsdata

    def resize(self, x, y):
        super(LabelWidget, self).resize(int(x), int(y))
        self.update_json()

    def move(self, x, y):
        super(LabelWidget, self).move(int(x), int(y))
        self.update_json()

    def update_json(self):
        if self.jsondata:
            # TODO : Manage colors and presend commands
            self.jsondata['bbox']['width'] = self.width() * self.uiscale
            self.jsondata['bbox']['height'] = self.height() * self.uiscale
            self.jsondata['bbox']['left'] = self.pos().x() * self.uiscale
            self.jsondata['bbox']['top'] = self.pos().y() * self.uiscale
