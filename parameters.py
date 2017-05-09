import sys
import time
import ecu, elm
import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import options, os
from xml.dom.minidom import parse
import xml.dom.minidom
import json, unicodedata, argparse, zipfile, glob
from StringIO import StringIO

# TODO :
# Delay unit (second, milliseconds ?) // OK -> ms (from builderX)
# little endian requests // Done needs check
# Read freezeframe data // Done (partially)
# Check ELM response validity (mode + 0x40)


def to_nfkd(input_str):
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])


def toascii(str):
    return to_nfkd(str).encode('ascii', 'ignore')


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


class paramWidget(gui.QWidget):
    def __init__(self, parent, ddtfile, ecu_addr, ecu_name, logview, prot_status):
        super(paramWidget, self).__init__(parent)
        self.main_protocol_status = prot_status
        self.scrollarea = parent
        self.refreshtime = 100
        self.protocol = ''
        self.layout = gui.QHBoxLayout(self)
        self.logview = logview
        self.ddtfile = ddtfile
        self.ecurequestsparser = None
        self.can_send_id = ''
        self.can_rcv_id = ''
        self.iso_send_id = ''
        self.iso_rcv_id = ''
        self.iso_fastinit = False
        self.panel = None
        self.uiscale = 8
        self.ecu_address = ecu_addr
        self.ecu_name = ecu_name
        self.button_requests = {}
        self.button_messages = {}
        self.displayDict = {}
        self.inputDict = {}
        self.presend = []
        self.ecu_addr = str(ecu_addr)
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

    def __del__(self):
        # Return to default session
        self.logview.append("<font color=blue>Returning to defaut session...</font>")
        if not options.simulation_mode:
            if self.protocol == "CAN":
                options.elm.start_session_can('1081')
            elif self.protocol == "KWP2000":
                options.elm.start_session_iso('1081')

    def tester_send(self):
        if self.tester_presend_command == "":
            return

        self.sendElm(self.tester_presend_command, True)

    def mousePressEvent(self, event):
        if event.button() == core.Qt.LeftButton:
            self.sliding = True
            self.mouseOldX = event.globalX()
            self.mouseOldY = event.globalY()

    def mouseReleaseEvent(self, event):
        if event.button() == core.Qt.LeftButton:
            self.sliding = False

    def mouseMoveEvent(self, event):
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
        self.init(self.current_screen)

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

        self.panel = gui.QWidget(self)

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
            if self.protocol == 'CAN':
                self.logview.append("Initializing CAN mode")
                ecu_conf = {'idTx': '', 'idRx': '', 'ecuname': str(self.ecu_name)}
                options.elm.init_can()
                options.elm.set_can_addr(self.ecu_addr, ecu_conf)
            elif self.protocol == 'KWP2000':
                self.logview.append("Initializing KWP2000 mode")
                ecu_conf = {'idTx': '', 'idRx': '', 'ecuname': str(self.ecu_name), 'protocol': 'KWP2000'}
                options.opt_si = not self.iso_fastinit
                options.elm.init_iso()
                options.elm.set_iso_addr(self.iso_send_id, ecu_conf)
            else:
                self.logview.append("Protocol " + self.protocol + " not supported")
        if self.main_protocol_status:
            if self.protocol == "CAN":
                if self.ecu_addr:
                    txrx = "(Tx 0x%s/Rx 0x%s)" % (self.ecurequestsparser.ecu_send_id,
                                                  self.ecurequestsparser.ecu_recv_id)
                    self.main_protocol_status.setText("DiagOnCan " + txrx)
            else:
                self.main_protocol_status.setText("KWP @ " + self.ecu_addr)

    def initJSON(self):
        self.layoutdict = None
        zf = zipfile.ZipFile("json/layouts.zip", mode='r')
        jsondata = zf.read(self.ddtfile)
        self.layoutdict = json.loads(jsondata)

        if self.layoutdict is None:
            return

        protocoldict = self.layoutdict['proto']
        if protocoldict.has_key('fastinit'):
            self.iso_fastinit = protocoldict['fastinit']
        self.iso_rcv_id = protocoldict['recv_id']
        self.iso_send_id = protocoldict['send_id']
        self.ecu_addr = self.iso_send_id

        self.categories = self.layoutdict['categories']
        self.xmlscreen = self.layoutdict['screens']

    def initXML(self):
        self.categories = {}
        self.xmlscreen = {}
        self.parser = ''

        if '.json' in self.ddtfile:
            self.parser = 'json'
            self.ecurequestsparser = ecu.Ecu_file(self.ddtfile, True)
            self.initJSON()
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

            can = self.getChildNodesByName(target, u"CAN")
            if can:
                can = can[0]
                self.protocol = "CAN"
                send_ids = self.getChildNodesByName(can, "SendId")
                if send_ids:
                    send_id = send_ids[0]
                    can_id = self.getChildNodesByName(send_id, "CANId")
                    if can_id:
                        self.can_send_id = hex(int(can_id[0].getAttribute("Value")))[2:].upper()
                        if not options.simulation_mode:
                            self.ecu_addr = options.elm.get_can_addr(self.can_send_id)

                rcv_ids = self.getChildNodesByName(can, "ReceiveId")
                if rcv_ids:
                    rcv_id = rcv_ids[0]
                    can_id = self.getChildNodesByName(rcv_id, "CANId")
                    if can_id:
                        self.can_rcv_id = hex(int(can_id[0].getAttribute("Value")))[2:].upper()

            k = self.getChildNodesByName(target, u"K")
            if k:
                kwp = self.getChildNodesByName(k[0], u"KWP")
                if kwp:
                    kwp = kwp[0]
                    self.protocol = "KWP2000"
                    fastinit = self.getChildNodesByName(kwp, "FastInit")
                    if fastinit:
                        self.iso_fastinit = True
                        self.iso_rcv_id = hex(int(self.getChildNodesByName(fastinit[0], "KW1")[0].getAttribute("Value")))[2:].upper()
                        self.iso_send_id = hex(int(self.getChildNodesByName(fastinit[0], "KW2")[0].getAttribute("Value")))[2:].upper()
                        self.ecu_addr = self.iso_send_id
                    else:
                        self.logview.append("Cannot init KWP2000 protocol")

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

        if self.protocol == "CAN":
            self.tester_presend_command = '3E'
            for k in reqk:
                if "testerpresent" in k.lower() or "tester_present" in k.lower():
                    self.tester_presend_command = self.ecurequestsparser.requests[k].sentbytes
                    break

    def sendElm(self, command, auto=False):
        txt = ''
        elm_response = '00 ' * 70

        if command.startswith('10'):
            self.logview.append('<font color=blue>Switching to session mode %s</font>' % command)
            if not options.simulation_mode:
                if self.protocol == "CAN":
                    options.elm.start_session_can(command)
                    return
                elif self.protocol == "KWP2000":
                    options.elm.start_session_iso(command)
                    return

        if not options.simulation_mode:
            if not options.promode:
                # Allow read only modes
                if command.startswith('3E') or command.startswith('21') or command.startswith('22') or command.startswith('17'):
                    elm_response = options.elm.request(command, cache=False)
                    txt = '<font color=blue>Sending simulated ELM request :</font>'
                else:
                    txt = '<font color=green>Blocked ELM request :</font>'
            else:
                # Pro mode *Watch out*
                elm_response = options.elm.request(command, cache=False)
                txt = '<font color=red>Sending ELM request:</font>'
        else:

            if "17FF00" in command:
                elm_response = "57 06 90 07 41 90 08 41 90 42 52 90 08 42 90 07 42 90 7C 40"
            if "17FFFF" in command:
                elm_response = "WRONG RESPONSE"
            txt = '<font color=green>Sending simulated ELM request :</font>'

        if not auto or options.log_all:
            self.logview.append(txt + command)

        if elm_response.startswith('7F'):
            nrsp = options.elm.errorval(elm_response[6:8])
            self.logview.append("<font color=red>Bad ELM response:</font> " + nrsp)

        if not auto or options.log_all:
            self.logview.append('ELM response: ' + elm_response)

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

        if self.parser == 'xml':
            self.screen_width  = int(screen.getAttribute("Width")) / self.uiscale + 40
            self.screen_height = int(screen.getAttribute("Height")) / self.uiscale + 40
            screencolor = screen.getAttribute("Color")
            self.setStyleSheet("background-color: %s" % self.colorConvert(screencolor))

            for elem in self.getChildNodesByName(screen, u"Send"):
                delay = elem.getAttribute('Delay')
                req_name = elem.getAttribute('RequestName')
                self.presend.append((delay, req_name))
        else:
            self.screen_width = int(screen['width']) / self.uiscale + 40
            self.screen_height = int(screen['height']) / self.uiscale + 40
            self.setStyleSheet("background-color: %s" % screen['color'])

            self.presend = screen['presend']

        self.panel.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.resize(self.screen_width + 100, self.screen_height + 100)
        self.panel.resize(self.screen_width, self.screen_height)

        self.drawLabels(screen)
        self.drawDisplays(screen)
        self.drawInputs(screen)
        self.drawButtons(screen)
        self.updateDisplays(True)
        self.timer.timeout.connect(self.updateDisplays)
        return True

    def colorConvert(self, color):
        hexcolor = hex(int(color) & 0xFFFFFF).replace("0x", "").upper().zfill(6)
        redcolor = int('0x' + hexcolor[0:2], 16)
        greencolor = int('0x' + hexcolor[2:4], 16)
        bluecolor = int('0x' + hexcolor[4:6], 16)
        return 'rgb(%i,%i,%i)' % (bluecolor, greencolor, redcolor)

    def getFontColor(self, xml):
        font = self.getChildNodesByName(xml, "Font")[0]
        if font.getAttribute("Color"):
            return self.colorConvert(font.getAttribute("Color"))
        else:
            return self.colorConvert(0xFFFFFF)
    
    def getRectangle(self, xml):
        rect = {}
        rect['left'] = int(xml.getAttribute("Left")) / self.uiscale
        rect['top'] = int(xml.getAttribute("Top")) / self.uiscale
        rect['height'] = int(xml.getAttribute("Height")) / self.uiscale
        rect['width'] = int(xml.getAttribute("Width")) / self.uiscale
        return rect
    
    def getFont(self, xml):
        font = self.getChildNodesByName(xml, "Font")[0]
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
        
        qfnt = gui.QFont(font_name, font_size, fnt_flags);
        
        return qfnt

    def jsonFont(self, fnt):
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

    def drawDisplays(self, screen):
        self.displayDict = {}
        if self.parser == 'xml':
            displays = self.getChildNodesByName(screen, "Display")

            for display in displays:
                text = display.getAttribute("DataName")
                req_name = display.getAttribute("RequestName")
                color = display.getAttribute("Color")
                width = int(display.getAttribute("Width")) / self.uiscale
                rect = self.getRectangle(self.getChildNodesByName(display, "Rectangle")[0])
                qfnt = self.getFont(display)
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
                    continue

                data = self.ecurequestsparser.data[text]

                if not color:
                    color = 0xAAAAAA

                qlabel = gui.QLabel(self.panel)
                qlabel.setFont(qfnt)
                qlabel.setText(text)
                qlabel.resize(width, rect['height'])
                qlabel.setStyleSheet("background: %s; color: %s" % (self.colorConvert(color), self.getFontColor(display)))
                qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
                qlabel.setAlignment(core.Qt.AlignLeft)
                qlabel.move(rect['left'], rect['top'])

                qlabelval = gui.QLabel(self.panel)
                qlabelval.setFont(qfnt)
                qlabelval.setText("")
                qlabelval.resize(rect['width'] - width, rect['height'])
                qlabelval.setStyleSheet("background: %s; color: %s" % (self.colorConvert(color), self.getFontColor(display)))
                qlabelval.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
                qlabelval.move(rect['left'] + width, rect['top'])
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
                qlabelval.setToolTip(infos)

                ddata = displayData(data, qlabelval)
                if not req_name in self.displayDict:
                    self.displayDict[req_name] = displayDict(req_name, req)

                dd = self.displayDict[req_name]
                dd.addData(ddata)
        else:
            displays = screen['displays']
            for display in displays:
                text = display['text']
                req_name = display['request']
                color = display['color']
                width = display['width'] / self.uiscale
                rect = display['rect']
                qfnt = self.jsonFont(display['font'])
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
                    continue

                data = self.ecurequestsparser.data[text]

                qlabel = gui.QLabel(self.panel)
                qlabel.setFont(qfnt)
                qlabel.setText(text)
                qlabel.resize(width, rect['height'] / self.uiscale)
                qlabel.setStyleSheet("background: %s; color: %s" % (color, fontcolor))
                qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
                qlabel.setAlignment(core.Qt.AlignLeft)
                qlabel.move(rect['left'] / self.uiscale, rect['top'] / self.uiscale)

                qlabelval = gui.QLabel(self.panel)
                qlabelval.setFont(qfnt)
                qlabelval.setText("")
                qlabelval.resize(rect['width'] / self.uiscale - width, rect['height'] / self.uiscale)
                qlabelval.setStyleSheet("background: %s; color: %s" % (color, fontcolor))
                qlabelval.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
                qlabelval.move(rect['left'] / self.uiscale + width, rect['top'] / self.uiscale)
                infos = req_name + u'\n'
                if data.comment:
                    infos += data.comment + u'\n'
                infos += u"Request=" + unicode(req.sentbytes) + u' ManualRequest=' + unicode(req.manualsend)
                infos += u'\nNumBits=' + unicode(data.bitscount)
                infos += u' FirstByte=' + unicode(dataitem.firstbyte)
                infos += u' BitOffset=' + unicode(dataitem.bitoffset)
                qlabelval.setToolTip(infos)

                ddata = displayData(data, qlabelval)
                if not req_name in self.displayDict:
                    self.displayDict[req_name] = displayDict(req_name, req)

                dd = self.displayDict[req_name]
                dd.addData(ddata)

    def drawButtons(self, screen):
        self.button_requests = {}
        self.button_messages = {}
        if self.parser == 'xml':
            buttons = self.getChildNodesByName(screen, "Button")
            button_count = 0

            for button in buttons:
                text = button.getAttribute("Text")
                rect = self.getRectangle(self.getChildNodesByName(button, "Rectangle")[0])
                qfnt = self.getFont(button)
                messages = self.getChildNodesByName(button, "Message")

                qbutton = gui.QPushButton(text, self.panel)
                qbutton.setFont(qfnt)
                qbutton.setText(text)
                qbutton.resize(rect['width'], rect['height'])
                qbutton.setStyleSheet("background: red; color: black")
                qbutton.move(rect['left'], rect['top'])
                butname = text + "_" + str(button_count)
                button_count += 1

                # Get messages
                for message in messages:
                    messagetext = message.getAttribute("Text")
                    if not messagetext:
                        continue
                    if not butname in self.button_messages:
                        self.button_messages[butname] = []
                    self.button_messages[butname].append(messagetext)

                # Get requests to send
                send = self.getChildNodesByName(button, "Send")
                if send:
                    sendlist = []
                    for snd in send:
                        smap = {}
                        delay  = snd.getAttribute("Delay")
                        reqname = snd.getAttribute("RequestName")
                        smap['Delay']       = delay
                        smap['RequestName'] = reqname
                        sendlist.append(smap)
                    self.button_requests[butname] = sendlist
                    tooltiptext = ''
                    for k in smap.keys():
                        tooltiptext += smap[k] + '\n'
                    tooltiptext = tooltiptext[0:-1]
                    qbutton.setToolTip(tooltiptext)

                qbutton.clicked.connect(lambda state, btn=butname: self.buttonClicked(btn))
        else:
            button_count = 0
            for button in screen['buttons']:
                text = button['text']
                rect = button['rect']
                qfnt = self.jsonFont(button['font'])
                self.button_messages = button['messages']

                qbutton = gui.QPushButton(text, self.panel)
                qbutton.setFont(qfnt)
                qbutton.setText(text)
                qbutton.resize(rect['width'] / self.uiscale, rect['height'] / self.uiscale)
                qbutton.setStyleSheet("background: red; color: black")
                qbutton.move(rect['left'] / self.uiscale, rect['top'] / self.uiscale)
                butname = text + "_" + str(button_count)
                button_count += 1

                self.button_messages = button['messages']

                if 'send' in button:
                    sendlist = button['send']
                    self.button_requests[butname] = sendlist

                qbutton.clicked.connect(lambda state, btn=butname: self.buttonClicked(btn))

    def drawLabels(self, screen):
        if self.parser == 'xml':
            labels = self.getChildNodesByName(screen, "Label")
            for label in labels:
                text = label.getAttribute("Text")
                color = label.getAttribute("Color")
                alignment = label.getAttribute("Alignment")

                rect = self.getRectangle(self.getChildNodesByName(label, "Rectangle")[0])
                qfnt = self.getFont(label)

                qlabel = gui.QLabel(self.panel)
                qlabel.setFont(qfnt)
                qlabel.setText(text)
                qlabel.resize(rect['width'], rect['height'])
                qlabel.setStyleSheet("background: %s; color: %s" % (self.colorConvert(color), self.getFontColor(label)))

                qlabel.move(rect['left'], rect['top'])
                if alignment == '2':
                    qlabel.setAlignment(core.Qt.AlignHCenter)
                else:
                    qlabel.setAlignment(core.Qt.AlignLeft)
        else:
            for label in screen['labels']:
                text = label['text']
                color = label['color']
                alignment = label['alignment']
                fontcolor = label['fontcolor']

                rect = label['bbox']
                qfnt = self.jsonFont(label['font'])

                qlabel = gui.QLabel(self.panel)
                qlabel.setFont(qfnt)
                qlabel.setText(text)
                qlabel.resize(rect['width'] / self.uiscale, rect['height'] / self.uiscale)
                qlabel.setStyleSheet("background: %s; color: %s" % (color, fontcolor))

                qlabel.move(rect['left'] / self.uiscale, rect['top'] / self.uiscale)
                if alignment == '2':
                    qlabel.setAlignment(core.Qt.AlignHCenter)
                else:
                    qlabel.setAlignment(core.Qt.AlignLeft)
    
    def drawInputs(self,screen):
        self.inputDict = {}
        if self.parser == 'xml':
            inputs = self.getChildNodesByName(screen, "Input")
            for input in inputs:
                text      = input.getAttribute("DataName")
                req_name  = input.getAttribute("RequestName")
                color     = input.getAttribute("Color")
                width     = int(input.getAttribute("Width")) / self.uiscale
                rect = self.getRectangle(self.getChildNodesByName(input, "Rectangle")[0])
                qfnt = self.getFont(input)

                if not color:
                    color = 0xAAAAAA

                qlabel = gui.QLabel(self.panel)
                qlabel.setFont(qfnt)
                qlabel.setText(text)
                qlabel.setStyleSheet("background:%s; color:%s" % (self.colorConvert(color), self.getFontColor(input)))
                qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken)
                qlabel.resize(rect['width'], rect['height'])
                qlabel.move(rect['left'], rect['top'])
                data = self.ecurequestsparser.data[text]

                if len(self.ecurequestsparser.data[text].items) > 0:
                    qcombo = gui.QComboBox(self.panel)
                    items_ref = self.ecurequestsparser.data[text].items

                    for key in items_ref.keys():
                        qcombo.addItem(key)

                    qcombo.resize(rect['width'] - width, rect['height'])
                    qcombo.move(rect['left'] + width, rect['top'])
                    if data.comment:
                        infos = data.comment + u'\n' + req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
                    else:
                        infos = req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
                    #infos += u' bitOffset=' + unicode(items_ref.bitoffset)
                    qcombo.setToolTip(infos)
                    qcombo.setStyleSheet("background:%s; color:%s" % (self.colorConvert(color), self.getFontColor(input)))
                    ddata = displayData(data, qcombo, True)
                else:
                    qlineedit = gui.QLineEdit(self.panel)
                    qlineedit.setFont(qfnt)
                    qlineedit.setText("No Value")
                    qlineedit.resize(rect['width'] - width, rect['height'])
                    qlineedit.setStyleSheet("background:%s; color:%s" % (self.colorConvert(color), self.getFontColor(input)))
                    qlineedit.move(rect['left'] + width, rect['top'])
                    if data.comment:
                        infos = data.comment + u'\n' + req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
                    else:
                        infos = req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
                    qlineedit.setToolTip(infos)
                    ddata = displayData(data, qlineedit)

                if not req_name in self.inputDict:
                    req = self.ecurequestsparser.requests[req_name]
                    self.inputDict[req_name] = displayDict(req_name, req)

                dd = self.inputDict[req_name]
                dd.addData(ddata)
        else:
            for input in screen['inputs']:
                text = input['text']
                req_name = input['request']
                color = input['color']
                width = input['width'] / self.uiscale
                rect = input['rect']
                qfnt = self.jsonFont(input['font'])
                fntcolor = input['fontcolor']

                qlabel = gui.QLabel(self.panel)
                qlabel.setFont(qfnt)
                qlabel.setText(text)
                qlabel.setStyleSheet("background:%s; color:%s" % (color, input))
                qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken)
                qlabel.resize(rect['width'] / self.uiscale, rect['height'] / self.uiscale)
                qlabel.move(rect['left'] / self.uiscale, rect['top'] / self.uiscale)
                data = self.ecurequestsparser.data[text]

                if len(self.ecurequestsparser.data[text].items) > 0:
                    qcombo = gui.QComboBox(self.panel)
                    items_ref = self.ecurequestsparser.data[text].items

                    for key in items_ref.keys():
                        qcombo.addItem(key)

                    qcombo.resize(rect['width'] / self.uiscale - width, rect['height'] / self.uiscale)
                    qcombo.move(rect['left'] / self.uiscale + width, rect['top'] / self.uiscale)
                    if data.comment:
                        infos = data.comment + u'\n' + req_name + u' : ' + text + u'\nNumBits=' + unicode(
                            data.bitscount)
                    else:
                        infos = req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
                    # infos += u' bitOffset=' + unicode(items_ref.bitoffset)
                    qcombo.setToolTip(infos)
                    qcombo.setStyleSheet(
                        "background:%s; color:%s" % (color, fntcolor))
                    ddata = displayData(data, qcombo, True)
                else:
                    qlineedit = gui.QLineEdit(self.panel)
                    qlineedit.setFont(qfnt)
                    qlineedit.setText("No Value")
                    qlineedit.resize(rect['width'] / self.uiscale - width, rect['height'] / self.uiscale)
                    qlineedit.setStyleSheet(
                        "background:%s; color:%s" % (color, fntcolor))
                    qlineedit.move(rect['left'] / self.uiscale + width, rect['top'] / self.uiscale)
                    if data.comment:
                        infos = data.comment + u'\n' + req_name + u' : ' + text + u'\nNumBits=' + unicode(
                            data.bitscount)
                    else:
                        infos = req_name + u' : ' + text + u'\nNumBits=' + unicode(data.bitscount)
                    qlineedit.setToolTip(infos)
                    ddata = displayData(data, qlineedit)

                if not req_name in self.inputDict:
                    req = self.ecurequestsparser.requests[req_name]
                    self.inputDict[req_name] = displayDict(req_name, req)

                dd = self.inputDict[req_name]
                dd.addData(ddata)

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

                if not request_name in self.inputDict:
                    # Simple command with no user parameters
                    continue

                inputdict = self.inputDict[request_name]
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
                if request_name in self.displayDict:
                    data_item = rcvbytes_data_items[key]
                    dd_ecu_data = self.ecurequestsparser.data[key]
                    value = dd_ecu_data.getDisplayValue(elm_response, data_item, ecu_request.endian)
                    dd_request_data = self.displayDict[request_name]
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
        request_data = self.displayDict[request_name]
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
                for inputkey in self.inputDict:
                    input = self.inputDict[inputkey]
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

    def updateDisplays(self, update_inputs= False):
        # Begin diag session
        if not options.simulation_mode:
            if self.protocol == "CAN":
                options.elm.start_session_can('10C0')
            elif self.protocol == "KWP2000":
                options.elm.start_session_iso('10C0')

        # <Screen> <Send/> <Screen/> tag management
        # Manage pre send commands
        for sendcom in self.presend:
            delay = float(sendcom[0])
            req_name = sendcom[1]

            time.sleep(delay / 1000.)
            request = self.getRequest(self.ecurequestsparser.requests, req_name)
            if not request:
                self.logview.append(u"Cannot call request " + req_name)

            self.sendElm(request.sentbytes, True)

        for request_name in self.displayDict.keys():
            self.updateDisplay(request_name, update_inputs)

        if options.auto_refresh:
            self.timer.start(self.refreshtime)

    def clearDTC(self):
        request = None
        if not options.simulation_mode:
            if self.protocol == "CAN":
                options.elm.start_session_can('10C0')
            elif self.protocol == "KWP2000":
                options.elm.start_session_iso('10C0')

        if "ClearDiagnosticInformation.All" in self.ecurequestsparser.requests:
            request = self.ecurequestsparser.requests["ClearDiagnosticInformation.All"].sentbytes
            self.logview.append("Clearing DTC information")
        elif "ClearDTC" in self.ecurequestsparser.requests:
            self.logview.append("Clearing DTC information")
            request = self.ecurequestsparser.requests["ClearDTC"].sentbytes
        else:
            self.logview.append("No ClearDTC request for that ECU, will send default 14FFFFFF")
            request = "14FFFFFF"

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
            if self.protocol == "CAN":
                options.elm.start_session_can('10C0')
            elif self.protocol == "KWP2000":
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

        while len(can_response) >= shiftbytecount:
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


def getRectangle(xml):
    rect = {}
    rect['left'] = int(xml.getAttribute("Left"))
    rect['top'] = int(xml.getAttribute("Top"))
    rect['height'] = int(xml.getAttribute("Height"))
    rect['width'] = int(xml.getAttribute("Width"))
    return rect

def getFontColor(xml):
    font = getChildNodesByName(xml, "Font")[0]
    if font.getAttribute("Color"):
        return colorConvert(font.getAttribute("Color"))
    else:
        return colorConvert(0xAAAAAA)


def getFont(xml):
    f = {}
    font = getChildNodesByName(xml, "Font")[0]
    f['name'] = font.getAttribute("Name")
    f['size'] = float(font.getAttribute("Size"))
    f['bold'] = font.getAttribute("Bold")
    f['italic'] = font.getAttribute("Italic")
    return f

def dumpXML(xmlname):
    xdom = xml.dom.minidom.parse(xmlname)
    xdoc = xdom.documentElement

    target = getChildNodesByName(xdoc, u"Target")
    if not target:
        return None

    target = target[0]
    js_proto = {}
    js_screens = {}

    can = getChildNodesByName(target, u"CAN")
    if can:
        js_proto['protocol'] = "CAN"
        send_ids = getChildNodesByName(can[0], "SendId")
        if send_ids:
            send_id = send_ids[0]
            can_id = getChildNodesByName(send_id, "CANId")
            if can_id:
                js_proto['send_id'] = hex(int(can_id[0].getAttribute("Value")))[2:].upper()

        rcv_ids = getChildNodesByName(can[0], "ReceiveId")
        if rcv_ids:
            rcv_id = rcv_ids[0]
            can_id = getChildNodesByName(rcv_id, "CANId")
            if can_id:
                js_proto['recv_id'] = hex(int(can_id[0].getAttribute("Value")))[2:].upper()

    k = getChildNodesByName(target, u"K")
    if k:
        kwp = getChildNodesByName(k[0], u"KWP")
        if kwp:
            kwp = kwp[0]
            js_proto['protocol'] = "KWP2000"
            fastinit = getChildNodesByName(kwp, "FastInit")
            if fastinit:
                js_proto['fastinit'] = True
            else:
                return None
            js_proto['recv_id'] = hex(int(getChildNodesByName(fastinit[0], "KW1")[0].getAttribute("Value")))[
                                  2:].upper()
            js_proto['send_id'] = hex(int(getChildNodesByName(fastinit[0], "KW2")[0].getAttribute("Value")))[
                                  2:].upper()

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
            label_dict['bbox'] = getRectangle(getChildNodesByName(label, "Rectangle")[0])
            label_dict['font'] = getFont(label)
            js_screens[screen_name]['labels'].append(label_dict)

        displays = getChildNodesByName(screen, "Display")
        js_screens[screen_name]['displays'] = []
        for display in displays:
            display_dict = {}
            display_dict['text'] = toascii(display.getAttribute("DataName"))
            display_dict['request'] = toascii(display.getAttribute("RequestName"))
            display_dict['color'] = colorConvert(display.getAttribute("Color"))
            display_dict['width'] = int(display.getAttribute("Width"))
            display_dict['rect'] = getRectangle(getChildNodesByName(display, "Rectangle")[0])
            display_dict['font'] = getFont(display)
            display_dict['fontcolor'] = getFontColor(display)
            js_screens[screen_name]['displays'].append(display_dict)

        buttons = getChildNodesByName(screen, "Button")
        js_screens[screen_name]['buttons'] = []
        for button in buttons:
            button_dict = {}
            button_dict['text'] = toascii(button.getAttribute("Text"))
            button_dict['rect'] = getRectangle(getChildNodesByName(button, "Rectangle")[0])
            button_dict['font'] = getFont(button)

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
            input_dict['rect'] = getRectangle(getChildNodesByName(input, "Rectangle")[0])
            input_dict['font'] = getFont(input)
            js_screens[screen_name]['inputs'].append(input_dict)

    return json.dumps({'proto': js_proto, 'screens': js_screens, 'categories': js_categories}, indent=1)

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
