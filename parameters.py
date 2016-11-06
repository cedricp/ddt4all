import sys, os
import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import options
from   xml.dom.minidom import parse
import xml.dom.minidom

import ecu

class Param_widget(gui.QWidget):
    def __init__(self, parent, ddtfile, ecu_addr, ecu_name, logview):
        super(Param_widget, self).__init__(parent)
        self.logview           = logview
        self.ddtfile           = ddtfile
        self.ecurequestsparser = None
        self.can_send_id       = 0
        self.can_rcv_id        = 0
        self.panel             = None
        self.layout            = gui.QHBoxLayout(self)
        self.uiscale           = 15
        self.ecu_address       = ecu_addr
        self.ecu_name          = ecu_name
        self.startsession_command = '10C0'
        self.initXML()
                 
        if not options.simulation_mode:
            ecu_conf = { 'idTx' : self.can_send_id, 'idRx' : self.can_rcv_id, 'ecuname' : ecu_name }
            options.elm.set_can_addr(self.ecu_addr, ecu_conf)
                        
    def init(self, screen):
        if self.panel:
            self.layout.removeWidget(self.panel)
            self.panel.close()
            self.panel.destroy()
        self.panel              = gui.QWidget(self)
        self.button_requests    = {}
        self.display_input      = {}
        self.display_labels     = {}
        self.display_labels_req = {}
        self.button_requests    = {}
        self.display_labels_req = {}
        self.display_values     = {}
        self.elm_req_cache      = {}
        self.timer              = core.QTimer()
        self.timer.setSingleShot(True)
        self.initScreen(screen)
        self.layout.addWidget(self.panel)
         
    def initXML(self):
        self.categories = {}
        self.xmlscreen = {}
        xdom = xml.dom.minidom.parse(self.ddtfile)
        xdoc = xdom.documentElement
        
        if not xdoc:
            print("XML file not found : " + self.ddtfile)
            return
            
        self.ecurequestsparser = ecu.Ecu_file(xdoc)
        
        send_id = xdoc.getElementsByTagName("SendId")
        if send_id:
            can_id = send_id.item(0).getElementsByTagName("CANId")
            self.can_send_id = hex(int(can_id.item(0).getAttribute("Value")))
        
        rcv_id = xdoc.getElementsByTagName("ReceiveId")
        if rcv_id:
            can_id = rcv_id.item(0).getElementsByTagName("CANId")
            self.can_rcv_id = hex(int(can_id.item(0).getAttribute("Value")))

        xml_cats = xdoc.getElementsByTagName("Category")
        for category in xml_cats:
            category_name = category.getAttribute("Name")
            self.categories[category_name] = []
            screens_name = category.getElementsByTagName("Screen")
            for screen in screens_name:
                screen_name = screen.getAttribute("Name")
                self.xmlscreen[screen_name] = screen
                self.categories[category_name].append(screen_name)

        if self.ecurequestsparser.requests.has_key("Start Diagnostic Session"):
            diag_request = self.ecurequestsparser.requests["Start Diagnostic Session"]
            self.startsession_command = diag_request.sentbytes
        elif self.ecurequestsparser.requests.has_key("StartDiagnosticSession"):
            diag_request = self.ecurequestsparser.requests["StartDiagnosticSession"]
            self.startsession_command = diag_request.sentbytes
        else:
            print "Cannot find a valid StartDiagnoticSession entry, using default"
            self.startsession_command = '10C0'

    def sendElm(self, command, auto=False):
        if not auto:
            self.logview.append('ELM Send : ' + command)

        if not options.simulation_mode:
            elm_response = options.elm.request(command=command, cache=False)
        else:
            elm_response = ''.zfill(90)

        if not auto:
            self.logview.append('ELM Receive : ' + elm_response)
        return elm_response

    def initScreen(self, screen_name):
        self.timer.stop()
        if not screen_name in self.xmlscreen.keys():
            return
        screen = self.xmlscreen[screen_name]
        
        rectangles = screen.getElementsByTagName("Rectangle")
        self.screen_width  = 0
        self.screen_height = 0
        
        for rectangle in rectangles:
            rect = self.getRectangle(rectangle)
            
            if rect['left'] + rect['width'] > self.screen_width:
                self.screen_width = rect['left'] + rect['width']
                
            if rect['top'] + rect['height'] > self.screen_height:
                self.screen_height = rect['top'] + rect['height']
        
        self.resize(self.screen_width+20, self.screen_height+20)
        self.panel.resize(self.screen_width+40, self.screen_height+40)
        self.drawLabels(screen)
        self.drawDisplays(screen)
        self.drawInputs(screen)
        self.drawButtons(screen)
        self.timer.timeout.connect(self.updateDisplays)
        self.timer.start(1000)

    def colorConvert(self, color):
        return '#'+hex(int(color)).replace("0x","").zfill(6).upper()
    
    def getFontColor(self, xml):
        font = xml.getElementsByTagName("Font").item(0)
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
        font = xml.getElementsByTagName("Font").item(0)
        font_name    = font.getAttribute("Name")
        font_size    = float(font.getAttribute("Size"))
        font_bold    = font.getAttribute("Bold")
        font_italic  = font.getAttribute("Italic")
        
        if font_bold == '1':
            fnt_flags = gui.QFont.Bold
        else:
            fnt_flags = gui.QFont.Normal
        
        qfnt = gui.QFont(font_name, int(font_size), fnt_flags);
        if font_italic == '1':
            qfnt.setStyle(gui.QFont.StyleItalic)
        
        return qfnt
    
    def drawDisplays(self, screen):
        self.display_labels = {}
        self.display_labels_req = {}
        displays = screen.getElementsByTagName("Display")
        for display in displays:
            text      = display.getAttribute("DataName")
            req_name  = display.getAttribute("RequestName")
            color     = display.getAttribute("Color")
            width     = int(display.getAttribute("Width")) / self.uiscale
            rect = self.getRectangle(display.getElementsByTagName("Rectangle").item(0))
            qfnt = self.getFont(display)
            
            qlabel = gui.QLabel(self.panel)
            qlabel.setFont(qfnt)
            qlabel.setText(text)
            qlabel.resize(width, rect['height'])
            qlabel.setStyleSheet("background-color: %s; color: %s" % ( self.colorConvert(color), self.getFontColor(display) ) )
            qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
            qlabel.setAlignment(core.Qt.AlignLeft)
            qlabel.move(rect['left'], rect['top'])
            
            qlabelval = gui.QLabel(self.panel)
            qlabelval.setFont(qfnt)
            qlabelval.setText("")
            qlabelval.resize(rect['width'] - width, rect['height'])
            qlabelval.setStyleSheet("background-color: %s; color: %s" % ( self.colorConvert(color), self.getFontColor(display) ) )
            qlabelval.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
            qlabelval.move(rect['left'] + width, rect['top'])
            qlabelval.setToolTip(req_name)
            
            self.display_labels[text]     = qlabel
            self.display_values[text]     = qlabelval
            self.display_labels_req[text] = self.ecurequestsparser.requests[req_name]
            
    def drawButtons(self, screen):
        self.button_requests = {}
        buttons = screen.getElementsByTagName("Button")
        button_count = 0
        for button in buttons:
            text = button.getAttribute("Text")
            rect = self.getRectangle(button.getElementsByTagName("Rectangle").item(0))
            qfnt = self.getFont(button)
            
            qbutton = gui.QPushButton(text, self.panel)
            qbutton.setFont(qfnt)
            qbutton.setText(text)
            qbutton.resize(rect['width'], rect['height'])
            qbutton.setStyleSheet("background-color: red; color: black")
            qbutton.move(rect['left'], rect['top'])
            butname = text + "_" + str(button_count)
            button_count += 1
            send = button.getElementsByTagName("Send")
            if send:
                sendlist = []
                for snd in send:
                    smap = {}
                    delay       = snd.getAttribute("Delay")
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
    
    def drawLabels(self, screen):
        labels = screen.getElementsByTagName("Label")
        for label in labels:
            text      = label.getAttribute("Text")
            color     = label.getAttribute("Color")
            alignment = label.getAttribute("Alignment")
            
            rect = self.getRectangle(label.getElementsByTagName("Rectangle").item(0))
            qfnt = self.getFont(label)
                
            qlabel = gui.QLabel(self.panel)
            qlabel.setFont(qfnt)
            qlabel.setText(text)
            qlabel.resize(rect['width'], rect['height'])
            qlabel.setStyleSheet("background-color: %s; color: %s" % (self.colorConvert(color), self.getFontColor(label)))
            #qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
            qlabel.move(rect['left'], rect['top'])
            if alignment == '2':
                qlabel.setAlignment(core.Qt.AlignHCenter)
            else:
                qlabel.setAlignment(core.Qt.AlignLeft)
    
    def drawInputs(self,screen):
        self.display_inputs = {}
        self.inputs = {}
        inputs = screen.getElementsByTagName("Input")
        for input in inputs:
            text      = input.getAttribute("DataName")
            req       = input.getAttribute("RequestName")
            color     = input.getAttribute("Color")
            width     = int(input.getAttribute("Width")) / self.uiscale
            rect = self.getRectangle(input.getElementsByTagName("Rectangle").item(0))
            qfnt = self.getFont(input)  

            qlabel = gui.QLabel(self.panel)
            qlabel.setFont(qfnt)
            qlabel.setText(text)
            qlabel.resize(rect['width'], rect['height'])
            qlabel.setStyleSheet("background-color: " + self.colorConvert(color))
            qlabel.setStyleSheet("color: " + self.getFontColor(input))
            qlabel.setFrameStyle(gui.QFrame.Panel | gui.QFrame.Sunken);
            qlabel.move(rect['left'], rect['top'])
            
            if len(self.ecurequestsparser.data[text].items) > 0:
                print self.ecurequestsparser.data[text].items
                qcombo = gui.QComboBox(self.panel)
                items_ref = self.ecurequestsparser.data[text].items
                for key in items_ref.keys():
                    qcombo.addItem(key)
                qcombo.resize(rect['width'] - width, rect['height'])
                qcombo.move(rect['left'] + width, rect['top'])
                self.inputs[text] = (qcombo, True)
            else:
                qlineedit = gui.QLineEdit(self.panel)
                qlineedit.setFont(qfnt)
                qlineedit.setText("--")
                qlineedit.resize(rect['width'] - width, rect['height'])
                qlineedit.setStyleSheet("background-color: " + self.colorConvert(color))
                qlineedit.setStyleSheet("color: " + self.getFontColor(input))
                qlineedit.move(rect['left'] + width, rect['top'])
                self.inputs[text] = (qlineedit, False)
            
            self.display_inputs[text] = self.ecurequestsparser.requests[req].name
      
    def buttonClicked(self, txt):
        if not self.button_requests.has_key(txt):
            print "Button request not found : " + txt
            return
            
        requests =  self.button_requests[txt]
        for req in requests:
            request_delay = req['Delay']
            request_type  = req['RequestName']
            log = 'Request name : ' + request_type.decode('ascii')
            self.logview.append(log)
            dataitems = self.ecurequestsparser.requests[request_type].sendbyte_dataitems
            for k in dataitems.keys():
                ecu_data  = self.ecurequestsparser.data[k]
                dataitem = dataitems[k]
                print dataitem.name


    def updateDisplays(self):
        self.elm_req_cache = {}
        if not options.simulation_mode:
            options.elm.start_session_can(self.startsession_command)
            
        for key in self.display_labels.keys():
            can_req   = self.display_labels_req[key]
            ecu_data  = self.ecurequestsparser.data[key]
            data_item = self.ecurequestsparser.requests[can_req.name].dataitems[key]
            
            qlabel   = self.display_labels[key]
            qvalues  = self.display_values[key]
            
            reply_bytes = can_req.replybytes.encode('ascii')

            min_bytes   = can_req.minbytes
            shiftbytes  = can_req.shiftbytescount
            ecu_bytes_to_send = can_req.sentbytes

            if (self.elm_req_cache.has_key(ecu_bytes_to_send)):
                #Prefer using cached data to speed up display processing
                elm_response = self.elm_req_cache[ecu_bytes_to_send]
            else :
                # TODO : Send bytes here replace line below
                elm_response = self.sendElm(ecu_bytes_to_send, True)
                # elm_response = "610A163232025800B43C3C1E3C0A0A0A0A012C5C6167B5BBC10A5C"
                self.elm_req_cache[ecu_bytes_to_send] = elm_response
                
            value = ecu_data.getDisplayValue(elm_response, data_item)

            qvalues.setText(value + ' ' + ecu_data.unit)
            # Auto-fill inputs with same DataName with value
            if self.inputs.has_key(key):
                input_widget = self.inputs[key]
                if input_widget[1] == False:
                    # lineedit case
                    input_widget[0].setText(value)
                else:
                    # combobox case
                    index = input_widget[0].findData(value)
                    if index != -1:
                        input_widget[0].setCurrentIndex(index)
                        
        self.timer.start(1000)
    def readDTC(self):
        if not options.simulation_mode:
            options.elm.start_session_can(self.startsession_command)
            
        request   = self.ecurequestsparser.requests["ReadDTC"]
        dataitems = request.dataitems
        sendbyte_dataitems = request.sendbyte_dataitems
        moredtcbyte = -1
        
        if sendbyte_dataitems.has_key("MoreDTC"):
            moredtcbyte = sendbyte_dataitems["MoreDTC"].firstbyte - 1
        
        dtclist = [0]
        if moredtcbyte > 0:
            dtclist = [i for i in range(0, 10)]
        
        dtc_result = {}
        dtc_num = 0
        for dtcnum in dtclist:        
            bytestosend = list(request.sentbytes.encode('ascii'))
            if moredtcbyte != -1:
                bytestosend[2*moredtcbyte+1] = hex(dtcnum)[-1:]
            dtcread_command = ''.join(bytestosend)
            can_response = self.sendElm(dtcread_command)
                
            dtc_num += 1
            
            for k in request.dataitems.keys():
                ecu_data  = self.ecurequestsparser.data[k]
                dataitem = request.dataitems[k]
                value_hex = ecu_data.getValue(can_response, dataitem)
                
                if not dtc_result.has_key(dataitem.name):
                    dtc_result[dataitem.name] = []
                
                if ecu_data.scaled:
                    dtc_result[dataitem.name].append(str(value_hex))
                    continue
                value = int('0x'+value_hex, 0)
                
                value = 16
                
                if len(ecu_data.items) > 0 and ecu_data.lists.has_key(value):
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
    w = Param_widget(None, "ecus/UCH_84_J84_04_00.xml")
    w.show()
    app.exec_()

