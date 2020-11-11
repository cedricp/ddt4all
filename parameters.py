# -*- coding: utf-8 -*-
import time
import os
import ecu
import elm
import displaymod
from uiutils import *
import options
from xml.dom.minidom import parse
import xml.dom.minidom
import json, argparse, zipfile, glob
import datetime

try:
    from StringIO import StringIO
    from BytesIO import BytesIO
except ImportError:
    from io import StringIO
    from io import BytesIO


import PyQt5.QtGui as gui
import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets

__author__ = "Cedric PAILLE"
__copyright__ = "Copyright 2016-2020"
__credits__ = []
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Cedric PAILLE"
__email__ = "cedricpaille@gmail.com"
__status__ = "Beta"

_ = options.translator('ddt4all')
# TODO :
# Read freezeframe data // Done (partially)
# Check ELM response validity (mode + 0x40)

class ecuCommand(widgets.QDialog):
    def __init__(self, paramview, ecurequestparser, sds):
        super(ecuCommand, self).__init__(None)
        self.ecu = ecurequestparser
        self.ecu.requests.keys()
        self.sds = sds
        self.paramview = paramview

        layout = widgets.QVBoxLayout()
        self.req_combo = widgets.QComboBox()
        self.sds_combo = widgets.QComboBox()
        self.com_table = widgets.QTableWidget()
        self.rcv_table = widgets.QTableWidget()
        self.isotp_frame_edit = widgets.QLineEdit()
        self.com_table.setColumnCount(2)
        self.com_table.verticalHeader().hide()

        self.rcv_table.setColumnCount(2)
        self.rcv_table.verticalHeader().hide()
        layout.addWidget(widgets.QLabel("Start diagnostic session"))
        layout.addWidget(self.sds_combo)
        layout.addWidget(widgets.QLabel("Request"))
        layout.addWidget(self.req_combo)
        layout.addWidget(widgets.QLabel("Data to send"))
        layout.addWidget(self.com_table)
        layout.addWidget(widgets.QLabel("Computed ISOTP Frame"))
        layout.addWidget(self.isotp_frame_edit)
        checkbutton = widgets.QPushButton("Compute frame")
        layout.addWidget(checkbutton)
        layout.addWidget(widgets.QLabel("Data received"))
        layout.addWidget(self.rcv_table)
        button = widgets.QPushButton("Execute")
        layout.addWidget(button)
        button.clicked.connect(self.execute)
        self.setLayout(layout)
        self.reqs = []
        self.send_data = []
        self.current_request = None
        checkbutton.clicked.connect(self.recompute)

        reqlist = [a for a in self.ecu.requests.keys()]
        reqlist.sort()
        for k in reqlist:
            self.req_combo.addItem(k)
            self.reqs.append(k)
        self.req_combo.currentIndexChanged.connect(self.req_changed)

        for k, v in self.sds.items():
            self.sds_combo.addItem(k)

        text = "<center>This feature is experimental</center>\n"
        text += "<center>Use it at your own risk</center>\n"
        text += "<center>and if you know exactely what you do</center>\n"
        msgbox = widgets.QMessageBox()
        msgbox.setText(text)
        msgbox.exec_()

    def recompute(self):
        frame = self.compute_frame(False)
        self.isotp_frame_edit.setText(frame)

    def compute_frame(self, check=True):
        data_to_stream = {}
        for i in range(0, self.com_table.rowCount()):
            cellwidget = self.com_table.cellWidget(i, 1)
            reqkey = self.com_table.item(i, 0).text()
            if cellwidget:
                curtext = cellwidget.currentText()
            elif self.com_table.item(i, 1) is not None:
                curtext = self.com_table.item(i, 1).text()
            else:
                if check:
                    msgbox = widgets.QMessageBox()
                    msgbox.setText("Missing data in table")
                    msgbox.exec_()
                return "Missing input data"

            if curtext is None:
                # Error here
                data_to_stream[reqkey] = ""
            else:
                data_to_stream[reqkey] = curtext

        stream_to_send = " ".join(self.current_request.build_data_stream(data_to_stream))
        return stream_to_send

    def execute(self):
        if self.current_request is None:
            return

        sds = self.sds[self.sds_combo.currentText()]
        self.paramview.sendElm(sds)

        stream_to_send = self.compute_frame()
        reveived_stream = self.paramview.sendElm(stream_to_send, False, True)
        if reveived_stream.startswith("WRONG"):
            msgbox = widgets.QMessageBox()
            msgbox.setText("ECU returned error (check logview)")
            msgbox.exec_()
            return
        received_data = self.current_request.get_values_from_stream(reveived_stream)

        self.rcv_table.setRowCount(len(received_data))
        itemcount = 0
        for k, v in received_data.items():
            item = widgets.QTableWidgetItem(k)
            self.rcv_table.setItem(itemcount, 0, item)
            if v is not None:
                item = widgets.QTableWidgetItem(v)
            else:
                item = widgets.QTableWidgetItem("NONE")
            self.rcv_table.setItem(itemcount, 1, item)
            itemcount += 1

        self.rcv_table.resizeColumnsToContents()
        self.rcv_table.resizeRowsToContents()

    def req_changed(self, item):
        self.com_table.clear()
        self.com_table.setColumnCount(5)
        self.current_request = self.ecu.requests[self.reqs[item]]
        self.com_table.setRowCount(len(self.current_request.sendbyte_dataitems))
        self.send_data = []

        self.com_table.setHorizontalHeaderLabels(["Key", "Value", "Unit", "Data type", "Description"])
        self.rcv_table.setHorizontalHeaderLabels(["Key", "Value"])

        itemcount = 0
        for k, v in self.current_request.sendbyte_dataitems.items():
            self.send_data.append(k)
            ecudata = self.ecu.data[k]

            item = widgets.QTableWidgetItem(k)
            item.setFlags(item.flags() ^ core.Qt.ItemIsEditable)
            self.com_table.setItem(itemcount, 0, item)
            item = widgets.QTableWidgetItem(ecudata.unit)
            item.setFlags(item.flags() ^ core.Qt.ItemIsEditable)
            self.com_table.setItem(itemcount, 2, item)
            if ecudata.scaled:
                item = widgets.QTableWidgetItem("Numeric decimal")
            elif len(ecudata.items):
                item = widgets.QTableWidgetItem("List")
            elif ecudata.bytesascii:
                item = widgets.QTableWidgetItem("String")
            else:
                item = widgets.QTableWidgetItem("Hexadecimal")
            item.setFlags(item.flags() ^ core.Qt.ItemIsEditable)
            self.com_table.setItem(itemcount, 3, item)
            item = widgets.QTableWidgetItem(ecudata.description)
            item.setFlags(item.flags() ^ core.Qt.ItemIsEditable)
            self.com_table.setItem(itemcount, 4, item)

            if len(ecudata.items):
                items = ecudata.items.keys()
                combo = widgets.QComboBox()
                for item in items:
                    combo.addItem(item)
                self.com_table.setCellWidget(itemcount, 1, combo)
            itemcount += 1

        self.com_table.resizeColumnsToContents()
        self.com_table.resizeRowsToContents()
        self.rcv_table.setRowCount(0)

class paramWidget(widgets.QWidget):
    def __init__(self, parent, ddtfile, ecu_addr, ecu_name, logview, prot_status, canline):
        super(paramWidget, self).__init__(parent)
        self.pagename = ""
        self.logfile = None
        self.updatelog = False
        self.defaultdiagsessioncommand = "10C0"
        self.setFocusPolicy(core.Qt.ClickFocus)
        self.sds = {}
        self.canline = canline
        self.currentsession = ""
        self.layoutdict = None
        self.targetsdata = None
        self.main_protocol_status = prot_status
        self.scrollarea = parent
        self.refreshtime = 100
        self.layout = widgets.QHBoxLayout(self)
        self.logview = logview
        self.ddtfile = ddtfile
        self.ecurequestsparser = None
        self.panel = None
        self.uiscale = 8
        self.ecu_name = ecu_name
        self.button_requests = {}
        self.button_messages = {}
        self.displaydict = {}
        self.inputdict = {}
        self.presend = []
        self.currentwidget = None
        self.timer = core.QTimer()
        self.timer.setSingleShot(True)
        self.tester_timer = core.QTimer()
        self.tester_timer.setSingleShot(False)
        self.tester_timer.setInterval(1500)
        self.tester_timer.timeout.connect(self.tester_send)
        self.tester_timer.start()
        self.tester_presend_command = ""
        self.initXML()
        self.sliding = False
        self.mouseOldX = 0
        self.mouseOldY = 0
        self.current_screen = ''
        self.movingwidgets = []
        self.allow_parameters_update = True
        self.record_values = []
        self.record_keys = {}
        self.infobox = None

    def set_soft_fc(self, b):
        if options.elm is not None:
            options.elm.ATCFC0 = b

    def tester_send(self):
        if self.tester_presend_command == "":
            return

        # No need to send "tester_present" command if we're auto updating
        if options.auto_refresh:
            return

        self.sendElm(self.tester_presend_command, True)

    def saveEcu(self, name=None):
        if not name:
            filename_tuple = widgets.QFileDialog.getSaveFileName(self, _("Save ECU (keep '.json' extension)"), "./json/myecu.json", "*.json")

            filename = str(filename_tuple[0])

            if filename == "":
                return
        else:
            filename = name

        if self.parser == 'xml':
            layoutjs = dumpXML(self.ddtfile)
            js = self.ecurequestsparser.dumpJson()
            jsfile = open(filename, "w")
            jsfile.write(js)
            jsfile.close()
            jsfile = open(filename + ".layout", "w")
            jsfile.write(layoutjs)
            jsfile.close()
        elif self.parser == 'json':
            js = self.ecurequestsparser.dumpJson()
            jsfile = open(filename, "w")
            jsfile.write(js)
            jsfile.close()
            jsfile = open(filename + ".layout", "w")
            jsfile.write(json.dumps(self.layoutdict))
            jsfile.close()

        target_name = filename + ".targets"
        if self.targetsdata:
            js = json.dumps(self.targetsdata, indent=1)
            jsfile = open(target_name, "w")
            jsfile.write(js)
            jsfile.close()
        else:
            ecu_idents = options.ecu_scanner.ecu_database.getTargetsByHref(os.path.basename(self.ddtfile))
            if len(ecu_idents):
                js_targets = []
                for ecui in ecu_idents:
                    js_targets.append(ecui.dump())

                js = json.dumps(js_targets, indent=1)
                jsfile = open(target_name, "w")
                jsfile.write(js)
                jsfile.close()

    def renameCategory(self, oldname, newname):
        if oldname not in self.categories:
            print("Err, cannot rename ", oldname)
            return

        self.categories[newname] = self.categories.pop(oldname)

    def renameScreen(self, oldname, newname):
        if oldname not in self.xmlscreen:
            print("Err, cannot rename ", oldname)
            return

        self.xmlscreen[newname] = self.xmlscreen.pop(oldname)
        for key, cat in self.categories.items():
            if oldname in cat:
                cat.remove(oldname)
                cat.append(newname)
                break

    def createCategory(self, name):
        self.categories[name] = []

    def createScreen(self, name, category):
        self.categories[category].append(name)
        self.xmlscreen[name] = {}
        self.xmlscreen[name]['inputs'] = []
        self.xmlscreen[name]['buttons'] = []
        self.xmlscreen[name]['displays'] = []
        self.xmlscreen[name]['labels'] = []
        self.xmlscreen[name]['width'] = 8000
        self.xmlscreen[name]['height'] = 8000
        self.xmlscreen[name]['color'] = "rgb(0,0,30)"
        self.xmlscreen[name]['presend'] = []

    def addParameter(self, requestname, issend, screenname, item):
        if self.parser != "json":
            self.logview.append("<font color=red>" + _("To be able to edit your screen, first export it in JSON format") + "</font>")
            return

        self.init(screenname)
        if issend:
            input_dict = {}
            input_dict['text'] = item
            input_dict['request'] = requestname
            input_dict['color'] = "rgb(200,200,200)"
            input_dict['fontcolor'] = "rgb(10,10,10)"
            input_dict['width'] = 3000
            input_dict['rect'] = {'width': 4000, 'height': 400, 'top': 100, 'left': 100}
            input_dict['font'] = {'name': "Arial", 'size':12, 'bold': False, 'italic': False}
            self.layoutdict['screens'][screenname]['inputs'].append(input_dict)
        else:
            display_dict = {}
            display_dict['text'] = item
            display_dict['request'] = requestname
            display_dict['color'] = "rgb(200,200,200)"
            display_dict['width'] = 3000
            display_dict['rect'] = {'width': 4000, 'height': 400, 'top': 100, 'left': 100}
            display_dict['font'] =  {'name': "Arial", 'size':12, 'bold': False, 'italic': False}
            display_dict['fontcolor'] = "rgb(10,10,10)"
            self.layoutdict['screens'][screenname]['displays'].append(display_dict)
        self.init(screenname)

    def addButton(self):
        if self.parser != "json":
            self.logview.append("<font color=red>" + _("To be able to edit your screen, first export it in JSON format") + "</font>")
            return

        cursorpos = self.panel.mapFromGlobal(gui.QCursor.pos())
        posx = cursorpos.x() * self.uiscale
        posy = cursorpos.y() * self.uiscale

        button_dict = {}
        button_dict['text'] = "Newbutton"
        button_dict['uniquename'] = "Newbutton_0"
        button_dict['color'] = "rgb(200,200,200)"
        button_dict['width'] = 3000
        button_dict['rect'] = {'width': 4000, 'height': 400, 'top': posy, 'left': posx}
        button_dict['font'] = {'name': "Arial", 'size': 12, 'bold': False, 'italic': False}
        button_dict['messages'] = []
        button_dict['send'] = []

        self.layoutdict['screens'][self.current_screen]['buttons'].append(button_dict)

        self.reinitScreen()

    def addLabel(self):
        if self.parser != "json":
            self.logview.append("<font color=red>" + _("To be able to edit your screen, first export it in JSON format") + "</font>")
            return

        cursorpos = self.panel.mapFromGlobal(gui.QCursor.pos())
        posx = cursorpos.x() * self.uiscale
        posy = cursorpos.y() * self.uiscale

        label_dict = {}
        label_dict['text'] = "NewLabel"
        label_dict['color'] = "rgb(200,150,200)"
        label_dict['bbox'] = {'width': 4000, 'height': 400, 'top': posy, 'left': posx}
        label_dict['font'] = {'name': "Arial", 'size': 12, 'bold': False, 'italic': False}
        label_dict['fontcolor'] = "rgb(0,0,0)"
        label_dict['alignment'] = '2'

        self.layoutdict['screens'][self.current_screen]['labels'].append(label_dict)

        self.reinitScreen()

    def changeLabelColor(self):
        if self.currentwidget is None:
            return

        if isinstance(self.currentwidget, displaymod.labelWidget):
            colordialog = widgets.QColorDialog()
            color = colordialog.getColor()
            if color.isValid():
                self.currentwidget.jsondata['color'] = "rgb(%i,%i,%i)" % (color.red(), color.green(), color.blue())

        self.reinitScreen()


    def renameLabel(self):
        if self.currentwidget is None:
            return

        if isinstance(self.currentwidget, displaymod.labelWidget):
            for label in self.layoutdict['screens'][self.current_screen]['labels']:
                txt = label['text']
                if txt == self.currentwidget.text():
                    nln = widgets.QInputDialog.getText(self, 'DDT4All', _('Enter label name'))
                    if not nln[1]:
                        return
                    newlabelname = nln[0]
                    label['text'] = newlabelname
                    break

        self.reinitScreen()

    def removeElement(self):
        if self.currentwidget is None:
            return

        if isinstance(self.currentwidget, displaymod.labelWidget):
            count = 0
            for label in self.layoutdict['screens'][self.current_screen]['labels']:
                txt = label['text']
                if txt == self.currentwidget.text():
                    self.layoutdict['screens'][self.current_screen]['labels'].pop(count)
                    break
                count += 1

        if isinstance(self.currentwidget, displaymod.inputWidget):
            count = 0
            for inp in self.layoutdict['screens'][self.current_screen]['inputs']:
                txt = inp['text']
                if txt == self.currentwidget.qlabel.text():
                    self.layoutdict['screens'][self.current_screen]['inputs'].pop(count)
                    break
                count += 1

        if isinstance(self.currentwidget, displaymod.displayWidget):
            count = 0
            for display in self.layoutdict['screens'][self.current_screen]['displays']:
                txt = display['text']
                if txt == self.currentwidget.qlabel.text():
                    self.layoutdict['screens'][self.current_screen]['displays'].pop(count)
                    break
                count += 1

        if isinstance(self.currentwidget, displaymod.buttonRequest):
            count = 0
            for button in self.layoutdict['screens'][self.current_screen]['buttons']:
                txt = button['uniquename']
                if txt == self.currentwidget.uniquename:
                    self.layoutdict['screens'][self.current_screen]['buttons'].pop(count)
                    break
                count += 1

        self.reinitScreen()

    def mousePressEvent(self, event):
        if options.simulation_mode and options.mode_edit:
            self.currentwidget = None
            widget = widgets.QApplication.widgetAt(gui.QCursor.pos())

            found = False
            while widget.parent():
                if "ismovable" in dir(widget):
                    found = True
                    break
                widget = widget.parent()

            if event.button() == core.Qt.RightButton:
                self.currentwidget = widget
                popmenu = widgets.QMenu(self)
                addbuttonaction = widgets.QAction(_("Add button"), popmenu)
                addlabelaction = widgets.QAction(_("Add label"), popmenu)

                popmenu.addAction(addbuttonaction)
                popmenu.addAction(addlabelaction)
                addbuttonaction.triggered.connect(self.addButton)
                addlabelaction.triggered.connect(self.addLabel)

                if isinstance(widget, displaymod.labelWidget):
                    renamelabelaction = widgets.QAction(_("Rename label"), popmenu)
                    changecoloraction = widgets.QAction(_("Change color"), popmenu)
                    popmenu.addAction(renamelabelaction)
                    popmenu.addAction(changecoloraction)
                    renamelabelaction.triggered.connect(self.renameLabel)
                    changecoloraction.triggered.connect(self.changeLabelColor)
                if found:
                    removeaction = widgets.QAction(_("Remove element"), popmenu)
                    popmenu.addSeparator()
                    popmenu.addAction(removeaction)
                    removeaction.triggered.connect(self.removeElement)

                popmenu.exec_(gui.QCursor.pos())

            if event.button() == core.Qt.LeftButton:
                if not found or widget == self.panel:
                    for mv in self.movingwidgets:
                        mv.toggle_selected(False)
                    self.movingwidgets = []
                    return

                self.mouseOldX = event.globalX()
                self.mouseOldY = event.globalY()
                if not widget in self.movingwidgets:
                    self.movingwidgets.append(widget)
                widget.toggle_selected(True)
        else:
            if event.button() == core.Qt.LeftButton:
                self.sliding = True
                self.mouseOldX = event.globalX()
                self.mouseOldY = event.globalY()
                return

    def mouseReleaseEvent(self, event):
        if options.simulation_mode:
            if event.button() == core.Qt.RightButton:
                self.movingwidgets = []

        if event.button() == core.Qt.LeftButton:
            self.sliding = False

    def mouseMoveEvent(self, event):
        if options.simulation_mode and options.mode_edit == True:
            if len(self.movingwidgets):
                sizemodifier = widgets.QApplication.keyboardModifiers() == core.Qt.ControlModifier
                ratiomodifier = widgets.QApplication.keyboardModifiers() == core.Qt.ShiftModifier
                mouseX = event.globalX() - self.mouseOldX
                mouseY = event.globalY() - self.mouseOldY
                self.mouseOldX = event.globalX()
                self.mouseOldY = event.globalY()
                for mw in self.movingwidgets:
                    if sizemodifier:
                        mw.resize(mw.width() + mouseX, mw.height() + mouseY)
                    elif ratiomodifier and 'change_ratio' in dir(mw):
                        mw.change_ratio(mouseX)
                    else:
                        mw.move(mw.pos().x() + mouseX, mw.pos().y() + mouseY)
            return

        if self.sliding:
            mouseX = event.globalX() - self.mouseOldX
            mouseY = event.globalY() - self.mouseOldY
            self.mouseOldX = event.globalX()
            self.mouseOldY = event.globalY()
            self.scrollarea.verticalScrollBar().setValue(self.scrollarea.verticalScrollBar().value() - mouseY)
            self.scrollarea.horizontalScrollBar().setValue(self.scrollarea.horizontalScrollBar().value() - mouseX)

    def setRefreshTime(self, value):
        self.refreshtime = value

    def keyPressEvent(self, event):
        if event.key() == core.Qt.Key_Plus:
            self.zoomin_page()
        elif event.key() == core.Qt.Key_Minus:
            self.zoomout_page()
        else:
            event.ignore()
            return

        event.accept()

    def zoomin_page(self):
        self.uiscale -= 1
        if self.uiscale < 4:
            self.uiscale = 4

        self.allow_parameters_update = False
        self.init(self.current_screen)
        self.allow_parameters_update = True

    def zoomout_page(self):
        self.uiscale += 1
        if self.uiscale > 20:
            self.uiscale = 20

        self.allow_parameters_update = False
        self.init(self.current_screen)
        self.allow_parameters_update = True

    def init(self, screen, logfile=None):
        if logfile is not None:
            self.logfile = logfile
        self.updatelog = True
        if self.panel:
            self.layout.removeWidget(self.panel)
            self.panel.setParent(None)
            self.panel.close()
            self.panel.destroy()

        if not screen:
            return False

        scr_init = self.initScreen(screen)
        self.layout.addWidget(self.panel)
        return scr_init

    def command_editor(self):
        editor = ecuCommand(self, self.ecurequestsparser, self.sds)
        editor.exec_()

    def hexeditor(self):
        self.dialogbox = widgets.QWidget()
        wlayout = widgets.QVBoxLayout()
        diaglabel = widgets.QLabel(_("Diagnotic session"))
        inputlabel = widgets.QLabel(_("Input"))
        outputlabel = widgets.QLabel(_("Output"))

        diaglabel.setAlignment(core.Qt.AlignCenter)
        inputlabel.setAlignment(core.Qt.AlignCenter)
        outputlabel.setAlignment(core.Qt.AlignCenter)

        self.diagsession = widgets.QComboBox()
        rqsts = self.ecurequestsparser.requests.keys()
        self.request_editor_sds = {}

        self.diagsession.addItem(u"None")
        self.request_editor_sds[u'None'] = ""


        for diag in rqsts:
            if "start" in diag.lower() and "session" in diag.lower() and 'diag' in diag.lower():

                sds = self.ecurequestsparser.requests[diag]

                if u'Session Name' in sds.sendbyte_dataitems:
                    session_names = self.ecurequestsparser.data[u'Session Name']
                    for name in session_names.items.keys():
                        sds_stream = " ".join(sds.build_data_stream({u'Session Name': name}))
                        name = name + "[" + sds_stream + "]"
                        self.request_editor_sds[name] = sds_stream
                        self.diagsession.addItem(name)
                    print(sds.sendbyte_dataitems[u'Session Name'])

        if len(self.request_editor_sds) == 1:
            for k, v in self.sds.items():
                self.diagsession.addItem(k)
                self.request_editor_sds[k] = v

        self.input = widgets.QLineEdit()
        self.input.returnPressed.connect(self.send_manual_cmd)
        self.output = widgets.QLineEdit()
        self.output.setReadOnly(True)
        hexvalidaor = core.QRegExp(("^[\s0-9a-fA-F]+"))
        rev = gui.QRegExpValidator(hexvalidaor, self)
        self.input.setValidator(rev)
        wlayout.addWidget(diaglabel)
        wlayout.addWidget(self.diagsession)
        wlayout.addWidget(inputlabel)
        wlayout.addWidget(self.input)
        wlayout.addWidget(outputlabel)
        wlayout.addWidget(self.output)
        self.dialogbox.setLayout(wlayout)
        self.dialogbox.show()

    def changeSDS(self, qttext):
        diagsession = self.sds[qttext]
        self.defaultdiagsessioncommand = diagsession
        self.sendElm(diagsession)

    def send_manual_cmd(self):
        diagmode = self.diagsession.currentText()
        if diagmode:
            sds = diagmode
            if sds != u'None':
                rq = self.request_editor_sds[sds]
                self.sendElm(rq)

        command = self.input.text()
        ascii_cmd = str(command).upper().replace(" ", "")
        output = self.sendElm(ascii_cmd)
        self.output.setText(output)

    def setCanLine(self, line):
        self.canline = line
        self.initELM()

    def initELM(self):
        connection_status = self.ecurequestsparser.connect_to_hardware(self.canline)
        if not connection_status:
            self.logview.append("<font color='red'>Protocol not supported</font>")
            return

        if self.main_protocol_status:
            if self.ecurequestsparser.ecu_protocol == "CAN":
                self.startDiagnosticSession()
                txrx = "(Tx0x%s/Rx0x%s)@%iK" % (self.ecurequestsparser.ecu_send_id,
                                              self.ecurequestsparser.ecu_recv_id,
                                              self.ecurequestsparser.baudrate/1000)
                self.main_protocol_status.setText("CAN " + txrx)
            elif self.ecurequestsparser.ecu_protocol == "KWP2000":
                self.startDiagnosticSession()
                self.main_protocol_status.setText("KWP @ " + self.ecurequestsparser.funcaddr)
            elif self.ecurequestsparser.ecu_protocol == "ISO8":
                self.main_protocol_status.setText("ISO8 @ " + self.ecurequestsparser.funcaddr)
            else:
                self.main_protocol_status.setText("??? @ " + self.ecurequestsparser.funcaddr)
                print("Protocol not supported : " + self.ecurequestsparser.ecu_protocol)

    def initJSON(self):
        self.layoutdict = None
        layoutfile = "./json/" + os.path.basename(self.ddtfile) + ".layout"
        targetsfile = "./json/" + os.path.basename(self.ddtfile) + ".targets"
        if os.path.exists(layoutfile):
            jsfile = open(layoutfile, "r")
            jsondata = jsfile.read()
            jsfile.close()
        else:
            zf = zipfile.ZipFile("ecu.zip", mode='r')
            layoutfile = self.ddtfile[5:] + ".layout"
            jsondata = zf.read(layoutfile)
        if os.path.exists(targetsfile):
            jsfile = open(targetsfile, "r")
            self.targetsdata = json.loads(jsfile.read())
            jsfile.close()
        else:
            # Fallback to main database (if zipped ECU)
            tgt = options.main_window.ecu_scan.ecu_database.getTargetsByHref(self.ddtfile[5:])
            if tgt:
                self.targetsdata = []
                for t in tgt:
                    self.targetsdata.append(t.dump())
            else:
                self.targetsdata = None

        self.layoutdict = json.loads(jsondata)

        if self.layoutdict is None:
            return

        self.categories = self.layoutdict['categories']
        self.xmlscreen = self.layoutdict['screens']

    def clearAll(self):
        self.categories = {}
        self.xmlscreen = {}
        self.parser = ''
        self.tester_presend_command = ""
        self.movingwidgets = []
        self.sliding = False
        self.sds = {}
        options.main_window.sdsready = False
        options.main_window.sdscombo.clear()

    def initXML(self):
        self.clearAll()

        if '.json' in self.ddtfile:
            self.parser = 'json'
            self.ecurequestsparser = ecu.Ecu_file(self.ddtfile, True)
            self.initJSON()
        else:
            self.parser = 'xml'
            xdom = xml.dom.minidom.parse(self.ddtfile)
            xdoc = xdom.documentElement

            if not xdoc:
                print(_("XML file not found : ") + self.ddtfile)
                return

            self.ecurequestsparser = ecu.Ecu_file(xdoc)

            target = self.getChildNodesByName(xdoc, u"Target")[0]
            if not target:
                self.logview.append(_("Invalid DDT file"))
                return

            categories = self.getChildNodesByName(target, u"Categories")

            for cats in categories:
                xml_cats = self.getChildNodesByName(cats, u"Category")
                for category in xml_cats:
                    category_name = category.getAttribute(u"Name")
                    self.categories[category_name] = []
                    screens_name = self.getChildNodesByName(category, u"Screen")
                    for screen in screens_name:
                        screen_name = screen.getAttribute(u"Name")
                        self.xmlscreen[screen_name] = screen
                        self.categories[category_name].append(screen_name)

        if self.ecurequestsparser.funcaddr == '00':
            self.tester_presend_command = ""
            return

        self.defaultdiagsessioncommand = "10C0"

        options.main_window.sdscombo.addItem("After sales (default) [10C0]")
        self.sds["After sales (default) [10C0]"] = "10C0"

        # Init startDiagnosticSession combo
        for reqname, request in self.ecurequestsparser.requests.items():
            uppername = reqname.upper()
            if "START" in uppername and "DIAG" in uppername and "SESSION" in uppername:
                sessionnamefound = False
                for di in request.sendbyte_dataitems.keys():
                    dataitemnameupper = di.upper()
                    if u"SESSION" in dataitemnameupper and u"NAME" in dataitemnameupper:
                        ecu_data = self.ecurequestsparser.data[di]
                        for dataname, dataitem in ecu_data.items.items():
                            datastream = request.build_data_stream({di: dataname})
                            sdsrequest = ''.join(datastream)
                            dataname += u" [" + sdsrequest + u"]"
                            options.main_window.sdscombo.addItem(dataname)
                            self.sds[dataname] = sdsrequest
                            sessionnamefound = True

                if len(request.sendbyte_dataitems) == 0 or not sessionnamefound:
                    sdsrequest = "".join(request.build_data_stream({}))
                    dataname = reqname + u" [" + sdsrequest + u"]"
                    options.main_window.sdscombo.addItem(dataname)
                    self.sds[dataname] = sdsrequest

        for i in range(0, options.main_window.sdscombo.count()):
            itemname = options.main_window.sdscombo.itemText(i)
            if u'EXTENDED' in itemname.upper():
                options.main_window.sdscombo.setCurrentIndex(i)
                self.defaultdiagsessioncommand = self.sds[itemname]
                break

        options.main_window.sdsready = True
        self.initELM()

        reqk = self.ecurequestsparser.requests.keys()
        if self.ecurequestsparser.ecu_protocol == 'CAN':
            self.tester_presend_command = '3E'
            for k in reqk:
                if "tester" in k.lower() and "present" in k.lower():
                    self.tester_presend_command = self.ecurequestsparser.requests[k].sentbytes
                    break

    def sendElm(self, command, auto=False, force=False):
        if isinstance(command, bytes):
            command = command.decode("utf-8")
        elif not isinstance(command, str):
            command = str(command)

        elm_response = '00 ' * 70
        if not options.simulation_mode:
            if not options.elm.connectionStat():
                options.main_window.setConnected(False)
                self.logview.append(_("Connection to ELM lost, trying to reconnect..."))
                if elm.reconnect_elm():
                    if not options.elm.connectionStatus:
                        self.logview.append(_("Cannot reconnect..."))
                        return
                    # Must reinit ELM
                    self.initELM()
                    options.main_window.setConnected(True)

            if command.startswith('10'):
                self.logview.append('<font color=blue>' + _(
                    'Switching to session mode') + '</font> <font color=orange>%s</font>' % command)
                options.elm.request(command, cache=False)
                return

            if not force and not options.promode:
                # Allow read only modes
                if command[0:2] in options.safe_commands:
                    elm_response = options.elm.request(command, cache=False)
                    txt = '<font color=blue>' + _('Sending ELM request :') + '</font>'
                else:
                    txt = '<font color=green>' + _('Blocked ELM request :') + '</font>'
                    elm_response = "BLOCKED"
            else:
                # Pro mode *Watch out*
                elm_response = options.elm.request(command, cache=False)
                txt = '<font color=red>' + _('Sending ELM request:') + '</font>'
        else:
            if "1902" in command:
                elm_response="59 40 FF 01 00 28 40 01 00 28 40 02 25 12 40 02 25 14 40 02 56 44 02 12 01 24 02 12 01 44 02 12 06 44 02 29 93 14 02 29 99 74 00 30 16 64 00 30 26 64 00 30 36 64 00 30 46 64 00 30 06 64 02 42 51 24 02 42 51 14 02 42 51 34 02 42 54 94 00 48 71 24 00 48 71 14 00 48 71 34 00 48 87 34 00 48 87 24 00 54 41 55 02 08 0F 15 02 08 0F 15 00 34 03 14 00 34 03 84 00 33 53 14 00 33 53 84 00 01 63 84 02 26 92 45 00 38 02 F4 00 38 03 16 80 38 00 94 00 67 11 24 00 67 10 94 00 67 21 24 00 67 20 94 00 67 31 24 00 67 30 94 00 67 41 24 00 67 40 94 01 20 51 24 02 42 AF 15 02 42 AF 04 02 14 61 14 02 14 64 94 00 62"
            # Only test data
            if self.ecurequestsparser.ecu_send_id == "745":
                if "2144" in command:
                    elm_response = "61 44 0A 00 24 14 0F 14 14 12 01 06 08 0A 0C 16 01 0E 10 14 32 14 0A FF FF FF FF"
                if "210B" in command:
                    elm_response = "61 0B 02 00 6C 10 80 00 02 01 02 01 02 00 00 05 FF FF FF FF"
                if "2147" in command:
                    elm_response = "61 47 00 30 50 50 20 1E 0A 20 FF FF FF"
                if "2126" in command:
                    elm_response = "61 26 14 0F 1C 28 64 5A 50 46 3C 32 28 1E 14 0A 00 5A 0A FF"
                if "2125" in command:
                    elm_response = "61 25 1E 0A 4C 87 14 40 14 06 0F FF FF"
                if "216B" in command:
                    elm_response = "61 6B 10 00"
            if '210A' in command:
                elm_response = "61 0A 16 32 32 02 58 00 B4 3C 3C 1E 3C 0A 0A 0A 0A 01 2C 5C 61 67 B5 BB C1 0A 5C"
            elif "17FF00" in command:
                # Test for ACU4
                elm_response = "57 06 90 07 41 90 08 41 90 42 52 90 08 42 90 07 42 90 7C 40"
                elm_response = "57 01 56 07 4D 00 00"
                # Test for EDC16
                # elm_response = "57 02 05 34 68 06 70 4F 09 A4 09 A4 17"
            elif "17FFFF" in command:
                elm_response = "7F 57 12"
            txt = '<font color=green>' + _('Sending simulated ELM request :') + '</font>'

            if not force and not options.promode:
                # Allow read only modes
                if command[0:2] not in options.safe_commands:
                    elm_response = "BLOCKED"

        if not auto or options.log_all:
            self.logview.append(txt + command)

        if elm_response.startswith('WRONG'):
            self.logview.append("<font color=red>" + _('Bad ELM response :') + "</font> " + elm_response)

        if not auto or options.log_all:
            self.logview.append(_('ELM response : ') + elm_response)

        return elm_response

    def getChildNodesByName(self, parent, name):
        nodes = []
        for node in parent.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.localName == name:
                nodes.append(node)
        return nodes

    def reinitScreen(self):
        self.init(self.current_screen)

    def initScreen(self, screen_name):
        self.movingwidgets = []
        self.sliding = False
        self.current_screen = screen_name
        self.presend = []
        self.timer.stop()

        try:
            self.timer.timeout.disconnect()
        except:
            pass

        if not screen_name in self.xmlscreen.keys():
            self.current_screen = ''
            return False

        screen = self.xmlscreen[screen_name]

        self.panel = displaymod.screenWidget(self, self.uiscale)

        if self.parser == 'xml':
            self.panel.initXML(screen)
        else:
            self.panel.initJson(screen)

        self.setContentsMargins(0, 0, 0, 0)
        self.resize(self.panel.screen_width + 50, self.panel.screen_height + 50)

        self.drawLabels(screen)
        self.drawDisplays(screen)
        self.drawInputs(screen)
        self.drawButtons(screen)
        self.updateDisplays(True)
        self.timer.timeout.connect(self.updateDisplays)
        return True

    def drawDisplays(self, screen):
        self.displaydict = {}
        if self.parser == 'xml':
            displays = self.getChildNodesByName(screen, "Display")

            for disp in displays:
                displaywidget = displaymod.displayWidget(self.panel, self.uiscale, self.ecurequestsparser)
                displaywidget.initXML(disp, self.displaydict)
        else:
            displays = screen['displays']
            for disp in displays:
                displaywidget = displaymod.displayWidget(self.panel, self.uiscale, self.ecurequestsparser)
                displaywidget.initJson(disp, self.displaydict)

    def drawButtons(self, screen):
        self.button_requests = {}
        self.button_messages = {}
        if self.parser == 'xml':
            buttons = self.getChildNodesByName(screen, "Button")
            button_count = 0

            for button in buttons:
                qbutton = displaymod.buttonRequest(self.panel, self.uiscale, self.ecurequestsparser, button_count)
                qbutton.initXML(button)
                button_count += 1

                # Get messages
                for message in qbutton.messages:
                    messagetext = message.getAttribute("Text")
                    if not messagetext:
                        continue
                    if not qbutton.butname in self.button_messages:
                        self.button_messages[qbutton.butname] = []
                    self.button_messages[qbutton.butname].append(messagetext)

                # Get requests to send
                send = self.getChildNodesByName(button, "Send")
                if send:
                    sendlist = []
                    for snd in send:
                        smap = {}
                        delay  = snd.getAttribute("Delay")
                        reqname = snd.getAttribute("RequestName")
                        smap['Delay'] = delay
                        smap['RequestName'] = reqname
                        sendlist.append(smap)
                    self.button_requests[qbutton.butname] = sendlist
                    tooltiptext = ''
                    for k in smap.keys():
                        tooltiptext += smap[k] + '\n'
                    tooltiptext = tooltiptext[0:-1]
                    qbutton.setToolTip(tooltiptext)

                qbutton.clicked.connect(lambda state, btn=qbutton.butname: self.buttonClicked(btn))
        else:
            button_count = 0
            for button in screen['buttons']:
                qbutton = displaymod.buttonRequest(self.panel, self.uiscale, self.ecurequestsparser, button_count)
                qbutton.initJson(button)
                button_count += 1

                self.button_messages = qbutton.messages

                if 'send' in button:
                    sendlist = button['send']
                    self.button_requests[qbutton.butname] = sendlist

                qbutton.clicked.connect(lambda state, btn=qbutton.uniquename: self.buttonClicked(btn))

    def drawLabels(self, screen):
        labeldict = {}
        if self.parser == 'xml':
            labels = self.getChildNodesByName(screen, "Label")
            for label in labels:
                qlabel = displaymod.labelWidget(self.panel, self.uiscale)
                qlabel.initXML(label)
                labeldict[qlabel] = qlabel.area
        else:
            for label in screen['labels']:
                qlabel = displaymod.labelWidget(self.panel, self.uiscale)
                qlabel.initJson(label)
                labeldict[qlabel] = qlabel.area

        # Raise the small labels so they're not hidden by bigger ones
        for key, value in [(k, labeldict[k]) for k in sorted(labeldict, key=labeldict.get, reverse=True)]:
            key.setParent(self.panel)
            key.raise_()

    def drawInputs(self,screen):
        self.inputdict = {}
        if self.parser == 'xml':
            inputs = self.getChildNodesByName(screen, "Input")
            for inp in inputs:
                inputwidget = displaymod.inputWidget(self.panel, self.uiscale, self.ecurequestsparser)
                inputwidget.initXML(inp, self.inputdict)
        else:
            for inp in screen['inputs']:
                inputwidget = displaymod.inputWidget(self.panel, self.uiscale, self.ecurequestsparser)
                inputwidget.initJson(inp, self.inputdict)

    def buttonClicked(self, txt):
        if not txt in self.button_requests:
            self.logview.append(u"<font color=red>" + _("Button request not found : ") + txt + u"</font>")
            return

        if txt in self.button_messages:
            messages = self.button_messages[txt]
            for message in messages:
                msgbox = widgets.QMessageBox()
                msgbox.setText(message)
                msgbox.exec_()

        request_list = self.button_requests[txt]
        for req in request_list:
            request_delay = float(req['Delay'].encode('ascii'))
            request_name  = req['RequestName']
            self.logview.append(u'<font color=purple>' + _('Sending request :') + '</font>' + request_name)

            ecu_request = self.ecurequestsparser.get_request(request_name)
            if ecu_request is None:
                self.logview.append("Unknown request " + request_name)
                self.logview.append("Command aborted ")

            sendbytes_data_items = ecu_request.sendbyte_dataitems
            rcvbytes_data_items = ecu_request.dataitems

            elm_data_stream = ecu_request.get_formatted_sentbytes()

            logdict = {}
            for k in sendbytes_data_items.keys():
                dataitem = sendbytes_data_items[k]

                if not request_name in self.inputdict:
                    # Simple command with no user parameters
                    continue

                inputdict = self.inputdict[request_name]
                data = inputdict.getDataByName(k)

                if data == None:
                    # Keep values provided by sentbytes
                    # Confirmed with S3000 ECU request "ReadMemoryByAddress" value "MEMSIZE"
                    continue

                widget = data.widget
                ecu_data = data.data
                is_combo_widget = data.is_combo

                newval = ""
                if not is_combo_widget:
                    # Get input string from user line edit
                    input_value = widget.text()
                    newval = input_value
                else:
                    # Get value from user input combo box
                    combo_value = widget.currentText()
                    newval = combo_value
                    items_ref = ecu_data.items
                    input_value = hex(int(items_ref[combo_value]))[2:]

                elm_data_stream = ecu_data.setValue(input_value, elm_data_stream, dataitem, ecu_request.ecu_file.endianness)
                logdict[dataitem.name] = newval

                if not elm_data_stream:
                    widget.setStyleSheet("background-color: red;color: black")
                    self.logview.append(_("Request aborted (look at red paramters entries): ") + str(input_value))
                    return

                widget.setStyleSheet("background-color: white;color: black")

            # Manage delay
            blocked = False
            self.logview.append("Delay %d ms" % request_delay)
            time.sleep(request_delay / 1000.0)
            # Then show received values
            elm_response = self.sendElm(' '.join(elm_data_stream))
            if elm_response == "BLOCKED":
                msgbox = widgets.QMessageBox()
                msgbox.setWindowTitle("For your safety")
                msgbox.setText("<center>BLOCKED COMMAND</center>\nActivate expert mode to unlock")
                msgbox.exec_()
                blocked = True

            if self.logfile is not None and len(logdict) > 0:
                self.logfile.write("\t@ " + datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3] + "\n")
                if not blocked:
                    self.logfile.write("\tWriting parameter : \n\t\t")
                else:
                    self.logfile.write("\tBlocked writing parameter : \n\t\t")
                self.logfile.write(json.dumps(logdict))
                self.logfile.write("\n")
                self.logfile.flush()

            if blocked:
                return

            for key in rcvbytes_data_items.keys():
                if request_name in self.displaydict:
                    data_item = rcvbytes_data_items[key]
                    dd_ecu_data = self.ecurequestsparser.data[key]
                    value = dd_ecu_data.getDisplayValue(elm_response, data_item, self.ecurequestsparser.endianness)
                    dd_request_data = self.displaydict[request_name]
                    data = dd_request_data.getDataByName(key)

                    if value == None:
                        if data:
                            data.widget.setStyleSheet("background-color: red;color: black")
                        value = _("Invalid")
                    else:
                        if data:
                            data.widget.setStyleSheet("background-color: white;color: black")

                    if data:
                        data.widget.setText(value + ' ' + dd_ecu_data.unit)

        # Give some time to ECU to refresh parameters
        time.sleep(0.1)
        # Want to show result in log
        self.updatelog = True
        self.updateDisplays()

    def startDiagnosticSession(self, sds=""):
        if sds == "":
            sds = self.defaultdiagsessioncommand

        if self.currentsession == sds:
            return

        self.logview.append('<font color=blue>' + _('ECU uses SDS ') + '</font> <font color=orange>%s</font>' % sds)

        if self.ecurequestsparser.ecu_protocol == "CAN":
            if not options.simulation_mode:
                options.elm.start_session_can(sds)
            self.currentsession = sds
        elif self.ecurequestsparser.ecu_protocol == "KWP2000":
            if not options.simulation_mode:
                options.elm.start_session_iso(sds)
            self.currentsession = sds

    def getRequest(self, requests, reqname):
        if reqname in requests:
            return requests[reqname]
        for req in requests:
            if req.upper() == reqname.upper():
                return requests[req]
        return None

    def prepare_recording(self):
        self.record_values = []
        self.record_keys = []
        units = {}
        self.record_time = time.time()

        for request_name in self.displaydict.keys():
            request_data = self.displaydict[request_name]
            request = request_data.request
            if request.manualsend:
                continue

            for data_struct in request_data.data:
                ecu_data = data_struct.data
                data_item = request.dataitems[ecu_data.name]
                self.record_keys.append(data_item.name)
                units[data_item.name] = ecu_data.unit

        first_entry = []
        first_entry.append("Time (ms)")
        for key in self.record_keys:
            first_entry.append(key + "(" + units[key] + ")")

        self.record_values.append(first_entry)

    def get_record_size(self):
        return len(self.record_values)

    def export_record(self, filename):
        f = open(filename, "w")
        for line in self.record_values:
            f.write(';'.join(line))
            f.write("\n")

    def updateDisplays(self, update_inputs=False):
        if not self.panel:
            return

        if not self.allow_parameters_update:
            return
        start_time = time.time()
        # <Screen> <Send/> <Screen/> tag management
        # Manage pre send commands

        self.startDiagnosticSession()

        if not options.auto_refresh:
            for sendcom in self.panel.presend:
                delay = float(sendcom['Delay'])
                req_name = sendcom['RequestName']

                time.sleep(delay / 1000.)
                request = self.getRequest(self.ecurequestsparser.requests, req_name)
                if not request:
                    self.logview.append(_("Cannot call request ") + req_name)
                self.sendElm(request.sentbytes, True)

        self.recorddict = {}
        for request_name in self.displaydict.keys():
            self.updateDisplay(request_name, update_inputs)

        if options.auto_refresh:
            elapsed_time = time.time() - self.record_time
            current_time = '{:.3f}'.format(elapsed_time*1000.0)
            lst = []
            lst.append(current_time)
            for key in self.record_keys:
                if key in self.recorddict.keys():
                    if key in self.recorddict:
                        lst.append(self.recorddict[key])
                    else:
                        lst.append("N/A")
            self.record_values.append(lst)

        elapsed_time = time.time() - start_time
        if self.infobox:
            self.infobox.setText('Update time {:.3f} ms'.format(elapsed_time*1000.0))
        # Stop log
        self.updatelog = False
        if options.auto_refresh:
            self.timer.start(options.refreshrate)

    def updateDisplay(self, request_name, update_inputs=False):
        request_data = self.displaydict[request_name]
        request = request_data.request

        if request.manualsend:
            return

        ecu_bytes_to_send = request.sentbytes.encode('ascii')
        elm_response = self.sendElm(ecu_bytes_to_send, True)

        # Test data for offline test, below is UCT_X84 (roof) parameter misc timings and values
        # elm_response = "61 0A 16 32 32 02 58 00 B4 3C 3C 1E 3C 0A 0A 0A 0A 01 2C 5C 61 67 B5 BB C1 0A 5C"
        # Test data for DAE_X84
        # elm_response = "61 01 0E 0E FF FF 70 00 00 00 00 01 11 64 00 00 EC 00 00 00"
        # elm_response = "61 08 F3 0C 48 00 00 00 00 F3 0C 48 00 00 00 00 00 00 00 00 00 00 00 FF 48 FF FF"
        logdict = {}
        for data_struct in request_data.data:
            qlabel = data_struct.widget
            ecu_data = data_struct.data
            data_item = request.dataitems[ecu_data.name]
            value = ecu_data.getDisplayValue(elm_response, data_item, request.ecu_file.endianness)

            if value is None:
                qlabel.setStyleSheet("background-color: red;color: black")
                value = "NO DATA"
            else:
                qlabel.resetDefaultStyle()

            out_value = "N/A"
            if value is not None:
                out_value = value

            logdict[data_item.name] = out_value

            if options.auto_refresh:
                self.recorddict[data_item.name] = out_value.replace(".", ",")

            qlabel.setText(value + ' ' + ecu_data.unit)

            if update_inputs:
                for inputkey in self.inputdict:
                    input = self.inputdict[inputkey]
                    if ecu_data.name in input.datadict:
                        data = input.datadict[ecu_data.name]
                        if not data.is_combo:
                            data.widget.setText(value)
                        else:
                            combovalueindex = -1
                            for i in range(data.widget.count()):
                                itemname = data.widget.itemText(i)
                                if itemname == value:
                                    combovalueindex = i
                                    break

                            if combovalueindex != -1:
                                data.widget.setCurrentIndex(combovalueindex)

        if self.updatelog and self.logfile is not None:
            self.logfile.write("\t@ " + datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3] + "\n")
            self.logfile.write("\tScreen : " + self.pagename + "\tRequest : " + request_name + "\n")
            string = json.dumps(logdict)
            self.logfile.write(u"\t\t" + string)
            self.logfile.write("\n")
            self.logfile.flush()

    def setCanTimeout(self):
        if not options.simulation_mode:
            options.elm.set_can_timeout(options.cantimeout)

    def clearDTC(self):
        self.logview.append(_("Clearing DTC information"))

        if "ClearDiagnosticInformation.All" in self.ecurequestsparser.requests:
            req = self.ecurequestsparser.requests["ClearDiagnosticInformation.All"]
            request = req.sentbytes
        elif "ClearDTC" in self.ecurequestsparser.requests:
            req = self.ecurequestsparser.requests["ClearDTC"]
            request = req.sentbytes
        elif "Clear Diagnostic Information" in self.ecurequestsparser.requests:
            req = self.ecurequestsparser.requests["Clear Diagnostic Information"]
            request = req.sentbytes
        else:
            self.logview.append(_("No ClearDTC request for that ECU, will send default 14FF00"))
            request = "14FF00"

        msgbox = widgets.QMessageBox()
        msgbox.setText(_("<center>You are about to clear diagnostic troubles codes</center>") +
                       _("<center>Ae you sure this is what you want.</center>"))

        msgbox.setStandardButtons(widgets.QMessageBox.Yes)
        msgbox.addButton(widgets.QMessageBox.Abort)
        msgbox.setDefaultButton(widgets.QMessageBox.Abort)
        userreply = msgbox.exec_()

        if userreply == widgets.QMessageBox.Abort:
            return

        self.startDiagnosticSession()

        # Extend timeout to not miss response
        if options.elm is not None:
            options.elm.set_can_timeout(1500)
        # Add a little delay
        time.sleep(.5)

        response = self.sendElm(request)
        if options.elm is not None:
            options.elm.set_can_timeout(options.cantimeout)

        self.dtcdialog.close()

        if 'WRONG' in response:
            msgbox = widgets.QMessageBox()
            msgbox.setText("There was an error clearing DTC")
            msgbox.exec_()
            options.main_window.logview.append("<font color=red>Clear DTC failed</font>")
        else:
            options.main_window.logview.append("<font color=green>Clear DTC successfully done</font>")

    def readDTC(self):
        if not options.simulation_mode:
            if self.ecurequestsparser.ecu_protocol == "CAN":
                options.elm.start_session_can('10C0')
            elif self.ecurequestsparser.ecu_protocol == "KWP2000":
                options.elm.start_session_iso('10C0')

        if "ReadDTCInformation.ReportDTC" in self.ecurequestsparser.requests:
            request = self.ecurequestsparser.requests["ReadDTCInformation.ReportDTC"]
        elif "ReadDTC" in self.ecurequestsparser.requests:
            request = self.ecurequestsparser.requests["ReadDTC"]
        else:
            self.logview.append("No ReadDTC request for that ECU")
            return

        shiftbytecount = request.shiftbytescount
        bytestosend = list(map(''.join, zip(*[iter(request.sentbytes)]*2)))

        dtcread_command = ''.join(bytestosend)
        can_response = self.sendElm(dtcread_command)

        moredtcread_command = None
        if 'MoreDTC' in request.sendbyte_dataitems:
            moredtcfirstbyte = int(request.sendbyte_dataitems['MoreDTC'].firstbyte)
            bytestosend[moredtcfirstbyte - 1] = "FF"
            moredtcread_command = ''.join(str(bytestosend))

        if "RESPONSE" in can_response:
            msgbox = widgets.QMessageBox()
            msgbox.setText(_("Invalid response for ReadDTC command"))
            msgbox.exec_()
            return

        can_response = can_response.split(' ')

        # Handle error
        if can_response[0].upper() == "7F":
            msgbox = widgets.QMessageBox()
            msgbox.setText(_("Read DTC returned an error"))
            msgbox.exec_()
            return

        # Handle no DTC
        if len(can_response) == 2:
            #No errors
            msgbox = widgets.QMessageBox()
            msgbox.setText(_("No DTC"))
            msgbox.exec_()
            return

        # Ask for more DTCs, allow only 50 iterations in case infinite loop
        maxcount = 50
        if moredtcread_command is not None:
            while maxcount > 0:
                more_can_response = self.sendElm(moredtcread_command)
                more_can_response = more_can_response.split(' ')

                if more_can_response[0].upper() == 'WRONG':
                    break
                # Append result to build one frame
                can_response += more_can_response[2:]
                maxcount -= 1

        numberofdtc = int('0x' + can_response[1], 16)
        self.dtcdialog = widgets.QDialog(None)
        dtc_view = widgets.QTextEdit(None)
        dtc_view.setReadOnly(True)
        layout = widgets.QVBoxLayout()
        self.dtcdialog.setLayout(layout)
        clearbutton = widgets.QPushButton(_("Clear ALL DTC"))
        layout.addWidget(clearbutton)
        layout.addWidget(dtc_view)

        clearbutton.clicked.connect(self.clearDTC)

        html = '<h1 style="color:red">' + _('ECU trouble codes') + '</color></h1>'

        for dn in range(0, numberofdtc):
            html += '<h2 style="color:orange">DTC #%i' % dn + "</h2>"
            html += "<p>"
            for k in request.dataitems.keys():
                # Filter out NDTC, not needed
                if k == "NDTC":
                    continue
                ecu_data = self.ecurequestsparser.data[k]
                dataitem = request.dataitems[k]
                value_hex = ecu_data.getHexValue(' '.join(can_response), dataitem, request.ecu_file.endianness)

                if value_hex is None:
                    continue

                value = int('0x' + value_hex, 16)

                if len(ecu_data.items) > 0 and value in ecu_data.lists:
                    html += "<u>" + dataitem.name + "</u> : [" + str(value_hex) + "] " + ecu_data.lists[value] + "<br>"
                else:
                    html += "<u>" + dataitem.name + "</u> : " + str(value) + " [" + hex(value) + "]<br>"
            html += "</p>"
            can_response = can_response[shiftbytecount:]

        dtc_view.setHtml(html)
        self.dtcdialog.exec_()

    def requestNameChanged(self, oldname, newname):
        for screen_k, screen_data in self.layoutdict['screens'].items():
            print(_("Parsing screen "), screen_k)
            for input_data in screen_data['inputs']:
                if oldname == input_data['request']:
                    print("found request in input ", screen_k)
                    input_data['request'] = newname

            for display_data in screen_data['displays']:
                if oldname == display_data['request']:
                    print("found in display ", screen_k)
                    display_data['request'] = newname

            for button_data in screen_data['buttons']:
                if 'send' in button_data.keys():
                    for send in button_data['send']:
                        if send['RequestName'] == oldname:
                            print("found in button ", screen_k)
                            send['RequestName'] = newname

            for presend_data in screen_data['presend']:
                if 'RequestName' in presend_data:
                    if presend_data['RequestName'] == oldname:
                        print("found in presend ", screen_k)
                        presend_data['RequestName'] = newname

        self.reinitScreen()

    def dataNameChanged(self, oldname, newname):
        for screen_k, screen_data in self.layoutdict['screens'].items():
            print("Parsing screen ", screen_k)
            for input_data in screen_data['inputs']:
                if oldname == input_data['text']:
                    print("found data in input ", screen_k)
                    input_data['text'] = newname

            for display_data in screen_data['displays']:
                if oldname == display_data['text']:
                    print("found data in display ", screen_k)
                    display_data['text'] = newname

        self.reinitScreen()

def dumpXML(xmlname):
    try:
        xdom = xml.dom.minidom.parse(xmlname)
        xdoc = xdom.documentElement
    except:
        return None
    return dumpDOC(xdoc)

def dumpAddressing():
    xdom = xml.dom.minidom.parse("GenericAddressing.xml")
    xdoc = xdom.documentElement
    dict = {}
    xml_funcs = getChildNodesByName(xdoc, u"Function")
    for func in xml_funcs:
        shortname = func.getAttribute(u"Name")
        address = func.getAttribute(u"Address")
        for name in  getChildNodesByName(func, u"Name"):
            longname = name.firstChild.nodeValue
            dict[hex(int(address))[2:].upper()] = (shortname, longname)
            break

    js = json.dumps(dict)
    f = open("json/addressing.json", "w")
    f.write(js)
    f.close()


def dumpDOC(xdoc):
    target = getChildNodesByName(xdoc, u"Target")
    if not target:
        return None

    target = target[0]
    js_screens = {}

    xml_categories = getChildNodesByName(target, u"Categories")

    xmlscreens = {}
    js_categories = {}

    for cats in xml_categories:
        xml_cats = getChildNodesByName(cats, u"Category")
        for category in xml_cats:
            category_name = category.getAttribute(u"Name")
            js_categories[category_name] = []
            screens_name = getChildNodesByName(category, u"Screen")
            for screen in screens_name:
                screen_name = screen.getAttribute(u"Name")
                xmlscreens[screen_name] = screen
                js_categories[category_name].append(screen_name)

    for scrname, screen in xmlscreens.items():
        screen_name = scrname
        js_screens[screen_name] = {}
        js_screens[screen_name]['width'] = int(screen.getAttribute("Width"))
        js_screens[screen_name]['height'] = int(screen.getAttribute("Height"))
        js_screens[screen_name]['color'] = colorConvert(screen.getAttribute("Color"))
        js_screens[screen_name]['labels'] = {}

        presend = []
        for elem in getChildNodesByName(screen, u"Send"):
            delay = elem.getAttribute('Delay')
            req_name = elem.getAttribute('RequestName')
            presend.append({"Delay": delay, "RequestName": req_name})
        js_screens[screen_name]['presend'] = presend

        labels = getChildNodesByName(screen, "Label")
        js_screens[screen_name]['labels'] = []
        for label in labels:
            label_dict = {}
            label_dict['text'] = label.getAttribute("Text")
            label_dict['color'] = colorConvert(label.getAttribute("Color"))
            label_dict['alignment'] = label.getAttribute("Alignment")
            label_dict['fontcolor'] = getFontColor(label)
            label_dict['bbox'] = getRectangleXML(getChildNodesByName(label, "Rectangle")[0])
            label_dict['font'] = getFontXML(label)
            js_screens[screen_name]['labels'].append(label_dict)

        displays = getChildNodesByName(screen, "Display")
        js_screens[screen_name]['displays'] = []
        for display in displays:
            display_dict = {}
            display_dict['text'] = display.getAttribute("DataName")
            display_dict['request'] = display.getAttribute("RequestName")
            display_dict['color'] = colorConvert(display.getAttribute("Color"))
            display_dict['width'] = int(display.getAttribute("Width"))
            display_dict['rect'] = getRectangleXML(getChildNodesByName(display, "Rectangle")[0])
            display_dict['font'] = getFontXML(display)
            display_dict['fontcolor'] = getFontColor(display)
            js_screens[screen_name]['displays'].append(display_dict)

        buttons = getChildNodesByName(screen, "Button")
        js_screens[screen_name]['buttons'] = []
        count = 0
        for button in buttons:
            button_dict = {}
            txt = button.getAttribute("Text")
            button_dict['text'] = txt
            button_dict['uniquename'] = txt + "_%i" % count
            button_dict['rect'] = getRectangleXML(getChildNodesByName(button, "Rectangle")[0])
            button_dict['font'] = getFontXML(button)

            xmlmessages = getChildNodesByName(button, "Message")
            messages = []
            # Get messages
            for message in xmlmessages:
                messages.append(message.getAttribute("Text"))

            button_dict['messages'] = messages

            send = getChildNodesByName(button, "Send")
            if send:
                sendlist = []
                for snd in send:
                    smap = {}
                    delay = snd.getAttribute("Delay")
                    reqname = snd.getAttribute("RequestName")
                    smap['Delay'] = delay
                    smap['RequestName'] = reqname
                    sendlist.append(smap)
                button_dict['send'] = sendlist

            js_screens[screen_name]['buttons'].append(button_dict)
            count += 1

        inputs = getChildNodesByName(screen, "Input")
        js_screens[screen_name]['inputs'] = []

        for input in inputs:
            input_dict = {}
            input_dict['text'] = input.getAttribute("DataName")
            input_dict['request']  = input.getAttribute("RequestName")
            color     = input.getAttribute("Color")
            if not color:
                color = 0xAAAAAA
            input_dict['color'] = colorConvert(color)
            input_dict['fontcolor'] = getFontColor(input)
            input_dict['width'] = int(input.getAttribute("Width"))
            input_dict['rect'] = getRectangleXML(getChildNodesByName(input, "Rectangle")[0])
            input_dict['font'] = getFontXML(input)
            js_screens[screen_name]['inputs'].append(input_dict)

    return json.dumps({'screens': js_screens, 'categories': js_categories}, indent=1)


def zipConvertXML(dbfilename="ecu.zip"):
    zipoutput = BytesIO()
    options.ecus_dir = "./ecus"

    ecus_glob = glob.glob("ecus/*.xml")
    imgs = []
    if os.path.exists("./graphics"):
        for dirpath, dirs, files in os.walk("graphics/"):
            for file in files:
                if ".gif" in file.lower():
                    imgs.append(os.path.join(dirpath, file))

    if len(ecus_glob) == 0:
        print("Cannot zip database, no 'ecus' directory")
        return

    ecus = []
    for e in ecus_glob:
        if 'eculist.xml' in e.lower():
            continue
        ecus.append(e)

    i = 0
    print("Starting conversion")

    targetsdict = {}
    with zipfile.ZipFile(zipoutput, mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for img in imgs:
            zf.write(img)
        for target in ecus:
            filename = target.replace(".xml", ".json")
            if filename.startswith("ecus/"):
                filename = filename.replace("ecus/", "")
            else:
                filename = filename.replace("ecus\\", "")
            print("Starting processing " + target + " " + str(i) + "/" + str(len(ecus)) + " to " + filename)

            i += 1
            layoutjs = dumpXML(target)
            if layoutjs is None:
                print("Skipping current file (cannot parse it)")
                continue
            ecufile = ecu.Ecu_file(target, True)
            js = ecufile.dumpJson()

            if js:
                zf.writestr(filename, str(js))

            if layoutjs:
                zf.writestr(filename + ".layout", str(layoutjs))

            ecu_ident = ecufile.dump_idents()

            targetsdict[filename] = ecu_ident

        print('Writing database')
        zf.writestr("db.json", str(json.dumps(targetsdict, indent=1)))

    print('Writing archive')
    with open(dbfilename, "wb") as f:
        f.write(zipoutput.getvalue())


def convertXML():
    options.ecus_dir = "./ecus"

    ecus = glob.glob("ecus/*.xml")
    ecus.remove("ecus/eculist.xml")
    i = 0

    print("Opening ECU Database...")
    ecu_database = ecu.Ecu_database()
    print("Starting conversion")

    for target in ecus:
        filename = target.replace(".xml", ".json")
        filename = filename.replace("ecus/", "json/")
        print("Starting processing " + target + " " + str(i) + "/" + str(len(ecus)) + " to " + filename)

        i += 1
        layoutjs = dumpXML(target)
        if layoutjs is None:
            print("Skipping current file (cannot parse it)")
            continue
        ecufile = ecu.Ecu_file(target, True)
        js = ecufile.dumpJson()

        if js:
            jsfile = open(filename, "w")
            jsfile.write(js)
            jsfile.close()

        if layoutjs:
            jsfile = open(filename + ".layout", "w")
            jsfile.write(layoutjs)
            jsfile.close()

        target_name = filename + ".targets"
        ecu_ident = ecu_database.getTargets(ecufile.ecuname)

        js_targets = []
        for ecui in ecu_ident:
            js_targets.append(ecui.dump())

        js = json.dumps(js_targets, indent=1)
        if js:
            jsfile = open(target_name, "w")
            jsfile.write(js)
            jsfile.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dumpaddressing', action="store_true", default=None, help="Dump addressing")
    parser.add_argument('--convert', action="store_true", default=None, help="Convert all XML to JSON")
    parser.add_argument('--zipconvert', action="store_true", default=None,
                        help="Convert all XML to JSON in a Zip archive")
    args = parser.parse_args()

    if args.zipconvert:
        zipConvertXML()

    if args.convert:
        convertXML()

    if args.dumpaddressing:
        dumpAddressing()
