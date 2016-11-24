import sys
import time
import ecu
import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import options
from xml.dom.minidom import parse
import xml.dom.minidom

# TODO :
# Delay unit (second, milliseconds ?) // Seems ms
# little endian requests // Done needs check
# Read freezeframe data
# Check ELM response validity (mode + 0x40)

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
    def __init__(self, parent, ddtfile, ecu_addr, ecu_name, logview):
        super(paramWidget, self).__init__(parent)
        self.refreshtime = 400
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
        self.startsession_command = '10C0'
        self.timer = core.QTimer()
        self.timer.setSingleShot(True)
        self.initXML()

    def init(self, screen):
        if self.panel:
            self.layout.removeWidget(self.panel)
            self.panel.close()
            self.panel.destroy()

        self.panel = gui.QWidget(self)

        if not screen:
            return False

        scr_init = self.initScreen(screen)
        self.layout.addWidget(self.panel)
        self.initELM()
        return scr_init

    def setRefreshTime(self, value):
        self.refreshtime = value

    def initELM(self):
        if not options.simulation_mode:
            if self.protocol == 'CAN':
                self.logview.append("Initialisation ELM en mode CAN")
                ecu_conf = {'idTx': '', 'idRx': '', 'ecuname': str(self.ecu_name)}
                options.elm.init_can()
                options.elm.set_can_addr(self.ecu_addr, ecu_conf)
            elif self.protocol == 'KWP2000':
                self.logview.append("Initialisation ELM en mode KWP2000")
                ecu_conf = {'idTx': '', 'idRx': '', 'ecuname': str(self.ecu_name), 'protocol': 'KWP2000'}
                options.opt_si = not self.iso_fastinit
                options.elm.init_iso()
                options.elm.set_iso_addr(self.iso_send_id, ecu_conf)
            else:
                self.logview.append("Protocole " + self.protocol + " non supporte")

    def initXML(self):
        self.categories = {}
        self.xmlscreen = {}
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
                    self.can_send_id = hex(int(can_id[0].getAttribute("Value")))

            rcv_ids = self.getChildNodesByName(can, "ReceiveId")
            if rcv_ids:
                rcv_id = rcv_ids[0]
                can_id = self.getChildNodesByName(rcv_id, "CANId")
                if can_id:
                    self.can_rcv_id = hex(int(can_id[0].getAttribute("Value")))

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
                else:
                    self.logview.append("Determination protocol KWP2000 impossible")

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

        if "Start Diagnostic Session" in self.ecurequestsparser.requests:
            diag_request = self.ecurequestsparser.requests["Start Diagnostic Session"]
            self.startsession_command = diag_request.sentbytes
        elif "StartDiagnosticSession" in self.ecurequestsparser.requests:
            diag_request = self.ecurequestsparser.requests["StartDiagnosticSession"]
            self.startsession_command = diag_request.sentbytes
        else:
            print "Cannot find a valid StartDiagnoticSession entry, using default"
            self.startsession_command = '10C0'

    def sendElm(self, command, auto=False):
        txt = ''
        elm_response = '00 ' * 70

        if not options.simulation_mode:
            if not options.promode:
                # Allow read only modes
                if command.startswith('10') or command.startswith('21') or command.startswith('22') or command.startswith('17'):
                    elm_response = options.elm.request(command, cache=False)
                    txt = '<font color=blue>Envoie requete securisee ELM :</font>'
                else:
                    txt = '<font color=green>Requete bloquee ELM :</font>'
            else:
                # Pro mode *Watch out*
                elm_response = options.elm.request(command, cache=False)
                txt = '<font color=red>Envoie requete ELM :</font>'
        else:
            txt = '<font color=green>Envoie requete simulee ELM :</font>'

        if not auto or options.log_all:
            self.logview.append(txt + command)

        if elm_response.startswith('7F'):
            nrsp = options.elm.errorval(elm_response[6:8])
            self.logview.append("<font color=red>Mauvaise reponse ELM :</font> " + nrsp)

        if not auto or options.log_all:
            self.logview.append('Reception ELM : ' + elm_response)

        return elm_response

    def getChildNodesByName(self, parent, name):
        nodes = []
        for node in parent.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.localName == name:
                nodes.append(node)
        return nodes

    def initScreen(self, screen_name):
        self.presend = []
        self.timer.stop()
        if not screen_name in self.xmlscreen.keys():
            return False

        screen = self.xmlscreen[screen_name]
        
        self.screen_width  = int(screen.getAttribute("Width")) / self.uiscale
        self.screen_height = int(screen.getAttribute("Height")) / self.uiscale
        screencolor = screen.getAttribute("Color")
        self.setStyleSheet("background-color: %s" % self.colorConvert(screencolor))

        self.resize(self.screen_width+20, self.screen_height + 20)
        self.panel.resize(self.screen_width+40, self.screen_height + 40)

        for elem in self.getChildNodesByName(screen, u"Send"):
            delay = elem.getAttribute('Delay')
            req_name = elem.getAttribute('RequestName')
            self.presend.append((delay, req_name))

        self.drawLabels(screen)
        self.drawDisplays(screen)
        self.drawInputs(screen)
        self.drawButtons(screen)
        self.updateDisplays(True)
        self.timer.timeout.connect(self.updateDisplays)
        self.timer.start(1000)
        return True

    def colorConvert(self, color):
        hexcolor = hex(int(color) & 0xFFFFFF).replace("0x", "").upper().zfill(6)
        redcolor = int('0x' + hexcolor[0:2], 16)
        greencolor = int('0x' + hexcolor[2:4], 16)
        bluecolor = int('0x' + hexcolor[4:6], 16)
        return 'rgb(%i,%i,%i)' % (bluecolor, greencolor, redcolor)

    def getFontColor(self, xml):
        font = self.getChildNodesByName(xml, "Font")[0]
        return self.colorConvert(font.getAttribute("Color"))
    
    def getRectangle(self, xml):
        rect = {}
        rect['left']    = int(xml.getAttribute("Left"))  / self.uiscale
        rect['top']     = int(xml.getAttribute("Top"))  / self.uiscale
        rect['height']  = int(xml.getAttribute("Height"))  / self.uiscale
        rect['width']   = int(xml.getAttribute("Width"))  / self.uiscale
        return rect
    
    def getFont(self, xml):
        data = {}
        font = self.getChildNodesByName(xml, "Font")[0]
        font_name    = font.getAttribute("Name")
        font_size    = float(font.getAttribute("Size"))
        font_bold    = font.getAttribute("Bold")
        font_italic  = font.getAttribute("Italic")
        
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
        displays = self.getChildNodesByName(screen, "Display")

        for display in displays:
            text = display.getAttribute("DataName")
            req_name = display.getAttribute("RequestName")
            color = display.getAttribute("Color")
            width = int(display.getAttribute("Width")) / self.uiscale
            rect = self.getRectangle(self.getChildNodesByName(display, "Rectangle")[0])
            qfnt = self.getFont(display)
            req = self.ecurequestsparser.requests[req_name]
            dataitem = req.dataitems[text]
            data = self.ecurequestsparser.data[text]

            qlabel = gui.QLabel(self.panel)
            qlabel.setFont(qfnt)
            qlabel.setText(text)
            qlabel.resize(width, rect['height'])
            qlabel.setStyleSheet("background: %s; color: %s" % ( self.colorConvert(color), self.getFontColor(display) ) )
            qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
            qlabel.setAlignment(core.Qt.AlignLeft)
            qlabel.move(rect['left'], rect['top'])
            
            qlabelval = gui.QLabel(self.panel)
            qlabelval.setFont(qfnt)
            qlabelval.setText("")
            qlabelval.resize(rect['width'] - width, rect['height'])
            qlabelval.setStyleSheet("background: %s; color: %s" % ( self.colorConvert(color), self.getFontColor(display) ) )
            qlabelval.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
            qlabelval.move(rect['left'] + width, rect['top'])
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
                    rq = self.ecurequestsparser.requests[reqname]
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
    
    def drawLabels(self, screen):
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
    
    def drawInputs(self,screen):
        self.inputDict = {}
        inputs = self.getChildNodesByName(screen, "Input")
        for input in inputs:
            text      = input.getAttribute("DataName")
            req_name  = input.getAttribute("RequestName")
            color     = input.getAttribute("Color")
            width     = int(input.getAttribute("Width")) / self.uiscale
            rect = self.getRectangle(self.getChildNodesByName(input, "Rectangle")[0])
            qfnt = self.getFont(input)  

            qlabel = gui.QLabel(self.panel)
            qlabel.setFont(qfnt)
            qlabel.setText(text)
            qlabel.setStyleSheet("background: " + self.colorConvert(color))
            qlabel.setStyleSheet("color: " + self.getFontColor(input))
            qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
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
                qcombo.setToolTip(infos)
                ddata = displayData(data, qcombo, True)
            else:
                qlineedit = gui.QLineEdit(self.panel)
                qlineedit.setFont(qfnt)
                qlineedit.setText("No Value")
                qlineedit.resize(rect['width'] - width, rect['height'])
                qlineedit.setStyleSheet("background: " + self.colorConvert(color))
                qlineedit.setStyleSheet("color: " + self.getFontColor(input))
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

    def buttonClicked(self, txt):
        if not txt in self.button_requests:
            self.logview.append(u"<font color=red>Requete bouton non trouvee : " + txt + u"</font>")
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
            self.logview.append(u'<font color=purple>Lancement requete :</font>' + request_name)

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
                    input_value = hex(items_ref[combo_value])[2:]

                elm_data_stream = ecu_data.setValue(input_value, elm_data_stream, dataitem, ecu_request.endian)

                if not elm_data_stream:
                    widget.setStyleSheet("background: red")
                    self.logview.append("Abandon de requete, entree ligne incorrecte (voir entree en rouge): " + str(input_value))
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
                        value = "Invalide"
                    else:
                        if data: data.widget.setStyleSheet("background: white")

                    if data:
                        data.widget.setText(value + ' ' + dd_ecu_data.unit)

        # Give some time to ECU to refresh parameters
        time.sleep(0.8)
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
                value = "ERREUR"
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
            request = self.ecurequestsparser.requests[req_name]

            self.sendElm(request.sentbytes, True)

        for request_name in self.displayDict.keys():
            self.updateDisplay(request_name, update_inputs)

        if options.auto_refresh:
            self.timer.start(self.refreshtime)

    def readDTC(self):
        if not "ReadDTC" in self.ecurequestsparser.requests:
            self.logview.append("Pas de fonction ReadDTC pour ce calculateur")
            return

        if not options.simulation_mode:
            if self.protocol == "CAN":
                options.elm.start_session_can('10C0')
            elif self.protocol == "KWP2000":
                options.elm.start_session_iso('10C0')
            
        request = self.ecurequestsparser.requests["ReadDTC"]
        sendbyte_dataitems = request.sendbyte_dataitems
        moredtcbyte = -1
        
        if "MoreDTC" in sendbyte_dataitems:
            moredtcbyte = sendbyte_dataitems["MoreDTC"].firstbyte - 1

        dtclist = [0]
        if moredtcbyte > 0:
            dtclist = [i for i in range(0, 10)]
        
        dtc_result = {}
        dtc_num = 0
        for dtcnum in dtclist:
            time.sleep(0.1)
            bytestosend = list(request.sentbytes.encode('ascii'))
            if moredtcbyte != -1:
                bytestosend[2 * moredtcbyte + 1] = hex(dtcnum)[-1:]
            dtcread_command = ''.join(bytestosend)
            can_response = self.sendElm(dtcread_command)
            dtc_num += 1

            if "WRONG RESPONSE" in can_response:
                continue

            for k in request.dataitems.keys():
                ecu_data = self.ecurequestsparser.data[k]
                dataitem = request.dataitems[k]
                value_hex = ecu_data.getHexValue(can_response, dataitem, request.endian)

                if value_hex is None:
                    continue
                
                if not dataitem.name in dtc_result:
                    dtc_result[dataitem.name] = []
                
                value = int('0x' + value_hex, 16)

                if ecu_data.scaled:
                    dtc_result[dataitem.name].append(str(value))
                    continue

                if len(ecu_data.items) > 0 and value in ecu_data.lists:
                    dtc_result[dataitem.name].append(ecu_data.lists[value])
                else:
                    dtc_result[dataitem.name].append(str(value))
                    
        columns = dtc_result.keys()
        self.table = gui.QTableWidget(None)
        self.table.setColumnCount(len(columns))
        self.table.setRowCount(dtc_num)
        
        self.table.setHorizontalHeaderLabels(dtc_result.keys())
        i = 0
        for dtc_key in columns:
            j = 0
            for dtc_val in dtc_result[dtc_key]:
                self.table.setItem(j, i, gui.QTableWidgetItem(dtc_val))
                j += 1
            i += 1
        self.table.resizeColumnsToContents()
        self.table.setFixedSize(self.table.horizontalHeader().length() + 40, self.table.verticalHeader().length() + 50);
        self.table.show()

if __name__ == '__main__':
    app = gui.QApplication(sys.argv)
    w = paramWidget(None)
    w.show()
    app.exec_()

