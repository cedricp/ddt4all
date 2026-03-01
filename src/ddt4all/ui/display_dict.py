class DisplayDict:
    def __init__(self, request_name, request):
        self.request = request
        self.request_name = request_name
        self.data = []
        self.datadict = {}

    def addData(self, displaydata):
        self.data.append(displaydata)
        if displaydata.data.name not in self.datadict:
            self.datadict[displaydata.data.name] = displaydata

    def getDataByName(self, name):
        for data in self.data:
            if data.data.name == name:
                return data
        return None
