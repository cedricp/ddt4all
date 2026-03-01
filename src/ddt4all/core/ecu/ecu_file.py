
import os
import re
import xml.dom.minidom
import zipfile

import elm
import json

from ddt4all.core.ecu.utils import getChildNodesByName
from ddt4all.core.ecu.ecu_device import EcuDevice
from ddt4all.core.ecu.ecu_request import EcuRequest
from ddt4all.core.ecu.ecu_data import EcuData
import ddt4all.options as options

_ = options.translator('ddt4all')

class EcuFile:
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
                        print(_("Cannot find file "), data)
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
                ecu_dev = EcuDevice(device)
                self.devices[ecu_dev.name] = ecu_dev

            requests = ecudict['requests']
            for request in requests:
                ecu_req = EcuRequest(request, self)
                self.requests[ecu_req.name] = ecu_req

            datalist = ecudict['data']
            for k, v in datalist.items():
                self.data[k] = EcuData(v, k)
        else:
            if isfile:
                if not os.path.exists(data):
                    print(_("Cannot load ECU file"), data)
                    return
            xdom = xml.dom.minidom.parse(data)
            self.xmldoc = xdom.documentElement

            if not self.xmldoc:
                print(_("XML not found"))
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
                ecu_dev = EcuDevice(d)
                self.devices[ecu_dev.name] = ecu_dev

            requests_tag = self.xmldoc.getElementsByTagName("Requests")

            if requests_tag:
                for request_tag in requests_tag:

                    endian_attr = request_tag.getAttribute("Endian")
                    if endian_attr:
                        self.endianness = endian_attr

                    requests = request_tag.getElementsByTagName("Request")
                    for f in requests:
                        ecu_req = EcuRequest(f, self)
                        self.requests[ecu_req.name] = ecu_req

                    data = self.xmldoc.getElementsByTagName("Data")
                    for f in data:
                        ecu_data = EcuData(f)
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
        short_addr = None
        if self.ecu_protocol == 'CAN':
            if not options.simulation_mode:
                if len(self.ecu_send_id) == 8:
                    short_addr = elm.get_can_addr_ext(self.ecu_send_id)
                else:
                    short_addr = elm.get_can_addr(self.ecu_send_id)
                if short_addr is None:
                    print(
                        _("Cannot retrieve functionnal address of ECU") + " %s @ %s" % (self.ecuname, self.ecu_send_id))
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
