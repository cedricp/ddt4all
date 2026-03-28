# Protocols:
# KWP2000 FastInit MonoPoint            ?ATSP 5?
# KWP2000 FastInit MultiPoint           ?ATSP 5?
# KWP2000 Init 5 Baud Type I and II     ?ATSP 4?
# DiagOnCAN                             ATSP 6
# CAN Messaging (125 kbps CAN)          ?ATSP B?
# ISO8                                  ?ATSP 3?

class EcuIdent:
    def __init__(self, diagversion, supplier, soft, version, name, group, href, protocol, projects, address,
                 zipped=False):
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
        elif "DOIP" in protocol.upper():
            self.protocol = 'DOIP'
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