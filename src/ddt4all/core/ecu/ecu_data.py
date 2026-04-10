import math
import string

from ddt4all.core.ecu.utils import (
    cleanhtml,
    hex16_tosigned,
    hex8_tosigned
)
import ddt4all.options as options

_ = options.translator('ddt4all')

class EcuData:
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

            lists = self.xmldoc.getElementsByTagName("List")
            if lists:
                for lst in lists:
                    items = lst.getElementsByTagName("Item")
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
                if bytesascii and bytesascii == '1':
                    self.bytesascii = True

            bits = self.xmldoc.getElementsByTagName("Bits")
            if bits:
                bitscount = bits.item(0).getAttribute("count")
                if bitscount:
                    self.bitscount = int(bitscount)
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
        if not self.scaled:
            js['scaled'] = self.scaled
        if not self.signed:
            js['signed'] = self.signed
        if not self.byte:
            js['byte'] = self.byte
        if not self.binary:
            js['binary'] = self.binary
        if self.bytescount != 1:
            js['bytescount'] = self.bytescount
        if not self.bytesascii:
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
                except Exception:
                    return None

                # Input value must be base 10
                value = int((value * float(self.divideby) - float(self.offset)) / float(self.step))
            else:
                value = int("0x" + value, 16)
        else:
            if not test_mode:
                # Check input length and validity
                if isinstance(value, list):
                    if not all(len(byte) == 2 and all(c in string.hexdigits for c in byte) for byte in value):
                        return None
                    value = int('0x' + ''.join(value), 16)
                elif isinstance(value, str):
                    if not all(c in string.hexdigits for c in value):
                        return None
                    value = int('0x' + value, 16)
                else:
                    return None
            else:
                # Value is base 16
                value = int('0x' + value, 16)

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
        requestasbin = "0b" + requestasbin.lstrip("b")
        valueasint = int(requestasbin, 2)
        valueashex = hex(valueasint)[2:].replace("L", "").zfill(numreqbytes * 2).upper()

        for i in range(numreqbytes):
            bytes_list[i + start_byte] = valueashex[i * 2:i * 2 + 2].zfill(2)

        return bytes_list

    def getDisplayValue(self, elm_data, dataitem, ecu_endian):
        value = self.getHexValue(elm_data, dataitem, ecu_endian)
        if value is None:
            return None

        if self.bytesascii:
            return bytes.fromhex(value).decode('utf-8', errors="ignore")

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
                    print(_("Warning, cannot get signed value for") + " %s" % dataitem.name)

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
            print(_("Division by zero, please check data item: "), dataitem.name)
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
        if not all(c in string.hexdigits for c in resp):
            resp = ''
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
                print(_("getHexValue >> abnormal remaining bytes "), bits, totalremainingbits)
            hexval = hex(int("0b" + tmp_bin, 2))[2:].replace("L", "")
        else:
            valtmp = "0b" + hextobin[startBit:startBit + bits]
            hexval = hex(int(valtmp, 2))[2:].replace("L", "")

        # Resize to original length
        hexval = hexval.zfill(databytelen * 2)
        return hexval