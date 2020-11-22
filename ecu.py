# -*- coding: utf-8 -*-
import math, string
import options
import elm
import zipfile
from xml.dom.minidom import parse
import xml.dom.minidom
import json, os
import re
import glob
import argparse

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
    def unichr(t):
        return chr(t)

__author__ = "Cedric PAILLE"
__copyright__ = "Copyright 2016-2020"
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
            if 'firstbyte' in item:
                self.firstbyte = item['firstbyte']
            if 'bitoffset' in item:
                self.bitoffset = item['bitoffset']
            if 'ref' in item:
                self.ref = item['ref']
            if 'endian' in item:
                self.endian = item['endian']
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
                self.endian = endian

            ref = item.getAttribute("Ref")
            if ref and ref == '1':
                self.ref = True

    def dump(self):
        js = {}
        if self.firstbyte != 0:
            js['firstbyte'] = self.firstbyte
        if self.bitoffset != 0:
            js['bitoffset'] = self.bitoffset
        if self.ref != False:
            js['ref'] = self.ref
        if self.endian != '':
            js['endian'] = self.endian
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
    def __init__(self, data, ecu_file):
        self.minbytes = 0
        self.shiftbytescount = 0
        self.replybytes = ''
        self.manualsend = False
        self.sentbytes = ''
        self.dataitems = {}
        self.sendbyte_dataitems = {}
        self.name = ''
        self.ecu_file = ecu_file
        # StartDiagSession requirements
        # Seems relatively useless...
        self.sds = {'nosds': True,
                    'plant': True,
                    'aftersales': True,
                    'engineering': True,
                    'supplier': True}

        if isinstance(data, dict):
            if 'minbytes' in data: self.minbytes = data['minbytes']
            if 'shiftbytescount' in data: self.shiftbytescount = data['shiftbytescount']
            if 'replybytes' in data: self.replybytes = data['replybytes']
            if 'manualsend' in data: self.manualsend = data['manualsend']
            if 'sentbytes' in data: self.sentbytes = data['sentbytes']

            self.name = data['name']
            if 'deny_sds' in data:
                if 'nosds' in data['deny_sds']:
                    self.sds['nosds'] = False
                if 'plant' in data['deny_sds']:
                    self.sds['plant'] = False
                if 'aftersales' in data['deny_sds']:
                    self.sds['aftersales'] = False
                if 'engineering' in data['deny_sds']:
                    self.sds['engineering'] = False
                if 'supplier' in data['deny_sds']:
                    self.sds['supplier'] = False

            if 'sendbyte_dataitems' in data:
                sbdi = data['sendbyte_dataitems']
                for k, v in sbdi.items():
                    di = Data_item(v, self.ecu_file.endianness, k)
                    self.sendbyte_dataitems[k] = di

            if 'receivebyte_dataitems' in data:
                rbdi = data['receivebyte_dataitems']
                for k, v in rbdi.items():
                    di = Data_item(v, self.ecu_file.endianness, k)
                    self.dataitems[k] = di

        elif isinstance(data, str):
            # Create a blank, new one
            self.name = data
        else:
            self.xmldoc = data
            self.name = self.xmldoc.getAttribute("Name")

            accessdata = self.xmldoc.getElementsByTagName("DenyAccess").item(0)
            if accessdata:
                for accessdatachild in accessdata.childNodes:
                    if accessdatachild.nodeName == "NoSDS":
                        self.sds['nosds'] = False
                    elif accessdatachild.nodeName == "Plant":
                        self.sds['plant'] = False
                    elif accessdatachild.nodeName == "AfterSales":
                        self.sds['aftersales'] = False
                    elif accessdatachild.nodeName == "Engineering":
                        self.sds['engineering'] = False
                    elif accessdatachild.nodeName == "Supplier":
                        self.sds['supplier'] = False

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
                        di = Data_item(dataitem, self.ecu_file.endianness)
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
                        di = Data_item(dataitem, self.ecu_file.endianness)
                        self.sendbyte_dataitems[di.name] = di

    def send_request(self, inputvalues={}, test_data=None):
        request_stream = self.build_data_stream(inputvalues)
        request_stream = " ".join(request_stream)

        if options.debug:
            print("Generated stream ", request_stream)

        if options.simulation_mode:
            if test_data is not None:
                elmstream = test_data
                print("Send request stream", request_stream)
            else:
                # return default reply bytes...
                elmstream = self.replybytes
        else:
            elmstream = options.elm.request(request_stream)

        if options.debug:
            print("Received stream ", elmstream)

        if elmstream.startswith('WRONG RESPONSE'):
            return None

        if elmstream.startswith('7F'):
            nrsp = options.elm.errorval(elmstream[6:8])
            print("Request ECU Error", nrsp)
            return None

        values = self.get_values_from_stream(elmstream)

        if options.debug:
            print("Decoded values", values)

        return values

    def get_data_inputs(self):
        return self.sendbyte_dataitems.keys()

    def build_data_stream(self, data):
        data_stream = self.get_formatted_sentbytes()

        for k, v in data.items():
            if k in self.sendbyte_dataitems:
                datatitem = self.sendbyte_dataitems[k]
            else:
                raise KeyError('Ecurequest::build_data_stream : Data item %s does not exist' % k)

            if k in self.ecu_file.data:
                data = self.ecu_file.data[k]
            else:
                raise KeyError('Ecurequest::build_data_stream : Data %s does not exist' % k)

            if v in data.items:
                v = hex(data.items[v])[2:].upper()

            data.setValue(v, data_stream, datatitem, self.ecu_file.endianness)

        return data_stream

    def get_values_from_stream(self, stream):
        values = {}
        for k, v in self.dataitems.items():
            if k in self.ecu_file.data:
                data = self.ecu_file.data[k]
                values[k] = data.getDisplayValue(stream, v, self.ecu_file.endianness)
            else:
                raise KeyError('Ecurequest::get_values_from_stream : Data %s does not exist' % k)
        return values

    def get_formatted_sentbytes(self):
        bytes_to_send_ascii = self.sentbytes
        return [str(bytes_to_send_ascii[i:i + 2]) for i in range(0, len(bytes_to_send_ascii), 2)]

    def dump(self):
        js = {}
        if self.minbytes != 0:
            js['minbytes'] = self.minbytes
        if self.shiftbytescount != 0:
            js['shiftbytescount'] = self.shiftbytescount
        if self.replybytes != '':
            js['replybytes'] = self.replybytes
        if self.manualsend:
            js['manualsend'] = self.manualsend
        if self.sentbytes != '':
            js['sentbytes'] = self.sentbytes

        js['name'] = self.name
        js['deny_sds'] = []
        if self.sds['nosds'] is False:
            js['deny_sds'].append('nosds')
        if self.sds['plant'] is False:
            js['deny_sds'].append('plant')
        if self.sds['aftersales'] is False:
            js['deny_sds'].append('aftersales')
        if self.sds['engineering'] is False:
            js['deny_sds'].append('engineering')
        if self.sds['supplier'] is False:
            js['deny_sds'].append('supplier')

        sdi = {}
        for key, value in self.sendbyte_dataitems.items():
            sdi[key] = value.dump()
        if len(sdi):
            js['sendbyte_dataitems'] = sdi

        rdi = {}
        for key, value in self.dataitems.items():
            rdi[key] = value.dump()
        if len(rdi):
            js['receivebyte_dataitems'] = rdi
        return js

    def dump_dataitems(self):
        di = {}
        for key, value in self.dataitems.items():
            di[key] = value.dump()
        return di

    def dump_sentdataitems(self):
        di = {}
        for key, value in self.sendbyte_dataitems.items():
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
        self.lists = {}
        self.items = {}
        self.description = ''
        self.unit = ""
        self.comment = ''
        self.name = name

        if data:
            self.init(data)

    def init(self, data):

        if isinstance(data, dict):
            if 'bitscount' in data:
                self.bitscount = data['bitscount']
            if 'bytesascii' in data:
                self.bytesascii = data['bytesascii']
            if 'scaled' in data:
                self.scaled = data['scaled']
            if 'signed' in data:
                self.signed = data['signed']
            if 'byte' in data:
                self.byte = data['byte']
            if 'binary' in data:
                self.binary = data['binary']
            if 'step' in data:
                self.step = data['step']
            if 'offset' in data:
                self.offset = data['offset']
            if 'divideby' in data:
                self.divideby = data['divideby']
            if 'format' in data:
                self.format = data['format']
            if 'bytescount' in data:
                self.bytescount = data['bytescount']
            if 'unit' in data:
                self.unit = data['unit']
            if 'comment' in data:
                self.comment = data['comment']

            if 'lists' in data:
                for k, v in data['lists'].items():
                    self.lists[int(k)] = v
                    self.items[v] = int(k)
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
                        val = item.getAttribute('Text')
                        self.lists[int(key)] = val
                        self.items[val] = int(key)

            bytes = self.xmldoc.getElementsByTagName("Bytes")
            if bytes:
                self.byte = True
                bytescount = bytes.item(0).getAttribute("count").replace(',', '.')
                if '.' in bytescount:
                    self.bytescount = math.ceil(float(bytescount))
                    self.bitscount = int(float(bytescount) * 8)
                elif bytescount:
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
        if len(self.lists) > 0:
            lst = {}
            for k, v in self.lists.items():
                lst[int(k)] = v
            js['lists'] = lst
        if self.unit != '':
            js['unit'] = self.unit
        if self.comment != '':
            js['comment'] = cleanhtml(self.comment)
        return self.name, js

    def setValue(self, value, bytes_list, dataitem, ecu_endian, test_mode=False):
        start_byte = dataitem.firstbyte - 1
        start_bit = dataitem.bitoffset
        little_endian = False

        if ecu_endian == "Little":
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

    def getDisplayValue(self, elm_data, dataitem, ecu_endian):
        value = self.getHexValue(elm_data, dataitem, ecu_endian)
        if value is None:
            return None

        if self.bytesascii:
            return bytes.fromhex(value).decode('utf-8')

        # I think we want Hex format for non scaled values
        if not self.scaled:
            val = int('0x' + value, 16)

            # Manage signed values
            if self.signed:
                if self.bytescount == 1:
                    val = hex8_tosigned(val)
                elif self.bytescount == 2:
                    val = hex16_tosigned(val)
                else:
                    print("Warning, cannot get signed value for %s" % dataitem.name)

            # Manage mapped values if exists
            if val in self.lists:
                return self.lists[val]

            # Return default hex value
            return value

        value = int('0x' + value, 16)

        # Manage signed values
        if self.signed:
            if self.bytescount == 1:
                value = hex8_tosigned(value)
            elif self.bytescount == 2:
                value = hex16_tosigned(value)

        if self.divideby == 0:
            print("Division by zero, please check data item : ", dataitem.name)
            return None

        res = (float(value) * float(self.step) + float(self.offset)) / float(self.divideby)

        if len(self.format) and '.' in self.format:
            acc = len(self.format.split('.')[1])
            fmt = '%.' + str(acc) + 'f'
            res = fmt % res
        else:
            if int(res) == res:
                return str(int(res))

        return str(res)

    def getIntValue(self, resp, dataitem, ecu_endian):
        val = self.getHexValue(resp, dataitem, ecu_endian)
        if val is None:
            return None

        return int("0x" + val, 16)

    def getHexValue(self, resp, dataitem, ecu_endian):
        little_endian = False

        if ecu_endian == "Little":
            little_endian = True

        if dataitem.endian == "Little":
            little_endian = True

        if dataitem.endian == "Big":
            little_endian = False

        # Data cleaning
        resp = resp.strip().replace(' ', '')
        if not all(c in string.hexdigits for c in resp): resp = ''
        resp.replace(' ', '')

        res_bytes = [resp[i:i + 2] for i in range(0, len(resp), 2)]

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
                print("getHexValue >> abnormal remaining bytes ", bits, totalremainingbits)
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
        self.funcaddr = "00"
        self.ecuname = ""
        self.projects = []
        self.autoidents = []
        self.baudrate = 0

        if not data:
            return

        if isfile:
            if not os.path.exists(data):
                if os.path.exists("./ecus/" + data + ".xml"):
                    data = "./ecus/" + data + ".xml"

        if isfile and ".xml" not in data[-4:] and ".json" not in data[-5:]:
            xmlname = data + ".xml"
            if os.path.exists(xmlname):
                data = xmlname
            else:
                data += ".json"

        if isfile and '.json' in data:
            data2 = "./json/" + os.path.basename(data)
            jsdata = None
            if os.path.exists(data):
                jsfile = open(data, "r")
                jsdata = jsfile.read()
                jsfile.close()
            elif os.path.exists(data2):
                jsfile = open(data2, "r")
                jsdata = jsfile.read()
                jsfile.close()
            else:
                # Zipped json here
                if os.path.exists('ecu.zip'):
                    zf = zipfile.ZipFile('ecu.zip', mode='r')
                    if data in zf.namelist():
                        jsdata = zf.read(data)
                    elif os.path.basename(data) in zf.namelist():
                        jsdata = zf.read(os.path.basename(data))
                    else:
                        print("Cannot find file ", data)
                        return

            if jsdata is None:
                return

            ecudict = json.loads(jsdata)

            if "obd" in ecudict:
                self.ecu_protocol = ecudict['obd']['protocol']
                if self.ecu_protocol == "CAN":
                    self.ecu_send_id = ecudict['obd']['send_id']
                    self.ecu_recv_id = ecudict['obd']['recv_id']
                    if 'baudrate' in ecudict['obd']:
                        self.baudrate = int(ecudict['obd']['baudrate'])
                if self.ecu_protocol == "KWP2000":
                    self.fastinit = ecudict['obd']['fastinit']
                self.funcaddr = ecudict['obd']['funcaddr']
                if 'funcname' in ecudict['obd']:
                    self.funcname = ecudict['obd']['funcname']
                if "kw1" in ecudict['obd']:
                    self.kw1 = ecudict['obd']['kw1']
                    self.kw2 = ecudict['obd']['kw2']

            if 'endian' in ecudict:
                self.endianness = ecudict['endian']

            if 'ecuname' in ecudict:
                self.ecuname = ecudict['ecuname']

            devices = ecudict['devices']
            for device in devices:
                ecu_dev = Ecu_device(device)
                self.devices[ecu_dev.name] = ecu_dev

            requests = ecudict['requests']
            for request in requests:
                ecu_req = Ecu_request(request, self)
                self.requests[ecu_req.name] = ecu_req

            datalist = ecudict['data']
            for k, v in datalist.items():
                self.data[k] = Ecu_data(v, k)
        else:
            if isfile:
                if not os.path.exists(data):
                    print("Cannot load ECU file", data)
                    return
                xdom = xml.dom.minidom.parse(data)
                self.xmldoc = xdom.documentElement
            else:
                self.xmldoc = data

            if not self.xmldoc:
                print("XML not found")
                return

            target = getChildNodesByName(self.xmldoc, u"Target")

            if target:
                self.ecuname = target[0].getAttribute("Name")
                autoidents = getChildNodesByName(target[0], u"AutoIdents")
                if autoidents:
                    autoident = getChildNodesByName(autoidents[0], u"AutoIdent")
                    for ai in autoident:
                        autoident_dict = {}

                        autoident_dict['diagversion'] = ai.getAttribute("DiagVersion")
                        autoident_dict['supplier'] = ai.getAttribute("Supplier")
                        autoident_dict['soft'] = ai.getAttribute("Soft")
                        autoident_dict['version'] = ai.getAttribute("Version")
                        self.autoidents.append(autoident_dict)

                projects = getChildNodesByName(target[0], u"Projects")
                if projects:
                    for project in projects[0].childNodes:
                        self.projects.append(project.nodeName)

                functions = getChildNodesByName(target[0], u"Function")
                if functions:
                    self.funcaddr = hex(int(functions[0].getAttribute("Address")))[2:].upper().zfill(2)
                    self.funcname = functions[0].getAttribute("Name")

                can = getChildNodesByName(target[0], u"CAN")
                if can:
                    self.ecu_protocol = "CAN"
                    self.baudrate = int(can[0].getAttribute("BaudRate"))
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
                            KW1 = getChildNodesByName(fastinit[0], "KW1")
                            KW2 = getChildNodesByName(fastinit[0], "KW2")
                        else:
                            iso8 = getChildNodesByName(kwp, u"ISO8")
                            KW1 = getChildNodesByName(iso8[0], "KW1")
                            KW2 = getChildNodesByName(iso8[0], "KW2")

                        self.kw1 = hex(int(KW1[0].getAttribute("Value")))[2:].upper()
                        self.kw2 = hex(int(KW2[0].getAttribute("Value")))[2:].upper()

                    elif iso8:
                        self.fastinit = False
                        self.ecu_protocol = "ISO8"

                        self.kw1 = hex(
                            int(getChildNodesByName(iso8[0], "KW1")[0].getAttribute("Value")))[2:].upper()
                        self.kw2 = hex(
                            int(getChildNodesByName(iso8[0], "KW2")[0].getAttribute("Value")))[2:].upper()

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
                        self.endianness = endian_attr

                    requests = request_tag.getElementsByTagName("Request")
                    for f in requests:
                        ecu_req = Ecu_request(f, self)
                        self.requests[ecu_req.name] = ecu_req

                    data = self.xmldoc.getElementsByTagName("Data")
                    for f in data:
                        ecu_data = Ecu_data(f)
                        self.data[ecu_data.name] = ecu_data

    def get_request(self, name):
        if name in self.requests:
            return self.requests[name]
        for k, v in self.requests.items():
            if k.lower() == name.lower():
                return v
        return None

    def connect_to_hardware(self, canline=0):
        # Can
        ecuname = self.ecuname.encode('ascii', errors='ignore')
        if self.ecu_protocol == 'CAN':
            short_addr = elm.get_can_addr(self.ecu_send_id)
            if short_addr is None:
                print("Cannot retrieve functionnal address of ECU %s @ %s" % (self.ecuname, self.ecu_send_id))
                return False
            ecu_conf = {'idTx': self.ecu_send_id, 'idRx': self.ecu_recv_id, 'ecuname': str(ecuname)}

            if not options.simulation_mode:
                if self.baudrate == 250000 or self.baudrate == 10400:
                    ecu_conf['brp'] = "1"
                options.elm.init_can()
                options.elm.set_can_addr(short_addr, ecu_conf, canline)

        # KWP 2000 Handling
        elif self.ecu_protocol == 'KWP2000':
            ecu_conf = {'idTx': '', 'idRx': '', 'ecuname': str(ecuname), 'protocol': 'KWP2000'}
            options.opt_si = not self.fastinit
            if not options.simulation_mode:
                options.elm.init_iso()
                options.elm.set_iso_addr(self.funcaddr, ecu_conf)

        # ISO8 handling
        elif self.ecu_protocol == 'ISO8':
            ecu_conf = {'idTx': '', 'idRx': '', 'ecuname': str(ecuname), 'protocol': 'ISO8'}
            if not options.simulation_mode:
                options.elm.init_iso()
                options.elm.set_iso8_addr(self.funcaddr, ecu_conf)
        else:
            return False

        return True

    def dump_idents(self):
        idents = {}
        idents["address"] = self.funcaddr
        idents["group"] = self.funcname
        idents["protocol"] = self.ecu_protocol
        idents["projects"] = self.projects
        idents["ecuname"] = self.ecuname
        idents["autoidents"] = []

        for ai in self.autoidents:
            aidict = {"diagnostic_version": ai["diagversion"],
                      "supplier_code": ai["supplier"],
                      "soft_version": ai["soft"],
                      "version": ai["version"]}
            idents["autoidents"].append(aidict)

        return idents

    def dumpJson(self):
        js = {}
        js['autoidents'] = self.autoidents
        js['ecuname'] = self.ecuname
        js['obd'] = {}
        js['obd']['protocol'] = self.ecu_protocol
        if self.ecu_protocol == "CAN":
            js['obd']['send_id'] = self.ecu_send_id
            js['obd']['recv_id'] = self.ecu_recv_id
            js['obd']['baudrate'] = self.baudrate
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

        for key, value in self.data.items():
            name, d = value.dump()
            js['data'][name] = d

        for key, value in self.requests.items():
            js['requests'].append(value.dump())

        for key, value in self.devices.items():
            js['devices'].append(value.dump())

        dump = json.dumps(js, indent=1)
        return re.sub('\n +', lambda match: '\n' + '\t' * int(len(match.group().strip('\n')) / 2), dump)

# Protocols:
# KWP2000 FastInit MonoPoint            ?ATSP 5?
# KWP2000 FastInit MultiPoint           ?ATSP 5?
# KWP2000 Init 5 Baud Type I and II     ?ATSP 4?
# DiagOnCAN                             ATSP 6
# CAN Messaging (125 kbps CAN)          ?ATSP B?
# ISO8                                  ?ATSP 3?

class Ecu_ident:
    def __init__(self, diagversion, supplier, soft, version, name, group, href, protocol, projects, address, zipped=False):
        self.diagversion = diagversion
        self.supplier = supplier
        self.soft = soft
        self.version = version
        self.name = name
        self.group = group
        self.projects = projects
        self.href = href
        self.addr = address
        if "CAN" in protocol.upper():
            self.protocol = 'CAN'
        elif "KWP" in protocol.upper():
            self.protocol = 'KWP2000'
        elif "ISO8" in protocol.upper():
            self.protocol = 'ISO8'
        else:
            self.protocol = 'UNKNOWN'
        self.hash = diagversion + supplier + soft + version
        self.zipped = zipped

    def checkWith(self, diagversion, supplier, soft, version, addr):
        if self.diagversion == "":
            return
        supplier_strip = self.supplier.strip()
        soft_strip = self.soft.strip()
        version_strip = self.version.strip()
        if int("0x" + self.diagversion, 16) != int("0x" + diagversion, 16):
            return False
        if supplier_strip != supplier.strip()[:len(supplier_strip)]:
            return False
        if soft_strip != soft.strip()[:len(soft_strip)]:
            return False
        if version_strip != version.strip()[:len(version_strip)]:
            return False

        self.addr = addr
        return True

    # Minimal checking
    def checkApproximate(self, diagversion, supplier, soft, addr):
        if self.diagversion == "":
            return
        if self.supplier.strip() != supplier.strip():
            return False
        if self.soft.strip() != soft.strip():
            return False

        self.addr = addr
        return True

    def dump(self):
        js = {}
        js['diagnostic_version'] = self.diagversion
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

    def __init__(self, forceXML=False):
        self.targets = []
        self.vehiclemap = {}
        self.numecu = 0
        self.available_addr_kwp = []
        self.available_addr_can = []
        self.addr_group_mapping_long = {}
        self.addr_group_mapping = {"02": u"Suspension pilotée", "51": u"Tableau de bord", "29": u"Climatisation",
                                   "D2": u"GATEWAY", "00": u"CAN Vehicle Network", "1E": u"4WD", "01": u"ABS-VDC - ABS-ESP",
                                   "95": u"EVC", "26": u"UCBIC/BFR", "60": u"HMD", "50": u"Tachometer", "A1": u"HFM",
                                   "93": u"LBC", "6E": u"BVA", "04": u"Direction assistée", "68": u"PEB", "58": u"Navigation",
                                   "2B": u"RADAR", "F7": u"LDCM", "08": u"TPMS", "C0": u"HFM", "13": u"Audio", "59": u"MIU",
                                   "F8": u"RDCM", "24": u"ACC", "27": u"EMM", "A8": u"LBC2", "23": u"4WS", "11": u"ADAS-Sub",
                                   "2E": u"UBP", "67": u"BCB", "0E": u"Aide au parking", "0D": u"Frein de parking électrique",
                                   "28": u"CSHV", "FF": u"CAN2", "62": u"FCAM", "DA": u"EVC-HCM-VCM_29b", "E8": u"SVS", "2F": u"IKEY",
                                   "64": u"SOW_right", "07": u"HLS", "D3": u"UDM", "77": u"DCM Renault", "86": u"AAU", "3A": u"AAM",
                                   "4D": u"SCU", "DF": u"Cluster", "A5": u"DCM", "10": u"Injection NISSAN", "0B": u"ACC", "61": u"AVM",
                                   "46": u"Engineering", "EA": u"TCASE", "87": u"C-Box", "1B": u"DIFF LOCK", "72": u"Lampes à décharge à droite 84",
                                   "ED": u"Audio", "EC": u"TPAD", "1C": u"Pilotage capote", "37": u"Onduleur", "D0": u"GATEWAY",
                                   "32": u"Superviseur", "A6": u"PDCM", "66": u"VCCU", "71": u"HLL_DDL2", "E9": u"EPS",
                                   "25": u"IDM", "79": u"GPL", "E2": u"C-Display", "A7": u"PBD", "6B": u"BSW", "2D": u"ABS-VDC",
                                   "97": u"PLC/PLGW", "DE": u"ASBMD", "31": u"Transpondeur", "63": u"SOW Left", "E6": u"SCCM",
                                   "2A": u"ADP", "0F": u"HFCK", "EB": u"HU", "78": u"DCM", "73": u"Embrayage piloté",
                                   "5B": u"ADAS Insulator", "5A": u"ODS_DDL2", "3F": u"Navigation", "81": u"VSP", "40": u"TSR_FRONTCAM",
                                   "06": u"EMCU", "E1": u"CCU", "1A": u"Additional Heater", "E3": u"HMI GateWay",
                                   "AE": u"UCBIC ISO8", "91": u"LBC (HEV) CPC", "09": u"MC HEV FSCM", "EE": u"Controlographe",
                                   "52": u"Synthèse de la parole", "D1": u"UDM", "E7": u"SCRCM", "41": u"GATEWAY", "2C": u"Airbag",
                                   "70": u"Lampes à décharge 84", "E4": u"IBS", "E0": u"HERMES", "7A": u"Injection",
                                   "AB": u"Régulateur de vitesse (ISO 8)", "B0": u"Transpondeur (ISO8)", "82": u"WCGS"}

        f = open("./json/addressing.json", "r")
        js = json.loads(f.read())
        f.close()

        for k, v in js.items():
            self.addr_group_mapping[k] = v[0]
            self.addr_group_mapping_long[k] = v[1]

        xmlfile = options.ecus_dir + "/eculist.xml"

        jsonecu_files = glob.glob("./json/*.json.targets")
        for jsonecu_file in jsonecu_files:
            self.numecu += 1
            json_file = open(jsonecu_file, "r")
            json_data = json_file.read()
            json_file.close()
            ecus_dict = json.loads(json_data)
            for ecu_dict in ecus_dict:
                href = jsonecu_file.replace(".targets", "")
                name = os.path.basename(href)
                # Fix typo bug
                diagversion = ""
                if 'diagnostic_version' in ecu_dict:
                    diagversion = ecu_dict['diagnostic_version']
                else:
                    diagversion = ecu_dict['diagnotic_version']

                addr = ecu_dict['address']

                if 'KWP' in ecu_dict['protocol']:
                    if addr not in self.available_addr_kwp:
                        self.available_addr_kwp.append(str(addr))
                elif 'CAN' in ecu_dict['protocol']:
                    if addr not in self.available_addr_can:
                        self.available_addr_can.append(str(addr))

                if str(addr) not in self.addr_group_mapping:
                    print("Adding group ", addr,  ecu_dict['group'])
                    self.addr_group_mapping[str(addr)] = ecu_dict['group']

                ecu_ident = Ecu_ident(diagversion, ecu_dict['supplier_code'],
                                      ecu_dict['soft_version'], ecu_dict['version'],
                                      name, ecu_dict['group'], href, ecu_dict['protocol'],
                                      ecu_dict['projects'], addr)

                for proj in ecu_dict['projects']:
                    projname = proj[0:3].upper()
                    if not projname in self.vehiclemap:
                        self.vehiclemap[projname] = []
                    self.vehiclemap[projname].append((ecu_dict['protocol'], addr))

                self.targets.append(ecu_ident)

        if os.path.exists("ecu.zip") and not forceXML:
            zf = zipfile.ZipFile("ecu.zip", mode='r')
            jsdb = zf.read("db.json")
            dbdict = json.loads(jsdb)
            for href, targetv in dbdict.items():
                self.numecu += 1
                ecugroup = targetv['group']
                ecuprotocol = targetv['protocol']
                ecuprojects = targetv['projects']
                ecuaddress = targetv['address']
                ecuname = targetv['ecuname']

                if 'KWP' in ecuprotocol:
                    if not ecuaddress in self.available_addr_kwp:
                        self.available_addr_kwp.append(str(ecuaddress))
                elif 'CAN' in ecuprotocol:
                    if not ecuaddress in self.available_addr_can:
                        self.available_addr_can.append(str(ecuaddress))

                if str(ecuaddress) not in self.addr_group_mapping:
                    self.addr_group_mapping[ecuaddress] = targetv['group']

                if len(targetv['autoidents']) == 0:
                    ecu_ident = Ecu_ident("", "", "", "", ecuname, ecugroup, href, ecuprotocol,
                                          ecuprojects, ecuaddress, True)
                    self.targets.append(ecu_ident)
                else:
                    for target in targetv['autoidents']:
                        ecu_ident = Ecu_ident(target['diagnostic_version'], target['supplier_code'],
                                              target['soft_version'], target['version'],
                                              ecuname, ecugroup, href, ecuprotocol,
                                              ecuprojects, ecuaddress, True)

                        self.targets.append(ecu_ident)

                for proj in ecuprojects:
                    projname = proj[0:3].upper()
                    if not projname in self.vehiclemap:
                        self.vehiclemap[projname] = []
                    self.vehiclemap[projname].append((ecuprotocol, ecuaddress))

                self.targets.append(ecu_ident)

        if os.path.exists(xmlfile):
            xdom = xml.dom.minidom.parse(xmlfile)
            self.xmldoc = xdom.documentElement

            if not self.xmldoc:
                print("Unable to find eculist")
                return

            functions = self.xmldoc.getElementsByTagName("Function")
            for function in functions:
                targets = function.getElementsByTagName("Target")
                address = function.getAttribute("Address")
                address = hex(int(address))[2:].zfill(2).upper()

                for target in targets:
                    group = target.getAttribute("group")
                    href = target.getAttribute("href")
                    name = target.getAttribute("Name")
                    protnode = target.getElementsByTagName("Protocol")
                    if protnode:
                        protocol = protnode[0].firstChild.nodeValue

                    if len(group) and (str(address) not in self.addr_group_mapping):
                        self.addr_group_mapping[str(address)] = group

                    if 'CAN' in protocol.upper():
                        if address not in self.available_addr_can:
                            self.available_addr_can.append(str(address))
                    elif 'KWP' in protocol.upper():
                        if address not in self.available_addr_kwp:
                            self.available_addr_kwp.append(str(address))

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
                            ecu_ident = Ecu_ident(diagversion, supplier, soft, version, name, group, href, protocol,
                                                  projects, address)
                            self.targets.append(ecu_ident)

                    if projectselems:
                        for project in projectselems[0].childNodes:
                            projname = project.nodeName[0:3].upper()
                            if not projname in self.vehiclemap:
                                self.vehiclemap[projname] = []
                            self.vehiclemap[projname].append((ecu_ident.protocol, address))

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

    def getTargetsByHref(self, href):
        tgt = []
        for t in self.targets:
            if t.href == href:
                tgt.append(t)
        return tgt

    def dump(self):
        js = []
        for t in self.targets:
            if t.protocol == 'CAN' or t.protocol == 'KWP2000' or 'ISO8' == t.protocol:
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

    def identify_old(self, addr, label, force=False):
        if not options.simulation_mode:
            if not options.elm.start_session_can('10C0'):
                return

        if options.simulation_mode and not force:
            # Give scanner something to eat...
            if addr == "04":
                can_response = "61 80 30 36 32 36 52 35 37 31 31 35 32 31 36 52 01 99 00 00 00 00 02 00 00 88"
            if addr == "51":
                can_response = "61 80 82 00 45 15 05 08 32 31 33 21 11 31 39 09 00 09 06 02 05 01 0D 8D 39 00"
            elif addr == "7A":
                # Test approximate case
                can_response = "61 80 82 00 44 66 27 44 32 31 33 82 00 38 71 38 00 A7 75 00 56 05 02 01 00 00"
            else:
                can_response = "7F 80"
        else:
            can_response = options.elm.request(req='2180', positive='61', cache=False)

        self.check_ecu(can_response, label, addr, "CAN")

    def identify_from_frame(self, addr, can_response):
        self.check_ecu(can_response, None, addr, "CAN")

    def identify_new(self, addr, label):
        diagversion = ""
        supplier = ""
        soft_version = ''
        soft = ""
        can_response = ""

        # Check diag version
        if not options.simulation_mode:
            if not options.elm.start_session_can('1003'):
                # Bad response of SDS, no need check old method (10C0)
                return False

        if options.simulation_mode:
            # Give scanner something to eat...
            if addr == '26':
                can_response = "62 F1 A0 08"
            elif addr == '13':
                can_response = "62 F1 A0 0D"
            elif addr == '26':
                can_response = "62 F1 A0 08"
            elif addr == '62':
                can_response = "62 F1 A0 04"
            elif addr == '01':
                can_response = "62 F1 A0 04"
            elif addr == '04':
                can_response = "62 F1 A0 04"
        else:
            can_response = options.elm.request(req='22F1A0', positive='', cache=False)
            if 'WRONG' in can_response:
                return False
        diagversion = can_response.replace(' ', '')[6:8]

        # Check supplier ident
        if options.simulation_mode:
            # Give scanner something to eat...
            if addr == '26':
                can_response = "62 F1 8A 43 4F 4E 54 49 4E 45 4E 54 41 4C 20 41 55 54 4F 4D 4F 54 49 56 45 20 20 20 20 "\
                               "20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 "\
                               "20 20 20 20 20 20 20 20 20"
            elif addr == '13':
                can_response = "62 F1 8A 43 41 50"
            elif addr == '26':
                can_response = "62 F1 8A 43 4F 4E 54 49 4E 45 4E 54 41 4C 20 41 55 54 4F 4D 4F 54 49 56 45 20 20 20 20"\
                               "20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20"\
                               "20 20 20 20 20 20 20 20 20 FF FF"
            elif addr == '62':
                can_response = "62 F1 8A 41 46 4B"
            elif addr == '01':
                can_response = "62 F1 8A 43 41 53"
            elif addr == '04':
                can_response = "62 F1 8A 56 69 73 74 65 6F 6E 5F 4E 61 6D 65 73 74 6F 76 6F 5F 30 39 36 20 20 20 20"\
                               "20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20"\
                               "20 20 20 20 20 20 20 20 20 20 20 20 20"
        else:
            can_response = options.elm.request(req='22F18A', positive='', cache=False)
            if 'WRONG' in can_response:
                return False
        supplier = bytes.fromhex(can_response.replace(' ', '')[6:132]).decode("utf8", "ignore")

        # Check soft number
        if options.simulation_mode:
            # Give scanner something to eat...
            if addr == '26':
                can_response = "62 F1 94 31 34 32 36 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 " \
                               "20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 " \
                               "20 20 20 20 20 20 20 20 20"
            elif addr == '13':
                can_response = "62 F1 94 32 32"
            elif addr == '26':
                can_response = "62 F1 94 31 34 32 36 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 "\
                               "20 20 20 20 20 FF FF FF FF FF FF"
            elif addr == '62':
                can_response = "62 F1 94 31 30 30 30 30 30 30 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 "\
                               "20 20 20 20 20 FF FF FF FF FF FF"
            elif addr == '01':
                can_response = "62 F1 94 4E 33 32 52 41 46 30 30 30 31 31 00 00 00 00 00 00"
            elif addr == '04':
                can_response = "62 F1 94 56 30 36 30 32 F1 94 56 30 36"
        else:
            can_response = options.elm.request(req='22F194', positive='', cache=False)
            if 'WRONG' in can_response:
                return False

        soft = bytes.fromhex(can_response.replace(' ', '')[6:38]).decode("utf8", "ignore")
        # Check soft version
        if options.simulation_mode:
            # Give scanner something to eat...
            if addr == '26':
                can_response = "62 F1 95 31 30 30 30 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 " \
                               "20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 " \
                               "20 20 20 20 20 20 20 20 20"
            elif addr == '13':
                can_response = "62 F1 95 31 38 35 39 30 FF FF FF FF FF"
            elif addr == '26':
                can_response = "62 F1 95 46 30 37 2F 34 6F 00 00 00 03"
            elif addr == '62':
                can_response = "62 F1 95 30 35 30 31 30 30 30 32 31 37 30 30 FF FF FF FF FF"
            elif addr == '01':
                can_response = "62 F1 95 46 30 37 2F 34 6F 00 00 00 03"
            elif addr == '04':
                can_response = "62 F1 95 56 30 36 30 32 F1 95 56 30 36"
        else:
            can_response = options.elm.request(req='22F195', positive='', cache=False)
            if 'WRONG' in can_response:
                return False

        # Remove unwanted non-ascii FF from string
        soft_version = bytes.fromhex(can_response.replace(' ', '')[6:38]).decode("utf8", "ignore")
        if diagversion == "":
            return False

        self.check_ecu2(diagversion, supplier, soft, soft_version, label, addr, "CAN")
        # New method succeded, return the good news
        return True

    def scan(self, progress=None, label=None, vehiclefilter=None, canline=0):
        i = 0
        if not options.simulation_mode:
            options.elm.init_can()

        project_can_addresses = []
        if vehiclefilter:
            if vehiclefilter in self.ecu_database.vehiclemap:
                for proto, addr in self.ecu_database.vehiclemap[vehiclefilter]:
                    if proto == u"CAN" and not addr in project_can_addresses:
                        project_can_addresses.append(addr)
        else:
            project_can_addresses = self.ecu_database.available_addr_can

        if len(project_can_addresses) == 0:
            return

        if progress:
            progress.setRange(0, len(project_can_addresses))
            progress.setValue(0)

        try_new = []

        # Only scan available ecu addresses
        for addr in list(set(project_can_addresses)):
            i += 1
            if progress:
                progress.setValue(i)
                self.qapp.processEvents()

            # Don't want to scan NON ISO-TP
            if addr == '00' or addr == 'FF':
                continue

            if addr not in elm.dnat:
                print("Warning, address %s is not mapped" % addr)
                continue

            if len(elm.dnat[addr]) > 3:
                print("Skipping CAN extended address (not supported yet) ", addr)
                continue

            print("Scanning ECU %s" % self.ecu_database.addr_group_mapping[addr].encode('ascii', 'ignore'))
            if not options.simulation_mode:
                options.elm.init_can()
                options.elm.set_can_addr(addr, {'ecuname': 'SCAN'}, canline)

            # Avoid to waste time, try new method : not working -> try old
            if not self.identify_new(addr, label):
                self.identify_old(addr, label)

        if not options.simulation_mode:
            options.elm.close_protocol()

        return try_new

    def scan_kwp(self, progress=None, label=None, vehiclefilter=None):
        if options.simulation_mode:
            # Test data..
            # diagversion, supplier, soft, version, name, group, href, protocol, projects, address):
            self.ecus["S2000_Atmo__SoftA3"] = Ecu_ident("004", "213", "00A5", "8300", "UCH", "GRP", "S2000_Atmo___SoftA3.json",
                                                        "KWP2000 FastInit MonoPoint", [], "7A")
        else:
            options.elm.init_iso()

        project_kwp_addresses = []
        if vehiclefilter:
            if vehiclefilter in self.ecu_database.vehiclemap:
                for proto, addr in self.ecu_database.vehiclemap[vehiclefilter]:
                    if proto == u"KWP2000" and not addr in project_kwp_addresses:
                        project_kwp_addresses.append(addr)
        else:
            project_kwp_addresses = self.ecu_database.available_addr_kwp

        if len(project_kwp_addresses) == 0:
            return

        i = 0
        if progress:
            progress.setRange(0, len(project_kwp_addresses))
            progress.setValue(0)

        for addr in project_kwp_addresses:
            i += 1
            if progress:
                progress.setValue(i)
                self.qapp.processEvents()

            if not options.simulation_mode:
                options.opt_si = True
                if not options.elm.set_iso_addr(addr,
                                            {'idTx': '', 'idRx': '',
                                             'ecuname': 'SCAN',
                                             'protocol': "KWP2000"}):
                    continue
                options.elm.start_session_iso('10C0')
                can_response = options.elm.request(req='2180', positive='61', cache=False)
            else:
                # Send some data collected during my tests
                if addr == "02":
                    can_response = "61 80 77 00 31 38 31 04 41 42 45 E3 17 03 00 38 00 07 00 00 00 00 09 11 12 00"
                elif addr == "7A":
                    can_response = "61 80 82 00 23 66 18 14 30 33 37 82 00 08 53 86 00 CB A4 00 70 06 3C 02 B1 A4"
                elif addr == "26":
                    can_response = "61 80 82 00 03 27 76 00 32 31 33 11 01 10 30 08 00 66 00 00 00 41 06 01 F1 38"
                else:
                    continue

            self.check_ecu(can_response, label, addr, "KWP")
        if not options.simulation_mode:
            options.elm.close_protocol()

    def check_ecu(self, can_response, label, addr, protocol):
        if len(can_response) > 59:
            diagversion = str(int(can_response[21:23], 16))
            supplier = bytes.fromhex(can_response[24:32].replace(' ', '')).decode('utf-8')
            soft = can_response[48:53].replace(' ', '')
            version = can_response[54:59].replace(' ', '')
            self.check_ecu2(diagversion, supplier, soft, version, label, addr, protocol)

    def check_ecu2(self, diagversion, supplier, soft, version, label, addr, protocol):
        approximate_ecu = []
        found_exact = False
        found_approximate = False
        if addr in self.ecu_database.addr_group_mapping:
            ecu_type = self.ecu_database.addr_group_mapping[addr]
        else:
            ecu_type = "UNKNOWN"

        targetNum = 0
        for target in self.ecu_database.targets:
            if target.protocol == "CAN" and protocol != "CAN":
                continue
            if target.protocol.startswith("KWP") and protocol != "KWP":
                continue

            if target.checkWith(diagversion, supplier, soft, version, addr):
                ecuname = "[ " + target.group + " ] " + target.name

                self.ecus[ecuname] = target
                self.num_ecu_found += 1
                if label is not None:
                    label.setText("Found %i ecu" % self.num_ecu_found)
                found_exact = True
                href = target.href
                line = "<font color='green'>Identified ECU [%s]@%s : %s DIAGVERSION [%s]"\
                       "SUPPLIER [%s] SOFT [%s] VERSION [%s] {%i}</font>"\
                       % (ecu_type, target.addr, href, diagversion, supplier, soft, version, targetNum)

                options.main_window.logview.append(line)
                break
            elif target.checkApproximate(diagversion, supplier, soft, addr):
                approximate_ecu.append(target)
                found_approximate = True

            targetNum += 1

        # Try to find the closest possible version of an ECU
        if not found_exact and found_approximate:
            min_delta_version = 0xFFFFFF
            kept_ecu = None
            for tgt in approximate_ecu:
                ecu_protocol = 'CAN'
                if tgt.protocol.startswith("KWP"):
                    ecu_protocol = "KWP"
                # Shouldn't happen, but...
                if tgt.protocol.startswith("ISO8"):
                    ecu_protocol = "KWP"
                if ecu_protocol != protocol:
                    continue

                # If version contains ASCII characters, I can do nothing for you...
                try:
                    int_version = int('0x' + version, 16)
                    int_tgt_version = int('0x' + tgt.version, 16)
                except ValueError:
                    continue

                delta = abs(int_tgt_version - int_version)
                if delta < min_delta_version:
                    min_delta_version = delta
                    kept_ecu = tgt

            if kept_ecu:
                self.approximate_ecus[kept_ecu.name] = kept_ecu
                self.num_ecu_found += 1
                if label is not None:
                    label.setText("Found %i ecu" % self.num_ecu_found)

                line = "<font color='red'>Found ECU [%s] (not perfect match) :"\
                       "%s DIAGVERSION [%s] SUPPLIER [%s] SOFT [%s] VERSION [%s instead %s]</font>"\
                       % (ecu_type, kept_ecu.name, diagversion, supplier, soft, version, tgt.version)

                options.main_window.logview.append(line)

        if not found_exact and not found_approximate:
            line = "<font color='red'>Found ECU [%s] (no relevant ECU file found) :" \
                   "DIAGVERSION [%s] SUPPLIER [%s] SOFT [%s] VERSION [%s]</font>" \
                   % (ecu_type, diagversion, supplier, soft, version)

            options.main_window.logview.append(line)


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
            print("Starting zipping " + target + " " + str(i) + "/" + str(len(ecus)))
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
    parser.add_argument('--convertxml', action="store_true", default=None, help="Convert XML file to JSON")

    args = parser.parse_args()

    if args.zipfs:
        make_zipfs()

    if args.testdb:
        db = Ecu_database()

    if args.convertxml:
        db = Ecu_database()

    if args.testecufile:
        db = Ecu_file("ecus/Sim32_RD3CA0_W44_J77_X85.json", True)
