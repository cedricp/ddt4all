import argparse

from ddt4all.core.doip.doip_devices import DoIPDevice
import ddt4all.options as options

_ = options.translator("ddt4all")


def cmd_doip(args: argparse.Namespace) -> int:
    """Discover and activate a configured DoIP entity."""
    target_ip = options.configuration.get(
        "doip_target_ip", getattr(options, "doip_target_ip", "192.168.0.12")
    )
    target_port = options.configuration.get(
        "doip_target_port", getattr(options, "doip_target_port", 13400)
    )
    device = DoIPDevice(target_ip, target_port)
    device.timeout = float(
        options.configuration.get("doip_timeout", getattr(options, "doip_timeout", 5))
    )

    try:
        if not device.connect():
            print(_("Failed to connect to DoIP entity: %s") % device.last_error)
            return 1

        print(_("DoIP routing activated for %(ip)s:%(port)s") % {
            "ip": target_ip, "port": target_port
        })
        if not device.vehicle_info:
            print(_("No vehicle-identification response was received"))
        for vehicle in device.vehicle_info:
            print(_("Vehicle VIN=%(vin)s logical address=0x%(address)04X EID=%(eid)s") % {
                "vin": vehicle["vin"],
                "address": vehicle["logical_address"],
                "eid": vehicle["eid"],
            })
        return 0
    finally:
        device.disconnect()
