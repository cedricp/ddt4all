import os
import zipfile

import PyQt5.QtCore as core
from PyQt5.QtGui import QIcon, QPixmap
import PyQt5.QtWidgets as widgets

import ddt4all.options as options
from ddt4all.ui.utils import (
    jsonFont,
    getChildNodesByName,
    getRectangleXML,
    getXMLFont,
)

_ = options.translator('ddt4all')

class ButtonRequest(widgets.QPushButton):
    def __init__(self, parent, uiscale, ecureq, count):
        super(ButtonRequest, self).__init__(parent)
        self.jsdata = None
        self.ismovable = True
        self.uiscale = uiscale
        self.ecurequest = ecureq
        self.count = count
        self.messages = []
        self.butname = ""
        self.uniquename = ""
        self.jsondata = None
        self.toggle_selected(False)

    def toggle_selected(self, sel):
        if sel:
            # self.setFrameStyle(widgets.QFrame.Panel | widgets.QFrame.StyledPanel)
            pass
        else:
            # self.setFrameStyle(0)
            pass

    def change_ratio(self, x):
        pass

    def initXML(self, xmldata):
        text = xmldata.getAttribute("Text")
        rect = getRectangleXML(getChildNodesByName(xmldata, "Rectangle")[0], self.uiscale)
        qfnt = getXMLFont(xmldata, self.uiscale)
        self.messages = getChildNodesByName(xmldata, "Message")
        as_picture = False

        if text.upper().startswith("::BTN:"):
            gifName = text.replace("::BTN:|", "").replace("::btn:|", "").replace("::btn:DOWN|", "").replace("::btn:UP|", "").replace("::btn:LEFT|", "").replace("::btn:RIGHT|", "").replace("\\", "/")
            image_data = os.path.join(options.graphics_dir, gifName + '.gif')
            if not os.path.exists(image_data):
                image_data = os.path.join(options.graphics_dir, gifName + '.GIF')
            if os.path.exists(image_data):
                with open(image_data, 'rb') as gif:
                    data = gif.read()
                if data:
                    pixmap = QPixmap()
                    byte_array = core.QByteArray(data)
                    buffer = core.QBuffer(byte_array)
                    buffer.open(core.QIODevice.ReadOnly)
                    pixmap.loadFromData(buffer.readAll())
                    self.setIcon(QIcon(pixmap))
                    self.setIconSize(self.size())
                    as_picture = True
        if not as_picture:
            self.setFont(qfnt)
            self.setText(text)
            self.setStyleSheet("background: yellow; color: black")
        self.resize(rect['width'], rect['height'])
        self.move(rect['left'], rect['top'])
        self.butname = text + "_" + str(self.count)

    def initJson(self, jsdata):
        text = jsdata['text']
        rect = jsdata['rect']
        qfnt = jsonFont(jsdata['font'], self.uiscale)
        self.messages = jsdata['messages']
        as_picture = False

        if text.upper().startswith("::BTN:"):
            gifName = text.replace("::BTN:|", "").replace("::btn:|", "").replace("::btn:DOWN|", "").replace("::btn:UP|", "").replace("::btn:LEFT|", "").replace("::btn:RIGHT|", "").replace("\\", "/")
            if os.path.exists("ecu.zip"):
                image_data = self.extract_image_from_zip('ecu.zip', os.path.join(options.graphics_dir, gifName + '.gif'))
                if image_data is None:
                    image_data = self.extract_image_from_zip('ecu.zip', os.path.join(options.graphics_dir, gifName + '.GIF'))
                if image_data:
                    pixmap = QPixmap()
                    byte_array = core.QByteArray(image_data)
                    buffer = core.QBuffer(byte_array)
                    buffer.open(core.QIODevice.ReadOnly)
                    pixmap.loadFromData(buffer.readAll())
                    self.setIcon(QIcon(pixmap))
                    self.setIconSize(self.size())
                    as_picture = True
        if not as_picture:
            self.setFont(qfnt)
            self.setText(text)
            self.setStyleSheet("background: yellow; color: black")
        self.resize(rect['width'] / self.uiscale, rect['height'] / self.uiscale)
        self.move(rect['left'] / self.uiscale, rect['top'] / self.uiscale)
        self.butname = jsdata['text'] + "_" + str(self.count)
        self.uniquename = jsdata['uniquename']
        self.jsondata = jsdata

    @staticmethod
    def extract_image_from_zip(zip_file, image_name):
        """Extrait une image du fichier ZIP et retourne les données en mémoire"""
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            if image_name in zip_ref.namelist():
                # Lire l'image en mémoire et retourner les données
                return zip_ref.read(image_name)
            else:
                return None

    def mousePressEvent(self, event):
        if options.simulation_mode and options.mode_edit:
            self.parent().mousePressEvent(event)
            return
        return super(ButtonRequest, self).mousePressEvent(event)

    def resize(self, x, y):
        super(ButtonRequest, self).resize(int(x), int(y))
        self.update_json()

    def move(self, x, y):
        super(ButtonRequest, self).move(int(x), int(y))
        self.update_json()

    def update_json(self):
        if self.jsondata:
            self.jsondata['rect']['left'] = self.pos().x() * self.uiscale
            self.jsondata['rect']['top'] = self.pos().y() * self.uiscale
            self.jsondata['rect']['height'] = self.height() * self.uiscale
            self.jsondata['rect']['width'] = self.width() * self.uiscale
