import argparse
from unittest.mock import call

from ddt4all.cli.cmd_handlers.usbdevice import cmd_usbdevice


def test_cmd_usbdevice_calls_obd_device_methods_in_order(mocker, capsys):
    mock_obd_device_class = mocker.patch(
        "ddt4all.cli.cmd_handlers.usbdevice.OBDDevice"
    )
    mock_obd_device = mock_obd_device_class.return_value
    mock_obd_device.start_session_can.return_value = "OK"

    cmd_usbdevice(argparse.Namespace())
    captured = capsys.readouterr()

    assert mock_obd_device.mock_calls == [
        call.init_can(),
        call.set_can_addr(26, {}),
        call.start_session_can("10C0"),
    ]
    assert captured.out.strip() == "OK"