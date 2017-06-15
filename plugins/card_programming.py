# -*- coding: utf-8 -*-

# Plugin to program keys on Megane II
# (c) 2017
# This is an example plugin

import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import ecu

plugin_name = "Megane/Scenic II card programming"
category = "Keys"


def get_isk(ecu, ecu_response = None):
    isk_data_name = u'ISK Code'
    request_ab_frame_name = u'Trame AB: Trame réservée'

    # ECU Request
    abframe_request = ecu.requests[request_ab_frame_name]
    # Request data information (Tells where in the received ELM byte stream we will find it)
    isk_code_data = abframe_request.dataitems[isk_data_name]
    # Data item definition (Number of bytes, bits, encoding, format, etc.)
    isk_code_ecu_data = ecu.data[isk_data_name]

    # Send request (No data to provide here)
    if ecu_response is None:
        # Get it for real, else try a predefined value
        pass
    # Get Request
    return isk_code_ecu_data.getHexValue(ecu_response, isk_code_data, abframe_request.endian).upper()


def plugin_entry():
    megane_ecu = ecu.Ecu_file("../json/UCH_Megane.json", True)
    apv_data_name = u'Code APV'

    # Request gathering
    start_session_request = megane_ecu.requests[u'Start Diagnostic Session']
    after_sale_request = megane_ecu.requests[u'ACCEDER AU MODE APRES-VENTE']
    learn_key_request = megane_ecu.requests[u'APPRENDRE BADGE']
    tester_present_request = megane_ecu.requests[u'Tester present']

    # Data items gathering
    code_apv_data = after_sale_request.sendbyte_dataitems[apv_data_name]
    code_apv_ecu_data = megane_ecu.data[apv_data_name]

    # First generate a list of bytes representing the frame to be sent to the ELM
    # A template of it is available in the 'sentbytes' member of an 'Ecu_request' class
    elm_data_stream = after_sale_request.get_formatted_sentbytes()
    print code_apv_ecu_data.setValue("001122334455", elm_data_stream, code_apv_data, after_sale_request.endian)
    print get_isk(megane_ecu, "61AB02FC0D08514C86555400000000000000008DE8EE1679D3C9A7A7CCF6AC0000000000002A")
