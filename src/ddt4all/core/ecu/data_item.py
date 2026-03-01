class DataItem:
    def __init__(self, item, req_endian, name=''):
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
        if not self.ref:
            js['ref'] = self.ref
        if self.endian != '':
            js['endian'] = self.endian
        return js