
from ddt4all.core.ecu.ecu_database import EcuDatabase
from ddt4all.core.ecu.ecu_ident import EcuIdent
import ddt4all.core.elm.elm as elm
import ddt4all.options as options

_ = options.translator('ddt4all')

class EcuScanner:
    def __init__(self):
        self.totalecu = 0
        self.ecus = {}
        self.approximate_ecus = {}
        self.ecu_database = EcuDatabase()
        self.num_ecu_found = 0
        self.report_data = []
        self.qapp = None

    def getNumEcuDb(self):
        return self.ecu_database.numecu

    def getNumAddr(self):
        count = []
        for k in elm.dnat:
            if k not in count:
                count.append(k)
        for k in elm.dnat_ext:
            if k not in count:
                count.append(k)
        return len(count)

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
                can_response = "62 F1 8A 43 4F 4E 54 49 4E 45 4E 54 41 4C 20 41 55 54 4F 4D 4F 54 49 56 45 20 20 20 20 " \
                               "20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 " \
                               "20 20 20 20 20 20 20 20 20"
            elif addr == '13':
                can_response = "62 F1 8A 43 41 50"
            elif addr == '26':
                can_response = "62 F1 8A 43 4F 4E 54 49 4E 45 4E 54 41 4C 20 41 55 54 4F 4D 4F 54 49 56 45 20 20 20 20" \
                               "20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20" \
                               "20 20 20 20 20 20 20 20 20 FF FF"
            elif addr == '62':
                can_response = "62 F1 8A 41 46 4B"
            elif addr == '01':
                can_response = "62 F1 8A 43 41 53"
            elif addr == '04':
                can_response = "62 F1 8A 56 69 73 74 65 6F 6E 5F 4E 61 6D 65 73 74 6F 76 6F 5F 30 39 36 20 20 20 20" \
                               "20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20" \
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
                can_response = "62 F1 94 31 34 32 36 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 " \
                               "20 20 20 20 20 FF FF FF FF FF FF"
            elif addr == '62':
                can_response = "62 F1 94 31 30 30 30 30 30 30 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 " \
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
            # Use integrated DeviceManager for enhanced features
            if hasattr(options, 'elm') and options.elm:
                # Initialize device with enhanced features
                from elm import DeviceManager
                DeviceManager.initialize_device(options.elm)
            
            options.elm.init_can()

        project_can_addresses = []
        if vehiclefilter:
            if vehiclefilter in self.ecu_database.vehiclemap:
                for proto, addr in self.ecu_database.vehiclemap[vehiclefilter]:
                    if proto == u"CAN" and addr not in project_can_addresses:
                        project_can_addresses.append(addr)
        else:
            project_can_addresses = self.ecu_database.available_addr_can

        if len(project_can_addresses) == 0:
            return

        if progress:
            progress.setRange(0, len(project_can_addresses))
            progress.setValue(0)

        # Only scan available ecu addresses
        for addr in list(set(project_can_addresses)):
            i += 1
            if progress:
                progress.setValue(i)
                self.qapp.processEvents()

            # Don't want to scan NON ISO-TP
            if addr == '00' or addr == 'FF':
                continue

            if not elm.addr_exist(addr):
                print(_("Warning, address") + " " + addr + " " + _("is not mapped"))
                continue

            text = _("Scanning address: ")
            try:
                # Try long name first
                print(f"{text + addr:<35} ECU: {self.ecu_database.addr_group_mapping_long[addr]}")
            except KeyError:
                # If not, short name
                print(f"{text + addr:<35} ECU: {self.ecu_database.addr_group_mapping[addr]}")

            if not options.simulation_mode:
                options.elm.init_can()
                options.elm.set_can_addr(addr, {'ecuname': 'SCAN'}, canline)

            # Avoid to waste time, try new method : not working -> try old
            if not self.identify_new(addr, label):
                self.identify_old(addr, label)

        if not options.simulation_mode:
            options.elm.close_protocol()

    def scan_kwp(self, progress=None, label=None, vehiclefilter=None):
        if options.simulation_mode:
            # Test data..
            # diagversion, supplier, soft, version, name, group, href, protocol, projects, address):
            self.ecus["S2000_Atmo__SoftA3"] = EcuIdent("004", "213", "00A5", "8300", "UCH", "GRP",
                                                        "S2000_Atmo___SoftA3.json",
                                                        "KWP2000 FastInit MonoPoint", [], "7A")
        else:
            # Use integrated DeviceManager for enhanced features
            if hasattr(options, 'elm') and options.elm:
                # Initialize device with enhanced features
                from elm import DeviceManager
                DeviceManager.initialize_device(options.elm)
            
            options.elm.init_iso()

        project_kwp_addresses = []
        if vehiclefilter:
            if vehiclefilter in self.ecu_database.vehiclemap:
                for proto, addr in self.ecu_database.vehiclemap[vehiclefilter]:
                    if proto == u"KWP2000" and addr not in project_kwp_addresses:
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

            text = _("Scanning address: ")
            try:
                # Try long name first
                print(f"{text + addr:<35} ECU: {self.ecu_database.addr_group_mapping_long[addr]}")
            except KeyError:
                # If not, short name
                print(f"{text + addr:<35} ECU: {self.ecu_database.addr_group_mapping[addr]}")

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
        global tgt
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
                    label.setText(_("Found: ") + " %i ECU" % self.num_ecu_found)
                found_exact = True
                href = target.href
                line = "<font color='green'>" + _("Identified ECU") + " [%s]@%s : %s DIAGVERSION [%s]" \
                                                                      "SUPPLIER [%s] SOFT [%s] VERSION [%s] {%i}</font>" \
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
                    label.setText(_("Found: ") + " %i ECU" % self.num_ecu_found)

                text = _("Found ECU")
                text1 = _("(not perfect match)")
                # accessbbitity blue color for reason in window bad reader
                line = f"<font color='blue'>{text} {ecu_type} {text1} :" \
                       "%s DIAGVERSION [%s] SUPPLIER [%s] SOFT [%s] VERSION [%s instead %s]</font>" \
                       % (kept_ecu.name, diagversion, supplier, soft, version, tgt.version)

                options.main_window.logview.append(line)

        if not found_exact and not found_approximate:
            text = _("Found ECU")
            text1 = _("(no relevant ECU file found)")
            line = f"<font color='red'>{text} {ecu_type} {text1} :" \
                   "DIAGVERSION [%s] SUPPLIER [%s] SOFT [%s] VERSION [%s]</font>" \
                   % (diagversion, supplier, soft, version)

            options.main_window.logview.append(line)
