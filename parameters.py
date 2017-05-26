import time
import os
import ecu, elm
import displaymod
from uiutils import *
import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import options
from xml.dom.minidom import parse
import xml.dom.minidom
import json, unicodedata, argparse, zipfile, glob
from StringIO import StringIO

# TODO :
# Read freezeframe data // Done (partially)
# Check ELM response validity (mode + 0x40)


def to_nfkd(input_str):
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])


def toascii(str):
    return to_nfkd(str).encode('ascii', 'ignore')


class paramWidget(gui.QWidget):
    def __init__(self, parent, ddtfile, ecu_addr, ecu_name, logview, prot_status):
        super(paramWidget, self).__init__(parent)
        self.layoutdict = None
        self.main_protocol_status = prot_status
        self.scrollarea = parent
        self.refreshtime = 100
        self.layout = gui.QHBoxLayout(self)
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
        self.movingwidget = None
        self.allow_parameters_update = True

    def __del__(self):
        # Return to default session
        self.logview.append("<font color=blue>Returning to defaut session...</font>")
        if not options.simulation_mode:
            if self.ecurequestsparser.ecu_protocol == "CAN":
                options.elm.start_session_can('1081')
            elif self.ecurequestsparser.ecu_protocol == "KWP2000":
                options.elm.start_session_iso('1081')

    def tester_send(self):
        if self.tester_presend_command == "":
            return

        # No need to send "tester_present" command if we're updating
        if options.auto_refresh:
            return

        self.sendElm(self.tester_presend_command, True)

    def saveEcu(self, name = None):
        if not name:
            filename = gui.QFileDialog.getSaveFileName(self, "Save ECU (keep '.json' extension)", "./json/myecu.json", "*.json")
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
        ecu_ident = options.ecu_scanner.ecu_database.getTargets(self.ecu_name)

        js_targets = []
        for ecui in ecu_ident:
            js_targets.append(ecui.dump())

        js = json.dumps(js_targets, indent=1)
        jsfile = open(target_name, "w")
        jsfile.write(js)
        jsfile.close()

    def renameCategory(self, oldname, newname):
        if oldname not in self.categories:
            print "Err, cannot rename ", oldname
            return

        self.categories[newname] = self.categories.pop(oldname)

    def renameScreen(self, oldname, newname):
        if oldname not in self.xmlscreen:
            print "Err, cannot rename ", oldname
            return

        self.xmlscreen[newname] = self.xmlscreen.pop(oldname)
        for key, cat in self.categories.iteritems():
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
            self.logview.append("<font color=red>To be able to edit your screen, first export it in JSON format</font>")
            return

        self.init(screenname)
        if issend:
            input_dict = {}
            input_dict['text'] = toascii(item)
            input_dict['request'] = toascii(requestname)
            input_dict['color'] = "rgb(200,200,200)"
            input_dict['fontcolor'] = "rgb(10,10,10)"
            input_dict['width'] = 3000
            input_dict['rect'] = {'width': 4000, 'height': 400, 'top': 100, 'left': 100}
            input_dict['font'] = {'name': "Arial", 'size':12, 'bold': False, 'italic': False}
            self.layoutdict['screens'][screenname]['inputs'].append(input_dict)
        else:
            display_dict = {}
            display_dict['text'] = toascii(item)
            display_dict['request'] = toascii(requestname)
            display_dict['color'] = "rgb(200,200,200)"
            display_dict['width'] = 3000
            display_dict['rect'] = {'width': 4000, 'height': 400, 'top': 100, 'left': 100}
            display_dict['font'] =  {'name': "Arial", 'size':12, 'bold': False, 'italic': False}
            display_dict['fontcolor'] = "rgb(10,10,10)"
            self.layoutdict['screens'][screenname]['displays'].append(display_dict)
        self.init(screenname)

    def addButton(self):
        if self.parser != "json":
            self.logview.append("<font color=red>To be able to edit your screen, first export it in JSON format</font>")
            return

        button_dict = {}
        button_dict['text'] = "Newbutton"
        button_dict['color'] = "rgb(200,200,200)"
        button_dict['width'] = 3000
        button_dict['rect'] = {'width': 4000, 'height': 400, 'top': 100, 'left': 100}
        button_dict['font'] = {'name': "Arial", 'size': 12, 'bold': False, 'italic': False}
        button_dict['messages'] = []

        self.layoutdict['screens'][self.current_screen]['buttons'].append(button_dict)

        self.init(self.current_screen)

    def addLabel(self):
        pass

    def mousePressEvent(self, event):
        if options.simulation_mode:
            if event.button() == core.Qt.RightButton:
                popmenu = gui.QMenu(self)
                addbuttonaction = gui.QAction("Add button", popmenu)
                addlabelaction = gui.QAction("Add label", popmenu)

                popmenu.addAction(addbuttonaction)
                popmenu.addAction(addlabelaction)

                addbuttonaction.triggered.connect(self.addButton)
                addlabelaction.triggered.connect(self.addLabel)

                popmenu.exec_(gui.QCursor.pos())

            if event.button() == core.Qt.LeftButton:
                widget = gui.QApplication.widgetAt(gui.QCursor.pos())

                found = False
                while widget.parent():
                    if "ismovable" in dir(widget):
                        found = True
                        break
                    widget = widget.parent()

                if not found:
                    self.movingwidget = None
                    return

                self.mouseOldX = event.globalX()
                self.mouseOldY = event.globalY()
                self.movingwidget = widget

        else:
            if event.button() == core.Qt.LeftButton:
                self.sliding = True
                self.mouseOldX = event.globalX()
                self.mouseOldY = event.globalY()
                return

    def mouseReleaseEvent(self, event):
        if options.simulation_mode:
            if event.button() == core.Qt.RightButton:
                self.movingwidget = None

        if event.button() == core.Qt.LeftButton:
            self.sliding = False

    def mouseMoveEvent(self, event):
        if options.simulation_mode:
            if self.movingwidget:
                sizemodifier = gui.QApplication.keyboardModifiers() == core.Qt.ControlModifier
                ratiomodifier = gui.QApplication.keyboardModifiers() == core.Qt.ShiftModifier
                mouseX = event.globalX() - self.mouseOldX
                mouseY = event.globalY() - self.mouseOldY
                self.mouseOldX = event.globalX()
                self.mouseOldY = event.globalY()
                if sizemodifier:
                    self.movingwidget.resize(self.movingwidget.width() + mouseX, self.movingwidget.height() + mouseY)
                elif ratiomodifier and 'change_ratio' in dir(self.movingwidget):
                    self.movingwidget.change_ratio(mouseX)
                else:
                    self.movingwidget.move(self.movingwidget.pos().x() + mouseX, self.movingwidget.pos().y() + mouseY)
                return

        if self.sliding:
            mouseX = event.globalX() - self.mouseOldX
            mouseY = event.globalY() - self.mouseOldY
            self.mouseOldX = event.globalX()
            self.mouseOldY = event.globalY()
            self.scrollarea.verticalScrollBar().setValue(self.scrollarea.verticalScrollBar().value() - mouseY)
            self.scrollarea.horizontalScrollBar().setValue(self.scrollarea.horizontalScrollBar().value() - mouseX)

    def wheelEvent(self, event):
        if event.delta() > 0:
            self.zoomin_page()
        else:
            self.zoomout_page()
        self.allow_parameters_update = False
        self.init(self.current_screen)
        self.allow_parameters_update = True

    def zoomin_page(self):
        self.uiscale -= 1
        if self.uiscale < 4:
            self.uiscale = 4

    def zoomout_page(self):
        self.uiscale += 1
        if self.uiscale > 20:
            self.uiscale = 20

    def init(self, screen):
        if self.panel:
            self.layout.removeWidget(self.panel)
            self.panel.setParent(None)
            self.panel.close()
            self.panel.destroy()

        if not screen:
            return False

        self.initELM()
        scr_init = self.initScreen(screen)
        self.layout.addWidget(self.panel)
        return scr_init

    def hexeditor(self):
        self.dialogbox = gui.QWidget()
        wlayout = gui.QVBoxLayout()
        diaglabel = gui.QLabel("Diagnotic session")
        inputlabel = gui.QLabel("Input")
        outputlabel = gui.QLabel("Output")
        self.diagsession = gui.QComboBox()
        rqsts = self.ecurequestsparser.requests.keys()

        for diag in rqsts:
            if "start" in diag.lower() and "session" in diag.lower():
                self.diagsession.addItem(diag)

        self.input = gui.QLineEdit()
        self.input.returnPressed.connect(self.send_manual_cmd)
        self.output = gui.QLineEdit()
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

    def send_manual_cmd(self):
        diagmode = self.diagsession.currentText()
        if diagmode:
            rq = self.ecurequestsparser.requests[str(diagmode.toUtf8()).decode("utf-8")].sentbytes
            self.sendElm(rq)

        command = self.input.text()
        ascii_cmd = str(command).upper().replace(" ", "")
        output = self.sendElm(ascii_cmd)
        self.output.setText(output)

    def setRefreshTime(self, value):
        self.refreshtime = value

    def initELM(self):
        if not options.simulation_mode:
            if self.ecurequestsparser.ecu_protocol == 'CAN':
                self.logview.append("Initializing CAN mode")
                short_addr = options.elm.get_can_addr(self.ecurequestsparser.ecu_send_id)
                ecu_conf = {'idTx': self.ecurequestsparser.ecu_send_id, 'idRx':
                    self.ecurequestsparser.ecu_recv_id, 'ecuname': str(self.ecu_name)}
                options.elm.init_can()
                options.elm.set_can_addr(short_addr, ecu_conf)
            elif self.ecurequestsparser.ecu_protocol == 'KWP2000':
                self.logview.append("Initializing KWP2000 mode")
                ecu_conf = {'idTx': '', 'idRx': '', 'ecuname': str(self.ecu_name), 'protocol': 'KWP2000'}
                options.opt_si = not self.ecurequestsparser.fastinit
                options.elm.init_iso()
                options.elm.set_iso_addr(self.ecurequestsparser.ecu_send_id, ecu_conf)
            else:
                self.logview.append("Protocol " + self.ecurequestsparser.ecu_protocol + " not supported")
        if self.main_protocol_status:
            if self.ecurequestsparser.ecu_protocol == "CAN":
                txrx = "(Tx 0x%s/Rx 0x%s)" % (self.ecurequestsparser.ecu_send_id,
                                              self.ecurequestsparser.ecu_recv_id)
                self.main_protocol_status.setText("DiagOnCan " + txrx)
            elif self.ecurequestsparser.ecu_protocol == "KWP2000":
                self.main_protocol_status.setText("KWP @ " + self.ecurequestsparser.ecu_send_id)
            elif self.ecurequestsparser.ecu_protocol == "ISO8":
                self.main_protocol_status.setText("ISO8 @ " + self.ecurequestsparser.ecu_send_id)
                print "Protocol not yet supported : " + self.ecurequestsparser.ecu_protocol

    def initJSON(self):
        self.layoutdict = None
        layoutfile = "./json/" + self.ddtfile + ".layout"
        if os.path.exists(layoutfile):
            jsfile = open(layoutfile, "r")
            jsondata = jsfile.read()
            jsfile.close()
        else:
            zf = zipfile.ZipFile("json/layouts.zip", mode='r')
            jsondata = zf.read(self.ddtfile)

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

    def initXML(self):
        self.clearAll()

        if '.json' in self.ddtfile:
            self.parser = 'json'
            self.ecurequestsparser = ecu.Ecu_file(self.ddtfile, True)
            self.initJSON()
            self.initELM()
        else:
            self.parser = 'xml'
            xdom = xml.dom.minidom.parse(self.ddtfile)
            xdoc = xdom.documentElement

            if not xdoc:
                print("XML file not found : " + self.ddtfile)
                return

            self.ecurequestsparser = ecu.Ecu_file(xdoc)

            target = self.getChildNodesByName(xdoc, u"Target")[0]
            if not target:
                self.logview.append("Invalid DDT file")
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
            self.initELM()
        reqk = self.ecurequestsparser.requests.keys()

        if self.ecurequestsparser.ecu_protocol == "CAN":
            self.tester_presend_command = '3E'
            for k in reqk:
                if "tester" in k.lower() and "present" in k.lower():
                    self.tester_presend_command = self.ecurequestsparser.requests[k].sentbytes
                    break

    def sendElm(self, command, auto=False):
        elm_response = '00 ' * 70

        if command.startswith('10'):
            self.logview.append('<font color=blue>Switching to session mode %s</font>' % command)
            if not options.simulation_mode:
                if self.ecurequestsparser.ecu_protocol == "CAN":
                    options.elm.start_session_can(command)
                    return
                elif self.ecurequestsparser.ecu_protocol == "KWP2000":
                    options.elm.start_session_iso(command)
                    return

        if not options.simulation_mode:
            if not options.promode:
                # Allow read only modes
                if command.startswith('3E') or command.startswith('14')\
                        or command.startswith('21') or command.startswith('22')\
                        or command.startswith('17'):

                    elm_response = options.elm.request(command, cache=False)
                    txt = '<font color=blue>Sending ELM request :</font>'
                else:
                    txt = '<font color=green>Blocked ELM request :</font>'
            else:
                # Pro mode *Watch out*
                elm_response = options.elm.request(command, cache=False)
                txt = '<font color=red>Sending ELM request:</font>'
        else:
            if "210A" in command:
                elm_response = "61 0A 16 32 32 02 58 00 B4 3C 3C 1E 3C 0A 0A 0A 0A 01 2C 5C 61 67 B5 BB C1 0A 5C"
            elif "17FF00" in command:
                # Test for ACU4
                elm_response = "57 06 90 07 41 90 08 41 90 42 52 90 08 42 90 07 42 90 7C 40"
                # Test for EDC16
                #elm_response = "57 03 05 34 68 06 70 4F 09 A4 09 A4 17"
            txt = '<font color=green>Sending simulated ELM request :</font>'

        if not auto or options.log_all:
            self.logview.append(txt + command)

        if elm_response.startswith('7F'):
            nrsp = options.elm.errorval(elm_response[6:8])
            self.logview.append("<font color=red>Bad ELM response :</font> " + nrsp)

        if not auto or options.log_all:
            self.logview.append('ELM response : ' + elm_response)

        return elm_response

    def getChildNodesByName(self, parent, name):
        nodes = []
        for node in parent.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.localName == name:
                nodes.append(node)
        return nodes

    def initScreen(self, screen_name):
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

                qbutton.clicked.connect(lambda state, btn=qbutton.butname: self.buttonClicked(btn))

    def drawLabels(self, screen):
        if self.parser == 'xml':
            labels = self.getChildNodesByName(screen, "Label")
            for label in labels:
                qlabel = displaymod.labelWidget(self.panel, self.uiscale)
                qlabel.initXML(label)

        else:
            for label in screen['labels']:
                qlabel = displaymod.labelWidget(self.panel, self.uiscale)
                qlabel.initJson(label)
    
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
            self.logview.append(u"<font color=red>Button request not found : " + txt + u"</font>")
            return

        if txt in self.button_messages:
            messages = self.button_messages[txt]
            for message in messages:
                msgbox = gui.QMessageBox()
                msgbox.setText(message)
                msgbox.exec_()

        request_list = self.button_requests[txt]
        for req in request_list:
            request_delay = float(req['Delay'].encode('ascii'))
            request_name  = req['RequestName']
            self.logview.append(u'<font color=purple>Sending request :</font>' + request_name)

            ecu_request = self.ecurequestsparser.requests[request_name]
            sendbytes_data_items = ecu_request.sendbyte_dataitems
            rcvbytes_data_items = ecu_request.dataitems

            bytes_to_send_ascii = ecu_request.sentbytes.encode('ascii', 'ignore')
            bytes_to_send = [bytes_to_send_ascii[i:i + 2] for i in range(0, len(bytes_to_send_ascii), 2)]
            elm_data_stream = bytes_to_send

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

                if not is_combo_widget:
                    # Get input string from user line edit
                    input_value = widget.text().toAscii()
                else:
                    # Get value from user input combo box
                    combo_value = unicode(widget.currentText().toUtf8(), encoding="UTF-8")
                    items_ref = ecu_data.items
                    input_value = hex(int(items_ref[combo_value]))[2:]

                elm_data_stream = ecu_data.setValue(input_value, elm_data_stream, dataitem, ecu_request.endian)

                if not elm_data_stream:
                    widget.setStyleSheet("background: red")
                    self.logview.append("Request aborted (look at red paramters entries): " + str(input_value))
                    return

                widget.setStyleSheet("background: white")

            # Manage delay
            time.sleep(request_delay / 1000.0)
            # Then show received values
            elm_response = self.sendElm(' '.join(elm_data_stream))

            for key in rcvbytes_data_items.keys():
                if request_name in self.displaydict:
                    data_item = rcvbytes_data_items[key]
                    dd_ecu_data = self.ecurequestsparser.data[key]
                    value = dd_ecu_data.getDisplayValue(elm_response, data_item, ecu_request.endian)
                    dd_request_data = self.displaydict[request_name]
                    data = dd_request_data.getDataByName(key)

                    if value == None:
                        if data: data.widget.setStyleSheet("background: red")
                        value = "Invalid"
                    else:
                        if data: data.widget.setStyleSheet("background: white")

                    if data:
                        data.widget.setText(value + ' ' + dd_ecu_data.unit)

        # Give some time to ECU to refresh parameters
        time.sleep(0.1)
        self.updateDisplays()

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
        for data_struct in request_data.data:
            qlabel = data_struct.widget
            ecu_data = data_struct.data
            data_item = request.dataitems[ecu_data.name]
            #if not data_item.ref:
            #    continue
            value = ecu_data.getDisplayValue(elm_response, data_item, request.endian)

            if value == None:
                qlabel.setStyleSheet("background: red")
                value = "ERROR"
            else:
                qlabel.setStyleSheet("background: white")

            qlabel.setText(value + ' ' + ecu_data.unit)

            if update_inputs:
                for inputkey in self.inputdict:
                    input = self.inputdict[inputkey]
                    if ecu_data.name in input.datadict:
                        data = input.datadict[ecu_data.name]
                        if not data.is_combo:
                            data.widget.setText(value)

    def getRequest(self, requests, reqname):
        if reqname in requests:
            return requests[reqname]
        for req in requests:
            if req.upper() == reqname.upper():
                return requests[req]
        return None

    def updateDisplays(self, update_inputs=False):
        if not self.allow_parameters_update:
            return

        # Begin diag session
        if not options.simulation_mode:
            if self.ecurequestsparser.ecu_protocol == "CAN":
                options.elm.start_session_can('10C0')
            elif self.ecurequestsparser.ecu_protocol == "KWP2000":
                options.elm.start_session_iso('10C0')

        # <Screen> <Send/> <Screen/> tag management
        # Manage pre send commands
        for sendcom in self.panel.presend:
            delay = float(sendcom[0])
            req_name = sendcom[1]

            time.sleep(delay / 1000.)
            request = self.getRequest(self.ecurequestsparser.requests, req_name)
            if not request:
                self.logview.append(u"Cannot call request " + req_name)

            self.sendElm(request.sentbytes, True)

        for request_name in self.displaydict.keys():
            self.updateDisplay(request_name, update_inputs)

        if options.auto_refresh:
            self.timer.start(self.refreshtime)

    def clearDTC(self):
        request = None
        if not options.simulation_mode:
            if self.ecurequestsparser.ecu_protocol == "CAN":
                options.elm.start_session_can('10C0')
            elif self.ecurequestsparser.ecu_protocol == "KWP2000":
                options.elm.start_session_iso('10C0')

        self.logview.append("Clearing DTC information")

        if "ClearDiagnosticInformation.All" in self.ecurequestsparser.requests:
            request = self.ecurequestsparser.requests["ClearDiagnosticInformation.All"].sentbytes
        elif "ClearDTC" in self.ecurequestsparser.requests:
            request = self.ecurequestsparser.requests["ClearDTC"].sentbytes
        elif "Clear Diagnostic Information" in self.ecurequestsparser.requests:
            request = self.ecurequestsparser.requests["Clear Diagnostic Information"].sentbytes
        else:
            self.logview.append("No ClearDTC request for that ECU, will send default 14FF00")
            request = "14FF00"

        msgbox = gui.QMessageBox()
        msgbox.setText("<center>You are about to clear diagnostic troubles codes</center>"
                       "<center>Ae you sure this is what you want.</center>")

        msgbox.setStandardButtons(gui.QMessageBox.Yes)
        msgbox.addButton(gui.QMessageBox.Abort)
        msgbox.setDefaultButton(gui.QMessageBox.Abort)
        userreply = msgbox.exec_()

        if not request:
            return

        if userreply == gui.QMessageBox.Abort:
            return

        self.sendElm(request)

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
        dtc_num = 0
        bytestosend = map(''.join, zip(*[iter(request.sentbytes.encode('ascii'))]*2))

        dtcread_command = ''.join(bytestosend)
        can_response = self.sendElm(dtcread_command)

        if "RESPONSE" in can_response:
            msgbox = gui.QMessageBox()
            msgbox.setText("Invalid response for ReadDTC command")
            msgbox.exec_()
            return

        can_response = can_response.split(' ')

        if len(can_response) == 2:
            #No errors
            msgbox = gui.QMessageBox()
            msgbox.setText("No DTC")
            msgbox.exec_()
            return

        dtcdialog = gui.QDialog(None)
        dtc_view = gui.QTextEdit(None)
        dtc_view.setReadOnly(True)
        layout = gui.QVBoxLayout()
        dtcdialog.setLayout(layout)
        clearbutton = gui.QPushButton("Clear ALL DTC")
        layout.addWidget(clearbutton)
        layout.addWidget(dtc_view)

        clearbutton.clicked.connect(self.clearDTC)

        html = '<h1 style="color:red">ECU trouble codes</color></h1>'

        while len(can_response) >= shiftbytecount + 2:
            html += '<h2 style="color:orange">DTC #%i' % dtc_num + "</h2>"
            html += "<p>"
            for k in request.dataitems.keys():
                ecu_data = self.ecurequestsparser.data[k]
                dataitem = request.dataitems[k]
                value_hex = ecu_data.getHexValue(' '.join(can_response), dataitem, request.endian)

                if value_hex is None:
                    continue

                value = int('0x' + value_hex, 16)

                if ecu_data.scaled:
                    html += "<u>" + dataitem.name + "</u> : " + str(value) + " [" + hex(value) + "]<br>"
                    continue

                if len(ecu_data.items) > 0 and value in ecu_data.lists:
                    html += "<u>" + dataitem.name + "</u> : [" + str(value_hex) + "] " + ecu_data.lists[value] + "<br>"
                else:
                    html += "<u>" + dataitem.name + "</u> : " + str(value) + " [" + hex(value) + "]<br>"
            html += "</p>"
            can_response = can_response[shiftbytecount:]

            dtc_num += 1

        dtc_view.setHtml(html)
        dtcdialog.exec_()


def dumpXML(xmlname):
    xdom = xml.dom.minidom.parse(xmlname)
    xdoc = xdom.documentElement
    return dumpDOC(xdoc)

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
            category_name = toascii(category.getAttribute(u"Name"))
            js_categories[category_name] = []
            screens_name = getChildNodesByName(category, u"Screen")
            for screen in screens_name:
                screen_name = toascii(screen.getAttribute(u"Name"))
                xmlscreens[screen_name] = screen
                js_categories[category_name].append(screen_name)

    for scrname, screen in xmlscreens.iteritems():
        screen_name = toascii(scrname)
        js_screens[screen_name] = {}
        js_screens[screen_name]['width'] = int(screen.getAttribute("Width"))
        js_screens[screen_name]['height'] = int(screen.getAttribute("Height"))
        js_screens[screen_name]['color'] = colorConvert(screen.getAttribute("Color"))
        js_screens[screen_name]['labels'] = {}

        presend = []
        for elem in getChildNodesByName(screen, u"Send"):
            delay = elem.getAttribute('Delay')
            req_name = toascii(elem.getAttribute('RequestName'))
            presend.append((delay, req_name))
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
            display_dict['text'] = toascii(display.getAttribute("DataName"))
            display_dict['request'] = toascii(display.getAttribute("RequestName"))
            display_dict['color'] = colorConvert(display.getAttribute("Color"))
            display_dict['width'] = int(display.getAttribute("Width"))
            display_dict['rect'] = getRectangleXML(getChildNodesByName(display, "Rectangle")[0])
            display_dict['font'] = getFontXML(display)
            display_dict['fontcolor'] = getFontColor(display)
            js_screens[screen_name]['displays'].append(display_dict)

        buttons = getChildNodesByName(screen, "Button")
        js_screens[screen_name]['buttons'] = []
        for button in buttons:
            button_dict = {}
            button_dict['text'] = toascii(button.getAttribute("Text"))
            button_dict['rect'] = getRectangleXML(getChildNodesByName(button, "Rectangle")[0])
            button_dict['font'] = getFontXML(button)

            xmlmessages = getChildNodesByName(button, "Message")
            messages = []
            # Get messages
            for message in xmlmessages:
                messages.append(toascii(message.getAttribute("Text")))

            button_dict['messages'] = messages

            send = getChildNodesByName(button, "Send")
            if send:
                sendlist = []
                for snd in send:
                    smap = {}
                    delay = snd.getAttribute("Delay")
                    reqname = toascii(snd.getAttribute("RequestName"))
                    smap['Delay'] = delay
                    smap['RequestName'] = reqname
                    sendlist.append(smap)
                button_dict['send'] = sendlist

            js_screens[screen_name]['buttons'].append(button_dict)

        inputs = getChildNodesByName(screen, "Input")
        js_screens[screen_name]['inputs'] = []

        for input in inputs:
            input_dict = {}
            input_dict['text'] = toascii(input.getAttribute("DataName"))
            input_dict['request']  = toascii(input.getAttribute("RequestName"))
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


def make_zipfs():
    options.ecus_dir = "./ecus"
    zipoutput = StringIO()
    i = 0
    ecus = glob.glob("ecus/*.xml")
    ecus.remove("ecus/eculist.xml")

    with zipfile.ZipFile(zipoutput, mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for target in ecus:
            name = toascii(target)
            print "Starting zipping " + target + " " + str(i) + "/" + str(len(ecus))
            fileout = name.replace('.xml', '.json')
            dump = dumpXML(name)
            if dump is not None:
                zf.writestr(fileout, str(dump))
            i += 1

    with open("json/layouts.zip", "w") as f:
        f.write(zipoutput.getvalue())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--zipfs', action="store_true", default=None, help="Create a zip filesystem of the XMLs")

    args = parser.parse_args()

    if args.zipfs:
        make_zipfs()
