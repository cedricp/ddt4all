class EcuDevice:
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
            if dtc:
                self.dtc = int(dtc)
            dtctype = dev.getAttribute("Type")
            if dtctype:
                self.dtctype = int(dtctype)

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