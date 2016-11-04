import sys, os, math, string
import options, elm
from   xml.dom.minidom import parse
import xml.dom.minidom
		 
class Data_item:
    def __init__(self, item):
        self.firstbyte = 0
        self.bitoffset = 0
        self.ref = None
        self.endian = ''
        self.name = item.getAttribute("Name")
        
        fb = item.getAttribute("FirstByte")
        if fb: self.firstbyte = int(fb)
        bo = item.getAttribute("BitOffset")
        if bo: self.bitoffset = int(bo)
        endian = item.getAttribute("Endian")
        if endian:
            self.endian = endian
        ref = item.getAttribute("Ref")
        if ref and ref == '1': self.ref = True

class Ecu_device:
     def __init__(self, dev):
        self.xmldoc = xml
        self.dtc = 0
        self.dtctype = 0
        self.devicedata = {}
        self.name = dev.getAttribute("Name")
        dtc = dev.getAttribute("DTC")
        if dtc: self.dtc = int(dtc)
        dtctype = dev.getAttribute("Type")
        if dtctype: self.dtctype = int(dtctype)

        devicedata = dev.getElementsByTagName("DeviceData")
        if devicedata:
            for data in devicedata:
                name = data.getAttribute("Name")
                failureflag = data.getAttribute("FailureFlag")
                self.devicedata[name] = failureflag

class Ecu_request:
    def __init__(self, xml):
        self.xmldoc = xml
        self.minbytes = 0
        self.shiftbytescount = 0
        self.replybytes = ''
        self.manualsend = False
        self.sentbytes = 0
        self.dataitems = {}
        self.name = 'uninit'
        
        self.initEcuReq()
        
    def initEcuReq(self):
        manualsend = False
        self.name = self.xmldoc.getAttribute("Name")

        manualsenddata = self.xmldoc.getElementsByTagName("ManuelSend").item(0)
        if manualsenddata: self.manualsend = True
        
        shiftbytescount = self.xmldoc.getElementsByTagName("ShiftBytesCount")
        if shiftbytescount: self.shiftbytescount = int(shiftbytescount.item(0).firstChild.nodeValue)
        
        replybytes = self.xmldoc.getElementsByTagName("ReplyBytes")
        if replybytes: self.replybytes = replybytes.item(0).firstChild.nodeValue

        receiveddata = self.xmldoc.getElementsByTagName("Received").item(0)
        if receiveddata:
            minbytes = receiveddata.getAttribute("MinBytes")
            if minbytes: self.minbytes = int(minbytes)

            dataitems =  receiveddata.getElementsByTagName("DataItem")
            if dataitems:
                for dataitem in dataitems:
                    di = Data_item(dataitem)
                    self.dataitems[di.name] = di

        sentdata = self.xmldoc.getElementsByTagName("Sent")
        if sentdata:
            sent = sentdata.item(0)
            sentbytesdata  = sent.getElementsByTagName("SentBytes")
            if sentbytesdata:
                self.sentbytes = sentbytesdata.item(0).firstChild.nodeValue
                
            dataitems =  sent.getElementsByTagName("DataItem")
            if dataitems:
                for dataitem in dataitems:
                    di = Data_item(dataitem)
                    self.dataitems[di.name] = di

class Ecu_data:
    def __init__(self, xml):
        self.xmldoc = xml
        self.name = ''
        self.bitscount = 8
        self.scaled = False
        self.signed = False
        self.byte = False
        self.bits = False
        self.binary = False
        self.bytescount = 1
        self.bytesascii  = False
        self.step = 1.0
        self.offset = 0.0
        self.divideby = 1.0
        self.format = ""
        self.items = {}
        self.description = ''
        self.unit = ""
        
        self.initData()
        
    def getValue(self, elm_data, dataitem):
        hv = self.getHex( elm_data, dataitem )
        assert hv is not None

        if self.scaled:
            res = (int(hv,16) * float(self.step) + float(self.offset)) / float(self.divideby) 
            if len(self.format) and '.' in self.format:
                acc = len(self.format.split('.')[1])
                fmt = '%.'+str(acc)+'d'
                res = fmt%(res)
            return str(res)

        if self.bytesascii:
            res = hv.decode('hex')
            return res

        return hv
    
    def getHex(self, resp, dataitem):
        resp = resp.strip().replace(' ','')
        if not all(c in string.hexdigits for c in resp): resp = ''
        resp = ' '.join( a + b for a, b in zip(resp[::2], resp[1::2]))
          
        bits  = self.bitscount
        bytes = bits/8
        if bits % 8:
            bytes = bytes + 1
        
        startByte = dataitem.firstbyte
        startBit  = dataitem.bitoffset
        littleEndian = True if dataitem.endian=="Little" else False
        
        sb = startByte-1
        assert ((sb * 3 + bytes * 3 - 1) <= (len(resp)))
        
        hexval = resp[sb*3:(sb+bytes)*3-1]
        hexval = hexval.replace(" ","")
        assert len(hexval) > 0
        
        if littleEndian:
              a = hexval
              b = ''
              if not len(a) % 2:
                    for i in range(0,len(a),2):
                        b = a[i:i+2]+b
                    hexval = b
        exbits = bits % 8
        if exbits:
            val = int(hexval,16)
            val = (val<<int(startBit)>>(8-exbits))&(2**bits-1)
            hexval = hex(val)[2:]
            if hexval[-1:].upper()=='L':
                hexval = hexval[:-1]
            if len(hexval)%2:
                hexval = '0'+hexval
        return hexval
    
    def initData(self):
        self.name = self.xmldoc.getAttribute("Name")
        description = self.xmldoc.getElementsByTagName("Description")
        if description:
            self.description = description.item(0).firstChild.nodeValue.replace('<![CDATA[','').replace(']]>','')
        
        bytes = self.xmldoc.getElementsByTagName("Bytes")
        if bytes:
            self.byte = True
            bytescount = bytes.item(0).getAttribute("count")
            if bytescount:
                self.bytescount = int(bytescount)
                self.bitscount  = self.bytescount * 8
            
            bytesascii = bytes.item(0).getAttribute("ascii")
            if bytesascii and bytesascii == '1': self.bytesascii = True
            
        bits = self.xmldoc.getElementsByTagName("Bits")
        if bits:
            self.bits = True
            bitscount = bits.item(0).getAttribute("count")
            if bitscount:
                self.bitscount  = int(bitscount)
                self.bytescount = int(math.ceil(float(bitscount) / 8.0))
            
            signed = bits.item(0).getAttribute("signed")
            if signed: self.signed = True
            
            binary = bits.item(0).getElementsByTagName("Binary")
            if binary: self.binary = True
            
            self.items = {}
            items = bits.item(0).getElementsByTagName("Item")
            if items:
                for item in items:
                    value = int(item.getAttribute("Value"))
                    text  = item.getAttribute("Text")
                    self.items[text] = value
                  
            scaled_value = bits.item(0).getElementsByTagName("Scaled")
            if scaled_value:
                sc = scaled_value.item(0)

                step = sc.getAttribute("Step")
                if step:
                    self.step = float(step) 
                    self.scaled = True

                offset = sc.getAttribute("Offset")
                if offset:
                    self.offset = float(offset) 
                    self.scaled = True

                divideby = sc.getAttribute("DivideBy")
                if divideby:
                    self.divideby = float(divideby) 
                    self.scaled = True

                format = sc.getAttribute("Format")
                if format:
                    self.format = format 
                    self.scaled = True

                unit = sc.getAttribute("Unit")
                if unit: self.unit = unit  
        
class Ecu_file:
    def __init__(self, xmldoc, isfile = False):
        self.requests = {}
        self.data = {}
        if isfile == True:
            xdom = xml.dom.minidom.parse(xmldoc)
            self.xmldoc = xdom.documentElement
        else:
            self.xmldoc = xmldoc
        self.parseXML()
        
    def parseXML(self):
        if not self.xmldoc:
            print("XML not found")
            return
        
        devices = self.xmldoc.getElementsByTagName("Device")
        for d in devices:
            ecu_dev = Ecu_device(d)
            self.requests[ecu_dev.name] = ecu_dev
            
        requests = self.xmldoc.getElementsByTagName("Request")
        for f in requests:
            ecu_req = Ecu_request(f)
            self.requests[ecu_req.name] = ecu_req
            
        data = self.xmldoc.getElementsByTagName("Data")
        for f in data:
            ecu_data = Ecu_data(f)
            self.data[ecu_data.name] = ecu_data

class Ecu_ident:
    def __init__(self, diagversion, supplier, soft, version, name, group, href):
        self.diagversion = diagversion
        self.supplier    = supplier
        self.soft        = soft
        self.version     = version
        self.name        = name
        self.group       = group
        self.href        = href
        
    def check_with(self, diagversion, supplier, soft, version):
        if self.diagversion != diagversion: return False
        if self.supplier != supplier: return False
        if self.soft != soft: return False
        if self.version != version: return False
        return True
        
class Ecu_database:
    def __init__(self):
        xmlfile = "ecus/eculist.xml"
        xdom = xml.dom.minidom.parse(xmlfile)
        self.xmldoc = xdom.documentElement  
        self.targets = []
        self.numecu = 0
          
        if not self.xmldoc:
            print "Unable to find eculist"
            return
            
        targets = self.xmldoc.getElementsByTagName("Target")
        
        for target in targets:
            href  = target.getAttribute("href")
            name  = target.getAttribute("Name")
            group = target.getAttribute("group")
            autoidents = target.getElementsByTagName("AutoIdents")
            for autoident in autoidents:
                self.numecu += 1
                for ai in autoident.getElementsByTagName("AutoIdent"):
                    diagversion = ai.getAttribute("DiagVersion")
                    supplier    = ai.getAttribute("Supplier")
                    soft        = ai.getAttribute("Soft")
                    version     = ai.getAttribute("Version")
                    ecu_ident = Ecu_ident(diagversion, supplier, soft, version, name, group, href)
                    self.targets.append(ecu_ident)

class Ecu_scanner:
    def __init__(self):
        self.totalecu = 0
        self.ecus = []
        self.ecu_database = Ecu_database()
        self.num_ecu_found = 0
    def getNumEcuDb(self):
        return self.ecu_database.numecu
    def scan(self):
        options.elm.init_can()
        
        for addr in elm.snat.keys():
            TXa, RXa = options.elm.set_can_addr(addr, { 'idTx' : '', 'idRx' : '', 'ecuname' : 'SCAN' })
            options.elm.start_session_can('10C0')
            
            if options.simulation_mode:
                if TXa == "745": can_response = "61 80 82 00 14 97 39 04 33 33 30 40 50 54 87 04 00 05 00 01 00 00 00 00 00 00 01"
                elif TXa == "7E0": can_response =  "61 80 82 00 44 66 27 44 32 31 33 82 00 38 71 38 00 A7 74 00 56 05 02 01 00 00"
                else: can_response = "61 80 82 00 14 97 39 00 00 00 30 00 50 54 87 04 00 05 00 01 00 00 00 00 00 00 01"
            else:
                options.elm.request( req = '2180', positive = '41', cache = False )
                
            if len(can_response)>59:
                diagversion = str(int(can_response[21:23],16))
                supplier    = can_response[24:32].replace(' ','').decode('hex')
                soft        = can_response[48:53].replace(' ','')
                version     = can_response[54:59].replace(' ','')

                for target in self.ecu_database.targets:
                    if target.check_with(diagversion, supplier, soft, version):
                        self.ecus.append(target)
                        self.num_ecu_found += 1
                        

if __name__ == '__main__':
    ecur = Ecu_file("ecus/UCH_84_J84_04_00.xml", True)
    
