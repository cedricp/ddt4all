import sys, os
import PyQt4.QtGui as gui
import PyQt4.QtCore as core

from   xml.dom.minidom import parse
import xml.dom.minidom

import ecu

class Param_widget(gui.QWidget):
    def __init__(self, parent, ddtfile):
         super(Param_widget, self).__init__(parent)
         self.ddtfile = ddtfile
         self.ecurequestsparser = None
         self.can_send_id = 0
         self.can_rcv_id  = 0
         self.panel = None
         self.layout = gui.QHBoxLayout(self)
         self.initXML()
         self.uiscale = 10
                        
    def init(self, screen):
         if self.panel:
            self.layout.removeWidget(self.panel)
            self.panel.close()
            self.panel.destroy()
         self.panel = gui.QWidget(self)
         self.button_requests = {}
         self.display_inputs = {}
         self.display_labels = {}
         self.display_labels_req = {}
         self.button_requests = {}
         self.display_labels_req = {}
         self.display_values = {}
         self.elm_req_cache = {}
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
            self.can_send_id = int(can_id.item(0).getAttribute("Value"))
        
        rcv_id = xdoc.getElementsByTagName("ReceiveId")
        if rcv_id:
            can_id = rcv_id.item(0).getElementsByTagName("CANId")
            self.can_rcv_id = int(can_id.item(0).getAttribute("Value"))

        xml_cats = xdoc.getElementsByTagName("Category")
        for category in xml_cats:
            category_name = category.getAttribute("Name")
            self.categories[category_name] = []
            screens_name = category.getElementsByTagName("Screen")
            for screen in screens_name:
                screen_name = screen.getAttribute("Name")
                self.xmlscreen[screen_name] = screen
                self.categories[category_name].append(screen_name)
            
    def initScreen(self, screen_name):
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
        
        self.resize(self.screen_width+10, self.screen_height+10)
        self.panel.resize(self.screen_width+10, self.screen_height+10)
        self.drawLabels(screen)
        self.drawDisplays(screen)
        self.drawInputs(screen)
        self.drawButtons(screen)
        self.updateDisplays()

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
            
            self.display_labels[text]     = qlabel
            self.display_values[text]     = qlabelval
            self.display_labels_req[text] = self.ecurequestsparser.requests[req_name]
            
    def drawButtons(self, screen):
        self.button_requests = {}
        buttons = screen.getElementsByTagName("Button")
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
            
            send = button.getElementsByTagName("Send")
            if send:
                sendlist = []
                for snd in send:
                    smap = {}
                    xsDelay       = snd.getAttribute("Delay")
                    xsRequestName = snd.getAttribute("RequestName")
                    smap['Delay']       = xsDelay
                    smap['RequestName'] = xsRequestName
                    sendlist.append(smap)
                self.button_requests[text] = sendlist
            qbutton.clicked.connect(lambda state, btn=text: self.buttonClicked(btn))
    
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
            else:
                qlineedit = gui.QLineEdit(self.panel)
                qlineedit.setFont(qfnt)
                qlineedit.setText("--")
                qlineedit.resize(rect['width'] - width, rect['height'])
                qlineedit.setStyleSheet("background-color: " + self.colorConvert(color))
                qlineedit.setStyleSheet("color: " + self.getFontColor(input))
                qlineedit.move(rect['left'] + width, rect['top'])
            
            self.display_inputs[text] = self.ecurequestsparser.requests[req].name
      
    def buttonClicked(self, txt):
        if not self.button_requests.has_key(txt):
            print "Button request not found : " + txt
            return
            
        requests =  self.button_requests[txt]
        for req in requests:
            request_delay = req['Delay']
            request_type  = req['RequestName']
            
            req_ref = self.ecurequestsparser.requests[request_type].dataitems
            for k in req_ref.keys():
                ecu_data  = self.ecurequestsparser.data[k]
                dataitem = req_ref[k]
                print "DATA >> " , ecu_data.unit, dataitem.name, dataitem.firstbyte
        
    def updateDisplays(self):
        self.elm_req_cache = {}
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
                elm_response = ''.zfill((min_bytes + 1 + shiftbytes)*2 - len(reply_bytes)) # for testing
                # test data below
                # elm_response = "610A163232025800B43C3C1E3C0A0A0A0A012C5C6167B5BBC10A5C"
                self.elm_req_cache[ecu_bytes_to_send] = elm_response
                
            #if (reply_bytes != elm_response[:len(reply_bytes)]):
            #    print "Reply problem to request : %s, response : %s" % (ecu_bytes_to_send, elm_response)
            #    return

            value = ecu_data.getValue(elm_response, data_item)
            qvalues.setText(value + ' ' + ecu_data.unit)
            
    def readDTC(self):
        request   = self.ecurequestsparser.requests["ReadDTC"]
        print "Requesting %s with command %s" % (request.name, request.sentbytes)
        print "Command returns %i bytes + %i bytes" % (request.minbytes, request.shiftbytescount)
        can_response = "47".zfill(10)
        for k in request.dataitems.keys():
            ecu_data  = self.ecurequestsparser.data[k]
            dataitem = request.dataitems[k]
            value = ecu_data.getValue(can_response, dataitem)
            for i in ecu_data.items.keys():
                print ecu_data.items[i], i
            if len(ecu_data.items) > 0 and ecu_data.items.has_key(int(value)):
                print dataitem.name + " : " + ecu_data.items[value]
            else:
                print dataitem.name + " : " , value

if __name__ == '__main__':
    app = gui.QApplication(sys.argv)
    w = Param_widget(None, "ecus/UCH_84_J84_04_00.xml")
    w.show()
    app.exec_()

