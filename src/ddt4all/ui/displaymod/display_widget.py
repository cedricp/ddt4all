import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets

import ddt4all.options as options
from ddt4all.ui.display_data import DisplayData
from ddt4all.ui.display_dict import DisplayDict
from ddt4all.ui.displaymod.style_label import StyleLabel
from ddt4all.ui.utils import (
    colorConvert,
    jsonFont,
    getChildNodesByName,
    getFontColor,
    getRectangleXML,
    getXMLFont,
    unicode,
)

_ = options.translator('ddt4all')

class DisplayWidget(widgets.QWidget):

    def __init__(self, parent, uiscale, ecureq):
        super(DisplayWidget, self).__init__(parent)
        self.uiscale = uiscale
        self.ecurequestsparser = ecureq
        self.ismovable = True
        self.qlabel = None
        self.qlabelval = None
        self.jsondata = None

    def toggle_selected(self, sel):
        if sel:
            self.qlabel.setFrameStyle(widgets.QFrame.Panel | widgets.QFrame.StyledPanel)
            self.qlabelval.setFrameStyle(widgets.QFrame.Panel | widgets.QFrame.StyledPanel)
        else:
            self.qlabel.setFrameStyle(widgets.QFrame.NoFrame)
            self.qlabelval.setFrameStyle(widgets.QFrame.Panel | widgets.QFrame.Sunken)

    def lock(self, lock):
        pass

    def resize(self, x, y):
        oldwidth = self.width()
        super(DisplayWidget, self).resize(int(x), int(y))
        newwidth = self.width()

        if not self.qlabelval or not self.qlabel:
            return

        diff = newwidth - oldwidth
        self.qlabel.resize(self.qlabel.width() + diff, self.height())
        self.qlabelval.resize(self.qlabelval.width(), self.height())
        self.qlabelval.move(self.qlabelval.pos().x() + diff, 0)
        self.update_json()

    def move(self, x, y):
        super(DisplayWidget, self).move(int(x), int(y))
        self.update_json()

    def update_json(self):
        if self.jsondata:
            self.jsondata['width'] = self.qlabel.width() * self.uiscale
            self.jsondata['rect']['left'] = self.pos().x() * self.uiscale
            self.jsondata['rect']['top'] = self.pos().y() * self.uiscale
            self.jsondata['rect']['height'] = self.height() * self.uiscale
            self.jsondata['rect']['width'] = self.width() * self.uiscale

    def change_ratio(self, x):
        valnewx = self.qlabelval.pos().x() + x
        if valnewx < 0:
            return
        if valnewx > self.width():
            return

        oldlabelsize = self.qlabel.width()
        oldvalsize = self.qlabelval.width()
        self.qlabel.resize(oldlabelsize + x, self.height())
        self.qlabelval.resize(oldvalsize - x, self.height())
        self.qlabelval.move(valnewx, 0)
        self.update_json()

    def initXML(self, display, displaydict):
        text = display.getAttribute("DataName")
        req_name = display.getAttribute("RequestName")
        color = display.getAttribute("Color")
        width = int(display.getAttribute("Width")) / self.uiscale
        rect = getRectangleXML(getChildNodesByName(display, "Rectangle")[0], self.uiscale)
        qfnt = getXMLFont(display, self.uiscale)
        if req_name not in self.ecurequestsparser.requests:
            print(_("No request named"), req_name)
            return
        req = self.ecurequestsparser.requests[req_name]
        dataitem = None
        if text in req.dataitems:
            dataitem = req.dataitems[text]
        else:
            keys = req.dataitems.keys()
            for k in keys:
                if k.upper() == text.upper():
                    dataitem = req.dataitems[k]
                    print(_("Found similar"), k, " vs ", text)
                    break

        if not dataitem:
            print(_("DataItem not found"), text)
            return

        try:
            data = self.ecurequestsparser.data[text]
        except Exception:
            print(_("Cannot find data "), text)
            return

        if not color:
            color = 0x55555

        self.move(rect['left'], rect['top'])
        self.resize(rect['width'], rect['height'])

        self.qlabel = widgets.QLabel(self)
        self.qlabel.setFont(qfnt)
        self.qlabel.setText(text)
        self.qlabel.resize(int(width), rect['height'])
        self.qlabel.setStyleSheet("background-color: %s; color: %s" % (colorConvert(color), getFontColor(display)))
        self.qlabel.setAlignment(core.Qt.AlignLeft)
        self.qlabel.setWordWrap(True)

        self.qlabelval = StyleLabel(self)
        self.qlabelval.setFont(qfnt)
        self.qlabelval.setText("")
        self.qlabelval.resize(rect['width'] - int(width), rect['height'])
        self.qlabelval.setDefaultStyle("background-color: %s; color: %s" % (colorConvert(color), getFontColor(display)))
        self.qlabelval.move(int(width), 0)

        endianess = req.ecu_file.endianness
        if dataitem.endian != "":
            endianess = dataitem.endian
        infos = req_name + u'\n'

        if data.comment:
            infos += data.comment + u'\n'

        infos += u"Request=" + unicode(req.sentbytes) + u' ManualRequest=' + unicode(req.manualsend)
        infos += u'\nNumBits=' + unicode(data.bitscount)
        infos += u' FirstByte=' + unicode(dataitem.firstbyte)
        infos += u' BitOffset=' + unicode(dataitem.bitoffset)
        infos += u' Endianess=' + unicode(endianess)
        self.qlabelval.setToolTip(infos)

        ddata = DisplayData(data, self.qlabelval)
        if req_name not in displaydict:
            displaydict[req_name] = DisplayDict(req_name, req)

        dd = displaydict[req_name]
        dd.addData(ddata)
        self.toggle_selected(False)

    def initJson(self, display, displaydict):
        text = display['text']
        req_name = display['request']
        color = display['color']
        width = display['width'] / self.uiscale
        rect = display['rect']
        qfnt = jsonFont(display['font'], self.uiscale)
        fontcolor = display['fontcolor']

        req = self.ecurequestsparser.requests[req_name]
        dataitem = None
        if text in req.dataitems:
            dataitem = req.dataitems[text]
        else:
            keys = req.dataitems.keys()
            for k in keys:
                if k.upper() == text.upper():
                    dataitem = req.dataitems[k]
                    print(_("Found similar"), k, _(" vs "), text)
                    break

        if not dataitem:
            print(_("DataItem not found"), text)
            return

        data = self.ecurequestsparser.data[text]

        self.move(rect['left'] / self.uiscale, rect['top'] / self.uiscale)
        self.resize(rect['width'] / self.uiscale, rect['height'] / self.uiscale)

        self.qlabel = widgets.QLabel(self)
        self.qlabel.setFont(qfnt)
        self.qlabel.setText(text)
        self.qlabel.resize(int(width), int(rect['height'] / self.uiscale))
        self.qlabel.setStyleSheet("background-color: %s; color: %s" % (color, fontcolor))
        self.qlabel.setAlignment(core.Qt.AlignLeft)
        self.qlabel.setWordWrap(True)

        self.qlabelval = StyleLabel(self)
        self.qlabelval.setFont(qfnt)
        self.qlabelval.setText("")
        self.qlabelval.resize(int(rect['width'] / self.uiscale - width), int(rect['height'] / self.uiscale))
        self.qlabelval.setDefaultStyle("background-color: %s; color: %s" % (color, fontcolor))
        self.qlabelval.move(int(width), 0)

        infos = req_name + u'\n'
        if data.comment:
            infos += data.comment + u'\n'

        endianess = req.ecu_file.endianness
        if dataitem.endian != "":
            endianess = dataitem.endian

        infos += u"Request=" + unicode(req.sentbytes) + u' ManualRequest=' + unicode(req.manualsend)
        infos += u'\nNumBits=' + unicode(data.bitscount)
        infos += u' FirstByte=' + unicode(dataitem.firstbyte)
        infos += u' BitOffset=' + unicode(dataitem.bitoffset)
        infos += u' Endianess=' + unicode(endianess)
        self.qlabelval.setToolTip(infos)

        ddata = DisplayData(data, self.qlabelval)
        if req_name not in displaydict:
            displaydict[req_name] = DisplayDict(req_name, req)

        dd = displaydict[req_name]
        dd.addData(ddata)
        self.jsondata = display
        self.toggle_selected(False)
