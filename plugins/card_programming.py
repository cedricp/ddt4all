# -*- coding: utf-8 -*-

# Plugin to program keys on Megane II
# (c) 2017
# This is an example plugin


import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import ecu

plugin_name = "Megane/Scenic II card programming"
category = "Keys"
need_hw = True

def get_isk(ecu, ecu_response):
    ecu_response = ecu_response.replace(' ', '').strip()
    return ecu_response[19 * 2:25 * 2]


def plugin_entry():
    megane_ecu = ecu.Ecu_file("UCH_84_J84_03_60.json", True)

    # Request gathering
    start_session_request = megane_ecu.requests[u'Start Diagnostic Session']
    after_sale_request = megane_ecu.requests[u'ACCEDER AU MODE APRES-VENTE']
    learn_key_request = megane_ecu.requests[u'APPRENDRE BADGE']
    #tester_present_request = megane_ecu.requests[u'Tester present']

    # First generate a list of bytes representing the frame to be sent to the ELM
    # A template of it is available in the 'sentbytes' member of an 'Ecu_request' class
    print after_sale_request.build_data_stream({u'Code APV': "001122334455"})
    print get_isk(megane_ecu, "61AB02FC0D08514C86555400000000000000008DE8EE1679D3C9A7A7CCF6AC0000000000002A")

