# -*- coding: utf-8 -*-

import PyQt5.QtGui as gui
import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets


def unicode(a):
    return str(a)

import options, os, zipfile
from uiutils import *

__author__ = "Cedric PAILLE"
__copyright__ = "Copyright 2016-2018"
__credits__ = []
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Cedric PAILLE"
__email__ = "cedricpaille@gmail.com"
__status__ = "Beta"

_ = options.translator('ddt4all')

class labelWidget(widgets.QLabel):
    def __init__(self, parent, uiscale):
        super(labelWidget, self).__init__(parent)
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
            if not zname in zf.namelist():
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
                self.img = gui.QMovie(imgname)
            self.setMovie(self.img)
            self.img.start()
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
                self.img = gui.QMovie(imgname)
            self.setMovie(self.img)
            self.img.start()
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
        super(labelWidget, self).resize(x, y)
        self.update_json()

    def move(self, x, y):
        super(labelWidget, self).move(x, y)
        self.update_json()

    def update_json(self):
        if self.jsondata:
            # TODO : Manage colors and presend commands
            self.jsondata['bbox']['width'] = self.width() * self.uiscale
            self.jsondata['bbox']['height'] = self.height() * self.uiscale
            self.jsondata['bbox']['left'] = self.pos().x() * self.uiscale
            self.jsondata['bbox']['top'] = self.pos().y() * self.uiscale


class screenWidget(widgets.QFrame):
    def __init__(self, parent, uiscale):
        super(screenWidget, self).__init__(parent)
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
        self.screen_width = int(xmldata.getAttribute("Width")) / self.uiscale
        self.screen_height = int(xmldata.getAttribute("Height")) / self.uiscale
        self.setStyleSheet("background-color: %s" % self.screencolor)
        self.resize(self.screen_width, self.screen_height)

        for elem in getChildNodesByName(xmldata, u"Send"):
            delay = elem.getAttribute('Delay')
            req_name = elem.getAttribute('RequestName')
            self.presend.append({'Delay': delay, 'RequestName': req_name})

    def initJson(self, jsdata):
        self.screen_width = int(jsdata['width']) / self.uiscale
        self.screen_height = int(jsdata['height']) / self.uiscale
        self.setStyleSheet("background-color: %s" % jsdata['color'])
        self.resize(self.screen_width, self.screen_height)
        self.presend = jsdata['presend']
        self.jsondata = jsdata

    def resize(self, x, y):
        super(screenWidget, self).resize(x, y)
        self.update_json()

    def lock(self, lock):
        pass

    def move(self, x, y):
        return

    def update_json(self):
        if self.jsondata:
            # TODO : Manage colors and presend commands
            self.jsondata['width'] = self.width() * self.uiscale
            self.jsondata['height'] = self.height() * self.uiscale

class buttonRequest(widgets.QPushButton):
    def __init__(self, parent, uiscale, ecureq, count):
        super(buttonRequest, self).__init__(parent)
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
            #self.setFrameStyle(widgets.QFrame.Panel | widgets.QFrame.StyledPanel)
            pass
        else:
            #self.setFrameStyle(0)
            pass

    def change_ratio(self, x):
        pass

    def initXML(self, xmldata):
        text = xmldata.getAttribute("Text")
        rect = getRectangleXML(getChildNodesByName(xmldata, "Rectangle")[0], self.uiscale)
        qfnt = getXMLFont(xmldata, self.uiscale)
        self.messages = getChildNodesByName(xmldata, "Message")
        self.setFont(qfnt)
        self.setText(text)
        self.resize(rect['width'], rect['height'])
        self.setStyleSheet("background: yellow; color: black")
        self.move(rect['left'], rect['top'])
        self.butname = text + "_" + str(self.count)

    def initJson(self, jsdata):
        text = jsdata['text']
        rect = jsdata['rect']
        qfnt = jsonFont(jsdata['font'], self.uiscale)
        self.messages = jsdata['messages']

        self.setFont(qfnt)
        self.setText(text)
        self.resize(rect['width'] / self.uiscale, rect['height'] / self.uiscale)
        self.setStyleSheet("background: yellow; color: black")
        self.move(rect['left'] / self.uiscale, rect['top'] / self.uiscale)
        self.butname = jsdata['text'] + "_" + str(self.count)
        self.uniquename = jsdata['uniquename']
        self.jsondata = jsdata

    def mousePressEvent(self, event):
        if options.simulation_mode and options.mode_edit:
            self.parent().mousePressEvent(event)
            return
        return super(buttonRequest, self).mousePressEvent(event)

    def resize(self, x, y):
        super(buttonRequest, self).resize(x, y)
        self.update_json()

    def move(self, x, y):
        super(buttonRequest, self).move(x, y)
        self.update_json()

    def update_json(self):
        if self.jsondata:
            self.jsondata['rect']['left'] = self.pos().x() * self.uiscale
            self.jsondata['rect']['top'] = self.pos().y() * self.uiscale
            self.jsondata['rect']['height'] = self.height() * self.uiscale
            self.jsondata['rect']['width'] = self.width() * self.uiscale


class styleLabel(widgets.QLabel):
    def __init__(self, parent):
        super(styleLabel, self).__init__(parent)
        self.defaultStyle = ""

    def setDefaultStyle(self, style):
        self.defaultStyle = style
        self.setStyleSheet(self.defaultStyle)

    def resetDefaultStyle(self):
        self.setStyleSheet(self.defaultStyle)

class displayWidget(widgets.QWidget):
    def __init__(self, parent, uiscale, ecureq):
        super(displayWidget, self).__init__(parent)
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
        super(displayWidget, self).resize(x, y)
        newwidth = self.width()

        if not self.qlabelval or not self.qlabel:
            return

        diff = newwidth - oldwidth
        self.qlabel.resize(self.qlabel.width() + diff, self.height())
        self.qlabelval.resize(self.qlabelval.width(), self.height())
        self.qlabelval.move(self.qlabelval.pos().x() + diff, 0)
        self.update_json()

    def move(self, x, y):
        super(displayWidget, self).move(x, y)
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
            print(_("No request named "), req_name)
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
            print("DataItem not found", text)
            return

        try:
            data = self.ecurequestsparser.data[text]
        except:
            print(_("Cannot find data "), text)
            return

        if not color:
            color = 0x55555

        self.move(rect['left'], rect['top'])
        self.resize(rect['width'], rect['height'])

        self.qlabel = widgets.QLabel(self)
        self.qlabel.setFont(qfnt)
        self.qlabel.setText(text)
        self.qlabel.resize(width, rect['height'])
        self.qlabel.setStyleSheet("background-color: %s; color: %s" % (colorConvert(color), getFontColor(display)))
        self.qlabel.setAlignment(core.Qt.AlignLeft)
        self.qlabel.setWordWrap(True)

        self.qlabelval = styleLabel(self)
        self.qlabelval.setFont(qfnt)
        self.qlabelval.setText("")
        self.qlabelval.resize(rect['width'] - width, rect['height'])
        self.qlabelval.setDefaultStyle("background-color: %s; color: %s" % (colorConvert(color), getFontColor(display)))
        self.qlabelval.move(width, 0)

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

        ddata = displayData(data, self.qlabelval)
        if not req_name in displaydict:
            displaydict[req_name] = displayDict(req_name, req)

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
                    print("Found similar", k, " vs ", text)
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
        self.qlabel.resize(width, rect['height'] / self.uiscale)
        self.qlabel.setStyleSheet("background-color: %s; color: %s" % (color, fontcolor))
        self.qlabel.setAlignment(core.Qt.AlignLeft)
        self.qlabel.setWordWrap(True)

        self.qlabelval = styleLabel(self)
        self.qlabelval.setFont(qfnt)
        self.qlabelval.setText("")
        self.qlabelval.resize(rect['width'] / self.uiscale - width, rect['height'] / self.uiscale)
        self.qlabelval.setDefaultStyle("background-color: %s; color: %s" % (color, fontcolor))
        self.qlabelval.move(width, 0)

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

        ddata = displayData(data, self.qlabelval)
        if not req_name in displaydict:
            displaydict[req_name] = displayDict(req_name, req)

        dd = displaydict[req_name]
        dd.addData(ddata)
        self.jsondata = display
        self.toggle_selected(False)

class inputWidget(widgets.QWidget):
    def __init__(self, parent, uiscale, ecureq):
        super(inputWidget, self).__init__(parent)
        self.uiscale = uiscale
        self.ecurequestsparser = ecureq
        self.ismovable = True
        self.qlabel = None
        self.editwidget = None
        self.jsondata = None
        self.locked = False

    def toggle_selected(self, sel):
        if sel:
            self.qlabel.setFrameStyle(widgets.QFrame.Panel | widgets.QFrame.StyledPanel)
        else:
            self.qlabel.setFrameStyle(widgets.QFrame.NoFrame)

    def lock(self, lock):
        self.locked = lock

    def resize(self, x, y):
        oldwidth = self.width()
        super(inputWidget, self).resize(x, y)
        newwidth = self.width()

        if not self.qlabel or not self.editwidget:
            return

        diff = newwidth - oldwidth
        self.qlabel.resize(self.qlabel.width() + diff, self.height())
        self.editwidget.resize(self.editwidget.width(), self.height())
        self.editwidget.move(self.editwidget.pos().x() + diff, 0)
        self.update_json()

    def move(self, x, y):
        super(inputWidget, self).move(x, y)
        self.update_json()

    def update_json(self):
        if self.jsondata:
            scale = float(self.uiscale)
            self.jsondata['width'] = int(self.qlabel.width() * scale)
            self.jsondata['rect']['left'] = int(self.pos().x() * scale)
            self.jsondata['rect']['top'] = int(self.pos().y() * scale)
            self.jsondata['rect']['height'] = int(self.height() * scale)
            self.jsondata['rect']['width'] = int(self.width() * scale)

    def change_ratio(self, x):
        valnewx = self.editwidget.pos().x() + x
        if valnewx < 0:
            return
        if valnewx > self.width():
            return

        oldlabelsize = self.qlabel.width()
        oldvalsize = self.editwidget.width()
        self.qlabel.resize(oldlabelsize + x, self.height())
        self.editwidget.resize(oldvalsize - x, self.height())
        self.editwidget.move(valnewx, 0)
        self.update_json()

    def initXML(self, input, inputdict):
        text = input.getAttribute("DataName")
        req_name = input.getAttribute("RequestName")
        color = input.getAttribute("Color")
        width = int(input.getAttribute("Width")) / self.uiscale
        rect = getRectangleXML(getChildNodesByName(input, "Rectangle")[0], self.uiscale)
        qfnt = getXMLFont(input, self.uiscale)

        if not color:
            color = 0xAAAAAA

        self.resize(rect['width'], rect['height'])
        self.qlabel = widgets.QLabel(self)
        self.qlabel.setWordWrap(True)
        self.qlabel.setFont(qfnt)
        self.qlabel.setText(text)
        self.qlabel.setStyleSheet("background:%s; color:%s" % (colorConvert(color), getFontColor(input)))
        self.qlabel.resize(width, rect['height'])
        self.move(rect['left'], rect['top'])

        try:
            data = self.ecurequestsparser.data[text]
        except:
            print(_("Cannot draw input "), text)
            return

        if len(self.ecurequestsparser.data[text].items) > 0:
            self.editwidget = widgets.QComboBox(self)
            items_ref = self.ecurequestsparser.data[text].items

            for key in sorted(items_ref.keys()):
                self.editwidget.addItem(key)

            self.editwidget.resize(rect['width'] - width, rect['height'])
            self.editwidget.move(width, 0)
            if data.comment:
                infos = data.comment + u'\n' + req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
            else:
                infos = req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)

            self.editwidget.setToolTip(infos)
            self.editwidget.setStyleSheet("background:%s; color:%s" % (colorConvert(color), getFontColor(input)))
            ddata = displayData(data, self.editwidget, True)
        else:
            self.editwidget = widgets.QLineEdit(self)
            if options.simulation_mode and options.mode_edit:
                self.editwidget.setEnabled(False)
            self.editwidget.setFont(qfnt)
            self.editwidget.setText(_("No Value"))
            self.editwidget.resize(rect['width'] - width, rect['height'])
            self.editwidget.setStyleSheet("background:%s; color:%s" % (colorConvert(color), getFontColor(input)))
            self.editwidget.move(width, 0)
            if data.comment:
                infos = data.comment + u'\n' + req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
            else:
                infos = req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
            self.editwidget.setToolTip(infos)
            ddata = displayData(data, self.editwidget)

        if not req_name in inputdict:
            req = self.ecurequestsparser.requests[req_name]
            inputdict[req_name] = displayDict(req_name, req)

        dd = inputdict[req_name]
        dd.addData(ddata)
        self.toggle_selected(False)

    def initJson(self, jsoninput, inputdict):
        text = jsoninput['text']
        req_name = jsoninput['request']
        color = jsoninput['color']
        width = jsoninput['width'] / self.uiscale
        rect = jsoninput['rect']
        qfnt = jsonFont(jsoninput['font'], self.uiscale)
        fntcolor = jsoninput['fontcolor']

        self.move(rect['left'] / self.uiscale, rect['top'] / self.uiscale)
        self.resize(rect['width'] / self.uiscale, rect['height'] / self.uiscale)

        self.qlabel = widgets.QLabel(self)
        self.qlabel.setFont(qfnt)
        self.qlabel.setText(text)
        self.qlabel.setStyleSheet("background:%s; color:%s" % (color, jsoninput))
        self.qlabel.setWordWrap(True)
        self.qlabel.resize(width, rect['height'] / self.uiscale)

        if not text in self.ecurequestsparser.data:
            print(_("Cannot find data "), text)
            return
        data = self.ecurequestsparser.data[text]

        if len(self.ecurequestsparser.data[text].items) > 0:
            self.editwidget = widgets.QComboBox(self)
            items_ref = self.ecurequestsparser.data[text].items

            for key in sorted(items_ref.keys()):
                self.editwidget.addItem(key)


            self.editwidget.move(width, 0)
            if data.comment:
                infos = data.comment + u'\n' + req_name + u' : ' + text + u'\nNumBits=' + unicode(
                    data.bitscount)
            else:
                infos = req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)

            self.editwidget.setToolTip(infos)
            self.editwidget.setStyleSheet(
                "background:%s; color:%s" % (color, fntcolor))

            ddata = displayData(data, self.editwidget, True)
        else:
            self.editwidget = widgets.QLineEdit(self)

            self.editwidget.setFont(qfnt)
            self.editwidget.setText("No Value")
            self.editwidget.setStyleSheet(
                "background:%s; color:%s" % (color, fntcolor))
            if data.comment:
                infos = data.comment + u'\n' + req_name + u' : ' + text + u'\nNumBits=' + unicode(
                    data.bitscount)
            else:
                infos = req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
            self.editwidget.setToolTip(infos)
            ddata = displayData(data, self.editwidget)

        if options.simulation_mode and options.mode_edit:
            self.editwidget.setEnabled(False)

        self.editwidget.resize(rect['width'] / self.uiscale - width, rect['height'] / self.uiscale)
        self.editwidget.move(width, 0)

        if not req_name in inputdict:
            req = self.ecurequestsparser.requests[req_name]
            inputdict[req_name] = displayDict(req_name, req)

        dd = inputdict[req_name]
        dd.addData(ddata)

        self.jsondata = jsoninput
        self.toggle_selected(False)
