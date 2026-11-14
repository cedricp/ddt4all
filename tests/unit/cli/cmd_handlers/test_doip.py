import argparse

from ddt4all.cli.cmd_handlers.doip import cmd_doip


def test_cmd_doip_reports_discovered_vehicle_and_closes_device(mocker, capsys):
    device_class = mocker.patch("ddt4all.cli.cmd_handlers.doip.DoIPDevice")
    device = device_class.return_value
    device.connect.return_value = True
    device.vehicle_info = [{
        "vin": "VF1TEST0000000000",
        "logical_address": 0x0E00,
        "eid": "010203040506",
    }]

    assert cmd_doip(argparse.Namespace()) == 0

    output = capsys.readouterr().out
    assert "DoIP routing activated" in output
    assert "VF1TEST0000000000" in output
    device.disconnect.assert_called_once()


def test_cmd_doip_connection_failure_is_reported_and_closed(mocker, capsys):
    device_class = mocker.patch("ddt4all.cli.cmd_handlers.doip.DoIPDevice")
    device = device_class.return_value
    device.connect.return_value = False
    device.last_error = "routing activation rejected"

    assert cmd_doip(argparse.Namespace()) == 1

    output = capsys.readouterr().out
    assert "routing activation rejected" in output
    device.disconnect.assert_called_once()
