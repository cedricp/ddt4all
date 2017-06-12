# -*- coding: utf-8 -*-
import math, string
import options
import elm
import report
import zipfile
from xml.dom.minidom import parse
import xml.dom.minidom
import json, os
import re
import glob
import argparse

from StringIO import StringIO

__author__ = "Cedric PAILLE"
__copyright__ = "Copyright 2016-2017"
__credits__ = []
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Cedric PAILLE"
__email__ = "cedricpaille@gmail.com"
__status__ = "Beta"

# Returns signed value from 16 bits (2 bytes)
def hex16_tosigned(value):
    return -(value & 0x8000) | (value & 0x7fff)


# Returns signed value from 8 bits (1 byte)
def hex8_tosigned(value):
    return -(value & 0x80) | (value & 0x7f)

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def getChildNodesByName(parent, name):
    nodes = []
    for node in parent.childNodes:
        if node.nodeType == node.ELEMENT_NODE and node.localName == name:
            nodes.append(node)
    return nodes

class Data_item:
    def __init__(self, item, req_endian, name = ''):
        self.firstbyte = 0
        self.bitoffset = 0
        self.ref = False
        self.endian = ''
        self.req_endian = req_endian

        if isinstance(item, dict):
            self.name = name
            if item.has_key('firstbyte'): self.firstbyte = item['firstbyte']
            if item.has_key('bitoffset'): self.bitoffset = item['bitoffset']
            if item.has_key('ref'): self.ref = item['ref']
            if item.has_key('endian'): self.endian = item['endian']
        else:
            self.name = item.getAttribute("Name")

            fb = item.getAttribute("FirstByte")
            if fb:
                self.firstbyte = int(fb)

            bo = item.getAttribute("BitOffset")
            if bo:
                self.bitoffset = int(bo)

            endian = item.getAttribute("Endian")
            if endian:
                self.endian = endian.encode('ascii')

            ref = item.getAttribute("Ref")
            if ref and ref == '1': self.ref = True

    def dump(self):
        js = {}
        if self.firstbyte != 0: js['firstbyte'] = self.firstbyte
        if self.bitoffset != 0: js['bitoffset'] = self.bitoffset
        if self.ref != False: js['ref'] = self.ref
        if self.endian != '': js['endian'] = self.endian
        return js


class Ecu_device:
    def __init__(self, dev):
        self.dtc = 0
        self.dtctype = 0
        self.devicedata = {}
        self.name = ''

        if isinstance(dev, dict):
            # Json data
            self.name = dev['name']
            self.dtctype = dev['dtctype']
            self.devicedata = dev['devicedata']
            self.dtc = dev['dtc']
        else:
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

    def dump(self):
        js = {}
        js['dtc'] = self.dtc
        js['dtctype'] = self.dtctype
        js['devicedata'] = self.devicedata
        js['name'] = self.name
        return js

class Ecu_request:
    def __init__(self, data, endian):
        self.minbytes = 0
        self.shiftbytescount = 0
        self.replybytes = ''
        self.manualsend = False
        self.sentbytes = ''
        self.dataitems = {}
        self.sendbyte_dataitems = {}
        self.name = ''
        self.endian = endian

        if isinstance(data, dict):
            if data.has_key('minbytes'): self.minbytes = data['minbytes']
            if data.has_key('shiftbytescount'): self.shiftbytescount = data['shiftbytescount']
            if data.has_key('replybytes'): self.replybytes = data['replybytes']
            if data.has_key('manualsend'): self.manualsend = data['manualsend']
            if data.has_key('sentbytes'): self.sentbytes = data['sentbytes']

            self.endian = data['endian']
            self.name = data['name']

            if data.has_key('sendbyte_dataitems'):
                sbdi = data['sendbyte_dataitems']
                for k, v in sbdi.iteritems():
                    di = Data_item(v, self.endian, k)
                    self.sendbyte_dataitems[k] = di

            if data.has_key('receivebyte_dataitems'):
                rbdi = data['receivebyte_dataitems']
                for k, v in rbdi.iteritems():
                    di = Data_item(v, self.endian, k)
                    self.dataitems[k] = di
        elif isinstance(data, unicode):
            # Create a blank, new on
            self.name = data
        else:
            self.xmldoc = data
            self.name = self.xmldoc.getAttribute("Name")

            manualsenddata = self.xmldoc.getElementsByTagName("ManuelSend").item(0)
            if manualsenddata:
                self.manualsend = True

            shiftbytescount = self.xmldoc.getElementsByTagName("ShiftBytesCount")
            if shiftbytescount:
                self.shiftbytescount = int(shiftbytescount.item(0).firstChild.nodeValue)

            replybytes = self.xmldoc.getElementsByTagName("ReplyBytes")
            if replybytes:
                self.replybytes = replybytes.item(0).firstChild.nodeValue

            receiveddata = self.xmldoc.getElementsByTagName("Received").item(0)
            if receiveddata:
                minbytes = receiveddata.getAttribute("MinBytes")
                if minbytes:
                    self.minbytes = int(minbytes)

                dataitems = receiveddata.getElementsByTagName("DataItem")
                if dataitems:
                    for dataitem in dataitems:
                        di = Data_item(dataitem, self.endian)
                        self.dataitems[di.name] = di

            sentdata = self.xmldoc.getElementsByTagName("Sent")
            if sentdata:
                sent = sentdata.item(0)
                sentbytesdata = sent.getElementsByTagName("SentBytes")
                if sentbytesdata:
                    if sentbytesdata.item(0).firstChild:
                        self.sentbytes = sentbytesdata.item(0).firstChild.nodeValue

                dataitems = sent.getElementsByTagName("DataItem")
                if dataitems:
                    for dataitem in dataitems:
                        di = Data_item(dataitem, self.endian)
                        self.sendbyte_dataitems[di.name] = di

    def dump(self):
        js = {}
        if self.minbytes != 0: js['minbytes'] = self.minbytes
        if self.shiftbytescount != 0: js['shiftbytescount'] = self.shiftbytescount
        if self.replybytes != '': js['replybytes'] = self.replybytes
        if self.manualsend: js['manualsend'] = self.manualsend
        if self.sentbytes != '': js['sentbytes'] = self.sentbytes

        js['endian'] = self.endian
        js['name'] = self.name

        sdi = {}
        for key, value in self.sendbyte_dataitems.iteritems():
            sdi[key] = value.dump()
        if len(sdi):
            js['sendbyte_dataitems'] = sdi

        rdi = {}
        for key, value in self.dataitems.iteritems():
            rdi[key] = value.dump()
        if len(rdi):
            js['receivebyte_dataitems'] = rdi
        return js

    def dump_dataitems(self):
        di = {}
        for key, value in self.dataitems.iteritems():
            di[key] = value.dump()
        return di

    def dump_sentdataitems(self):
        di = {}
        for key, value in self.sendbyte_dataitems.iteritems():
            di[key] = value.dump()
        return di

class Ecu_data:
    def __init__(self, data, name=''):
        self.bitscount = 8
        self.scaled = False
        self.signed = False
        self.byte = False
        self.binary = False
        self.bytescount = 1
        self.bytesascii = False
        self.step = 1.0
        self.offset = 0.0
        self.divideby = 1.0
        self.format = ""
        self.items = {}
        self.lists = {}
        self.description = ''
        self.unit = ""
        self.comment = ''
        self.name = name

        if data:
            self.init(data)

    def init(self, data):

        if isinstance(data, dict):
            if data.has_key('bitscount'): self.bitscount = data['bitscount']
            if data.has_key('scaled'): self.scaled = data['scaled']
            if data.has_key('signed'): self.signed = data['signed']
            if data.has_key('byte'): self.byte = data['byte']
            if data.has_key('binary'): self.binary = data['binary']
            if data.has_key('step'): self.step = data['step']
            if data.has_key('offset'): self.offset = data['offset']
            if data.has_key('divideby'): self.divideby = data['divideby']
            if data.has_key('format'): self.format = data['format']
            if data.has_key('bytescount'): self.bytescount = data['bytescount']
            if data.has_key('unit'): self.unit = data['unit']
            if data.has_key('comment'): self.comment = data['comment']

            if data.has_key('items'):
                for k, v in data['items'].iteritems():
                    self.items[k] = v

            if data.has_key('lists'):
                for k, v in data['lists'].iteritems():
                    self.lists[k] = v
        else:
            self.xmldoc = data
            self.name = self.xmldoc.getAttribute("Name")
            description = self.xmldoc.getElementsByTagName("Description")
            if description:
                self.description = description.item(0).firstChild.nodeValue.replace('<![CDATA[', '').replace(']]>', '')

            comment = self.xmldoc.getElementsByTagName("Comment")
            if comment:
                self.comment = comment.item(0).firstChild.nodeValue.replace('<![CDATA[', '').replace(']]>', '')

            lst = self.xmldoc.getElementsByTagName("List")
            if lst:
                for l in lst:
                    items = l.getElementsByTagName("Item")
                    for item in items:
                        key = int(item.getAttribute('Value'))
                        self.lists[key] = item.getAttribute('Text')

            bytes = self.xmldoc.getElementsByTagName("Bytes")
            if bytes:
                self.byte = True
                bytescount = bytes.item(0).getAttribute("count")
                if '.' in bytescount:
                    bytescount = bytescount.split('.')[0]
                if bytescount:
                    self.bytescount = int(bytescount)
                    self.bitscount = self.bytescount * 8

                bytesascii = bytes.item(0).getAttribute("ascii")
                if bytesascii and bytesascii == '1': self.bytesascii = True

            bits = self.xmldoc.getElementsByTagName("Bits")
            if bits:
                bitscount = bits.item(0).getAttribute("count")
                if bitscount:
                    self.bitscount  = int(bitscount)
                    self.bytescount = int(math.ceil(float(bitscount) / 8.0))

                signed = bits.item(0).getAttribute("signed")
                if signed:
                    self.signed = True

                binary = bits.item(0).getElementsByTagName("Binary")
                if binary:
                    self.binary = True

                self.items = {}
                items = bits.item(0).getElementsByTagName("Item")
                if items:
                    for item in items:
                        value = int(item.getAttribute("Value"))
                        text  = item.getAttribute("Text")
                        self.items[text] = value

                scaled_value = bits.item(0).getElementsByTagName("Scaled")
                if scaled_value:
                    self.scaled = True
                    sc = scaled_value.item(0)

                    step = sc.getAttribute("Step")
                    if step:
                        self.step = float(step)

                    offset = sc.getAttribute("Offset")
                    if offset:
                        self.offset = float(offset)

                    divideby = sc.getAttribute("DivideBy")
                    if divideby:
                        self.divideby = float(divideby)

                    format = sc.getAttribute("Format")
                    if format:
                        self.format = format

                    unit = sc.getAttribute("Unit")
                    if unit:
                        self.unit = unit

    def dump(self):
        js = {}
        if self.bitscount != 8:
            js['bitscount'] = self.bitscount
        if self.scaled != False:
            js['scaled'] = self.scaled
        if self.signed != False:
            js['signed'] = self.signed
        if self.byte != False:
            js['byte'] = self.byte
        if self.binary != False:
            js['binary'] = self.binary
        if self.bytescount != 1:
            js['bytescount'] = self.bytescount
        if self.bytesascii != False:
            js['bytesascii'] = self.bytesascii
        if self.step != 1:
            js['step'] = self.step
        if self.offset != 0:
            js['offset'] = self.offset
        if self.divideby != 1:
            js['divideby'] = self.divideby
        if self.format != '':
            js['format'] = self.format
        if len(self.items) > 0:
            itms = {}
            for k, v in self.items.iteritems():
                itms[k] = v
            js['items'] = itms
        if len(self.lists) > 0:
            itms = {}
            for k, v in self.lists.iteritems():
                itms[k] = v
            js['lists'] = itms
        if self.unit != '':
            js['unit'] = self.unit
        if self.comment != '':
            js['comment'] = cleanhtml(self.comment)
        return self.name, js

    def setValue(self, value, bytes_list, dataitem, request_endian, test_mode=False):
        start_byte = dataitem.firstbyte - 1
        start_bit = dataitem.bitoffset
        little_endian = False

        if request_endian == "Little":
            little_endian = True

        # It seems that DataItem can override Request endianness
        if dataitem.endian == "Little":
            little_endian = True

        if dataitem.endian == "Big":
            little_endian = False

        if self.bytesascii:
            value = str(value)
            if self.bytescount > len(value):
                value = value.ljust(self.bytescount)
            if self.bytescount < len(value):
                value = value[0:self.bytescount]

            asciival = ""
            for i in range(self.bytescount):
                if not test_mode:
                    asciival += hex(ord(value[i]))[2:].upper()
                else:
                    asciival += "FF"

            value = asciival

        if self.scaled:
            if not test_mode:
                try:
                    value = float(value)
                except:
                    return None

                # Input value must be base 10
                value = int((value * float(self.divideby) - float(self.offset)) / float(self.step))
            else:
                value = int("0x" + value, 16)
        else:
            if not test_mode:
                # Check input length and validity
                if not all(c in string.hexdigits for c in value):
                    return None
                # Value is base 16
                value = int('0x' + str(value), 16)
            else:
                value = int("0x" + value, 16)

        valueasbin = bin(value)[2:].zfill(self.bitscount)

        numreqbytes = int(math.ceil(float(self.bitscount + start_bit) / 8.))
        request_bytes = bytes_list[start_byte:start_byte + numreqbytes]
        requestasbin = ""

        for r in request_bytes:
            requestasbin += bin(int(r, 16))[2:].zfill(8)
        requestasbin = list(requestasbin)

        if little_endian:
            # Little endian coding is really weird :/
            # Cannot figure out why it's being used
            # But tried to do my best to mimic the read/write process
            # Actually, need to do it in 3 steps

            remainingbits = self.bitscount

            # Step 1
            lastbit = 7 - start_bit + 1
            firstbit = lastbit - self.bitscount
            if firstbit < 0:
                firstbit = 0

            count = 0
            for i in range(firstbit, lastbit):
                requestasbin[i] = valueasbin[count]
                count += 1

            remainingbits -= count

            # Step 2
            currentbyte = 1
            while remainingbits >= 8:
                for i in range(0, 8):
                    requestasbin[currentbyte * 8 + i] = valueasbin[count]
                    count += 1
                remainingbits -= 8
                currentbyte += 1

            # Step 3
            if remainingbits > 0:
                lastbit = 8
                firstbit = lastbit - remainingbits

                for i in range(firstbit, lastbit):
                    requestasbin[currentbyte * 8 + i] = valueasbin[count]
                    count += 1

        else:
            for i in range(self.bitscount):
                requestasbin[i + start_bit] = valueasbin[i]

        requestasbin = "".join(requestasbin)
        valueasint = int("0b" + requestasbin, 2)
        valueashex = hex(valueasint)[2:].replace("L", "").zfill(numreqbytes * 2).upper()

        for i in range(numreqbytes):
            bytes_list[i + start_byte] = valueashex[i * 2:i * 2 + 2].zfill(2)

        return bytes_list

    def getDisplayValue(self, elm_data, dataitem, req_endian):
        value = self.getHexValue(elm_data, dataitem, req_endian)
        if value is None:
            return None

        if self.bytesascii:
            return value.decode('hex')

        # I think we want Hex format for non scaled values
        if not self.scaled:
            val = int('0x' + value, 16)

            # Manage mapped values
            if val in self.lists:
                return self.lists[val]

            return value

        value = int('0x' + value, 16)

        # Manage signed values
        if self.signed:
            if self.bytescount == 1:
                value = hex8_tosigned(value)
            elif self.bytescount == 2:
                value = hex16_tosigned(value)

        if self.divideby == 0:
            print "Division by zero, please check data item : ", dataitem.name
            return None

        res = (value * float(self.step) + float(self.offset)) / float(self.divideby)
        if len(self.format) and '.' in self.format:
            acc = len(self.format.split('.')[1])
            fmt = '%.' + str(acc) + 'f'
            res = fmt % res
        else:
            res = int(res)

        return str(res)

    def getHexValue(self, resp, dataitem, req_endian):
        little_endian = False

        if req_endian == "Little":
            little_endian = True

        if dataitem.endian == "Little":
            little_endian = True

        if dataitem.endian == "Big":
            little_endian = False

        # Data cleaning
        resp = resp.strip().replace(' ', '')
        if not all(c in string.hexdigits for c in resp): resp = ''
        resp.replace(' ', '')

        res_bytes = [resp[i:i + 2] for i in range(0,len(resp), 2)]

        # Data count
        startByte = dataitem.firstbyte
        startBit = dataitem.bitoffset
        bits = self.bitscount

        databytelen = int(math.ceil(float(self.bitscount) / 8.0))
        reqdatabytelen = int(math.ceil(float(self.bitscount + startBit) / 8.0))

        sb = startByte - 1
        if (sb * 2 + databytelen * 2) > (len(resp)):
            return None

        hexval = resp[sb * 2:(sb + reqdatabytelen) * 2]

        hextobin = ""
        for b in res_bytes[sb:sb + reqdatabytelen]:
            hextobin += bin(int(b, 16))[2:].zfill(8)

        if len(hexval) == 0:
            return None

        if little_endian:
            # Don't like this method

            totalremainingbits = bits
            lastbit = 7 - startBit + 1
            firstbit = lastbit - bits
            if firstbit < 0:
                firstbit = 0

            tmp_bin = hextobin[firstbit:lastbit]
            totalremainingbits -= lastbit - firstbit

            if totalremainingbits > 8:
                offset1 = 8
                offset2 = offset1 + ((reqdatabytelen - 2) * 8)
                tmp_bin += hextobin[offset1:offset2]
                totalremainingbits -= offset2 - offset1

            if totalremainingbits > 0:
                offset1 = (reqdatabytelen - 1) * 8
                offset2 = offset1 - totalremainingbits
                tmp_bin += hextobin[offset2:offset1]
                totalremainingbits -= offset1 - offset2

            if totalremainingbits != 0:
                print "getHexValue >> abnormal remaining bytes ", bits, totalremainingbits
            hexval = hex(int("0b" + tmp_bin, 2))[2:].replace("L", "")
        else:
            valtmp = "0b" + hextobin[startBit:startBit + bits]
            hexval = hex(int(valtmp, 2))[2:].replace("L", "")

        # Resize to original length
        hexval = hexval.zfill(databytelen * 2)
        return hexval

class Ecu_file:
    def __init__(self, data, isfile=False):
        self.requests = {}
        self.devices = {}
        self.data = {}
        self.endianness = ''
        self.ecu_protocol = ''
        self.ecu_send_id = "00"
        self.ecu_recv_id = "00"
        self.fastinit = False
        self.kw1 = ""
        self.kw2 = ""
        self.funcname = ""
        self.funcaddr = ""

        if not data:
            return

        if isfile and '.json' in str(data):
            data = "./json/" + data
            if os.path.exists(data):
                jsfile = open(data, "r")
                jsdata = jsfile.read()
                jsfile.close()
            else:
                # Zipped json here
                zf = zipfile.ZipFile('json/ecus.zip', mode='r')
                jsdata = zf.read(data)

            ecudict = json.loads(jsdata)

            if "obd" in ecudict:
                self.ecu_protocol = ecudict['obd']['protocol']
                if self.ecu_protocol == "CAN":
                    self.ecu_send_id = ecudict['obd']['send_id']
                    self.ecu_recv_id = ecudict['obd']['recv_id']
                if self.ecu_protocol == "KWP2000":
                    self.fastinit = ecudict['obd']['fastinit']
                self.funcaddr = ecudict['obd']['funcaddr']
                self.funcname = ecudict['obd']['funcname']
                if "kw1" in ecudict['obd']:
                    self.kw1 = ecudict['obd']['kw1']
                    self.kw2 = ecudict['obd']['kw2']

            if 'endian' in ecudict:
                self.endianness = ecudict['endian']

            devices = ecudict['devices']
            for device in devices:
                ecu_dev = Ecu_device(device)
                self.devices[ecu_dev.name] = ecu_dev

            requests = ecudict['requests']
            for request in requests:
                ecu_req = Ecu_request(request, self.endianness)
                self.requests[ecu_req.name] = ecu_req

            datalist = ecudict['data']
            for k, v in datalist.iteritems():
                self.data[k] = Ecu_data(v, k)
        else:
            if isfile:
                xdom = xml.dom.minidom.parse(data)
                self.xmldoc = xdom.documentElement
            else:
                self.xmldoc = data

            if not self.xmldoc:
                print("XML not found")
                return

            target = getChildNodesByName(self.xmldoc, u"Target")

            if target:
                functions = getChildNodesByName(target[0], u"Function")
                if functions:
                    self.funcaddr = hex(int(functions[0].getAttribute("Address")))[2:].upper()
                    self.funcname = functions[0].getAttribute("Name")

                can = getChildNodesByName(target[0], u"CAN")
                if can:
                    self.ecu_protocol = "CAN"
                    send_ids = getChildNodesByName(can[0], "SendId")
                    if send_ids:
                        send_id = send_ids[0]
                        can_id = getChildNodesByName(send_id, "CANId")
                        if can_id:
                            self.ecu_send_id = hex(int(can_id[0].getAttribute("Value")))[2:].upper()

                    rcv_ids = getChildNodesByName(can[0], "ReceiveId")
                    if rcv_ids:
                        rcv_id = rcv_ids[0]
                        can_id = getChildNodesByName(rcv_id, "CANId")
                        if can_id:
                            self.ecu_recv_id = hex(int(can_id[0].getAttribute("Value")))[2:].upper()

                k = getChildNodesByName(target[0], u"K")
                if k:
                    kwp = getChildNodesByName(k[0], u"KWP")
                    iso8 = getChildNodesByName(k[0], u"ISO8")
                    if kwp:
                        kwp = kwp[0]
                        self.ecu_protocol = u"KWP2000"
                        fastinit = getChildNodesByName(kwp, u"FastInit")
                        if fastinit:
                            self.fastinit = True

                            self.kw1 = hex(
                                int(getChildNodesByName(fastinit[0], "KW1")[0].getAttribute("Value")))[
                                               2:].upper()
                            self.kw2 = hex(
                                int(getChildNodesByName(fastinit[0], "KW2")[0].getAttribute("Value")))[
                                               2:].upper()
                    elif iso8:
                        self.fastinit = False

                        if iso8:
                            self.ecu_protocol = "ISO8"
                            self.kw1 = hex(
                                int(getChildNodesByName(iso8[0], "KW1")[0].getAttribute("Value")))[
                                               2:].upper()
                            self.kw2 = hex(
                                int(getChildNodesByName(iso8[0], "KW2")[0].getAttribute("Value")))[
                                               2:].upper()


            devices = self.xmldoc.getElementsByTagName("Device")
            for d in devices:
                ecu_dev = Ecu_device(d)
                self.devices[ecu_dev.name] = ecu_dev

            requests_tag = self.xmldoc.getElementsByTagName("Requests")

            if requests_tag:
                for request_tag in requests_tag:
                    endian = ''
                    endian_attr = request_tag.getAttribute("Endian")
                    if endian_attr:
                        endian = endian_attr.encode('ascii')
                        self.endianness = endian

                    requests = request_tag.getElementsByTagName("Request")
                    for f in requests:
                        ecu_req = Ecu_request(f, endian)
                        self.requests[ecu_req.name] = ecu_req

                    data = self.xmldoc.getElementsByTagName("Data")
                    for f in data:
                        ecu_data = Ecu_data(f)
                        self.data[ecu_data.name] = ecu_data

    def dumpJson(self):
        js = {}
        js['obd'] = {}
        js['obd']['protocol'] = self.ecu_protocol
        if self.ecu_protocol == "CAN":
            js['obd']['send_id'] = self.ecu_send_id
            js['obd']['recv_id'] = self.ecu_recv_id
        if self.ecu_protocol == "KWP2000":
            js['obd']['fastinit'] = self.fastinit
        js['obd']['funcaddr'] = self.funcaddr
        js['obd']['funcname'] = self.funcname

        js['data'] = {}
        js['requests'] = []
        js['devices'] = []

        if self.kw1:
            js['obd']['kw1'] = self.kw1
        if self.kw2:
            js['obd']['kw2'] = self.kw2

        if self.endianness:
            js['endian'] = self.endianness

        for key, value in self.data.iteritems():
            name, d = value.dump()
            js['data'][name] = d

        for key, value in self.requests.iteritems():
            js['requests'].append(value.dump())

        for key, value in self.devices.iteritems():
            js['devices'].append(value.dump())

        dump = json.dumps(js, indent=1)
        return re.sub('\n +', lambda match: '\n' + '\t' * (len(match.group().strip('\n')) / 2), dump)

# Protocols:
# KWP2000 FastInit MonoPoint            ?ATSP 5?
# KWP2000 FastInit MultiPoint           ?ATSP 5?
# KWP2000 Init 5 Baud Type I and II     ?ATSP 4?
# DiagOnCAN                             ATSP 6
# CAN Messaging (125 kbps CAN)          ?ATSP B?
# ISO8                                  ?ATSP 3?

class Ecu_ident:
    def __init__(self, diagversion, supplier, soft, version, name, group, href, protocol, projects, address):
        self.protocols = [u"KWP2000 Init 5 Baud Type I and II", u"ISO8",
                          u"CAN Messaging (125 kbps CAN)", u"KWP2000 FastInit MultiPoint",
                          u"KWP2000 FastInit MonoPoint", u"DiagOnCAN"]
        self.diagversion = diagversion
        self.supplier = supplier
        self.soft = soft
        self.version = version
        self.name = name
        self.group = group
        self.projects = projects
        self.href = href
        self.addr = address
        self.protocol = protocol
        self.hash = diagversion + supplier + soft + version

    def checkWith(self, diagversion, supplier, soft, version, addr):
        if self.hash != diagversion + supplier + soft + version: return False
        self.addr = addr
        return True

    def checkApproximate(self, diagversion, supplier, soft, version, addr):
        if self.diagversion != diagversion:
            return False
        if self.supplier != supplier:
            return False
        if self.soft != soft:
            return False

        self.addr = addr
        return True

    def checkProtocol(self):
        if not self.protocol in self.protocols:
            print "Unknown protocol '", self.protocol, "' "

    def dump(self):
        js = {}
        js['diagnotic_version'] = self.diagversion
        js['supplier_code'] = self.supplier
        js['soft_version'] = self.soft
        js['version'] = self.version
        js['group'] = self.group
        js['projects'] = [p for p in self.projects]
        js['protocol'] = self.protocol
        js['address'] = self.addr
        return js

class Ecu_database:
    jsonfile = "json/ecus.zip"

    def __init__(self, forceXML = False):
        self.targets = []
        self.numecu = 0
        xmlfile = options.ecus_dir + "/eculist.xml"
        if os.path.exists(self.jsonfile) and not forceXML:
            zf = zipfile.ZipFile(self.jsonfile, mode='r')
            jsdb = zf.read("db.json")
            dbdict = json.loads(jsdb)
            for target in dbdict:
                ecu_ident = Ecu_ident(target['diagnotic_version'], target['supplier_code'],
                                      target['soft_version'], target['version'],
                                      target['name'], target['group'], target['href'], target['protocol'],
                                      target['projects'])
                self.targets.append(ecu_ident)
        elif os.path.exists(xmlfile):
            xdom = xml.dom.minidom.parse(xmlfile)
            self.xmldoc = xdom.documentElement

            if not self.xmldoc:
                print "Unable to find eculist"
                return

            functions = self.xmldoc.getElementsByTagName("Function")
            for function in functions:
                targets = function.getElementsByTagName("Target")
                address = function.getAttribute("Address")
                group = function.getAttribute("Name")
                address = hex(int(address))[2:].zfill(2).upper()

                for target in targets:
                    href = target.getAttribute("href")
                    name = target.getAttribute("Name")
                    protnode = target.getElementsByTagName("Protocol")
                    if protnode:
                        protocol = protnode[0].firstChild.nodeValue
                    autoidents = target.getElementsByTagName("AutoIdents")
                    projectselems = target.getElementsByTagName("Projects")
                    projects = []
                    if projectselems:
                        for c in projectselems[0].childNodes:
                            projects.append(c.nodeName)
                    for autoident in autoidents:
                        self.numecu += 1
                        if len(autoident.getElementsByTagName("AutoIdent")) == 0:
                            ecu_ident = Ecu_ident("00", "??????", "0000", "0000", name, group, href, protocol,
                                                  projects, address)
                            self.targets.append(ecu_ident)
                        for ai in autoident.getElementsByTagName("AutoIdent"):
                            diagversion = ai.getAttribute("DiagVersion")
                            supplier = ai.getAttribute("Supplier")
                            soft = ai.getAttribute("Soft")
                            version = ai.getAttribute("Version")
                            ecu_ident = Ecu_ident(diagversion, supplier, soft, version, name, group, href, protocol, projects, address)
                            self.targets.append(ecu_ident)

    def getTarget(self, name):
        for t in self.targets:
            if t.name == name:
                return t
        return None

    def getTargets(self, name):
        tgt = []
        for t in self.targets:
            if t.name == name:
                tgt.append(t)
        return tgt

    def dump(self):
        js = []
        for t in self.targets:
            if t.protocol == u'DiagOnCAN' or u'KWP' in t.protocol or u'ISO8' == t.protocol:
                js.append(t.dump())
        return json.dumps(js, indent=1)

class Ecu_scanner:
    def __init__(self):
        self.totalecu = 0
        self.ecus = {}
        self.approximate_ecus = {}
        self.ecu_database = Ecu_database()
        self.num_ecu_found = 0
        self.report_data = []
        self.qapp = None

    def getNumEcuDb(self):
        return self.ecu_database.numecu

    def getNumAddr(self):
        return len(elm.dnat)
        
    def addTarget(self, target):
        self.ecus[target.name] = target

    def clear(self):
        self.totalecu = 0
        self.ecus = {}
        self.approximate_ecus = {}
        self.num_ecu_found = 0
        self.report_data = []

    def send_report(self):
        if options.report_data:
            # order : diagversion, supplier, soft, addr, can_response, version, href
            for reportdata in self.report_data:
                report.report_ecu(reportdata[1], reportdata[2], reportdata[5], reportdata[0], reportdata[3], reportdata[4], reportdata[6], reportdata[7])

    def scan(self, progress=None, label=None):
        i = 0
        if not options.simulation_mode:
            options.elm.init_can()
        for addr in elm.snat.keys():
            progress.setValue(i)
            self.qapp.processEvents()
            i += 1
            if not options.simulation_mode:
                txa, rxa = options.elm.set_can_addr(addr, {'ecuname': 'SCAN'})
                options.elm.start_session_can('10C0')
            else:
                txa = addr
                if addr == "7A": txa = "7E0"
                if addr == "04": txa = "742"
                rxa = ""
            if options.simulation_mode:
                # Give scanner something to eat...
                if txa == "742":
                    can_response = "61 80 82 00 30 64 35 48 30 30 31 00 00 32 03 00 03 22 03 60 00 00 2D 32 14 00 60"
                elif txa == "742":
                    #can_response = "61 80 82 00 14 97 39 04 33 33 30 40 50 54 87 04 00 05 00 06 00 00 00 00 00 00 01"
                    can_response = "61 80 82 00 14 97 39 04 33 33 30 40 50 54 87 04 00 05 00 01 00 00 00 00 00 00 01"
                    print can_response
                elif txa == "7E0":
                    # Test approximate case
                    #can_response = "61 80 82 00 44 66 27 44 32 31 33 82 00 38 71 38 00 A7 74 00 56 05 02 01 00 00"
                    can_response = "61 80 82 00 44 66 27 44 32 31 33 82 00 38 71 38 00 A7 75 00 56 05 02 01 00 00"
                else:
                    can_response = "7F 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
            else:
                can_response = options.elm.request(req='2180', positive='61', cache=False)

            self.check_ecu(can_response, label, addr, "CAN")
        if not options.simulation_mode:
            options.elm.close_protocol()

    def scan_kwp(self, progress=None, label=None):
        if options.simulation_mode:
            # Test data..
            # diagversion, supplier, soft, version, name, group, href, protocol, projects, address):
            self.ecus["S2000_Atmo__SoftA3"] = Ecu_ident("004", "213", "00A5", "8300", "UCH", "GRP", "S2000_Atmo___SoftA3.xml",
                                                        "KWP2000 FastInit MonoPoint", [], "7A")

        i = 0
        if not options.simulation_mode:
            options.elm.init_iso()
        for addr in elm.snat.keys():
            progress.setValue(i)
            self.qapp.processEvents()
            i += 1

            if not options.simulation_mode:
                options.elm.set_iso_addr(addr, {'idTx': '', 'idRx': '', 'ecuname': 'SCAN', 'protocol': "KWP2000"})
                options.elm.start_session_iso('10C0')
                can_response = options.elm.request(req='2180', positive='61', cache=False)
            else:
                continue

            self.check_ecu(can_response, label, addr, "KWP")
        if not options.simulation_mode:
            options.elm.close_protocol()

    def check_ecu(self, can_response, label, addr, protocol):
        if len(can_response) > 59:
            diagversion = str(int(can_response[21:23], 16))
            supplier = can_response[24:32].replace(' ', '').decode('hex')
            soft = can_response[48:53].replace(' ', '')
            version = can_response[54:59].replace(' ', '')
            approximate_ecu = []
            found_exact = False
            found_approximate = False
            href = ""

            for target in self.ecu_database.targets:
                if target.checkWith(diagversion, supplier, soft, version, addr):
                    self.ecus[target.name] = target
                    self.num_ecu_found += 1
                    label.setText("Found %i ecu" % self.num_ecu_found)
                    found_exact = True
                    href = target.href

                    break
                elif target.checkApproximate(diagversion, supplier, soft, version, addr):
                    approximate_ecu.append(target)
                    found_approximate = True

            # Try to find the closest possible version of an ECU
            if not found_exact and found_approximate:
                min_delta_version = 0xFFFFFF
                kept_ecu = None
                for tgt in approximate_ecu:
                    delta = abs(int('0x' + tgt.version, 16) - int('0x' + version, 16))
                    if delta < min_delta_version:
                        min_delta_version = delta
                        kept_ecu = tgt

                if kept_ecu:
                    self.approximate_ecus[kept_ecu.name] = kept_ecu
                    self.num_ecu_found += 1
                    href = "-->" + kept_ecu.href + "<--"
                    label.setText("Found %i ecu" % self.num_ecu_found)

            if can_response.startswith('61'):
                self.report_data.append((diagversion, supplier, soft, addr, can_response, version, href, protocol))


def make_zipfs():
    options.ecus_dir = "./ecus"
    zipoutput = StringIO()
    i = 0
    ecus = glob.glob("ecus/*.xml")
    ecus.remove("ecus/eculist.xml")

    with zipfile.ZipFile(zipoutput, mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        print("Writing vehicles database...")
        db = Ecu_database(True)
        zf.writestr("db.json", str(db.dump()))

        for target in ecus:
            name = target
            print "Starting zipping " + target + " " + str(i) + "/" + str(len(ecus))
            fileout = name.replace('.xml', '.json')
            ecur = Ecu_file(name, True)

            zf.writestr(fileout, ecur.dumpJson())
            i += 1
            # if i == 15:
            #    break

    with open("json/ecus.zip", "w") as f:
        f.write(zipoutput.getvalue())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--zipfs', action="store_true", default=None, help="Create a zip filesystem of the XMLs")
    parser.add_argument('--testdb', action="store_true", default=None, help="Test ecudatabse loading")
    parser.add_argument('--testecufile', action="store_true", default=None, help="Test ecudatabse loading")

    args = parser.parse_args()

    if args.zipfs:
        make_zipfs()

    if args.testdb:
        db = Ecu_database()

    if args.testecufile:
        db = Ecu_file("ecus/Sim32_RD3CA0_W44_J77_X85.json", True)