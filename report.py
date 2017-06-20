import urllib
import urllib2
import json

report_url = 'https://www.ragic.com/ddt4all/office-manager1/3'


def report_ecu(supplier, soft, version, diagversion, address, can_bytes, href, protocol):
    form_data = {}
    form_data['1000275'] = str(supplier)
    form_data['1000276'] = str(diagversion)
    form_data['1000277'] = str(soft)
    form_data['1000278'] = str(version)
    form_data['1000280'] = str(can_bytes)
    form_data['1000281'] = str(address)
    form_data['1000282'] = str(href)
    form_data['1000283'] = str(protocol)

    params = urllib.urlencode(form_data)
    response = urllib2.urlopen(report_url, params)

    json_data = response.read()
    data = json.loads(json_data)
    print data