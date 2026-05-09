import glob
import os
import xml.dom.minidom
import zipfile

import json

from ddt4all.core.ecu.ecu_ident import EcuIdent
import ddt4all.options as options

_ = options.translator('ddt4all')
addressing = {}
doip_addressing = {}


class EcuDatabase:

    def __init__(self, forceXML=False):
        global ecu_ident, protocol
        self.targets = []
        self.vehiclemap = {}
        self.numecu = 0
        self.available_addr_kwp = []
        self.available_addr_can = []
        self.available_addr_doip = []  # Add DoIP address support
        self.addr_group_mapping_long = {}
        self.addr_group_mapping = {}

        for k, v in doip_addressing.items():
            self.addr_group_mapping[k] = v
            self.addr_group_mapping_long[k] = v

        for k, v in addressing.items():
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
                elif 'DOIP' in ecu_dict['protocol'].upper():
                    if addr not in self.available_addr_doip:
                        self.available_addr_doip.append(str(addr))

                if str(addr) not in self.addr_group_mapping:
                    print(_("Adding group "), addr, ecu_dict['group'])
                    self.addr_group_mapping[str(addr)] = ecu_dict['group']

                ecu_ident = EcuIdent(diagversion, ecu_dict['supplier_code'],
                                      ecu_dict['soft_version'], ecu_dict['version'],
                                      name, ecu_dict['group'], href, ecu_dict['protocol'],
                                      ecu_dict['projects'], addr)

                for proj in ecu_dict['projects']:
                    projname = proj[0:3].upper()
                    if projname not in self.vehiclemap:
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
                    if ecuaddress not in self.available_addr_kwp:
                        self.available_addr_kwp.append(str(ecuaddress))
                elif 'CAN' in ecuprotocol:
                    if ecuaddress not in self.available_addr_can:
                        self.available_addr_can.append(str(ecuaddress))
                elif 'DOIP' in ecuprotocol.upper():
                    if ecuaddress not in self.available_addr_doip:
                        self.available_addr_doip.append(str(ecuaddress))

                if str(ecuaddress) not in self.addr_group_mapping:
                    self.addr_group_mapping[ecuaddress] = targetv['group']

                if len(targetv['autoidents']) == 0:
                    ecu_ident = EcuIdent("", "", "", "", ecuname, ecugroup, href, ecuprotocol,
                                          ecuprojects, ecuaddress, True)
                    self.targets.append(ecu_ident)
                else:
                    for target in targetv['autoidents']:
                        ecu_ident = EcuIdent(target['diagnostic_version'], target['supplier_code'],
                                              target['soft_version'], target['version'],
                                              ecuname, ecugroup, href, ecuprotocol,
                                              ecuprojects, ecuaddress, True)

                        self.targets.append(ecu_ident)

                for proj in ecuprojects:
                    projname = proj[0:3].upper()
                    if projname not in self.vehiclemap:
                        self.vehiclemap[projname] = []
                    self.vehiclemap[projname].append((ecuprotocol, ecuaddress))

                self.targets.append(ecu_ident)

        if os.path.exists(xmlfile):
            xdom = xml.dom.minidom.parse(xmlfile)
            self.xmldoc = xdom.documentElement

            if not self.xmldoc:
                print(_("Unable to find eculist"))
                return

            functions = self.xmldoc.getElementsByTagName("Function")
            for function in functions:
                targets = function.getElementsByTagName("Target")
                address = function.getAttribute("Address")
                address = hex(int(address))[2:].zfill(2).upper()

                for target in targets:
                    self.numecu += 1
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
                    elif 'DOIP' in protocol.upper():
                        if address not in self.available_addr_doip:
                            self.available_addr_doip.append(str(address))

                    autoidents = target.getElementsByTagName("AutoIdents")
                    projectselems = target.getElementsByTagName("Projects")
                    projects = []
                    if projectselems:
                        for c in projectselems[0].childNodes:
                            projects.append(c.nodeName)
                    for autoident in autoidents:
                        if len(autoident.getElementsByTagName("AutoIdent")) == 0:
                            ecu_ident = EcuIdent("00", "??????", "0000", "0000", name, group, href, protocol,
                                                  projects, address)
                            self.targets.append(ecu_ident)
                        for ai in autoident.getElementsByTagName("AutoIdent"):
                            diagversion = ai.getAttribute("DiagVersion")
                            supplier = ai.getAttribute("Supplier")
                            soft = ai.getAttribute("Soft")
                            version = ai.getAttribute("Version")
                            ecu_ident = EcuIdent(diagversion, supplier, soft, version, name, group, href, protocol,
                                                  projects, address)
                            self.targets.append(ecu_ident)

                    if projectselems:
                        for project in projectselems[0].childNodes:
                            projname = project.nodeName[0:3].upper()
                            if projname not in self.vehiclemap:
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