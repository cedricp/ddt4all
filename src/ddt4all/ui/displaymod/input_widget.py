import PyQt5.QtWidgets as widgets

import ddt4all.options as options
from ddt4all.ui.display_data import DisplayData
from ddt4all.ui.display_dict import DisplayDict
from ddt4all.ui.utils import (
    getRectangleXML,
    getChildNodesByName,
    getXMLFont,
    colorConvert,
    unicode,
    getFontColor,
    jsonFont
)

_ = options.translator('ddt4all')

class InputWidget(widgets.QWidget):
    def __init__(self, parent, uiscale, ecureq):
        super(InputWidget, self).__init__(parent)
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
        super(InputWidget, self).resize(int(x), int(y))
        newwidth = self.width()

        if not self.qlabel or not self.editwidget:
            return

        diff = newwidth - oldwidth
        self.qlabel.resize(self.qlabel.width() + diff, self.height())
        self.editwidget.resize(self.editwidget.width(), self.height())
        self.editwidget.move(self.editwidget.pos().x() + diff, 0)
        self.update_json()

    def move(self, x, y):
        super(InputWidget, self).move(int(x), int(y))
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
        self.qlabel.resize(int(width), int(rect['height']))
        self.move(rect['left'], rect['top'])

        try:
            data = self.ecurequestsparser.data[text]
        except Exception:
            print(_("Cannot draw input "), text)
            return

        if len(self.ecurequestsparser.data[text].items) > 0:
            self.editwidget = widgets.QComboBox(self)
            items_ref = self.ecurequestsparser.data[text].items

            for key in sorted(items_ref.keys()):
                self.editwidget.addItem(key)

            self.editwidget.resize(rect['width'] - int(width), rect['height'])
            self.editwidget.move(int(width), 0)
            if data.comment:
                infos = data.comment + u'\n' + req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
            else:
                infos = req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)

            self.editwidget.setToolTip(infos)
            self.editwidget.setStyleSheet("background:%s; color:%s" % (colorConvert(color), getFontColor(input)))
            ddata = DisplayData(data, self.editwidget, True)
        else:
            self.editwidget = widgets.QLineEdit(self)
            if options.simulation_mode and options.mode_edit:
                self.editwidget.setEnabled(False)
            self.editwidget.setFont(qfnt)
            self.editwidget.setText(_("No Value"))
            self.editwidget.resize(rect['width'] - int(width), rect['height'])
            self.editwidget.setStyleSheet("background:%s; color:%s" % (colorConvert(color), getFontColor(input)))
            self.editwidget.move(int(width), 0)
            if data.comment:
                infos = data.comment + u'\n' + req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
            else:
                infos = req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
            self.editwidget.setToolTip(infos)
            ddata = DisplayData(data, self.editwidget)

        if req_name not in inputdict:
            req = self.ecurequestsparser.requests[req_name]
            inputdict[req_name] = DisplayDict(req_name, req)

        dd = inputdict[req_name]
        dd.addData(ddata)
        self.toggle_selected(False)

    def initJson(self, jsoninput, inputdict):
        text = jsoninput['text']
        req_name = jsoninput['request']
        color = jsoninput['color']
        width = int(jsoninput['width'] / self.uiscale)
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
        self.qlabel.resize(int(width), int(rect['height'] / self.uiscale))

        if text not in self.ecurequestsparser.data:
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

            ddata = DisplayData(data, self.editwidget, True)
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
            ddata = DisplayData(data, self.editwidget)

        if options.simulation_mode and options.mode_edit:
            self.editwidget.setEnabled(False)

        self.editwidget.resize(int(rect['width'] / self.uiscale - width), int(rect['height'] / self.uiscale))
        self.editwidget.move(int(width), 0)

        if req_name not in inputdict:
            req = self.ecurequestsparser.requests[req_name]
            inputdict[req_name] = DisplayDict(req_name, req)

        dd = inputdict[req_name]
        dd.addData(ddata)

        self.jsondata = jsoninput
        self.toggle_selected(False)
