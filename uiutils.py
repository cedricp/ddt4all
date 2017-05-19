import PyQt4.QtGui as gui

def getChildNodesByName(parent, name):
    nodes = []
    for node in parent.childNodes:
        if node.nodeType == node.ELEMENT_NODE and node.localName == name:
            nodes.append(node)
    return nodes


def colorConvert(color):
    hexcolor = hex(int(color) & 0xFFFFFF).replace("0x", "").upper().zfill(6)
    redcolor = int('0x' + hexcolor[0:2], 16)
    greencolor = int('0x' + hexcolor[2:4], 16)
    bluecolor = int('0x' + hexcolor[4:6], 16)
    return 'rgb(%i,%i,%i)' % (bluecolor, greencolor, redcolor)


def getRectangleXML(xml, scale = 1):
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
    f['size'] = float(font.getAttribute("Size"))
    f['bold'] = font.getAttribute("Bold")
    f['italic'] = font.getAttribute("Italic")
    return f


def getXMLFont(xml, scale = 1):
    font = getChildNodesByName(xml, "Font")[0]
    font_name = font.getAttribute("Name")
    font_size = float(font.getAttribute("Size"))
    font_bold = font.getAttribute("Bold")
    font_italic = font.getAttribute("Italic")

    if font_bold == '1':
        fnt_flags = gui.QFont.Bold
    else:
        fnt_flags = gui.QFont.Normal

    if font_italic == '1':
        fnt_flags |= gui.QFont.StyleItalic

    font_size = font_size / float(scale) * 10.
    qfnt = gui.QFont(font_name, font_size, fnt_flags);

    return qfnt


def colorConvert(color):
    hexcolor = hex(int(color) & 0xFFFFFF).replace("0x", "").upper().zfill(6)
    redcolor = int('0x' + hexcolor[0:2], 16)
    greencolor = int('0x' + hexcolor[2:4], 16)
    bluecolor = int('0x' + hexcolor[4:6], 16)
    return 'rgb(%i,%i,%i)' % (bluecolor, greencolor, redcolor)


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


def jsonFont(fnt):
    font_name = fnt['name']
    font_size = fnt['size']
    font_bold = fnt['bold']
    font_italic = fnt['italic']

    if font_bold == '1':
        fnt_flags = gui.QFont.Bold
    else:
        fnt_flags = gui.QFont.Normal

    if font_italic == '1':
        fnt_flags |= gui.QFont.StyleItalic

    qfnt = gui.QFont(font_name, font_size, fnt_flags);

    return qfnt