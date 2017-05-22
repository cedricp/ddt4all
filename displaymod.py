import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import options
from uiutils import *

class screenWidget(gui.QFrame):
    def __init__(self, parent, uiscale):
        super(screenWidget, self).__init__(parent)
        self.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken)

        self.setStyleSheet("background-color: red")
        self.jsondata = None
        self.ismovable = True
        self.uiscale = uiscale
        self.setContentsMargins(0, 0, 0, 0)
        self.screen_height = 0
        self.screen_width = 0
        self.presend = []

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
            self.presend.append((delay, req_name))

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

    def move(self, x, y):
        return

    def update_json(self):
        if self.jsondata:
            # TODO : Manage colors and presend commands
            self.jsondata['width'] = self.width() * self.uiscale
            self.jsondata['height'] = self.height() * self.uiscale

class buttonRequest(gui.QPushButton):
    def __init__(self, parent, uiscale, ecureq, count):
        super(buttonRequest, self).__init__(parent)
        self.jsdata = None
        self.ismovable = True
        self.uiscale = uiscale
        self.ecurequest = ecureq
        self.count = count
        self.messages = []
        self.butname = ""
        self.jsondata = None

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
        self.setStyleSheet("background: red; color: black")
        self.move(rect['left'], rect['top'])
        self.butname = text + "_" + str(self.count)

    def initJson(self, jsdata):
        text = jsdata['text']
        rect = jsdata['rect']
        qfnt = jsonFont(jsdata['font'])
        self.messages = jsdata['messages']

        self.setFont(qfnt)
        self.setText(text)
        self.resize(rect['width'] / self.uiscale, rect['height'] / self.uiscale)
        self.setStyleSheet("background: red; color: black")
        self.move(rect['left'] / self.uiscale, rect['top'] / self.uiscale)
        self.butname = text + "_" + str(self.count)
        self.jsondata = jsdata

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

class displayValue(gui.QWidget):
    def __init__(self, parent, uiscale, ecureq):
        super(displayValue, self).__init__(parent)
        self.uiscale = uiscale
        self.ecurequestsparser = ecureq
        self.ismovable = True
        self.qlabel = None
        self.qlabelval = None
        self.jsondata = None

    def resize(self,x ,y):
        oldwidth = self.width()
        super(displayValue, self).resize(x, y)
        newwidth = self.width()

        if not self.qlabelval or not self.qlabel:
            return

        diff = newwidth - oldwidth
        self.qlabel.resize(self.qlabel.width() + diff, self.height())
        self.qlabelval.resize(self.qlabelval.width(), self.height())
        self.qlabelval.move(self.qlabelval.pos().x() + diff, 0)
        self.update_json()

    def move(self, x, y):
        super(displayValue, self).move(x, y)
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
            print "No request named ", req_name
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
                    print "Found similar", k, " vs ", text
                    break

        if not dataitem:
            print "DataItem not found", text
            return

        try:
            data = self.ecurequestsparser.data[text]
        except:
            print "Cannot find data ", text
            return

        if not color:
            color = 0xAAAAAA

        self.move(rect['left'], rect['top'])
        self.resize(rect['width'], rect['height'])

        self.qlabel = gui.QLabel(self)
        self.qlabel.setFont(qfnt)
        self.qlabel.setText(text)
        self.qlabel.resize(width, rect['height'])
        self.qlabel.setStyleSheet("background: %s; color: %s" % (colorConvert(color), getFontColor(display)))
        self.qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken)
        self.qlabel.setAlignment(core.Qt.AlignLeft)

        self.qlabelval = gui.QLabel(self)
        self.qlabelval.setFont(qfnt)
        self.qlabelval.setText("")
        self.qlabelval.resize(rect['width'] - width, rect['height'])
        self.qlabelval.setStyleSheet("background: %s; color: %s" % (colorConvert(color), getFontColor(display)))
        self.qlabelval.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken)
        self.qlabelval.move(width, 0)

        endianess = req.endian
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

    def initJson(self, display, displaydict):
        text = display['text']
        req_name = display['request']
        color = display['color']
        width = display['width'] / self.uiscale
        rect = display['rect']
        qfnt = jsonFont(display['font'])
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
                    print "Found similar", k, " vs ", text
                    break

        if not dataitem:
            print "DataItem not found", text
            return

        data = self.ecurequestsparser.data[text]

        self.move(rect['left'] / self.uiscale, rect['top'] / self.uiscale)
        self.resize(rect['width'] / self.uiscale, rect['height'] / self.uiscale)

        self.qlabel = gui.QLabel(self)
        self.qlabel.setFont(qfnt)
        self.qlabel.setText(text)
        self.qlabel.resize(width, rect['height'] / self.uiscale)
        self.qlabel.setStyleSheet("background: %s; color: %s" % (color, fontcolor))
        self.qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
        self.qlabel.setAlignment(core.Qt.AlignLeft)

        self.qlabelval = gui.QLabel(self)
        self.qlabelval.setFont(qfnt)
        self.qlabelval.setText("")
        self.qlabelval.resize(rect['width'] / self.uiscale - width, rect['height'] / self.uiscale)
        self.qlabelval.setStyleSheet("background: %s; color: %s" % (color, fontcolor))
        self.qlabelval.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
        self.qlabelval.move(width, 0)
        infos = req_name + u'\n'
        if data.comment:
            infos += data.comment + u'\n'
        infos += u"Request=" + unicode(req.sentbytes) + u' ManualRequest=' + unicode(req.manualsend)
        infos += u'\nNumBits=' + unicode(data.bitscount)
        infos += u' FirstByte=' + unicode(dataitem.firstbyte)
        infos += u' BitOffset=' + unicode(dataitem.bitoffset)
        self.qlabelval.setToolTip(infos)

        ddata = displayData(data, self.qlabelval)
        if not req_name in displaydict:
            displaydict[req_name] = displayDict(req_name, req)

        dd = displaydict[req_name]
        dd.addData(ddata)
        self.jsondata = display

class inputValue(gui.QWidget):
    def __init__(self, parent, uiscale, ecureq):
        super(inputValue, self).__init__(parent)
        self.uiscale = uiscale
        self.ecurequestsparser = ecureq
        self.ismovable = True
        self.qlabel = None
        self.editwidget = None
        self.jsondata = None

    def resize(self, x, y):
        oldwidth = self.width()
        super(inputValue, self).resize(x, y)
        newwidth = self.width()

        if not self.qlabel or not self.editwidget:
            return

        diff = newwidth - oldwidth
        self.qlabel.resize(self.qlabel.width() + diff, self.height())
        self.editwidget.resize(self.editwidget.width(), self.height())
        self.editwidget.move(self.editwidget.pos().x() + diff, 0)
        self.update_json()

    def move(self, x, y):
        super(inputValue, self).move(x, y)
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
        self.qlabel = gui.QLabel(self)
        self.qlabel.setFont(qfnt)
        self.qlabel.setText(text)
        self.qlabel.setStyleSheet("background:%s; color:%s" % (colorConvert(color), getFontColor(input)))
        self.qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken)
        self.qlabel.resize(width, rect['height'])
        self.move(rect['left'], rect['top'])

        try:
            data = self.ecurequestsparser.data[text]
        except:
            print "Cannot draw input ", text
            return

        if len(self.ecurequestsparser.data[text].items) > 0:
            self.editwidget = gui.QComboBox(self)
            items_ref = self.ecurequestsparser.data[text].items

            for key in items_ref.keys():
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
            self.editwidget = gui.QLineEdit(self)
            if options.simulation_mode:
                self.editwidget.setEnabled(False)
            self.editwidget.setFont(qfnt)
            self.editwidget.setText("No Value")
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

    def initJson(self, jsoninput, inputdict):
        text = jsoninput['text']
        req_name = jsoninput['request']
        color = jsoninput['color']
        width = jsoninput['width'] / self.uiscale
        rect = jsoninput['rect']
        qfnt = jsonFont(jsoninput['font'])
        fntcolor = jsoninput['fontcolor']

        self.move(rect['left'] / self.uiscale, rect['top'] / self.uiscale)
        self.resize(rect['width'] / self.uiscale, rect['height'] / self.uiscale)

        self.qlabel = gui.QLabel(self)
        self.qlabel.setFont(qfnt)
        self.qlabel.setText(text)
        self.qlabel.setStyleSheet("background:%s; color:%s" % (color, jsoninput))
        self.qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken)
        self.qlabel.resize(width, rect['height'] / self.uiscale)

        data = self.ecurequestsparser.data[text]

        if len(self.ecurequestsparser.data[text].items) > 0:
            self.editwidget = gui.QComboBox(self)
            items_ref = self.ecurequestsparser.data[text].items

            for key in items_ref.keys():
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
            self.editwidget = gui.QLineEdit(self)

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

        if options.simulation_mode:
            self.editwidget.setEnabled(False)

        self.editwidget.resize(rect['width'] / self.uiscale - width, rect['height'] / self.uiscale)
        self.editwidget.move(width, 0)

        if not req_name in inputdict:
            req = self.ecurequestsparser.requests[req_name]
            inputdict[req_name] = displayDict(req_name, req)

        dd = inputdict[req_name]
        dd.addData(ddata)

        self.jsondata = jsoninput
