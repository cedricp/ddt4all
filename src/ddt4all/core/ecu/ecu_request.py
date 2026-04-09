from ddt4all.core.ecu.data_item import DataItem
import ddt4all.options as options

_ = options.translator('ddt4all')

class EcuRequest:
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
            if 'minbytes' in data:
                self.minbytes = data['minbytes']
            if 'shiftbytescount' in data:
                self.shiftbytescount = data['shiftbytescount']
            if 'replybytes' in data:
                self.replybytes = data['replybytes']
            if 'manualsend' in data:
                self.manualsend = data['manualsend']
            if 'sentbytes' in data:
                self.sentbytes = data['sentbytes']

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
                    di = DataItem(v, self.ecu_file.endianness, k)
                    self.sendbyte_dataitems[k] = di

            if 'receivebyte_dataitems' in data:
                rbdi = data['receivebyte_dataitems']
                for k, v in rbdi.items():
                    di = DataItem(v, self.ecu_file.endianness, k)
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
                        di = DataItem(dataitem, self.ecu_file.endianness)
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
                        di = DataItem(dataitem, self.ecu_file.endianness)
                        self.sendbyte_dataitems[di.name] = di

    def send_request(self, inputvalues=None, test_data=None):
        if inputvalues is None:
            inputvalues = {}
        request_stream = self.build_data_stream(inputvalues)
        request_stream = " ".join(request_stream)

        if options.debug:
            print(_("Generated stream "), request_stream)

        if options.simulation_mode:
            if test_data is not None:
                elmstream = test_data
                print(_("Send request stream "), request_stream)
            else:
                # return default reply bytes...
                elmstream = self.replybytes
        else:
            elmstream = options.elm.request(request_stream)

        if options.debug:
            print(_("Received stream "), elmstream)

        if elmstream.startswith('WRONG RESPONSE'):
            return None

        if elmstream.startswith('7F'):
            nrsp = options.elm.errorval(elmstream[6:8])
            print(_("Request ECU Error"), nrsp)
            return None

        values = self.get_values_from_stream(elmstream)

        if options.debug:
            print(_("Decoded values"), values)

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