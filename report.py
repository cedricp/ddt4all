import urllib
import urllib2
import json

report_url = 'https://api.ragic.com/ddt4all/office-manager1/3'


def report_ecu(supplier, soft, version, diagversion, address, can_bytes, href):
    form_data = {}
    form_data['1000275'] = supplier
    form_data['1000276'] = diagversion
    form_data['1000277'] = soft
    form_data['1000278'] = version
    form_data['1000280'] = can_bytes
    form_data['1000281'] = address
    form_data['1000282'] = href

    params = urllib.urlencode(form_data)
    response = urllib2.urlopen(report_url, params)

    json_data = response.read()
    data = json.loads(json_data)