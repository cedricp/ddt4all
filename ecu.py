import math, string
import options
import elm
import report
import zipfile
from xml.dom.minidom import parse
import xml.dom.minidom
import json, os
import unicodedata
import re
import glob
import argparse

from StringIO import StringIO


# Returns signed value from 16 bits (2 bytes)
def hex16_tosigned(value):
    return -(value & 0x8000) | (value & 0x7fff)


# Returns signed value from 8 bits (1 byte)
def hex8_tosigned(value):
    return -(value & 0x80) | (value & 0x7f)


def to_nfkd(input_str):
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])


def toascii(str):
    return to_nfkd(str).encode('ascii', 'ignore')


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return toascii(cleantext)

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
        js['name'] = toascii(self.name)
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
        js['name'] = toascii(self.name)

        sdi = {}
        for key, value in self.sendbyte_dataitems.iteritems():
            sdi[toascii(key)] = value.dump()
        if len(sdi):
            js['sendbyte_dataitems'] = sdi

        rdi = {}
        for key, value in self.dataitems.iteritems():
            rdi[toascii(key)] = value.dump()
        if len(rdi):
            js['receivebyte_dataitems'] = rdi
        return js

    def dump_dataitems(self):
        di = {}
        for key, value in self.dataitems.iteritems():
            di[toascii(key)] = value.dump()
        return di

    def dump_sentdataitems(self):
        di = {}
        for key, value in self.sendbyte_dataitems.iteritems():
            di[toascii(key)] = value.dump()
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

        if isinstance(data, dict):
            self.name = name
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
            js['format'] = toascii(self.format)
        if len(self.items) > 0:
            itms = {}
            for k, v in self.items.iteritems():
                itms[toascii(k)] = toascii(v)
            js['items'] = itms
        if len(self.lists) > 0:
            itms = {}
            for k, v in self.lists.iteritems():
                itms[toascii(k)] = toascii(v)
            js['lists'] = itms
        if self.unit != '':
            js['unit'] = toascii(self.unit)
        if self.comment != '':
            js['comment'] = cleanhtml(self.comment)
        return self.name, js

    def setValue(self, value, bytes_list, dataitem, request_endian):
        start_byte = dataitem.firstbyte - 1
        start_bit = dataitem.bitoffset
        little_endian = False

        if request_endian == "Little":
            little_endian = True

        # It seems that DataItem can override Request endianness
        if dataitem.endian == "Little":
            little_endian = True

        if self.bytesascii:
            if self.bytescount != len(value):
                return None

            for i in range(self.bytescount):
                bytes_list[self.bytescount - i - 1] = ord(value[i])

            return bytes_list

        if self.scaled:
            if not str(value).isdigit():
                return None

            value = float(value)
            # Input value must be base 10
            value = int((value * float(self.divideby) - float(self.offset)) / float(self.step))
        else:
            # Check input length and validity
            if not all(c in string.hexdigits for c in value):
                return None
            # Value is base 16
            value = int('0x' + str(value), 16)

        # We're working at bit level, we may need to OR these values
        bit_operation = self.bitscount < 8

        if bit_operation and start_bit > 7:
            print "bit operation on multiple bytes not implemented"
            return None

        value_mask_shifted_inv = 0xFF
        if bit_operation:
            if little_endian:
                offset = start_bit
            else:
                offset = 8 - start_bit - self.bitscount

            value_mask = 2 ** self.bitscount - 1

            value_mask_shifted = value_mask << offset
            value_mask_shifted_str = bin(value_mask_shifted)[2:].zfill(self.bytescount * 8)
            value_mask_shifted_str_inv = value_mask_shifted_str.replace('0', 'O')
            value_mask_shifted_str_inv = value_mask_shifted_str_inv.replace('1', '0')
            value_mask_shifted_str_inv = value_mask_shifted_str_inv.replace('O', '1')
            value_mask_shifted_inv = int('0b' + value_mask_shifted_str_inv, 2)

            value = int(value)
            value &= value_mask
            value = (value << offset)

        hex_value = "{0:#0{1}x}".format(value, self.bytescount * 2 + 2)[2:].upper()
        hex_bytes = [hex_value[i:i + 2] for i in range(0, len(hex_value), 2)]

        n = 0
        if len(hex_bytes) > self.bytescount:
            return None

        for h in hex_bytes:
            original_byte  = int('0x' + bytes_list[n + start_byte], 16)
            original_value = int('0x' + h, 16)

            if bit_operation:
                # Need to clear bits before or'ing
                original_byte &= value_mask_shifted_inv
                new = original_value | original_byte
            else:
                new = original_value

            value_formatted = "{0:#0{1}x}".format(new, 4)[2:].upper()

            bytes_list[start_byte + n] = value_formatted

            n += 1

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
            print "Division by zero : ", dataitem.name
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

        resp = resp.strip().replace(' ','')
        if not all(c in string.hexdigits for c in resp): resp = ''
        resp.replace(' ', '')
        
        bits = self.bitscount
        bytes = bits / 8

        if bits % 8:
            bytes += 1

        startByte = dataitem.firstbyte
        startBit = dataitem.bitoffset

        if startBit + bits > (bytes * 8):
            bytes += 1

        sb = startByte - 1
        if (sb * 2 + bytes * 2) > (len(resp)):
            return None

        hexval = resp[sb * 2:(sb + bytes) * 2]
        if len(hexval) == 0:
            return None

        if bits % 8:
            if little_endian:
                offset = startBit
            else:
                offset = (bytes * 8) - startBit - bits

            if (offset < 0):
                print "negative offset : ", dataitem.name, bits, offset, little_endian, hexval
                return None

            val = int(hexval, 16)
            val = (val >> int(offset)) & (2**bits - 1)
            hexval = hex(val)[2:]
            # Remove trailing L if exists
            if hexval[-1:].upper() == 'L':
                hexval = hexval[:-1]
            # Resize to original length
            hexval = hexval.zfill(bytes * 2)

        return hexval

class Ecu_file:
    def __init__(self, data, isfile=False):
        self.requests = {}
        self.devices = {}
        self.data = {}
        self.endianness = ''
        self.ecu_protocol = ''
        self.ecu_send_id = 0
        self.ecu_recv_id = 0
        self.fastinit = False

        if isfile and '.json' in str(data):
            # Json here
            zf = zipfile.ZipFile('json/ecus.zip', mode='r')
            jsdata = zf.read(data)
            ecudict = json.loads(jsdata)

            if ecudict.has_key('endian'):
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
                    if kwp:
                        kwp = kwp[0]
                        self.ecu_protocol = "KWP2000"
                        fastinit = getChildNodesByName(kwp, "FastInit")
                        if fastinit:
                            self.fastinit = True
                        else:
                            return None
                        self.ecu_recv_id = hex(int(getChildNodesByName(fastinit[0], "KW1")[0].getAttribute("Value")))[
                                              2:].upper()
                        self.ecu_send_id = hex(int(getChildNodesByName(fastinit[0], "KW2")[0].getAttribute("Value")))[
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
        js['obd']['send_id'] = self.ecu_send_id
        js['obd']['recv_id'] = self.ecu_recv_id
        js['obd']['fastinit'] = self.fastinit

        js['data'] = {}
        js['requests'] = []
        js['devices'] = []

        if self.endianness:
            js['endian'] = self.endianness

        for key, value in self.data.iteritems():
            name, d = value.dump()
            js['data'][toascii(name)] = d

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
    def __init__(self, diagversion, supplier, soft, version, name, group, href, protocol, projects):
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
        self.addr = None
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
        js['diagnotic_version'] = toascii(self.diagversion)
        js['supplier_code'] = toascii(self.supplier)
        js['soft_version'] = toascii(self.soft)
        js['version'] = toascii(self.version)
        js['name'] = toascii(self.name)
        js['group'] = toascii(self.group)
        js['projects'] = [toascii(p) for p in self.projects]
        js['href'] = toascii(self.href.replace('.xml', '.json'))
        js['protocol'] = toascii(self.protocol)
        return js

class Ecu_database:
    jsonfile = "json/ecus.zip"

    def __init__(self, forceXML = False):
        self.targets = []
        self.numecu = 0

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
        else:
            xmlfile = options.ecus_dir + "/eculist.xml"
            xdom = xml.dom.minidom.parse(xmlfile)
            self.xmldoc = xdom.documentElement

            if not self.xmldoc:
                print "Unable to find eculist"
                return

            targets = self.xmldoc.getElementsByTagName("Target")

            for target in targets:
                href = target.getAttribute("href")
                name = target.getAttribute("Name")
                group = target.getAttribute("group")
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
                    for ai in autoident.getElementsByTagName("AutoIdent"):
                        diagversion = ai.getAttribute("DiagVersion")
                        supplier = ai.getAttribute("Supplier")
                        soft = ai.getAttribute("Soft")
                        version = ai.getAttribute("Version")
                        ecu_ident = Ecu_ident(diagversion, supplier, soft, version, name, group, href, protocol, projects)
                        self.targets.append(ecu_ident)

    def getTarget(self, name):
        for t in self.targets:
            if t.name == name:
                return t
        return None

    def dump(self):
        js = []
        for t in self.targets:
            if t.protocol == u'DiagOnCAN' or u'KWP' in t.protocol:
                js.append(t.dump())
        return json.dumps(js, indent=1)

class Ecu_scanner:
    def __init__(self):
        self.totalecu = 0
        self.ecus = {}
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
        options.elm.init_can()
        for addr in elm.snat.keys():
            progress.setValue(i)
            self.qapp.processEvents()
            i += 1
            txa, rxa = options.elm.set_can_addr(addr, {'idTx': '', 'idRx': '', 'ecuname': 'SCAN'})
            options.elm.start_session_can('10C0')

            if options.simulation_mode:
                # Give scanner something to eat...
                if txa == "742":
                    can_response = "61 80 82 00 30 64 35 48 30 30 31 00 00 32 03 00 03 22 03 60 00 00 2D 32 14 00 60"
                elif txa == "74B":
                    #can_response = "61 80 82 00 14 97 39 04 33 33 30 40 50 54 87 04 00 05 00 06 00 00 00 00 00 00 01"
                    can_response = "61 80 82 00 14 97 39 04 33 33 30 40 50 54 87 04 00 05 00 01 00 00 00 00 00 00 01"
                elif txa == "7E0":
                    # Test approximate case
                    #can_response = "61 80 82 00 44 66 27 44 32 31 33 82 00 38 71 38 00 A7 74 00 56 05 02 01 00 00"
                    can_response = "61 80 82 00 44 66 27 44 32 31 33 82 00 38 71 38 00 A7 75 00 56 05 02 01 00 00"
                else:
                    can_response = "7F 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
            else:
                can_response = options.elm.request(req='2180', positive='61', cache=False)

            self.check_ecu(can_response, label, addr, "CAN")
        options.elm.close_protocol()

    def scan_kwp(self, progress=None, label=None):
        if options.simulation_mode:
            # Test data..
            self.ecus["S2000_Atmo__SoftA3"] = Ecu_ident("004", "213", "00A5", "8300", "UCH", "GRP", "S2000_Atmo___SoftA3.xml",
                                                        "KWP2000 FastInit MonoPoint", [])

        i = 0
        options.elm.init_iso()
        for addr in elm.snat.keys():
            progress.setValue(i)
            self.qapp.processEvents()
            i += 1
            options.elm.set_iso_addr(addr, {'idTx': '', 'idRx': '', 'ecuname': 'SCAN', 'protocol': "KWP2000"})
            options.elm.start_session_iso('10C0')

            if not options.simulation_mode:
                can_response = options.elm.request(req='2180', positive='61', cache=False)
            else:
                continue

            self.check_ecu(can_response, label, addr, "KWP")

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
            name = toascii(target)
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