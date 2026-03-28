"""DoIP (Diagnostics over IP) Protocol Implementation

ISO 13400 Standard Implementation for Ethernet-based vehicle diagnostics

This module provides complete DoIP protocol support for modern automotive diagnostic
interfaces that support Ethernet communication, such as Bosch MTS, VXDIAG, VAG ODIS,
and JLR DoIP VCI devices.

DoIP is primarily used for newer vehicles (2016+) with extended 29-bit CAN identifiers
and modern ECU architectures requiring high-speed Ethernet diagnostics.

Note: Traditional ELM327-based adapters (OBDLink, VGate, DERLEK) do not support DoIP
as they lack Ethernet hardware and IP stack capabilities.

This module includes internationalization support for multi-language environments."""

import argparse

from ddt4all.core.doip.doip_devices import DoIPDevice
import ddt4all.options as options

_ = options.translator('ddt4all')

def cmd_doip(args: argparse.Namespace) -> int:
    # Test DoIP implementation with Electric ECU support
    doip_device = DoIPDevice()
    
    if doip_device.connect():
        print(_("DoIP device connected successfully"))
        
        # Test CAN initialization
        if doip_device.init_can():
            print(_("DoIP CAN initialized with Electric ECU support"))
        
        # Test diagnostic request
        try:
            response = doip_device.request("22 F1 90")  # Read VIN
            print(_("DoIP response: {}").format(response))
        except Exception as e:
            print(_("DoIP request failed: {}").format(e))
        
        # Test Electric ECU configurations
        electric_ecus = [
            ('EVC', {'idTx': 0x18DA10F1, 'idRx': 0x18DB10F1}),  # Electric Vehicle Controller
            ('BMS', {'idTx': 0x18DA20F1, 'idRx': 0x18DB20F1}),  # Battery Management System
            ('OBC', {'idTx': 0x18DA30F1, 'idRx': 0x18DB30F1}),  # On-Board Charger
            ('INV', {'idTx': 0x18DA40F1, 'idRx': 0x18DB40F1}),  # Inverter (Motor Control)
            ('VCM', {'idTx': 0x18DA50F1, 'idRx': 0x18DB50F1}),  # Vehicle Control Module
            ('BCM', {'idTx': 0x18DA60F1, 'idRx': 0x18DB60F1}),  # Body Control Module
            ('GWM', {'idTx': 0x18DA70F1, 'idRx': 0x18DB70F1})   # Gateway Module
        ]
        
        for ecu_name, ecu_data in electric_ecus:
            print("\n" + _("Testing Electric ECU: {}").format(ecu_name))
            doip_device.set_can_addr(ecu_name, ecu_data)
            response = doip_device.request("22 F1 90")  # Read VIN
            print(_("DoIP response: {}").format(response))
        
        doip_device.disconnect()
    else:
        print(_("Failed to connect to DoIP device"))
