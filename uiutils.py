# -*- coding: utf-8 -*-
try:
    import PyQt5.QtGui as gui
except:
    import PyQt4.QtGui as gui

__author__ = "Cedric PAILLE"
__copyright__ = "Copyright 2016-2018"
__credits__ = []
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Cedric PAILLE"
__email__ = "cedricpaille@gmail.com"
__status__ = "Beta"


def getChildNodesByName(parent, name):
    nodes = []
    for node in parent.childNodes:
        if node.nodeType == node.ELEMENT_NODE and node.localName == name:
            nodes.append(node)
    return nodes


def colorConvert(color):
    hexcolor = hex(int(color) & 0xFFFFFF)[2:].upper().zfill(6)
    redcolor = int('0x' + hexcolor[0:2], 16)
    greencolor = int('0x' + hexcolor[2:4], 16)
    bluecolor = int('0x' + hexcolor[4:6], 16)
    return 'rgb(%i,%i,%i)' % (bluecolor, greencolor, redcolor)


def getRectangleXML(xml, scale=1):
    rect = {}
    rect['left'] = int(float(xml.getAttribute("Left")) / float(scale))
    rect['top'] = int(float(xml.getAttribute("Top")) / float(scale))
    rect['height'] = int(float(xml.getAttribute("Height")) / float(scale))
    rect['width'] = int(float(xml.getAttribute("Width")) / float(scale))
    return rect


def getFontColor(xml):
    font = getChildNodesByName(xml, "Font")[0]
    if font.getAttribute("Color"):
        return colorConvert(font.getAttribute("Color"))
    else:
        return colorConvert(0xAAAAAA)


def getFontXML(xml):
    f = {}
    font = getChildNodesByName(xml, "Font")[0]
    f['name'] = font.getAttribute("Name")
    f['size'] = float(font.getAttribute("Size").replace(',', '.'))
    f['bold'] = font.getAttribute("Bold")
    f['italic'] = font.getAttribute("Italic")
    return f


def getXMLFont(xml, scale = 1):
    font = getChildNodesByName(xml, "Font")[0]
    font_name = font.getAttribute("Name")
    font_size = float(font.getAttribute("Size").replace(',', '.'))
    font_bold = font.getAttribute("Bold")
    font_italic = font.getAttribute("Italic")

    if font_bold == '1':
        fnt_flags = gui.QFont.Bold
    else:
        fnt_flags = gui.QFont.Normal

    if font_italic == '1':
        fnt_flags |= gui.QFont.StyleItalic

    font_size = font_size / float(scale) * 14.
    qfnt = gui.QFont(font_name, font_size, fnt_flags)
    qfnt.setPixelSize(font_size)
    return qfnt


def getFontColor(xml):
    font = getChildNodesByName(xml, "Font")[0]
    if font.getAttribute("Color"):
        return colorConvert(font.getAttribute("Color"))
    else:
        return colorConvert(0xFFFFFF)


class displayData:
    def __init__(self, data, widget, is_combo=False):
        self.data    = data
        self.widget  = widget
        self.is_combo = is_combo


class displayDict:
    def __init__(self, request_name, request):
        self.request = request
        self.request_name = request_name
        self.data    = []
        self.datadict = {}

    def addData(self, displaydata):
        self.data.append(displaydata)
        if not displaydata.data.name in self.datadict:
            self.datadict[displaydata.data.name] = displaydata

    def getDataByName(self, name):
        for data in self.data:
            if data.data.name == name:
                return data
        return None


def jsonFont(fnt, scale):
    font_name = fnt['name']
    font_size = fnt['size']
    if 'bold' in fnt:
        font_bold = fnt['bold']
    else:
        font_bold = '0'
    if 'italic' in fnt:
        font_italic = fnt['italic']
    else:
        font_italic = '0'

    if font_bold == '1':
        fnt_flags = gui.QFont.Bold
    else:
        fnt_flags = gui.QFont.Normal

    if font_italic == '1':
        fnt_flags |= gui.QFont.StyleItalic

    font_size = font_size / float(scale) * 14.

    qfnt = gui.QFont(font_name, font_size, fnt_flags);
    qfnt.setPixelSize(font_size)
    return qfnt
